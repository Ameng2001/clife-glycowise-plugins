import json, sys
from pathlib import Path
WK = Path(__file__).resolve().parent.parent
def load(p): return {(r["case"], r["variant"]): r for r in map(json.loads, open(p, encoding="utf-8"))}
base = load(WK / "fallout-h10.jsonl")
D = set()
import yaml, glob
for f in glob.glob(str(WK.parent / "attribution/round-10/P*-Di.yaml")): D |= set(yaml.safe_load(open(f))["ids"])
for name in sys.argv[1:]:
    new = load(WK / f"fallout-{name}.jsonl")
    up = {k[0] for k in base if base[k]["pass"] == 0 and new[k]["pass"] == 1}
    down = {}
    for k in base:
        if base[k]["pass"] == 1 and new[k]["pass"] == 0: down.setdefault(k[0], []).append(k)
    ch = {k[0] for k in base if base[k]["actual"] != new[k]["actual"] and base[k]["pass"] == new[k]["pass"]}
    div = sum(1 for k in new for f in new[k]["flags"] if f.startswith("SETUP_DIVERGED")) - sum(1 for k in base for f in base[k]["flags"] if f.startswith("SETUP_DIVERGED"))
    print(f"== {name}: 修好 {len(up)} 例（Dᵢ 内 {len(up & D)}，Dᵢ 外 {sorted(up - D)}）；误伤 {len(down)} 例；判定不变但违规集变 {len(ch)} 例 {sorted(ch)[:8]}；新增 SETUP_DIVERGED {div}")
    for c, ks in sorted(down.items()):
        k = ks[0]; print(f"   ↓ {c} ×{len(ks)} expect={base[k]['expect']} | {base[k]['actual']} → {new[k]['actual']}")
