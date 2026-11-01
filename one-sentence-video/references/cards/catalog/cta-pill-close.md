---
id: cta-pill-close
name_zh: 结尾 CTA 胶囊
category: catalog
role: layout
energy: 3
duration: 2.0
layouts: [centered-hero]
seams: [zoom-through]
sound: [chime, thud]
genres: [tech-deep, career, gaming, auto]
source: 逆向本地 minimax-h3 scene-06（"都AI剪辑，不用再等人工了" 胶囊 + 下箭头）
verified: measured
---

## 意图
最后一镜必须给一个"动作"或"结论"，而不是让画面淡出。胶囊是最低成本的行动召唤形态。

## 适用
成片最后一镜；章节结尾（弱化版）。

## 构图
- 一句话（≤14 字）装进胶囊：高 96–112，左右内边距 56，全圆角
- 胶囊用强调色描边 + 8% 同色填充（不要实心——实心太重）
- 上方一行主结论（40–56px），下方可留品牌名
- 箭头：胶囊内右侧，或胶囊下方（二选一）

## 时间表
| t | 动作 |
|---|---|
| 0.00 | 主结论从 y+50 落位，`power3.out`，0.6s |
| 0.45 | 胶囊从 scale 0.94 → 1 + 透明度，`power2.out`，0.5s |
| 0.75 | 箭头下落 14px 再回，`sine.inOut`，**2 次即止**（不是无限） |
| 1.90 | 整组 opacity 1→0，`power2.in`，0.3s |

## 参数表
| 参数 | 典型值 | 调节手感 |
|---|---|---|
| 胶囊高 | 96–112 | <80 读作标签；>130 读作按钮，视频里按钮不可点会显得假 |
| 文字 | ≤14 字 | 超出换行就失去胶囊形状 |
| 箭头回弹 | 2 次 | `repeat:4` 是"idle wobble"，观众会等它停 |
| 收尾淡出 | 0.3s | 长于 0.5s 读作"没做完" |

## HyperFrames 要点
- 箭头**不要**用无限 `repeat:-1`（渲染器对无限重复不可靠，且是禁词）。
- 收尾淡出若与下一镜重叠，注意 clip 时间窗不重叠。

## 声音
`chime` 胶囊落定（gain .4）；`thud` 整片结束（gain .45，与最后一帧同帧）。

## 何时不用
- 无 CTA 的纯信息片：用一个 `caption-bar-close` 收尾即可，硬加 CTA 会显得像广告。
