#!/usr/bin/env python3
"""拍点吸附：校验剪辑点是否落在拍上，或反推一组对齐小节的镜头边界。

用法:
    # 校验（有音乐时必须过；容差默认 ±50ms ≈ 1.5 帧）
    python3 beat-snap.py --grid audio/beat-grid.json --check 3.2,7.8,12.4

    # 反推：给 N 镜，输出对齐到小节的边界
    python3 beat-snap.py --grid audio/beat-grid.json --plan 7

    # 从 STORYBOARD 的 [t0–t1s] 时间码直接校验
    python3 beat-snap.py --grid audio/beat-grid.json --storyboard STORYBOARD.md

规则：
  - 优先吸到**强拍**（小节头），其次拍，最后 8 分音符。
  - 容差外不硬吸——宁可报"这一刀不在拍上"，也不改坏分镜节奏。
  - 退出码 1 = 有剪辑点超出容差。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

GRID_KINDS = (("downbeats", "强拍"), ("beats", "拍"), ("eighths", "8分"))


def load_grid(path: Path) -> dict:
    g = json.loads(path.read_text(encoding="utf-8"))
    for k in ("downbeats", "beats", "eighths"):
        if k not in g:
            raise SystemExit(f"BLOCK: beat-grid 缺 {k}")
    return g


def nearest(g: dict, t: float, tol: float) -> tuple[float, float, str]:
    """返回 (吸附后时间, 偏差, 拍类型)。按 强拍 → 拍 → 8分 的顺序优先。"""
    best = (t, 0.0, "none")
    for key, label in GRID_KINDS:
        cand = min(g[key], key=lambda x: abs(x - t))
        d = abs(cand - t)
        if d <= tol:
            return cand, cand - t, label
        if d < abs(best[1]) or best[2] == "none":
            best = (cand, cand - t, label)
    return best


def parse_storyboard(path: Path) -> list[float]:
    """抓每个镜头节的 [t0–t1s] 起止，返回所有边界时刻（去重排序）。"""
    text = path.read_text(encoding="utf-8")
    times: set[float] = set()
    for m in re.finditer(r"\[\s*(\d+(?:\.\d+)?)\s*[–\-~]\s*(\d+(?:\.\d+)?)\s*s?\s*\]", text):
        times.add(float(m.group(1)))
        times.add(float(m.group(2)))
    return sorted(times)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--grid", required=True)
    ap.add_argument("--check", default="")
    ap.add_argument("--storyboard", default="")
    ap.add_argument("--plan", type=int, default=0)
    ap.add_argument("--tolerance", type=float, default=0.050)
    ap.add_argument("--on", default="beats", choices=["downbeats", "beats", "eighths"],
                    help="--plan 用哪一级网格（默认 beats）")
    args = ap.parse_args()

    g = load_grid(Path(args.grid))
    print(f"# grid: {g.get('style','?')} · {g['bpm']:g} BPM · {g['bars']} bars · "
          f"{g['duration']:.2f}s · 容差 ±{args.tolerance*1000:.0f}ms")

    if args.plan:
        step = {"downbeats": g["bar_sec"], "beats": g["beat_sec"], "eighths": g["beat_sec"] / 2}[args.on]
        # 让 N 镜尽量均匀铺满，再对齐到网格
        total = g["duration"]
        raw = [total * i / args.plan for i in range(args.plan + 1)]
        snapped = [min(g[args.on], key=lambda x: abs(x - t)) for t in raw]
        print(f"\n# {args.plan} 镜边界（对齐 {args.on}）")
        for i in range(args.plan):
            a, b = snapped[i], snapped[i + 1]
            print(f"  镜 {i+1:>2}  {a:6.2f} → {b:6.2f}   ({b-a:.2f}s)")
        print(f"  末点   {snapped[-1]:6.2f}")
        if snapped[-1] > g["duration"]:
            print(f"  ⚠ 末点超出 BGM 时长 {g['duration']:.2f}s —— 加小节或缩短片长")
        return 0

    times: list[float] = []
    if args.check:
        times = [float(x) for x in args.check.replace(" ", "").split(",") if x]
    if args.storyboard:
        times += parse_storyboard(Path(args.storyboard))
    if not times:
        print("没有要校验的时间点（用 --check 或 --storyboard）")
        return 0

    times = sorted(set(times))
    bad = 0
    print(f"\n{'时间':>8}  {'吸附到':>8}  {'偏差':>8}  类型   判定")
    for t in times:
        snap, delta, kind = nearest(g, t, args.tolerance)
        ok = abs(delta) <= args.tolerance + 1e-9
        if not ok:
            bad += 1
        print(f"{t:8.2f}  {snap:8.2f}  {delta*1000:+7.0f}ms  {kind:<5}  {'OK' if ok else 'MISS'}")

    print()
    if bad:
        print(f"GATE: BLOCK ({bad}/{len(times)} 个剪辑点不在拍上，容差 ±{args.tolerance*1000:.0f}ms)")
        print("  修法：① 改镜头时长让它落拍；② 换 --plan 反推边界；③ 明确接受并记入 design-spec")
        return 1
    print(f"GATE: PASS ({len(times)} 个剪辑点全部在拍上)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
