---
id: easing-family
name_zh: 缓动家族分工
category: motion
role: rhythm
energy: 3
duration: 0
layouts: []
seams: [cut-the-curve, zoom-through, waterfall cut]
sound: [whoosh, thud]
genres: [tech-deep, career, neutral, gaming, finance]
source: 逆向本地 minimax-h3（6 镜全部 back.out(1.7)）+ eccom METHOD §6 实测
verified: measured
---

## 意图
**缓动是按角色分工的，不是一个全局默认。** 全片一个 `back.out(1.7)` 是"AI 制服"最明显的签名——
观众说不出哪里不对，但会觉得"这个片子和别的一样"。

## 适用
每一镜、每一个元素。这是唯一一张"所有片子都该用"的卡。

## 分工表

| 角色 | 该用什么 | 不该用什么 | 理由 |
|---|---|---|---|
| **入场**（元素出现） | `power3.out` / `expo.out` | `back.out` | 入场要"快到位、稳停下"，过冲会让文字像弹簧 |
| **位移**（A→B 移动） | `power2.inOut` / `sine.inOut` | `power3.out` | 位移两端都要减速，单向 out 会"撞墙" |
| **出场**（离开画面） | `power2.in` / `power4.in` | `power3.out` | 出场要加速离开，减速离开读作"舍不得走" |
| **镜头**（推拉摇移） | `none`（匀速）/ `power1.inOut` | 任何 out | 镜头是机器，机器没有"缓停" |
| **撞击**（唯一允许过冲） | `back.out(1.2~1.4)` **一次** | `1.7` 及以上 | 过冲 >1.4 会读成弹球 |
| **收尾定版** | `power2.out` | `expo.out` | 收尾要"落定"，不是"甩出去" |

## 反例（本地实测）

`minimax-h3` 6 个场景，**全部**是：
```js
tl.fromTo(el, { y: 60, opacity: 0 }, { y: 0, opacity: 1, duration: 0.9, ease: "back.out(1.7)" })
```
出现位置：scene-01 的 badge / elo / 标题逐字、scene-02 的 cat / cards、scene-06 的 quote / cta。
画面差分均值 6.77（本地最高），但**缓动只有一种**——动得多，不等于动得好。

## 自检
写完后 grep 一遍：
```bash
grep -c "back.out" compositions/frames/*.html     # 全片应 ≤ 2 次（撞击/定版各一）
grep -o 'ease: "[^"]*"' compositions/frames/*.html | sort | uniq -c | sort -rn
```
第二行若出现一个 ease 占 70% 以上，就是制服。

## 参数表
| 角色 | 典型值 | 调节手感 |
|---|---|---|
| `back.out` 出现次数 | 全片 ≤2 | 超过 2 次就是制服 |
| 入场 | `power3.out` | 想更利落用 `expo.out`，不要用 `back` |
| 出场 | `power2.in` | 用 out 读作「舍不得走」 |
| 镜头 | `none` | 镜头是机器，没有缓停 |
| 撞击过冲 | `back.out(1.2~1.4)` 一次 | >1.4 读作弹球 |
| 单一 ease 占比 | <50% | 超过 70% 就是制服（用 grep 自检） |

## 何时不用
- 情感/治愈片：整套换成 `sine.out`，时长 ×1.4，禁 `back`、禁 `power4`。
