"""内审可修项的三项补充（探索性）：
1. 三次重抽主分析上剔除被判提案自身 Dᵢ 的敏感性；2. T5 按五条朴素规则拆分；3. 按缺陷聚类（同一 pair 的根因 + 朴素为一簇）的 bootstrap。"""
import json, random, re, yaml
from collections import defaultdict
from pathlib import Path
W = Path(__file__).resolve().parents[2]
a = json.load(open(W / "arms/formal-3x/arms.json")); P = a["proposals"]
meta = {}
for R in (8, 9, 10, 11):
    for p in yaml.safe_load(open(W / f"chains-formal/pa-r{R}.yaml"))["proposals"]:
        di = set()
        for f in p["di"]:
            y = yaml.safe_load(open(W / f)); di |= set(map(str, y.get("ids") or y.get("source_cases") or []))
        meta[(R, str(p["num"]))] = {**p, "di_ids": di}
# 1. 剔除自身 Dᵢ：被判提案在某份重抽上「被弄坏」的案例若全在其 Dᵢ 里，或其 Dᵢ 让该提案回退判定翻转，需重算；这里按逐案例结果重判
O = W / "results/rq1-resample"; SEEDS = {R: [R + 1, R + 2, R + 3] for R in (8, 9, 10, 11)}
def load(f, drop):
    d = defaultdict(list); t = {}
    for l in open(f, encoding="utf-8"):
        r = json.loads(l)
        if r.get("variant") or r.get("pass") is None or r["case"] in drop: continue
        d[r["case"]].append(int(r["pass"])); t[r["case"]] = int(r.get("tier", 0))
    return d, t
def reading(d, t):
    rows = [(t[c], x) for c, v in d.items() for x in v]; A = sum(x for _, x in rows) / len(rows); T = {}; n = {}
    for k in (1, 2, 3, 4):
        s = [x for tt, x in rows if tt == k]; T[k] = sum(s) / len(s) if s else None; n[k] = sum(1 for c in d if t[c] == k)
    return A, T, n
def regress(b, c):
    (A0, T0, n0), (A1, T1, _) = b, c
    return int(A1 < A0 - 1e-12 or any(n0[k] >= 8 and T0[k] is not None and T1[k] is not None and T0[k] - T1[k] > 0.02 for k in T0))
own = {}
for p in P:
    m = meta[(p["round"], str(p["proposal"]))]; R = p["round"]
    own[(R, str(p["proposal"]))] = [regress(reading(*load(O / f"r{R}-s{s}-base.jsonl", m["di_ids"])), reading(*load(O / f"r{R}-s{s}-{m['id']}.jsonl", m["di_ids"]))) for s in SEEDS[R]]
def rate(m, table):
    acc = [p for p in P if p["accepted"][m]]; v = [x for p in acc for x in table[(p["round"], str(p["proposal"]))]]
    return sum(v) / len(v)
orig = {(p["round"], str(p["proposal"])): [x["regress"] for x in p["per_seed"]] for p in P}
sens = {m: {"main": rate(m, orig), "drop_own_Di": rate(m, own)} for m in ("3d", "1d", "none", "random")}
flips = [(meta[k]["id"], orig[k], own[k]) for k in orig if orig[k] != own[k]]
# 2. 朴素规则拆分
def rule_of(m):
    r = str(m.get("naive_rule") or "")
    for key, lab in (("1", "放宽阈值"), ("2", "跳过缺参数校验"), ("3", "删命中分支"), ("4", "hard→soft"), ("5", "字面量")):
        if re.search(rf"(^|[^0-9])(N?{key})([^0-9]|$)|{lab[:2]}", r): return lab
    if "字面" in r: return "字面量"
    if "删" in r: return "删命中分支"
    if "soft" in r: return "hard→soft"
    return r or "?"
split = defaultdict(lambda: {"n": 0, "acc_3d": 0, "regress_sum_3x": 0.0, "regress_sum_none": 0.0})
for p in P:
    m = meta[(p["round"], str(p["proposal"]))]
    lab = "根因" if m["kind"] == "root" else rule_of(m)
    x = split[lab]; x["n"] += 1; x["acc_3d"] += int(p["accepted"]["3d"]); x["regress_sum_none"] += p["regress"]
    if p["accepted"]["3d"]: x["regress_sum_3x"] += p["regress"]
# 3. 按缺陷聚类的 bootstrap（random − 3d、none − 3d）
clusters = defaultdict(list)
for p in P:
    m = meta[(p["round"], str(p["proposal"]))]; clusters[(p["round"], m["chain"], re.match(r"P\d+", m["id"]).group())].append(p)
keys = sorted(clusters); rng = random.Random(0); bs = defaultdict(list)
def arm_rate(ps, m):
    v = [x["regress"] for p in ps if p["accepted"][m] for x in p["per_seed"]]; return sum(v) / len(v) if v else None
for _ in range(1000):
    ps = [p for k in (keys[rng.randrange(len(keys))] for _ in keys) for p in clusters[k]]
    r3 = arm_rate(ps, "3d")
    for m in ("random", "none", "1d"):
        rm = arm_rate(ps, m)
        if rm is not None and r3 is not None: bs[m].append(rm - r3)
ci = {m: [sorted(v)[int(.025 * (len(v) - 1))], sorted(v)[int(.975 * (len(v) - 1))]] for m, v in bs.items()}
out = {"own_Di_sensitivity": sens, "own_Di_flips": flips, "naive_rule_split": dict(split), "n_clusters": len(keys), "cluster_bootstrap_ci_minus_3d": ci}
(W / "arms/formal-3x/extra.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=1))
