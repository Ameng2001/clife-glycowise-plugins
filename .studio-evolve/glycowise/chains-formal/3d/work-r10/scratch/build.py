#!/usr/bin/env python3
"""按 spec.py 建沙箱、出补丁、dry-run、py_compile。用法：build.py [提案名 …]（缺省全部）"""
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parent                                   # chains-formal/3d/work-r10
STATE = WORK.parent / "state"                        # 本链状态（plugins/ 的上一级）
SRC = STATE / "plugins" / "glycowise"
OUT = WORK.parent / "attribution" / "round-10"
sys.path.insert(0, str(HERE))
from spec import PROPOSALS  # noqa: E402

names = sys.argv[1:] or list(PROPOSALS)
OUT.mkdir(parents=True, exist_ok=True)
for name in names:
    edits = PROPOSALS[name]
    sb = WORK / "sb" / name / "plugins" / "glycowise"
    if sb.parent.parent.exists():
        shutil.rmtree(sb.parent.parent)
    shutil.copytree(SRC, sb, ignore=shutil.ignore_patterns("__pycache__"))
    touched = []
    for fn, old, new in edits:
        p = sb / fn
        txt = p.read_text(encoding="utf-8")
        n = txt.count(old)
        assert n == 1, f"{name}: {fn} 原文片段出现 {n} 次"
        p.write_text(txt.replace(old, new), encoding="utf-8")
        if fn not in touched:
            touched.append(fn)
    patch = ""
    for fn in sorted(touched):
        r = subprocess.run(["diff", "-u", "--label", f"a/plugins/glycowise/{fn}", "--label", f"b/plugins/glycowise/{fn}",
                            str(SRC / fn), str(sb / fn)], capture_output=True, text=True)
        assert r.returncode == 1, (name, fn, r.stderr)
        patch += r.stdout
    pf = OUT / f"{name}.patch"
    pf.write_text(patch, encoding="utf-8")
    dry = subprocess.run(["patch", "-p1", "--dry-run", "-d", str(STATE), "-i", str(pf)], capture_output=True, text=True)
    comp = subprocess.run([sys.executable, "-m", "py_compile", *[str(sb / fn) for fn in touched]], capture_output=True, text=True)
    lines = [l for l in patch.splitlines() if l[:1] in "+-" and not l.startswith(("+++", "---"))]
    add = sum(1 for l in lines if l.startswith("+"))
    rm = len(lines) - add
    print(f"{name}\tfiles={','.join(touched)}\t+{add}/-{rm}\tdry-run={'OK' if dry.returncode == 0 else 'FAIL ' + dry.stdout + dry.stderr}\tcompile={'OK' if comp.returncode == 0 else 'FAIL ' + comp.stderr}")
    for d in sb.rglob("__pycache__"):
        shutil.rmtree(d)
