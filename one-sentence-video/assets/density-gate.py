#!/usr/bin/env python3
"""「平」检测器：把 METHOD §1 的三条症状 + 实测基准变成可拦截的判据。

旧版只查「单帧亮像素占比 ≥0.10% + 4 列里 2 列有内容」——一个死区 60% 的画面，
只要活的 40% 够亮就照样 PASS。那测不出「平」。

现在五个判据（前四个 FAIL，第五个 WARN）：

  1. 死区        九宫格里 ≥4 格同时无内容，连续 ≥2.0s
  2. 结构变化    画面差分峰的间隔中位数 > 4.0s（基准：参考片 3.0s）
  3. 冻结        帧间差分 < 0.5 的时间占比 > 30%
  4. 缓动指纹    单一 ease 占比 > 70%，或 back.out 出现 > 2 次
  5. 构图重复    相邻镜 layout 相同（需 STORYBOARD 里有 layout 行）
  6. 安全区      内容外接框侵入动作安全区（左右 <96px / 上下 <54px）的帧 >20%

用法:
    python3 density-gate.py <project-dir>                      # 自动找 renders/draft-check.mp4
    python3 density-gate.py --video renders/video.mp4          # 指定视频
    python3 density-gate.py /tmp/dv                            # 兼容旧用法：给一个抽好的帧目录
    python3 density-gate.py <project-dir> --json

退出码 0 = PASS，1 = BLOCK。
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

# —— 判据阈值（标定自 5 支实测片）——
DEAD_CELLS = 4          # ≥4 格同时空 → 该帧算「死」
DEAD_SECONDS = 2.0      # 连续死 ≥2s → FAIL
STRUCTURE_MAX = 4.0     # 结构变化间隔中位数上限（秒）
FREEZE_DIFF = 0.5       # 帧间差分低于此值算「冻住」
FREEZE_SHARE = 0.30     # 冻住的时间占比上限
EASE_SHARE = 0.70       # 单一 ease 占比上限
BACK_OUT_MAX = 2        # back.out 出现次数上限
EDGE_MIN = 4.0          # 格内平均梯度 ≥ 此值 = 该格有内容（对比度判据，明暗无关）
GRID = 3                # 九宫格
SAFE_X, SAFE_Y = 96, 54  # 动作安全区边距（1920×1080 的 90%）
SAFE_SHARE = 0.20       # 越界帧占比上限
DARK = 140              # 判「内容」的暗像素阈值


def extract_frames(video: Path, fps: float, out: Path) -> int:
    out.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(video),
         "-vf", f"fps={fps},scale=192:108", str(out / "f%04d.png")],
        check=True,
    )
    return len(list(out.glob("f*.png")))


def load_gray(frames: list[Path]) -> np.ndarray:
    """→ (n, H, W) float32，缩到 96×54。"""
    arrs = []
    for f in frames:
        im = Image.open(f).convert("L").resize((192, 108), Image.BILINEAR)
        arrs.append(np.asarray(im, dtype=np.float32))
    return np.stack(arrs) if arrs else np.zeros((0, 108, 192), np.float32)


def cell_occupancy(frame: np.ndarray) -> int:
    """九宫格里「有内容」的格子数。

    判据是格内**边缘密度**（平均梯度），不是亮像素：
    浅纸底整屏都是亮的，用亮度判据会让所有格子都算"有内容"，死区永远测不出来。
    """
    h, w = frame.shape
    g = np.abs(np.diff(frame, axis=0))[:, : w - 1] + np.abs(np.diff(frame, axis=1))[: h - 1, :]
    gh, gw = g.shape
    ch, cw = gh // GRID, gw // GRID
    n = 0
    for gy in range(GRID):
        for gx in range(GRID):
            cell = g[gy * ch:(gy + 1) * ch, gx * cw:(gx + 1) * cw]
            if cell.mean() >= EDGE_MIN:
                n += 1
    return n


def check_dead(gray: np.ndarray, fps: float) -> tuple[list[str], dict]:
    fails, info = [], {}
    if len(gray) == 0:
        return ["没有可分析的帧"], info
    occ = np.array([cell_occupancy(f) for f in gray])
    dead = occ < DEAD_CELLS
    longest, run, worst = 0.0, 0, 0
    for i, d in enumerate(dead):
        if d:
            if run == 0:
                start = i
            run += 1
            if run / fps > longest:
                longest, worst = run / fps, start
        else:
            run = 0
    info["dead_longest_s"] = round(longest, 2)
    info["dead_share"] = round(float(dead.mean()), 3)
    info["occupancy_mean"] = round(float(occ.mean()), 2)
    if longest >= DEAD_SECONDS:
        fails.append(
            f"死区：{worst/fps:.1f}s 起连续 {longest:.1f}s 九宫格只有 <{DEAD_CELLS} 格有内容"
            f"（上限 {DEAD_SECONDS}s）"
        )
    return fails, info


def check_structure(gray: np.ndarray, fps: float) -> tuple[list[str], dict]:
    fails, info = [], {}
    if len(gray) < 3:
        return fails, info
    d = np.abs(np.diff(gray, axis=0)).mean(axis=(1, 2))
    thr = d.mean() + 2 * d.std()
    peaks = [i for i in range(1, len(d) - 1) if d[i] > thr and d[i] >= d[i - 1] and d[i] >= d[i + 1]]
    gaps = np.diff(peaks) / fps if len(peaks) > 1 else np.array([])
    med = float(np.median(gaps)) if len(gaps) else 999.0
    info["peaks"] = len(peaks)
    info["structure_median_s"] = round(med, 2) if med < 900 else None
    info["diff_mean"] = round(float(d.mean()), 2)
    if med > STRUCTURE_MAX:
        fails.append(
            f"结构变化太稀：{len(peaks)} 个强变化点，间隔中位数 "
            f"{'∞' if med >= 900 else f'{med:.1f}s'}（上限 {STRUCTURE_MAX}s；参考片基准 3.0s）"
        )
    return fails, info


def check_freeze(gray: np.ndarray) -> tuple[list[str], dict]:
    fails, info = [], {}
    if len(gray) < 2:
        return fails, info
    d = np.abs(np.diff(gray, axis=0)).mean(axis=(1, 2))
    share = float((d < FREEZE_DIFF).mean())
    info["freeze_share"] = round(share, 3)
    if share > FREEZE_SHARE:
        fails.append(
            f"画面冻结：{share*100:.0f}% 的时间帧间差分 <{FREEZE_DIFF}"
            f"（上限 {FREEZE_SHARE*100:.0f}%）—— 多半是动效只有入场，之后就没东西在动"
        )
    return fails, info


def check_safe_area(frames: list[Path], strict: bool = False) -> tuple[list[str], dict]:
    """内容是否侵入动作安全区。文字贴边/出血是「不合格」最直观的一种。"""
    fails, info = [], {}
    if not frames:
        return fails, info
    bad = 0
    worst = None
    for f in frames:
        a = np.asarray(Image.open(f).convert("L"))
        h, w = a.shape
        ys, xs = np.where(a < DARK)
        if len(xs) == 0:
            continue
        mx = min(int(xs.min()), int(ys.min()), int(w - 1 - xs.max()), int(h - 1 - ys.max()))
        need = min(SAFE_X, SAFE_Y)
        # 横向与纵向分别判，按比例缩放到 1920×1080 口径
        scale = 1920.0 / w
        left = xs.min() * scale
        right = (w - 1 - xs.max()) * scale
        top = ys.min() * (1080.0 / h)
        bottom = (h - 1 - ys.max()) * (1080.0 / h)
        m = min(left, right, top * 1920 / 1080, bottom * 1920 / 1080)
        if left < SAFE_X or right < SAFE_X or top < SAFE_Y or bottom < SAFE_Y:
            bad += 1
            if worst is None or m < worst[0]:
                worst = (m, f.name, round(left), round(right), round(top), round(bottom))
    share = bad / max(1, len(frames))
    info["safe_violation_share"] = round(share, 3)
    if worst:
        info["safe_worst"] = f"{worst[1]} 左{worst[2]} 右{worst[3]} 上{worst[4]} 下{worst[5]}"
    if share > SAFE_SHARE:
        (fails if strict else info.setdefault("safe_warn", [])).append(
            f"安全区越界：{share*100:.0f}% 的帧内容侵入动作安全区"
            f"（左右需 ≥{SAFE_X}px、上下需 ≥{SAFE_Y}px；上限 {SAFE_SHARE*100:.0f}%）"
            + (f" · 最差 {info['safe_worst']}" if worst else "")
        )
    return fails, info


def check_easing(project: Path | None) -> tuple[list[str], dict]:
    fails, info = [], {}
    if project is None or not project.is_dir():
        return fails, info
    # 只统计真正参与渲染的文件：compositions/ + index.html。
    # 根目录的 *-visual-draft.html 之类不参与渲染，计进来会虚高。
    files = list(project.glob("compositions/**/*.html"))
    if (project / "index.html").is_file():
        files.append(project / "index.html")
    if not files:
        return fails, info
    eases: list[str] = []
    back_out = 0
    for f in files:
        try:
            t = f.read_text(encoding="utf-8")
        except Exception:
            continue
        eases += re.findall(r'ease:\s*"([^"]+)"', t)
        eases += re.findall(r"ease:\s*'([^']+)'", t)
        back_out += len(re.findall(r"back\.out\(", t))
    if not eases:
        return fails, info
    from collections import Counter
    top, n = Counter(eases).most_common(1)[0]
    share = n / len(eases)
    info["ease_total"] = len(eases)
    info["ease_top"] = f"{top} {share*100:.0f}%"
    info["back_out"] = back_out
    if share > EASE_SHARE:
        fails.append(
            f"缓动指纹：`{top}` 占 {share*100:.0f}%（上限 {EASE_SHARE*100:.0f}%，共 {len(eases)} 处）"
            "—— 全片一种缓动就是「AI 制服」"
        )
    if back_out > BACK_OUT_MAX:
        fails.append(f"`back.out` 出现 {back_out} 次（上限 {BACK_OUT_MAX}）—— 过冲是撞击专用，不是默认入场")
    return fails, info


def check_layout_repeat(project: Path | None) -> tuple[list[str], dict]:
    warns, info = [], {}
    if project is None or not project.is_dir():
        return warns, info
    sb = project / "STORYBOARD.md"
    if not sb.is_file():
        return warns, info
    lays = re.findall(r"(?m)^\s*-?\s*layout:\s*`?([a-z0-9-]+)`?", sb.read_text(encoding="utf-8"))
    if len(lays) < 2:
        return warns, info
    rep = sum(1 for a, b in zip(lays, lays[1:]) if a == b)
    info["layout_repeat"] = rep
    if rep:
        warns.append(f"相邻镜构图重复 {rep} 处（layout: {', '.join(lays)}）")
    return warns, info


BENCH = [
    ("参考片（目录片）", "102s", 22, "3.0s", 5.98, "PASS 基准"),
    ("eccom-ai-troubleshoot", "44s", 3, "11.5s", 2.98, "BLOCK 结构稀"),
    ("minimax-h3", "37s", 3, "7.4s", 6.77, "BLOCK 结构稀 + 缓动单一"),
    ("openai-astra-pause", "40s", 6, "5.2s", 0.64, "BLOCK 冻结"),
    ("qwen38-flash", "82s", 12, "8.5s", 0.35, "BLOCK 冻结 + 结构稀"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("target", nargs="?", default="", help="项目目录，或已抽好的帧目录")
    ap.add_argument("--video", default="")
    ap.add_argument("--fps", type=float, default=6.0)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict-safe", action="store_true",
                    help="安全区越界算 FAIL（自己画的版式用；满幅实拍片不要加）")
    args = ap.parse_args()

    project: Path | None = None
    frames_dir: Path | None = None

    if args.video:
        video = Path(args.video)
        tmp = Path(tempfile.mkdtemp(prefix="dgate-"))
        extract_frames(video, args.fps, tmp)
        frames_dir = tmp
        if args.target and Path(args.target).is_dir():
            project = Path(args.target)
    elif args.target:
        p = Path(args.target)
        if not p.is_dir():
            print(f"BLOCK: not a directory: {p}")
            return 1
        if sorted(p.glob("*.png")) and not (p / "index.html").exists():
            frames_dir = p                       # 旧用法：帧目录
        else:
            project = p
            video = next((c for c in (p / "renders/draft-check.mp4", p / "renders/video.mp4") if c.is_file()), None)
            if video is None:
                print(f"BLOCK: {p} 下找不到 renders/draft-check.mp4 或 renders/video.mp4")
                return 1
            tmp = Path(tempfile.mkdtemp(prefix="dgate-"))
            extract_frames(video, args.fps, tmp)
            frames_dir = tmp
    else:
        ap.print_help()
        return 1

    frames = sorted(frames_dir.glob("f*.png"))
    if not frames:
        print(f"BLOCK: {frames_dir} 里没有 f*.png")
        return 1
    gray = load_gray(frames)
    dur = len(gray) / args.fps

    fails: list[str] = []
    warns: list[str] = []
    info: dict = {"frames": len(gray), "duration_s": round(dur, 1), "fps": args.fps}

    f, i = check_dead(gray, args.fps);        fails += f; info.update(i)
    f, i = check_structure(gray, args.fps);   fails += f; info.update(i)
    f, i = check_freeze(gray);                fails += f; info.update(i)
    f, i = check_easing(project);             fails += f; info.update(i)
    f, i = check_safe_area(frames, args.strict_safe); fails += f; info.update(i)
    w, i = check_layout_repeat(project);      warns += w; info.update(i)

    if args.json:
        print(json.dumps({"ok": not fails, "fails": fails, "warns": warns, "info": info},
                         ensure_ascii=False, indent=1))
        return 0 if not fails else 1

    print(f"# {len(gray)} 帧 / {dur:.1f}s @ {args.fps:g}fps")
    print(f"  九宫格平均占用 {info.get('occupancy_mean','-')}/9 格 · "
          f"死区占比 {info.get('dead_share',0)*100:.0f}% · 最长死区 {info.get('dead_longest_s',0):.1f}s")
    print(f"  结构变化 {info.get('peaks',0)} 次 · 间隔中位数 "
          f"{info.get('structure_median_s') or '∞'}s · 差分均值 {info.get('diff_mean','-')}")
    print(f"  安全区越界 {info.get('safe_violation_share',0)*100:.0f}%"
          + (f" · 最差 {info['safe_worst']}" if info.get("safe_worst") else ""))
    print(f"  冻结占比 {info.get('freeze_share',0)*100:.0f}%"
          + (f" · 缓动 {info.get('ease_top')} / back.out {info.get('back_out')} 次"
             if "ease_top" in info else ""))

    print("\n## 基准对照")
    print(f"{'片子':<24}{'时长':>6}{'变化':>6}{'间隔':>8}{'差分':>7}  判定")
    for name, d, p, gap, diff, verdict in BENCH:
        print(f"{name:<24}{d:>6}{p:>6}{gap:>8}{diff:>7}  {verdict}")

    for w in info.get("safe_warn", []) or []:
        warns.append(w + "（警告级：满幅实拍可忽略；自己画的版式请加 --strict-safe）")
    if warns:
        print("\n## 警告")
        for w in warns:
            print("  !", w)
    if fails:
        print("\nGATE: BLOCK")
        for x in fails:
            print("  ✗", x)
        return 1
    print("\nGATE: PASS（六个判据全过）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
