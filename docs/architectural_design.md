# AI agent architecture for Bharat Agentic hackathon

**Created:** 10/1/2026 11:53:26  
**Updated:** 10/1/2026 12:05:37  
**Exported:** 10/1/2026 12:21:46  
**Link:** [https://claude.ai/chat/90f8ee09-ef2f-4819-b668-21571c28964e](https://claude.ai/chat/90f8ee09-ef2f-4819-b668-21571c28964e)  

## Assistant:

> 10/1/2026 12:05:37

> Drafting a detailed hackathon-ready architecture document.
>
> - Drafting a detailed hackathon-ready architecture document.
> - **Done**

# NammaTwin v2: "Tickets Are the Sensors" (Hackathon Build Blueprint)

## 0. One-line pitch

> **NammaTwin turns scattered citizen complaints into a cross-department incident, finds the likely root cause using real public signals, and dispatches coordinated, human-approved actions in Kannada and English, then checks whether they worked.**

**What changed from v1:**

| v1 | v2 |
|---|---|
| Hand-typed "digital twin" dict | Real signals (rainfall, elevation, OSM, traffic) plus clearly labelled simulated feeds |
| 3 LLM calls in a row | A looping Investigator that picks tools based on what it has found |
| Asserted root causes | Ranked hypotheses with confidence and linked evidence |
| Auto-dispatch | Officer approves, edits, or rejects |
| Ends at the dossier | Verifier closes the loop |
| English only | Kannada voice and photo intake, Kannada replies |
| No validation | Backtest on a real flood day plus a labelled eval set |

---

## 1. System architecture

```
┌────────────────────────── INTAKE LAYER ──────────────────────────┐
│ Telegram bot (text / Kannada voice / photo)   Web form            │
└───────────────┬──────────────────────────────────────────────────┘
                ▼
┌───────────────────────────┐
│ 1. Intake Agent           │ STT (Sarvam) → translate → LLM extract
│  • category, severity     │ → geocode → H3 cell → vision on photo
│  • Pydantic Ticket        │ → write to DB
└───────────────┬───────────┘
                ▼
┌───────────────────────────┐
│ 2. Cluster Detector       │ NON-LLM. H3 k-ring + time window
│  • spatial-temporal       │ → emits Incident when threshold met
│  • cross-category rule    │ → updates Incident when tickets join
└───────────────┬───────────┘
                ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Investigator Agent (LangGraph loop)                      │
│    state: incident, hypotheses[], evidence[], step_budget   │
│                                                             │
│   propose_hypotheses ─► select_tool ─► run_tool ─►          │
│        ▲                                   │                │
│        │                              update_scores         │
│        └──── continue? ◄──────────────────┘                 │
│                  │ stop: confidence ≥ 0.75, gap ≥ 0.2,      │
│                  │       or steps ≥ 6                       │
└──────────────────┼──────────────────────────────────────────┘
        ┌──────────┴───────────── TOOL LAYER ─────────────────┐
        │ rainfall · elevation · osm_context · traffic ·      │
        │ ticket_history · outage_feed(sim) · stp_feed(sim) · │
        │ hotspot_registry · vision_depth                     │
        └─────────────────────────────────────────────────────┘
                   ▼
┌───────────────────────────┐
│ 4. Planner Agent          │ per-department actions, priority score,
│  • vulnerability-weighted │ rationale tied to evidence IDs
└───────────────┬───────────┘
                ▼
┌───────────────────────────┐
│ 5. Officer Console (HITL) │ LangGraph interrupt() → approve/edit/reject
└───────────────┬───────────┘
                ▼
┌───────────────────────────┐
│ 6. Dispatcher             │ Telegram/email/webhook per department
│  + Citizen Notifier       │ Kannada/English status reply to reporters
└───────────────┬───────────┘
                ▼
┌───────────────────────────┐
│ 7. Verifier (scheduled)   │ re-check rainfall/tickets/traffic after
│                           │ N min → resolving / escalate / closed
└───────────────────────────┘

Cross-cutting: Postgres/SQLite · Langfuse trace · Evidence ledger
```

**Design principle:** LLMs do language understanding, hypothesis generation, tool choice, and writing. **Code does** clustering, scoring, geo math, and thresholds. This keeps the demo reliable and gives you an honest answer to "isn't this just prompting?"

---

## 2. Component detail

### 2.1 Intake Agent

**Inputs:** Telegram text, Telegram voice (OGG), photo, web form, and a **seed script** that replays synthetic tickets for the demo and backtest.

**Steps:**
1. If voice: convert OGG → WAV with `ffmpeg`, then Sarvam STT (Kannada), which returns transcript and detected language.
2. If not English: translate to English for reasoning. Store both original and translated text.
3. LLM extraction into a Pydantic `Ticket`.
4. Geocode: Telegram location pin (best), else a landmark gazetteer (a 100-300 row CSV of Bellandur/ORR/HSR/Silk Board landmarks), else LLM-extracted place name matched with fuzzy search.
5. Convert to an H3 cell (resolution 8, ~0.7 km² hexes, is a good default).
6. If a photo is attached, call the vision model for a flood-depth bucket (`ankle / knee / waist / vehicle-stalled`) with a confidence value.

```python
class Ticket(BaseModel):
    id: str
    ts: datetime
    channel: Literal["telegram","web","synthetic"]
    lang: str
    text_original: str
    text_en: str
    category: Literal["waterlogging","power","sewage","water_supply",
                      "traffic","garbage_debris","road_damage","other"]
    severity: int            # 1-5, LLM-estimated
    lat: float; lon: float
    geo_confidence: float
    h3_r8: str
    photo_depth: Optional[Literal["ankle","knee","waist","vehicle"]]
    reporter_chat_id: Optional[str]
    is_synthetic: bool
```

### 2.2 Cluster Detector (no LLM)

**Rule:** an **Incident** opens when, within a 2-ring of H3 cells (~2-3 km) and a rolling 60-minute window, there are **≥ 4 tickets and ≥ 2 distinct categories**, or **≥ 8 tickets of one category**.

- Use `h3.grid_disk(cell, 2)` for neighbourhoods. DBSCAN over (lat, lon, time) is an optional refinement.
- Incident score = weighted ticket count × severity × recency decay.
- New tickets that fall inside an open incident's footprint are attached and trigger a re-investigation (debounced to once per 5 minutes).

```python
class Incident(BaseModel):
    id: str; opened_at: datetime; status: Literal["open","investigating",
        "awaiting_approval","dispatched","resolving","closed","escalated"]
    ticket_ids: list[str]
    centroid: tuple[float,float]; cells: list[str]
    category_mix: dict[str,int]
```

### 2.3 Investigator Agent (the core)

**Hypothesis catalog** (hand-written, 5-6 entries; this is your domain-knowledge moat):

| ID | Expected signature | Departments |
|---|---|---|
| `RAIN_OVERWHELM` | High rainfall (>25 mm/hr), low-lying cell, historical hotspot | Stormwater, Traffic |
| `DRAIN_BLOCKAGE` | Waterlogging with *low or moderate* rain, debris/garbage tickets nearby, narrow localized spread | Stormwater/SWD, Solid Waste |
| `POWER_LED_STP_OVERFLOW` | Power tickets precede sewage/odour tickets by 30-120 min, large apartments/tech parks nearby | Power utility, Sewerage board |
| `PIPE_BURST` | Water-supply tickets, localized, dry weather, linear spread along a road | Water board |
| `LAKE_OVERFLOW` | Near a lake polygon, sustained rain over previous 24 h | Lake authority, Stormwater |
| `TRAFFIC_ONLY` | Traffic tickets with no water/power signal (null hypothesis, which makes the system honest) | Traffic police |

Each hypothesis has **evidence rules**: how much each observation shifts belief. Scoring in log-odds:

```python
LR = {  # likelihood ratios: P(evidence|H) / P(evidence|not H)
 "RAIN_OVERWHELM": {"rain_gt_25": 6.0, "low_lying": 2.5, "known_hotspot": 3.0,
                    "rain_lt_5": 0.1},
 "DRAIN_BLOCKAGE": {"rain_lt_15": 2.5, "debris_tickets_nearby": 4.0,
                    "localized_spread": 2.0, "rain_gt_40": 0.4},
 "POWER_LED_STP_OVERFLOW": {"power_tickets_precede_sewage": 5.0,
                            "large_stp_site_nearby": 2.5},
 ...
}
def update(logodds, evidence_key, H): return logodds + math.log(LR[H][evidence_key])
```

Priors come from a small table (or uniform). Posteriors are normalised across hypotheses. **The LR numbers are expert-set heuristics, not learned.** Say so on the slide, and calibrate lightly against your backtest scenarios.

**Loop (LangGraph nodes):**

1. `propose`: LLM sees the incident summary plus the catalog and returns the active hypotheses with what evidence would discriminate between them.
2. `select_tool`: LLM picks the tool with the highest expected information gain (a structured output: `tool_name`, `args`, `why`). Tools already called are excluded.
3. `run_tool`: Python executes it and returns a typed `Evidence` object.
4. `update`: code maps evidence to evidence keys and updates scores. The LLM does **not** compute scores.
5. `decide`: stop if top posterior ≥ 0.75 **and** margin over second ≥ 0.2, or steps ≥ 6, or tools are exhausted. If stopped without confidence, output "inconclusive: top candidates A, B" and recommend a field inspection. That is a feature.

```python
class Evidence(BaseModel):
    id: str; tool: str; ts: datetime
    summary: str                 # "Rainfall 38 mm/hr at 06:00-07:00"
    keys: list[str]              # ["rain_gt_25"]
    source: str                  # "Open-Meteo archive API"
    provenance: Literal["real","simulated","derived"]
    raw: dict

class InvState(TypedDict):
    incident: Incident
    tickets: list[Ticket]
    hypotheses: dict[str, float]     # log-odds
    evidence: list[Evidence]
    tools_used: list[str]
    steps: int
    trace: list[dict]                # for UI streaming
    result: Optional[Dossier]
```

### 2.4 Tool layer

Every tool is a plain Python function with a Pydantic input/output schema. Optionally wrap them in **FastMCP** servers grouped by department (`weather-mcp`, `geo-mcp`, `utility-mcp`) as your scalability story. The adapters are the only things a real department needs to replace.

| Tool | Source | Real/Sim | Notes |
|---|---|---|---|
| `get_rainfall(lat, lon, t0, t1)` | Open-Meteo forecast + archive API | **Real** | Free, no key. Archive for backtest; forecast API with `past_hours` for live |
| `get_elevation_context(lat, lon)` | OpenTopoData SRTM or a pre-downloaded raster | **Real** | Compute whether the cell is lower than neighbours (a "bowl" check). **Pre-cache for your 2-3 demo areas** |
| `get_osm_context(lat, lon, r)` | Overpass API (cache the result to JSON) | **Real** | Hospitals, schools, lakes, drains/waterways, large buildings, major roads. **Pre-fetch before demo** |
| `get_traffic(lat, lon)` | TomTom Traffic Flow free tier | **Real (live only)** | No historical data, so use simulated values for the backtest and label them |
| `get_ticket_history(cells, window)` | Your DB | Real (own data) | Counts and timelines by category, which powers "power precedes sewage" |
| `get_hotspot_registry(cell)` | A CSV you compile from news and published reports of known waterlogging points | Derived | Cite your sources in the README |
| `get_outage_feed(area, window)` | Mock BESCOM adapter | **Simulated** | Label "SIMULATED: stand-in for utility API" in the UI. Same interface a real feed would implement |
| `get_stp_status(site)` | Mock | **Simulated** | Optional. Skip if short on time |
| `estimate_flood_depth(photo)` | Vision LLM | Real (model) | Report a bucket and confidence |

**Provenance badges** ("REAL / SIMULATED / DERIVED") appear next to every evidence line in the UI. This is the honesty feature judges will remember.

### 2.5 Planner Agent

Input: the final `Dossier` (ranked hypotheses plus evidence). Output: a list of `Action`s.

```python
class Action(BaseModel):
    dept: Literal["stormwater","power_utility","sewerage","traffic_police",
                  "solid_waste","water_board"]
    action: str                  # "Inspect and clear culvert near X"
    target_latlon: Optional[tuple[float,float]]
    priority: Literal["P1","P2","P3"]
    rationale: str
    evidence_ids: list[str]      # must be non-empty; validator enforces
    confidence: float
    needs_field_verification: bool
```

**Vulnerability-weighted priority** (code, not LLM):

```
priority_score = 0.35·severity_norm + 0.25·ticket_velocity
               + 0.25·vulnerability + 0.15·hypothesis_confidence
vulnerability = f(distance to hospital, school, ambulance route / arterial road, #people-affected proxy)
```

Map the score to P1/P2/P3, then show the officer **why** (a small bar breakdown). Replace the old static 72-hour SLA with dynamic target response times.

**Guardrails:** low-confidence hypotheses produce *inspect-first* actions ("send an engineer to verify"), not *remedy* actions ("dispatch a backhoe"). A validator rejects any action without evidence IDs.

### 2.6 Officer Console (human-in-the-loop)

LangGraph `interrupt()` pauses the graph at `awaiting_approval`. The officer sees the dossier and per-action checkboxes and can **Approve / Edit text / Reject with reason**. The graph resumes with the officer's decision, which is also logged for audit.

### 2.7 Dispatcher and Citizen Notifier

- **Departments:** one Telegram group or chat per department (use your team's own test chats), plus an email via SMTP/Resend as a second channel. Messages are structured: incident ID, location pin, action, evidence summary, confidence, approval stamp.
- **Citizens:** each reporting chat gets a status in their language ("Your report is linked to a larger incident. Cause under investigation. BESCOM and the stormwater team have been notified."), with Sarvam TTS for a voice reply as a stretch goal.
- WhatsApp is the roadmap item. Don't build it today.

### 2.8 Verifier (closes the loop)

A scheduled job (APScheduler, or a LangGraph node with a delay; for the demo use a **"fast-forward 45 minutes" button**) re-checks:
- new tickets in the footprint (decaying = good)
- rainfall (stopped or not)
- traffic speed ratio (if live)
- officer-marked "action completed"

It sets the status to `resolving`, `escalated` (with a new message to a higher-level official), or `closed`, and sends a citizen update.

---

## 3. Data sources and honesty

| Layer | Status |
|---|---|
| Rainfall, elevation, OSM | Real |
| Traffic | Real live (TomTom), simulated for backtest |
| Hotspot registry | Derived from public news and reports (cite) |
| Utility outage / STP | **Simulated adapters** with the interface a real feed would use |
| Tickets in demo | **Synthetic**, generated to match a documented event |

Include one slide, "What's real, what's simulated, how a department plugs in." Honest framing scores better than a faked "live" claim, and it reads as a feasibility answer.

---

## 4. Validation (your Technical Implementation score)

### 4.1 Backtest on a real event
1. Choose a documented heavy-rain/flood day in Bengaluru (e.g., ORR/Bellandur/Silk Board waterlogging coverage). Search news for the date and affected areas.
2. Pull hourly rainfall for that date from Open-Meteo's archive API.
3. Write a synthetic ticket generator that produces realistic tickets (mixed Kannada/English, varied categories) with timestamps tied to the news timeline. Mark all as `is_synthetic=True`.
4. Replay in simulated time. Record **when NammaTwin opens an incident and names the likely cause** versus **when official response is reported** in the news.
5. Report **lead time = official response time − NammaTwin flag time**, with the caveat that the ticket stream is synthetic.

Don't overclaim. Phrase it as "on a replay of [date], the system flagged the cluster ~X minutes after the first reports and identified the likely cause."

### 4.2 Labelled eval set
Create 15-20 scenarios as JSON: ticket stream, simulated or real signals, and a ground-truth cause. Cover all hypotheses including `TRAFFIC_ONLY` and 2-3 deliberately ambiguous ones. Metrics:
- top-1 and top-2 root-cause accuracy
- correct-department-routing rate
- vs. **baseline**: "route by ticket category only" (what today's systems do)
- calibration sanity check: average confidence on correct vs. incorrect

One bar chart (baseline vs. NammaTwin) goes on a slide.

---

## 5. Recommended stack (final)

| Layer | Choice |
|---|---|
| Language | Python 3.11 |
| Agents | **LangGraph** (loop, state, interrupt, checkpointer) |
| Schemas | **Pydantic v2** with the LLM's structured-output mode |
| LLM | One fast model for loops and intake, one stronger model for the final dossier and planner, using whatever credits the hackathon provides |
| Indic | **Sarvam AI** (STT, translate, TTS). Fallback: IndicTrans2 or the LLM for translation |
| Vision | Same multimodal LLM |
| Geo | `h3`, `shapely`, `geopandas`, `requests` to Overpass/Open-Meteo |
| DB | SQLite + SQLAlchemy (swap to Postgres/PostGIS in the roadmap) |
| Bot | `python-telegram-bot` |
| API | FastAPI (webhook endpoints for the bot, console actions, SSE for trace streaming) |
| UI | **Streamlit** + pydeck for speed; React + MapLibre only if you have a dedicated frontend dev |
| Observability | Langfuse (free tier) or LangSmith, with a link to the trace in the demo |
| Scheduling | APScheduler |
| Deploy | Render or Railway for FastAPI + bot; Streamlit Cloud for the UI. Keep a local fallback and a pre-recorded video in case the network fails |

---

## 6. Repo structure

```
namma-twin/
├─ app/
│  ├─ main.py                  # FastAPI
│  ├─ models.py                # Pydantic: Ticket, Incident, Evidence, Action
│  ├─ db.py
│  ├─ intake/  (stt.py, extract.py, geocode.py, vision.py)
│  ├─ cluster/ (detector.py)
│  ├─ investigator/
│  │   ├─ graph.py             # LangGraph definition
│  │   ├─ hypotheses.py        # catalog + LR tables
│  │   ├─ scoring.py
│  │   └─ prompts.py
│  ├─ tools/   (rainfall.py, elevation.py, osm.py, traffic.py,
│  │            history.py, hotspots.py, outage_sim.py)
│  ├─ planner/ (planner.py, priority.py)
│  ├─ dispatch/ (telegram.py, email.py, notifier.py)
│  └─ verifier/ (verifier.py)
├─ ui/streamlit_app.py
├─ data/ (landmarks.csv, hotspots.csv, osm_cache/, elev_cache/)
├─ backtest/ (generate_tickets.py, replay.py, scenarios/*.json, eval.py)
├─ docs/ (architecture.png, data_provenance.md)
└─ README.md
```

---

## 7. UI layout (Streamlit)

- **Left, "Incoming":** live ticket feed with language flag, category chip, and a "synthetic" tag where applicable.
- **Center, map:** H3 hex heat layer for ticket density, incident footprint outline, hospital/school markers, and evidence pins.
- **Right, "Investigator":** streaming trace (hypothesis bars moving as evidence arrives, each tool call with provenance badge), then the **Dossier** (ranked causes with confidence, evidence links) and **Actions** with Approve / Edit / Reject.
- **Bottom tab, "Impact":** backtest timeline and the eval chart.

Streaming the hypothesis bars shifting as each tool returns is the single most persuasive visual. Build it early.

---

## 8. Build plan for today (4 people)

Adjust to your actual start time. The structure is what matters.

| Person | Scope |
|---|---|
| **A: Agent core** | Models, LangGraph investigator, hypotheses and scoring, planner |
| **B: Data/geo** | H3, cluster detector, tools (rainfall, elevation, OSM cache, history, hotspots), simulated outage adapter |
| **C: Interfaces** | Telegram bot, Sarvam intake, Streamlit UI and map, dispatcher |
| **D: Proof and story** | Ticket generator, backtest, eval set and chart, deck, README, demo video |

**Phases:**
1. **Hours 0-1.5:** agree on `models.py` and tool signatures first, because everything else depends on them. Create the repo, grab API keys, pre-fetch OSM and elevation for 2-3 areas.
2. **Hours 1.5-5:** vertical slice. One synthetic incident goes ticket → cluster → investigator → dossier printed in a terminal. Do not build UI before this works.
3. **Hours 5-8:** console with HITL, Telegram dispatch, map, trace streaming, Kannada voice and photo intake.
4. **Hours 8-10:** backtest and eval, Verifier with the fast-forward button, deploy.
5. **Hours 10-11:** feature freeze. Bug-bash the demo path 3 times. Record the video. Finish the deck.
6. **Final hour:** submit early. Don't wait for the last 15 minutes.

**Cut order if behind:** Verifier (keep only the button, with a simple recheck) → photo depth → TTS → email dispatch → traffic live tool. **Never cut:** clustering, the investigator loop with real rainfall and elevation tools, HITL approval, evidence/provenance display.

---

## 9. Risks and mitigations

| Risk | Mitigation |
|---|---|
| API outage or rate limit mid-demo | Cache every tool response for demo scenarios; a `DEMO_MODE` flag replays cached evidence |
| LLM returns malformed output | Pydantic structured output plus retry-once and a deterministic fallback tool order |
| Geocoding errors | Landmark gazetteer for demo areas; Telegram location pin as the primary path |
| Latency of the loop | Fast model for loop steps; parallelize independent tool calls; cap at 6 steps |
| Judge challenges the LR numbers | Say plainly: expert priors, sanity-checked on 20 scenarios, designed to be learned from officer feedback logs |
| Naming and organisation accuracy | Bengaluru's civic structure changed (the Greater Bengaluru Authority and city corporations). Verify current department names and use generic labels ("Stormwater division") where unsure |
| Privacy | Store only chat ID and location needed; note anonymization and data-retention in the deck |

---

## 10. Demo script (3 minutes)

1. **0:00-0:25** The problem: one road, four departments, no shared picture.
2. **0:25-1:00** A Kannada voice note with a flood photo arrives via Telegram. Show transcription, translation, and extracted ticket.
3. **1:00-1:50** Synthetic tickets stream in and the hexes light up. An incident opens. Show the Investigator trace: hypotheses shift as rainfall, elevation, and ticket history come back, with REAL/SIMULATED badges.
4. **1:50-2:25** Officer reviews the dossier, edits one action, and approves. Department Telegram messages arrive on a second screen, and the citizen gets a Kannada status reply.
5. **2:25-2:45** Click "fast-forward 45 min": the Verifier shows the cluster decaying and marks it resolving.
6. **2:45-3:00** Backtest lead-time and baseline-vs-NammaTwin accuracy.

---

## 11. 5-slide pitch deck

1. **Problem and who suffers.** The silo story with a single real-feeling example.
2. **Solution.** "Tickets are the sensors," with a one-line flow.
3. **Architecture.** The diagram from Section 1 plus the "what's real/simulated" strip.
4. **Results.** Backtest lead time and eval chart vs. baseline.
5. **Impact, scalability, roadmap.** Department adapters via MCP, WhatsApp, real utility APIs, learning LRs from officer feedback, other cities.

---

## 12. Mapping to judging criteria

| Criterion | What delivers it |
|---|---|
| Agentic Capability | Investigator loop with tool selection, HITL, dispatch, Verifier |
| Bharat Impact | Kannada voice/photo intake, dynamic vulnerability-based triage |
| Technical Implementation | Typed schemas, scoring engine, trace, eval and backtest |
| Innovation | Cross-department cascade detection from tickets rather than a siloed pipeline |
| UX | Live hypothesis bars, map, simple approve/edit/reject |
| Scalability & Feasibility | Adapter/MCP pattern, honest data provenance, HITL safety |
| Demo | Single end-to-end flow with a visible before/after |

---

I can write the code for the next pieces if you tell me which to start with: the `models.py` and LangGraph investigator skeleton, the hypotheses/scoring module, or the synthetic ticket generator and backtest harness. I can also put this whole blueprint into a file (Markdown or Word) if you want to share it with your team.

Powered by Claude Exporter (https://www.ai-chat-exporter.net)
