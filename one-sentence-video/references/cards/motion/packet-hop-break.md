---
id: packet-hop-break
name_zh: 逐跳撞断点
category: motion
role: sequence
energy: 4
duration: 2.2
layouts: [banded-three]
seams: [waterfall cut]
sound: [tick, thud]
genres: [tech-deep, finance, neutral]
source: eccom METHOD §4.2（因果同帧：撞击与变色必须同一时间点）
verified: measured
---

## 意图
把"数据走到某处断了"变成一次可见的物理事件，而不是一句结论文字。

## 适用
有「断点 / 失败 / 阻断」因果的技术叙事；网络、链路、调用链排障。

## 时间表
```js
var PKT = [240, 590, 940, 1290];
for (var i = 1; i < PKT.length; i++)
  tl.to("#s5-pkt", { x: PKT[i]-PKT[0], duration: 0.22, ease: "power2.inOut" }, 0.60 + i*0.34);
tl.to("#s5-pkt", { x: 1454-PKT[0], duration: 0.20, ease: "power2.out" }, 1.66);   // 冲向断点
tl.to("#s5-pkt", { x: 1454-PKT[0]-26, duration: 0.18, ease: "power2.in" }, 1.92); // 撞回
tl.to("#s5-pkt", { backgroundColor: "#ff3b5c", duration: 0.14 }, 1.92);           // 同帧变色
```

## 因果同帧
撞击与变色**必须在同一时间点**（1.92）。晚 0.1s 就不像撞的，像"过一会儿变红了"。

## 参数表
| 参数 | 典型值 | 调节手感 |
|---|---|---|
| 每跳时长 | 0.22s | <0.15 看不清落点；>0.3 拖 |
| 跳间隔 | 0.34s | 与节拍对齐时用 1/2 拍 |
| 撞回距离 | 26px | <16 读不出「撞」；>40 读作弹开 |
| 变色时长 | 0.14s | 必须与撞击同帧（1.92） |
| 变色色值 | 强调色（如 `#ff3b5c`） | 不要用纯红，太刺 |

## HyperFrames 要点
- `backgroundColor` 可以 tween（是 GSAP 识别的 CSS 属性），但**不要**用它换文字（`textContent` 不被识别，静默失败）。
- 每一跳一个 tween 而非一个 clip；若跨镜，注意 track 不重叠。

## 声音
每跳 `tick`（gain .22），撞击 `thud`（gain .5）**与变色同帧**。

## 何时不用
- 没有"断点"这个因果：不要为了动效硬造一次撞击。
