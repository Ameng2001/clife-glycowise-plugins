"""RQ-2 终点（按 chains-formal/endpoint-plan.md §2）：三份重抽留出集上 h_s / 3d 末态 / 1d 末态的配对读数，
T_tier3_gain_diff 与 A_holdout_diff（三维 − 一维）的点估计与 bootstrap 95% CI（1000 次，seed 0，按重抽分层），以及判定分支。"""
import json, random, sys
from collections import defaultdict
from pathlib import Path
D = Path(__file__).resolve().parent
SETS = ["holdout-12", "holdout-12b", "holdout-12c"]
STATES = ["hs", "3d", "1d"]

def per_case(f):
    """原题行（无 variant）按案例取通过率均值；返回 {case: (tier, mean_pass, n_rows)}。与 growth_metrics.compute 的 T_k / A 等价（每例行数相同）。"""
    acc = defaultdict(list); tier = {}
    for l in open(f, encoding="utf-8"):
        r = json.loads(l)
        if r.get("variant") or r.get("pass") is None:
            continue
        acc[r["case"]].append(int(r["pass"])); tier[r["case"]] = int(r.get("tier", 0))
    return {c: (tier[c], sum(v) / len(v), len(v)) for c, v in acc.items()}

def stats(cases, data):
    out = {}
    for st in STATES:
        rows = [data[st][c] for c in cases]
        A = sum(p * n for _, p, n in rows) / sum(n for _, _, n in rows)
        T = {}
        for k in (1, 3, 4):
            sel = [(p, n) for t, p, n in rows if t == k]
            T[k] = (sum(p * n for p, n in sel) / sum(n for _, n in sel)) if sel else None
        out[st] = {"A": A, "T": T}
    return out

def endpoints(per_set):
    g3 = sum(s["3d"]["T"][3] - s["hs"]["T"][3] for s in per_set) / len(per_set)
    g1 = sum(s["1d"]["T"][3] - s["hs"]["T"][3] for s in per_set) / len(per_set)
    a3 = sum(s["3d"]["A"] for s in per_set) / len(per_set); a1 = sum(s["1d"]["A"] for s in per_set) / len(per_set)
    t1drop = sum(s["hs"]["T"][1] - s["3d"]["T"][1] for s in per_set) / len(per_set)
    return {"T_tier3_gain_3d": g3, "T_tier3_gain_1d": g1, "T_tier3_gain_diff": g3 - g1, "A_3d": a3, "A_1d": a1, "A_holdout_diff": a3 - a1,
            "T_tier1_drop_3d": t1drop}

data = {h: {st: per_case(D / f"{st}-{h}.jsonl") for st in STATES} for h in SETS}
for h in SETS:
    assert set(data[h]["hs"]) == set(data[h]["3d"]) == set(data[h]["1d"]), h
cases = {h: sorted(data[h]["hs"]) for h in SETS}
point_sets = [stats(cases[h], data[h]) for h in SETS]
point = endpoints(point_sets)
n_t3 = sum(sum(1 for c in cases[h] if data[h]["hs"][c][0] == 3) for h in SETS)
n_t1 = [sum(1 for c in cases[h] if data[h]["hs"][c][0] == 1) for h in SETS]
rng = random.Random(0); boots = defaultdict(list)
for _ in range(1000):
    ps = []
    for h in SETS:
        cs = [rng.choice(cases[h]) for _ in cases[h]]
        if not any(data[h]["hs"][c][0] == 3 for c in cs):
            continue
        ps.append(stats(cs, data[h]))
    e = endpoints(ps)
    for k in ("T_tier3_gain_diff", "A_holdout_diff"):
        boots[k].append(e[k])
ci = {}
for k, v in boots.items():
    v = sorted(v); ci[k] = [v[24], v[974]]
half = {k: (c[1] - c[0]) / 2 for k, c in ci.items()}
chains = {c: json.load(open(D.parent / c / "chain.json", encoding="utf-8")) for c in ("3d", "1d")}
res = {"per_set": {h: s for h, s in zip(SETS, point_sets)}, "point": point, "ci95": ci, "ci_half_width": half,
       "n_tier3_pooled": n_t3, "n_tier1_per_set": n_t1, "boot": 1000, "seed": 0}
fail_to_measure = [k for k, w in half.items() if w > 0.10] + (["tier3_pooled<30"] if n_t3 < 30 else [])
fail = [k for k in ci if ci[k][0] <= -0.10] + (["T_tier3_gain_3d<0"] if point["T_tier3_gain_3d"] < 0 else []) \
       + (["T_tier1_drop>0.02"] if all(n >= 8 for n in n_t1) and point["T_tier1_drop_3d"] > 0.02 else [])
res["fail_to_measure"] = fail_to_measure; res["fail"] = fail
res["verdict"] = "功效不足、不判定" if fail_to_measure else ("失败" if fail else "通过（H-2a、H-2b）")
(D / "rq2-endpoint.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps({k: res[k] for k in ("point", "ci95", "ci_half_width", "n_tier3_pooled", "n_tier1_per_set", "fail_to_measure", "fail", "verdict")}, ensure_ascii=False, indent=1))
