---
id: beat-grid-snap
name_zh: 拍点吸附
category: sound
role: rhythm
energy: 3
duration: 0
layouts: []
seams: []
sound: [thud, whoosh]
genres: [tech-deep, career, gaming, sports]
source: 实测 ScreenRecording_10-26-2026 11-11-20：约 86 BPM，视觉变化间隔中位数 3.0s
verified: measured
---

## 意图
让"剪辑点"落在拍点上。不是所有片子都需要，但一旦用了音乐，cut 不落在拍上就会读成"卡了一下"。

## 适用
有 BGM 的片子（几乎全部）；需要用一首现成曲子卡点的场合。

## 实测参考
- 参考片：**≈86 BPM**（音频 onset 中位间隔 0.35s = 半拍）
- 视觉变化（spike peak）间隔中位数 **3.0s** ≈ 1 小节（86 BPM 下 4 拍 = 2.79s）
- 102s 内 22 个强变化点 ≈ 平均每 4.6s 一次，**不是每一拍都动**

## 流程
```bash
# 1. 用账本的 sound.bgm 生成 BGM（同时产出拍点网格）
python3 assets/bgm-gen.py --style paper --bpm 86 --duration 26 --out audio/bgm.wav

# 2. 校验剪辑点是否落在拍上
python3 assets/beat-snap.py --grid audio/beat-grid.json --check 3.2,7.8,12.4

# 3. 或反过来：先定镜数，让工具给出吸附后的边界
python3 assets/beat-snap.py --grid audio/beat-grid.json --plan 7
```

## 规则
- 容差 **±50ms**（1 帧 33ms，两帧内可接受）
- 优先吸到**强拍**（小节头），其次拍，最后 8 分音符
- 不要在容差外硬吸——那会把分镜节奏改坏，宁可承认"这一刀不在拍上"

## 参数表
| 参数 | 典型值 | 调节手感 |
|---|---|---|
| 容差 | **±50ms** | ≈1.5 帧；<±30ms 太苛刻，>±80ms 听得出来 |
| 优先吸附 | 强拍 → 拍 → 8 分 | 强拍落刀最稳 |
| 参考 BPM | 86 | 一小节 2.79s |
| 段落变化 | 每 1–2 小节 | 参考片 102s 只有 22 次 |
| 硬吸上限 | 容差外不吸 | 硬吸会改坏分镜节奏 |

## 何时不用
- 无音乐（纯 SFX）的片子：拍点网格没有意义，用 SFX 事件对齐即可。
- 快闪片（每镜 < 0.5s）：拍点会限制剪辑，反而更差。
