# 卡片库（Shot Cards）

一张卡 = **一个可复用的镜头配方**，带实测数值、时间表、参数表、HyperFrames 实现要点与声音配对。
它不是灵感板，是施工图：写帧时照着抄数值，不需要重新发明。

## 卡格式

```yaml
---
id: <kebab-case>
name_zh: 中文名
category: catalog | motion | sound
role: layout | typography | data | camera | sequence | transition | background | rhythm
energy: 1..5          # 视觉能量，用于排节奏（不能连续三镜同 energy）
duration: 秒（0 = 不绑定时长）
layouts: [构图原型]    # 对应 style-ledger 的 layout 轴
seams: [具名 seam]
sound: [motif]
genres: [题材]
source: 来源（逆向自哪支片 / 哪份 METHOD）
verified: measured | derived   # measured = 有实测数值；derived = 推理
---
```

正文七节（`--audit` 会查）：

| 节 | 必需性 | 作用 |
|---|---|---|
| **意图** | 必填 | 这一镜解决什么问题 |
| **适用** | 必填 | 什么时候该用（不给适用面的卡会被乱用） |
| **构图** | layout / typography / data / background 必填 | 坐标、尺寸、层级 |
| **时间表** | layout / typography / data / camera / sequence 必填 | 拍点 → 动作 |
| **参数表** | 除 transition / rhythm 外必填 | 典型值 + **调节手感**（调过头会怎样） |
| **HyperFrames 要点** | 必填 | clip / track / seek 安全约束 |
| **声音** | 必填 | 配哪个 motif、几时响 |
| **何时不用** | 必填 | 边界。没有边界的配方会被滥用 |

> **参数表的「调节手感」是整张卡最有价值的一栏**——它告诉你往两边调会发生什么，
> 而不是只给一个数。抄数容易，知道边界才是配方。

## 造卡流程（逆向一支片）

1. **抽帧定位**：`ffmpeg -i film.mp4 -vf fps=6,scale=64:36,format=gray -f rawvideo -`
   → 逐帧差分找视觉突变点（比 ffmpeg `scene` 滤镜更灵，后者对渐变转场不敏感）。
2. **量节奏**：突变点间隔的中位数 = 这片子的「呼吸」。参考片实测 3.0s ≈ 86 BPM 一小节。
3. **取色**：裁掉黑边后取四角中位数当底色，取高饱和像素众数当强调色。
4. **拆时间表**：对一个镜头逐 0.1s 抽帧，记录每个元素第一次出现/开始移动/停下的时刻。
5. **反推缓动**：量两点的位移差 → 速度曲线 → 匹配到 power1/2/3/4 或 back。
   **有源码就读源码**——本地成片能同时读到 `compositions/*.html`，数值是精确的。
6. **写卡**：只写你能量到的。量不到的写 `verified: derived` 并说明依据。
7. **自审 + 登记**：`python3 assets/card-index.py --audit && python3 assets/card-index.py --rebuild`

## 与 registry 的关系

- **registry 是「装现成的」**（`hyperframes add`，有实现、能跑）
- **卡片是「怎么写」**（有数值、有边界、有声音配对）
- 顺序：先按构图查 `layout-index.py` 看有没有现成块；没有才按卡片手写。
- 卡片命中但 registry 无块 → 这是**该提 feedback 的信号**（`hyperframes feedback --search-miss`）。
- STORYBOARD 里写了 `card: <id>` 就必须真实存在，`process-gate --stage layout` 会拦编造的 id。

## 当前卡片（22 张）

| 类别 | 卡片 |
|---|---|
| catalog（13） | 大序号章节开场 / 主图加缩略图墙 / 三案并排比选 / 底部一句话条 / 双栏收敛走廊 / 环形巡回标题 / 海报大字+名单 / 统计胶囊 / 重复文字底纹 / 结尾 CTA 胶囊 / 渐进式贝塞尔节点树 (`progressive-node-tree`) / 四阶漏斗过滤流水线 (`funnel-stage-filter`) / GPU算力矩阵与单位经济学账本 (`gpu-matrix-ledger`) |
| motion（8） | 缝合 / 一镜一世界视差 / 逐跳撞断点 / seek 安全计数器 / 累积刻痕 / 缓动家族分工 / 结构拍点密度 / 场景重叠交接 |
| sound（1） | 拍点吸附 |

来源分四类：
- **参考片**（`ScreenRecording_10-26-2026`，实测 86 BPM / 3.0s 一小节）：章节开场、缩略图墙、三案比选、字幕条
- **eccom METHOD**（v1→v2 标定）：缝合、一镜一世界、逐跳撞断点、计数器、累积刻痕、双栏走廊
- **本地成片逆向**（minimax-h3 等）：环形巡回、海报名单、统计胶囊、重复文字、CTA 胶囊、场景重叠、缓动家族
- **知识讲解标杆视频实测拆帧**（小哲讲agent / 小哲讲大模型 / 第四种黑猩猩）：渐进式贝塞尔节点树、四阶漏斗过滤流水线、GPU算力矩阵与单位经济学账本

查询：`python3 assets/card-index.py --genre tech-deep` / `--layout` / `--seam` / `--energy-plan N`
