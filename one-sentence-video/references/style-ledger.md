# 风格账本（人读版）

> 由 `references/style-ledger.json` 自动生成，**不要手改本文件**。
> 查询：`python3 assets/style-query.py --genre <题材>`
> 构图→现成块：`python3 assets/layout-index.py --style <id>`
> 卡片：`python3 assets/card-index.py --genre <题材>`

共 23 条 style：17 条浅底 + 6 条深色（🌙 必须用户拍板）。

## 全部条目

| id | 名称 | 底 | 强调 | 构图 | seam | 声音 | BGM | 题材 |
|---|---|---|---|---|---|---|---|---|
| `paper-catalog` | 纸感目录  | `#F0ECE5` | `#E85D26` | numbered-sections / hero-plus-grid | cut-the-curve | tick+flap | paper @ 86bpm | tech-deep, career, neutral |
| `manifesto-poster` | 宣言海报  | `#FFFFFF` | `#D8000F` | poster-full-bleed / centered-hero | zoom-through | thud+whoosh | dry-tech @ 100bpm | tech-deep, gaming, food |
| `research-note` | 研究笔记  | `#efe7d4` | `#2e4a2a` | editorial-grid / two-column-corridor | rack-focus blur-cut | tick+swipe | paper @ 92bpm | tech-deep, finance, guofeng |
| `blueprint-report` | 产品报告  | `#fdfae7` | `#1e2bfa` | data-dashboard / ui-stage | cut-the-curve | tick+chime | dry-tech @ 104bpm | finance, career, auto |
| `broadside-news` | 头版大字报  | `#F0ECE5` | `#E85D26` | poster-full-bleed / banded-three | waterfall cut | thud+flap | pulse @ 118bpm | news, sports, gaming |
| `code-editorial-tour` | 代码编辑导览  | `#FAF9F5` | `#CC785C` | one-shot-world / editorial-grid | zoom-through | swipe+tick | dry-tech @ 104bpm | tech-deep, career |
| `cobalt-index` | 蓝格索引  | `#F0EBDE` | `#5560E5` | editorial-grid / numbered-sections | cut-the-curve | tick | paper @ 96bpm | tech-deep, neutral |
| `cartesian-restraint` | 克制图录  | `#EDE8E0` | `#8A8178` | editorial-grid / split-compare | rack-focus blur-cut | swipe | soft @ 76bpm | guofeng, finance, neutral |
| `coral-contrast` | 珊瑚强对比  | `#F5F0E8` | `#E85D5D` | split-compare / poster-full-bleed | waterfall cut | thud+chime | pulse @ 112bpm | food, gaming, movie |
| `capsule-candy` | 糖果几何  | `#F5F5F0` | `#E85D4E` | card-deck / centered-hero | waterfall cut | chime+flap | soft @ 84bpm | baby, emotional, food |
| `blockframe-blocks` | 积木色块  | `#FFFDF5` | `#FE90E8` | card-deck / poster-full-bleed | waterfall cut | thud+chime | pulse @ 120bpm | gaming, sports, baby |
| `creative-journal` | 创作手记  | `#EFE9D9` | `#1F8A4C` | editorial-grid / hero-plus-grid | cut-the-curve | flap+tick | paper @ 92bpm | career, tech-deep, emotional |
| `daisy-soft` | 柔彩手账  | `#F5F0E6` | `#7ECDC0` | card-deck / centered-hero | rack-focus blur-cut | chime | soft @ 76bpm | baby, emotional, food |
| `biennale-artbook` | 艺术年鉴  | `#E9E5DB` | `#F1EE2E` | poster-full-bleed / hero-plus-grid | zoom-through | flap+chime | paper @ 88bpm | guofeng, movie, neutral |
| `ink-scroll` | 水墨卷轴  | `#F5EFE0` | `#A63B2A` | one-shot-world / poster-full-bleed | cut-the-curve | swipe+chime | soft @ 72bpm | guofeng |
| `speed-board` | 记分牌 🌙 | `#101418` | `#FFD400` | data-dashboard / banded-three | waterfall cut | thud+riser | pulse @ 124bpm | sports |
| `vault-gold` | 金库蓝 🌙 | `#0E1B2C` | `#C9A227` | data-dashboard / two-column-corridor | cut-the-curve | tick+thud | dry-tech @ 96bpm | finance |
| `night-cinema` | 夜场影院 🌙 | `#0D0D0F` | `#D4AF37` | poster-full-bleed / centered-hero | zoom-through | thud+riser | soft @ 70bpm | movie |
| `metal-spec` | 金属参数 🌙 | `#14161A` | `#FF6A00` | data-dashboard / one-shot-world | cut-the-curve | whoosh+thud | pulse @ 110bpm | auto |
| `cyber-hud` | 赛博 HUD 🌙 | `#0A0A14` | `#FF2E88` | data-dashboard / poster-full-bleed | waterfall cut | riser+thud | pulse @ 128bpm | gaming |
| `xiaozhe-mcp-node-graph` | 分层拓扑树 🌙 | `#050C0A` | `#4ADE80` | progressive-node-tree / numbered-sections | scale-through | tick+whoosh+chime | dry-tech @ 100bpm | tech-deep, career |
| `xiaozhe-rag-pipeline-flow` | RAG四层漏斗 | `#F7F6F2` | `#2563EB` | funnel-stage-filter / two-column-corridor | cut-the-curve | tick+thud+swipe | paper @ 94bpm | tech-deep, career, neutral |
| `chimp-deepseek-unit-economics` | 算力经济学 | `#FAF9F6` | `#2563EB` | gpu-matrix-ledger / data-dashboard | whip-x | tick+thud+whoosh | dry-tech @ 104bpm | tech-deep, finance, career |

## 题材 → 默认候选

| 题材 | 默认（浅底） |
|---|---|
| `tech-deep` | 纸感目录 / 研究笔记 / 代码编辑导览 / 宣言海报 / 蓝格索引 / RAG四层漏斗 / 算力经济学 |
| `tech-minimal` | 产品报告 / 克制图录 / 纸感目录 / 创作手记 |
| `finance` | 产品报告 / 研究笔记 / 克制图录 / 算力经济学 |
| `guofeng` | 水墨卷轴 / 艺术年鉴 / 克制图录 / 研究笔记 |
| `emotional` | 糖果几何 / 柔彩手账 / 创作手记 |
| `food` | 珊瑚强对比 / 糖果几何 / 柔彩手账 / 宣言海报 |
| `gaming` | 积木色块 / 珊瑚强对比 / 头版大字报 |
| `career` | 纸感目录 / 创作手记 / 产品报告 / 代码编辑导览 |
| `sports` | 头版大字报 / 积木色块 / 珊瑚强对比 |
| `news` | 头版大字报 / 纸感目录 / 珊瑚强对比 |
| `baby` | 糖果几何 / 柔彩手账 / 积木色块 |
| `auto` | 产品报告 / 克制图录 / 代码编辑导览 |
| `movie` | 艺术年鉴 / 珊瑚强对比 / 克制图录 |
| `neutral` | 纸感目录 / 克制图录 / 研究笔记 / 产品报告 |

## 四个轴

### look
_13 个 frame-preset 的真实调色板（全部为浅底）。preset 只定义原子，不定义构图与动效。_

- **biennale-yellow** — 艺术年鉴，纸张与印章 `#E9E5DB`
- **blockframe** — 积木色块，儿童积木/潮玩 `#FFFDF5`
- **blue-professional** — 产品报告，克莱因蓝压奶油纸 `#fdfae7`
- **bold-poster** — 印刷宣言，反科技制服 `#FFFFFF`
- **broadside** — 报刊头版，强冲击 `#F0ECE5`
- **capsule** — 糖果几何，圆角胶囊 `#F5F5F0`
- **cartesian** — 克制图录，低饱和 `#EDE8E0`
- **cobalt-grid** — 蓝格索引（浅纸上的蓝网格，不是深蓝底） `#F0EBDE`
- **code-editorial** — 代码编辑导览，近黑墨配奶油 `#FAF9F5`
- **coral** — 珊瑚强对比 `#F5F0E8`
- **creative-mode** — 创作手记，绿粉双强调 `#EFE9D9`
- **daisy-days** — 柔彩手账，多色低饱和 `#F5F0E6`
- **editorial-forest** — 研究笔记，森林绿配奶油纸 `#efe7d4`

### layout
_构图轴——13 个 preset 都没有覆盖这一轴，必须显式点名。取自 eccom METHOD §5 与参考片结构。registry 侧用 assets/layout-index.py 按此轴查现成块。_

- **hero-plus-grid** — 左/上 1 张主图 + 右/下 缩略图网格（当前项高亮描边）
- **numbered-sections** — 巨大两位序号 + 标题 + 一行说明，章节化
- **two-column-corridor** — 左栏候选 / 右栏结论 / 中间 ≥140px 走廊给收敛线
- **banded-three** — 顶部 tag+标题 / 中部主体 / 底部数据带，三段留 40–60px
- **one-shot-world** — 世界宽 = 站数 × 站宽，站间距 = 站宽，横移换站
- **poster-full-bleed** — 满版巨字 + 硬边分隔，不设安全边距
- **editorial-grid** — 多栏发丝线网格，内容按栏对齐
- **centered-hero** — 单件居中 + 大留白（仅 hero / lockup 镜）
- **card-deck** — 卡片扇形/堆叠/发牌，数量表达语义
- **data-dashboard** — 仪表盘式：指标块 + 趋势线 + 状态色
- **timeline-rail** — 竖线 + 刻痕，进度与内容合一（禁底部进度条）
- **split-compare** — 左右等分对比，仅用于 2 个真实对象
- **ui-stage** — 产品界面/设备居中成舞台，镜头绕它走（registry 里最多的一类）
- **code-panel** — 代码编辑器/终端/差异面板占主区，行级动画
- **progressive-node-tree** — 左上角章节编号胶囊 (`[01] 核心问题`) + 从左至右三次贝塞尔曲线分支节点树 + 右侧圆环痛点仪表盘 (`90% 容易混淆`) + 底部居中字幕条
- **funnel-stage-filter** — 四阶水平/漏斗流水线 + 角色拟人标签（超级实习生/短期便利贴/长期知识库）+ 顶部全流程进度轨 (`notch-rail-progress`)
- **gpu-matrix-ledger** — 左上角直给观点大标题 + 中央 GPU 算力砖块矩阵 + 巨型倍率算式 (`$38 vs $5.7 ≈ 6.7x`) + 左下角圆形讲者 PiP 锚点

### motion
_动效轴——每个条目点名 1 个 seam + 1 个镜内 route。数值配方见 METHOD §6（项目标定，换题材需重标）。_

- **zoom-through** — 推近穿过画面进入下一镜
- **inverse zoom-through** — 拉远退出，反向
- **cut-the-curve** — 两侧都在运动中切，partial travel ~12%
- **waterfall cut** — 错峰瀑布式切入
- **rack-focus blur-cut** — 焦外模糊切换
- **scale-through** — 焦点节点缩放穿场进入下一层拓扑
- **whip-x** — 横向高速甩镜切章
- **waterfall entry** — 群组错峰到达，stagger 0.12–0.18s
- **nudge curve** — 慢-快-慢三段位移
- **focus-spotlight** — 焦点节点放大高亮 (`scale: 1.08`) 同时非焦点分支自动降暗至 `opacity: 0.25`，SVG 连线脉冲流光
- **packet-hop-break** — 文档块沿轨道跳跃，错误切分时在节点碎裂为红色残片，经过 Rerank 漏斗时低分淘汰、高分汇入 Prompt 槽位
- **counter-seek-safe** — 巨型数字跳动 + GPU 网格逐列染色波浪 + 木桶效应短板阻塞条对比
- **分阶段揭示** — ≥2 组内容依次落位
- **有意图的镜头** — 一镜一个空间，镜头本身在走
- **界面自己的生命** — 步骤条点亮 / 光标点击 / 落库提示
- **动画序列** — 有因果的动作链（走→撞→变色）
- **光标驱动** — 超大光标从画外进入

## 知识讲解类标杆视频风格深度卡片（3 套新增）

### 1. `xiaozhe-mcp-node-graph`（小哲讲agent · MCP/Skill/本地Tools分层拓扑风）
- **polarity**: `dark`（已加入 `USER_APPROVED_DARK_STYLES` 白名单）
- **best_for**: `["agent architecture", "protocol vs skill vs tool taxonomy", "system topology explainer", "progressive node-graph"]`
- **look**: 画布背景 `#050C0A` → `#081614` 深黑曜石青绿微光，主字色 `#F8FAFC`，协议层薄荷绿 `#4ADE80`，方法层丁香紫 `#A78BFA`，执行层琥珀黄 `#FBBF24`，警示痛点珊瑚粉 `#FB7185`。
- **layout**: 左上角章节编号胶囊 (`[01] 核心问题`) + 从左至右三次贝塞尔曲线分支节点树 (`progressive-node-tree`) + 右侧圆环痛点仪表盘 (`90% 容易混淆`) + 底部居中字幕条。
- **motion**: 焦点节点放大高亮 (`scale: 1.08`) 同时非焦点分支自动降暗至 `opacity: 0.25`，SVG 连线脉冲流光，接缝采用 `scale-through` 与 `whip-x`。

### 2. `xiaozhe-rag-pipeline-flow`（小哲讲大模型 · 一条视频彻底吃透RAG四层漏斗风）
- **polarity**: `light`
- **best_for**: `["RAG pipeline explainer", "LLM data flow", "multi-stage funnel", "chunking recall rerank architecture"]`
- **look**: 暖白编辑室画布 `#F7F6F2`，卡片 `#FFFFFF` (`2px solid #0F172A`)，切片钴蓝 `#2563EB`，向量召回青色 `#0891B2`，重排琥珀橙 `#EA580C`，生成翠绿 `#16A34A`，幻觉碎片警示红 `#DC2626`。
- **layout**: 四阶水平/漏斗流水线 (`funnel-stage-filter` + `two-column-corridor`) + 角色拟人标签（超级实习生/短期便利贴/长期知识库）+ 顶部全流程进度轨 (`notch-rail-progress`)。
- **motion**: `packet-hop-break`（文档块沿轨道跳跃，错误切分时在节点碎裂为红色残片，经过 Rerank 漏斗时低分淘汰、高分汇入 Prompt 槽位）。

### 3. `chimp-deepseek-unit-economics`（第四种黑猩猩 · DeepSeek 单卡 $38 算力经济学风）
- **polarity**: `light`
- **best_for**: `["GPU unit economics", "AI infrastructure throughput", "quantitative token matrix", "financial & systems breakdown"]`
- **look**: 暖米白纸张背景 `#FAF9F6`，深墨黑标题 `#0F172A`，基准灰 `#94A3B8`，克莱因蓝 `#2563EB`，瓶颈活力橙 `#F97316`，命中率翡翠绿 `#10B981`，MoE 专家紫 `#8B5CF6`。
- **layout**: 左上角直给观点大标题（如 `先说 EP 和 DP`、`每一步，都得等最慢的那张卡算完`）+ 中央 GPU 算力砖块矩阵 (`gpu-matrix-ledger`) + 巨型倍率算式 (`$38 vs $5.7 ≈ 6.7x`, `60K / 1.5M 省了25倍`) + 左下角圆形讲者 PiP 锚点。
- **motion**: `counter-seek-safe` 巨型数字跳动 + GPU 网格逐列染色波浪 + 木桶效应短板阻塞条对比 + `whip-x` 高速切章。


### sound
_声音轴——sfx-gen.py 的 7 个 motif + bgm-gen.py 的 4 个编曲风格。BGM 同时产出拍点网格（audio/beat-grid.json），用 beat-snap.py 校验剪辑点。_

- **flap** — 翻牌 / 卡片落位
- **whoosh** — 镜头横扫 / 穿场
- **swipe** — 镜内群组滑移
- **tick** — 打字机 / 计数 / 索引推进
- **chime** — hub / 规则 / 定版
- **thud** — 撞击 / 到达
- **riser** — zoom 张力
- **paper** — 轻刷 + 暖 pad，鼓很退（86–96 BPM）→ 纸感/编辑类
- **dry-tech** — 干燥克制，鼓在 1/3，8 分 hat（96–104 BPM）→ 科技/报告类
- **pulse** — 四拍底鼓 + 2/4 拍手 + offbeat bass + arp（110–128 BPM）→ promo/游戏类
- **soft** — 无鼓，只有 pad 与偶发 chime（70–84 BPM）→ 情感/母婴/影院类
