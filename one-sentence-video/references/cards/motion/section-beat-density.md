---
id: section-beat-density
name_zh: 结构拍点密度
category: motion
role: rhythm
energy: 4
duration: 0
layouts: []
seams: [cut-the-curve]
sound: [thud, whoosh]
genres: [tech-deep, career, neutral, news]
source: 实测：参考片 22 个强变化/102s（3.0s 一次）vs 本地四支片 3–12 个（5.2–11.5s 一次）
verified: measured
---

## 意图
**"平"的量化定义**：不是画面不好看，是结构变化太稀疏。
观众每隔一段时间需要一次"这件事变了"的信号；超过 5s 没有，注意力就掉了。

## 适用
成片完成后诊断「平」；或分镜阶段预防结构变化过稀。

## 实测基准

| 片子 | 时长 | 强变化点 | 中位间隔 | 画面差分均值 |
|---|---|---|---|---|
| 参考片（目录片） | 102s | **22** | **3.0s** | 5.98 |
| eccom-ai-troubleshoot | 44s | 3 | 11.5s | 2.98 |
| minimax-h3 | 37s | 3 | 7.4s | 6.77 |
| openai-astra-pause | 40s | 6 | 5.2s | 0.64 |
| qwen38-flash | 82s | 12 | 8.5s | 0.35 |

**目标：中位间隔 ≤ 4s。** 超过 6s 就有段落读起来像静止画面。

## 怎么测（10 秒出结果）
```bash
ffmpeg -v error -i renders/video.mp4 -vf "fps=6,scale=64:36,format=gray" -f rawvideo - \
 | python3 -c "
import sys,numpy as np
f=np.frombuffer(sys.stdin.buffer.read(),dtype=np.uint8)
n=len(f)//(64*36); fr=f[:n*64*36].reshape(n,36,64).astype(float)
d=np.abs(np.diff(fr,axis=0)).mean(axis=(1,2)); thr=d.mean()+2*d.std()
p=[i for i in range(2,len(d)-2) if d[i]>thr and d[i]>=d[i-1] and d[i]>=d[i+1]]
g=[p[i+1]-p[i] for i in range(len(p)-1)]
print('peaks',len(p),'median gap %.2fs'%(np.median(g)/6 if g else 0))"
```

## 怎么补（不靠加装饰）
1. **章节化**：每 3–4 镜给一个 `numbered-section-open` 或 `caption-bar-close`。
2. **换构图**：相邻镜的构图轴必须不同（`hero-plus-grid` → `banded-three` → `one-shot-world`）。
3. **换能量**：`card-index.py --energy-plan N` 直接给一条不重复的能量曲线。
4. **加结构音**：每 3–4s 一个 `thud`（不是每拍）。

## 参数表
| 参数 | 典型值 | 调节手感 |
|---|---|---|
| 强变化中位间隔 | **≤4s** | >6s 有段落像静止画面 |
| 参考片基准 | 3.0s（22 次/102s） | 目录/信息密集片的上限 |
| 画面差分均值 | >1.5 | <1 说明整片近乎静止（本地两支片 0.35 / 0.64） |
| 每 3–4s | 一个结构音 `thud` | 每拍都给 = 白噪 |
| 相邻镜构图 | 必须不同 | 同构图连着出现 = 无变化 |

## 何时不用
- 长镜头冥想类/单镜一镜到底：本来就是低密度，硬加变化会破坏意图。此时在 design-spec 写明。
