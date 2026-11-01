# 音频栈：Python 做音乐，哪些库真的强

> 结论先行：**不要手写合成器去追"好听"**。分工是
> `music21` 作曲 → `numpy/bgm-gen` 出声 → `pedalboard` 混音 → `librosa` 分析。
> 想要"真乐器"，唯一的路是 **fluidsynth + SoundFont**，那是另一个依赖层级。

## 实测环境（本机 2026-10）

| 库 | 状态 | 用途 | 评价 |
|---|---|---|---|
| `numpy` 2.3 | 已装 | 采样级合成 | 万能，但音色要自己写 |
| `scipy` 1.17 | 已装 | 滤波 / 重采样 | 够用 |
| **`librosa` 0.11** | **已装** | 拍点、onset、BPM、节拍跟踪 | **卡点的主力**，`beat_track()` 能吃任意音频 |
| `soundfile` 0.12 | 已装 | WAV/FLAC 读写 | 比 `wave` 稳 |
| `pydub` | 已装 | 剪辑拼接 | 需 ffmpeg，适合粗剪 |
| **`music21` 10.3** | **已装** | 乐理 / 和声 / 声部 / MIDI 导出 | **作曲主力**：`roman.RomanNumeral('i', Key('a','minor'))` 直接给和弦音 |
| **`pedalboard` 0.9.26** | **可装（wheel，2MB）** | EQ / 压缩 / 混响 / 限幅 | Spotify 出品，**混音主力**，无编译依赖 |
| `aubio` 0.4.9 | 可装（需编译） | onset / 音高 / 节拍 | 比 librosa 轻，但装起来麻烦 |
| `mido` / `pretty_midi` | 可装（纯 Python） | MIDI 读写 | 只在需要精修 MIDI 时用 |
| `pyo` 1.1 | 需编译 | 完整 DSP 合成引擎 | 音色强，但 C 依赖重 |
| `scamp` 0.13 | 可装（拉 fluidsynth 链） | 高级作曲 + 回放 | 设计最贴近"写一段就出声"，但依赖链长 |
| `audiocraft`（MusicGen） | 不建议 | 神经音乐生成 | **GB 级权重 + GPU**，与本机"不加载大模型"规则冲突 |
| `fluidsynth` + SF2 | 未装 | MIDI → 真乐器音频 | **唯一能"听起来像真乐器"的路**，需 brew + 下载 SoundFont（~30MB） |

## 为什么不用 MusicGen / 神经生成

三个硬理由：
1. **权重 GB 级**，本机规则明确"模型加载类操作先查内存"；
2. **不可复现**（同一 prompt 出不同结果），而视频需要帧级可复现；
3. **拿不到拍点**——生成音频的 BPM 是随机的，卡点无从谈起。

## 推荐架构（已落地）

```
分镜确定时长
   ↓
bgm-gen.py --style <paper|dry-tech|pulse|soft> --bpm N
   ├── audio/bgm.wav           ← numpy 加法合成（零依赖）
   └── audio/beat-grid.json    ← BPM / 拍 / 强拍 / 8 分 / 小节
   ↓
beat-snap.py --plan 7          ← 反推对齐小节的镜头边界
   （或 --check 3.2,7.8 校验已有剪辑点，容差 ±50ms）
   ↓
pedalboard 母带               ← 自动接入：Highpass 28Hz / LowShelf -2dB@120
                                  / Compressor -16dB 2.5:1 / Limiter -1.5dB
   ↓
sfx-gen.py                    ← 事件级 SFX，与画面拍点同帧
```

`bgm-gen.py` 会在 import 成功时自动用 pedalboard 做母带；缺失时退回 `tanh` 软削并打印 `master=tanh`。

## 手写合成器的诚实边界（实测）

用**功率谱**（不是幅度谱——幅度谱会让宽带噪声虚高）测四个风格的频段能量占比：

| style | sub<80 | low 80–300 | mid 300–2k | hi>2k | 判断 |
|---|---|---|---|---|---|
| `pulse` | 13.8% | 33.0% | 39.7% | 8.3% | 均衡，可用 |
| `dry-tech` | 8.7% | 41.4% | 46.5% | 2.0% | 低频略多，空气感不足 |
| `paper` | 1.2% | 11.0% | 87.2% | 0.4% | **中频独大**，闷 |
| `soft` | 0.0% | 16.4% | 83.6% | 0.0% | pad 主导，可接受（本就无鼓） |

**根因**：加法合成（正弦叠加）把能量集中在少数频点，而真实乐器有噪声成分与谐波扩散。
所以 `paper`/`soft` 这类"靠 pad 撑"的风格会闷。这不是调参能解决的，是方法上限。

**结论**：`bgm-gen.py` 定位是**零依赖兜底**——保证任何机器上都能有 BGM + 拍点网格。
要"好听"，走下面的升级路径。

## 升级路径（按性价比）

1. **先加 pedalboard**（已做）：同样一坨正弦，过了压缩+限幅+EQ 之后可用度提升很大。
2. **再用 music21 管和声**：把 `PROGRESSION` 换成 `roman.RomanNumeral`，自动给正确转位与声部进行，
   避免手写音级算错。代价：多一个已装依赖。
3. **最后上 fluidsynth + SoundFont**（要真乐器才做）：
   ```bash
   brew install fluid-synth
   # 下 GeneralUser GS 或 FluidR3_GM（~30MB）到 assets/audio/sf2/
   ```
   然后 `music21` 出 MIDI → `fluidsynth -F out.wav soundfont.sf2 in.mid`。
   这一步之后，`bgm-gen.py` 的合成层就可以退役，只保留编曲逻辑。

## 卡点：用 librosa 分析外部音乐

如果用户坚持用一首现成的曲子（不是我们生成的），**不要猜 BPM**：

```python
import librosa
y, sr = librosa.load("track.mp3", sr=22050)
tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units="time")
```

把 `tempo` 与 `beats` 写进 `audio/beat-grid.json`（`downbeats` 可取每 4 拍），
后面 `beat-snap.py` 的流程完全不变。这是唯一可靠的"卡点音乐"做法。

## 参考片实测（作为节奏基准）

`ScreenRecording_10-26-2026 11-11-20`（102s 目录片）：
- 音频 onset 中位间隔 **0.35s** → **≈86 BPM**
- 视觉突变点间隔中位数 **3.0s** ≈ 1 小节（86 BPM 下 4 拍 = 2.79s）
- 102s 内 22 个强变化点 ≈ 每 4.6s 一次 —— **不是每一拍都动**

即：这类片子的呼吸是「一小节一个变化，偶尔两小节一个」，而不是逐拍卡点。
`--plan` 默认对齐 `beats` 是对的；追求更强的卡点感再用 `--on downbeats`。
