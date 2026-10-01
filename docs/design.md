# CrossWire Design Specification & Stitch Prototype Blueprint

> **System Name:** CrossWire (NammaTwin Incident Intelligence)  
> **Target Platform:** Google Stitch (`stitch.withgoogle.com`) & Production Frontend  
> **Archetype:** Tactical Dark-Vector Telemetry & Geospatial Mission Hub  
> **Aesthetic Dials:** `DESIGN_VARIANCE: 7` | `MOTION_INTENSITY: 6` | `VISUAL_DENSITY: 8`  
> **Formatting Rules:** Strictly zero emojis, WCAG AA compliant contrast, no generic AI-purple gradients, no default Inter/Fraunces fonts.

---

## 1. Quick-Copy Master Prompt for Google Stitch

```text
Create a high-density, mission-critical incident command and digital twin console named "CrossWire". The system turns scattered citizen complaints into cross-department urban emergency incidents, autonomously investigates root causes using real public signals (rainfall, elevation, drainage networks), and provides a Human-In-The-Loop (HITL) dispatch cockpit for municipal officers.

Visual Style: Tactical Dark-Vector Telemetry (think Palantir Gotham, defense flight decks, and Bloomberg Terminal ergonomics). Dark obsidian background (#0B0D11), deep slate panels (#12161F), hairline slate borders (#242D3D), with sharp telemetry accents in Tactical Amber (#F59E0B), Telemetry Cyan (#06B6D4), Critical Red (#EF4444), and Resolved Emerald (#10B981). Typography uses geometric sans-serif for headlines (Cabinet Grotesk style) and monospaced font for telemetry, timestamps, and coordinates (JetBrains Mono style). Absolutely no generic purple gradients, no soft blurry drop shadows, and no emojis.

Layout Architecture: A full-viewport widescreen 3-pane dashboard with an ultra-compact 56px top header:
1. Top Header: Brand mark "CROSSWIRE", live Incident ID (#INC-892), severity badge "P1 CRITICAL", location tag "Bellandur Catchment / Ward 150", and operational status "AUTONOMOUS LOOP: STEP 4/6".
2. Left Pane (25% width - Sensor Ingestion Stream): Real-time citizen ticket feed. Top card is an expanded multimodal ticket showing: a flood photo with computer vision depth bounding box ("WATER_DEPTH: 45-60cm [Conf: 0.92]"), an audio waveform player for a Kannada citizen voice report with side-by-side Sarvam STT Kannada transcript and verified English translation ("Drain overflowing near Green Glen layout"), followed by compact incoming ticket rows with category badges (DRAINAGE, SEWAGE, POWER, TRAFFIC).
3. Center Pane (45% width - Geospatial Digital Twin): A dark vector map canvas (Carto Dark style) showing the urban layout. The active incident H3 hexagonal cell (resolution 8) is illuminated with a cyan/amber glowing border. Surrounding k=2 ring cells are shaded with heat opacity based on ticket density. Layered over the map are elevation depression contours showing the low-lying catchment, illuminated vector lines tracing the Rajakaluve stormwater drainage network draining into Bellandur Lake, and distinct geometric markers for vulnerable infrastructure (Government High School, Columbia Asia Hospital, 66kV BESCOM Substation). Includes a bottom temporal scrubber slider from T-180m to NOW.
4. Right Pane (30% width - Autonomous Investigator & Officer Cockpit): Top section shows the Bayesian Hypothesis Ranking with horizontal posterior probability bars (RAIN_OVERWHELM: 82% leading, DRAIN_BLOCKAGE: 12%, POWER_LED_STP_OVERFLOW: 6%). Middle section contains the Evidence Ledger with color-coded provenance tags: [REAL] Open-Meteo Rainfall (42.8 mm/hr), [REAL] OpenTopoData Elevation (884m vs 896m median - Low Lying), [DERIVED] Ticket Velocity (8 tickets in 30 mins), and [SIMULATED] BESCOM Outage Feed (Substation Feeder 4 Tripped). Bottom section is the HITL Dispatch Card with actionable multi-department recommendations (BWSSB 50HP dewatering pumps, BTP traffic diversion at ORR, BBMP storm drain clearance) with prominent high-contrast buttons: "Approve and Dispatch", "Edit Rationale", and "Reject".
```

---

## 2. Design System Tokens & Style Variables

### 2.1 Color Palette
The console enforces an authoritative, monochromatic dark telemetry base with deliberate signal colors. Pure black and muddy grays are banned.

| Token | Hex Value | RGB | Purpose |
| :--- | :--- | :--- | :--- |
| `surface-canvas` | `#0B0D11` | `11, 13, 17` | Root background canvas, gutters |
| `surface-panel` | `#12161F` | `18, 22, 31` | Card containers, sidebar docks, canvas wrappers |
| `surface-elevated` | `#181E2B` | `24, 30, 43` | Popovers, active cell inspectors, hover states |
| `border-subtle` | `#242D3D` | `36, 45, 61` | Hairline panel borders, 1px structural separators |
| `border-active` | `#3B82F6` | `59, 130, 246` | Active selection rings, focused inputs |
| `text-primary` | `#F1F5F9` | `241, 245, 249`| Section headlines, key metrics (WCAG 14.5:1) |
| `text-secondary` | `#94A3B8` | `148, 163, 184`| Field labels, secondary descriptions, timestamps |
| `text-muted` | `#64748B` | `100, 116, 139`| Inactive indicators, table headers |
| `signal-amber` | `#F59E0B` | `245, 158, 11` | P1 incident warnings, active investigating status |
| `signal-red` | `#EF4444` | `239, 68, 68` | Cascading failure, toxic sewage spill, emergency alert |
| `signal-cyan` | `#06B6D4` | `6, 182, 212` | Sensor feeds, H3 hexagon outlines, water vectors |
| `signal-emerald` | `#10B981` | `16, 185, 129`| Provenance verified, closed loops, dispatch success |

### 2.2 Typography Specifications
* **Display & Primary Headlines:** `Cabinet Grotesk` (or fallback `Outfit`, weights 700 Bold, 800 Heavy).
  * Headline H1: `28px` (`1.75rem`), letter-spacing `-0.02em`, line-height `1.15`.
  * Headline H2: `18px` (`1.125rem`), letter-spacing `-0.01em`, line-height `1.2`.
  * Headline H3: `14px` (`0.875rem`), letter-spacing `0.02em`, uppercase, weight 700.
* **Body & Explanatory Text:** `Satoshi` (weights 400 Regular, 500 Medium).
  * Body Standard: `13px` (`0.8125rem`), line-height `1.5`, color `#CBD5E1`.
  * Body Small: `11px` (`0.6875rem`), line-height `1.4`, color `#94A3B8`.
* **Telemetry, Metrics & Machine Identifiers:** `JetBrains Mono` (weights 500 Medium, 600 SemiBold).
  * Metrics Large: `20px` (`1.25rem`), tabular numerals, weight 600.
  * Telemetry Labels: `11px` (`0.6875rem`), uppercase, letter-spacing `0.05em`.
  * Coordinates & Hashes: `10.5px` (`0.656rem`), letter-spacing `0.02em`.

### 2.3 Component Geometry & Spacing
* **Corner Radius:** Strict `rounded-md` (`6px`) across all cards, inputs, and interactive surfaces. No pill shapes except small metadata chips (`rounded-full` for 20px tags).
* **Border Philosophy:** No drop shadows on dark backgrounds. Depth is achieved via `1px solid #242D3D` hairline borders and subtle background elevation.
* **Density:** High visual density with `p-3` to `p-4` internal padding, enabling officers to absorb critical situational metrics without vertical scrolling.

---

## 3. Screen Structure & Layout Grid

```
+-------------------------------------------------------------------------------------------------------------------------+
| TOP NAVIGATION BAR (56px fixed height)                                                                                  |
| [LOGO: CrossWire] | Incident #INC-892 | [P1 CRITICAL] | Ward 150 Bellandur | Loop: Step 4/6 (Investigating) | [DEMO MODE]|
+-----------------------------+---------------------------------------------------------+---------------------------------+
| COLUMN 1: INGESTION (25%)   | COLUMN 2: GEOSPATIAL DIGITAL TWIN (45%)                 | COLUMN 3: INVESTIGATOR (30%)    |
|                             |                                                         |                                 |
| 1. Feed Status Header       | 1. Map Canvas Toolbar (Layers: Terrain, Drains, Assets) | 1. Hypothesis Posterior Stack   |
| 2. Expanded Multimodal Card | 2. Vector Basemap (Carto Dark)                          |    - RAIN_OVERWHELM (82%)       |
|    - Photo + Depth BBox     |    - H3 Hexagonal Resolution-8 Cluster (k=2)            |    - DRAIN_BLOCKAGE (12%)       |
|    - Audio Waveform Scrubber|    - Elevation Basin Contours                           |    - STP_OVERFLOW (6%)          |
|    - Dual Lang (KN / EN)    |    - Stormwater Rajakaluve Vectors                      | 2. Evidence Ledger              |
| 3. Chronological Mini-Cards |    - Critical Anchor Markers (Hospitals/Schools)        |    - [REAL] Open-Meteo          |
|    - Category Badges        | 3. Temporal Playback Controller                         |    - [REAL] Elevation           |
|    - Time Elapsed & Channel |    - T-180m Scrub Slider with Rainfall Bar Chart Overlay|    - [SIMULATED] Outage Feed    |
|                             | 4. Active Cell Telemetry Ribbon                         | 3. Officer HITL Action Deck     |
|                             |    (Centroid: 12.9352N, 77.6821E | Elev: 884m)         |    - Multi-Dept Directives      |
|                             |                                                         |    - [APPROVE] [EDIT] [REJECT]  |
+-----------------------------+---------------------------------------------------------+---------------------------------+
| BOTTOM SYSTEM BAR (32px fixed height)                                                                                   |
| Engine: LangGraph v2.4 | LLM: Gemini 3.8 Flash | Trace: tr-881290 | STT: Sarvam AI | Geo: H3 Res-8 | WAL: SQLite       |
+-------------------------------------------------------------------------------------------------------------------------+
```

---

## 4. Detailed Component Specifications

### 4.1 Top Navigation Bar (56px)
* **Brand Cluster:** Left-aligned bold wordmark `CROSSWIRE` with an inline glowing signal beacon (6px cyan dot).
* **Incident Target Chip:** `Incident #INC-892` rendered in `JetBrains Mono` with a high-contrast danger badge `P1 CRITICAL` (background `#450A0A`, border `#B91C1C`, text `#FCA5A5`).
* **Location Descriptor:** `Bellandur Gate / Outer Ring Road Corridor (Ward 150)`.
* **Autonomous Engine Status:** Pulse indicator displaying `INVESTIGATOR LOOP: STEP 4 OF 6` with confidence delta indicator `Gap: +0.70 (Converging)`.
* **Mode Switch & User:** Right-aligned `DEMO MODE (CACHED)` pill badge in muted slate, alongside the active officer badge (`Cmdr. R. Sharma - BBMP Central`).

### 4.2 Column 1: Ingestion & Telemetry Stream (25% Width)
* **Section Title:** `CITIZEN SENSOR INTAKE` (11px uppercase mono, tracking 0.05em).
* **Multimodal Ticket Card (Active Focus):**
  * Container: Background `#12161F`, border `1px solid #3B82F6` (highlighted active ticket).
  * Header: `Ticket #TK-4821` | `Telegram Voice & Photo` | `3 mins ago`.
  * Visual Inspector: Photo thumbnail showing waterlogged road with a technical green bounding overlay: `CV DEPTH: 45-60cm (Confidence: 0.92)`.
  * Voice Audio Player: Dark audio waveform strip with play/pause toggle, timecode `0:14 / 0:28`, and a language tag `Kannada (Native)`.
  * Bilingual Transcription Card:
    * Kannada (Sarvam STT): `ಬೆಳ್ಳಂದೂರು ಗೇಟ್ ಬಳಿ ರಾಜಕಾಲುವೆ ನೀರು ರಸ್ತೆಗೆ ನುಗ್ಗಿದೆ, ವಾಹನಗಳು ಮುಳುಗಿವೆ.`
    * English (Verified): `"Storm drain near Bellandur Gate is overflowing onto the main road. Multiple vehicles submerged."`
  * Geocode Tag: `12.9352° N, 77.6821° E` attached to H3 cell `88618925d3fffff`.
* **Compact Ticket Queue (3 Items):**
  * `Ticket #TK-4819`: `SEWAGE_OVERFLOW` | `Manhole bubbling black water near Green Glen` | `T-12m`.
  * `Ticket #TK-4814`: `POWER_OUTAGE` | `Transformer spark followed by blackout` | `T-22m`.
  * `Ticket #TK-4809`: `TRAFFIC_GRIDLOCK` | `ORR stationary from Iblur to Ecospace` | `T-31m`.

### 4.3 Column 2: Geospatial Digital Twin Canvas (45% Width)
* **Map Container:** Full-height container with MapLibre GL / Carto Dark Matter rendering.
* **Canvas Toolbar (Top Overlay):** Floating pill controls for layer toggling:
  * `Elevation (Low-lying Basins)`: Enabled (contour glow).
  * `Rajakaluve Drainage`: Enabled (cyan directional animated dashed vectors).
  * `Vulnerability Nodes`: Enabled (Hospital, School, Substation pins).
* **H3 Hexagon Geometry Overlay:**
  * Primary Incident Hexagon (`88618925d3fffff`): Centered over Bellandur junction. Stroke `2px solid #06B6D4`, fill `rgba(6, 182, 212, 0.25)`.
  * Neighboring K-Ring Hexagons (18 cells): Opacity dynamically weighted by ticket density (`rgba(245, 158, 11, 0.15)` to `rgba(239, 68, 68, 0.35)`).
* **Downstream Hydrological Vector:** A sharp, glowing cyan line tracing the canal route from Bellandur junction culvert toward Bellandur Lake inlet, with a warning icon at the culvert choke-point.
* **Vulnerable Anchor Pins:**
  * Square marker: `Columbia Asia Hospital` (`420m NW - Access Road Flooded`).
  * Square marker: `Govt. Primary School Ward 150` (`310m S - Safe / High Ground`).
  * Square marker: `66kV BESCOM Substation` (`180m E - Water Ingress Alert`).
* **Temporal Scrub Bar (Bottom Overlay):**
  * Slider tracking `T-180m` to `LIVE`.
  * Synchronized micro-histogram showing rainfall precipitation intensity peaks (`42.8 mm/hr` peak at `T-45m`).

### 4.4 Column 3: Autonomous Investigator & HITL Cockpit (30% Width)
* **Section Title:** `INVESTIGATION & DISPATCH COCKPIT` (11px uppercase mono).
* **Bayesian Hypothesis Ranking:**
  * Card displaying real-time convergence:
    * `RAIN_OVERWHELM`: Horizontal progress bar at `82%` (`bg-amber-500`), score `P = 0.82`, trend indicator `+0.34`.
    * `DRAIN_BLOCKAGE`: Horizontal progress bar at `12%` (`bg-slate-600`), score `P = 0.12`, trend indicator `-0.20`.
    * `POWER_LED_STP_OVERFLOW`: Horizontal progress bar at `6%` (`bg-slate-700`), score `P = 0.06`.
* **Evidence Ledger (Verified Tool Output Stack):**
  * `[REAL]` Open-Meteo Tool: `RAIN_GT_40` | `42.8 mm/hr sustained precipitation (Threshold: 40.0)`.
  * `[REAL]` Elevation Tool: `LOW_LYING` | `Elevation 884m (12m below local 2-ring median 896m)`.
  * `[DERIVED]` History Tool: `DEBRIS_TICKETS_NEARBY` | `5 uncollected waste tickets in culvert radius past 48h`.
  * `[SIMULATED]` Outage Feed: `FEEDER_TRIP` | `Feeder 4 tripped at T-20m (Automated sensor trip)`.
* **Human-In-The-Loop Action Desk:**
  * Banner: `ACTION PLAN PROPOSED (Confidence: 0.82 >= Threshold: 0.75)`.
  * Directives List:
    1. `BWSSB`: Dispatch 2x 50HP mobile dewatering diesel pumps to Bellandur culvert.
    2. `BTP (Traffic)`: Implement immediate vehicle diversion at Iblur flyover toward Sarjapur road.
    3. `BBMP SWM`: Deploy rapid emergency crew for debris clearance at culvert inlet grate.
  * Dispatch Preview Drawer: Shows bilingual Kannada/English citizen alert notification ready for broadcast to 342 subscribed ward residents.
  * Decision Button Bar:
    * `Approve & Dispatch`: Solid high-contrast emerald button (`bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold px-4 py-2.5 rounded-md`).
    * `Edit Plan`: Secondary outlined button (`border border-slate-600 text-slate-200 px-3 py-2.5 rounded-md`).
    * `Reject / Re-investigate`: Danger ghost button (`text-red-400 hover:bg-red-950/40 px-3 py-2.5 rounded-md`).

---

## 5. Mock Data & Microcopy Dictionary

Use these exact strings in Stitch for 100% authentic domain fidelity:

```json
{
  "incident": {
    "id": "INC-892",
    "name": "Bellandur Gate / ORR Drainage Inundation",
    "ward": "Ward 150 - Bellandur",
    "severity": "P1_CRITICAL",
    "status": "INVESTIGATING",
    "step_count": 4,
    "max_steps": 6,
    "confidence": 0.82,
    "primary_h3": "88618925d3fffff"
  },
  "hypotheses": [
    { "id": "RAIN_OVERWHELM", "name": "Heavy Rain Overwhelming Natural Basin", "posterior": 0.82, "status": "LEADING" },
    { "id": "DRAIN_BLOCKAGE", "name": "Solid Waste Blockage at Culvert", "posterior": 0.12, "status": "DISPROVED_PRIMARY" },
    { "id": "POWER_LED_STP_OVERFLOW", "name": "Substation Failure Halting STP Pumps", "posterior": 0.06, "status": "LOW_PROBABILITY" }
  ],
  "evidence": [
    { "id": "EV-01", "source": "Open-Meteo Radar", "key": "RAIN_GT_40", "value": "42.8 mm/hr", "provenance": "REAL" },
    { "id": "EV-02", "source": "SRTM / OpenTopoData", "key": "LOW_LYING", "value": "884m (-12m depression)", "provenance": "REAL" },
    { "id": "EV-03", "source": "Ticket History Engine", "key": "DEBRIS_TICKETS_NEARBY", "value": "5 tickets in 48h", "provenance": "DERIVED" },
    { "id": "EV-04", "source": "BESCOM SCADA Stream", "key": "FEEDER_TRIP", "value": "Feeder 4 offline", "provenance": "SIMULATED" }
  ],
  "actions": [
    { "dept": "BWSSB", "order": 1, "task": "Deploy 2x 50HP mobile suction pumps to Bellandur Gate culvert." },
    { "dept": "BTP", "order": 2, "task": "Divert westbound ORR traffic at Iblur Flyover to Sarjapur Road." },
    { "dept": "BBMP", "order": 3, "task": "Emergency clearing of solid waste grating at secondary stormwater inlet." }
  ],
  "kannada_strings": {
    "voice_transcript": "ಬೆಳ್ಳಂದೂರು ಗೇಟ್ ಬಳಿ ರಾಜಕಾಲುವೆ ನೀರು ರಸ್ತೆಗೆ ನುಗ್ಗಿದೆ, ವಾಹನಗಳು ಮುಳುಗಿವೆ.",
    "citizen_sms": "ನಿಮ್ಮ ವಾರ್ಡ್ 150 ರ ಬೆಳ್ಳಂದೂರು ಗೇಟ್‌ನಲ್ಲಿ ನೀರಿನ ನಿಲುಗಡೆ ವರದಿಯಾಗಿದೆ. ಬಿಡಬ್ಲ್ಯೂಎಸ್‌ಎಸ್‌ಬಿ ಪಂಪ್‌ಗಳನ್ನು ನಿಯೋಜಿಸಲಾಗಿದೆ. ಪರ್ಯಾಯ ಮಾರ್ಗ ಬಳಸಿ."
  }
}
```

---

## 6. Pre-Flight Verification & Strict Prohibitions

Before submitting to Stitch or deploying code, verify that:
1. **Zero Emojis:** No emoji symbols exist in labels, headers, or mock feeds. Iconography relies strictly on SVG outlines (`@phosphor-icons/react` or `@tabler/icons-react`).
2. **No Purple AI Clichés:** No `#8B5CF6`, `#A855F7`, or radial neon glows. Surfaces remain strictly Obsidian `#0B0D11`, Panel `#12161F`, and Border `#242D3D`.
3. **No Unconstrained Headlines:** H1 container is constrained with `max-w-5xl` to prevent 4-line wrapping.
4. **Button Readability:** Every button label has at least a 7:1 contrast ratio against its button background.
5. **No Blind Grid Spaces:** CSS grid components utilize `grid-auto-flow: dense` with mathematically interlocking spans.
