---
id: scene-handoff-overlap
name_zh: 场景重叠交接
category: motion
role: transition
energy: 3
duration: 0.5
layouts: []
seams: [cut-the-curve, waterfall cut, zoom-through]
sound: [whoosh]
genres: [tech-deep, movie, gaming, auto, neutral]
source: 逆向本地 minimax-h3（6 场景，相邻重叠 0.4–0.6s）+ 参考片实测
verified: measured
---

## 意图
两个场景在时间轴上**重叠** 0.4–0.6s，交接时前后两镜同时可见——
这是子组合架构下最稳的缝合方式，比硬切柔和，比长 crossfade 利落。

## 适用
子组合架构下的镜间交接（几乎所有多镜片）；需要柔和但不能拖的转场。

## 实测数据（minimax-h3）
| 场景 | start | dur | 与下一镜重叠 |
|---|---|---|---|
| scene-01 | 0.0 | 5.0 | 0.6s |
| scene-02 | 4.4 | 6.0 | 0.4s |
| scene-03 | 10.0 | 5.0 | 0.6s |
| scene-04 | 14.4 | 9.0 | 0.6s |
| scene-05 | 22.8 | 7.0 | 0.4s |
| scene-06 | 29.4 | 7.0 | — |

重叠量 0.4–0.6s，**不是固定值**——按镜头能量微调：能量高的重叠短（0.4），低的可以长（0.6）。

## 写法
```html
<div class="scene" data-composition-id="scene-02"
     data-composition-src="compositions/scene-02.html"
     data-start="4.4" data-duration="6"></div>
<!-- 上一镜 data-start="0" data-duration="5" → 4.4~5.0 之间两者同时可见 -->
```

## 交接期两边各做什么
- **出场镜**：最后 0.3s `opacity 1→0` + 位移（`power2.in`）
- **入场镜**：前 0.5s `opacity 0→1`（`power2.out`）
- **两侧都在动**——只做淡入淡出会读作"幻灯片切换"

## 参数表
| 参数 | 典型值 | 调节手感 |
|---|---|---|
| 重叠时长 | 0.4–0.6s | <0.3 读作硬切但有鬼影；>0.8 两镜内容会打架 |
| 出场淡出 | 0.3s `power2.in` | 与重叠时长同步，别在重叠结束后还在淡 |
| 入场淡入 | 0.5s `power2.out` | 比出场长一点，观感更稳 |
| 底色一致性 | 必须相同 | 底色不同时 0.5 透明度会闪白 |

## HyperFrames 要点
- 重叠区里**两个 scene 的 clip 都在跑**，track index 必须不同，否则冲突。
- 若两镜中央都有主体，重叠时会出现"两个主体"——错开 60–100px 或让一方先退。

## 声音
`whoosh` 在重叠区中点（不是出场镜末尾），pan 跟运动方向。

## 何时不用
- 同底色、同构图的连续镜：硬切更好，重叠反而糊。
