"""RQ-1 / RQ-3 三次留出集重抽的回退率（口径见 chains-formal/endpoint-plan-rq1.md，先于读数提交）。
读 results/rq1-resample/r{R}-s{s}-{base|提案名}.jsonl；裁决（各臂接受与否）取 arms/formal/arms.json。
输出 arms/formal-3x/arms.json（与 arm_compare 同结构，供 results_tables / fig_results）与 per-resample 明细。
用法：python3 compute.py [--no-targeted]"""
import json, random, sys, yaml
from collections import defaultdict
from pathlib import Path
W = Path(__file__).resolve().parents[2]
NO_T = "--no-targeted" in sys.argv
MODES = ["3d", "1d", "random", "1d-strict", "none", "3d-noT", "3d-noS", "3d-noW"]
SEEDS = {R: [R + 1, R + 2, R + 3] for R in (8, 9, 10, 11)}
drop = set()
if NO_T:
    for w in range(50, 55):
        drop |= set(yaml.safe_load(open(W / f"sets/targeted-W{w}.yaml"))["ids"])

def load(f):
    """原题行：{case: (tier, [pass...])}"""
    d = defaultdict(list); t = {}
    for l in open(f, encoding="utf-8"):
        r = json.loads(l)
        if r.get("variant") or r.get("pass") is None or r["case"] in drop:
            continue
        d[r["case"]].append(int(r["pass"])); t[r["case"]] = int(r.get("tier", 0))
    return {c: (t[c], v) for c, v in d.items()}

def reading(m):
    rows = [(t, p) for t, v in m.values() for p in v]
    A = sum(p for _, p in rows) / len(rows)
    T, n = {}, {}
    for k in (1, 2, 3, 4):
        s = [p for t, p in rows if t == k]
        T[k] = sum(s) / len(s) if s else None; n[k] = sum(1 for t, _ in m.values() if t == k)
    return A, T, n

def regress(b, c):
    (A0, T0, n0), (A1, T1, _) = reading(b), reading(c)
    why = (["dA"] if A1 < A0 - 1e-12 else []) + [f"dT_{k}" for k in T0 if n0[k] >= 8 and T0[k] is not None and T1[k] is not None and T0[k] - T1[k] > 0.02]
    return int(bool(why)), why

def regress_any(b, c):
    broken = sorted(k for k, (_, v) in b.items() if sum(v) == len(v) and k in c and sum(c[k][1]) < len(c[k][1]))
    return int(bool(broken)), broken

arms = json.load(open(W / "arms/formal/arms.json"))
ids = {}
for R in (8, 9, 10, 11):
    for p in yaml.safe_load(open(W / f"chains-formal/pa-r{R}.yaml"))["proposals"]:
        ids[(R, str(p["num"]))] = p["id"]
O = W / "results/rq1-resample"
props, detail = [], []
for p in arms["proposals"]:
    R, n = p["round"], str(p["proposal"]); name = ids[(R, n)]
    per = []
    for s in SEEDS[R]:
        b, c = load(O / f"r{R}-s{s}-base.jsonl"), load(O / f"r{R}-s{s}-{name}.jsonl")
        assert set(b) == set(c), (R, s, name)
        g, why = regress(b, c); ga, broken = regress_any(b, c)
        per.append({"seed": s, "regress": g, "why": why, "regress_any": ga, "broken": broken, "n_cases": len(b)})
    props.append({**p, "regress": sum(x["regress"] for x in per) / 3, "regress_any": sum(x["regress_any"] for x in per) / 3,
                  "regress_any_cases": sorted({c for x in per for c in x["broken"]}), "regress_basis": "B_next_x3", "per_seed": per, "id": name})

def stats(sample):
    """sample: [(prop, seed_index)]；比例按 (提案, 重抽) 对合并。"""
    out = {}
    for m in MODES:
        judged = [(p, k) for p, k in sample if m in p["accepted"]]
        acc = [(p, k) for p, k in judged if p["accepted"][m]]
        r = [p["per_seed"][k]["regress"] for p, k in acc]; ra = [p["per_seed"][k]["regress_any"] for p, k in acc]
        out[m] = {"accept_rate": (len(acc) / len(judged)) if judged else None, "n_accept": len(acc) // 3 if sample is pairs else len(acc),
                  "n_judged": len(judged) // 3 if sample is pairs else len(judged), "regress_rate": (sum(r) / len(r)) if r else None,
                  "regress_any_rate": (sum(ra) / len(ra)) if ra else None, "n_any_known": len(acc) // 3 if sample is pairs else len(acc), "n_pairs": len(acc)}
    return out

def diffs(st):
    r3 = st["3d"]["regress_rate"]; d = {}
    d["regress_rate_diff"] = st["1d"]["regress_rate"] - r3
    d["regress_any_diff"] = st["1d"]["regress_any_rate"] - st["3d"]["regress_any_rate"]
    for m in ("random", "1d-strict", "3d-noT", "3d-noS", "3d-noW"):
        d[f"{m}_minus_3d"] = st[m]["regress_rate"] - r3
    return d

pairs = [(p, k) for p in props for k in range(3)]
point = stats(pairs); pd = diffs(point)
rng = random.Random(0); boots = defaultdict(list)
by_round = defaultdict(list)
for p in props:
    by_round[p["round"]].append(p)
for _ in range(1000):
    smp = []
    for k in range(3):                      # 按重抽分层
        for R, ps in by_round.items():      # 每份内按轮次对提案有放回重抽，各臂共用
            smp += [(ps[rng.randrange(len(ps))], k) for _ in ps]
    st = stats(smp)
    for key, v in diffs(st).items():
        boots[key].append(v)
ci = {k: sorted(v)[24:975:950] for k, v in boots.items()}
out = dict(arms)
out.update({"arms": point, "diffs": {k: {"value": pd[k], "ci95": ci[k], "boot": 1000} for k in pd}, "proposals": props,
            "flags": ["B_NEXT_X3"] + (["NO_TARGETED"] if NO_T else []), "seed": 0, "boot": 1000,
            "resample": {"seeds": SEEDS, "plan": "chains-formal/endpoint-plan-rq1.md", "drop_targeted": NO_T}})
dst = W / ("arms/formal-3x-notargeted" if NO_T else "arms/formal-3x"); dst.mkdir(parents=True, exist_ok=True)
(dst / "arms.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps({m: {k: point[m][k] for k in ("accept_rate", "n_accept", "regress_rate", "regress_any_rate", "n_pairs")} for m in MODES}, ensure_ascii=False))
print(json.dumps({k: [round(pd[k], 4), [round(x, 4) for x in ci[k]]] for k in pd}, ensure_ascii=False))
print("regress (proposal, seed):", [(p["id"], [x["regress"] for x in p["per_seed"]]) for p in props if any(x["regress"] for x in p["per_seed"]) and p["accepted"]["3d"]])
