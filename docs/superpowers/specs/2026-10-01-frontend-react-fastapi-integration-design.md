# CrossWire Production Frontend: React + TypeScript + FastAPI Integration Design

> **Topic:** CrossWire Production Frontend (React 19 + TypeScript + Vite) connecting to FastAPI & LangGraph  
> **Date:** 2026-10-01  
> **Status:** Validated Design Spec  
> **Design Philosophy:** Editorial Minimalist Architecture (`minimalist-ui`) + Award-Winning Frontend Engineering (`gpt-taste`)  
> **Color System:** Warm Monochrome (Canvas `#FBFBFA`, Surface `#FFFFFF`, Hairline `#EAEAEA`, Accent Border `#111111`, Muted `#57606A`)  
> **Banned:** Developer convenience placeholder buttons (`assets.html`, `🎨 City Assets`), decorative fake filler cards, emojis in code/labels, cheap meta-labels ("SECTION 01").

---

## 1. System Architecture & Directory Layout (Approach 1: Integrated Monorepo)

The repository integrates a dedicated `frontend/` single-page application communicating with the existing FastAPI backend (`app/api/main.py`) via Vite's proxy during local development and direct container / CDN serving in production.

```text
E:\CrossWire/
├── app/                              # Python 3.12+ FastAPI & LangGraph Backend
│   ├── api/
│   │   ├── main.py                   # REST endpoints: /incidents, /tickets, /decision, /verify, /stream
│   │   └── schemas.py                # Pydantic request/response schemas
│   ├── contracts/
│   │   ├── models.py                 # Ticket, Incident, Evidence, Dossier, Action, Decision
│   │   └── keys.py                   # HypothesisID, EvidenceKey
│   └── investigator/                 # Multi-agent LangGraph workflow
│
├── frontend/                         # React 19 + TypeScript + Vite Application
│   ├── package.json                  # Dependencies: react, @gsap/react, gsap, lucide-react, leaflet
│   ├── vite.config.ts                # Reverse proxy /api and /incidents to localhost:8000
│   ├── tsconfig.json                 # Strict TypeScript configuration
│   ├── tailwind.config.js            # Design tokens (Newsreader, Plus Jakarta Sans, JetBrains Mono)
│   ├── index.html                    # Root HTML mount with zero-fluff editorial typography
│   └── src/
│       ├── main.tsx                  # React DOM root
│       ├── App.tsx                   # Top-level state coordinator & 4-stage sequential controller
│       ├── types/api.ts              # TypeScript mirrors of backend Pydantic models
│       ├── api/
│       │   ├── client.ts             # Fetch client for REST endpoints
│       │   └── stream.ts             # EventSource wrapper for /incidents/{id}/stream
│       ├── components/
│       │   ├── nav/
│       │   │   └── HeaderNav.tsx     # Clean header: Vidhana Soudha crest, status badge, stage tabs
│       │   ├── reports/
│       │   │   ├── CitizenReports.tsx # Triage queue, Kannada audio statement, depth estimation
│       │   │   └── ReportCard.tsx    # Individual ticket card with severity and status
│       │   ├── map/
│       │   │   └── CityFloodMap.tsx  # Architectural grayscale Leaflet map with H3 flood polygon
│       │   ├── cause/
│       │   │   ├── CauseAnalysis.tsx # Dynamic Bayesian hypothesis bars (GSAP animated)
│       │   │   └── EvidenceList.tsx  # Provenance badges (REAL / SIMULATED / DERIVED)
│       │   └── dispatch/
│       │       ├── DispatchConsole.tsx # Municipal directives (BWSSB, BBMP, Traffic Police)
│       │       └── ActionOrderCard.tsx # HITL decision toggle & authorization button
│       └── styles/
│           └── index.css             # Tailwind base and editorial typography rules
│
└── Makefile                          # dev-api, dev-frontend, dev (both concurrently)
```

---

## 2. API Contract & Live Data Binding

| Frontend Component | Backend Endpoint | HTTP Method / Transport | Bound Data Attributes |
| :--- | :--- | :--- | :--- |
| `HeaderNav` | `/incidents` | `GET` | Incident ID, status badge, cell count, time opened |
| `CitizenReports` | `/incidents/{id}` | `GET` | Associated tickets: `text_original`, `text_en`, `photo_depth`, `lang`, `severity` |
| `CityFloodMap` | `/incidents/{id}` | `GET` | `centroid` `[lat, lon]`, `cells` (H3 index strings), OSM waterway vectors |
| `CauseAnalysis` | `/incidents/{id}` | `GET` & `/incidents/{id}/stream` (SSE) | Dossier `ranked` tuples `[(HypothesisID, probability)]`, `evidence` list with `provenance` |
| `DispatchConsole` | `/incidents/{id}/decision` | `POST` | Dispatches HITL `Decision` (`approved=True/False`, `modified_actions`) |
| `FastForwardAction` | `/incidents/{id}/verify?fast_forward_min=45` | `POST` | Drainage reassessment result, new incident status |

### Handling Zero-Data State (No Fluff)
When the backend returns an empty incident list or zero tickets:
* Display an authentic, understated operational state card: *"System Operational · Listening to 112/Ward feeds. No active high-severity flood clusters detected."*
* Never generate fake placeholder cards, fake stock metrics, or dummy developer SVG links.

---

## 3. Strict Elimination of Developer Convenience Fluff

In compliance with explicit user priority:
1. **Removed:** Any links or buttons referencing `assets.html` or `🎨 City Assets`.
2. **Removed:** Navigation shortcuts labeled `Bangalore Assets →`.
3. **Removed:** Decorative placeholder buttons that lack active backend data roles.
4. **Removed:** Cheap meta-labels (e.g., "QUESTION 05", "SECTION 01", "STEP 04").
5. **Enforced:** Pure operational civic workflow: Citizen Reports → Spatial Basin Map → Root Cause Investigation → Municipal Dispatch Orders.

---

## 4. UI/UX Design System & Motion Engineering (`gpt-taste`)

### 4.1 Layout & Visual Hierarchy
* **Canvas:** Warm off-white (`#FBFBFA`) avoiding sterile bright white or dark-mode obsidian.
* **Containers:** Solid white (`#FFFFFF`) framed with 1px hairline borders (`#EAEAEA`).
* **Active State:** Distinctive 2.5px solid black border (`#111111`) representing active focus and selection.
* **Typography:**
  * Editorial Serif: *Newsreader* (bold italic titles and executive quotes).
  * Body Sans: *Plus Jakarta Sans* (high legibility at 13-14px).
  * Data/Code: *JetBrains Mono* (coordinates, H3 hex addresses, timestamps, probabilities).

### 4.2 Bento Grid Execution (`grid-flow-dense`)
All multi-card sections (reports overview and evidence items) enforce `grid-flow-dense` with strict column spans (`col-span-12`, `md:col-span-8`, `md:col-span-4`) ensuring zero dead voids or orphaned grid gaps.

### 4.3 GSAP Motion Specification (`@gsap/react`)
* **Component Entrance:** Coordinated timeline with `stagger: 0.08` and `ease: "power2.out"`.
* **Probability Bar Transitions:** Real-time tweening on Bayesian probability values as SSE events stream from LangGraph investigator nodes.
* **Clean Cleanup:** All animations scoped inside React's `useGSAP` hook for zero memory leaks.

---

## 5. Verification & Acceptance Criteria

1. **Frontend Builds Cleanly:** `npm run build` succeeds without TypeScript or Tailwind errors.
2. **Vite Development Proxy Works:** `GET /incidents` returns live data from FastAPI at `http://localhost:5173/api/incidents`.
3. **Fluff Removed:** Zero references to `assets.html` or developer asset vault buttons exist in the code.
4. **All 4 Stages Functional:**
   - Citizen reports show Kannada text and English translation.
   - Grayscale map renders incident centroid and H3 boundary.
   - Hypothesis bars reflect actual backend dossier ranking.
   - Dispatch button issues verified POST to `/incidents/{id}/decision`.
