#!/usr/bin/env python3
"""one-sentence-video BGM 合成器 —— 纯 Python 编曲，不下载任何素材。

为什么用代码编曲而不是找免费曲：
  1. 版权干净、可复现（同 seed 同结果）；
  2. **能同时产出拍点网格** —— 卡点的前提是知道拍点在哪，下载的曲子只能事后猜 BPM；
  3. 时长、段落、BPM 可以精确贴合分镜（不需要裁歌）。

四个风格，对应账本 sound.bgm 字段：
    dry-tech  干燥、克制，鼓在 1/3，8 分音符 hat，无 pad   → 科技/编辑类
    paper     轻刷、暖 pad，鼓很退，16 分 hat 极轻        → 纸感目录类
    pulse     四拍底鼓 + 2/4 拍手 + offbeat bass + arp    → promo/游戏类
    soft      无鼓，只有 pad 与偶发 chime                  → 情感/母婴类

用法:
    python3 bgm-gen.py --style paper --bpm 92 --bars 16 --out audio/bgm.wav
    python3 bgm-gen.py --style dry-tech --bpm 104 --duration 26 --out audio/bgm.wav

产物：
    audio/bgm.wav          立体声 48k
    audio/beat-grid.json   BPM / 拍点 / 小节 / 强拍 / 段落 —— beat-snap.py 用它卡点

调性固定为自然小调的 i–VI–III–VII 循环（A 小调起），避免大调三和弦的"广告味"。
所有随机都有 seed，同参数同结果。
"""
from __future__ import annotations

import argparse
import json
import math
import wave
from pathlib import Path

import numpy as np

SR = 48000

# 自然小调音阶（半音），A 小调为根
MINOR = [0, 2, 3, 5, 7, 8, 10]
# i – VI – III – VII（级数索引，0-based，落在自然小调上）
PROGRESSION = [0, 5, 2, 6]

STYLE_DEFAULTS = {
    "dry-tech": {"bpm": 104, "drums": "sparse", "pad": 0.18, "arp": 0.0},
    "paper": {"bpm": 92, "drums": "soft", "pad": 0.55, "arp": 0.0},
    "pulse": {"bpm": 118, "drums": "four", "pad": 0.22, "arp": 0.5},
    "soft": {"bpm": 76, "drums": "none", "pad": 0.55, "arp": 0.0},
}
STYLES = set(STYLE_DEFAULTS)


def hz(semitone_from_a4: float) -> float:
    return 440.0 * (2.0 ** (semitone_from_a4 / 12.0))


def degree_freq(root: int, degree: int, octave: int = 0) -> float:
    """degree 是音阶级数（可 >6，自动跨八度）。root 是相对 A4 的半音数。"""
    oct_shift, idx = divmod(degree, 7)
    return hz(root + MINOR[idx] + 12 * (octave + oct_shift))


def adsr(n: int, attack: float, decay: float, sustain: float, release: float) -> np.ndarray:
    t = np.arange(n) / SR
    dur = n / SR
    a = np.clip(t / max(attack, 1e-6), 0, 1)
    d = np.clip((t - attack) / max(decay, 1e-6), 0, 1)
    level = 1.0 - (1.0 - sustain) * d
    r = np.clip((dur - t) / max(release, 1e-6), 0, 1)
    return a * level * r


def kick(rng, dur=0.34) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 118.0 * np.exp(-t / 0.045) + 44.0
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.10)
    click = rng.standard_normal(n) * np.exp(-t / 0.004) * 0.25
    return body + click


def snare(rng, dur=0.20) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    # 一阶高通：去掉低频，留"纸感"
    hp = np.diff(np.concatenate([[0.0], noise]))
    tone = np.sin(2 * np.pi * 186.0 * t) * np.exp(-t / 0.05)
    return hp * np.exp(-t / 0.045) * 0.55 + tone * 0.30


def hat(rng, dur=0.055, open_=False) -> np.ndarray:
    n = int((0.16 if open_ else dur) * SR)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    hp = np.diff(np.concatenate([[0.0], np.diff(np.concatenate([[0.0], noise]))]))
    return hp * np.exp(-t / (0.075 if open_ else 0.014)) * 0.5


def bass(root: int, degree: int, dur: float, octave: int = -2) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = degree_freq(root, degree, octave)
    # 正弦基 + 少量二次谐波，低通感
    sig = np.sin(2 * np.pi * f * t) + 0.22 * np.sin(4 * np.pi * f * t)
    return sig * adsr(n, 0.008, 0.09, 0.55, 0.10)


def pad_chord(root: int, degree: int, dur: float) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    sig = np.zeros(n)
    for k, (dd, det, amp) in enumerate(((0, -0.06, 0.5), (2, 0.0, 0.42), (4, 0.07, 0.34))):
        f = degree_freq(root, degree + dd, 0)
        sig += amp * (np.sin(2 * np.pi * f * t) + np.sin(2 * np.pi * (f + det) * t))
    return sig * adsr(n, 0.32, 0.25, 0.72, 0.45)


def body_stab(root: int, degree: int, dur: float = 0.42) -> np.ndarray:
    """中频 body：三和弦短促击发，带谐波滚降，补 300–1200Hz 的"肉"。"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    sig = np.zeros(n)
    for dd, amp in ((0, 0.42), (2, 0.30), (4, 0.24)):
        f = degree_freq(root, degree + dd, 0)
        for h, ha in ((1, 1.0), (2, 0.30), (3, 0.12), (4, 0.05)):
            sig += amp * ha * np.sin(2 * np.pi * f * h * t)
    return sig * adsr(n, 0.006, 0.16, 0.30, 0.14) * 0.42


def pluck(root: int, degree: int, dur: float = 0.24, octave: int = 0) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = degree_freq(root, degree, octave)
    return np.sin(2 * np.pi * f * t) * np.exp(-t / 0.075) * 0.55


def add(buf: np.ndarray, sig: np.ndarray, t0: float, gain: float, pan: float = 0.0) -> None:
    start = int(round(t0 * SR))
    if start >= buf.shape[0]:
        return
    end = min(buf.shape[0], start + sig.shape[0])
    if end <= start:
        return
    seg = sig[: end - start] * gain
    l = math.cos((pan + 1.0) * math.pi / 4.0)
    r = math.sin((pan + 1.0) * math.pi / 4.0)
    buf[start:end, 0] += seg * l
    buf[start:end, 1] += seg * r


def build(style: str, bpm: float, bars: int, root: int, seed: int):
    rng = np.random.default_rng(seed)
    d = STYLE_DEFAULTS[style]
    spb = 60.0 / bpm                 # 每拍秒数
    bar = spb * 4                    # 4/4
    duration = bars * bar
    n = int(round(duration * SR)) + SR // 2
    buf = np.zeros((n, 2), dtype=np.float64)

    hats16 = 16
    for b in range(bars):
        t_bar = b * bar
        deg = PROGRESSION[b % len(PROGRESSION)]

        # —— 鼓 ——
        if d["drums"] == "four":
            for beat in range(4):
                add(buf, kick(rng), t_bar + beat * spb, 0.50)
            for beat in (1, 3):
                add(buf, snare(rng), t_bar + beat * spb, 0.34, pan=0.1)
            for i in range(hats16):
                g = 0.145 if i % 2 == 0 else 0.072
                add(buf, hat(rng), t_bar + i * bar / hats16, g, pan=0.35 if i % 2 else -0.2)
            add(buf, hat(rng, open_=True), t_bar + 3.5 * spb, 0.16, pan=0.3)
        elif d["drums"] == "sparse":
            for beat in (0, 2):
                add(buf, kick(rng), t_bar + beat * spb, 0.45)
            for i in range(8):
                g = 0.135 if i % 2 == 0 else 0.065
                add(buf, hat(rng), t_bar + i * spb / 2, g, pan=0.3 if i % 2 else -0.25)
            if b % 4 == 3:
                add(buf, snare(rng), t_bar + 3 * spb, 0.20, pan=0.15)
        elif d["drums"] == "soft":
            add(buf, kick(rng), t_bar, 0.44)
            add(buf, snare(rng), t_bar + 2 * spb, 0.13, pan=0.2)
            for i in range(hats16):
                if i % 4 == 2:
                    add(buf, hat(rng), t_bar + i * bar / hats16, 0.072, pan=0.4)
        # none: 无鼓

        # —— 贝斯 ——
        if d["drums"] != "none":
            for i in range(4):
                add(buf, bass(root, deg, spb * 0.9), t_bar + i * spb, 0.16)
        else:
            add(buf, bass(root, deg, bar * 0.95), t_bar, 0.22)

        # —— 中频 body ——
        if d["drums"] != "none":
            add(buf, body_stab(root, deg), t_bar, 0.85)
        else:
            add(buf, body_stab(root, deg, bar * 0.9), t_bar, 0.40)

        # —— pad ——
        if d["pad"] > 0:
            add(buf, pad_chord(root, deg, bar * 0.98), t_bar, 0.42 * d["pad"])

        # —— arp ——
        if d["arp"] > 0:
            pattern = [0, 2, 4, 2, 4, 6, 4, 2]
            for i, pd in enumerate(pattern):
                add(buf, pluck(root, deg + pd), t_bar + i * spb / 2, 0.16 * d["arp"],
                    pan=(-0.35 if i % 2 else 0.35))

    return buf[: int(round(duration * SR))]


def beat_grid(bpm: float, bars: int) -> dict:
    spb = 60.0 / bpm
    bar = spb * 4
    beats = [round(i * spb, 4) for i in range(int(bars * 4))]
    downbeats = [round(i * bar, 4) for i in range(bars)]
    eighths = [round(i * spb / 2, 4) for i in range(int(bars * 8))]
    return {
        "bpm": bpm,
        "beats_per_bar": 4,
        "bars": bars,
        "beat_sec": round(spb, 5),
        "bar_sec": round(bar, 5),
        "duration": round(bars * bar, 4),
        "downbeats": downbeats,
        "beats": beats,
        "eighths": eighths,
        "sections": [
            {"bar": i, "t": round(i * bar, 4), "name": ("intro" if i == 0 else "body" if i < bars - 1 else "outro")}
            for i in range(bars)
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--style", default="dry-tech", choices=sorted(STYLES))
    ap.add_argument("--bpm", type=float, default=0)
    ap.add_argument("--bars", type=int, default=0)
    ap.add_argument("--duration", type=float, default=0, help="给秒数则自动向上取整到整小节")
    ap.add_argument("--key", type=int, default=0, help="根音相对 A4 的半音数（0=A，-3=F#…）")
    ap.add_argument("--out", required=True)
    ap.add_argument("--grid-out", default="")
    ap.add_argument("--peak", type=float, default=0.62)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--no-master", action="store_true", help="跳过 pedalboard 母带")
    args = ap.parse_args()

    bpm = args.bpm or STYLE_DEFAULTS[args.style]["bpm"]
    bars = args.bars
    if not bars:
        if args.duration <= 0:
            raise SystemExit("BLOCK: 需要 --bars 或 --duration")
        bars = max(1, math.ceil(args.duration / (60.0 / bpm * 4)))

    buf = build(args.style, bpm, bars, args.key, args.seed)

    # 母带：有 pedalboard 就用它（比 tanh 软削好得多），没有就退回 tanh
    mastered = "tanh"
    if not args.no_master:
        try:
            from pedalboard import (Pedalboard, Compressor, HighpassFilter,
                                    Limiter, LowShelfFilter)
            board = Pedalboard([
                HighpassFilter(cutoff_frequency_hz=28),
                LowShelfFilter(cutoff_frequency_hz=120, gain_db=-2.0),
                Compressor(threshold_db=-16.0, ratio=2.5, attack_ms=8.0, release_ms=140.0),
                Limiter(threshold_db=-1.5, release_ms=120.0),
            ])
            buf = board(buf.T.astype(np.float32), SR, reset=True).T.astype(np.float64)
            mastered = "pedalboard"
        except Exception:
            pass
    buf = np.tanh(buf * 1.25) / 1.25
    peak = float(np.max(np.abs(buf))) if buf.size else 0.0
    if peak > 0:
        buf *= args.peak / peak
    buf = np.clip(buf, -1.0, 1.0)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    pcm = np.int16(np.round(buf * 32767.0))
    with wave.open(str(out), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())

    grid = beat_grid(bpm, bars)
    grid["style"] = args.style
    grid["source"] = str(out)
    gout = Path(args.grid_out) if args.grid_out else out.with_name("beat-grid.json")
    gout.parent.mkdir(parents=True, exist_ok=True)
    gout.write_text(json.dumps(grid, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"wrote {out} · style={args.style} · {bpm:g} BPM · {bars} bars · "
          f"{grid['duration']:.2f}s · master={mastered} · peak={float(np.max(np.abs(buf))):.3f}")
    print(f"wrote {gout} · downbeats={len(grid['downbeats'])} · beats={len(grid['beats'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
