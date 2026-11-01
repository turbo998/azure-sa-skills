# Azure SA Skills

> [中文版 (`README.md`)](./README.md)

A collection of Hermes / GitHub Copilot skills for daily Azure Solution Architect (SA) workflows. Each subdirectory is a self-contained skill with its own `SKILL.md`, scripts, and templates.

## Skills

### Partner-Facing & Customer Delivery

- [`billing-assistant/`](./billing-assistant/) — Anchor-based PyMuPDF tool that rewrites raw partner/CSP billing PDFs (with markup annotations) into customer-ready invoices while preserving layout, supporting dual currencies, and stripping annotations without LLM hallucination.
- [`openclaw-wechat-deployment/`](./openclaw-wechat-deployment/) — OpenClaw on Azure deployment guide and WeChat group sharing workflow.
- [`wechat-article/`](./wechat-article/) — Converts technical material into polished WeChat Official Account articles.

### Azure / Hermes Infrastructure

- [`azure-hermes-ghcp-wechat/`](./azure-hermes-ghcp-wechat/) — Deploys Hermes Agent on an Azure VM, configures GitHub Copilot as the model provider, and connects WeChat/Weixin.
- [`azure-foundry-quota-tier/`](./azure-foundry-quota-tier/) — Quick lookup and diagnostics for Azure AI Foundry / OpenAI subscription quota tiers (Tier 1–6).
- [`chorus-azure-deployment/`](./chorus-azure-deployment/) — Deploys [Chorus-AIDLC/Chorus](https://github.com/Chorus-AIDLC/Chorus) to Azure Container Apps (Bicep IaC, PGlite, `emptyDir` vs. `azureFile`, MCAPS shared-key bypass).

### Presentation / Templates & Knowledge Animation

- [`azure-style-presentation/`](./azure-style-presentation/) — Interactive HTML slide presentations in Microsoft Azure visual style.
- [`ppt-template-strict-offering/`](./ppt-template-strict-offering/) — PowerPoint generation workflow strictly adhering to offering templates.
- [`one-sentence-video/`](./one-sentence-video/) — Autopilot HyperFrames motion-graphics video production skill featuring a 7-step pipeline, 23 4-axis style presets, 22 measured shot cards, procedural Python BGM/SFX synthesis, dual-layer quality gates, and 3 benchmark knowledge-explainer templates (*Xiaozhe MCP Node Graph*, *Xiaozhe RAG Pipeline Flow*, and *Chimp DeepSeek Unit Economics*).
  - 中文说明: [`one-sentence-video/README.md`](./one-sentence-video/README.md) | English: [`one-sentence-video/README.en.md`](./one-sentence-video/README.en.md)

---

## Usage

**As a Hermes skill**: Clone this repository into `~/.hermes/profiles/<profile>/skills/` or copy an individual skill directory there, then load via `skill_view(name='<skill-name>')`.

**As standalone scripts**: Run the tools in each skill's `scripts/`, `assets/`, or `templates/` directory directly.
