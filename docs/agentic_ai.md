# AI agent architecture for Bharat Agentic hackathon

**Created:** 10/1/2026 11:53:26  
**Updated:** 10/1/2026 12:28:07  
**Exported:** 10/1/2026 13:49:16  
**Link:** [https://claude.ai/chat/90f8ee09-ef2f-4819-b668-21571c28964e](https://claude.ai/chat/90f8ee09-ef2f-4819-b668-21571c28964e)  

## Assistant:

> 10/1/2026 12:28:07

> Listing shared evidence keys and tool specification details.
>
> - Listing shared evidence keys and tool specification details.
> - **Done**

# NammaTwin v2: Phased Build Plan for Two Developers

Paste Section 0 into the system prompt or rules file of your AI coding tool, then feed it one phase at a time.

---

## 0. Rules for the coding agent (paste at the top of every session)

```
You are implementing one phase of the NammaTwin repo. Follow strictly:
1. Edit ONLY files inside the directories owned by the current developer (see OWNERSHIP).
2. NEVER modify app/contracts/* unless the task says "contract change". Import from it.
3. Depend on other modules ONLY through Protocols in app/contracts/interfaces.py.
   If the real implementation does not exist yet, use the stub in app/stubs/.
4. Every phase must ship: code + tests in tests/<phase_id>/ + a runnable CLI/script
   entrypoint. Phase is done only when `pytest tests/<phase_id> -q` passes offline.
5. No network calls in tests. All external I/O goes through a client wrapper that
   supports DEMO_MODE=1 (reads cached JSON from data/cache/).
6. LLM calls go through app/llm.py::LLM.structured(schema, prompt, tier) only.
   Tests use FakeLLM with canned outputs.
7. Python 3.11, Pydantic v2, type hints everywhere, no global mutable state.
8. Commit small. Branch name = <phase_id>-<slug>. Rebase on main before PR.
```

---

## 1. Ownership map and git protocol

| Path | Owner | Notes |
|---|---|---|
| `app/contracts/` | **Frozen after P0** | `models.py`, `keys.py`, `interfaces.py`. Changes only via a PR the other dev approves |
| `app/llm.py`, `app/config.py` | P0 (joint), then **A** | |
| `app/investigator/`, `app/planner/`, `app/orchestrator/`, `app/verifier/`, `app/api/` | **Dev A** | |
| `backtest/`, `tests/A*/` | **Dev A** | |
| `app/geo/`, `app/db/`, `app/cluster/`, `app/tools/`, `app/intake/`, `app/dispatch/` | **Dev B** | |
| `ui/`, `data/`, `tests/B*/` | **Dev B** | |
| `app/stubs/` | **Each dev owns the stubs of the module they consume**, in separate files | |
| `requirements.txt`, `pyproject.toml`, `.env.example` | **P0 only** | Create the full dependency list up front so nobody edits it concurrently |

**Git rules**
- Trunk-based: `main` is always green. Short-lived branches `A1-scoring`, `B2-tools`, and so on.
- Add a `CODEOWNERS` file matching the table above.
- Merge order inside a track is sequential. Across tracks it is free, because directories don't overlap.
- Shared-file edits (`contracts/`, `requirements.txt`) go in a **separate, tiny PR** merged immediately, and the other dev rebases.
- `.gitignore`: `*.db`, `.env`, `data/cache/*.tmp`. Commit `data/cache/*.json` demo caches, since they are the DEMO_MODE fixtures.
- Integration only happens in I1. Until then each dev tests against stubs.

---

## 2. Dependency graph

```
                    P0 (joint, ~1h): contracts + scaffold + fixtures
                     │
        ┌────────────┴────────────┐
   Dev A track                Dev B track
   A1 scoring                 B1 geo+db+cluster
    ↓                          ↓
   A2 investigator            B2 tools (real+sim, cached)
    ↓                          ↓
   A3 planner+priority        B3 intake (+telegram)
    ↓                          ↓
   A4 orchestrator+API        B4 dispatch+notifier
    ↓                          ↓
   A5 backtest+eval           B5 UI (Streamlit)
        └────────────┬────────────┘
                I1 integration (joint)
                     ↓
                I2 hardening + demo + submission (joint)
```

A's track needs nothing from B at runtime because A2 uses `FakeToolRegistry` fixtures. B's track needs nothing from A because B5 reads from the repo layer and the API schema, with a mock API in B5.

---

## 3. Phase P0: Contracts and scaffold (joint, pair on one laptop, one pushes)

**Branch:** `P0-contracts`. Merge to `main` before anyone branches.

### 3.1 Files

```
app/contracts/models.py      # Ticket, Incident, Evidence, Hypothesis, Dossier, Action, Decision, Delivery
app/contracts/keys.py        # EvidenceKey, HypothesisID enums (the tool↔scoring contract)
app/contracts/interfaces.py  # Protocols
app/llm.py                   # LLM wrapper + FakeLLM
app/config.py                # pydantic-settings; DEMO_MODE, API keys
app/stubs/                   # in-memory repos, ConsoleNotifier, FakeToolRegistry
tests/fixtures/              # JSON fixtures (below)
Makefile                     # test, lint, run-api, run-ui
requirements.txt  .env.example  CODEOWNERS  .gitignore
```

### 3.2 Contracts (the part that must not drift)

```python
# keys.py: shared vocabulary. Tools EMIT these; scoring CONSUMES these.
class HypothesisID(str, Enum):
    RAIN_OVERWHELM="RAIN_OVERWHELM"; DRAIN_BLOCKAGE="DRAIN_BLOCKAGE"
    POWER_LED_STP_OVERFLOW="POWER_LED_STP_OVERFLOW"; PIPE_BURST="PIPE_BURST"
    LAKE_OVERFLOW="LAKE_OVERFLOW"; TRAFFIC_ONLY="TRAFFIC_ONLY"

class EvidenceKey(str, Enum):
    RAIN_GT_40; RAIN_GT_25; RAIN_LT_15; RAIN_LT_5; SUSTAINED_RAIN_24H
    LOW_LYING; KNOWN_HOTSPOT; NEAR_LAKE; LARGE_STP_SITE_NEARBY
    DEBRIS_TICKETS_NEARBY; LOCALIZED_SPREAD; LINEAR_SPREAD
    POWER_TICKETS_PRECEDE_SEWAGE; OUTAGE_REPORTED; NO_WATER_POWER_SIGNAL
    TRAFFIC_SLOWDOWN; DRY_WEATHER
```

```python
# models.py (fields as in the v2 blueprint; add these)
class Evidence(BaseModel):
    id: str; tool: str; ts: datetime; summary: str
    keys: list[EvidenceKey]; source: str
    provenance: Literal["real","simulated","derived"]; raw: dict

class ToolArgs(BaseModel):          # base; each tool subclasses
    incident_id: str; lat: float; lon: float
    t0: datetime; t1: datetime; cells: list[str]

class ToolSpec(BaseModel):
    name: str; description: str      # shown to the LLM in select_tool
    args_model: type[ToolArgs]; provenance: Literal["real","simulated","derived"]
    discriminates: list[HypothesisID]

class Dossier(BaseModel):
    incident_id: str
    ranked: list[tuple[HypothesisID, float]]   # posterior
    evidence: list[Evidence]
    conclusive: bool; stop_reason: str; trace: list[dict]

class Decision(BaseModel):          # officer HITL result
    incident_id: str; approved_action_ids: list[str]
    edits: dict[str,str]; rejected: dict[str,str]; officer: str
```

```python
# interfaces.py: the only cross-track coupling
class TicketRepo(Protocol):
    def add(self, t: Ticket) -> None: ...
    def window(self, cells: list[str], t0: datetime, t1: datetime) -> list[Ticket]: ...
class IncidentRepo(Protocol):
    def upsert(self, i: Incident) -> None; def get(self, id: str) -> Incident; def open(self) -> list[Incident]
class EvidenceRepo(Protocol): ...
class ToolRegistry(Protocol):
    def specs(self) -> list[ToolSpec]
    def run(self, name: str, args: ToolArgs) -> Evidence
class Notifier(Protocol):
    def send(self, dept: str, message: "OutboundMessage") -> "Delivery": ...
class ClusterDetector(Protocol):
    def ingest(self, t: Ticket) -> Incident | None: ...
```

**Tool auto-registration:** `@register_tool(spec)` decorator in `app/tools/_registry.py` (created in P0). B's tool files each add a decorator and never touch a shared registry file. `discover()` imports every module in `app/tools/` via `pkgutil`.

### 3.3 Fixtures (committed, used by both tracks)

```
tests/fixtures/tickets_bellandur_flood.json     # 14 synthetic tickets, mixed categories/langs
tests/fixtures/evidence_rain_overwhelm.json     # canned Evidence lists per scenario (3 scenarios)
tests/fixtures/evidence_power_led_stp.json
tests/fixtures/evidence_inconclusive.json
data/cache/                                      # empty; B fills in B2
```

### 3.4 Test and DoD

```
pytest tests/P0 -q
  - all models round-trip JSON
  - every EvidenceKey is referenced in keys.py
  - FakeLLM.structured returns the canned schema
  - discover() runs with zero tools without error
```
**DoD:** `main` has the contracts, `make test` is green, both devs can branch.

---

## 4. Dev A track: agent core (no external I/O)

### A1: Scoring engine and hypothesis catalog
**Branch** `A1-scoring` · **Files** `app/investigator/hypotheses.py`, `scoring.py` · **Depends on** P0

- Implement `LR: dict[HypothesisID, dict[EvidenceKey, float]]` and priors.
- Pure functions:
  - `init_state(priors) -> dict[HypothesisID, float]` (log-odds)
  - `apply(state, keys: list[EvidenceKey]) -> state` (immutable update)
  - `posterior(state) -> dict[HypothesisID, float]` (softmax-normalised)
  - `should_stop(post, steps, tools_left, budget) -> tuple[bool, str]` (top ≥ 0.75 and margin ≥ 0.2, or steps ≥ 6, or no tools left)
- Add `discriminating_keys(post) -> list[EvidenceKey]`, the keys that would most separate the top two hypotheses (feeds tool selection).

**Tests** `tests/A1/`
- Each fixture evidence set drives the expected top-1 hypothesis.
- Property test: posteriors sum to 1 and order is stable under permutation of evidence.
- `TRAFFIC_ONLY` wins when only `NO_WATER_POWER_SIGNAL` and `TRAFFIC_SLOWDOWN` are applied.
- `should_stop` returns inconclusive when margin < 0.2 at the step cap.

**DoD** `pytest tests/A1` green. CLI `python -m app.investigator.scoring --fixture <name>` prints the posterior table.

### A2: Investigator LangGraph loop
**Branch** `A2-investigator` · **Files** `app/investigator/graph.py`, `prompts.py`, `state.py` · **Depends on** A1

- Nodes: `propose → select_tool → run_tool → update → decide → (loop | finalize)`.
- `select_tool` uses `LLM.structured(ToolChoice, ...)` where `ToolChoice = {tool_name, args, why}`. It excludes tools already used and validates `tool_name` against `registry.specs()`. On a bad choice, retry once, then fall back to the deterministic order `rainfall → elevation → history → osm → hotspots → outage`.
- `run_tool` calls `ToolRegistry.run`, which is injected, never imported.
- `update` calls `scoring.apply` with `evidence.keys`. **No LLM math.**
- `finalize` builds a `Dossier`, including `conclusive` and `stop_reason`.
- Emit one `trace` dict per step (`{step, tool, why, evidence_id, posterior_snapshot}`) through a callback for later SSE streaming.
- Build the graph with `build_graph(registry, llm, repo)`, using dependency injection only.

**Tests** `tests/A2/`
- `FakeToolRegistry` replays fixture evidence by tool name, and `FakeLLM` picks tools from a scripted list.
- Assert: the loop terminates in ≤ 6 steps, never repeats a tool, and the inconclusive fixture yields `conclusive=False`.
- An invalid tool name from the LLM triggers the fallback order.
- The trace length equals the step count.

**DoD** `python -m app.investigator.run --scenario rain_overwhelm` prints the trace and dossier offline.

### A3: Planner, priority, guardrails
**Branch** `A3-planner` · **Files** `app/planner/planner.py`, `priority.py`, `validators.py` · **Depends on** P0 (and A2's `Dossier` type, which is already in the contracts)

- `priority.score(severity_norm, velocity, vulnerability, confidence) -> (float, breakdown: dict)` and `to_band(score) -> P1|P2|P3`. Weights 0.35, 0.25, 0.25, 0.15 live in config.
- `vulnerability(osm_context) -> float` is a pure function over a dict (`hospital_dist_m`, `school_dist_m`, `on_arterial: bool`). Accept the dict so there is no dependency on B's OSM tool.
- `Planner.plan(dossier, incident, osm_ctx) -> list[Action]` makes an LLM call with `Action` structured output.
- Validators (post-LLM, in code):
  - reject any Action with empty `evidence_ids`, or ids not in `dossier.evidence`
  - if `confidence < 0.6`, force `needs_field_verification=True` and rewrite remedy verbs to "inspect and verify"
  - the department must map from the top-2 hypotheses' department table, which lives in `hypotheses.py`

**Tests** `tests/A3/`
- Fixture dossiers produce valid Actions.
- A hallucinated `evidence_id` is rejected.
- Low confidence demotes the action to inspect-first.
- Priority monotonicity: higher vulnerability never lowers the band.

**DoD** `python -m app.planner.run --scenario power_led_stp` prints the actions.

### A4: Orchestrator, HITL, API, Verifier
**Branch** `A4-orchestrator` · **Files** `app/orchestrator/pipeline.py`, `app/verifier/verifier.py`, `app/api/main.py`, `app/api/schemas.py` · **Depends on** A2, A3

- Outer LangGraph: `incident_opened → investigate (subgraph A2) → plan (A3) → await_approval (interrupt) → dispatch (Notifier) → schedule_verify → verify → close|escalate`.
- Use the checkpointer (SQLite saver) so `interrupt()` survives restarts.
- FastAPI endpoints:
  - `POST /tickets` (ingest, calls `ClusterDetector.ingest`)
  - `GET /incidents`, `GET /incidents/{id}` (dossier + actions + status)
  - `GET /incidents/{id}/stream` (SSE of trace events)
  - `POST /incidents/{id}/decision` (body = `Decision`, resumes the graph)
  - `POST /incidents/{id}/verify?fast_forward_min=45` (demo button)
  - `GET /health`
- Verifier is a pure function `assess(incident, new_tickets, rainfall_now, traffic_ratio) -> Literal["resolving","escalated","closed"]` with rules (ticket decay > 50% and rain stopped → resolving, and so on), so it is testable without a scheduler.
- OpenAPI schema is exported to `docs/openapi.json` and committed. **B5 builds against this file.**

**Tests** `tests/A4/`
- `httpx.AsyncClient` plus in-memory repos plus stub notifier.
- Full flow: post fixture tickets → incident → dossier → actions → decision → notifier called with only the approved actions → fast-forward → status `resolving`.
- Rejected actions are not dispatched.
- Resume after a simulated restart works (checkpointer).

**DoD** `make run-api` with stubs, then `curl` walks the whole lifecycle. `docs/openapi.json` is committed.

### A5: Backtest and eval harness
**Branch** `A5-eval` · **Files** `backtest/generate_tickets.py`, `replay.py`, `eval.py`, `scenarios/*.json`, `backtest/report.py` · **Depends on** A4 (pipeline callable)

- `scenarios/*.json` has 15-20 entries: `{id, tickets[], evidence_overrides, ground_truth_hypothesis, ground_truth_depts}`. Include `TRAFFIC_ONLY` and 2-3 ambiguous cases.
- `eval.py` runs each scenario through the investigator with scenario-supplied evidence, then reports top-1 and top-2 accuracy, department-routing accuracy, a **baseline** (route by ticket category only), and mean confidence on correct vs. incorrect.
- `replay.py` replays a documented flood day in simulated time and records `t_incident_opened`, `t_cause_named`, and `lead_time = official_response_ts − t_cause_named`. All synthetic inputs stay tagged `is_synthetic=True`.
- `report.py` writes `docs/eval_results.json` and `docs/eval_chart.png` (matplotlib bar chart, baseline vs. NammaTwin).

**Tests** `tests/A5/`
- Scenario JSONs validate against the schema.
- The eval runs offline on FakeLLM or cached evidence in under 60 s.
- The metrics function is verified on a hand-made 3-case set.

**DoD** `python -m backtest.eval` prints the metrics table and writes the chart.

---

## 5. Dev B track: data, tools, interfaces

### B1: Geo, DB, cluster detector
**Branch** `B1-geo-cluster` · **Files** `app/geo/*.py`, `app/db/*.py`, `app/cluster/detector.py`, `data/landmarks.csv` · **Depends on** P0

- `geo`: `latlon_to_cell(lat, lon, res=8)`, `neighbors(cell, k=2)`, `geocode(text, pin=None) -> (lat, lon, conf)` (pin first, then a fuzzy match on `landmarks.csv` via `rapidfuzz`).
- `db`: SQLAlchemy models plus `SqlTicketRepo`, `SqlIncidentRepo`, `SqlEvidenceRepo` implementing the Protocols exactly. SQLite in WAL mode.
- `cluster.detector.H3ClusterDetector.ingest(ticket)`: the incident rule is ≥ 4 tickets and ≥ 2 categories, or ≥ 8 of one category, in a 2-ring and 60-minute window. It attaches new tickets to an open incident, and re-investigation is debounced to one trigger per 5 minutes (returns a `reinvestigate: bool` flag on the Incident).
- Tickets use event time (`ticket.ts`), not wall-clock time, so replay works.

**Tests** `tests/B1/`
- The repo contract suite runs against both `InMemoryRepo` (from stubs) and `SqlRepo`.
- Feeding `tickets_bellandur_flood.json` opens exactly one incident at the expected ticket index.
- Boundary cases: 3 tickets means no incident, a cross-category threshold triggers, tickets outside the window or ring do not join, and the debounce works.

**DoD** `python -m app.cluster.replay tests/fixtures/tickets_bellandur_flood.json` prints incident-open events.

### B2: Tool layer (real plus simulated, cached)
**Branch** `B2-tools` · **Files** `app/tools/*.py`, `app/tools/_http.py` (cache client), `scripts/prefetch.py`, `data/hotspots.csv`, `data/cache/*.json` · **Depends on** P0 (the `@register_tool` decorator)

Each tool is one file and emits `Evidence` with `keys` from `EvidenceKey`:

| Tool | Source | Emits (examples) | Provenance |
|---|---|---|---|
| `rainfall.py` | Open-Meteo (forecast + archive) | `RAIN_GT_25/40`, `RAIN_LT_15/5`, `SUSTAINED_RAIN_24H`, `DRY_WEATHER` | real |
| `elevation.py` | SRTM raster or OpenTopoData, cached | `LOW_LYING` (cell below neighbour median) | real |
| `osm.py` | Overpass, cached | `NEAR_LAKE`, `LARGE_STP_SITE_NEARBY`; also returns the context dict for A3 | real |
| `history.py` | `TicketRepo.window` | `DEBRIS_TICKETS_NEARBY`, `POWER_TICKETS_PRECEDE_SEWAGE`, `LOCALIZED_SPREAD`, `LINEAR_SPREAD` | real (own data) |
| `hotspots.py` | `hotspots.csv` | `KNOWN_HOTSPOT` | derived |
| `outage_sim.py` | mock, scenario-driven | `OUTAGE_REPORTED` | **simulated** |
| `traffic.py` | TomTom free tier | `TRAFFIC_SLOWDOWN` | real (live) or simulated |

- `_http.py`: `get_json(url, params, cache_key)` returns a cached copy when `DEMO_MODE=1` or when the network fails. The cache is keyed by a hash and stored in `data/cache/`.
- `scripts/prefetch.py` pre-warms the caches for the 2-3 demo areas. Run it once and commit the JSONs.
- Thresholds (25 and 40 mm/hr, etc.) are constants in `app/tools/thresholds.py`.
- Each tool exposes `discriminates=[...]` in its `ToolSpec`.

**Tests** `tests/B2/`
- Every tool runs in DEMO_MODE against cached JSON and returns valid `Evidence`.
- Threshold unit tests: 26 mm/hr yields `RAIN_GT_25` and not `RAIN_GT_40`.
- Every emitted key is a member of `EvidenceKey`.
- `discover()` finds all tools, and each `ToolSpec` has a non-empty description.
- One opt-in live smoke test: `pytest -m live`.

**DoD** `python -m app.tools.cli rainfall --lat 12.93 --lon 77.68 --t0 ... --t1 ...` prints Evidence for every tool.

### B3: Intake (extract, STT, translate, vision, Telegram)
**Branch** `B3-intake` · **Files** `app/intake/{extract,stt,vision}.py`, `app/intake/telegram_bot.py`, `app/intake/pipeline.py` · **Depends on** B1 (geocode/cell), P0 LLM wrapper

- `extract.to_ticket(raw: RawInput) -> Ticket`: translate via Sarvam if `lang != en`, then `LLM.structured(TicketDraft)`, then geocode, then cell. Keep both original and English text.
- `stt.transcribe(ogg_bytes) -> (text, lang)` using ffmpeg, then Sarvam STT. In DEMO_MODE it returns a cached transcript by file hash.
- `vision.depth(photo_bytes) -> (bucket, conf)` with the multimodal LLM.
- `telegram_bot.py` handles text, voice, photo, and location pin, then posts a `Ticket` to the API's `POST /tickets` (HTTP), so the bot has no import coupling with A. Until A4 lands, it writes to the repo directly behind a `--direct` flag.
- Includes `scripts/seed_tickets.py` to replay a fixture JSON to the ingest endpoint at an accelerated rate (also used by the demo).

**Tests** `tests/B3/`
- `FakeLLM` plus cached STT: a Kannada transcript yields a Ticket with the right category and cell.
- The geocode fallback chain: pin, then gazetteer, then fuzzy match, then low confidence.
- Photo bucket mapping.
- The bot handler functions are tested with mocked Telegram `Update` objects, with no network.

**DoD** `python -m app.intake.cli --voice tests/fixtures/sample_kn.ogg` prints a validated Ticket JSON.

### B4: Dispatcher and citizen notifier
**Branch** `B4-dispatch` · **Files** `app/dispatch/{telegram,email,notifier,templates}.py` · **Depends on** P0

- `MultiChannelNotifier` implements `Notifier`. Routing table `dept → [telegram_chat_id, email]` comes from config.
- `templates.py`: department message (incident ID, map pin, action, evidence summary with provenance, confidence, approval stamp) and citizen status message in en/kn, rendered from templates, **not** the LLM, so it is deterministic. Optionally a Sarvam TTS voice reply.
- Idempotency: `Delivery` is keyed by `(incident_id, action_id, channel)`, so an approval retry never double-sends.
- `dry_run` mode writes to `data/outbox.jsonl` instead of sending.

**Tests** `tests/B4/`
- Template snapshots in en and kn.
- Idempotency: a second send is a no-op.
- Dry-run writes the expected JSONL.
- The channel failure path degrades to the other channel and records an error in `Delivery`.

**DoD** `python -m app.dispatch.cli --incident-fixture ... --dry-run` prints the outbound messages.

### B5: Streamlit UI
**Branch** `B5-ui` · **Files** `ui/streamlit_app.py`, `ui/components/*.py`, `ui/api_client.py`, `ui/mock_api.py` · **Depends on** `docs/openapi.json` (from A4). Until A4 lands, use `ui/mock_api.py` (a FastAPI app serving fixture JSON on the same routes).

- Layout: left is the ticket feed (language flag, category chip, synthetic tag). Center is the pydeck `H3HexagonLayer` ticket density plus incident outline plus hospital/school markers. Right is the Investigator panel: SSE-fed hypothesis bars updating per step, evidence list with REAL/SIMULATED/DERIVED badges, the Dossier, and actions with Approve/Edit/Reject and a priority breakdown. A bottom "Impact" tab reads `docs/eval_results.json` and the chart.
- A "fast-forward 45 min" button calls the verify endpoint.
- Only `ui/api_client.py` touches HTTP. Components take plain Pydantic models.

**Tests** `tests/B5/`
- `streamlit.testing.v1.AppTest` smoke test against `mock_api`.
- Component functions unit-tested with fixture models: the badge mapping, and the bars sorted by posterior.
- The SSE client parses a recorded event stream.

**DoD** `make run-ui-mock` renders the full dashboard from fixtures with no backend.

---

## 6. Joint phases

### I1: Integration (replace the stubs)
**Branch** `I1-integrate` · **Both devs, one laptop drives**

1. Wire real implementations into the API's dependency container (`app/api/deps.py`): `SqlRepo`, `H3ClusterDetector`, `discover()` registry, `MultiChannelNotifier`.
2. Run `tests/e2e/test_pipeline.py` with `DEMO_MODE=1`: seed tickets → incident → investigator uses real tool code on cached data → dossier → approve → outbox → fast-forward → `resolving`.
3. Point the UI at the real API. Point the bot at `POST /tickets`.
4. Fix mismatches. Any contract change is a tiny PR on `app/contracts/` that both approve.

**DoD** One scripted command, `make demo`, runs the full flow end to end, offline and cached.

### I2: Hardening, deploy, submission
- Run the happy path three times from a clean clone. Record the 2-3 min video. Finish the 5-slide deck, README, and `docs/data_provenance.md` (real vs. simulated).
- Deploy: API plus bot on Render or Railway, UI on Streamlit Cloud, with `DEMO_MODE` fallback and the local video as a backup.
- Feature freeze before the final hour. Submit well before the 9 PM deadline (submissions open at 8 PM).

---

## 7. Suggested timing (12 h)

| Hours | Dev A | Dev B |
|---|---|---|
| 0-1 | **P0 together** | **P0 together** |
| 1-2.5 | A1 → A2 start | B1 |
| 2.5-5 | A2 → A3 | B2 |
| 5-7 | A4 | B3 |
| 7-8.5 | A5 | B4 → B5 start |
| 8.5-9.5 | A5 finish | B5 finish |
| 9.5-11 | **I1** | **I1** |
| 11-12 | **I2** | **I2** |

**If behind:** cut in this order: A4's Verifier beyond `assess()` plus the button → B3 vision/TTS → B4 email channel → `traffic.py`. **Never cut:** A1/A2 loop, the rainfall and elevation tools, HITL approval, and provenance badges.

---

## 8. What was removed or merged as redundant

- **Separate "Verifier" phase** is now part of A4, because the Verifier is a pure `assess()` function plus an endpoint.
- **Separate "Citizen notifier" and "Dispatcher"** are merged into B4, since they share the Notifier and templates.
- **Separate "Officer console" phase** is merged into A4 (the interrupt and decision endpoint) and B5 (the UI).
- **Separate "data/geo" and "cluster" phases** are merged into B1, since the cluster detector depends on the same H3 and repo code.
- **Separate "Observability" phase** is dropped. Enable Langfuse by setting two env vars in `config.py`, which takes about 10 minutes inside A2.

I can also put this into a `BUILD_PLAN.md` file, or write the P0 `models.py`, `keys.py`, and `interfaces.py` in full, if you want to start the pair session now.

Powered by Claude Exporter (https://www.ai-chat-exporter.net)
