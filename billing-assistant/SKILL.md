---
name: billing-assistant
description: Rewrite specific fields in a text-based PDF invoice (BILL TO / SHIP TO, summary rows like SUB TOTAL / EXTRA DISCOUNT / INVOICE TOTAL, dual-currency totals) without re-laying-out the whole page. Anchor-based — no hardcoded coordinates, works across templates. Use when a partner gives you a source invoice PDF plus modification instructions (often as PDF annotations) and asks for a polished output PDF. CJK-safe, no LLM, no API key.
version: 2.0.0
author: fde
license: MIT
metadata:
  hermes:
    tags: [PDF, Invoice, Azure, CSP, PyMuPDF, Partner]
---

# billing-assistant

Surgically edit text fields on a PDF invoice while preserving the original layout. Built for the SYNNEX-style CSP billing invoice but generalizes to any text-based PDF whose target fields can be located by nearby anchor text (e.g. "BILL TO", "SUB TOTAL").

**Not for**: scanned/image-only invoices (no text layer to anchor on) — use OCR + nano-pdf instead.

## When to use

Triggered when the user (typically a Microsoft partner) sends:
1. A **source PDF** — usually a vendor-issued invoice
2. **Modification instructions** — often embedded as PDF sticky-note annotations in the source, sometimes spoken in chat
3. A **reference PDF** ("改后.pdf") showing the target result — optional, but use it to verify

Output is a new PDF visually identical to the source except for the edited fields, with all annotations stripped.

## Why this approach (vs nano-pdf / LLM)

- `nano-pdf` requires `GEMINI_API_KEY` and rasterizes the page → LLM redraws → layout drifts, fonts change, totals can be hallucinated. Bad for financial documents.
- PyMuPDF cover-and-rewrite preserves the **exact** original layout (everything not touched stays byte-identical) and is fully deterministic.
- Anchor-based primitives in `scripts/invoice_edit.py` mean **no hardcoded coordinates** — re-locates target text by `page.search_for(...)` on every run, so the same script handles slight template variations.

## Prerequisites

```bash
uv pip install -q pymupdf
# CJK font (already on Hermes VM): /usr/share/fonts/truetype/wqy/wqy-zenhei.ttc
# Override with INVOICE_EDIT_FONT env var if needed.
```

## Workflow

### Step 1 — Inspect the source

Always start by extracting annotations so you know what the partner wants changed:

```python
import sys; sys.path.insert(0, "/home/azureuser/.hermes/profiles/fde/skills/productivity/billing-assistant/scripts")
from invoice_edit import Invoice

inv = Invoice("source.pdf")
for a in inv.annotations():
    print(f"P{a.page+1} near {a.anchor_text!r}:\n  {a.text}\n")
```

`anchor_text` shows the visible words near each sticky note — that's how you map an instruction like *"改为客户的真实公司名"* to the BILL TO or SHIP TO block.

### Step 2 — Confirm with the user (natural language)

Show the parsed annotations and ask for the specifics that can't be inferred. Phrase in Chinese, casual:

> 从原始账单提取到 4 条批注：
> 1. BILL TO → 替换为客户真实抬头
> 2. SHIP TO → 替换为客户真实抬头
> 3. 第一页汇总 → SUB TOTAL 改为 HKD $；EXTRA DISCOUNT 改为第二货币行；删除 INVOICE TOTAL 行
> 4. 末页汇总 → 仅保留 INVOICE TOTAL（金额 = 第一页的 SUB TOTAL）
>
> 请告诉我：
> - 客户的 BILL TO / SHIP TO 公司名分别是？
> - 是否需要第二货币行？如需，币种标签 / 汇率（或直接给金额）？

### Step 3 — Apply edits with the primitives

Compose calls based on the instructions. **Never hardcode coordinates** — always anchor on text the source PDF contains:

```python
inv.strip_annotations()                                              # always first

inv.replace_block_under("BILL TO", "示例客户公司A", stop_at="ATTN:")
inv.replace_block_under("SHIP TO", "示例客户公司B",   stop_at="ATTN:")

# Page 1 summary: dual currency, drop the last row
inv.replace_summary_row("SUB TOTAL",      label="HKD $")
inv.replace_summary_row("EXTRA DISCOUNT", label="人民币含税 ￥", amount="880.42")
inv.delete_summary_row("INVOICE TOTAL")
inv.cover_discount_amount()                                          # erase orphan 107.00 in discount table

# Last page: relabel SUB TOTAL row → INVOICE TOTAL (keeps its 893.10),
# drop EXTRA DISCOUNT and the old INVOICE TOTAL row
inv.delete_summary_row("INVOICE TOTAL", page=-1)
inv.delete_summary_row("EXTRA DISCOUNT", page=-1)
inv.replace_summary_row("SUB TOTAL", label="INVOICE TOTAL", page=-1)
inv.cover_discount_amount(page=-1)

inv.save("out.pdf")
```

### Step 4 — Verify visually

Render each edited page and (if a reference PDF exists) compare with `vision_analyze`:

```python
import fitz
d = fitz.open("out.pdf")
for pno in [0, -1]:
    d[pno].get_pixmap(dpi=150).save(f"/tmp/check_p{pno}.png")
```

Check for:
- Correct labels & amounts in the summary block
- No surviving yellow highlights / sticky-note popups
- No accidentally covered neighboring text (ATTN lines, addresses)
- Both summary pages (typically first and last) are correct

### Step 5 — Deliver

Send the user the PDF with a short Chinese summary of what changed.

## Primitives reference

All in `scripts/invoice_edit.py`:

| Method | Purpose |
|---|---|
| `Invoice(path)` | Open a PDF |
| `.annotations()` → `list[Annotation]` | Sticky-note instructions + anchor text + page |
| `.strip_annotations()` → `int` | Remove all annotations from every page |
| `.find_text(query, page)` → `list[Rect]` | Locate text rects (raw access) |
| `.cover(rect, page, pad=0.5)` | Paint a white rectangle (whiteout) |
| `.write(x, y, text, page, size=9)` | Insert CJK-safe text at baseline `(x, y)` |
| `.replace_block_under(anchor, new_text, *, stop_at=None, page=0, ...)` | Replace a multi-line block (BILL TO / SHIP TO style) |
| `.replace_summary_row(anchor_label, *, label=None, amount=None, delete=False, page=0)` | Edit a bottom-right summary row |
| `.delete_summary_row(anchor_label, page=0)` | Whiteout a summary row |
| `.cover_discount_amount(page=0)` | Erase orphan amount in PRODUCT DISCOUNTS detail table |
| `.save(path)` / `.close()` | IO |

Pages: 0-indexed positive integers or negative indices (`page=-1` = last page).

## Pitfalls (learned the hard way)

1. **Annotations survive `cover()`** — they're a layer above content. **Must** call `strip_annotations()` before saving, or yellow highlights/popup bubbles render on top of the white box. #1 mistake.
2. **`replace_summary_row` picks the bottom-right occurrence** of the anchor label (closest to summary block). `replace_block_under` picks the first occurrence. Verify with vision if a template has duplicates of the same label.
3. **Last-page "INVOICE TOTAL 893.10" trick**: the SYNNEX template puts the *grand* total in the SUB TOTAL slot of the last page. To "keep only INVOICE TOTAL with 893.10", relabel SUB TOTAL → INVOICE TOTAL and delete the other two rows. Do **not** delete SUB TOTAL — that wipes 893.10.
4. **`cover_discount_amount` y-range**: tuned to 35pt below the "PRODUCT DISCOUNTS" header (covers the orphan 107.00 even when other words sit just above). If a new template's discount table sits further down, bump the constant in the source.
5. **Vision-AI evaluation can mislead** — it may flag a blank AMOUNT cell as "missing data" when that's exactly what the partner wanted. Always cross-check against the reference PDF, not against an idealized invoice.
6. **CJK fonts must be embedded.** Default Helvetica can't render Chinese → blank glyphs. The helper passes `fontfile=` on every `insert_text`. Override the font path via `INVOICE_EDIT_FONT` env var if WenQuanYi is missing.
7. **Image-only invoices**: PyMuPDF cannot anchor on rasterized text. Bail out and use OCR + nano-pdf instead.

## New templates

For an invoice that isn't SYNNEX:
1. Run `.annotations()` first — if there are sticky notes, they usually tell you what to change.
2. Check whether your anchor labels (`BILL TO`, `SUB TOTAL`, `PRODUCT DISCOUNTS`, ...) exist as exact strings via `inv.find_text(label, page=N)`. If a label is split across lines or uses a different phrasing, you'll need to add a new primitive or use lower-level `.cover()` + `.write()`.
3. Validate visually before delivering.

## Files

- `scripts/invoice_edit.py` — the editing toolkit (import this)
- `scripts/example_synnex.py` — worked example reproducing the SYNNEX-template rewrite
- `templates/rewrite_synnex_csp.py` — legacy hardcoded-coords script (kept for reference only; prefer `scripts/example_synnex.py`)
