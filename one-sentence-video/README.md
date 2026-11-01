# One-Sentence Video (`one-sentence-video`)

> [English Version (`README.en.md`)](./README.en.md)

**一句话做视频**（One-Sentence Video）是面向 HyperFrames 程序化动画视频制作的**自包含自动驾驶入口 Skill**。它不依赖外部选题或口播脚本管道，内置从自然语言需求解析、三幕视觉分镜、审美方向三选一、组件注册表检索、具名镜头接缝（Seam）、代码合成音乐/音效（BGM + SFX）到抽帧密度门禁的完整端到端工程链路。

针对**「知识讲解类动画制作研究课题」**，本 Skill 在原有 20 套跨题材风格与 19 张实测镜头卡基础上，深度逆向并融合了三条抖音/B站爆款硬核知识讲解视频（小哲讲 Agent、小哲讲大模型、第四种黑猩猩 DeepSeek 算力经济学），扩展为 **23 套四轴风格账本** 与 **22 张测量级镜头卡（Shot Cards）**。

---

## 1. 核心架构：7 步自动驾驶制作流水线

| 步骤 | 阶段名称 | 核心产物 | 关键机制与强制规则 |
|---|---|---|---|
| **Step 0** | **收料与立项卡** | 3 行立项卡回复 | 解析主题/文案/画幅/素材；默认 **1920×1080 横屏 30fps、20–30s（5–7 镜）、无口播、开 BGM+SFX**。 |
| **Step 1** | **工程初始化** | HyperFrames 项目骨架 | 就地或通过 `npx hyperframes init` 创建标准横屏工程目录。 |
| **Step 2** | **三幕分镜（视觉驱动）** | `STORYBOARD.md` | 先查 `card-index.py` 套用实测镜头卡配方与能量曲线（`--energy-plan` 防止连续三镜同能量）；严控文字预算（标题 4–8 字 / 副句 ≤10 字 / 标签 ≤6 字 / 说明段 0 字）。 |
| **Step 3** | **三方向样帧比选** | `output/directions/{A,B,C}.png`<br>`design-spec.md` | **唯一强制用户决策**：从 `style-ledger.json` 取候选，渲染 3 张 1920×1080 真实文案样帧供用户拍板，落盘 `palette_source: <style-id>`。严禁默认深蓝霓虹 AI 制服。 |
| **Step 4** | **逐镜 Registry 布局闸** | `output/registry-ledger.md` | **能装不手写**：先用 `layout-index.py` 按构图轴查现成块，再用 `catalog-search.py` 按功能轴查块，逐镜登记命中与手写理由。 |
| **Step 5** | **写帧与具名 Seam 动效** | `compositions/frames/*.html` | 遵循 HyperFrames 渲染铁律（GSAP 只动平铺 clip 本体、禁嵌套 clip、CSS 进 `<template>`）；每镜边界声明具名 seam（`cut-the-curve` / `zoom-through` / `scale-through` / `whip-x` 等）。 |
| **Step 5.5** | **三层声音工程** | `audio/bgm.wav` + `beat-grid.json`<br>`audio/sfx.wav` + `sfx-events.json` | ① `bgm-gen.py` 代码编曲生成 WAV 与拍点网格 → ② `beat-snap.py` 校验剪辑点吸附（±50ms） → ③ `sfx-gen.py` 合成帧级因果音效。 |
| **Step 6** | **双层门禁与渲染交付** | `renders/draft-check.mp4`<br>`renders/video.mp4` | 先过 `process-gate.py --stage all` 与 `npm run check`，再经 draft 抽帧过 `density-gate.py --strict-safe` 六判据，用户确认后输出高画质成片。 |

---

## 2. 四轴风格账本（23 套风格预设）

真值源文件：`references/style-ledger.json`（人读版：`references/style-ledger.md`）。每套风格沿 **Look（调色板与字体）× Layout（构图原型）× Motion（接缝与镜内路线）× Sound（音效 Motif 与 BGM）** 四轴定义：

- **17 套浅底风格（默认候选池）**：
  `paper-catalog`（纸感目录）、`manifesto-poster`（宣言海报）、`research-note`（研究笔记）、`blueprint-report`（产品报告）、`broadside-news`（头版大字报）、`code-editorial-tour`（代码编辑导览）、`cobalt-index`（蓝格索引）、`cartesian-restraint`（克制图录）、`coral-contrast`（珊瑚强对比）、`capsule-candy`（糖果几何）、`blockframe-blocks`（积木色块）、`creative-journal`（创作手记）、`daisy-soft`（柔彩手账）、`biennale-artbook`（艺术年鉴）、`ink-scroll`（水墨卷轴）、**`xiaozhe-rag-pipeline-flow`（RAG四层漏斗）**、**`chimp-deepseek-unit-economics`（算力经济学）**。
- **6 套深色风格（🌙 须用户明确拍板，登记于 `USER_APPROVED_DARK_STYLES`）**：
  `speed-board`（记分牌）、`vault-gold`（金库蓝）、`night-cinema`（夜场影院）、`metal-spec`（金属参数）、`cyber-hud`（赛博 HUD）、**`xiaozhe-mcp-node-graph`（分层拓扑树）**。

---

## 3. 三大知识讲解标杆视频风格与镜头卡映射

针对技术/AI 架构与算力经济学知识讲解视频，本 Skill 提炼了 3 套标杆风格预设与 3 张配套测量级镜头卡：

| 标杆参考视频 | 风格 ID (`style-ledger.json`) | 极性 | 核心色板 (Look) | 构图与配套镜头卡 (`references/cards/catalog/`) | 核心动效签名 (Motion) |
|---|---|---|---|---|---|
| **小哲讲 agent**<br>《MCP / Skill / 本地 Tools 分层拓扑》 | `xiaozhe-mcp-node-graph` | `dark` 🌙 | 深黑曜石青绿微光 `#050C0A`→`#081614`、主字 `#F8FAFC`、协议薄荷绿 `#4ADE80`、方法丁香紫 `#A78BFA`、执行琥珀黄 `#FBBF24`、痛点珊瑚粉 `#FB7185` | 左上章节编号胶囊 (`[01] 核心问题`) + 三次贝塞尔分支节点树 + 右侧圆环痛点仪表盘 (`90% 容易混淆`)<br>👉 卡：[`progressive-node-tree.md`](./references/cards/catalog/progressive-node-tree.md) | 焦点节点放大高亮 (`scale: 1.08`) + 非焦点分支自动降暗 (`opacity: 0.25`) + SVG 连线脉冲流光；接缝 `scale-through` / `whip-x` |
| **小哲讲大模型**<br>《一条视频彻底吃透 RAG》 | `xiaozhe-rag-pipeline-flow` | `light` | 暖白编辑室 `#F7F6F2`、白卡 `#FFFFFF` (`2px solid #0F172A`)、切片钴蓝 `#2563EB`、召回青 `#0891B2`、重排橙 `#EA580C`、生成绿 `#16A34A`、碎片警示红 `#DC2626` | 四阶漏斗流水线 + 角色拟人标签（超级实习生/短期便利贴/长期知识库）+ 顶部进度轨<br>👉 卡：[`funnel-stage-filter.md`](./references/cards/catalog/funnel-stage-filter.md) | `packet-hop-break` 文档块沿轨跳跃，错误切分在节点同帧变红碎裂为残片，经 Rerank 漏斗低分下坠淘汰、高分入槽 |
| **第四种黑猩猩**<br>《DeepSeek 单卡 $38 算力经济学》 | `chimp-deepseek-unit-economics` | `light` | 暖米白纸张 `#FAF9F6`、深墨黑 `#0F172A`、基准灰 `#94A3B8`、克莱因蓝 `#2563EB`、瓶颈活力橙 `#F97316`、命中翡翠绿 `#10B981`、MoE 专家紫 `#8B5CF6` | 左上直给观点大标题 + 中央 GPU 算力砖块矩阵 + 右侧巨型倍率算式 (`$38 vs $5.7 ≈ 6.7x`) + 左下圆形 PiP 锚点<br>👉 卡：[`gpu-matrix-ledger.md`](./references/cards/catalog/gpu-matrix-ledger.md) | `counter-seek-safe` 巨型数字跳动 + GPU 网格逐列染色波浪 + 木桶效应最慢卡阻塞对比条 + `whip-x` 高速切章 |

---

## 4. 测量级镜头卡库（22 张 Shot Cards）

索引文件：`references/cards/_index.json`（通过 `python assets/card-index.py --rebuild` 生成，`--audit` 校验七节完整性）：

- **Catalog 构图/版式卡（13 张）**：
  `numbered-section-open`、`hero-plus-thumbnail-wall`、`three-way-bakeoff-row`、`caption-bar-close`、`two-column-corridor`、`orbit-ring-title`、`cast-list-poster`、`stat-pills-row`、`repeated-text-texture`、`cta-pill-close`、**`progressive-node-tree`**、**`funnel-stage-filter`**、**`gpu-matrix-ledger`**。
- **Motion 动效/时序卡（8 张）**：
  `seam-cut-the-curve`、`world-pan-parallax`、`packet-hop-break`、`counter-seek-safe`、`notch-rail-progress`、`easing-family`、`section-beat-density`、`scene-handoff-overlap`。
- **Sound 声音节拍卡（1 张）**：
  `beat-grid-snap`。

---

## 5. 双层门禁体系（Process Gate + Density Gate）

1. **过程闸门（`assets/process-gate.py` & `assets/palette-audit.py`）**：
   - **Palette 闸**：强制校验 `design-spec.md` 的 `palette_source`；深色风格必须属于 `USER_APPROVED_DARK_STYLES` 且具备用户拍板记录；拦截未授权的 Neon Pulse 残留色值。
   - **Direction 闸**：检查 `output/directions/` 下 3 张 `1920×1080` PNG 样帧、`README.md` 与方向决策记录。
   - **Layout 闸**：校验每镜 `registry:` 行、`output/registry-ledger.md` 台账行数以及 `card:` ID 在 `_index.json` 中的存在性。
   - **Motion 闸**：校验每镜具名 `seam`、`velocity=` ease 对、`carrier=` 驻留主体，并扫描 `STORYBOARD.md` 禁用词（如 `uniform fade+slide`）。
   - **Sound & Beat 闸**：校验 `audio/sfx-events.json`、`audio/sfx.wav`（≥44.1kHz 双声道）、根级 `<audio>` 挂载以及 `beat-snap.py` 剪辑点拍点对齐。
2. **成片密度闸门（`assets/density-gate.py`）**：
   - 基于抽帧图像梯度与时间差分检测「平庸/PPT 感」：死区检测（九宫格 ≥4 格空置连续 ≥2s）、结构变化间隔（中位数 ≤4.0s）、画面冻结占比（≤30%）、缓动指纹单一性（单一 ease ≤70%，`back.out` ≤2 次）、相邻构图重复警告与动作安全区越界检查（`--strict-safe`）。

---

## 6. 常用命令速查

```bash
# 1. 查看全部 23 套风格或按题材/构图/深色查询
python one-sentence-video/assets/style-query.py --list
python one-sentence-video/assets/style-query.py --genre tech-deep --dark
python one-sentence-video/assets/style-query.py --id xiaozhe-mcp-node-graph

# 2. 查看全部 22 张镜头卡、自审合规性或规划镜头能量曲线
python one-sentence-video/assets/card-index.py --list
python one-sentence-video/assets/card-index.py --audit
python one-sentence-video/assets/card-index.py --energy-plan 7

# 3. 执行过程门禁与成片密度门禁
python one-sentence-video/assets/process-gate.py <project-dir> --stage all
python one-sentence-video/assets/density-gate.py <project-dir> --strict-safe
```
