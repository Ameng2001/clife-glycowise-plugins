#!/usr/bin/env python3
"""对比 fallout-h10.jsonl 与 fallout-<提案>.jsonl：按 (case, variant) 列 pass 翻转与 actual 变化（不含 holdout-10 / targeted-W53）。"""
import json
import sys
from pathlib import Path

WK = Path(__file__).resolve().parent.parent


def load(p):
    return {(r["case"], r["variant"]): r for r in map(json.loads, open(p, encoding="utf-8"))}


base = load(WK / "fallout-h10.jsonl")
for name in sys.argv[1:]:
    new = load(WK / f"fallout-{name}.jsonl")
    up = sorted((k for k in base if base[k]["pass"] == 0 and new[k]["pass"] == 1), key=str)
    down = sorted((k for k in base if base[k]["pass"] == 1 and new[k]["pass"] == 0), key=str)
    changed = sorted((k for k in base if base[k]["actual"] != new[k]["actual"] and base[k]["pass"] == new[k]["pass"]), key=str)
    oc = lambda ks: sorted({k[0] for k in ks})
    print(f"== {name}: 0→1 {len(up)} 行 / {len(oc(up))} 案例；1→0 {len(down)} 行 / {len(oc(down))} 案例；同判定但 actual 变 {len(changed)} 行")
    for k in down:
        print(f"   ↓ {k[0]} [{k[1]}] expect={base[k]['expect']} | {base[k]['actual']} → {new[k]['actual']}")
    if "-v" in sys.argv[0:1] or len(sys.argv) == 2:
        for k in up:
            print(f"   ↑ {k[0]} [{k[1]}] expect={base[k]['expect']} | {base[k]['actual']} → {new[k]['actual']}")
        for k in changed[:15]:
            print(f"   ~ {k[0]} [{k[1]}] pass={base[k]['pass']} | {base[k]['actual']} → {new[k]['actual']}")
