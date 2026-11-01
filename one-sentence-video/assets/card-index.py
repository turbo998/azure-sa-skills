#!/usr/bin/env python3
"""卡片库索引：解析 references/cards/**/*.md 的 frontmatter，建机器可查的索引。

用法:
    python3 card-index.py --rebuild                 # 重建 _index.json
    python3 card-index.py --list                    # 全部卡
    python3 card-index.py --layout hero-plus-grid   # 按构图查
    python3 card-index.py --seam cut-the-curve      # 按 seam 查
    python3 card-index.py --genre tech-deep         # 按题材查
    python3 card-index.py --role transition         # 按角色查
    python3 card-index.py --energy-plan 8           # 给 8 镜排能量曲线（避免连续三镜同能量）
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
CARDS = ROOT / "references" / "cards"
INDEX = ROOT / "references" / "cards" / "_index.json"

KEYS = ("id", "name_zh", "category", "role", "energy", "duration",
        "layouts", "seams", "sound", "genres", "source", "verified")


def parse_card(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    meta: dict = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        k, v = k.strip(), v.strip()
        if k not in KEYS:
            continue
        if v.startswith("[") and v.endswith("]"):
            meta[k] = [x.strip() for x in v[1:-1].split(",") if x.strip()]
        elif k in ("energy",):
            try:
                meta[k] = int(v)
            except ValueError:
                meta[k] = 0
        elif k == "duration":
            try:
                meta[k] = float(v)
            except ValueError:
                meta[k] = 0.0
        else:
            meta[k] = v
    meta["path"] = path.relative_to(CARDS).as_posix()
    meta["has_when_not"] = "## 何时不用" in text
    meta["sections"] = [ln[3:].strip() for ln in text.splitlines() if ln.startswith("## ")]
    meta["lines"] = text.count("\n") + 1
    return meta


def build() -> dict:
    cards = []
    for p in sorted(CARDS.rglob("*.md")):
        if p.name == "README.md":
            continue
        c = parse_card(p)
        if c:
            cards.append(c)
    return {
        "_note": "卡片索引。由 card-index.py --rebuild 生成，不要手改。",
        "total": len(cards),
        "by_category": {k: [c["id"] for c in cards if c.get("category") == k]
                        for k in sorted({c.get("category", "") for c in cards})},
        "cards": cards,
    }


def show(cards: list[dict]) -> None:
    for c in cards:
        e = "★" * int(c.get("energy") or 0)
        print(f"{c['id']:<26}{c.get('name_zh',''):<14}{e:<6}"
              f" role={c.get('role',''):<11} {c.get('duration',0):>4.1f}s  "
              f"{c.get('verified','')}")
        print(f"{'':<26}layout={'/'.join(c.get('layouts') or []) or '-'}  "
              f"seam={'/'.join(c.get('seams') or []) or '-'}  "
              f"sfx={'+'.join(c.get('sound') or []) or '-'}")


def energy_plan(n: int) -> list[int]:
    """排一条不连续三镜同能量的曲线：钩子高、中段起伏、收尾定版。"""
    if n <= 0:
        return []
    base = [4, 2, 3, 2, 4, 3, 2, 3, 5, 3]
    plan = [base[i % len(base)] for i in range(n)]
    plan[0] = max(plan[0], 4)          # 钩子必须有冲击
    if n >= 3:
        plan[-1] = 2                   # 收尾定版，能量收回来
    # 修掉连续三镜同值
    for i in range(2, len(plan)):
        if plan[i] == plan[i - 1] == plan[i - 2]:
            plan[i] = plan[i] - 1 if plan[i] > 1 else plan[i] + 1
    return plan


REQUIRED = ("意图", "适用", "何时不用")
RECOMMENDED = {"layout": ("构图", "时间表", "参数表"),
               "typography": ("构图", "时间表", "参数表"),
               "data": ("构图", "时间表", "参数表"),
               "camera": ("时间表", "参数表"),
               "sequence": ("时间表", "参数表"),
               "transition": ("参数表",),
               "background": ("构图", "参数表"),
               "rhythm": ("参数表",)}


def audit() -> int:
    """卡库自审：没有「何时不用」或「参数表」的卡不算完成。"""
    cards = []
    for p in sorted(CARDS.rglob("*.md")):
        if p.name == "README.md":
            continue
        c = parse_card(p)
        if c:
            cards.append(c)
    bad = 0
    for c in cards:
        secs = c.get("sections") or []
        has = lambda name: any(sec.startswith(name) for sec in secs)  # noqa: E731
        problems = [f"缺「{r}」" for r in REQUIRED if not has(r)]
        for r in RECOMMENDED.get(c.get("role", ""), ()):
            if not has(r):
                problems.append(f"缺「{r}」")
        if c.get("verified") not in ("measured", "derived"):
            problems.append("verified 必须是 measured 或 derived")
        if c.get("role") != "rhythm" and not c.get("duration"):
            problems.append("duration 为 0（非 rhythm 卡必须有绑定或典型时长）")
        if problems:
            bad += 1
            print(f"  ✗ {c['id']:<28}{'；'.join(problems)}")
    print(f"\nAUDIT: {len(cards)-bad}/{len(cards)} 张卡合规" + ("" if not bad else f"（{bad} 张待补）"))
    return 0 if not bad else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebuild", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--layout")
    ap.add_argument("--seam")
    ap.add_argument("--genre")
    ap.add_argument("--role")
    ap.add_argument("--id")
    ap.add_argument("--energy-plan", type=int, default=0)
    ap.add_argument("--audit", action="store_true")
    args = ap.parse_args()

    if args.audit:
        return audit()

    if args.rebuild:
        idx = build()
        INDEX.write_text(json.dumps(idx, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"built: {idx['total']} cards → {INDEX}")
        for k, v in idx["by_category"].items():
            print(f"  {k:<10}{len(v)}")
        missing = [c["id"] for c in idx["cards"] if not c["has_when_not"]]
        if missing:
            print("  ⚠ 缺「何时不用」:", ", ".join(missing))
        return 0

    if args.energy_plan:
        print(f"# {args.energy_plan} 镜能量曲线（1 静 → 5 炸）")
        print("  " + " ".join(f"{e}" for e in energy_plan(args.energy_plan)))
        return 0

    if not INDEX.exists():
        print("索引不存在，先 --rebuild")
        return 1
    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    cards = idx["cards"]

    if args.id:
        c = next((c for c in cards if c["id"] == args.id), None)
        if not c:
            print(f"no such card: {args.id}")
            return 1
        print(json.dumps(c, ensure_ascii=False, indent=2))
        return 0

    if args.layout:
        cards = [c for c in cards if args.layout in (c.get("layouts") or [])]
    if args.seam:
        cards = [c for c in cards if args.seam in (c.get("seams") or [])]
    if args.genre:
        cards = [c for c in cards if args.genre in (c.get("genres") or [])]
    if args.role:
        cards = [c for c in cards if c.get("role") == args.role]

    print(f"# {len(cards)} 张卡\n")
    show(cards)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
