---
id: hero-plus-thumbnail-wall
name_zh: 主图加缩略图墙
category: catalog
role: layout
energy: 3
duration: 5.0
layouts: [hero-plus-grid]
seams: [cut-the-curve]
sound: [flap, tick]
genres: [tech-deep, neutral, career]
source: 逆向自 ScreenRecording_10-26-2026 11-11-20 @ 22.8–26.8s（43 格缩略图 + 当前项橙框）
verified: measured
---

## 意图
一次给出「有多少种」和「其中一种是这个」——数量与个体同时成立。
这是目录片最有说服力的一格：它证明体系存在，而不只是宣称。

## 适用
证明「体系存在」的目录镜；素材库 / 风格库 / 模板库 / 案例集的门面拍。

## 构图
- 左主图：x=180，y=300，880×500，1px 描边 + 4px 白边（像一张放上去的照片）
- 左下名称：主图下方 y=840，中文 44px + 拉丁 32px mono
- 右墙：x=1100 起，8 列 × 6 行，格宽 92，间距 6，总宽 780
- **当前项**：2px 强调色描边 + 向外 3px 偏移（不是发光，是硬边）
- 右下角注：「样张 · 来自 X 仓库（Y, MIT）」14px mono，透明度 .5

## 时间表
| t | 动作 |
|---|---|
| 0.0–0.9 | 墙整体 `stagger 0.018s` 逐格出现（8×6=48 格，总 0.86s） |
| 0.9 | 当前项描边 draw-on（SVG stroke-dashoffset 或 4 条边依次 scaleX/Y） |
| 1.2 | 主图从 scale 1.06 → 1.00，`power3.out` 0.7s |
| 1.6 | 名称两行依次上推 |

## 缓动
墙用 `power2.out`（快出现、末尾缓停，模拟"刷"出来）；主图用 `power3.out`（更慢，形成主次）。

## 参数表
| 参数 | 典型值 | 调节手感 |
|---|---|---|
| 主图 | 880×500 | 小于 720 宽压不住右侧墙 |
| 网格 | 8 列 × 6 行，格宽 92，间距 6 | 列数 <6 气势不够；>10 单格认不出 |
| 逐格 stagger | 0.018s | 总时长控制在 0.9s 内；>0.03 拖太久 |
| 当前项描边 | 2px 强调色 + 外偏 3px | 用发光会读成「加载中」 |
| 缩略图数量 | ≥12 | 少于 12 改用 `three-way-bakeoff-row` |

## HyperFrames 要点
- 48 格不要写成 48 个 clip。用**一个容器 div + CSS animation-delay**，或用 GSAP 对容器内 `:nth-child` 批量 stagger；clip 只包容器。
- 主图若是 `<img>`，放在容器内即可，不要单独做 clip（clip 内子树不可 tween）。
- 缩略图墙必须真图。**纯色块墙会读成"加载占位符"**。

## 声音
`flap` 每 6 格一次（不是每格——48 声会变成白噪），`tick` 在描边落定。

## 何时不用
- 缩略图少于 12 张：墙的气势不够，改用 `three-way-bakeoff-row`。
- 没有真实缩略图：这一格会塌成 PPT 色块页。
