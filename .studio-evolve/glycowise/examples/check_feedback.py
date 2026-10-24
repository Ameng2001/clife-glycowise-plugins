#!/usr/bin/env python3
"""标注回传验收：按 labeling.round6.brief.md「交付与验收」逐项检查 feedback.yaml。

用法：python3 check_feedback.py --window 2026-W47 [--window 2026-W48 ...]
退出码 0 = 全部通过；1 = 有不合格条目（逐条列出，退回补）。
检查项：YAML 可解析；status: reviewed；文件头 reviewer / labeled_at 非空；每条 label ∈ {correct, partial, wrong}；
每条 truth 非空；wrong 的 truth_expect 非空且格式为 query / action(名) / rejected(规则名)；
已有字段（utterance / engine_actual / cq_expect / suggested）与 draft 时一致（对照 audit.jsonl 的 trace_id 集合：不多不少不改序）。
告警（不算失败）：wrong 没填 layer（rule / router / seed，归因报告按它分组）；label 与 suggested 完全一致（提醒 reviewer 不是抄的）。
"""
import argparse, json, re, sys
from pathlib import Path
import yaml

HERE = Path(__file__).resolve().parent
EXPECT_RE = re.compile(r"^(query|action\([^()\s]+\)|rejected\([^()\s]+\))$")
LABELS = {"correct", "partial", "wrong"}

def check(window: str) -> tuple[list[str], list[str]]:
    errs, warns = [], []
    p = HERE / "trajectories" / window / "feedback.yaml"
    try:
        fb = yaml.safe_load(p.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        return [f"YAML 不可解析：{e}"], []
    if fb.get("status") != "reviewed":
        errs.append(f"status={fb.get('status')!r}，应为 reviewed")
    if not (fb.get("reviewer") or {}).get("id"):
        errs.append("文件头 reviewer 为空")
    if not fb.get("labeled_at"):
        errs.append("文件头 labeled_at 为空")
    items = fb.get("items") or []
    # 与轨迹对照：不多不少不改序
    traj = [json.loads(l)["trace_id"] for l in (HERE / "trajectories" / window / "audit.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    got = [i.get("trace_id") for i in items]
    if got != traj:
        errs.append(f"条目与 audit.jsonl 不一致：轨迹 {len(traj)} 条 / 反馈 {len(got)} 条" + ("" if set(got) == set(traj) else f"，缺 {sorted(set(traj)-set(got))[:5]} 多 {sorted(set(got)-set(traj))[:5]}") + ("（顺序被改）" if set(got) == set(traj) else ""))
    same_as_suggested = 0; n_sugg = 0
    for i in items:
        tid = i.get("trace_id")
        lab = i.get("label")
        if lab not in LABELS:
            errs.append(f"{tid}: label={lab!r}，应为 correct / partial / wrong"); continue
        if not (i.get("truth") or "").strip():
            errs.append(f"{tid}: truth 为空")
        te = i.get("truth_expect")
        if lab == "wrong":
            if not te:
                errs.append(f"{tid}: wrong 但 truth_expect 为空")
            elif not EXPECT_RE.match(str(te).strip()):
                errs.append(f"{tid}: truth_expect={te!r} 格式不对，应为 query / action(动作名) / rejected(规则名)")
            elif str(te).strip() == "rejected" or str(te).strip() == "rejected()":
                errs.append(f"{tid}: rejected 要写到规则名")
            if not i.get("layer"):
                warns.append(f"{tid}: wrong 没填 layer（rule / router / seed）")
        if not (i.get("reviewer") or {}).get("id") and not (fb.get("reviewer") or {}).get("id"):
            errs.append(f"{tid}: reviewer 为空且文件头也没有")
        if i.get("suggested"):
            n_sugg += 1
            if i.get("suggested") == lab:
                same_as_suggested += 1
    if n_sugg and same_as_suggested == n_sugg and n_sugg >= 10:
        warns.append(f"{n_sugg} 条 label 与 suggested 完全一致——请 reviewer 确认不是抄的")
    return errs, warns

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--window", action="append", required=True)
    a = ap.parse_args(); bad = False
    for w in a.window:
        errs, warns = check(w)
        if errs:
            bad = True
            print(f"✗ {w}: {len(errs)} 项不合格"); [print("   ", e) for e in errs[:40]]
            if len(errs) > 40: print(f"    …还有 {len(errs)-40} 项")
        else:
            print(f"✓ {w}: 验收通过")
        for wn in warns[:20]: print("   ⚠", wn)
    sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main()
