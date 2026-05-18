"""Validate invoice_edit.py against the sample SYNNEX invoice — no hardcoded coords."""
import sys
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from invoice_edit import Invoice

SRC = '/home/azureuser/.hermes/profiles/fde/cache/documents/doc_cd9651da18b3_原始文件.pdf'
OUT = '/tmp/invoice_v3.pdf'

inv = Invoice(SRC)

# Inspect partner annotations
print("=== Annotations ===")
for a in inv.annotations():
    print(f"  P{a.page+1} near {a.anchor_text!r}")
    print(f"    INSTRUCTION: {a.text}")
    print()

# Strip annotations
n = inv.strip_annotations()
print(f"Stripped {n} annotations\n")

# Apply edits derived from those instructions
inv.replace_block_under("BILL TO", "示例客户公司A", stop_at="ATTN:", page=0)
inv.replace_block_under("SHIP TO", "示例客户公司B",       stop_at="ATTN:", page=0)

# Page 1 summary: HKD$ + 第二货币 + delete invoice total row
inv.replace_summary_row("SUB TOTAL",      label="HKD $",          page=0)
inv.replace_summary_row("EXTRA DISCOUNT", label="人民币含税 ￥",  amount="880.42", page=0)
inv.delete_summary_row("INVOICE TOTAL", page=0)
inv.cover_discount_amount(page=0)

# Last page: only "INVOICE TOTAL 893.10" remains
# (relabel SUB TOTAL row -> INVOICE TOTAL, keeping its 893.10 amount,
#  then delete EXTRA DISCOUNT and the old INVOICE TOTAL rows)
inv.delete_summary_row("INVOICE TOTAL", page=-1)
inv.delete_summary_row("EXTRA DISCOUNT", page=-1)
inv.replace_summary_row("SUB TOTAL", label="INVOICE TOTAL", page=-1)
inv.cover_discount_amount(page=-1)

inv.save(OUT)
print(f"Wrote {OUT}")
