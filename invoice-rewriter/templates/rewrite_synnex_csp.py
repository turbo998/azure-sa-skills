"""SYNNEX CSP-Azure invoice rewriter — reference implementation.

Takes the original invoice PDF and produces a per-customer version:
- Replaces BILL TO company name
- Replaces SHIP TO company name
- Rewrites page 1 summary block to two-row form: HKD $ <amt> / <fx-label> <fx-amt>
- Rewrites final page summary block to single-row: INVOICE TOTAL <amt>
- Strips all PDF annotations

Layout coordinates are calibrated for the SYNNEX TECHNOLOGY INTERNATIONAL (HK) LTD
invoice template (page size A4, 595x842pt). For other templates, recalibrate by
running `page.get_text('words')` and updating the cover/write coordinates.
"""
import fitz

# ---- Inputs (turn these into CLI flags when productionizing) ----
SRC = '/path/to/original_invoice.pdf'
OUT = '/path/to/rewritten_invoice.pdf'

BILL_TO_NAME = '示例客户公司A'
SHIP_TO_NAME = '示例客户公司B'
PRIMARY_AMOUNT = '893.10'             # the HKD amount (kept from original)
FX_LABEL = '人民币含税 ￥'             # second-currency label (set to None to skip row 2)
FX_AMOUNT = '880.42'                  # converted amount

# ---- Font (must support CJK) ----
FONT_FILE = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
FONT_ALIAS = 'CJK'

WHITE = (1, 1, 1)
BLACK = (0, 0, 0)


def strip_annots(doc: fitz.Document) -> None:
    """Remove every annotation from every page. CRITICAL — otherwise yellow
    highlights / sticky-note popups will render on top of the new content."""
    for page in doc:
        for annot in list(page.annots() or []):
            page.delete_annot(annot)


def cover(page: fitz.Page, rect, pad: float = 0.5) -> None:
    """Paint a white rectangle to erase original content underneath."""
    r = fitz.Rect(rect[0] - pad, rect[1] - pad, rect[2] + pad, rect[3] + pad)
    page.draw_rect(r, color=WHITE, fill=WHITE, width=0, overlay=True)


def write_text(page: fitz.Page, x: float, y: float, text: str, size: float = 9) -> None:
    """Write text at baseline (x, y). Top-left origin; y grows downward."""
    page.insert_text(
        (x, y), text,
        fontsize=size,
        fontname=FONT_ALIAS,
        fontfile=FONT_FILE,
        color=BLACK,
    )


def rewrite_page1(page: fitz.Page) -> None:
    """Page 1: BILL TO + SHIP TO + two-row summary."""
    # BILL TO (left column): cover company-name line and address line,
    # KEEP the ATTN row (y≈206) and below.
    cover(page, (28, 138, 290, 152))   # SUPERPOP HK LTD line
    cover(page, (28, 165, 290, 192))   # address line(s)
    write_text(page, 28, 148, BILL_TO_NAME)

    # SHIP TO (right column): same idea
    cover(page, (302, 138, 560, 152))   # 香港威利有限公司
    cover(page, (302, 165, 560, 192))   # HONG KONG... GRANVILLE...
    write_text(page, 302, 148, SHIP_TO_NAME)

    # Summary block (bottom right). Original three rows:
    #   SUB TOTAL       893.10   (label y≈701, num y≈699)
    #   EXTRA DISCOUNT  107.00   (label y≈731, num y≈729)
    #   INVOICE TOTAL   786.10   (label y≈761, num y≈759)
    # Target: HKD $ 893.10 / FX-label FX-amount / (blank)
    cover(page, (380, 695, 480, 770))   # all three labels
    cover(page, (530, 725, 565, 770))   # second + third amounts (keep 893.10)
    write_text(page, 420, 709, 'HKD $')
    if FX_LABEL and FX_AMOUNT:
        write_text(page, 392, 739, FX_LABEL)
        write_text(page, 535, 739, FX_AMOUNT)

    # PRODUCT DISCOUNTS detail-row amount (107.00) at top of discount table
    cover(page, (530, 666, 565, 685))


def rewrite_final_page(page: fitz.Page) -> None:
    """Final page: collapse summary to single row 'INVOICE TOTAL <amt>'."""
    cover(page, (380, 770, 480, 815))   # all three labels (SUB / EXTRA / INVOICE)
    cover(page, (530, 783, 565, 815))   # 107.00 and 786.10 (keep 893.10)
    write_text(page, 402, 786, 'INVOICE TOTAL')
    # discount detail-row amount
    cover(page, (530, 760, 565, 778))


def main() -> None:
    doc = fitz.open(SRC)
    strip_annots(doc)
    rewrite_page1(doc[0])
    rewrite_final_page(doc[-1])         # always last page, regardless of count
    doc.save(OUT, garbage=4, deflate=True, clean=True)
    print(f'Wrote {OUT}')


if __name__ == '__main__':
    main()
