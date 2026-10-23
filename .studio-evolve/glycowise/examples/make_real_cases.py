#!/usr/bin/env python3
"""把 ① audit.jsonl + ② feedback.yaml 落成 ②' cases/real/{family}-{n}.yaml（evolve-attribute 第 1 步的样例实现）。

用法：python3 make_real_cases.py [--window 2026-W44] [--out ../cases/real] [--dry-run]

规则（与 examples/README.md 一致）：
  * 只处理有反馈的轨迹；partial 不落案例（只用于成本统计）。
  * expect：correct → 引擎实际裁决（ask→query；committed/pending_hil→action(名)；rejected→rejected(首条 violate 规则)）
            wrong   → 反馈里的 truth_expect（真实应有的裁决）
  * tier：query=1，多跳（oql 带 traverse）=2，action/rejected=3，pending_hil=4
  * family：按动作 / 规则 / 查询起点映射到仿真库的 10 个 family（可被反馈项的 family 字段覆盖）
  * 幂等：已存在且 label.trace_id 相同的案例原样保留，新轨迹按 family 顺延编号。
"""
import argparse, glob, json, os, re, sys
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
FAMILIES = ["指标口径", "参考与配置", "因果链溯源", "低血糖安全", "高血糖与波动", "结论层与分层", "缓解路径", "出口签发闸", "产品与机构合规", "数据与同意合规"]

# 决策点 → family。先按规则（更具体），再按动作，最后按查询起点对象。
RULE_FAMILY = {
    "R35": "高血糖与波动", "R42": "结论层与分层", "R01": "结论层与分层", "R18": "结论层与分层", "R51": "结论层与分层",
    "R29": "缓解路径", "R30": "缓解路径", "R33": "缓解路径", "R17": "缓解路径",
    "D11a": "出口签发闸", "D12": "出口签发闸", "D13": "出口签发闸", "C22": "出口签发闸", "C9": "出口签发闸",
    "D9": "产品与机构合规", "D8": "产品与机构合规", "C13": "产品与机构合规", "C16": "产品与机构合规", "R32": "产品与机构合规", "R54": "产品与机构合规", "C1": "产品与机构合规",
    "C3": "数据与同意合规", "R48": "数据与同意合规", "C21": "数据与同意合规",
    "R44": "低血糖安全", "R03a": "低血糖安全", "R04a": "低血糖安全", "R52": "低血糖安全", "R53": "低血糖安全", "R58": "低血糖安全", "R34": "低血糖安全",
    "R46": "参考与配置", "R56": "参考与配置",
}
ACTION_FAMILY = {
    "触发低血糖处置": "低血糖安全", "响应并回执告警": "低血糖安全", "转介医师": "低血糖安全",
    "生成方案草稿": "高血糖与波动", "生成去强化证据工单": "高血糖与波动",
    "签发方案": "出口签发闸", "输出服务分层标签": "结论层与分层", "判定缓解结果": "缓解路径",
    "收紧告警阈值": "参考与配置",
    "发布宣传素材": "产品与机构合规", "创建服务包SKU": "产品与机构合规", "生成产品推荐": "产品与机构合规", "上架产品SKU": "产品与机构合规",
    "摄入读数": "数据与同意合规", "撤回同意": "数据与同意合规", "处理数据主体权利请求": "数据与同意合规",
}
OBJECT_FAMILY = {
    "CgmSummary": "指标口径", "AlertThreshold": "参考与配置", "PatientProfile": "参考与配置", "DeviceModel": "参考与配置",
    "AlertEvent": "因果链溯源", "HypoEpisode": "低血糖安全", "GlucoseReading": "指标口径", "PlanSigned": "出口签发闸", "ReviewEvidence": "出口签发闸",
}
EVIDENCE_OBJECT = {  # evidence 里出现的键 → 本体对象（elements 用）
    "summary_id": "CgmSummary", "reading_id": "GlucoseReading", "alert_id": "AlertEvent", "draft_id": "PlanDraft", "plan_id": "PlanSigned",
    "credential_id": "Credential", "consent_records": "ConsentRecord", "lab_result_id": "LabResult", "remission_clock": "RemissionClock",
    "threshold_id": "AlertThreshold", "log_id": "ThresholdChangeLog", "content_id": "OutboundContent", "package_id": "ServicePackage",
    "event_id": "ClinicalContextEvent", "record_id": "SymptomTreatmentRecord", "referral_id": "ReferralRecord",
    "hypo_state": "HypoState", "med_class_hint": "MedClassHint", "dedup_key": "GlucoseReading",
}
PATIENT_NAMES = {"P0012": "刘阿姨", "P0031": "王叔", "P0007": "周先生", "P0023": "陈阿姨", "P0088": "李女士", "P0045": "黄伯", "P0066": "张阿姨", "P0099": "新客"}
RULE_RE = re.compile(r"^([A-Z]+\d+[a-z]?)_")


def rule_prefix(name):
    m = RULE_RE.match(name)
    return m.group(1) if m else name


def patient_of(t):
    s = json.dumps(t, ensure_ascii=False)
    m = re.search(r"P00\d\d", s)
    return m.group(0) if m else None


def family_of(t, fb, expect_rule):
    if fb.get("family"):
        return fb["family"]
    if expect_rule and rule_prefix(expect_rule) in RULE_FAMILY:
        return RULE_FAMILY[rule_prefix(expect_rule)]
    if t["kind"] == "execute" and t["action"] in ACTION_FAMILY:
        return ACTION_FAMILY[t["action"]]
    if t["kind"] == "ask":
        if t["oql"].get("traverse"):
            return "因果链溯源"
        return OBJECT_FAMILY.get(t["oql"]["start"], "指标口径")
    return "指标口径"


def expect_of(t, fb):
    """返回 (expect 字符串, 期望规则名或 None)。"""
    if fb["label"] == "wrong":
        e = fb["truth_expect"]
        m = re.match(r"rejected\((.+)\)", e)
        return e, (m.group(1) if m else None)
    if t["kind"] == "ask":
        return "query", None
    if t["decision"] == "rejected":
        viol = [r["rule"] for r in t["rules_evaluated"] if r["result"] == "violate"]
        return f"rejected({viol[0]})", viol[0]
    return f"action({t['action']})", None


def tier_of(t, expect):
    if expect == "query":
        return 2 if t["oql"].get("traverse") else 1
    if t["kind"] == "execute" and t["decision"] == "pending_hil" and not expect.startswith("rejected"):
        return 4
    return 3


def elements_of(t, expect_rule):
    els = []
    if t["kind"] == "execute":
        els.append(t["action"])
        if expect_rule:
            els.append(expect_rule)
        for e in t.get("evidence", []):
            for k in e:
                if k in EVIDENCE_OBJECT and EVIDENCE_OBJECT[k] not in els:
                    els.append(EVIDENCE_OBJECT[k])
    else:
        els.append(t["oql"]["start"])
        for tr in t["oql"].get("traverse", []):
            els += [tr["link"], tr["to"]]
    return els


def q_with_id(t):
    """案例 q 带对象 id（与 golden 口径一致）：口语里有患者称呼但没 id 时补上。"""
    q = t["utterance"]
    pid = patient_of(t)
    if pid and pid not in q:
        name = PATIENT_NAMES.get(pid)
        if name and name in q:
            q = q.replace(name, f"{name}（{pid}）", 1)
        else:
            q = f"{q}（患者 {pid}）"
    return q


def variants_of(t, q):
    out = []
    pid = patient_of(t)
    name = PATIENT_NAMES.get(pid or "")
    if name and name in q:
        # 同义改写：把称呼换成患者 id（口语里已带 id 的直接去掉称呼）
        para = q.replace(f"{name}（{pid}）", pid, 1) if f"{name}（{pid}）" in q else q.replace(name, f"患者 {pid}", 1)
        out.append({"q": para, "kind": "paraphrase"})
    if t["kind"] == "execute":
        out.append({"q": q + "；家属说他最近睡得还行。", "kind": "irrelevant_field"})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--window", default="2026-W44")
    ap.add_argument("--traj-dir", default=os.path.join(HERE, "trajectories"))
    ap.add_argument("--out", default=os.path.join(HERE, "cases", "real"))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    wdir = os.path.join(a.traj_dir, a.window)
    traj = {}
    for line in open(os.path.join(wdir, "audit.jsonl"), encoding="utf-8"):
        if line.strip():
            t = json.loads(line)
            traj[t["trace_id"]] = t
    fb = yaml.safe_load(open(os.path.join(wdir, "feedback.yaml"), encoding="utf-8"))
    default_reviewer = fb.get("reviewer", {}).get("id")

    # 已有案例：trace_id → 文件；family → 已用最大编号
    existing, maxn = {}, {f: 0 for f in FAMILIES}
    for p in glob.glob(os.path.join(a.out, "*.yaml")):
        c = yaml.safe_load(open(p, encoding="utf-8"))
        tid = (c.get("label") or {}).get("trace_id")
        if tid:
            existing[tid] = p
        m = re.match(r"(.+)-(\d+)$", c["id"])
        if m and m.group(1) in maxn:
            maxn[m.group(1)] = max(maxn[m.group(1)], int(m.group(2)))

    stats = {"kept": 0, "new": 0, "skipped_partial": 0, "no_trajectory": 0}
    for item in fb["items"]:
        tid = item["trace_id"]
        if tid not in traj:
            stats["no_trajectory"] += 1
            print(f"  ! {tid}: 反馈有、轨迹无，跳过", file=sys.stderr)
            continue
        if item["label"] == "partial":
            stats["skipped_partial"] += 1
            continue
        if tid in existing:
            stats["kept"] += 1
            continue
        t = traj[tid]
        expect, expect_rule = expect_of(t, item)
        fam = family_of(t, item, expect_rule)
        maxn[fam] += 1
        q = q_with_id(t)
        case = {
            "id": f"{fam}-{maxn[fam]:02d}",
            "q": q,
            "expect": expect,
            "tier": tier_of(t, expect),
            "family": fam,
            "origin": "real",
            "observed_at": t["ts"][:10],
            "elements": elements_of(t, expect_rule),
            "label": {
                "answer": item["truth"],
                "source": "feedback",
                "trace_id": tid,
                "reviewer": (item.get("reviewer") or {}).get("id", default_reviewer),
                "feedback_label": item["label"],
            },
            "variants": variants_of(t, q),
        }
        path = os.path.join(a.out, case["id"] + ".yaml")
        stats["new"] += 1
        if a.dry_run:
            print(f"  + {case['id']}  {expect}  tier {case['tier']}  ← {tid}")
            continue
        os.makedirs(a.out, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# 由 {tid} + 反馈（{item['label']}）自动落成的真实案例（evolve-attribute 第 1 步产出；外关卡留出集的唯一来源）\n")
            yaml.safe_dump(case, f, allow_unicode=True, sort_keys=False, width=200)
    print(f"window {a.window}: 新增 {stats['new']} · 已存在保留 {stats['kept']} · partial 不落 {stats['skipped_partial']} · 无轨迹 {stats['no_trajectory']}")


if __name__ == "__main__":
    main()
