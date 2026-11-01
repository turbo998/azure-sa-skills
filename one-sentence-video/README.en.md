# One-Sentence Video (`one-sentence-video`)

> [中文版 (`README.md`)](./README.md)

**One-Sentence Video** is a self-contained, autopilot-first skill for producing programmatic HyperFrames motion-graphics videos from a single natural-language prompt. Without relying on external scriptwriting or talking-head pipelines, it orchestrates requirement intake, 3-act visual storyboarding, 3-direction aesthetic bakeoffs, component registry lookup, named camera seams, procedural Python BGM/SFX synthesis, and frame-level quality gates.

Tailored for the **Knowledge Explainer Animation Research Track**, this skill expands the baseline 20 styles and 19 shot cards with **3 benchmark knowledge-explainer style presets** and **3 measured shot cards** reverse-engineered from viral Douyin/Bilibili technical explainers (*Xiaozhe on Agents*, *Xiaozhe on LLM RAG*, and *The Fourth Chimpanzee on DeepSeek GPU Unit Economics*), bringing the library to **23 style presets** and **22 measured shot cards**.

---

## 1. 7-Step Autopilot Production Pipeline

| Step | Stage | Key Deliverables | Core Mechanism & Guardrails |
|---|---|---|---|
| **Step 0** | **Intake & Brief Card** | 3-line project brief | Parses topic, copy, aspect ratio, and assets. Defaults: **1920×1080 landscape @ 30fps, 20–30s (5–7 shots), no voiceover, procedural BGM + SFX enabled**. |
| **Step 1** | **Project Scaffolding** | HyperFrames workspace | Initializes in-place or via `npx hyperframes init` with landscape resolution. |
| **Step 2** | **Visual Storyboard** | `STORYBOARD.md` | Queries `card-index.py` for measured shot recipes and energy curves (`--energy-plan` prevents 3 consecutive shots at the same energy). Enforces strict text budgets (title 4–8 chars, subtitle ≤10 chars, tag ≤6 chars, body prose 0 chars). |
| **Step 3** | **3-Direction Aesthetic Bakeoff** | `output/directions/{A,B,C}.png`<br>`design-spec.md` | **The only mandatory user decision**: pulls candidates from `style-ledger.json`, renders three 1920×1080 static sample frames with real copy, records `palette_source: <style-id>`, and bans default dark-blue neon AI uniforms. |
| **Step 4** | **Per-Shot Registry Gate** | `output/registry-ledger.md` | **Install before hand-coding**: searches layout archetypes via `layout-index.py` and functional blocks via `catalog-search.py`, logging every shot's match or hand-crafted justification. |
| **Step 5** | **Frame Authoring & Named Seams** | `compositions/frames/*.html` | Enforces HyperFrames renderer invariants (GSAP tweens flat clip roots only, no nested clips, CSS inside `<template>`) and requires a named seam (`cut-the-curve`, `zoom-through`, `scale-through`, `whip-x`, etc.) per cut. |
| **Step 5.5** | **3-Layer Audio Engineering** | `audio/bgm.wav` + `beat-grid.json`<br>`audio/sfx.wav` + `sfx-events.json` | ① `bgm-gen.py` synthesizes BGM and beat grids → ② `beat-snap.py` validates cut alignment (±50ms) → ③ `sfx-gen.py` synthesizes frame-accurate causal SFX motifs. |
| **Step 6** | **Dual-Layer Gates & Delivery** | `renders/draft-check.mp4`<br>`renders/video.mp4` | Runs `process-gate.py --stage all` and `npm run check`, extracts draft frames for `density-gate.py --strict-safe` (6 anti-flatness criteria), and renders high-quality MP4 after verification. |

---

## 2. 4-Axis Style Ledger (23 Style Presets)

Single source of truth: `references/style-ledger.json` (human-readable: `references/style-ledger.md`). Every style is defined across **Look (Palette & Fonts) × Layout (Archetypes) × Motion (Seam & In-Scene Route) × Sound (Motifs & BGM)**:

- **17 Light-Background Styles (Default Candidate Pool)**:
  `paper-catalog`, `manifesto-poster`, `research-note`, `blueprint-report`, `broadside-news`, `code-editorial-tour`, `cobalt-index`, `cartesian-restraint`, `coral-contrast`, `capsule-candy`, `blockframe-blocks`, `creative-journal`, `daisy-soft`, `biennale-artbook`, `ink-scroll`, **`xiaozhe-rag-pipeline-flow`**, and **`chimp-deepseek-unit-economics`**.
- **6 Dark-Background Styles (🌙 Require Explicit User Approval in `USER_APPROVED_DARK_STYLES`)**:
  `speed-board`, `vault-gold`, `night-cinema`, `metal-spec`, `cyber-hud`, and **`xiaozhe-mcp-node-graph`**.

---

## 3. Benchmark Knowledge-Explainer Styles & Shot Card Mapping

| Benchmark Video Source | Style ID (`style-ledger.json`) | Polarity | Look & Color Semantics | Layout & Paired Shot Card (`references/cards/catalog/`) | Motion Signature |
|---|---|---|---|---|---|
| **Xiaozhe on Agents**<br>*MCP vs. Skill vs. Local Tools Topology* | `xiaozhe-mcp-node-graph` | `dark` 🌙 | Obsidian-teal glow `#050C0A`→`#081614`, ink `#F8FAFC`, protocol mint `#4ADE80`, method lilac `#A78BFA`, execution amber `#FBBF24`, pain-point coral `#FB7185` | Top-left chapter pill (`[01] 核心问题`) + left-to-right cubic Bezier node tree + right donut gauge (`90% 容易混淆`) + bottom caption bar<br>👉 Card: [`progressive-node-tree.md`](./references/cards/catalog/progressive-node-tree.md) | Focus node spotlight (`scale: 1.08`) while non-focus branches dim (`opacity: 0.25`), SVG pulse stream along links, `scale-through` & `whip-x` seams |
| **Xiaozhe on LLMs**<br>*Mastering the 4-Stage RAG Funnel* | `xiaozhe-rag-pipeline-flow` | `light` | Warm editorial white `#F7F6F2`, crisp cards `#FFFFFF` (`2px solid #0F172A`), chunking cobalt `#2563EB`, vector recall cyan `#0891B2`, rerank amber `#EA580C`, generation green `#16A34A`, hallucination red `#DC2626` | 4-stage horizontal funnel pipeline + anthropomorphic role tags (Super Intern / Sticky Note / Long-Term KB) + top `notch-rail-progress`<br>👉 Card: [`funnel-stage-filter.md`](./references/cards/catalog/funnel-stage-filter.md) | `packet-hop-break` (document chunks hop across tracks; bad splits shatter into red fragments on impact; low-score chunks drop out in Rerank while top chunks enter the Prompt slot) |
| **The Fourth Chimpanzee**<br>*DeepSeek $38/GPU Unit Economics* | `chimp-deepseek-unit-economics` | `light` | Warm cream paper `#FAF9F6`, deep ink `#0F172A`, baseline slate `#94A3B8`, Klein blue `#2563EB`, bottleneck orange `#F97316`, cache-hit emerald `#10B981`, MoE purple `#8B5CF6` | Top-left thesis headline + central GPU brick matrix + giant multiplier formula (`$38 vs $5.7 ≈ 6.7x`, `60K / 1.5M 25x saved`) + bottom-left circular speaker PiP anchor<br>👉 Card: [`gpu-matrix-ledger.md`](./references/cards/catalog/gpu-matrix-ledger.md) | `counter-seek-safe` giant number roll + column-by-column GPU matrix color wave + straggler bottleneck bar comparison + `whip-x` rapid chapter cuts |

---

## 4. Measured Shot Card Library (22 Shot Cards)

Indexed in `references/cards/_index.json` (rebuilt via `python assets/card-index.py --rebuild` and validated via `--audit`):

- **Catalog Layout/Typography/Data Cards (13)**:
  `numbered-section-open`, `hero-plus-thumbnail-wall`, `three-way-bakeoff-row`, `caption-bar-close`, `two-column-corridor`, `orbit-ring-title`, `cast-list-poster`, `stat-pills-row`, `repeated-text-texture`, `cta-pill-close`, **`progressive-node-tree`**, **`funnel-stage-filter`**, **`gpu-matrix-ledger`**.
- **Motion & Sequence Cards (8)**:
  `seam-cut-the-curve`, `world-pan-parallax`, `packet-hop-break`, `counter-seek-safe`, `notch-rail-progress`, `easing-family`, `section-beat-density`, `scene-handoff-overlap`.
- **Sound & Rhythm Cards (1)**:
  `beat-grid-snap`.

---

## 5. Dual-Layer Quality Gates (`process-gate.py` + `density-gate.py`)

1. **Process Gate (`assets/process-gate.py` & `assets/palette-audit.py`)**:
   - **Palette Gate**: Verifies `palette_source` in `design-spec.md`; enforces `USER_APPROVED_DARK_STYLES` and explicit user sign-off for dark styles; blocks unauthorized Neon Pulse hex leftovers.
   - **Direction Gate**: Requires three `1920×1080` PNG sample frames in `output/directions/`, `README.md`, and recorded user selection.
   - **Layout Gate**: Verifies `registry:` lines per shot, row counts in `output/registry-ledger.md`, and valid `card:` IDs against `_index.json`.
   - **Motion Gate**: Verifies named seams (`SEAMS`), `velocity=` easing pairs, `carrier=` anchors, and scans `STORYBOARD.md` for banned phrases (`uniform fade+slide`, etc.).
   - **Sound & Beat Gate**: Verifies `audio/sfx-events.json`, stereo 44.1kHz `audio/sfx.wav`, root `<audio>` tags in `index.html`, and `beat-snap.py` cut alignment.
2. **Density Gate (`assets/density-gate.py`)**:
   - Evaluates extracted draft frames across 6 quantitative criteria: dead-zone duration (<2.0s with ≥4 empty 3×3 grid cells), structural change interval (median ≤4.0s), freeze share (≤30%), easing fingerprint diversity (single ease ≤70%, `back.out` ≤2), adjacent layout repetition warnings, and action-safe area bounds (`--strict-safe`).

---

## 6. Quick CLI Reference

```bash
# 1. List all 23 styles or query by genre / layout / dark mode
python one-sentence-video/assets/style-query.py --list
python one-sentence-video/assets/style-query.py --genre tech-deep --dark
python one-sentence-video/assets/style-query.py --id xiaozhe-mcp-node-graph

# 2. List all 22 shot cards, audit card completeness, or generate an energy plan
python one-sentence-video/assets/card-index.py --list
python one-sentence-video/assets/card-index.py --audit
python one-sentence-video/assets/card-index.py --energy-plan 7

# 3. Run process and frame-density quality gates
python one-sentence-video/assets/process-gate.py <project-dir> --stage all
python one-sentence-video/assets/density-gate.py <project-dir> --strict-safe
```
