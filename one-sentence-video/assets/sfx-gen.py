#!/usr/bin/env python3
"""one-sentence-video SFX synthesizer — Python-only, no downloads.

Build a dry, mechanical/analog sound-effects bed from an event map. The
palette is intentionally small so a film has one sonic identity instead of
a pile of unrelated stock whooshes:

    flap   split-flap / mechanical clack
    tick   typewriter / counter tick
    chime  soft metal bell (hub, rule, tagline)
    thud   low impact (cut, arrival)
    whoosh camera swipe, pan follows the film's current
    swipe  short tape-slide for an in-scene group move
    riser  upward tension into a zoom / arrival

Usage:
    python3 sfx-gen.py --events audio/sfx-events.json --out audio/sfx.wav
    python3 sfx-gen.py --events audio/sfx-events.json --out /tmp/test.wav --peak 0.6

Event map schema:
    {
      "duration": 26,
      "events": [
        {"t": 0.10, "type": "flap", "gain": 0.45, "pan": -0.2},
        {"t": 3.55, "type": "whoosh", "dur": 0.45, "gain": 0.55,
         "pan": 0.75, "pan_end": -0.75}
      ]
    }

All randomness is seeded; the same map produces the same WAV.
"""
from __future__ import annotations

import argparse
import json
import math
import wave
from pathlib import Path

import numpy as np

SR = 48000
PEAK = 0.70
TYPE_DUR = {
    "flap": 0.075,
    "tick": 0.028,
    "chime": 0.55,
    "thud": 0.34,
    "whoosh": 0.46,
    "swipe": 0.26,
    "riser": 0.58,
}
TYPES = set(TYPE_DUR)


def moving_average(x: np.ndarray, k: int) -> np.ndarray:
    if k < 1:
        return x
    return np.convolve(x, np.ones(k) / k, mode="same")


def pan_gains(pan_start: float, pan_end: float, n: int):
    """Equal-power stereo pan, linearly interpolated over the event."""
    p = np.linspace(float(pan_start), float(pan_end), n)
    left = np.cos((p + 1.0) * np.pi / 4.0)
    right = np.sin((p + 1.0) * np.pi / 4.0)
    return left, right


def env(n: int, attack: float = 0.004, decay: float = 0.10) -> np.ndarray:
    t = np.arange(n) / SR
    a = np.clip(t / max(attack, 1e-5), 0.0, 1.0)
    d = np.exp(-t / max(decay, 1e-5))
    return a * d


def synth(kind: str, dur: float, rng: np.random.Generator):
    n = max(1, int(round(dur * SR)))
    t = np.arange(n) / SR

    if kind == "flap":
        noise = rng.standard_normal(n)
        hp = noise - moving_average(noise, 3)
        ping = np.sin(2.0 * np.pi * 1750.0 * t) * np.exp(-t / 0.018)
        body = np.sin(2.0 * np.pi * 620.0 * t) * np.exp(-t / 0.035)
        sig = hp * 0.75 + ping * 0.50 + body * 0.30
        sig *= env(n, 0.0015, 0.055)

    elif kind == "tick":
        noise = rng.standard_normal(n)
        hp = noise - moving_average(noise, 2)
        ping = np.sin(2.0 * np.pi * 4200.0 * t) * np.exp(-t / 0.006)
        sig = hp * 0.45 + ping * 0.75
        sig *= env(n, 0.001, 0.018)

    elif kind == "chime":
        sig = np.zeros(n)
        for freq, decay, amp in (
            (880.0, 0.18, 0.42),
            (1320.0, 0.12, 0.28),
            (1760.0, 0.08, 0.18),
            (2640.0, 0.05, 0.08),
        ):
            sig += amp * np.sin(2.0 * np.pi * freq * t) * np.exp(-t / decay)
        sig += 0.16 * np.sin(2.0 * np.pi * 440.0 * t) * np.exp(-t / 0.28)
        sig *= env(n, 0.003, 0.40)

    elif kind == "thud":
        f = 80.0 - 24.0 * (t / max(dur, 1e-6))
        sub = np.sin(2.0 * np.pi * f * t) * np.exp(-t / 0.085)
        low = np.sin(2.0 * np.pi * 42.0 * t) * np.exp(-t / 0.12)
        mid = np.sin(2.0 * np.pi * 180.0 * t) * np.exp(-t / 0.06)
        noise = rng.standard_normal(n)
        body = moving_average(noise, 6) * 0.20
        sig = sub * 0.65 + low * 0.30 + mid * 0.45 + body
        sig *= env(n, 0.002, 0.22)

    elif kind == "whoosh":
        noise = rng.standard_normal(n)
        lp = moving_average(noise, 5)
        hp = noise - moving_average(noise, 95)
        body = lp - moving_average(lp, 14)
        sweep = np.sin(2.0 * np.pi * (480.0 + 1500.0 * (t / max(dur, 1e-6)) ** 2) * t)
        sig = body * 1.20 + hp * 0.25 + sweep * 0.28
        sig *= np.sin(np.pi * t / max(dur, 1e-6)) ** 1.4

    elif kind == "swipe":
        noise = rng.standard_normal(n)
        hp = noise - moving_average(noise, 4)
        sweep = np.sin(2.0 * np.pi * (1500.0 - 900.0 * (t / max(dur, 1e-6))) * t)
        sig = hp * 0.75 + sweep * 0.35
        sig *= np.sin(np.pi * t / max(dur, 1e-6)) ** 1.2

    elif kind == "riser":
        noise = rng.standard_normal(n)
        hp = noise - moving_average(noise, 70)
        sweep = np.sin(2.0 * np.pi * (220.0 + 900.0 * (t / max(dur, 1e-6)) ** 2) * t)
        sig = hp * 0.55 + sweep * 0.55
        sig *= (t / max(dur, 1e-6)) ** 1.6

    else:
        raise ValueError(f"unknown sfx type: {kind}")

    return sig


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", required=True, help="event-map JSON")
    ap.add_argument("--out", required=True, help="output WAV")
    ap.add_argument("--peak", type=float, default=PEAK, help="peak amplitude 0..1")
    ap.add_argument("--seed", type=int, default=1017)
    args = ap.parse_args()

    data = json.loads(Path(args.events).read_text(encoding="utf-8"))
    duration = float(data.get("duration", 0))
    events = data.get("events", [])
    if not isinstance(events, list) or not events:
        raise SystemExit("BLOCK: event map has no events")
    if duration <= 0:
        duration = max(float(e.get("t", 0)) + float(e.get("dur", TYPE_DUR.get(e["type"], 0.3))) for e in events) + 0.5

    rng = np.random.default_rng(args.seed)
    total = max(1, int(round(duration * SR)))
    mix = np.zeros((total, 2), dtype=np.float64)
    used = 0

    for ev in events:
        kind = str(ev.get("type", "")).strip()
        if kind not in TYPES:
            raise SystemExit(f"BLOCK: unknown event type {kind!r}")
        t0 = float(ev.get("t", 0.0))
        dur = float(ev.get("dur", TYPE_DUR[kind]))
        gain = float(ev.get("gain", 0.45))
        pan = float(ev.get("pan", 0.0))
        pan_end = float(ev.get("pan_end", pan))
        if t0 < 0 or t0 >= duration:
            continue
        sig = synth(kind, dur, rng)
        left, right = pan_gains(pan, pan_end, len(sig))
        start = int(round(t0 * SR))
        end = min(total, start + len(sig))
        if end <= start:
            continue
        seg = sig[: end - start]
        mix[start:end, 0] += seg * left[: end - start] * gain
        mix[start:end, 1] += seg * right[: end - start] * gain
        used += 1

    # Soft clip, then normalize to the requested peak. Dry broadside sound: no reverb.
    mix = np.tanh(mix * 1.15) / 1.15
    peak_now = float(np.max(np.abs(mix))) if mix.size else 0.0
    if peak_now > 0:
        mix *= min(float(args.peak), 1.0) / peak_now
    mix = np.clip(mix, -1.0, 1.0)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    pcm = np.int16(np.round(mix * 32767.0))
    with wave.open(str(out), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())

    print(f"wrote {out} · {duration:.2f}s · {SR} Hz stereo · events={used} · peak={float(np.max(np.abs(mix))):.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
