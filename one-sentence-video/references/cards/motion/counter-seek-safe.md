---
id: counter-seek-safe
name_zh: seek 安全计数器
category: motion
role: data
energy: 2
duration: 1.3
layouts: [data-dashboard]
seams: [waterfall entry]
sound: [tick]
genres: [finance, sports, news, tech-deep]
source: eccom METHOD §4.1（赋值而非累加）
verified: measured
---

## 意图
数字滚动。听起来简单，但这是最容易在渲染时变成乱码/黑屏的一类动画。

## 适用
任何数字滚动：倒计时、统计值、比分、百分比、金额。

## 写法（唯一正确形态）
```js
var clock = { p: 0 };                     // 代理对象，不要累加 DOM
var START = 58*60+42, END = 60*60;
function fmt(s){ /* 纯函数 */ }
tl.to(clock, {
  p: 1, duration: 1.30, ease: "power1.in",
  onUpdate: function () {
    var el = document.getElementById("s2-digits");
    if (!el) return;                      // 回调里查 DOM，IIFE 时元素可能还没插入
    el.textContent = fmt(START + (END - START) * clock.p);
  }
}, 3.60);
```

## 三条铁律
1. **赋值而非累加**——任意时间 seek 都能算出正确状态。
2. **回调里查 DOM**——IIFE 执行时元素可能还没进 DOM，外层变量会是 null。
3. **禁 `tl.call` 改 DOM**——每次 seek 都会重新执行，导致字符反复追加。

## 构图
- 数字单行、等宽字体（Menlo / JetBrains Mono），右对齐或居中
- 单位（%、s、万）小一号，跟在数字后
- 数字容器不要是 clip 的子元素

## 时间表
| t | 动作 |
|---|---|
| 0.00 | 数字从 START 起滚，1.30s，`power1.in` |
| 1.30 | 停在 END，容器 `scale 1.04→1` 落定 0.18s |
| 1.48 | 单位与标签淡入 |

## 参数表
| 参数 | 典型值 | 调节手感 |
|---|---|---|
| 滚动时长 | 1.0–1.6s | <0.8 看不清变化；>2.0 观众等得焦躁 |
| ease | `power1.in` | 用 out 会「先快后慢」，数字读起来像刹车 |
| 字体 | Menlo / JetBrains Mono | 非等宽会让整行宽度跳动 |
| tick 频率 | 每 3 个数字 | 每个数字一声 = 电钻 |

## HyperFrames 要点
- 数字容器不要是 clip 的子元素（clip 子树不可 tween）；把 clip 加在容器外层。
- 等宽字体（Menlo / JetBrains Mono），否则数字宽度变化会让整行跳动。

## 声音
`tick` 每 3 个数字一次，**不要每个数字一声**（会变成电钻）。

## 何时不用
- 数字本身不是信息（只是装饰）：不要滚。
