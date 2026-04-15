---
name: azure-style-presentation
description: Create Azure-style HTML slide presentations with Microsoft Azure visual language, cloud architecture sections, service badges, comparison tables, KPI cards, and keyboard-friendly navigation. Use this whenever the user wants to make a presentation, PPT, slides, technical sharing deck, Azure solution brief, architecture review, quota report, or product intro related to Azure.
license: MIT
---

# Azure-Style HTML Presentation Skill

Generate a zero-dependency, single-file HTML slide deck with all CSS and JavaScript inlined. The presentation should feel like a modern Azure solution briefing: clean, enterprise, cloud-focused, and visually consistent.

## When to Use

Use this skill when the user asks for:

- Azure solution presentations
- cloud architecture decks
- technical sharing slides
- quota, pricing, or capability comparison decks
- customer-facing Azure product introductions
- Chinese prompts such as `做 Azure 方案 PPT`, `生成演示稿`, `技术分享`, `做云架构介绍`

## Core Principles

- Prefer clarity over decoration.
- Use more slides instead of overcrowding a slide.
- Make architecture and tradeoff slides easy to scan.
- Support both Chinese and English content.
- Keep the final artifact as a single self-contained HTML file.

## Azure Color System

All presentations must define and use these CSS custom properties:

```css
:root {
    --azure-blue: #0078D4;
    --azure-dark-blue: #005A9E;
    --azure-cyan: #50E6FF;
    --azure-navy: #243A5E;
    --azure-ink: #1F2937;
    --azure-gray: #5F6B7A;
    --azure-light-gray: #F5F9FD;
    --azure-border: #D6E9F8;
    --success: #107C10;
    --warning: #FFB900;
    --danger: #D13438;
    --neutral: #6B7280;
}
```

Color usage rules:

- Body background: `linear-gradient(135deg, var(--azure-dark-blue), var(--azure-blue))`
- Slide background: `rgba(255,255,255,0.98)`
- h1: `var(--azure-blue)` with 4px `var(--azure-cyan)` bottom border
- h2: `var(--azure-dark-blue)`
- h3: `var(--azure-blue)`
- body text: `var(--azure-gray)`
- emphasis blocks: light blue background plus blue left border

## Typography

Use:

```css
font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
```

Recommended sizes:

- h1: `2.2em`, weight `700`
- h2: `1.35em`
- h3: `1.1em`
- body: `0.96em`, line-height `1.55`
- small text: `0.84em`

## Core Components

### 1. Slide Container

```css
.slide {
    position: absolute;
    width: 100vw;
    min-height: 100vh;
    max-height: 100vh;
    background: rgba(255,255,255,0.98);
    padding: 40px 60px 84px 60px;
    left: 0;
    top: 0;
    transform: translateX(100%);
    opacity: 0;
    transition: all 0.6s ease;
    overflow-y: auto;
    color: var(--azure-ink);
}
.slide.active {
    opacity: 1;
    transform: translateX(0);
    z-index: 10;
}
```

### 2. Card

Use cards for capabilities, risks, architecture notes, and design choices.

```css
.card {
    background: var(--azure-light-gray);
    padding: 14px;
    border-radius: 10px;
    margin: 10px 0;
    border-left: 4px solid var(--azure-blue);
    box-shadow: 0 4px 18px rgba(0, 90, 158, 0.08);
}
```

Left border semantics:

- blue: default information
- green: recommendation or advantage
- yellow: caution
- red: risk or limitation
- cyan: data point or architecture dependency

### 3. Grid

```css
.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 14px;
    margin: 12px 0;
}
```

### 4. Service Badge

Use badges for Azure services and lifecycle labels.

```css
.badge {
    display: inline-block;
    background: var(--azure-blue);
    color: white;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.8em;
    font-weight: 600;
}
.badge.ga { background: var(--success); }
.badge.preview { background: var(--warning); color: #1f2937; }
.badge.risk { background: var(--danger); }
.badge.arch { background: var(--azure-navy); }
```

### 5. Comparison Table

```css
.comparison-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.94em;
}
.comparison-table th {
    background: linear-gradient(135deg, var(--azure-dark-blue), var(--azure-blue));
    color: white;
    padding: 10px;
    text-align: left;
}
.comparison-table td {
    padding: 10px;
    border-bottom: 1px solid var(--azure-border);
}
.comparison-table tr:nth-child(even) {
    background: #F9FCFF;
}
.comparison-table tr.highlight-row {
    background: rgba(80,230,255,0.18);
    font-weight: 600;
}
```

Use `<strong style="color: var(--azure-blue);">` for the recommended or best-fit value.

### 6. KPI / Metric Box

```css
.metric-box {
    display: inline-block;
    background: linear-gradient(135deg, var(--azure-blue), var(--azure-cyan));
    color: var(--azure-navy);
    padding: 10px 18px;
    border-radius: 10px;
    font-size: 1.18em;
    font-weight: 700;
    margin: 8px 8px 8px 0;
}
```

### 7. Emphasis Block

```css
.emphasis {
    font-size: 1em;
    font-weight: 600;
    color: var(--azure-dark-blue);
    margin: 14px 0;
    padding: 12px;
    background: rgba(0,120,212,0.08);
    border-left: 4px solid var(--azure-blue);
    border-radius: 6px;
}
```

### 8. Architecture Panel

Use for diagrams described with HTML blocks when no image is provided.

```css
.arch-panel {
    background: linear-gradient(180deg, #ffffff, #f7fbff);
    border: 1px solid var(--azure-border);
    border-radius: 12px;
    padding: 16px;
    margin: 12px 0;
}
.arch-node {
    display: inline-block;
    background: white;
    border: 1px solid var(--azure-border);
    border-radius: 10px;
    padding: 10px 14px;
    margin: 6px;
    color: var(--azure-navy);
    font-weight: 600;
    box-shadow: 0 2px 10px rgba(0, 120, 212, 0.08);
}
```

### 9. Highlight Text

```css
.highlight {
    background: rgba(80,230,255,0.22);
    padding: 2px 6px;
    border-radius: 4px;
    color: var(--azure-ink);
    font-weight: 600;
}
```

## Slide Types

### Title Slide

Use a centered cover with Azure branding tone.

```html
<div class="slide active">
  <div style="display:flex;flex-direction:column;justify-content:center;align-items:center;height:80vh;text-align:center;">
    <h1 style="font-size:3.4em;margin-bottom:32px;border:none;color:white;">Main Title</h1>
    <h2 style="font-size:1.8em;color:var(--azure-cyan);margin-bottom:40px;">Subtitle</h2>
    <div style="margin-top:60px;font-size:1.2em;color:#dbeafe;">
      <p><strong>Author | Team | Date or Context</strong></p>
    </div>
  </div>
</div>
```

### Recommended Deck Flow

For Azure solution decks, this sequence usually works well:

1. Cover
2. Executive summary
3. Problem statement or requirements
4. Proposed Azure architecture
5. Service-by-service breakdown
6. Comparison or decision rationale
7. Cost, quota, governance, or operations considerations
8. Risks and mitigations
9. Next steps
10. Q&A

### Closing Slide

Centered `Q&A` or `Next Steps` slide with a calm Azure-branded ending.

## Navigation System

### Bottom Navigation

```css
.navigation {
    position: fixed;
    bottom: 24px;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    gap: 10px;
    z-index: 100;
    background: rgba(36,58,94,0.92);
    padding: 10px 20px;
    border-radius: 50px;
}
.nav-btn {
    background: var(--azure-blue);
    border: none;
    color: white;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    cursor: pointer;
    font-size: 1.2em;
    transition: all 0.3s ease;
}
.nav-btn:hover {
    background: var(--azure-cyan);
    color: var(--azure-navy);
    transform: scale(1.08);
}
```

### Progress Bar

Top-fixed 4px bar using `linear-gradient(90deg, var(--azure-cyan), var(--azure-blue))`.

### Slide Counter

Top-right rounded pill showing `current / total`.

### Logo

Top-left fixed label. Default text should be `Microsoft Azure` unless the user provides something else.

## Animation System

### Slide Transition

Use horizontal slide-in transition with opacity change.

### Staggered Content Entry

Use a simple fade-up animation:

```css
@keyframes slideIn {
    from { opacity: 0; transform: translateY(24px); }
    to { opacity: 1; transform: translateY(0); }
}
.slide.active > * { animation: slideIn 0.45s ease-out backwards; }
.slide.active > *:nth-child(1) { animation-delay: 0.08s; }
.slide.active > *:nth-child(2) { animation-delay: 0.16s; }
.slide.active > *:nth-child(3) { animation-delay: 0.24s; }
.slide.active > *:nth-child(4) { animation-delay: 0.32s; }
.slide.active > *:nth-child(5) { animation-delay: 0.40s; }
```

## JavaScript Navigation

Implement:

- next / previous buttons
- keyboard navigation: `ArrowRight`, `Space`, `PageDown`, `ArrowLeft`, `PageUp`, `Home`, `End`
- touch swipe navigation with a 50px threshold
- progress bar updates
- slide counter updates

Use a structure like:

```javascript
let currentSlide = 0;
const slides = document.querySelectorAll('.slide');
const totalSlides = slides.length;

function updateSlide() {
    slides.forEach((slide, index) => {
        slide.classList.remove('active');
        if (index === currentSlide) {
            slide.classList.add('active');
            slide.scrollTop = 0;
        }
    });
    document.getElementById('slideCounter').textContent = `${currentSlide + 1} / ${totalSlides}`;
    document.getElementById('progressBar').style.width = `${((currentSlide + 1) / totalSlides) * 100}%`;
}
```

## Print Styles

Include `@media print`:

- slides become `position: relative`
- all slides visible
- no transitions
- `page-break-after: always`
- hide navigation, progress bar, slide counter, and logo
- avoid breaking cards and tables awkwardly

## Azure Content Guidance

Favor these patterns when relevant:

- architecture: Front Door, App Service, Container Apps, AKS, Functions, API Management, Azure OpenAI, AI Search, Cosmos DB, Azure SQL, Storage, Key Vault, Monitor
- governance: RBAC, managed identity, private endpoint, policy, cost control
- operations: observability, scaling, DR, SLA, quota, latency, deployment flow
- communication style: solution-oriented, concise, executive-friendly

For architecture slides, prefer:

- left-to-right user flow
- grouped layers such as ingress, app, data, AI, and observability
- explicit trust boundaries or private/public separation when relevant

## Emoji Guidance

Use emoji sparingly. Preferred set:

- `☁️` cloud
- `🧠` AI
- `🔐` security
- `📊` metrics
- `⚙️` operations
- `🚀` launch or growth
- `💰` cost
- `⚠️` risk
- `✅` recommendation

Avoid turning every heading into an emoji list.

## Generation Rules

1. Output a single self-contained HTML file with all CSS and JavaScript inlined.
2. First slide must be a cover slide, last slide must be Q&A, summary, or next steps.
3. Keep each slide focused on one idea.
4. Use comparison tables for options, cards for capabilities, and architecture panels for topology.
5. Add an `.emphasis` takeaway near the bottom of content slides.
6. Highlight the recommended option in blue or cyan.
7. Support both Chinese and English content and set `lang` accordingly.
8. Replace the top-left logo text when the user specifies a custom team, project, or company label.
9. When the user provides Azure-specific numbers, preserve them exactly.
10. When the user does not provide enough structure, propose a clean slide sequence and then generate the deck.
