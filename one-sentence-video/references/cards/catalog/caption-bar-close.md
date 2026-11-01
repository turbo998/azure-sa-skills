---
id: caption-bar-close
name_zh: 底部一句话条
category: catalog
role: layout
energy: 1
duration: 1.6
layouts: [banded-three]
seams: [cut-the-curve]
sound: [thud]
genres: [tech-deep, neutral, news, career]
source: 逆向自 ScreenRecording_10-26-2026 11-11-20 全片复现（每章结尾一句）
verified: measured
---

## 意图
给每一章一个"结论句"，让观众带走一句话而不是一堆图。
它同时是章节之间的呼吸点——没有它，画面会连续轰炸。

## 适用
每一章结尾；章节之间需要「呼吸」的地方；成片需要观众带走一句话的场合。

## 构图
- 白底矩形：高 76，左右内边距 48，居中，y=930
- 文字：中文 40px，字重 500，黑
- 下面 1px 黑线（距底 6px），只画在文字宽度内（`width: fit-content`）

## 时间表
| t | 动作 |
|---|---|
| 0.0 | 条从 y+24 上浮 + 透明度 0→1，0.32s |
| 0.5 | 下划线从左 scaleX 0→1，0.4s |

## 缓动
`power2.out`——这一格是"收"，不是"放"，不要用 `power4`。

## 参数表
| 参数 | 典型值 | 调节手感 |
|---|---|---|
| 条高 | 76 | <60 读作细线；>96 读作卡片 |
| 左右内边距 | 48 | 小于 32 字会贴边 |
| 字号 | 40 | 与画面高度比 <3% 读不清 |
| 下划线距底 | 6 | 大于 10 会飘成两件东西 |
| 位置 | y=930（安全区内） | 超出 972 会压到动作安全区 |

## HyperFrames 要点
- 条的位置**必须在安全区内**（横屏 90% action-safe：y ≤ 972）。
- 条是白底，若整片底色是浅纸，白条会"浮"——加 1px 描边或把白换成 `#FFFFFF` + 4px 投影。
- 文字只用一句话 ≤ 12 字，超出换行就失去"条"的形状。

## 声音
`thud` 轻（gain .25），给"落定"感；不要 chime（太庆祝）。

## 何时不用
- 已经用了 `numbered-section-open` 的底部条：二者选一，否则底部会打架。
