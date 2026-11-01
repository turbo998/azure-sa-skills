---
id: seam-cut-the-curve
name_zh: 缝合（运动中对切）
category: motion
role: transition
energy: 3
duration: 0.66
layouts: []
seams: [cut-the-curve]
sound: [whoosh, swipe]
genres: [tech-deep, finance, neutral, career]
source: eccom-ai-troubleshoot METHOD §6（v1→v2 实测标定）
verified: measured
---

## 意图
两侧都在运动中切换，让两个镜头读成"一台连续摄像机"而不是"两张幻灯片"。

## 适用
相邻两镜需要「一台摄像机」的连续感；默认缝合方式，全片统一。

## 数值（本项目标定，换题材需重标）
```
出场：x 0 → -280，opacity 1 → 0.5，0.30s，power2.in     末速 ≈ 2×280/0.30 = 1867 px/s
入场：x 200 → 0，opacity 0.5 → 1，0.36s，power3.out    初速 ≈ 3×200/0.36 = 1667 px/s
```
速度比 **0.89**，肉眼接得住。

## 前提
- **两侧底色必须相同**（本项目都是 `#05070c`），否则 0.5 的透明度会闪白。
- partial travel 控制在画面宽度的 ~12%（1920 × 0.12 ≈ 230）。

## 换向需要许可证
默认向左。只有两种情况可以从右切入：
1. 撞击点（反向本身就是"撞"的语义）
2. 收尾镜（那是"最后一击"不是"下一拍"）

## 参数表
| 参数 | 典型值 | 调节手感 |
|---|---|---|
| 出场位移 | 280px / 0.30s `power2.in` | 末速 ≈1867 px/s |
| 入场位移 | 200px / 0.36s `power3.out` | 初速 ≈1667 px/s |
| 速度比 | 0.89 | 低于 0.7 或高于 1.15 会「顿一下」 |
| partial travel | 画面宽 12%（≈230px） | >18% 读作「滑走」不是「切」 |
| 两侧底色 | 必须相同 | 不同底色 + 0.5 透明度 = 闪白 |

## HyperFrames 要点
- 子组合架构（每镜一个 composition）下**没有 seam-stamp**：每镜的包裹层就是缝合载体，
  参数手写在每镜脚本末尾，**改一镜必须顺手改它的前后两镜**，否则速度不匹配。
- 平铺 clip 架构才用 `seam-stamp.mjs` 生成。

## 声音
`whoosh` 随运动方向同向 pan（左切 → 从右往左）；**禁止每刀同一个 whoosh**。

## 何时不用
- 情感/治愈题材：用 `rack-focus blur-cut` 或直接缓淡，硬切会破坏情绪。
