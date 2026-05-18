# invoice-rewriter

Surgically edit text fields on a PDF invoice (BILL TO / SHIP TO blocks, summary rows like SUB TOTAL / EXTRA DISCOUNT / INVOICE TOTAL, dual-currency totals) while preserving the original layout. Anchor-based — no hardcoded coordinates, no LLM, no API key. CJK-safe.

**Use case**: a Microsoft partner sends you a vendor-issued CSP/SaaS invoice (text-based PDF) plus modification instructions (often as PDF sticky-note annotations) and asks for a polished output PDF for the end customer.

**Not for**: scanned/image-only invoices (no text layer) — use OCR + nano-pdf instead.

See [`SKILL.md`](SKILL.md) for the full workflow, primitives reference, and pitfalls. Worked example in [`scripts/example_synnex.py`](scripts/example_synnex.py).

## Quick start

```bash
uv pip install pymupdf
python scripts/example_synnex.py   # edit SRC path inside first
```

In a Hermes agent session, this directory is also a Hermes skill — `skill_view(name='invoice-rewriter')` loads `SKILL.md` and the agent will follow the anchor-based workflow.
