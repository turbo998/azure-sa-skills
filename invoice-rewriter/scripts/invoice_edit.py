"""invoice_edit.py — Toolkit for surgical PDF invoice rewriting.

Anchor-based editing primitives that do NOT depend on hardcoded coordinates.
The agent composes these primitives based on annotation instructions parsed
from the source PDF and natural-language inputs from the user.

Usage in agent code:

    from invoice_edit import Invoice

    inv = Invoice("source.pdf")

    # Inspect what the partner annotated in the source
    for note in inv.annotations():
        print(note.page, note.text, note.anchor_text)

    # Strip annotations (they should never appear in the output)
    inv.strip_annotations()

    # Edit by text anchor — no hardcoded coords
    inv.replace_block_under("BILL TO", new_text="示例客户公司A",
                            stop_at="ATTN:")
    inv.replace_block_under("SHIP TO", new_text="示例客户公司B",
                            stop_at="ATTN:")

    # Summary row edits
    inv.replace_summary_row("SUB TOTAL",      label="HKD $")
    inv.replace_summary_row("EXTRA DISCOUNT", label="人民币含税 ￥", amount="880.42")
    inv.delete_summary_row("INVOICE TOTAL")

    # Last page: keep only INVOICE TOTAL + 893.10
    inv.replace_summary_row("SUB TOTAL", delete=True, page=-1)
    inv.replace_summary_row("EXTRA DISCOUNT", delete=True, page=-1)
    inv.replace_summary_row("INVOICE TOTAL", label="INVOICE TOTAL", page=-1)

    # Also remove orphan amounts in discount detail rows
    inv.cover_amount_at_row(label_anchor="PRODUCT DISCOUNTS",
                            row_index=0, page=-1)

    inv.save("out.pdf")

Design notes:
- All find_* methods return list of fitz.Rect, in reading order.
- All edits are stacked on top of the original page (whiteout + overprint).
- Default font is WenQuanYi (CJK-safe). Override via FONT_FILE env var if needed.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional, Sequence

import fitz  # PyMuPDF

# ---------- Font config (CJK-safe) ----------
FONT_FILE = os.environ.get(
    "INVOICE_EDIT_FONT",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
)
FONT_ALIAS = "CJK"

WHITE = (1, 1, 1)
BLACK = (0, 0, 0)


# ---------- Data classes ----------
@dataclass
class Annotation:
    """A user-authored annotation (sticky note) on the source PDF."""

    page: int                    # 0-indexed
    rect: fitz.Rect
    text: str                    # /Contents — the instruction text
    subtype: str
    anchor_text: str = ""        # nearest visible word(s) under/near the annot
    nearby_highlights: list = field(default_factory=list)


# ---------- Main facade ----------
class Invoice:
    def __init__(self, src_path: str):
        self.src_path = src_path
        self.doc = fitz.open(src_path)

    # ----- IO -----
    def save(self, out_path: str) -> None:
        self.doc.save(out_path, garbage=4, deflate=True, clean=True)

    def close(self) -> None:
        self.doc.close()

    # ----- annotations -----
    def annotations(self) -> list[Annotation]:
        """Return all sticky-note (/Text or /FreeText) annotations with
        their instruction text and the nearest underlying visible text
        (so the agent knows WHERE the instruction refers to)."""
        out: list[Annotation] = []
        for pno, page in enumerate(self.doc):
            for annot in list(page.annots() or []):
                info = annot.info
                contents = info.get("content") or ""
                sub = annot.type[1] if annot.type else ""
                if sub not in ("Text", "FreeText"):
                    continue
                if not contents.strip():
                    continue
                rect = fitz.Rect(annot.rect)
                anchor = _nearest_text(page, rect)
                out.append(Annotation(
                    page=pno, rect=rect, text=contents.strip(),
                    subtype=sub, anchor_text=anchor,
                ))
        return out

    def strip_annotations(self) -> int:
        """Remove ALL annotations from every page. Returns count removed."""
        n = 0
        for page in self.doc:
            for annot in list(page.annots() or []):
                page.delete_annot(annot)
                n += 1
        return n

    # ----- low-level primitives -----
    def _page(self, page_index):
        if page_index < 0:
            page_index += len(self.doc)
        return self.doc[page_index]

    def find_text(self, query: str, page: int = 0) -> list[fitz.Rect]:
        return list(self._page(page).search_for(query))

    def cover(self, rect, page: int = 0, pad: float = 0.5) -> None:
        r = fitz.Rect(rect[0] - pad, rect[1] - pad,
                      rect[2] + pad, rect[3] + pad)
        self._page(page).draw_rect(r, color=WHITE, fill=WHITE, width=0,
                                   overlay=True)

    def write(self, x: float, y: float, text: str, page: int = 0,
              size: float = 9.0) -> None:
        self._page(page).insert_text(
            (x, y), text, fontsize=size,
            fontname=FONT_ALIAS, fontfile=FONT_FILE, color=BLACK,
        )

    # ----- high-level edits -----
    def replace_block_under(
        self, anchor: str, new_text: str, *,
        stop_at: Optional[str] = None,
        page: int = 0,
        x_margin: float = 5.0,
        max_height: float = 80.0,
        size: float = 9.0,
    ) -> bool:
        """Replace the text block beneath an anchor label like 'BILL TO'.

        The block spans from just under the anchor down to either the
        `stop_at` text (e.g. 'ATTN:') or `max_height` pts.
        Width is bounded by the anchor's column (heuristic: half page width
        starting at the anchor's x0).
        """
        page_obj = self._page(page)
        rects = page_obj.search_for(anchor)
        if not rects:
            return False
        anc = rects[0]
        col_x0 = anc.x0 - x_margin
        # Column width: half the page (BILL TO / SHIP TO are 2-col layout)
        page_w = page_obj.rect.width
        col_x1 = col_x0 + page_w / 2 - x_margin

        y_top = anc.y1 + 1
        y_bottom = y_top + max_height
        if stop_at:
            for r in page_obj.search_for(stop_at):
                if r.x0 < col_x1 and r.y0 > y_top and r.y0 < y_bottom:
                    y_bottom = r.y0 - 1
                    break

        self.cover((col_x0, y_top, col_x1, y_bottom), page=page)
        # Write replacement at top of the cleared band
        self.write(anc.x0, y_top + size + 1, new_text, page=page, size=size)
        return True

    def _row_y(self, label: str, page_obj) -> Optional[fitz.Rect]:
        rects = page_obj.search_for(label)
        if not rects:
            return None
        # Pick the rect closest to bottom-right of page (summary block)
        rects.sort(key=lambda r: (-(r.y0 + r.x0)))
        return rects[0]

    def replace_summary_row(
        self, anchor_label: str, *,
        label: Optional[str] = None,
        amount: Optional[str] = None,
        delete: bool = False,
        page: int = 0,
        size: float = 9.0,
        amount_col_x: Optional[float] = None,
    ) -> bool:
        """Edit one of the bottom-right summary rows.

        anchor_label: the original label text, e.g. 'SUB TOTAL'.
        label: replacement label text (None = keep blank).
        amount: replacement amount string (None = keep original number).
        delete: cover the entire row, write nothing.
        amount_col_x: x position to write the amount (defaults to right edge
                      column inferred from the original numeric word).
        """
        page_obj = self._page(page)
        rect = self._row_y(anchor_label, page_obj)
        if rect is None:
            return False

        # Row band: a horizontal stripe centered on the label row.
        row_y0 = rect.y0 - 4
        row_y1 = rect.y1 + 4
        # Cover the label area
        label_x0 = rect.x0 - 50
        label_x1 = rect.x1 + 5
        self.cover((label_x0, row_y0, label_x1, row_y1), page=page)

        # Find the amount on the same row (to the right, x > label_x1)
        words = page_obj.get_text("words")
        amount_word = None
        for w in words:
            wx0, wy0, wx1, wy1, txt, *_ = w
            if wy0 >= row_y0 and wy1 <= row_y1 and wx0 > label_x1:
                # numeric?
                if any(ch.isdigit() for ch in txt):
                    amount_word = w
                    break

        if delete:
            if amount_word:
                ax0, ay0, ax1, ay1 = amount_word[:4]
                self.cover((ax0 - 2, ay0 - 2, ax1 + 2, ay1 + 2), page=page)
            return True

        if label:
            # Write new label at the anchor's original x
            self.write(rect.x0, rect.y1, label, page=page, size=size)

        if amount is not None and amount_word is not None:
            ax0, ay0, ax1, ay1 = amount_word[:4]
            self.cover((ax0 - 2, ay0 - 2, ax1 + 2, ay1 + 2), page=page)
            x = amount_col_x if amount_col_x is not None else ax0
            self.write(x, ay1, amount, page=page, size=size)

        return True

    def delete_summary_row(self, anchor_label: str, page: int = 0) -> bool:
        return self.replace_summary_row(
            anchor_label, delete=True, page=page)

    def cover_discount_amount(self, page: int = 0) -> bool:
        """Remove the orphan amount that appears in the PRODUCT DISCOUNTS
        detail table (right column, top row of discount table).

        Scans for a numeric word in the rightmost column within ~20pt
        below the 'PRODUCT DISCOUNTS' header and covers just that word.
        """
        page_obj = self._page(page)
        rects = page_obj.search_for("PRODUCT DISCOUNTS")
        if not rects:
            return False
        anc = rects[0]
        page_w = page_obj.rect.width
        y0, y1 = anc.y1, anc.y1 + 35
        for w in page_obj.get_text("words"):
            wx0, wy0, wx1, wy1, txt, *_ = w
            if (wy0 >= y0 and wy1 <= y1
                    and wx0 > page_w - 90
                    and any(ch.isdigit() for ch in txt)):
                self.cover((wx0 - 2, wy0 - 1, wx1 + 2, wy1 + 1), page=page)
                return True
        return False


# ---------- helpers ----------
def _nearest_text(page, rect: fitz.Rect, search_radius: float = 80) -> str:
    """Return up to ~6 nearest words around the given rect, joined."""
    words = page.get_text("words")
    cx = (rect.x0 + rect.x1) / 2
    cy = (rect.y0 + rect.y1) / 2
    scored = []
    for w in words:
        wx = (w[0] + w[2]) / 2
        wy = (w[1] + w[3]) / 2
        d = ((wx - cx) ** 2 + (wy - cy) ** 2) ** 0.5
        if d <= search_radius:
            scored.append((d, w))
    scored.sort(key=lambda t: t[0])
    return " ".join(w[1][4] for w in scored[:8])
