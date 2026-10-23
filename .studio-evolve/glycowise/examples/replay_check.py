#!/usr/bin/env python3
"""回放校验：在一份**新鲜 seed** 的引擎上，把窗口里每条轨迹重新预演一遍（execute → engine.validate 不落库；ask → 重跑 OQL），
看裁决 / 命中规则 / 行数能否复现。能复现 = 轨迹的参数与对象 id 在库里都查得到、规则行为确定。

    python3 replay_check.py --engine-root ../../../../onto-fundary-plugins --plugin ../../../plugins/glycowise --window 2026-W43
注意：窗口内靠前的写入（如签发 d-P0012-01）会改变后续轨迹看到的状态，新鲜 seed 上回放时这类条目可能标 STATE_DEPENDENT，不算不可复现。
"""
import argparse, importlib.util, json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine-root", required=True, type=Path); ap.add_argument("--plugin", required=True, type=Path); ap.add_argument("--window", required=True)
    ap.add_argument("--mode", choices=["preview", "sequential"], default="sequential",
                    help="sequential：按窗口顺序真 execute（含落库），复现当时的状态演进；preview：每条独立在新鲜 seed 上 validate（不落库）")
    a = ap.parse_args()
    sys.path.insert(0, str(a.engine_root.resolve()))
    from clife_onto_engine.sdk import spi
    from clife_onto_engine.sdk.context import Actor
    from clife_onto_engine.kernel import ActionEngine
    from clife_onto_engine.query import InMemoryStore, QueryView
    from clife_onto_engine.query.oql import execute as oql_execute
    from clife_onto_engine.intent.compiler import _parse_oql
    td = a.plugin.resolve()
    spec = importlib.util.spec_from_file_location(f"onto_plugin_{td.name}", td / "__init__.py", submodule_search_locations=[str(td)])
    mod = importlib.util.module_from_spec(spec); sys.modules[spec.name] = mod; spec.loader.exec_module(mod)
    store = InMemoryStore(); mod.seed_reference_data(store)
    engine = ActionEngine(spi.registry, store=store)
    ok = dep = diff = 0
    for line in open(HERE / "trajectories" / a.window / "audit.jsonl", encoding="utf-8"):
        t = json.loads(line)
        if t["kind"] == "execute":
            actor = Actor(t["actor"]["id"], t["actor"]["role"])
            rec_viol = sorted(r["rule"] for r in t["rules_evaluated"] if r["result"] == "violate")
            rec_commit = t["decision"] != "rejected"
            if a.mode == "sequential":
                res = engine.execute(t["ontology_id"], t["action"], dict(t["inputs_snapshot"]["params"]), actor, schema_version=t["schema_version"], ts=t["ts"])
                snap = engine.audit.query(t["ontology_id"])[-1]
                now_viol = sorted(r.rule for r in snap.rules_evaluated if r.result == "violate")
                now_commit = snap.decision != "rejected"
                same = (snap.decision == t["decision"]) and (set(rec_viol) == set(now_viol))
            else:
                prev = engine.validate(t["ontology_id"], t["action"], dict(t["inputs_snapshot"]["params"]), actor)
                now_viol = sorted(v.rule for v in prev.violations); now_commit = prev.would_commit
                same = (now_commit == rec_commit) and (set(rec_viol) == set(now_viol))
            tag = "OK" if same else "DIFF"
            if not same: diff += 1
            else: ok += 1
            print(f"  {tag:4} {t['trace_id']} {t['action']:<10} 记录 {t['decision']} {rec_viol} ｜ 回放 {'commit' if now_commit else 'reject'} {now_viol}")
        else:
            q = _parse_oql(t["oql"], t["ontology_id"])
            res = oql_execute(q, QueryView(store, []), spi.registry)
            same = len(res.rows) == t["rows"]
            if same: ok += 1
            else: diff += 1
            print(f"  {'OK' if same else 'DIFF':4} {t['trace_id']} ask {t['oql']['start']:<14} 记录 {t['rows']} 行 ｜ 回放 {len(res.rows)} 行")
    print(f"[{a.mode}] 复现 {ok} · 不一致 {diff}" + ("" if a.mode == "sequential" else "（preview 不一致项先看是否窗口内前序写入导致）"))


if __name__ == "__main__":
    main()
