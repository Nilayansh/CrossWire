# CrossWire Design Specification: Editorial Minimalist Architecture

> **System Name:** CrossWire (NammaTwin Incident Intelligence)  
> **Interactive Preview:** [preview/index.html](file:///e:/CrossWire/preview/index.html)  
> **Target Platform:** Google Stitch (`stitch.withgoogle.com`) & Production Frontend  
> **Design Philosophy:** Premium Utilitarian Minimalism & Editorial Document Architecture (`minimalist-ui`)  
> **Palette:** Warm Monochrome (Bone `#FBFBFA` + White `#FFFFFF` + Hairline `#EAEAEA` + Off-Black `#111111`)  
> **Highlight Mechanism:** Thicker 2.5px solid black border (`border-2 border-black`) instead of bright colored buttons  
> **Typography:** Bold & Italic Editorial Serif (`Newsreader`) + Clean Sans (`Plus Jakarta Sans`) + Monospace (`JetBrains Mono`)  
> **Navigation Model:** 4-Stage Sequential Investigation Workflow with 1-Line Navigation Hero

---

## 1. Google Stitch Master Prompt (Editorial Minimalist Multi-Page Flow)

```text
Design a clean, ultra-minimalist, editorial-style incident command console called "CrossWire". The system unifies scattered citizen complaints into cross-department urban emergency incidents, calculates spatial root causes using real public signals (rainfall, elevation, drainage infrastructure), and provides a Human-In-The-Loop (HITL) approval desk for municipal coordinators.

Aesthetic & Theme:
Warm monochrome, editorial workspace minimalism (inspired by Linear, Notion, and Swiss architectural planning sheets).
- Background Canvas: Warm Off-White / Bone (#FBFBFA).
- Surface Containers: Pure White (#FFFFFF) with crisp 1px hairline borders (#EAEAEA). Absolutely no heavy drop shadows or 3D elevation.
- Highlight System: Use a thicker, crisp black border (2.5px solid #111111) to indicate active/selected states, rather than bright colored buttons or glowing badges.
- Typography: High-contrast typography featuring an editorial serif in bold italics (Newsreader style) for brand and section titles, clean sans-serif (Plus Jakarta Sans style) for body text, and monospace (JetBrains Mono style) for coordinates, timestamps, and metric values. Primary text is Off-Black (#111111), and secondary text is Muted Slate (#787774).
- Banned: Strictly no dark mode, no obsidian backgrounds, no neon glows, no gradients, no bright saturated buttons, and no emojis.

Hero Section (Top of Each Page - Protocol Navigation Guide):
A prominent 2.5px black-bordered card containing a 4-step workflow guide with exactly 1 line per stage:
- Stage 1 (Citizen Reports): "Review incoming citizen complaints, flood depth photos, and voice audio statements."
- Stage 2 (Geographic Map): "Inspect the low-lying flood basin, stormwater canal vectors, and nearby hospitals and schools."
- Stage 3 (Cause Analysis): "Examine the verified findings comparing extreme rainfall, culvert debris, and electrical feeds."
- Stage 4 (Departmental Actions): "Authorize coordinated emergency orders for water dewatering pumps and traffic diversions."

Page Breakdown:
1. Citizen Reports (index.html): Displays verified citizen complaints, photo with water depth bounding overlay (45-60 cm), playable Kannada audio player with Sarvam STT native script and verified English translation, and queue of recent reports.
2. Geographic Map (map.html): Clean architectural monochrome map (OpenStreetMap with grayscale filter, zero API key watermarks, zero overflow) showing H3 hexagon boundary, Rajakaluve drainage path, facility markers, and rainfall timeline slider.
3. Cause Analysis (investigation.html): Evaluation of heavy rainfall (82% confidence) vs culvert obstruction (12%) vs power failure (6%), with official verification data table.
4. Departmental Actions (dispatch.html): Concrete directives for BWSSB, Traffic Police, and BBMP, official bilingual citizen advisory notice, and "Authorize & Issue Departmental Orders" button.
```

---

## 2. Animation & Motion Architecture (GSAP Specifications)

All pages include GSAP (`https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js`) for coordinated, lightweight motion design.

### 2.1 Staggered Entrance Choreography
```javascript
window.addEventListener('DOMContentLoaded', () => {
  if (window.gsap) {
    const tl = gsap.timeline({ defaults: { ease: "power2.out", duration: 0.6 } });
    tl.from("#hero-guide", { y: 20, opacity: 0 })
      .from(".step-card", { y: 15, opacity: 0, stagger: 0.08 }, "-=0.3")
      .from("#section-heading", { y: 15, opacity: 0 }, "-=0.2")
      .from("#primary-content", { y: 20, opacity: 0 }, "-=0.3");
  }
});
```

### 2.2 Semantic Animation Hooks
Each page provides dedicated data attributes and IDs for advanced GSAP ScrollTrigger or physics:
* `#hero-guide` & `.step-card[data-step="1..4"]`: Step cards with smooth hover lift and active black border.
* `#map-section` & `.map-wrapper`: Contained map surface with zero bleed.
* `#hypotheses-section` & `.highlight-box`: Bayesian probability bars ready for scrubbed width animations.
* `#directives-section` & `#receipt-card`: Dispatch order transitions and confirmation animations.

---

## 3. Map Containment & Rendering Standard

* **Zero Overflow Enforcement:**
  * Map wrapper uses `position: relative; overflow: hidden; contain: paint; border: 2.5px solid #111111;`
  * Map viewport uses `height: 520px; overflow: hidden; isolation: isolate; z-index: 10;`
  * Header and navigation tabs enforce `z-50` and `z-40` respectively.
* **Monochrome Tile Layer:**
  * Standard OpenStreetMap tiles (`https://tile.openstreetmap.org/{z}/{x}/{y}.png`)
  * Filter applied: `filter: grayscale(100%) contrast(90%) brightness(105%)`
  * **Result:** 100% reliable, zero "API KEY REQUIRED" watermarks, elegant Swiss architectural cartography.
