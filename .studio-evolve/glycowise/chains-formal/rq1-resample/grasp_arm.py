"""GRASP 式「回归计数预算」臂（探索性补充，内审 W27 / W39）：离线重判 formal 80 份提案。
接受 ⇔ Dᵢ 上 ΔA > 0（净分为正）且当轮外关卡留出集 B_i 上「hᵢ 全过、h′ 有一次不过」的案例数 ≤ budget（0；另报 1）。
读数取 P-A 当时的 hᵢ / h′ 读数（case_pass），回退取 arms/formal-3x 的三次重抽判定。"""
import json, yaml
from pathlib import Path
W = Path(__file__).resolve().parents[2]
a = json.load(open(W / "arms/formal-3x/arms.json"))
ids = {}
for R in (8, 9, 10, 11):
    for p in yaml.safe_load(open(W / f"chains-formal/pa-r{R}.yaml"))["proposals"]:
        ids[(R, str(p["num"]))] = p
def rd(f):
    return json.load(open(f))
out = {}
for budget in (0, 1):
    acc = []
    for p in a["proposals"]:
        R, n = p["round"], str(p["proposal"])
        v = rd(W / f"verdicts/{R}-{n}-1-3d.json")
        dA = v["inner"]["deltas"]["dA"]
        # 裁决时外关卡所用的那一对读数（run_pa 拷到 readings/P{num}-h{i,p}-B.json）
        hi = rd(W / f"readings/P{n}-hi-B.json")["case_pass"]; hp = rd(W / f"readings/P{n}-hp-B.json")["case_pass"]
        broken = [c for c, x in hi.items() if float(x) >= 1.0 and c in hp and float(hp[c]) < 1.0]
        if dA > 0 and len(broken) <= budget:
            acc.append(p)
    pairs = [x["regress"] for p in acc for x in p["per_seed"]]
    same3d = sum(1 for p in acc if p["accepted"]["3d"]); extra = [p["id"] for p in acc if not p["accepted"]["3d"]]; miss = [p["id"] for p in a["proposals"] if p["accepted"]["3d"] and p not in acc]
    out[budget] = {"n_accept": len(acc), "accept_rate": len(acc) / len(a["proposals"]), "regress_rate": sum(pairs) / len(pairs) if pairs else None,
                   "accepted_also_by_3d": same3d, "accepted_not_by_3d": extra, "rejected_but_3d_accepts": miss}
(W / "arms/formal-3x/grasp-arm.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False))
