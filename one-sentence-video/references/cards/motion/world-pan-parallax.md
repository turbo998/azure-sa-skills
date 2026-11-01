---
id: world-pan-parallax
name_zh: 一镜一世界（横移 + 视差）
category: motion
role: camera
energy: 3
duration: 3.1
layouts: [one-shot-world]
seams: [cut-the-curve]
sound: [whoosh]
genres: [tech-deep, career, auto, neutral]
source: eccom METHOD §5③ + §13.3（站间距 = 站宽；背景走前景 0.35×）
verified: measured
---

## 意图
用一个横向长世界承载 3 个阶段，镜头走过去，观众自己完成"递进"的推理。

## 适用
3–4 个阶段需要递进展示；一镜讲完一条时间线/流程。

## 构图
- 世界宽度 = 站数 × 站宽
- **站间距 = 站宽**（本项目 1680 / 1820，含 140 左边距）
- 间距 < 站宽 → 上一站内容会从画面边缘漏进来（v1 踩过）

## 时间表（3 站，3.1s）
```js
tl.to("#s4-world", { x: -3640, duration: 3.1, ease: "none" }, 0);   // 前景
tl.to("#s4-bg",    { x: -1274, duration: 3.1, ease: "none" }, 0);   // 背景 = 0.35×
```

## 视差规则
- 背景只走前景的 **30–40%**
- **必须同向**（都向左 / 都推近）；反向会读成穿帮
- 缩放镜头同理：`cam 1.0→1.045` 时背景只 `1.0→1.015`

## 参数表
| 参数 | 典型值 | 调节手感 |
|---|---|---|
| 站间距 | **= 站宽** | 小于站宽，上一站内容会从边缘漏进来 |
| 背景视差 | 前景的 0.35× | >0.5 读作「两层在打架」；<0.2 没有纵深 |
| 横移 ease | `none` | 用缓动会读作「卡了一下」 |
| 站数 | ≤4 | 超过 4 横移太长，改用分镜 |
| 总时长 | 站数 × 1.0s | 每站 <0.8s 读不完 |

## HyperFrames 要点
- `ease:"none"`——横移必须是匀速，缓动会读成"卡了一下"
- 世界容器不要做 clip 的子元素动画；只 tween 容器本身
- 站与站之间留空（无内容）也是构图，不要填满

## 声音
`whoosh` 每过一站一次，pan 跟运动方向；不要连续长 whoosh。

## 何时不用
- 站数 > 4：横移会太长，改用 `numbered-sections` 分镜。
