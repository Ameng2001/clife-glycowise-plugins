"""案例协议离线消融（探索性，内审 W12；先提交再运行）。
问题：去掉落库断言 expect_state、或去掉窗口前序落库动作 setup 后，formal 80 份提案的 3d / 1d 裁决会不会变。
做法：复制 cases/ 为两份变体（no_expect_state：删 expect_state 及 expect_state_* 键；no_setup：setup 置空），
对每份提案按 formal 同一沙箱与基线，在其 Dᵢ 与当轮外关卡留出集 holdout-R 上重算 hᵢ / h′ 读数（--as-of 2026-10-25，repeat 3），
再用同一 gate_decide 判 3d 与 1d，与 formal 裁决比对。不改插件、不改判据，台账记 exploratory。
用法：python3 run.py <variant> <jobs.txt>   variant ∈ {no_expect_state, no_setup}"""
import json, shutil, subprocess, sys, yaml
from pathlib import Path
W = Path(__file__).resolve().parents[2]; D = Path(__file__).resolve().parent
S = Path("/Users/liuyameng/Codes/astra-studio-plugins/studio-evolve/scripts"); E = "/Users/liuyameng/Codes/onto-fundary-plugins"
REPO = Path("/Users/liuyameng/Codes/clife-glycowise-plugins"); OV = W / "sets/family-override.yaml"
variant, jobs = sys.argv[1], Path(sys.argv[2])
cd = D / variant / "cases"
if not cd.exists():
    shutil.copytree(W / "cases", cd)
    for f in (cd / "real").glob("*.yaml"):
        y = yaml.safe_load(f.read_text(encoding="utf-8"))
        if variant == "no_expect_state":
            y = {k: v for k, v in y.items() if not k.startswith("expect_state")}
        else:
            y["setup"] = []
        f.write_text(yaml.safe_dump(y, allow_unicode=True, sort_keys=False), encoding="utf-8")
def run(target, state, cases_file, out):
    subprocess.run(["python3", S / "runner_onto_engine.py", "run", "--engine-root", E, "--target-dir", target, "--ontology", "glycowise", "--state", state,
                    "--cases-dir", cd, "--cases-file", cases_file, "--repeat", "3", "--router", "manual", "--recordings", "plugins/glycowise/cq/all_routes.json",
                    "--family-override", OV, "--as-of", "2026-10-25", "--out", out], check=True, capture_output=True, text=True, cwd=REPO)
    o = out.with_suffix(".json")
    subprocess.run(["python3", S / "growth_metrics.py", "compute", "--runner", "onto-engine", "--results", out, "--state", state, "--cases-file", cases_file,
                    "--family-override", OV, "--out", o], check=True, capture_output=True, text=True, cwd=REPO)
    return o
pa = {}
for R in (8, 9, 10, 11):
    for p in yaml.safe_load(open(W / f"chains-formal/pa-r{R}.yaml"))["proposals"]:
        pa[p["id"]] = p
res, base_cache = [], {}
od = D / variant / "out"; od.mkdir(parents=True, exist_ok=True)
for line in jobs.read_text().split("\n"):
    if not line.strip():
        continue
    R, pid, num, chain, base, sb = line.split()
    R = int(R); B = W / f"sets/holdout-{R}.yaml"; di = W / pa[pid]["di"][0]
    for key, cf in (("B", B), ("Di", di)):
        k = (R, key, str(cf))
        if k not in base_cache:
            base_cache[k] = run(W / base / "plugins/glycowise", "h_i", cf, od / f"r{R}-base-{key}-{cf.stem}.jsonl")
    hp_di = run(Path(sb) / "plugins/glycowise", "h_prime", di, od / f"{pid}-Di.jsonl")
    hp_b = run(Path(sb) / "plugins/glycowise", "h_prime", B, od / f"{pid}-B.jsonl")
    dec = {}
    for m in ("3d", "1d"):
        vout = od / f"{pid}-verdict-{m}.json"
        subprocess.run(["python3", S / "gate_decide.py", "--config", W / "config.yaml", "--proposal", num, "--attempt", "1", "--round", str(R),
                        "--inner-base", base_cache[(R, "Di", str(di))], "--inner-cand", hp_di, "--outer-pair", "default", base_cache[(R, "B", str(B))], hp_b,
                        "--gate-mode", m, "--holdout-file", B, "--verdict-out", vout], check=True, capture_output=True, text=True, cwd=REPO)
        dec[m] = json.loads(vout.read_text(encoding="utf-8"))["decision"]
    orig = {m: json.load(open(W / f"verdicts/{R}-{num}-1-{m}.json"))["decision"] for m in ("3d", "1d")}
    res.append({"round": R, "id": pid, "num": num, "orig": orig, "ablated": dec})
    print(pid, orig, "->", dec, flush=True)
(D / f"{variant}-summary.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
flip = {m: sum(1 for r in res if r["orig"][m] != r["ablated"][m]) for m in ("3d", "1d")}
div = sum(1 for r in res if r["ablated"]["3d"] != r["ablated"]["1d"])
print("FLIPS", flip, "3d≠1d after ablation:", div, "n", len(res))
