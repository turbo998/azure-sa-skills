---
id: cast-list-poster
name_zh: 海报大字 + 名单
category: catalog
role: typography
energy: 4
duration: 3.0
layouts: [poster-full-bleed]
seams: [waterfall cut]
sound: [thud, tick]
genres: [movie, gaming, sports, news]
source: 逆向本地 minimax-h3 scene-02（MIDNIGHT LINE + 演员表 MAYA CROSS / JUNO PARK / KATO / LENA WARD）
verified: measured
---

## 意图
把"参与方/功能/角色"排成电影海报的演员表——它天然自带"这是一部正经作品"的暗示，
而且比"三张等宽卡片"高级得多。

## 适用
片名镜、功能矩阵镜、"谁参与了"镜、章节封面。

## 构图
- 主标题：满版巨字，占宽 70–85%，行高 0.86，字重 800+
- 名单：主标题下方 4–6 行，右对齐或左对齐（**不要居中**），mono 20px，字距 .2em，全大写
- 名单与主标题之间留 ≥ 主标题高度的 40%
- 背景：全屏素材压暗到 35–45%，或重复文字底纹（见 `repeated-text-texture`）

## 时间表
| t | 动作 |
|---|---|
| 0.00 | 主标题逐词上推，`clip-path` inset 100%→0，`power4.out`，每词 0.42s，stagger 0.06 |
| 0.55 | 名单逐行从左滑入（x −24→0）+ 透明度，`power2.out`，stagger 0.09 |
| 1.60 | 底部分隔线 scaleX 0→1，`power3.out`，0.5s |
| 2.60 | 整组 opacity 1→0.85（为下一镜让位） |

## 参数表
| 参数 | 典型值 | 调节手感 |
|---|---|---|
| 主标题字号 | 占宽 70–85% | 低于 60% 读作"标题"，不是"海报" |
| 行高 | 0.86–0.92 | >1.0 会散成两行；<0.8 上下行会撞 |
| 名单字号 | 20–24px | 再大就抢主标题；再小在手机上看不清 |
| 逐词 stagger | 0.06s | <0.04 读作"一起出现"；>0.1 会拖到名单进场 |
| 背景压暗 | 35–45% | 高于 55% 字会糊；低于 30% 背景抢戏 |

## HyperFrames 要点
- 逐词动画：**每个词一个平铺 clip**（同 y、独立 track、独立时间窗）。clip 内子 span 不可 tween。
- 若主标题是两行，两行各自成组，**不要**让一行跨越 clip 边界。

## 声音
`thud` 主标题落定（0.42，gain .5）；`tick` 名单每行一声（gain .12，别太重）。

## 何时不用
- 浅纸/编辑类题材：海报大字会显得"喊"，改用 `numbered-section-open`。
- 标题超过 8 个字：会撑破满版，先减字。
