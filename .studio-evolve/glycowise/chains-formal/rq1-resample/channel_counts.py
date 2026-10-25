"""三维与一维仍能分开的通道在 formal 80 份提案 3d 裁决上的触发数（§5.5.1 表）。
(a) 某层 ΔT_k < −0.02 且 ΔA ≥ 0（内关卡或任一外关卡）；(b) ΔW_family < 0（内或外）；(c) 内关卡 ΔT、ΔS、ΔW 均不为正且 ΔC < 0；
另报外关卡 ΔS < 0 的次数及其中 ΔA ≥ 0 的次数，与 S_consist / S_stable 的取值分布（全部读数）。"""
import glob, json
from collections import Counter
from pathlib import Path
W = Path(__file__).resolve().parents[2]
a = json.load(open(W / "arms/formal/arms.json"))
ch = Counter(); outer_dS = Counter()
for p in a["proposals"]:
    v = json.load(open(W / f"verdicts/{p['round']}-{p['proposal']}-1-3d.json"))
    d = v["inner"]["deltas"]; outs = [o["deltas"] for o in v["outer"]]
    if any(t is not None and t < -0.02 for t in (d.get("dT") or {}).values()) and (d.get("dA") or 0) >= 0: ch["a_inner"] += 1
    if any(any(t is not None and t < -0.02 for t in (o.get("dT") or {}).values()) and (o.get("dA") or 0) >= 0 for o in outs): ch["a_outer"] += 1
    if ((d.get("dW") or {}).get("W_family") or 0) < 0 or any(((o.get("dW") or {}).get("W_family") or 0) < 0 for o in outs): ch["b"] += 1
    grow = any((t or 0) > 0 for t in (d.get("dT") or {}).values()) or (d.get("dS") or 0) > 0 or any((w or 0) > 0 for w in (d.get("dW") or {}).values())
    if not grow and (d.get("dC") or 0) < 0: ch["c"] += 1
    for o in outs:
        if (o.get("dS") or 0) < 0:
            outer_dS["lt0"] += 1; outer_dS["lt0_with_dA_ge0"] += int((o.get("dA") or 0) >= 0)
S = Counter()
for f in glob.glob(str(W / "**/*.json"), recursive=True):
    try: d = json.load(open(f))
    except Exception: continue
    if isinstance(d, dict) and "S_consist" in d and "S_stable" in d: S[(d["S_consist"], d["S_stable"])] += 1
out = {"n_proposals": len(a["proposals"]), "channels": dict(ch), "outer_dS": dict(outer_dS), "S_readings": {str(k): v for k, v in S.most_common()}}
(W / "arms/formal-3x/channel-counts.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False))
