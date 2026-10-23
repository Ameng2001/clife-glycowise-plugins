#!/usr/bin/env python3
"""给一个真实窗口起草 feedback.yaml 的**待标注清单**——不是标签。

    python3 draft_feedback.py --window 2026-W43

对每条 audit.jsonl 轨迹：列出引擎实际裁决（decision / 命中规则 / 行数），并把口语清单里的 CQ 领域期望（cq_expect）
与实际裁决做机器比对，给一个 `suggested` 供业务侧参考。业务侧要做的是把 `label` 从 null 改成 correct / partial / wrong，
wrong 的补 truth + truth_expect，再把 reviewer 写成自己。`status: draft` 没改成 `reviewed` 之前，evolve-attribute 不得消费。
"""
import argparse, json, os, re
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))


def actual_of(t):
    if t["kind"] == "ask":
        return "query", f"query·{t['rows']} 行"
    viol = [r["rule"] for r in t["rules_evaluated"] if r["result"] == "violate"]
    if t["decision"] == "rejected":
        return f"rejected({viol[0]})" if viol else "rejected", f"rejected {viol}"
    return f"action({t['action']})", f"{t['decision']} {t['action']}" + (f" soft={viol}" if viol else "")


def compare(cq_expect, actual_expect, t):
    if not cq_expect:
        return None, "无 CQ 期望"
    m = re.match(r"^(query|action|rejected)(?:\((.*)\))?$", cq_expect)
    kind, target = m.group(1), m.group(2)
    if kind == "query":
        ok = actual_expect == "query" and t.get("rows", 0) >= 1
        return ("correct" if ok else "wrong"), ("查到行" if ok else ("查到 0 行" if actual_expect == "query" else "没走查询"))
    if kind == "action":
        ok = actual_expect == f"action({target})"
        return ("correct" if ok else "wrong"), ("动作一致且未被拒" if ok else f"实际 {actual_expect}")
    if kind == "rejected":
        viol = [r["rule"] for r in t.get("rules_evaluated", []) if r["result"] == "violate"]
        hit = t.get("decision") == "rejected" and any(v == target or v.startswith(target.split("_")[0] + "_") for v in viol)
        return ("correct" if hit else "wrong"), ("被期望规则拒" if hit else f"实际 {actual_expect}")
    return None, ""


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--window", required=True); a = ap.parse_args()
    wdir = os.path.join(HERE, "trajectories", a.window)
    utts = {i["utterance"]: i for i in yaml.safe_load(open(os.path.join(HERE, f"utterances.{a.window}.yaml"), encoding="utf-8"))["items"]}
    items = []
    for line in open(os.path.join(wdir, "audit.jsonl"), encoding="utf-8"):
        if not line.strip():
            continue
        t = json.loads(line)
        exp, actual_txt = actual_of(t)
        cq = utts.get(t["utterance"], {}).get("cq_expect")
        sug, why = compare(cq, exp, t)
        items.append({"trace_id": t["trace_id"], "utterance": t["utterance"], "engine_actual": actual_txt, "cq_expect": cq,
                      "suggested": sug, "suggested_why": why, "label": None, "truth": None, "truth_expect": None, "reviewer": None})
    out = {"window": a.window, "status": "draft", "reviewer": None, "labeled_at": None,
           "_howto": "业务侧逐条填 label（correct/partial/wrong）、truth（一句真实答案或真实根因）；wrong 还要 truth_expect；reviewer 写自己的 id/role；全部填完把 status 改成 reviewed。suggested 只是机器比对 CQ 期望的参考，不是标签。",
           "items": items}
    p = os.path.join(wdir, "feedback.yaml")
    with open(p, "w", encoding="utf-8") as f:
        f.write("# 待标注清单（status: draft）——引擎真实裁决已列出，label 全部为空，等业务侧填写。draft 状态不得进 evolve-attribute。\n")
        yaml.safe_dump(out, f, allow_unicode=True, sort_keys=False, width=200)
    n = len(items); ns = sum(1 for i in items if i["suggested"] == "wrong")
    print(f"✓ {a.window}: {n} 条待标注 → {p}（机器比对与 CQ 期望不一致 {ns} 条，供业务侧优先看）")


if __name__ == "__main__":
    main()
