"""随机对照按 baselines.md 登记口径离线重做（探索性补充）：gate-random-matched = 每轮接受率匹配三维臂、seeds 3。
抽签沿用 gate_decide.py random 模式的实现（sha256(f"{seed}:{proposal}:{attempt}")），回退取 arms/formal-3x 的逐提案三次重抽判定。
另报 20 个 seed 的分布。formal 实际执行的是 p = 0.6、seed 0（§4.7），差异登记为协议偏离 D-7。"""
import hashlib, json, random, statistics
from pathlib import Path
W = Path(__file__).resolve().parents[2]
a = json.load(open(W / "arms/formal-3x/arms.json"))
P = a["proposals"]
p_r = {}
for R in sorted({p["round"] for p in P}):
    ps = [p for p in P if p["round"] == R]
    p_r[R] = sum(p["accepted"]["3d"] for p in ps) / len(ps)
def draw(seed, num, rate):
    r = random.Random(int(hashlib.sha256(f"{seed}:{num}:1".encode()).hexdigest(), 16) % (2**63))
    return r.random() < rate
def arm(seed):
    acc = [p for p in P if draw(seed, p["proposal"], p_r[p["round"]])]
    pairs = [x["regress"] for p in acc for x in p["per_seed"]]
    return len(acc), (sum(pairs) / len(pairs)) if pairs else None
r3 = a["arms"]["3d"]["regress_rate"]
out = {"p_by_round": p_r, "registered_seeds": {}, "seeds_20": {}}
for s in (0, 1, 2):
    n, r = arm(s); out["registered_seeds"][s] = {"n_accept": n, "accept_rate": n / len(P), "regress_rate": r, "minus_3d": r - r3}
for s in range(20):
    n, r = arm(s); out["seeds_20"][s] = {"n_accept": n, "regress_rate": r}
reg = [v["regress_rate"] for v in out["registered_seeds"].values()]
r20 = [v["regress_rate"] for v in out["seeds_20"].values()]
out["summary"] = {"3d": r3, "registered_mean": statistics.fmean(reg), "registered_minus_3d": statistics.fmean(reg) - r3,
                  "seeds20_mean": statistics.fmean(r20), "seeds20_min": min(r20), "seeds20_max": max(r20),
                  "seeds20_share_gt_3d": sum(1 for x in r20 if x > r3) / len(r20)}
(W / "arms/formal-3x/random-matched.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(out["p_by_round"])); print(json.dumps(out["registered_seeds"], ensure_ascii=False)); print(json.dumps(out["summary"], ensure_ascii=False))
