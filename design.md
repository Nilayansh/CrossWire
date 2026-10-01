# CrossWire Design Specification: Editorial Minimalist Architecture

> **System Name:** CrossWire (NammaTwin Incident Intelligence)  
> **Target Platform:** Google Stitch (`stitch.withgoogle.com`) & Production Frontend  
> **Design Philosophy:** Premium Utilitarian Minimalism & Editorial Document Architecture (`minimalist-ui`)  
> **Color Model:** Warm Monochrome + Muted Spot Pastels  
> **Base Canvas:** Pure White (`#FFFFFF`) / Bone (`#FBFBFA`)  
> **Strict Bans:** Zero neon glows, zero dark obsidian/cyberpunk themes, zero heavy drop shadows, zero emojis, zero AI copywriting clichés.

---

## 1. Copy-Paste Master Prompt for Google Stitch

```text
Design a clean, ultra-minimalist, editorial-style incident command console called "CrossWire". The system unifies scattered citizen complaints into cross-department urban emergency incidents, calculates spatial root causes using real public signals (rainfall, elevation, drainage infrastructure), and provides a Human-In-The-Loop (HITL) approval desk for municipal coordinators.

Aesthetic & Theme:
Warm monochrome and editorial workspace minimalism (inspired by Linear, Notion, and Swiss architectural planning sheets).
- Background Canvas: Warm Off-White / Bone (#FBFBFA).
- Surface Containers: Pure White (#FFFFFF) with crisp 1px hairline borders (#EAEAEA). Absolutely no heavy drop shadows or 3D elevation.
- Typography: High-contrast typography featuring Geist Sans for headers and body copy, with Geist Mono for coordinates, timestamps, and metric values. Primary text is Off-Black (#111111), and secondary text is Muted Slate (#787774).
- Color Accents: Color is used as a scarce semantic resource using desaturated, washed-out muted pastels only:
  * Pale Amber: #FBF3DB (Text: #956400) for active investigation status.
  * Pale Red: #FDEBEC (Text: #9F2F2D) for P1 critical severity tags.
  * Pale Green: #EDF3EC (Text: #346538) for real evidence provenance and approved dispatch.
  * Pale Blue: #E1F3FE (Text: #1F6C9F) for hydrological and sensor tags.
- Banned: No dark mode, no obsidian backgrounds, no neon glows, no gradients, and strictly no emojis.

Layout & Component Structure (3-Column Layout with 56px Top Header):
1. Top Header: Minimal 56px white navigation bar with 1px bottom border. Left side features the clean brandmark "CrossWire", Incident identifier "Incident #892", a Pale Red pill tag "P1 CRITICAL", and location "Ward 150 Bellandur". Right side features a quiet status tag "INVESTIGATOR: STEP 4 OF 6" and a solid black user profile button.
2. Left Column (25% width - Citizen Sensor Ingestion): Vertical feed of incoming citizen reports. The active report card contains:
   * Photo preview with a simple hairline bounding box and clean label "Water Depth: 45-60 cm (Conf: 0.92)".
   * Minimal audio player with a light gray waveform bar, playback timer "0:14 / 0:28", and tag "Kannada Voice".
   * Side-by-side transcripts: native Kannada ("ಬೆಳ್ಳಂದೂರು ಗೇಟ್ ಬಳಿ ರಾಜಕಾಲುವೆ ನೀರು ರಸ್ತೆಗೆ ನುಗ್ಗಿದೆ, ವಾಹನಗಳು ಮುಳುಗಿವೆ") and clean English translation ("Storm drain near Bellandur Gate overflowing onto road. Vehicles submerged.").
   * Followed by clean, flat queue items with 1px border dividers.
3. Center Column (45% width - Architectural Spatial Canvas): A light, paper-toned vector map (Carto Positron / OpenStreetMap Light style). Crisp, thin charcoal line boundaries for the primary H3 hexagon cell (resolution 8) over Bellandur junction. Neighboring k=2 rings shown in faint translucent washes. Delicate vector lines tracing the Rajakaluve drainage path toward Bellandur Lake, and clean square geometric icons marking critical facilities (Columbia Asia Hospital, Ward 150 School, BESCOM Substation). Bottom contains a minimalist horizontal time scrubber slider from T-180m to LIVE with a micro bar-chart of rainfall intensity.
4. Right Column (30% width - Autonomous Investigator & Action Desk):
   * Root Cause Hypotheses: Clean horizontal probability bars with light pastel fills: "Heavy Rain Overwhelm: 82%", "Drain Blockage: 12%", "Power-STP Outage: 6%".
   * Evidence Ledger: Table-style list with 1px bottom borders and muted pastel provenance tags: [REAL] Open-Meteo Rainfall (42.8 mm/hr), [REAL] OpenTopoData Elevation (884m, -12m depression), [DERIVED] Ticket Velocity (8 tickets / 30m), [SIMULATED] Feeder Outage.
   * Multi-Department Action Deck: Departmental action cards (BWSSB dewatering pumps, BTP traffic diversion, BBMP culvert clearing).
   * Primary Action Button: High-contrast solid black button (#111111) with white text "Approve & Dispatch", paired with a secondary white button with gray border "Edit Plan".
```

---

## 2. Color System & Visual Hierarchy

Color is strictly treated as an informational signal. Surfaces remain neutral, warm, and paper-like.

### 2.1 The Palette Architecture

| Role | Hex Code | Purpose | Contrast Ratio |
| :--- | :--- | :--- | :--- |
| **Canvas Background** | `#FBFBFA` | Master document viewport, gutters | Neutral Base |
| **Surface (Cards/Panels)** | `#FFFFFF` | Workspaces, ticket containers, map dock | 1.05:1 to canvas |
| **Subtle Divider** | `#EAEAEA` | 1px hairline card borders, table dividers | Structural |
| **Primary Text** | `#111111` | H1/H2 headlines, key metric values, titles | 18.5:1 (Ultra-high) |
| **Body Text** | `#2F3437` | Descriptions, translations, explanations | 14.2:1 (Compliant) |
| **Secondary / Muted** | `#787774` | Timestamps, coordinates, metadata labels | 5.2:1 (Compliant) |

### 2.2 Muted Spot Pastels (Semantic Meaning Only)

| Semantic Intent | Background Token | Text Token | UI Application |
| :--- | :--- | :--- | :--- |
| **Critical / Emergency** | `#FDEBEC` | `#9F2F2D` | P1 Severity tags, road closures, danger alerts |
| **Active / Investigating**| `#FBF3DB` | `#956400` | Loop status, leading hypothesis, warnings |
| **Verified / Success** | `#EDF3EC` | `#346538` | `[REAL]` provenance tags, approved actions |
| **Telemetry / Infrastructure**| `#E1F3FE` | `#1F6C9F` | Drainage vectors, H3 cell labels, sensor readings |
| **Neutral Tag** | `#F1F1EF` | `#5F5E5B` | `[SIMULATED]`, timestamps, channel identifiers |

---

## 3. Typographic System

The system uses a typographic scale centered on legibility, editorial restraint, and crisp structural hierarchy.

* **Primary Sans (Headlines, Body, Controls):** `Geist Sans` (or `SF Pro Display`, `Switzer`).
  * Headline 1: `24px` (`1.5rem`), Weight 600 SemiBold, tracking `-0.02em`, color `#111111`.
  * Headline 2: `16px` (`1.0rem`), Weight 600 SemiBold, tracking `-0.01em`, color `#111111`.
  * Section Headers: `11px` (`0.6875rem`), Weight 600 SemiBold, uppercase, tracking `0.06em`, color `#787774`.
  * Body Text: `13px` (`0.8125rem`), Weight 400 Regular, line-height `1.5`, color `#2F3437`.
* **Monospace (Telemetry, Coordinates, Hashes):** `Geist Mono` (or `JetBrains Mono`).
  * Telemetry Large: `18px` (`1.125rem`), Weight 500 Medium, tabular figures.
  * Cell IDs & Coordinates: `11px` (`0.6875rem`), Weight 400 Regular, color `#787774`.
* **Editorial Rules:**
  * No italic serif headlines.
  * No decorative quotes or faux-poetic copy.
  * Every metric has its unit explicitly labeled in muted monospace.

---

## 4. Layout Architecture: The 3-Pane Editorial Workspace

```
+------------------------------------------------------------------------------------------------------------------------+
| CrossWire  /  Incident #892  ·  [P1 CRITICAL]  ·  Bellandur Gate / Ward 150  ·  [INVESTIGATING: STEP 4/6]             |
+------------------------------+---------------------------------------------------------+-------------------------------+
| SENSOR INTAKE (25%)          | GEOSPATIAL DIGITAL TWIN (45%)                           | INVESTIGATION & DISPATCH (30%)|
|                              |                                                         |                               |
| [Active Incident Report]     | [Layer Controls: Elevation · Drainage · Vulnerability]  | [Root Cause Hypotheses]       |
| - Photo: Depth 45-60cm       |                                                         | Heavy Rain Overwhelm: 82%     |
| - Waveform Audio Player      | [Paper-Toned Vector Canvas]                             | Drain Blockage: 12%           |
| - Kannada & English Text     | - Fine Charcoal H3 Hexagon Outline (k=2)                | Power-STP Outage: 6%          |
| - Metadata: 12.9352N 77.6821E| - Light Cyan Wash on Low-lying Basin                    |                               |
|                              | - Thin Vector Lines for Stormwater Drains               | [Evidence Ledger]             |
| [Recent Queue - 3 Items]     | - Minimal Geometric Markers: Hospital, School, Substation| [REAL] Rainfall: 42.8 mm/hr    |
| - Sewage Overflow (T-12m)    |                                                         | [REAL] Elevation: 884m        |
| - Power Outage (T-22m)       | [Timeline Controller]                                   | [DERIVED] Velocity: 8/30m     |
| - Traffic Gridlock (T-31m)   | T-180m  ───────[ Slider ]─────── LIVE                   | [SIMULATED] Feeder Outage     |
|                              | Rainfall Curve: 42.8 mm/hr Peak at T-45m                |                               |
|                              |                                                         | [Action Dispatch Plan]        |
|                              |                                                         | BWSSB · BTP · BBMP Directives |
|                              |                                                         | [Approve & Dispatch] [Edit]   |
+------------------------------+---------------------------------------------------------+-------------------------------+
| Engine: LangGraph v2.4  |  LLM: Gemini 3.8 Flash  |  STT: Sarvam AI  |  H3 Res: 8  |  Database: SQLite WAL            |
+------------------------------------------------------------------------------------------------------------------------+
```

---

## 5. Component Engineering Specifications

### 5.1 Top Navigation Bar (56px)
* **Background:** `#FFFFFF` with `border-bottom: 1px solid #EAEAEA`.
* **Height:** Fixed `56px`.
* **Elements:**
  * Brandmark: `CrossWire` in 15px SemiBold `#111111`.
  * Breadcrumb Separator: `/` in `#EAEAEA`.
  * Incident Identifier: `Incident #892` in 13px Mono `#111111`.
  * Severity Tag: Pill badge with background `#FDEBEC`, text `#9F2F2D`, font size 10.5px, uppercase, tracking `0.05em`.
  * Location: `Ward 150 - Bellandur Corridor` in 12px `#787774`.
  * Status Pill: Background `#FBF3DB`, text `#956400`, content `Loop: Step 4/6 (Investigating)`.
  * Right Action: Minimalist dropdown for `Cmdr. Sharma (BBMP)` and `Demo Mode (Cached)`.

### 5.2 Pane 1: Sensor Ingestion (25% Width)
* **Active Multimodal Ticket Card:**
  * Container: `#FFFFFF` card with `border: 1px solid #EAEAEA`, `border-radius: 8px`, `padding: 16px`.
  * Header Row: `Ticket #TK-4821` (Mono 12px) · `Telegram Voice` · `3m ago`.
  * Photo Component:
    * Clean, desaturated photo thumbnail of waterlogged junction.
    * Hairline bounding overlay (`border: 1px solid #111111`) with clean label tag: `Water Depth: 45-60cm` (92% confidence).
  * Audio Waveform Scrubber:
    * Play/Pause button: Solid `#111111` circle (28px diameter) with white play triangle.
    * Track: 48 fine vertical gray bars (`#EAEAEA`), played bars turn `#111111`.
    * Timecode: `0:14 / 0:28` (Mono 11px).
  * Bilingual Transcripts:
    * Kannada Transcript: Native script rendered in 13px `#2F3437`, line-height `1.5`:  
      `"ಬೆಳ್ಳಂದೂರು ಗೇಟ್ ಬಳಿ ರಾಜಕಾಲುವೆ ನೀರು ರಸ್ತೆಗೆ ನುಗ್ಗಿದೆ, ವಾಹನಗಳು ಮುಳುಗಿವೆ."`
    * English Translation: Clean translation rendered in 12.5px `#787774`:  
      `"Storm drain near Bellandur Gate is overflowing onto main road. Multiple vehicles submerged."`
  * Geolocation Pill: `#F1F1EF` background with text `#5F5E5B`: `12.9352° N, 77.6821° E · H3: 88618925d3fffff`.
* **Compact Queue Rows:**
  * Clean, borderless rows separated only by `border-bottom: 1px solid #F1F1EF`.
  * Category indicators use subtle muted pastels: `SEWAGE` (`#FDEBEC`), `POWER` (`#FBF3DB`), `TRAFFIC` (`#E1F3FE`).

### 5.3 Pane 2: The Architectural Map Canvas (45% Width)
* **Map Style:** Carto Positron or MapLibre Light with warm gray tones (land: `#FBFBFA`, roads: `#FFFFFF`, road borders: `#EAEAEA`, water: `#E1F3FE`).
* **H3 Hexagonal Geometry:**
  * Primary Incident Cell (`88618925d3fffff`): Exact 1px charcoal outline (`#111111`) with a very pale amber fill (`rgba(251, 243, 219, 0.4)`).
  * Neighboring K-Ring Cells (18 cells): Very faint gray outlines (`#D4D4D4`) with fill opacity reflecting ticket report density.
* **Drainage & Hydrology Overlay:**
  * Stormwater Drain (Rajakaluve): Fine continuous 1.5px slate-blue line (`#4A88B7`) showing flow path from junction culvert to Bellandur Lake inlet.
  * Culvert Obstruction Marker: A minimal 8px circular marker with a diagonal slash (`#9F2F2D`).
* **Critical Facility Pins (Flat Geometric Markers):**
  * Hospital: Square `#FFFFFF` pin with 1px border `#EAEAEA`, label `Columbia Asia Hospital (420m NW)`.
  * School: Square `#FFFFFF` pin with 1px border `#EAEAEA`, label `Ward 150 High School (310m S)`.
  * Substation: Square `#FFFFFF` pin with 1px border `#EAEAEA`, label `66kV Substation (180m E)`.
* **Timeline Scrubber (Bottom of Canvas):**
  * Flat white container docked at the bottom of the map.
  * Time slider from `T-180m` to `LIVE`.
  * Mini precipitation bar chart above the track showing the rainfall peak (`42.8 mm/hr` at `T-45m`).

### 5.4 Pane 3: Autonomous Investigator & HITL Cockpit (30% Width)
* **Bayesian Hypothesis Stack:**
  * Card with `border: 1px solid #EAEAEA`, `border-radius: 8px`, `padding: 16px`.
  * Headline: `Root Cause Hypotheses` in 11px uppercase mono.
  * Bars:
    * `Heavy Rain Overwhelm`: Label and value `82%` (`P = 0.82`). Horizontal bar: 82% width filled with muted amber `#FBF3DB` with `#956400` border.
    * `Culvert Blockage`: Label and value `12%` (`P = 0.12`). Horizontal bar: 12% width filled with light gray `#F1F1EF`.
    * `STP Power Failure`: Label and value `6%` (`P = 0.06`). Horizontal bar: 6% width filled with light gray `#F1F1EF`.
* **Evidence Ledger (Flat Table Style):**
  * Minimalist list separated by `1px solid #EAEAEA` lines (no card containers).
  * Items:
    1. `[REAL]` Open-Meteo: `Rainfall > 40 mm/hr` (42.8 mm/hr recorded).
    2. `[REAL]` OpenTopoData: `Low Lying Basin` (Elevation 884m, 12m depression).
    3. `[DERIVED]` History: `Debris Complaints` (5 unresolved tickets in 48h).
    4. `[SIMULATED]` SCADA: `Substation Feeder 4 Tripped` (T-20m).
  * Provenance chips use exact muted pastels: `[REAL]` in Pale Green (`#EDF3EC`), `[DERIVED]` in Pale Blue (`#E1F3FE`), `[SIMULATED]` in Neutral Gray (`#F1F1EF`).
* **Multi-Agency Action Desk (HITL Approval):**
  * Action Directives:
    * `1. BWSSB`: Deploy 2x 50HP mobile suction pumps to Bellandur Gate culvert.
    * `2. BTP`: Divert westbound traffic at Iblur Flyover to Sarjapur Road.
    * `3. BBMP`: Dispatch rapid emergency team for trash grate desilting.
  * Citizen Notification Preview:
    * Expandable text drawer displaying approved bilingual message for 342 ward residents.
  * Action Buttons (Ultra-clean button group):
    * Primary CTA: `Approve & Dispatch` — solid `#111111` background, `#FFFFFF` text, `border-radius: 6px`, `padding: 10px 18px`, font weight 500. No shadow.
    * Secondary CTA: `Edit Plan` — `#FFFFFF` background, `border: 1px solid #EAEAEA`, `#111111` text, `border-radius: 6px`, `padding: 10px 14px`.
    * Reject Action: `Reject` — plain text link in `#9F2F2D` with subtle hover underline.

---

## 6. Pre-Flight Quality & Minimalism Audit

- [x] **No Obsidian or Dark Mode Slop:** 100% warm monochrome light palette (`#FBFBFA` canvas, `#FFFFFF` surfaces, `#EAEAEA` borders).
- [x] **No Neon Accents:** Saturated blues, cyans, and purples replaced with desaturated, washed-out spot pastels (`#FBF3DB`, `#FDEBEC`, `#EDF3EC`, `#E1F3FE`).
- [x] **No Generic Drop Shadows:** Elevation communicates via 1px crisp borders, zero blurry drop shadows.
- [x] **No Emojis:** Interface uses typography and SVG primitives only.
- [x] **No AI Copywriting Clichés:** Clear, concise language with domain-accurate municipal terminology (BWSSB, BTP, BBMP, Rajakaluve, H3 resolution-8).
- [x] **High Contrast Typography:** Primary text is `#111111` on `#FFFFFF` (18.5:1 contrast, exceeding WCAG AAA requirements).
