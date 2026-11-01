---
id: orbit-ring-title
name_zh: 环形巡回标题
category: catalog
role: layout
energy: 3
duration: 5.0
layouts: [centered-hero, card-deck]
seams: [cut-the-curve]
sound: [whoosh, chime]
genres: [tech-deep, gaming, movie, auto]
source: 逆向本地 minimax-h3 scene-01（5s，环形徽章 + 逐字标题 + glitch）
verified: measured
---

## 意图
"我们有一整套东西"——不摆九宫格，而是让卡片绕着一个中心匀速巡回：
永远有卡进画、有卡出画，画面自带"还有更多"的暗示，标题稳稳钉在中间。

## 适用
开场第一镜 / 素材库、模板库、功能矩阵的门面拍。

## 构图
- 椭圆轨道：RX 720 / RY 380（**RY/RX ≈ 0.53 读作"俯视的环"，比值→1 会读成转盘**）
- 卡 400×225（16:9），8 张，方位角间隔 45°
- 中心标题：上行 64px 灰、下行 156px 主色
- 轨道本身画成一圈 16% 透明度的强调色发丝线

## 时间表
| t | 动作 |
|---|---|
| 0.00 | 环从中心撑开 scale 0.62→1，`expo.out`，0.8s |
| 0.07 | 逐卡淡入，第 i 张从 `0.07+0.05i` 起，0.37s |
| 0.40 | 标题逐字：y 90→0，rotate 7→0，`power3.out`，单字 0.32s，stagger 0.08 |
| 1.50 | glitch 一次：x −10→7→−4→0，共 0.24s（**只此一次**） |
| 4.70 | 退场 opacity→0，0.3s `power2.in` |

## 纵深（关键）
卡身**永不倾斜**，只换位置。纵深完全交给 `depth = sin θ`：
`scale = 1 + 0.12·depth`，远处再叠 `blur(1.6·|depth|px)` + 压暗。
**缩放、z 序、明暗必须由同一个 depth 驱动**，否则会出现"远处的卡压住近处的卡"。

## 参数表
| 参数 | 典型值 | 调节手感 |
|---|---|---|
| 椭圆比 RY/RX | 0.53 | →1 读作正圆转盘；→0.3 卡在上下缘挤成一条 |
| 卡数 | 8 | 8 张在这个半径上任意转角互不遮挡；≥10 必须同步放大 RX/RY |
| 公转速度 | 0.3 rad/s | **别因为"看着慢"就调快**；>0.5 卡扫过边缘会有频闪 |
| 环入场 | 0.8s expo.out | <0.5s 像弹窗；>1.0s 标题起手时环还在长，两件事互相盖 |
| 逐卡步长 | 0.05s | 刚够读出"依次"；>0.1s 最后一张会晚到标题之后 |
| 纵深缩放 | ±12% | >15% 顶部卡缩成图标，环读作"透视隧道" |

## HyperFrames 要点
- 环上定位用 JS 逐帧算（`tl.to(obj,{...onUpdate})`）或 GSAP `motionPath`；**不要**给每张卡单独写 8 个 keyframe。
- 卡内若是视频/动效，入场期冻结在首帧（`video.currentTime` 由框架管），等环撑开后再播。
- 8 张卡各自一个 clip 会占 8 条 track；改用**一个容器 clip + 容器内绝对定位**。

## 声音
`whoosh` 环撑开（0.0，pan 由左到右）；`chime` 标题落定（0.72）。glitch 不给声音（无声更冷）。

## 何时不用
- 只有 3–4 个内容：环太稀，改用 `hero-plus-thumbnail-wall`。
- 浅纸底：椭圆轨道在浅底上会读成"阴影"，改用 `numbered-section-open`。
