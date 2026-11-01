#!/usr/bin/env python3
"""调色板溯源闸：深色底与霓虹强调必须「有出处、有拍板」，不能是模型默认。

用法:
    python3 palette-audit.py <project-dir> [--json]

判据（三条，任一不满足即 BLOCK）:
  1. design-spec.md 必须有 `palette_source: <style-id>`，且该 id 存在于 style-ledger.json。
  2. 若声明的是 dark 条目（ledger 里 dark:true），design-spec 必须同时有用户拍板记录
     （「方向决策记录」里出现该 id 或「用户选择」字样）。
  3. 帧文件/design-spec 里出现的深底或霓虹色值，必须能在所选条目的 atoms 里找到；
     否则视为「凭空引入的历史 Neon Pulse 残留」。

退出码 0 = PASS，1 = BLOCK。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

LEDGER = Path(__file__).resolve().parent.parent / "references" / "style-ledger.json"

HEX = re.compile(r"#[0-9a-fA-F]{6}\b")
BG_DECL = re.compile(r"(?:--bg|background(?:-color)?)\s*[:=]\s*[^;\"']*?(#[0-9a-fA-F]{6})", re.I)


def load_ledger() -> dict:
    with open(LEDGER, encoding="utf-8") as fh:
        return json.load(fh)


def declared_style(spec: str) -> str | None:
    m = re.search(r"(?m)^\s*(?:-\s*)?palette_source:\s*`?([a-z0-9-]+)`?", spec)
    return m.group(1) if m else None


def user_choice_recorded(spec: str, style_id: str) -> bool:
    if "方向决策记录" not in spec:
        return False
    block = spec.split("方向决策记录", 1)[1][:1500]
    return bool(re.search(re.escape(style_id), block)) or bool(
        re.search(r"用户(?:选择|拍板|选定)|chosen", block, re.I)
    )


def audit(project: Path) -> tuple[list[str], list[str]]:
    """Return (fails, notes)."""
    fails: list[str] = []
    notes: list[str] = []
    ledger = load_ledger()
    styles = {s["id"]: s for s in ledger["styles"]}

    spec_path = project / "design-spec.md"
    spec = spec_path.read_text(encoding="utf-8") if spec_path.exists() else ""
    if not spec:
        fails.append("design-spec.md 缺失，无法溯源调色板")
        return fails, notes

    sid = declared_style(spec)
    if not sid:
        fails.append(
            "design-spec.md 缺 `palette_source: <style-id>`（调色板必须能溯源到 style-ledger 条目）"
        )
        return fails, notes
    if sid not in styles:
        fails.append(f"palette_source: {sid} 不在 style-ledger.json 里（可用 id 见 --list）")
        return fails, notes

    entry = styles[sid]
    atoms = entry["atoms"]
    allowed = {v.lower() for v in atoms.values() if isinstance(v, str) and v.startswith("#")}
    notes.append(f"palette_source={sid} dark={atoms.get('dark', False)} atoms={sorted(allowed)}")

    if atoms.get("dark"):
        if not user_choice_recorded(spec, sid):
            fails.append(
                f"{sid} 是深色条目（bg {atoms.get('bg')}），design-spec 的「方向决策记录」里没有用户拍板记录"
            )

    # 收集实际用到的色值
    files = [spec_path]
    for pat in ("compositions/**/*.html", "index.html", "compositions/**/*.css"):
        files += list(project.glob(pat))
    used: dict[str, list[str]] = {}
    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
        except Exception:
            continue
        for hexv in HEX.findall(text):
            used.setdefault(hexv.lower(), []).append(f.name)

    banned_bg = {c.lower() for c in ledger["banned_palettes"]["dark_bg"]}
    banned_neon = {c.lower() for c in ledger["banned_palettes"]["neon_accent"]}

    # 霓虹只对 gaming 的 cyber-hud 开放
    neon_ok = sid == "cyber-hud"
    for hexv, where in sorted(used.items()):
        if hexv in banned_bg and hexv not in allowed:
            fails.append(
                f"深底 {hexv} 出现在 {','.join(sorted(set(where))[:3])}，但不在 {sid} 的 atoms 里"
                "（历史 Neon Pulse 残留）"
            )
        if hexv in banned_neon and not neon_ok:
            fails.append(
                f"霓虹色 {hexv} 出现在 {','.join(sorted(set(where))[:3])}，但所选条目是 {sid}；"
                "霓虹只允许 cyber-hud（gaming）"
            )
    return fails, notes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    project = Path(args.project).resolve()
    if not project.is_dir():
        print(f"BLOCK: project not found: {project}")
        return 1
    fails, notes = audit(project)
    if args.json:
        print(json.dumps({"ok": not fails, "fails": fails, "notes": notes}, ensure_ascii=False))
    else:
        if fails:
            print("GATE: BLOCK")
            for f in fails:
                print("  ✗", f)
        else:
            print("GATE: PASS (palette)")
        for n in notes:
            print("  ·", n)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
