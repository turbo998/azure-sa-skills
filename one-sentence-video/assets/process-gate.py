#!/usr/bin/env python3
"""one-sentence-video 过程闸门：调色板溯源 / 方向比选 / registry 逐镜台账 / 具名 seam / Python SFX 五闸。

用法:
    python3 process-gate.py <project-dir> --stage palette|direction|layout|motion|sound|all

退出码 0 = PASS，1 = BLOCK。缺产物时打印具体缺什么，不猜。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import wave
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SEAMS = [
    "zoom-through",
    "inverse zoom-through",
    "cut-the-curve",
    "waterfall cut",
    "rack-focus blur-cut",
    "scale-through",
    "whip-x",
    "waterfall entry",
    "nudge curve",
]

USER_APPROVED_DARK_STYLES = [
    "speed-board",
    "vault-gold",
    "night-cinema",
    "metal-spec",
    "cyber-hud",
    "xiaozhe-mcp-node-graph",
]

BANNED = [
    "uniform fade+slide",
    "uniform fade + slide",
    "所有元素同时 fade",
    "全片统一 power3.out",
    "每镜同一个 crossfade",
    "三张等宽等高卡片",
    "idle wobble",
    "原地抖动",
    "深蓝网格制服",
    "深蓝底+青色网格",
]


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def shot_sections(storyboard: str):
    """Return [(heading, body)] for sections that declare a frame src."""
    sections = []
    current = None
    for line in storyboard.splitlines():
        if line.startswith("## "):
            if current is not None:
                sections.append(current)
            current = [line.strip("# ").strip(), []]
        elif current is not None:
            current[1].append(line)
    if current is not None:
        sections.append(current)
    shots = []
    for heading, body in sections:
        text = "\n".join(body)
        if re.search(r"(?m)^\s*-\s*src:", text) or re.search(r"(?m)^\s*src:", text):
            shots.append((heading, text))
    return shots


def check_direction(project: Path) -> list[str]:
    fails = []
    ddir = project / "output" / "directions"
    pngs = sorted(ddir.glob("*.png")) if ddir.is_dir() else []
    if len(pngs) < 3:
        fails.append(f"output/directions/ 只有 {len(pngs)} 张 PNG（需 3 张方向样帧）")
    else:
        try:
            from PIL import Image

            for png in pngs[:6]:
                with Image.open(png) as im:
                    if im.size != (1920, 1080):
                        fails.append(f"{png.name} 尺寸 {im.size}，方向样帧必须是 1920×1080")
        except ImportError:
            pass
        except Exception as exc:  # noqa: BLE001
            fails.append(f"{pngs[0].name} 读不出尺寸: {exc}")
    readme = read(ddir / "README.md")
    if not readme:
        fails.append("output/directions/README.md 缺失")
    else:
        for label in ("A", "B", "C"):
            if not re.search(rf"(?i)(^|[^A-Za-z]){label}([^A-Za-z]|$)", readme):
                fails.append(f"output/directions/README.md 没有方向 {label} 的记录")
    spec = read(project / "design-spec.md")
    if not spec:
        fails.append("design-spec.md 缺失")
    else:
        if "方向决策记录" not in spec:
            fails.append("design-spec.md 缺「方向决策记录」")
        if not re.search(r"选择|拍板|chosen", spec, re.I):
            fails.append("design-spec.md 方向决策记录里没有用户选择")
    return fails


def check_cards(project: Path, shots) -> list[str]:
    """STORYBOARD 里声明的 card: 必须在卡片库里真实存在（防编造卡 id）。"""
    fails = []
    idx_path = Path(__file__).resolve().parent.parent / "references" / "cards" / "_index.json"
    if not idx_path.exists():
        return fails
    try:
        known = {c["id"] for c in json.loads(idx_path.read_text(encoding="utf-8"))["cards"]}
    except Exception:  # noqa: BLE001
        return fails
    for heading, body in shots:
        m = re.search(r"(?m)^\s*-?\s*card:\s*`?([a-z0-9-]+)`?", body)
        if not m:
            continue
        cid = m.group(1)
        if cid not in known:
            fails.append(f"镜头「{heading}」的 card: {cid} 不在卡片库里（可用 card-index.py --list 查）")
    return fails


def check_layout(project: Path, shots) -> list[str]:
    fails = []
    if not shots:
        fails.append("STORYBOARD.md 找不到任何带 src: 的镜头节")
        return fails
    for heading, body in shots:
        if not re.search(r"(?m)^\s*-?\s*registry:", body):
            fails.append(f"镜头「{heading}」缺 registry: 行（逐镜布局闸未过）")
    ledger = read(project / "output" / "registry-ledger.md")
    if not ledger:
        fails.append("output/registry-ledger.md 缺失（逐镜检索台账未落盘）")
    else:
        rows = [
            ln
            for ln in ledger.splitlines()
            if ln.strip().startswith("|")
            and not re.match(r"^\s*\|?\s*[-: ]+\|", ln.strip())
            and not re.search(r"英文 query|镜\s*\|", ln)
        ]
        if len(rows) < len(shots):
            fails.append(
                f"registry-ledger.md 数据行 {len(rows)} < 镜头数 {len(shots)}（每镜一行）"
            )
    return fails


def check_motion(project: Path, shots) -> list[str]:
    fails = []
    if not shots:
        fails.append("STORYBOARD.md 找不到任何带 src: 的镜头节")
        return fails
    for heading, body in shots:
        line = next(
            (ln for ln in body.splitlines() if re.search(r"(?m)^\s*-?\s*motion:", ln)),
            None,
        )
        if not line:
            fails.append(f"镜头「{heading}」缺 motion: 行（具名 seam 闸未过）")
            continue
        low = line.lower()
        if not any(seam in low for seam in SEAMS):
            fails.append(
                f"镜头「{heading}」的 motion: 没有具名 seam（允许：{', '.join(SEAMS)}）"
            )
        if "velocity=" not in low:
            fails.append(f"镜头「{heading}」的 motion: 缺 velocity= ease 对")
        if "carrier=" not in low:
            fails.append(f"镜头「{heading}」的 motion: 缺 carrier= 驻留主体")
    # 禁词只扫 STORYBOARD，design-spec 的 BANNED 清单允许出现禁词本身。
    storyboard = read(project / "STORYBOARD.md")
    for phrase in BANNED:
        for ln in storyboard.splitlines():
            if phrase.lower() in ln.lower() and not re.search(r"禁|BANNED|不许|避免|negative", ln, re.I):
                fails.append(f"STORYBOARD.md 出现禁词「{phrase}」：{ln.strip()[:80]}")
    return fails


def check_beat(project: Path, shots) -> list[str]:
    """BGM 与拍点：有 BGM 就必须有网格，且剪辑点必须校验过。"""
    fails = []
    bgm = project / "audio" / "bgm.wav"
    grid = project / "audio" / "beat-grid.json"
    if not bgm.is_file():
        return fails  # 无 BGM 的片子不适用拍点闸
    if not grid.is_file():
        fails.append("有 audio/bgm.wav 但缺 audio/beat-grid.json（拍点网格未落盘）")
        return fails
    try:
        g = json.loads(grid.read_text(encoding="utf-8"))
        for k in ("bpm", "beats", "downbeats", "duration"):
            if k not in g:
                fails.append(f"beat-grid.json 缺 {k}")
    except Exception as exc:  # noqa: BLE001
        fails.append(f"beat-grid.json 读不出: {exc}")
        return fails

    snap = Path(__file__).resolve().parent / "beat-snap.py"
    sb = project / "STORYBOARD.md"
    if snap.exists() and sb.is_file():
        import subprocess
        import sys

        proc = subprocess.run(
            [sys.executable, str(snap), "--grid", str(grid), "--storyboard", str(sb)],
            capture_output=True, text=True,
        )
        if proc.returncode != 0:
            tail = [ln for ln in proc.stdout.splitlines() if "MISS" in ln or ln.startswith("GATE")]
            fails.append("剪辑点不在拍上：" + " | ".join(tail[:4]))
    return fails


def check_sound(project: Path, shots) -> list[str]:
    fails = []
    if not shots:
        fails.append("STORYBOARD.md 找不到任何带 src: 的镜头节")
        return fails
    for heading, body in shots:
        line = next(
            (ln for ln in body.splitlines() if re.search(r"(?m)^\s*-?\s*sound:", ln)),
            None,
        )
        if not line:
            fails.append(f"镜头「{heading}」缺 sound: 行（Python SFX 声音闸未过）")
            continue
        low = line.lower()
        if "motif=" not in low:
            fails.append(f"镜头「{heading}」的 sound: 缺 motif=")
        if "cues=" not in low:
            fails.append(f"镜头「{heading}」的 sound: 缺 cues=")

    events_path = project / "audio" / "sfx-events.json"
    if not events_path.is_file():
        fails.append("audio/sfx-events.json 缺失（SFX 事件图未落盘）")
    else:
        try:
            data = json.loads(events_path.read_text(encoding="utf-8"))
            events = data.get("events", [])
            if not isinstance(events, list) or not events:
                fails.append("audio/sfx-events.json 没有 events")
        except Exception as exc:  # noqa: BLE001
            fails.append(f"audio/sfx-events.json 读不出: {exc}")

    index = read(project / "index.html")
    film_dur = 0.0
    if not index:
        fails.append("index.html 缺失")
    else:
        m = re.search(r'data-composition-id="main"[^>]*data-duration="([\d.]+)"', index)
        if m:
            film_dur = float(m.group(1))
        tags = re.findall(r"<audio\b[^>]*>", index, re.I)
        if not tags:
            fails.append("index.html 缺 root-level <audio>（SFX 未挂主时间线）")
        else:
            # 有 BGM 时 tags[0] 是 bgm，必须按 src 找 sfx 那一条
            tag = next((t for t in tags if 'audio/sfx.wav' in t), tags[0])
            if not re.search(r'\bid="[^"]+"', tag):
                fails.append("audio 缺 id")
            if 'src="audio/sfx.wav"' not in tag:
                fails.append("audio src 不是 audio/sfx.wav")
            if not re.search(r'data-start="0"', tag):
                fails.append("audio data-start 不是 0")
            dm = re.search(r'data-duration="([\d.]+)"', tag)
            if not dm:
                fails.append("audio 缺 data-duration")
            elif film_dur and abs(float(dm.group(1)) - film_dur) > 0.01:
                fails.append(f"audio data-duration {dm.group(1)} ≠ film {film_dur}")
            tm = re.search(r'data-track-index="(\d+)"', tag)
            if not tm:
                fails.append("audio 缺 data-track-index")
            elif int(tm.group(1)) < 10:
                fails.append(f"audio data-track-index {tm.group(1)} < 10（须独立于视觉）")
            if not re.search(r'data-volume="[\d.]+"', tag):
                fails.append("audio 缺 data-volume")
            if re.search(r'class="[^"]*clip', tag):
                fails.append("audio 带了 class=\"clip\"（音频无视觉）")
            if "crossorigin" in tag:
                fails.append("audio 带 crossorigin（本地文件禁止）")

    wav_path = project / "audio" / "sfx.wav"
    if not wav_path.is_file():
        fails.append("audio/sfx.wav 缺失（Python SFX 未生成）")
    else:
        try:
            with wave.open(str(wav_path), "rb") as wf:
                sr = wf.getframerate()
                ch = wf.getnchannels()
                dur = wf.getnframes() / float(sr)
                if sr < 44100:
                    fails.append(f"audio/sfx.wav 采样率 {sr} < 44100")
                if ch != 2:
                    fails.append(f"audio/sfx.wav 声道 {ch} ≠ 2")
                if film_dur and dur < film_dur - 0.05:
                    fails.append(f"audio/sfx.wav 时长 {dur:.2f}s < film {film_dur:.2f}s")
        except Exception as exc:  # noqa: BLE001
            fails.append(f"audio/sfx.wav 读不出: {exc}")
    return fails


def check_palette(project: Path) -> list[str]:
    """委托给 palette-audit.py，保持单一实现。"""
    import subprocess
    import sys

    audit = Path(__file__).resolve().parent / "palette-audit.py"
    if not audit.exists():
        return ["palette-audit.py 缺失（调色板溯源闸无法运行）"]
    proc = subprocess.run(
        [sys.executable, str(audit), str(project), "--json"],
        capture_output=True,
        text=True,
    )
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return [f"palette-audit.py 输出无法解析: {(proc.stdout or proc.stderr)[:200]}"]
    return list(data.get("fails") or [])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--stage", default="all", choices=["palette", "direction", "layout", "motion", "sound", "all"])
    args = ap.parse_args()
    project = Path(args.project).resolve()
    if not project.is_dir():
        print(f"BLOCK: project not found: {project}")
        return 1

    storyboard = read(project / "STORYBOARD.md")
    shots = shot_sections(storyboard)
    stages = (
        ["palette", "direction", "layout", "motion", "sound"] if args.stage == "all" else [args.stage]
    )
    fails: list[str] = []
    for stage in stages:
        if stage == "palette":
            fails += check_palette(project)
        elif stage == "direction":
            fails += check_direction(project)
        elif stage == "layout":
            fails += check_layout(project, shots)
            fails += check_cards(project, shots)
        elif stage == "motion":
            fails += check_motion(project, shots)
        elif stage == "sound":
            fails += check_sound(project, shots)
            fails += check_beat(project, shots)

    if fails:
        print("GATE: BLOCK")
        for f in fails:
            print("  ✗", f)
        return 1
    print("GATE: PASS", f"(stage={args.stage}, shots={len(shots)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
