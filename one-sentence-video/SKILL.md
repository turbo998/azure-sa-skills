---
name: one-sentence-video
description: |
  一句话做视频的默认入口（自包含，不依赖任何策划/选题/口播管道技能）。当用户用自然语言提出 HyperFrames 视频制作需求——"做个视频"、"做个短视频"、"把这个主题做成动画"、丢来一段文案/文章/数据要出画面、"改一下这个项目的风格"——且没有点名其他专用工作流时触发。技能自带完整制作链：需求收料与默认值 → 三幕分镜（视觉驱动，文字是卡片不是讲稿）→ 三方向样帧比选（用户拍板，禁止默认深蓝网格）→ HyperFrames registry 逐镜检索闸（能装不手写）→ 具名 seam 动效闸（cut-the-curve，禁 uniform fade+slide）→ Python SFX 声音设计 → check/draft 抽帧/density 证据链 → 复用浏览器渲染。小白零决策成本：缺信息最多问 3 个，其余自动并声明默认值；唯一强制用户决策 = 审美方向三选一。禁止跳过方向比选直接手写帧（那样会产出 PPT 式/深蓝网格 AI 制服视频）。
metadata:
  tags: video, hyperframes, beginner, autopilot, genre-style, registry, seam, direction-bakeoff, sfx, sound-design
---

# 一句话做视频（One-Sentence Video）

自包含的自动驾驶入口。**本技能不委托、不调用任何选题/策划类管道技能**；风格知识自带于 `references/style-map.md`，制作知识按需加载官方 HyperFrames 技能（那是平台本身，不是替代品）。

## 为什么是一个 skill，而不是拆成几个

**入口只留一个，能力靠 `references/` + `assets/` 分层加载。** 理由不是省事，是防漂移：

- **拆分会让风格真值源分裂，且已经分裂过**：本机曾同时存在三份风格真值源（本技能的 `style-map.md`、
  `short-video-pipeline/references/genre-style-map.md`、`tech-explainer-video/SKILL.md` 的色义表），
  同一组 Neon Pulse 色值（`#0a0a1a` `#00f0ff` `#ff006e`）在三处各写了一遍，改一处另两处不动。
  现在收敛为 **`references/style-ledger.json` 单一真值源**。
- **拆分的唯一合法理由是「触发语境不同」，不是「能力不同」**：制作（从零/改项目）是同一语境，不拆。
  P4「逆向真实产品片拆卡」是**离线生产流程**（产物是卡，不是视频），触发语境不同，将来可独立成 skill。
- **闸门脚本不占上下文**：`assets/*.py` 按需执行，不会因为留在同一技能里而变贵。
- **技能是靠 description 匹配触发的**：多个近义入口会互相抢触发、且用户要记更多名字——
  这正是"技能很多但没体系"的来源。

## 总原则

- **自动起飞**：默认不反问。题材/画幅/配音三项缺到无法开工才问，一次问完（≤3 个）。
- **方向必须用户拍板**：审美方向是本技能唯一强制用户决策——Step 3 出 3 个气质迥异的方向样帧，用户选完才继续。小白不做技术决策，但必须选审美。
- **视觉驱动**：信息由画面承载，文字是精炼卡片。**文字预算按元素分档**（不是统一 12 字）：标题 4–8 字 / 副句 ≤10 字 / 标签 ≤6 字 / 说明段 **0 字**。判据：1.5s 读不完的不是文案，是纹理。用户没给口播文案就不要自动生成口播——那会把视频做成 PPT 念稿。
- **能装不手写**：具名视觉（转场/背景/标题效果/图表/纹理）动手前先查 registry；装得进就用最大可装单元，手写必须写明为何无命中。
- **一镜一具名 seam**：动效必须像一台连续摄像机；每个镜头边界必须落到 `cut-the-curve` 的具名 seam（或 in-scene waterfall/nudge），禁止 uniform fade+slide。

## 默认值（缺省即采用，交付时在摘要里声明）

| 项 | 默认 |
|---|---|
| 画幅 | **1920×1080 横屏** 30fps（用户明确说竖屏/抖音/短视频平台才改 1080×1920） |
| 时长 | 20–30s，5–7 镜 |
| 配音 | 关（字幕卡承载信息）；用户贴了口播稿或明说要配音才开 |
| BGM | 开（`/media-use` 选免费曲，节奏匹配题材 motion） |
| 平台 | 横屏默认 90% action-safe / 80% title-safe；竖屏才用竖屏安全区 |

## 流程（每步过闸，产物落盘到项目目录）

### Step 0 · 收料

解析用户输入为：主题（必须有）/ 文案（可选）/ 画幅时长（可选）/ 素材（可选图/视频/logo）。写三行「立项卡」回复用户（题材判定 + 所用默认值 + 一句话视觉概念），不问继续。

### Step 1 · 立项

- 在 `videos/<项目>/` 内 → 就地开工。
- 在 hyper-video 容器根 → `npm run new-project -- <video-id>` 后进入项目目录。
- 容器外全新目录 → `npx hyperframes init <dir> --example blank --resolution landscape --non-interactive`。

### Step 2 · 分镜（视觉驱动，官方 STORYBOARD 格式）

写 `STORYBOARD.md`（frontmatter: format/duration/mode: autonomous/music），每镜一节，四要素必填：

```
## NN-<kebab名>  [t0–t1s]
card: <卡片 id>            ← 优先：references/cards 里的实测配方
blueprint: <蓝图名>        ← 没有卡时才用 hyperframes-animation 蓝图
framing: 构图与坐标（禁与相邻镜同构图；centered 仅限 hero/lockup）
scenes: 时间码窗口 → 内容进场拍点（内容铺满后 50%，不许 front-load）
motion_verb: 这一镜用哪个动词改变画面（不是"淡入"）
handoff_out / handoff_in: 数值边界（元素、坐标、scale、opacity、方向）
```

节奏骨架：**钩子镜 0–3s 必须有冲击**，中段每镜一个 motion verb，收尾定版。纯图形运动占至少 2 镜；转场镜中央必须有驻留主体。Step 4 会为每镜补 `registry:` 行、Step 5 会补 `motion:` 行——两行缺一不许写帧。

**先查卡，再编蓝图**：

```bash
python3 ~/.claude/skills/one-sentence-video/assets/card-index.py --genre <题材>      # 该题材可用的卡
python3 ~/.claude/skills/one-sentence-video/assets/card-index.py --layout <构型>     # 按构图查
python3 ~/.claude/skills/one-sentence-video/assets/card-index.py --energy-plan 7    # 排能量曲线
```

卡是**施工图**（实测数值 + 时间表 + 何时不用）；蓝图是**素材**。有卡照抄数值，没卡才从蓝图编。
`--energy-plan` 会保证不出现连续三镜同能量、钩子镜 ≥4、收尾镜 ≤2。

### Step 3 · 方向比选（写帧前强制闸门；本技能唯一强制用户决策）

**缺陷背景**：上一版把题材直接映射到第一个 preset（code-editorial 深蓝+网格=科技片 AI 味制服），没有候选→对比→拍板。本版禁止"命中即套第一个"。

**风格真值源 = `references/style-ledger.json`（四轴账本），不是模型记忆，也不是 style-map 的配色表。**

1. **查候选（不是选一个）**：按题材查账本，拿 3–5 条**浅底**候选。

   ```bash
   python3 ~/.claude/skills/one-sentence-video/assets/style-query.py --genre <题材>
   # 需要深色备选才加 --dark（深色条目一律需用户拍板）
   # 也可按构图/动效/声音反查：--layout hero-plus-grid / --motion cut-the-curve / --sound tick
   ```

   每条候选自带：`atoms`（真实 preset 色值）/ `layouts`（构图轴）/ `motion`（seam + route）/ `sound`（motif）/ `mood` / `cost`。
   **`tech-deep` 是题材标签，不是预设；科技题材默认全部浅底。** 深蓝霓虹（`#0B1020`/`#38E1FF`/`#0a0a1a`/`#00f0ff`）是历史 Neon Pulse 残留，已从账本默认列表移除，只保留 `cyber-hud`（gaming）一条且必须用户拍板。

2. **出 3 个方向样帧（真图，不是文字描述）**：每个方向用所选条目的 atoms（配色/字体/构图/组件）套本片真实文案，做一个 1920×1080 静态 HTML 样帧，渲染成 PNG。四条硬规则：
   - **气质必须迥异**：三个方向至少在「底色（米纸/纯白/深色/饱和色）」「字体声音（衬线/无衬线/展示体）」「构图（编辑网格/满版海报/居中极简）」三个轴中的两个轴上不同；三个都换汤不换药 = 无效比选。
   - **禁止默认深蓝+网格+霓虹青**：科技/AI 题材默认候选全是浅底；要深色必须用户明确点。至少 2 个方向是浅底，至少 1 个方向不得使用网格/玻璃态/发光粒子。
   - **样帧要能看出全片语言**：每张样帧除主标题外，至少带 1 个该方向的组件（卡/条/章/图表/边框）和 1 个次级信息，不能只放一行大字。
   - 样帧是**静态气质图**，不需要动效；但必须用本片真实文案，不许用 lorem ipsum。

3. **落盘**：`output/directions/{A,B,C}-<slug>.png` + `output/directions/README.md`（方向名 / style-id / 一句话气质 / 适合的理由 / 代价）。

4. **给用户选**：把三张图并排贴给用户（附一句话气质与代价），问「选 A / B / C（或指定混搭）」。**未收到明确选择，不许进入 Step 4**。用户说「都行/你定」→ 复述三个方向的气质差异再让他选；仍不选则默认选**与上一版差异最大**的方向并声明，但必须给出图。

5. **决策入档**：`design-spec.md` 必须写 `palette_source: <style-id>`（调色板溯源的唯一凭据，`palette-audit.py` 会校验），并增加「方向决策记录」：候选 A/B/C、用户选择、落选理由、style-id。然后才 `build-frame.mjs --preset <chosen>` 生成 frame.md 并拷字体。`design-spec.md` 还需落：风格定位声明 / token 引用 frame.md / BANNED 清单（uniform fade+slide 全家、back.out 过冲、居中滥用限 hero/lockup 镜、深蓝网格制服）。

闸门：`process-gate.py --stage direction` 必须 PASS（3 张 1920×1080 PNG + README + design-spec 方向决策记录），
且 `palette-audit.py` 必须 PASS（`palette_source` 存在、id 在账本里、深色条目有拍板记录）。缺一不许写帧。

**参考三方向（科技/AI 题材，仅示例，不照抄）**：
- A 宣言海报 → `bold-poster`：白底 / 番茄红 / 黑；倾斜巨字 + 双线框 + 左红条卡。气质：印刷宣言，反科技制服。
- B 研究笔记 → `editorial-forest`：奶油纸 / 森林绿 / 粉；衬线大标题 + 等宽 chrome + 细发丝线。气质：杂志/论文，冷静可信。
- C 大字报 → `broadside`：墨黑 / 火焰橙 / 米白；900 粗体巨字 + 等宽 chrome + 硬边分隔。气质：报刊头版，强冲击（深色但不是深蓝、无网格）。

### Step 4 · 逐镜 registry 布局闸（能装不手写）

**每一镜写 HTML 前先过这一闸；没有台账行 = 不许写帧。**

**先按构图查，再按功能查。** registry 自带的 tags 是**功能轴**（transition / typography / reveal），
没有**构图轴**；只按功能找块，找出来的块构图随机 → 每镜构图一样（这正是"平"的成因之一）。

1. 逐镜从 STORYBOARD 提取「这一镜要做的视觉/运动」，翻成英文关键词（layout / transition / kinetic type / chart / camera / overlay / title card…）。
2. **先查构图轴**（本片 style 已经指定了 layouts，直接问它有哪些现成块）：

   ```bash
   python3 ~/.claude/skills/one-sentence-video/assets/layout-index.py --style <style-id>
   # 或单查一个构型：--layout numbered-sections
   # 覆盖报告：--report（角色分布 + 每个构型有多少块）
   ```

   索引把 196 个横屏块先按**角色**分开：`background 49 / transition 32 / caption 14 / object 18 / layout 83`。
   **别把背景块当布局用，别把转场块塞进镜内。** layout 角色里 68% 已按 14 个构型分好。
   构型空 → 这个构型没有现成块（例：`numbered-sections` 目前 0 块），必须手写并在台账写明。
3. **再查功能轴**。本机 pin 的 CLI 是 `0.7.87`：**没有 `catalog --query`、没有 `--on-device`**（旧文档里的这两个参数会直接报 Unknown flag）。正确做法是拉全量 JSON 再本地过滤：

   ```bash
   npx hyperframes catalog --json > output/catalog.json
   python3 ~/.claude/skills/one-sentence-video/assets/catalog-search.py output/catalog.json "<英文关键词>" --type block
   ```

   也可用 `npx hyperframes catalog --tag transition --json` / `--type component`。
4. 命中 → 装进项目（**外网必须带代理前缀**，先 `lsof -iTCP:7897 -sTCP:LISTEN` 确认 Clash 在跑）：

   ```bash
   NODE_USE_ENV_PROXY=1 HTTPS_PROXY=http://127.0.0.1:7897 HTTP_PROXY=http://127.0.0.1:7897 \
     npx hyperframes add <name> --json
   ```

   用**最大可装单元**（整块 > 组件 > 手写）。装完只改配色/字体/文案变量，不改它的几何与时间签名；id 保留前缀，防两个块撞 id。
5. 未命中 → 先如实报告并回报：
   `npx hyperframes feedback --search-miss "<query>" --wanted "<想要的效果>"`，然后才手写；台账写明「为何无命中」。
6. **台账落盘** `output/registry-ledger.md`，每镜一行：

   `| 镜 | 构图 | 英文 query | 命中(名称/role/时长/尺寸) | 采用(装块/组件/手写) | 挂载或手写理由 |`

   闸门：台账数据行数 = 分镜镜数；任一镜缺行 → 回 Step 2 补，不许写帧。
7. 横屏片只装 1920×1080 或可裁的块；竖屏/方形块必须改造并写明改造点。

闸门：`python3 ~/.claude/skills/one-sentence-video/assets/process-gate.py "$PWD" --stage layout` 必须 PASS。

### Step 5 · 写帧（先加载知识；每镜动效落到具名 seam）

用 skill 工具依次加载：`hyperframes-core`（data-* 契约）→ `motion-doctrine`（矢量法则/禁原地抖动）→ `cut-the-curve`（五个具名 seam + waterfall entry + nudge curve）→ `hyperframes-animation`（每镜挑 1 blueprint + 2–4 条规则组装）。写完 STORYBOARD 后先生成帧 packets 当施工图（每节需 `- src: compositions/frames/NN-*.html` 行）：

```bash
node ~/.agents/skills/product-launch-video/scripts/frame-packets.mjs --project "$PWD" --storyboard STORYBOARD.md
```

官方链要求"每帧一个 worker"时，**本机一律降级为主线程串行**：逐帧自己写、逐帧自验，不派子智能体（用户规则优先）。

**动效签名闸（每镜必须落到具名 seam，不许挂 blueprint 名却执行 uniform fade+slide）：**

- 镜头边界有剪切/转场 → 从 `cut-the-curve` 五个具名 seam 中选一个：`zoom-through`、`inverse zoom-through`、`cut-the-curve`、`waterfall cut`、`rack-focus blur-cut`，并写清速度匹配的 ease 对（如 `power4.in` ↔ `power4.out`）与 ~12% 的 partial travel。
- 镜内群组/标题卡 → 用 in-scene 技术：`waterfall entry`（错峰到达）或 `nudge curve`（慢-快-慢三段位移）。
- 每镜在 STORYBOARD 追加一行：
  `motion: seam=<具名> | velocity=<ease 对> | carrier=<驻留主体> | verb=<一个动词>`
- **禁词清单（写帧与自查都扫）**：uniform fade+slide、所有元素同时 fade-in、全片同一个 `power3.out` 默认、每镜同一个 crossfade、三张等宽等高卡片并排、`back.out(1.7)` 默认过冲、idle wobble / 呼吸充数、只有淡入没有方向/遮罩/缩放、深蓝底+青色网格制服。
- 闸门：每镜都有 `motion:` 行且 seam 名在白名单内；缺行 = 不许写帧。

**渲染器实测铁律（违者内容永久黑屏，成片抽帧才能发现）：**

1. **GSAP 只动 clip 本体，永不动 clip 的子元素**——框架管理 clip 及其子树可见性，对子 span 的 tween 不会执行。逐词动画 → 每个词自成一个平铺 clip（同 y、独立 track、独立时间窗）。
2. **禁 `tl.set(el, {textContent/innerText})` 换字**——GSAP 不识别该键，静默失败。同位换词 = 前后两个 clip 硬切接力（窗 A 尾即窗 B 头）。
3. **clip 不能嵌套 clip**——分组容器要动画就降为普通 div（无 clip），内容切换靠平铺兄弟 clip。
4. 一帧内每个 clip 独立 `data-track-index`，同 track 时间不得重叠；某元素的退场 tween 终点必须避开任何 clip 的 start 边界（差 ≥0.05s）。
5. 前景内容留到后 50% 拍点进场；转场瞬间画面中央必须有稳定主体驻留（不许在 crossfade 里空屏）。
6. 打字机/计数用 `onUpdate` 按时间确定性赋值，禁 `tl.call` 改 DOM；闪烁用离散 `tl.set`；禁 `Date.now()`/未播种随机/`repeat:-1`。
7. 中文字体：系统内置（PingFang SC / Songti SC 等）`local()` 声明即可（制作机=渲染机）；拉丁 display 字体优先 preset 的 woff2 落 `assets/fonts/`，下载失败时回退到本机内置字体并在 design-spec 记偏差。
8. **子组合的 CSS 必须写在 `<template>` 内，不能写在 `<head>`**——框架克隆的是 `<template>` 的内容，`<head>` 里的 `<style>` 会被丢掉。症状极具迷惑性：**页面不报错、check 也不报错，但 `.safe` 之类的外层定位全部失效，文字贴着画布边缘排**。自己画的帧一律把 CSS 放进 template。

### Step 5.5 · 声音设计（BGM 代码编曲 + 拍点吸附 + Python 合成 SFX；默认开）

声音分三层，**顺序不能反**：先定 BGM 与拍点 → 再用拍点定镜头边界 → 最后补 SFX。

#### ① BGM + 拍点网格

BGM 用技能自带合成器**代码编曲**（不下载、不调 API），风格取自账本条目的 `sound.bgm`：

```bash
python3 ~/.claude/skills/one-sentence-video/assets/bgm-gen.py \
  --style paper --bpm 86 --duration 26 --out audio/bgm.wav
# → audio/bgm.wav + audio/beat-grid.json（BPM/拍/强拍/8分/小节）
```

四个编曲风格：`paper`（轻刷+暖 pad，86–96）/ `dry-tech`（干燥克制，96–104）/
`pulse`（四拍+arp，110–128）/ `soft`（无鼓只有 pad，70–84）。
有 `pedalboard` 时自动做母带（EQ+压缩+限幅），没有则退回软削并打印 `master=tanh`。
技术选型与实测边界见 `references/audio-stack.md`。

#### ② 拍点吸附（镜头边界必须落在拍上）

```bash
# 反推：给 N 镜，输出对齐拍点的边界
python3 ~/.claude/skills/one-sentence-video/assets/beat-snap.py --grid audio/beat-grid.json --plan 7
# 校验：已有剪辑点是否在拍上（容差 ±50ms ≈ 1.5 帧）
python3 ~/.claude/skills/one-sentence-video/assets/beat-snap.py --grid audio/beat-grid.json --storyboard STORYBOARD.md
```

容差外**不硬吸**——报 MISS 并在 design-spec 写明"这一刀刻意不在拍上"，不许悄悄改坏分镜节奏。

#### ③ SFX（事件级）

默认给 motion/promo 加**干燥、机械/模拟**的 SFX，与画面拍点**同帧**。先写事件图，再落 WAV：

```bash
python3 ~/.claude/skills/one-sentence-video/assets/sfx-gen.py --events audio/sfx-events.json --out audio/sfx.wav
```

`audio/sfx-events.json` schema：`{duration, events:[{t, type, gain, pan, pan_end?, dur?}]}`。每镜在 STORYBOARD 追加一行：

`sound: motif=<flap|whoosh|swipe|tick|chime|thud|riser> | cues=<绝对时间/事件> | mix=<dry/…>`

**音色法则**：
- 每个 motif 必须因果：翻牌→`flap`、打字机/计数→`tick`、hub/规则/定版→`chime`、撞击/到达→`thud`、镜头横扫→`whoosh`、镜内群组滑移→`swipe`、zoom 张力→`riser`。
- seam 声随电影 current 同向 pan（LEFT 片 → `whoosh`/`swipe` 从右往左）；**禁止每刀同一个 whoosh**，禁止无因果环境垫，禁止用音乐冒充音效。
- 事件必须落在真实拍点（cut、title swap、stamp、node reveal、lockup），不铺满整条时间线。

在 `index.html` 根层（与 scenes 同级）加：

```html
<audio id="sfx" src="audio/sfx.wav" data-start="0" data-duration="26" data-track-index="10" data-volume="0.8"></audio>
```

规则：必须有 `id`；**不要** `class="clip"`（音频无视觉）；不要 `crossorigin`；音频 track index 独立于视觉（10+）。`process-gate.py --stage all` 会检查每镜 `sound:` 行、事件图、WAV 和这个 audio 元素；缺一 BLOCK。

### Step 6 · 验证与交付（证据链 = draft 渲染抽帧，不是 snapshot）

先跑过程闸，再跑机器闸：

```bash
python3 ~/.claude/skills/one-sentence-video/assets/process-gate.py "$PWD" --stage all     # 方向/布局/动效/声音四闸
npm run check                                         # 全绿（有 Fix 逐条修；clip 铁律违规全在这层显形）

# 主时间线：index.html 手写或 assemble-index 生成，每个镜头包装器必须有
# id / class="scene" / data-composition-id / data-composition-src / data-start / data-duration，
# 并注册 `var tl = gsap.timeline({paused:true}); window.__timelines["main"] = tl;`
# 然后写 ledger.json（每条 seam 的 cut/technique/exit/entry，与 STORYBOARD 的 motion: seam= 对齐），
# 由 seam-stamp 生成 partial travel + 速度匹配，不许手写 uniform fade+crossfade。
node ~/.agents/skills/motion-doctrine/scripts/seam-stamp.mjs --ledger ledger.json --write index.html
node ~/.agents/skills/motion-doctrine/scripts/seam-gate.mjs verify --ledger ledger.json --project "$PWD"
export HYPERFRAMES_BROWSER_PATH="$(ls -d $HOME/.cache/puppeteer/chrome-headless-shell/*/chrome-headless-shell-mac-arm64/chrome-headless-shell 2>/dev/null | sort -V | tail -1)"
npx hyperframes render --quality draft --output renders/draft-check.mp4
mkdir -p /tmp/dv && ffmpeg -y -v error -i renders/draft-check.mp4 -vf fps=2 /tmp/dv/f%03d.png
python3 ~/.claude/skills/one-sentence-video/assets/density-gate.py "$PWD" --strict-safe   # 「平」检测器（六判据）
#   死区（≥4 格空 ≥2s）/ 结构变化（间隔 >4s）/ 冻结（>30%）/ 缓动指纹（单一 ease >70%、back.out >2）
#   / 构图重复 / 安全区越界（--strict-safe 时算 FAIL）
#   基准与阈值见 references/quality-benchmarks.md
ffprobe -v error -show_entries stream=codec_type -of csv=p=0 renders/draft-check.mp4 | grep -q '^audio$'   # 必须有音轨
```

- **`snapshot --review` 对子组合是静态基线假图（内容不出）**——唯一权威证据是 draft 渲染 + ffmpeg 抽帧，逐帧眼看。
- 抽帧后逐帧自查三问，任何一问不过 → 回 Step 2/5 修订：① 像片还是像 PPT？② 风格统一、accent 克制？③ 0–3s 有冲击？另加像素硬检：每 0.5s 一帧，**任何一帧文字区亮像素为 0 = 黑屏 bug（GSAP 多半死在半路）→ 二分定位**。
- 再扫禁词清单：若任一镜是 uniform fade+slide / 全片一个转场 / 深蓝网格制服 → 回 Step 5，不许只改配色糊弄。
- check 的 content_overlap/contrast 报修必须真修（挪位置/提 alpha），不许加 allow-overlap 标签糊弄。
- **声音**：draft 渲染日志必须打出 `hasAudio:true`；`ffprobe` 必须有 audio stream；音量 mean ≈ −25 dB、max ≈ −3 dB，无削波。缺音轨 = BLOCK，不许只交无声片。
- **拍点**：有 BGM 时必须跑 `beat-snap.py --grid audio/beat-grid.json --storyboard STORYBOARD.md`。
  全部 OK 才算过；有 MISS 要么改镜头时长，要么在 design-spec 写明「刻意不在拍上」的理由——
  **不许静默忽略**。
- **给用户看抽帧拼图/关键帧 + SFX 波形，用户点头后才 high 渲染**。用户说"还是不行" = 技能没修好，回去改 SKILL.md 或流程条款，不许只补视频。

过了再高质量渲染（同一浏览器复用 env）：

```bash
npx hyperframes render --quality high --output renders/video.mp4
```

交付摘要一行：`题材=X 风格=Y（方向=A/B/C） 默认值=[横屏/20-30s/无配音/SFX=Python 合成/BGM=曲名] registry块=[…] seam=[…] 校验=通过`。

## 反问上限（超出场景一律默认执行）

1. 题材关键词完全无法命中 style-map
2. 画幅/时长会显著改变方案且用户未提
3. 需要 33MB 语义索引或下载字体征求同意（可合并进其他问题）

> Step 3 的方向三选一**不计入**反问上限——它是强制审美决策，必须问。

## 边界

- 不绑定任何选题/热点/口播策划技能；本技能是**制作**入口，收料即开工。
- 修改既有项目同样走本技能 Step 3–6（风格 token 从项目现有 design-spec.md 读起；若已有方向决策记录则沿用，不重复比选）。
- 机器闸门只保结构一致与反呆板底线；观感最终由用户拍板——preview/抽帧 + SFX 波形必给用户看。
- 默认无配音但有 Python 合成 SFX；用户明确说“不要声音”才关闭 SFX。
