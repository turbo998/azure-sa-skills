#!/usr/bin/env python3
"""风格卡片生成器：把 style-ledger.json 的每条 style 渲染成一张 1920×1080 的「风格卡」PNG。

每张卡用自己的 atoms 上色 —— 所以卡本身就是那个风格，不是配色表的截图。
产物：references/gallery/<id>.html + <id>.png + index.html

用法:
    python3 gallery-gen.py [--out DIR] [--only id1,id2] [--no-render]

渲染依赖本机 chrome-headless-shell（不下载任何东西）。
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "references" / "style-ledger.json"
DEFAULT_OUT = ROOT / "references" / "gallery"

CHROME_CANDIDATES = [
    Path.home() / ".cache/puppeteer/chrome-headless-shell",
]

# 构图轴 → 线框示意图（纯 div 拼，不依赖图片）
WIREFRAMES = {
    "hero-plus-grid": "hero",
    "numbered-sections": "numbered",
    "two-column-corridor": "corridor",
    "banded-three": "banded",
    "one-shot-world": "world",
    "poster-full-bleed": "poster",
    "editorial-grid": "grid",
    "centered-hero": "centered",
    "card-deck": "deck",
    "data-dashboard": "dash",
    "timeline-rail": "rail",
    "split-compare": "split",
    "ui-stage": "uistage",
    "code-panel": "codepanel",
    "progressive-node-tree": "nodetree",
    "funnel-stage-filter": "funnel",
    "gpu-matrix-ledger": "gpumatrix",
}

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1920px;height:1080px;overflow:hidden}
body{background:var(--bg);color:var(--ink);font-family:var(--body);position:relative}
.safe{position:absolute;left:96px;top:72px;width:1728px;height:936px}
.chrome{font-family:var(--mono);font-size:19px;letter-spacing:.16em;text-transform:uppercase;
  color:var(--ink);opacity:.55}
.hair{height:1px;background:currentColor;opacity:.22;width:100%}
/* 左：名称区 */
.title{font-family:var(--display);font-size:112px;line-height:.98;letter-spacing:-.02em;margin-top:18px}
.sub{font-family:var(--mono);font-size:23px;letter-spacing:.1em;opacity:.6;margin-top:16px}
.mood{font-size:27px;line-height:1.6;margin-top:34px;max-width:660px;opacity:.86}
.cost{font-size:21px;line-height:1.55;margin-top:22px;max-width:660px;opacity:.5}
.acc-bar{width:96px;height:7px;background:var(--acc);margin-top:30px}
/* 右：调色板 */
.sw{display:flex;gap:0;margin-top:12px}
.sw>div{height:104px;flex:1;position:relative}
.sw .hex{position:absolute;left:14px;bottom:12px;font-family:var(--mono);font-size:15px;opacity:.55;letter-spacing:.04em}
/* 线框 */
.wire{position:relative;border:1.5px solid currentColor;opacity:.5}
.wire i{position:absolute;display:block}
.wire .solid{background:var(--acc);opacity:.55}
.wire .soft{background:var(--ink);opacity:.16}
.tags{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px}
.tag{font-family:var(--mono);font-size:16px;letter-spacing:.1em;text-transform:uppercase;
  border:1px solid currentColor;padding:7px 13px;opacity:.7}
.tag.acc{border-color:var(--acc);color:var(--acc);opacity:1}
"""


def wireframe(kind: str) -> str:
    """返回一段绝对定位的 div 结构，示意构图。容器 760×420。"""
    W, H = 760, 420
    boxes = []
    def b(x, y, w, h, cls="solid"):
        boxes.append(f'<i class="{cls}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px"></i>')
    if kind == "hero":
        b(0, 0, 400, 420, "soft"); b(424, 0, 336, 120); b(424, 140, 160, 130, "soft")
        b(600, 140, 160, 130, "soft"); b(424, 290, 336, 130, "soft")
    elif kind == "numbered":
        b(0, 0, 120, 96); b(150, 10, 520, 34); b(150, 62, 400, 18, "soft")
        for i, y in enumerate((170, 250, 330)):
            b(0, y, 60, 60, "soft"); b(86, y + 6, 500 - i * 60, 16, "soft"); b(86, y + 32, 340, 12, "soft")
    elif kind == "corridor":
        for i, y in enumerate((0, 110, 220, 330)):
            b(0, y, 300, 92, "soft")
        b(450, 40, 310, 340, "solid"); b(330, 200, 90, 3, "solid")
    elif kind == "banded":
        b(0, 0, 400, 26); b(0, 46, 700, 120, "soft"); b(0, 300, 760, 3)
        b(0, 316, 120, 16, "soft"); b(140, 316, 120, 16, "soft"); b(280, 316, 120, 16, "soft")
    elif kind == "world":
        for i in range(4):
            b(i * 190, 40, 170, 340, "soft")
        b(560, 40, 200, 340, "solid")
    elif kind == "poster":
        b(0, 60, 700, 110); b(0, 190, 560, 110); b(0, 330, 300, 20, "soft")
    elif kind == "grid":
        for r in range(3):
            for c in range(4):
                b(c * 192, r * 145, 180, 130, "soft" if (r + c) % 3 else "solid")
    elif kind == "centered":
        b(230, 110, 300, 200, "solid"); b(300, 340, 160, 14, "soft")
    elif kind == "deck":
        for i, (x, y) in enumerate(((0, 120), (140, 90), (280, 60), (420, 30))):
            b(x, y, 300, 240, "soft" if i < 3 else "solid")
    elif kind == "dash":
        for i in range(3):
            b(i * 260, 0, 240, 150, "soft")
        b(0, 180, 500, 220, "solid"); b(530, 180, 230, 220, "soft")
    elif kind == "rail":
        b(60, 0, 3, 420, "solid")
        for i, y in enumerate((30, 130, 230, 330)):
            b(40, y, 44, 3); b(120, y - 8, 460, 18, "soft")
    elif kind == "split":
        b(0, 0, 350, 420, "soft"); b(400, 0, 360, 420, "solid"); b(355, 0, 3, 420)
    elif kind == "uistage":
        b(170, 60, 420, 300, "solid"); b(200, 96, 360, 26, "soft"); b(200, 136, 200, 12, "soft")
        b(200, 166, 300, 12, "soft"); b(200, 220, 340, 90, "soft")
    elif kind == "codepanel":
        b(0, 0, 60, 420, "soft")
        for i, y in enumerate(range(30, 400, 46)):
            b(90, y, 260 + (i % 4) * 90, 14, "soft" if i % 5 else "solid")
    elif kind == "nodetree":
        b(20, 20, 140, 28, "solid")
        b(30, 170, 150, 80, "soft")
        for i, y in enumerate((70, 175, 280)):
            b(190, y + 36, 90, 3, "solid" if i == 0 else "soft")
            b(290, y, 210, 76, "solid" if i == 0 else "soft")
        b(540, 90, 190, 240, "soft")
    elif kind == "funnel":
        b(20, 16, 720, 16, "soft")
        for i, (x, y, h) in enumerate(((20, 60, 300), (205, 85, 250), (390, 115, 190), (575, 145, 130))):
            b(x, y, 165, h, "solid" if i in (0, 2) else "soft")
    elif kind == "gpumatrix":
        b(20, 18, 460, 42, "solid")
        for r in range(4):
            for c in range(6):
                b(20 + c * 72, 84 + r * 76, 60, 62, "solid" if (r + c) % 3 == 0 else "soft")
        b(476, 84, 264, 150, "solid")
        b(476, 254, 264, 134, "soft")
    else:
        b(0, 0, 760, 420, "soft")
    return f'<div class="wire" style="width:{W}px;height:{H}px">' + "".join(boxes) + "</div>"


def plain(text: str) -> str:
    """去掉账本里的 markdown 强调标记，避免字面渲染 **。"""
    return text.replace("**", "").replace("`", "")


def label_color(hexv: str) -> str:
    """按背景亮度选标签色，避免深色块上的字看不见。"""
    h = hexv.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in (r, g, b)]
    lum = 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
    return "#FFFFFF" if lum < 0.45 else "#111111"


def card_html(s: dict, led: dict) -> str:
    a = s["atoms"]
    bg, ink = a["bg"], a["ink"]
    acc = a.get("accent", ink)
    aux = a.get("aux", acc)
    f = s["fonts"]
    dark = a.get("dark", False)
    wire = WIREFRAMES.get(s["layouts"][0], "grid")
    swatches = [(bg, "BG"), (ink, "INK"), (acc, "ACC")] + ([(aux, "AUX")] if aux != acc else [])
    sw_html = "".join(
        f'<div style="background:{c};border:1px solid rgba({"255,255,255" if dark else "0,0,0"},.14)">'
        f'<span class="hex" style="color:{label_color(c)}">{c.upper()} · {n}</span></div>'
        for c, n in swatches
    )
    tags = "".join(f'<span class="tag{" acc" if i == 0 else ""}">{t}</span>'
                   for i, t in enumerate(s["layouts"][:2] + [s["motion"]["seam"]] + s["sound"]["motifs"][:2]))
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
:root{{--bg:{bg};--ink:{ink};--acc:{acc};--aux:{aux};
 --display:"{f['display']}",Songti SC,PingFang SC,serif;
 --body:"{f['body']}",PingFang SC,sans-serif;
 --mono:"{f['mono']}",Menlo,monospace}}
{CSS}</style></head><body>
<div class="safe">
  <div style="display:flex;gap:56px;height:100%">
    <div style="width:760px;display:flex;flex-direction:column">
      <div class="chrome">style-ledger · {s['id']}</div>
      <div class="title">{s['name_zh']}</div>
      <div class="sub">{s['name_en']}{'  ·  DARK (needs approval)' if dark else ''}</div>
      <div class="acc-bar"></div>
      <div class="mood">{plain(s['mood'])}</div>
      <div class="cost">代价 · {plain(s['cost'])}</div>
      <div style="margin-top:46px">
        <div class="hair" style="margin-bottom:16px"></div>
        <div class="chrome" style="margin-bottom:14px">type specimen</div>
        <div style="font-family:var(--display);font-size:58px;line-height:1.05;letter-spacing:-.01em">标题四到八字</div>
        <div style="font-size:26px;line-height:1.5;margin-top:14px;opacity:.85">副句不超过十个字，一眼读完</div>
        <div style="font-family:var(--mono);font-size:17px;letter-spacing:.14em;margin-top:14px;color:var(--acc)">标签 · 六字内 · LABEL</div>
      </div>
      <div style="margin-top:auto">
        <div class="tags">{tags}</div>
      </div>
    </div>
    <div style="width:912px;display:flex;flex-direction:column">
      <div class="chrome" style="margin-bottom:14px">layout · {s['layouts'][0]}</div>
      <div style="opacity:{0.92 if dark else 0.7};transform-origin:left top;transform:scale(1.2)">
        {wireframe(wire)}
      </div>
      <div style="margin-top:56px">
        <div class="hair" style="margin-bottom:16px"></div>
        <div class="chrome" style="margin-bottom:12px">palette</div>
        <div class="sw">{sw_html}</div>
      </div>
      <div style="margin-top:auto" class="chrome">
        motion {s['motion']['seam']} · route {s['motion']['route']} · sound {'+'.join(s['sound']['motifs'])} · bgm {s['sound'].get('bgm','-')}
      </div>
    </div>
  </div>
</div></body></html>"""


def index_html(styles: list[dict]) -> str:
    cells = "".join(
        f'<a class="cell" href="{s["id"]}.png"><img src="{s["id"]}.png" loading="lazy">'
        f'<div class="cap"><b>{s["name_zh"]}</b><span>{s["id"]}</span></div></a>'
        for s in styles
    )
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>style gallery</title><style>
body{{background:#EDE8E0;color:#1A1A1A;font-family:PingFang SC,sans-serif;margin:0;padding:56px}}
h1{{font-family:Songti SC,serif;font-size:52px;margin:0 0 8px}}
p{{font-family:Menlo,monospace;font-size:15px;opacity:.6;margin:0 0 40px;letter-spacing:.06em}}
.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:28px}}
.cell{{text-decoration:none;color:inherit}}
.cell img{{width:100%;border:1px solid rgba(0,0,0,.16);display:block}}
.cap{{display:flex;justify-content:space-between;margin-top:9px;font-size:15px}}
.cap span{{font-family:Menlo,monospace;opacity:.5;font-size:13px}}
</style></head><body><h1>风格账本 · {len(styles)} 条</h1>
<p>每张卡用自己的 atoms 上色 · 点开看全尺寸</p><div class="grid">{cells}</div></body></html>"""


def find_chrome() -> str | None:
    for base in CHROME_CANDIDATES:
        if not base.exists():
            continue
        cands = sorted(base.glob("*/chrome-headless-shell-mac-*/chrome-headless-shell"))
        if cands:
            return str(cands[-1])
    return shutil.which("chrome-headless-shell") or shutil.which("chromium")


def render(chrome: str, html: Path, png: Path) -> tuple[bool, str]:
    proc = subprocess.run(
        [chrome, "--headless", "--disable-gpu", "--hide-scrollbars", "--no-sandbox",
         "--window-size=1920,1080", "--virtual-time-budget=2500", f"--screenshot={png}", f"file://{html}"],
        capture_output=True, text=True, timeout=120,
    )
    ok = png.exists() and png.stat().st_size > 5000
    return ok, ("" if ok else (proc.stderr or proc.stdout)[-300:])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--only", default="")
    ap.add_argument("--no-render", action="store_true")
    args = ap.parse_args()

    led = json.loads(LEDGER.read_text(encoding="utf-8"))
    styles = led["styles"]
    if args.only:
        want = {x.strip() for x in args.only.split(",")}
        styles = [s for s in styles if s["id"] in want]

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for s in styles:
        (out / f"{s['id']}.html").write_text(card_html(s, led), encoding="utf-8")
    (out / "index.html").write_text(index_html(styles), encoding="utf-8")
    print(f"html: {len(styles)} cards + index → {out}")

    if args.no_render:
        return 0
    chrome = find_chrome()
    if not chrome:
        print("BLOCK: 找不到 chrome-headless-shell，只生成了 HTML")
        return 1
    print(f"chrome: {chrome}")
    bad = []
    for s in styles:
        ok, err = render(chrome, out / f"{s['id']}.html", out / f"{s['id']}.png")
        print(("  OK   " if ok else "  FAIL ") + s["id"] + ("" if ok else f"  {err}"))
        if not ok:
            bad.append(s["id"])
    print(f"GATE: {'PASS' if not bad else f'BLOCK ({len(bad)})'}")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
