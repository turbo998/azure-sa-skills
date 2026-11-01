#!/usr/bin/env python3
"""风格账本查询：按题材 / 构图 / 动效 / 声音 反查可用的 style 条目。

用法:
    python3 style-query.py --genre tech-deep          # 该题材的默认候选（永远不含深色）
    python3 style-query.py --genre tech-deep --dark   # 追加显示深色备选（需用户拍板）
    python3 style-query.py --layout hero-plus-grid
    python3 style-query.py --motion cut-the-curve
    python3 style-query.py --sound tick
    python3 style-query.py --id paper-catalog         # 看单条完整配方
    python3 style-query.py --list                     # 全部 id
    python3 style-query.py --axes                     # 四个轴的定义
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

LEDGER = Path(__file__).resolve().parent.parent / "references" / "style-ledger.json"


def load() -> dict:
    with open(LEDGER, encoding="utf-8") as fh:
        return json.load(fh)


def line(s: dict) -> str:
    a = s["atoms"]
    dark = " 🌙" if a.get("dark") else ""
    return (
        f"{s['id']:<30}{s['name_zh']:<10}{dark:<3}"
        f" bg={a['bg']} ink={a['ink']} acc={a.get('accent','-')}"
        f" | {'/'.join(s['layouts'])}"
        f" | seam={s['motion']['seam']} route={s['motion']['route']}"
        f" | sfx={'+'.join(s['sound']['motifs'])}\n"
        f"{'':<30}气质: {s['mood']}\n"
        f"{'':<30}代价: {s['cost']}"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--genre")
    ap.add_argument("--layout")
    ap.add_argument("--motion")
    ap.add_argument("--sound")
    ap.add_argument("--id")
    ap.add_argument("--dark", action="store_true", help="包含深色条目（需用户拍板）")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--axes", action="store_true")
    args = ap.parse_args()

    L = load()
    styles = {s["id"]: s for s in L["styles"]}

    if args.axes:
        for axis, body in L["axes"].items():
            print(f"## {axis}")
            for k, v in body.items():
                if k == "note":
                    print(f"  ({v})")
                elif isinstance(v, dict):
                    for kk, vv in v.items():
                        print(f"  {kk:<24}{vv if isinstance(vv, str) else vv.get('mood','')}")
                else:
                    print(f"  {k}: {v}")
            print()
        return 0

    if args.list:
        for sid, s in styles.items():
            print(f"{sid:<30}{s['name_zh']:<10}{'🌙' if s['atoms'].get('dark') else '  '} {','.join(s['genres'])}")
        return 0

    if args.id:
        s = styles.get(args.id)
        if not s:
            print(f"no such style: {args.id}")
            return 1
        print(json.dumps(s, ensure_ascii=False, indent=2))
        return 0

    picked: list[dict] = []
    if args.genre:
        ids = L["defaults_by_genre"].get(args.genre)
        if ids is None:
            print(f"unknown genre: {args.genre}\nknown: {', '.join(k for k in L['defaults_by_genre'] if not k.startswith('_'))}")
            return 1
        picked = [styles[i] for i in ids if i in styles]
        if args.dark:
            picked += [s for s in styles.values() if s["atoms"].get("dark") and args.genre in s["genres"]]
        print(f"# genre={args.genre}  默认候选 {len(picked)} 条（深色条目标 🌙，必须用户拍板才可用）\n")
    else:
        picked = list(styles.values())
        if not args.dark:
            picked = [s for s in picked if not s["atoms"].get("dark")]
        if args.layout:
            picked = [s for s in picked if args.layout in s["layouts"]]
        if args.motion:
            picked = [s for s in picked if args.motion in (s["motion"]["seam"], s["motion"]["in_scene"])]
        if args.sound:
            picked = [s for s in picked if args.sound in s["sound"]["motifs"]]
        print(f"# 命中 {len(picked)} 条\n")

    if not picked:
        print("（无命中：这可能是 layout/motion 轴的空白，值得登记成新卡）")
        return 0
    for s in picked:
        print(line(s))
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
