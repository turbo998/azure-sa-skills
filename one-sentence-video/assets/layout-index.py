#!/usr/bin/env python3
"""构图轴索引：给 hyperframes registry 的 block 按 layout 原型打标签。

registry 自带的 tags 是**功能轴**（transition / typography / reveal），没有**构图轴**。
Step 4「能装不手写」因此只能按功能找块，找出来的块构图随机 → 每镜构图一样。
本脚本补的就是构图轴。

用法:
    python3 layout-index.py --build [--catalog output/catalog.json]   # 重建索引
    python3 layout-index.py --layout numbered-sections                # 按构图查块
    python3 layout-index.py --style paper-catalog                     # 该 style 的构图 → 可用块
    python3 layout-index.py --report                                  # 覆盖率报告

判据：只给 1920×1080 或可裁的横屏块打标签；置信度 < 2 分记为 unclassified，不硬塞。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "references" / "style-ledger.json"
INDEX = ROOT / "references" / "layout-index.json"

# 构图原型 → 关键词（命中 title/description/tags 任一处计分；强词 2 分，弱词 1 分）
SIGNALS: dict[str, dict[str, list[str]]] = {
    "hero-plus-grid":     {"strong": ["hero and grid", "thumbnail grid", "gallery grid", "image grid"],
                           "weak": ["gallery", "grid", "carousel", "thumbnails"]},
    "numbered-sections":  {"strong": ["numbered", "index", "chapter", "table of contents"],
                           "weak": ["list", "steps", "agenda"]},
    "two-column-corridor": {"strong": ["two column", "split panel", "before after"],
                            "weak": ["compare", "side by side", "versus"]},
    "banded-three":       {"strong": ["lower third", "band", "banner", "ticker"],
                           "weak": ["caption", "label strip"]},
    "one-shot-world":     {"strong": ["camera move", "pan across", "world", "parallax", "scroll through"],
                           "weak": ["camera", "2.5d", "dolly", "tracking"]},
    "poster-full-bleed":  {"strong": ["full bleed", "poster", "giant type", "billboard"],
                           "weak": ["big type", "display type", "headline"]},
    "editorial-grid":     {"strong": ["editorial", "magazine", "newspaper", "column layout"],
                           "weak": ["columns", "hairline", "rules"]},
    "centered-hero":      {"strong": ["centered", "center stage", "logo lockup", "title card"],
                           "weak": ["logo", "lockup", "hero", "centered"]},
    "card-deck":          {"strong": ["card stack", "card deck", "deal", "fan of cards", "tumble"],
                           "weak": ["card", "cards", "deck", "stack"]},
    "data-dashboard":     {"strong": ["dashboard", "chart", "graph", "kpi", "axis"],
                           "weak": ["data", "metric", "stat", "number", "counter"]},
    "timeline-rail":      {"strong": ["timeline", "progress rail", "stepper", "roadmap"],
                           "weak": ["step", "progress", "sequence"]},
    "split-compare":      {"strong": ["split screen", "side by side", "before after", "comparison"],
                           "weak": ["compare", "versus", "vs"]},
    "ui-stage":           {"strong": ["app showcase", "device mockup", "browser window", "product demo", "ui tour"],
                           "weak": ["showcase", "app", "ui", "mock", "screen", "device"]},
    "code-panel":         {"strong": ["code editor", "terminal", "diff", "syntax", "code animation"],
                           "weak": ["code", "developer", "line"]},
    "progressive-node-tree": {"strong": ["node tree", "bezier tree", "mindmap", "topology", "node graph"],
                              "weak": ["tree", "node", "branch", "graph", "hierarchy"]},
    "funnel-stage-filter":   {"strong": ["funnel", "pipeline stage", "multi stage", "filter flow"],
                              "weak": ["pipeline", "stage", "filter", "flow", "chunk"]},
    "gpu-matrix-ledger":     {"strong": ["gpu matrix", "token matrix", "unit economics", "grid ledger"],
                              "weak": ["matrix", "ledger", "throughput", "gpu", "cost"]},
}

# 角色分类：不是所有块都该被塞进构图轴
ROLE_TAGS = {
    "background": {"webgpu", "webgpu-shader", "background", "texture", "light", "aurora", "gradient"},
    "transition": {"transition", "transitions-dev-port", "transition-primitive"},
    "caption": {"captions", "caption-style", "lower-third"},
    "object": {"3d", "object", "chrome", "metal", "glass"},
}


def role_of(b: dict) -> str:
    tags = {t.lower() for t in (b.get("tags") or [])}
    for role, keys in ROLE_TAGS.items():
        if tags & keys:
            return role
    return "layout"


def score_block(b: dict) -> dict[str, int]:
    raw = " ".join([
        b.get("name", ""), b.get("title", ""), b.get("description", ""),
        " ".join(b.get("tags") or []),
    ]).lower()
    # registry 的 tags 带连字符（title-card / card-stack / lower-third），
    # 直接做词边界匹配会全部漏掉 —— 统一把 - 和 _ 折成空格。
    hay = re.sub(r"[-_]+", " ", raw)
    out: dict[str, int] = {}
    for layout, sig in SIGNALS.items():
        s = 0
        for w in sig["strong"]:
            if w in hay:
                s += 2
        for w in sig["weak"]:
            if re.search(rf"\b{re.escape(w)}\b", hay):
                s += 1
        if s:
            out[layout] = s
    return out


def build(catalog_path: Path) -> dict:
    data = json.loads(catalog_path.read_text(encoding="utf-8"))
    blocks = [b for b in data if b.get("type") == "block"]
    landscape = [
        b for b in blocks
        if (b.get("dimensions") or {}).get("width") in (1920, 1440) or not (b.get("dimensions") or {}).get("width")
    ]
    entries = []
    for b in landscape:
        role = role_of(b)
        sc = score_block(b)
        ranked = sorted(sc.items(), key=lambda kv: -kv[1])
        primary = [k for k, v in ranked if v >= 2][:2] if role == "layout" else []
        entries.append({
            "name": b["name"],
            "title": b.get("title", ""),
            "duration": b.get("duration"),
            "dims": b.get("dimensions"),
            "tags": b.get("tags") or [],
            "role": role,
            "layouts": primary or (["unclassified"] if role == "layout" else []),
            "scores": dict(ranked[:3]),
        })
    layout_role = [e for e in entries if e["role"] == "layout"]
    covered = sum(1 for e in layout_role if e["layouts"] != ["unclassified"])
    roles: dict[str, int] = {}
    for e in entries:
        roles[e["role"]] = roles.get(e["role"], 0) + 1
    by_layout: dict[str, list[str]] = {k: [] for k in SIGNALS}
    by_layout["unclassified"] = []
    for e in entries:
        key = e["layouts"][0] if e["layouts"] else f"role:{e['role']}"
        by_layout.setdefault(key, []).append(e["name"])
    return {
        "_note": "构图轴索引。由 layout-index.py --build 生成，不要手改。registry 自带 tags 是功能轴，这里是构图轴。",
        "source_catalog": str(catalog_path),
        "total_blocks": len(blocks),
        "landscape_blocks": len(landscape),
        "classified": covered,
        "layout_role_total": len(layout_role),
        "coverage": round(covered / max(1, len(layout_role)), 3),
        "roles": roles,
        "by_layout": by_layout,
        "blocks": entries,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--catalog", default="output/catalog.json")
    ap.add_argument("--layout")
    ap.add_argument("--style")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()

    if args.build:
        cat = Path(args.catalog)
        if not cat.exists():
            print(f"BLOCK: 找不到 {cat}；先跑 npx hyperframes catalog --json > {cat}")
            return 1
        idx = build(cat)
        INDEX.write_text(json.dumps(idx, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"built: 横屏块 {idx['landscape_blocks']}，角色分布 {idx['roles']}")
        print(f"  其中 layout 角色 {idx['layout_role_total']} 块，构图已分类 "
              f"{idx['classified']}（{idx['coverage']*100:.0f}%）→ {INDEX}")
        for k, v in sorted(idx["by_layout"].items(), key=lambda kv: -len(kv[1])):
            print(f"  {k:<22}{len(v)}")
        return 0

    if not INDEX.exists():
        print("索引不存在，先 --build")
        return 1
    idx = json.loads(INDEX.read_text(encoding="utf-8"))

    if args.report:
        print(f"横屏块 {idx['landscape_blocks']} / 全 block {idx['total_blocks']}")
        print(f"角色分布: {idx.get('roles')}")
        print(f"layout 角色 {idx.get('layout_role_total')} 块，构图已分类 "
              f"{idx['classified']}（{idx['coverage']*100:.0f}%）")
        for k, v in sorted(idx["by_layout"].items(), key=lambda kv: -len(kv[1])):
            print(f"  {k:<22}{len(v):>3}")
        return 0

    layouts = []
    if args.style:
        led = json.loads(LEDGER.read_text(encoding="utf-8"))
        entry = next((s for s in led["styles"] if s["id"] == args.style), None)
        if not entry:
            print(f"no such style: {args.style}")
            return 1
        layouts = entry["layouts"]
        print(f"# style {args.style}（{entry['name_zh']}）的构图 → 可用现成块\n")
    elif args.layout:
        layouts = [args.layout]
    else:
        ap.print_help()
        return 1

    for lay in layouts:
        names = idx["by_layout"].get(lay, [])
        print(f"## {lay}  ({len(names)} 块)")
        for n in names[:12]:
            print(f"   {n}")
        if not names:
            print("   （空：这一构型没有现成块，手写并在台账写明无命中）")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
