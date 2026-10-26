"""把审计轨迹（trajectories/{window}/audit.jsonl）里引擎实际用过的意图原样登记为 manual 路由：
execute → {"kind":"action","action","params"}；ask → {"kind":"query","oql"}。键 = 原始 utterance，以及 cases/real 里同 trace_id 案例的 q 与 variants。
这是「真实轨迹的路由」：不是 LLM 重新路由，而是当时真的走过的那条路。

    python cq/make_real_routes.py --trajectories ../../.studio-evolve/glycowise/trajectories --cases ../../.studio-evolve/glycowise/cases/real --out cq/real_routes.json
"""
import argparse, glob, json
from pathlib import Path
import yaml

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trajectories", required=True, type=Path); ap.add_argument("--cases", required=True, type=Path); ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    by_trace = {}
    for f in sorted(a.trajectories.glob("*/audit.jsonl")):
        for l in f.read_text(encoding="utf-8").splitlines():
            if not l.strip(): continue
            t = json.loads(l)
            if t.get("kind") == "execute":
                r = {"kind": "action", "confidence": float(t.get("confidence", 0.95)), "action": t["action"], "params": t["inputs_snapshot"]["params"]}
            elif t.get("kind") == "ask":
                r = {"kind": "query", "confidence": float(t.get("confidence", 0.95)), "oql": t["oql"]}
            else:
                continue
            by_trace[t["trace_id"]] = (t.get("utterance"), r)
    routes = {}
    for u, r in by_trace.values():
        if u: routes[u] = r
    n_case = 0
    for f in sorted(a.cases.glob("*.yaml")):
        c = yaml.safe_load(f.read_text(encoding="utf-8")); tid = (c.get("label") or {}).get("trace_id")
        if tid not in by_trace: print(f"  ⚠ {c['id']} 的 trace_id {tid} 没有轨迹"); continue
        r = by_trace[tid][1]; routes[c["q"]] = r; n_case += 1
        for v in c.get("variants") or []:
            if v.get("q"): routes[v["q"]] = r
    a.out.write_text(json.dumps(routes, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"✓ 轨迹 {len(by_trace)} 条 → 路由 {len(routes)} 键（案例 {n_case}）→ {a.out}")

if __name__ == "__main__":
    main()
