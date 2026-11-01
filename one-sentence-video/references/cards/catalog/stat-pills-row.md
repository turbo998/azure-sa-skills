---
id: stat-pills-row
name_zh: 统计胶囊
category: catalog
role: data
energy: 3
duration: 2.5
layouts: [data-dashboard, banded-three]
seams: [waterfall entry]
sound: [tick, chime]
genres: [tech-deep, finance, sports, auto, career]
source: 逆向本地 minimax-h3（2K / 15s / 2 三枚胶囊，等距横排，带描边与数值）
verified: measured
---

## 意图
三个数字胜过三句话。胶囊形状（全圆角 + 细描边）让数字读作"规格"而不是"标语"。

## 适用
参数镜、能力镜、"三个关键指标"镜。

## 构图
- 三枚等距横排，胶囊高 88–104，宽度随内容（**不要三枚等宽**——等宽读作表格）
- 每枚：数值 44–52px（等宽字体）+ 标签 15px mono 大写 + 1px 描边
- 整组居中，间距 24–32
- 上方一行说明（22px），下方一行补充（15px，透明度 .55）

## 时间表
| t | 动作 |
|---|---|
| 0.00 / 0.10 / 0.20 | 三枚依次从 y+28 落位，`power3.out`，0.45s |
| 0.60 | 数值 count-up（seek 安全写法，见 `counter-seek-safe`） |
| 1.40 | 描边从透明到实色，`power2.out`，0.3s |
| 2.10 | 上方说明淡入 |

## 参数表
| 参数 | 典型值 | 调节手感 |
|---|---|---|
| 胶囊高 | 88–104 | <70 读作"标签"；>120 读作"卡片" |
| 数值字号 | 44–52 | 与标签字号比 ≥2.5:1，否则没有主次 |
| 落位 stagger | 0.10s | <0.06 三枚一起弹；>0.16 最后一枚晚到说明之后 |
| 圆角 | 高度的一半（全圆） | 半圆角会读作"按钮" |

## HyperFrames 要点
- 三枚胶囊在**一个容器**里用 flex，容器做一个 clip；不要三个 clip（会撞 track）。
- 数值用等宽字体，否则 count-up 时整行宽度跳动。

## 声音
`tick` 每枚落位（gain 递增 .14/.18/.22）；`chime` 数值停住（gain .3）。

## 何时不用
- 只有 2 个指标：用 `split-compare`；4 个以上：改用 `data-dashboard` 整页。
- 数字不真实：胶囊会放大虚假感，宁可不放。
