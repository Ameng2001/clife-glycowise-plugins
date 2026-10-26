"""golden.yaml → runner/cases/golden-NN.yaml（studio-evolve runner 案例格式，带 variants）。

与 runner_onto_engine.py golden-to-cases 等价，多做一件事：把 golden 的 variants 原样带进案例，
runner 会为每个 variant 另跑一行（variant 列 = "<kind>-<i>"），原题判定只算 q。
"""
import datetime as dt, json, sys
from pathlib import Path
import yaml

HERE = Path(__file__).resolve().parent
TIER = {"query": 1, "action": 3, "rejected": 3}

def main() -> int:
    items = yaml.safe_load((HERE / "golden.yaml").read_text(encoding="utf-8")) or []
    out_dir = HERE / "runner" / "cases"; out_dir.mkdir(parents=True, exist_ok=True)
    for f in out_dir.glob("golden-*.yaml"): f.unlink()
    today = dt.date.today().isoformat()
    for i, it in enumerate(items, 1):
        expect = str(it["expect"]).strip(); kind = expect.split("(")[0]
        cid = f"golden-{i:02d}"
        doc = {"id": cid, "q": it["q"], "expect": expect, "tier": TIER[kind], "family": "golden", "origin": "sim",
               "observed_at": today, "elements": [], "label": {"answer": expect, "source": "simulate"},
               "variants": [{"kind": v.get("kind", "variant"), "q": v["q"]} for v in (it.get("variants") or []) if v.get("q")]}
        (out_dir / f"{cid}.yaml").write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"✓ {len(items)} 条案例（{sum(1 for it in items if it.get('variants'))} 条带 variants）→ {out_dir}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
