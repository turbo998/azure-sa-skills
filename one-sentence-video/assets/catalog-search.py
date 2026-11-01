#!/usr/bin/env python3
"""Search a HyperFrames catalog JSON dump locally.

CLI 0.7.87 has no `catalog --query`; dump the full catalog and filter here.

用法:
    python3 catalog-search.py <catalog.json> "kinetic typography poster" \
        [--type block|component] [--tag text] [--top 8]

无命中时打印 NO HITS 和一行 feedback 命令，方便台账记录。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def tokens(text: str) -> list[str]:
    return [t for t in re.split(r"[^a-z0-9]+", text.lower()) if t]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("catalog")
    ap.add_argument("query")
    ap.add_argument("--type", dest="type", default=None, choices=["block", "component"])
    ap.add_argument("--tag", dest="tag", default=None)
    ap.add_argument("--top", type=int, default=8)
    args = ap.parse_args()

    items = json.loads(Path(args.catalog).read_text(encoding="utf-8"))
    q = tokens(args.query)
    if not q:
        print("No searchable words in query", file=sys.stderr)
        return 2

    scored = []
    for item in items:
        if args.type and item.get("type") != args.type:
            continue
        tags = [str(t).lower() for t in item.get("tags", [])]
        if args.tag and args.tag.lower() not in tags:
            continue
        name = str(item.get("name", "")).lower()
        title = str(item.get("title", "")).lower()
        desc = str(item.get("description", "")).lower()
        score = 0
        for tok in q:
            if tok in name:
                score += 4
            if tok in title:
                score += 3
            if tok in tags:
                score += 2
            if tok in desc:
                score += 1
        if score:
            scored.append((score, item))

    scored.sort(key=lambda pair: (-pair[0], pair[1].get("name", "")))
    if not scored:
        print("NO HITS")
        print(
            'feedback: npx hyperframes feedback --search-miss "%s" --wanted "<想要的效果>"'
            % args.query
        )
        return 0

    for rank, (score, item) in enumerate(scored[: args.top], 1):
        dim = item.get("dimensions", {})
        print(
            f"{rank:>2}. {item.get('name')}  [{item.get('type')}]  score={score}  "
            f"dur={item.get('duration')}  {dim.get('width')}x{dim.get('height')}"
        )
        print(f"    title: {item.get('title')}")
        print(f"    tags : {', '.join(item.get('tags', []))}")
        print(f"    desc : {str(item.get('description', ''))[:220]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
