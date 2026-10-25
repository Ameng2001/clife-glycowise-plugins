"""正对照（实现校验，探索性）：按 paper proposal/positive-control-spec-2026-10-25.md 构造三类候选读数，经 formal 同一 growth_metrics / gate_decide 走八臂。
只改结果行，不改插件、不跑引擎；规则写死在本文件，先提交再运行。用法：python3 run.py"""
import json, subprocess, sys
from collections import defaultdict
from pathlib import Path
W = Path(__file__).resolve().parents[2]; D = Path(__file__).resolve().parent
S = Path("/Users/liuyameng/Codes/astra-studio-plugins/studio-evolve/scripts")
OV = W / "sets/family-override.yaml"
MODES = ["3d", "3d-noT", "3d-noS", "3d-noW", "1d", "1d-strict", "none", "random"]
# 底稿：round 10 / 11 中 3d 链接受、编号最小的 3 份根因修（i、ii 用 round 10；iii 用 round 11）
BASES = {"i": [(10, "P42a", "P42"), (10, "P43a", "P43"), (10, "P44a", "P44")],
         "ii": [(10, "P42a", "P42"), (10, "P43a", "P43"), (10, "P44a", "P44")],
         "iii": [(11, "P52a", "P52"), (11, "P53a", "P53"), (11, "P54a", "P54")]}
M_FLIP = 2

def rows(f):
    return [json.loads(l) for l in open(f, encoding="utf-8")]

def write(rs, f):
    f.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rs) + "\n", encoding="utf-8")

def case_state(rs):
    """原题行按案例：全过 = 1、全不过 = 0、混合 = None；以及 tier / family。"""
    g = defaultdict(list); meta = {}
    for r in rs:
        if r.get("variant") or r.get("pass") is None:
            continue
        g[r["case"]].append(int(r["pass"])); meta[r["case"]] = (int(r.get("tier", 0)), r.get("family"))
    return {c: (1 if all(v) else 0 if not any(v) else None) for c, v in g.items()}, meta

def flip(rs, cases, to):
    """把这些案例的全部行（原题与变体）的 pass 置为 to，保持各行其余字段不变。"""
    out = []
    for r in rs:
        if r["case"] in cases and r.get("pass") is not None:
            r = {**r, "pass": to}
        out.append(r)
    return out

def build_i(b):
    st, meta = case_state(b)
    t3 = sorted(c for c, v in st.items() if v == 1 and meta[c][0] == 3)[:M_FLIP]
    t1 = sorted(c for c, v in st.items() if v == 0 and meta[c][0] == 1)[:M_FLIP]
    assert len(t3) == M_FLIP and len(t1) == M_FLIP
    return flip(flip(b, set(t3), 0), set(t1), 1), {"t3_to_fail": t3, "t1_to_pass": t1}

def build_ii(b):
    st, meta = case_state(b)
    fams = sorted({m[1] for m in meta.values() if m[1]})
    best = None
    for f in fams:
        hi = sorted(c for c, v in st.items() if v == 1 and meta[c][1] == f and meta[c][0] >= 2)
        if not hi:
            continue
        need = defaultdict(int)
        for c in hi:
            need[meta[c][0]] += 1
        comp = []
        for t, k in sorted(need.items()):
            pool = sorted(c for c, v in st.items() if v == 0 and meta[c][0] == t and meta[c][1] != f)
            if len(pool) < k:
                comp = None; break
            comp += pool[:k]
        if comp is not None and (best is None or len(hi) < len(best[1])):
            best = (f, hi, comp)
    assert best, "找不到可补偿的场景族"
    f, hi, comp = best
    return flip(flip(b, set(hi), 0), set(comp), 1), {"family_dropped": f, "to_fail": hi, "compensate_to_pass": comp}

def build_iii(b):
    out = [{**r, "steps": (r["steps"] - 1) if isinstance(r.get("steps"), (int, float)) and r["steps"] >= 1 else r.get("steps"), "state": "h_prime"} for r in b]
    return out, {"steps_minus": 1}

def reading(res, state, out):
    subprocess.run(["python3", S / "growth_metrics.py", "compute", "--runner", "onto-engine", "--results", res, "--state", state,
                    "--family-override", OV, "--out", out], check=True, capture_output=True, text=True)
    return out

summary = []
for cls, bases in BASES.items():
    for k, (R, pid, dn) in enumerate(bases):
        tag = f"{cls}-{pid}"; od = D / tag; od.mkdir(exist_ok=True)
        pa = W / f"chains-formal/pa-r{R}"; B = W / f"sets/holdout-{R}.yaml"
        hi_di, hp_di = pa / f"hi-3d-{dn}-Di.json", pa / f"{pid}-hp-Di.json"
        hi_b, hp_b = pa / f"hi-B{R}.json", pa / f"{pid}-hp-B{R}.json"
        if cls in ("i", "ii"):
            cand, info = (build_i if cls == "i" else build_ii)(rows(pa / f"{pid}-hp-B{R}.jsonl"))
            write(cand, od / "cand-B.jsonl"); hp_b = reading(od / "cand-B.jsonl", "h_prime", od / "cand-B.json")
        else:
            cand, info = build_iii(rows(pa / f"hi-3d-{dn}-Di.jsonl"))
            write(cand, od / "cand-Di.jsonl"); hp_di = reading(od / "cand-Di.jsonl", "h_prime", od / "cand-Di.json")
            hp_b = hi_b   # 外关卡：候选与基线相同（不回退）
        dec = {}
        for m in MODES:
            extra = {"1d-strict": ["--delta", "0.03"], "random": ["--accept-rate", "0.6", "--seed", "0"]}.get(m, [])
            vout = od / f"verdict-{m}.json"
            subprocess.run(["python3", S / "gate_decide.py", "--config", W / "config.yaml", "--proposal", str(9000 + len(summary)), "--attempt", "1", "--round", str(R),
                            "--inner-base", hi_di, "--inner-cand", hp_di, "--outer-pair", "default", hi_b, hp_b, "--gate-mode", m, "--holdout-file", B,
                            "--verdict-out", vout] + extra, check=True, capture_output=True, text=True)
            v = json.loads(vout.read_text(encoding="utf-8")); dec[m] = (v["decision"], v["triggered"])
        expect_ok = dec["3d"][0] != "ACCEPT" and dec["1d"][0] == "ACCEPT"
        summary.append({"class": cls, "base": pid, "round": R, "construction": info, "decisions": dec, "expected_3d_reject_1d_accept": expect_ok})
        print(tag, {m: d[0] for m, d in dec.items()}, "expected" if expect_ok else "UNEXPECTED", flush=True)
(D / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
print("ALL", sum(s["expected_3d_reject_1d_accept"] for s in summary), "/", len(summary))
