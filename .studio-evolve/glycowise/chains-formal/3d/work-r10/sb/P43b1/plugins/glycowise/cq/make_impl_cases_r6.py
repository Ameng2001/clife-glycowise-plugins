"""round 6（W47）的实现缺失提案 P12 / P13 的来源案例（Dᵢ）：真实窗口 W47 非轨迹里第一次被路由到的两个桩动作——
确认缓解时钟Day0（0021）、撤销更正已发出告警（0075）。

编号说明：P9 的三份修法在 verdict / 台账里已占用 proposal 9 / 10 / 11（P9a / P9b / P9c），所以这两条从 P12 起编。

口语是给这两个动作补的 CQ（IR §7 此前没有覆盖）；生产插件 h_i 上 handler 抛 NotImplementedError（runner 记 IMPL_MISSING、判不过），
沙箱 h' 上按 IR §5 的声明裁决。路由 manual（CQ 原句 + 变体 → 同一意图），写进 cq/impl_routes_r6.json 并并入 all_routes.json。
expect_state 的真值只从 IR 推：RemissionClock.status 由 gated_by_meds 决定（任一降糖药在用即清零 → reset，否则 running）；
AlertEvent 撤销后 lifecycle 进 retracted。

    python cq/make_impl_cases_r6.py --out-cases ../../.studio-evolve/glycowise/cases/sim --out-routes cq/impl_routes_r6.json --out-sets ../../.studio-evolve/glycowise/sets
"""
import argparse, datetime as dt, json, re
from pathlib import Path

TODAY = dt.date.today().isoformat()
CONF = 0.95
PROPOSALS = {}


def a_(action, **params):
    return {"kind": "action", "confidence": CONF, "action": action, "params": params}


def case(prop, cid, fam, tier, expect, q, elements, answer, route, variants, note, expect_state=None, state_note=None):
    PROPOSALS.setdefault(prop, []).append(cid)
    d = {"id": cid, "q": q, "expect": expect, "tier": tier, "family": fam, "origin": "sim", "observed_at": TODAY,
         "elements": list(elements), "label": {"answer": answer, "source": "cq+expert"},
         "variants": [{"kind": k, "q": vq} for k, vq in variants], "note": note, "_route": route}
    if expect_state:
        d["expect_state"] = expect_state
        d["expect_state_note"] = state_note
    return d


def build(next_id):
    out = []
    # ---- P12：确认缓解时钟Day0（IR §5：医师另行确认，系统不得自动推断；writes RemissionClock；HIL 医师 always；无 guard / post 规则）
    r = a_("确认缓解时钟Day0", patient_id="P0007", day0="2026-07-28")
    out.append(case("P12", next_id("缓解路径"), "缓解路径", 3, "action(确认缓解时钟Day0)",
                    "给周先生（P0007）把缓解时钟的 Day0 确认在 2026 年 7 月 28 日",
                    ["确认缓解时钟Day0", "RemissionClock", "gated_by_meds"],
                    "P0007 无降糖药在用（profile.meds 空），医师确认 Day0 → RemissionClock day0 改写为 2026-07-28、status running、confirmed_by 为确认人，进 HIL（医师 always）；h_i 的 handler 是桩", r,
                    [("paraphrase", "P0007 的缓解时钟 Day0 定 2026-07-28，医师确认。"),
                     ("irrelevant_field", "给周先生（P0007）把缓解时钟的 Day0 确认在 2026 年 7 月 28 日，他说那天刚好是生日。")],
                    "P12 来源案例：W47 0021 路由到只有桩的动作",
                    [{"type": "RemissionClock", "key": "P0007", "fields": {"day0": "2026-07-28", "status": "running"}}],
                    "IR §1 RemissionClock{day0,status}；§2 gated_by_meds：任一降糖药在用即清零，P0007 meds=[] → running"))
    r = a_("确认缓解时钟Day0", patient_id="P0066", day0="2026-10-01")
    out.append(case("P12", next_id("缓解路径"), "缓解路径", 3, "action(确认缓解时钟Day0)",
                    "张阿姨（P0066）停药满期了，医师确认缓解时钟 Day0 为 2026 年 10 月 1 日，启动缓解观察",
                    ["确认缓解时钟Day0", "RemissionClock"],
                    "P0066 此前没有 RemissionClock、meds 空 → 新建时钟 day0 2026-10-01、status running，进 HIL（医师）", r,
                    [("paraphrase", "P0066 缓解时钟 Day0 = 2026-10-01，启动。"),
                     ("irrelevant_field", "张阿姨（P0066）停药满期了，医师确认缓解时钟 Day0 为 2026 年 10 月 1 日，启动缓解观察；她女儿陪着来的。")],
                    "P12 来源案例：无既有时钟的患者",
                    [{"type": "RemissionClock", "key": "P0066", "fields": {"day0": "2026-10-01", "status": "running"}}],
                    "同上；P0066 无既有 RemissionClock，seed 事实"))
    r = a_("确认缓解时钟Day0", patient_id="P0012", day0="2026-09-15")
    out.append(case("P12", next_id("缓解路径"), "缓解路径", 3, "action(确认缓解时钟Day0)",
                    "医师给刘阿姨（P0012）确认缓解时钟 Day0 为 2026 年 9 月 15 日",
                    ["确认缓解时钟Day0", "RemissionClock", "gated_by_meds", "PatientProfile"],
                    "P0012 仍在用二甲双胍（profile.meds）→ 按 §2 gated_by_meds「任一降糖药在用即清零」，时钟落为 status reset（day0 照记、confirmed_by 照记），进 HIL 由医师定夺；不是拒绝——IR 没有把它声明成规则", r,
                    [("paraphrase", "P0012 的缓解时钟 Day0 确认为 2026-09-15。"),
                     ("irrelevant_field", "医师给刘阿姨（P0012）确认缓解时钟 Day0 为 2026 年 9 月 15 日；她问要不要换个传感器。")],
                    "P12 来源案例：gated_by_meds 分支",
                    [{"type": "RemissionClock", "key": "P0012", "fields": {"day0": "2026-09-15", "status": "reset"}}],
                    "§2 gated_by_meds：P0012 meds=[二甲双胍]（seed）→ reset"))
    # ---- P13：撤销更正已发出告警（IR §5：上游读数被 retract 或 corrected 时撤销并发更正说明；writes AlertEvent, PlanSigned；HIL 触及已签发方案时转签发人）
    r = a_("撤销更正已发出告警", alert_id="A-P0045-02", reason="厂商将对应读数标为传感器压迫伪差并撤回")
    out.append(case("P13", next_id("因果链溯源"), "因果链溯源", 3, "action(撤销更正已发出告警)",
                    "黄伯（P0045）凌晨那条告警 A-P0045-02 对应的读数被厂商标为传感器压迫伪差撤回了，撤销这条告警并发更正说明",
                    ["撤销更正已发出告警", "AlertEvent", "R02_传感器压迫伪差识别"],
                    "A-P0045-02 存在（seed，Level2 实时告警）→ AlertEvent 进 retracted，带撤销原因与更正说明；P0045 的已签发方案 plan-P0045-w41 签发在告警之前，不受触及 → 不写 PlanSigned、不进签发人 HIL，committed", r,
                    [("paraphrase", "A-P0045-02 的读数被撤回了，撤销告警并更正。"),
                     ("irrelevant_field", "黄伯（P0045）凌晨那条告警 A-P0045-02 对应的读数被厂商标为传感器压迫伪差撤回了，撤销这条告警并发更正说明；他女儿早上打电话来问过。")],
                    "P13 来源案例：W47 0075 路由到只有桩的动作（0075 原句「复测 4.1 了把告警关掉」更像回执闭环，归路由层候选；本案例按动作的 IR 语义重写）",
                    [{"type": "AlertEvent", "key": "A-P0045-02", "fields": {"status": "retracted"}}],
                    "IR §1 AlertEvent lifecycle 含 retracted；plan-P0045-w41 signed_at = 5 天前 < raised_at 1 天前（seed）"))
    r = a_("撤销更正已发出告警", alert_id="A-P0031-backfill-01", reason="回填批次读数经核对为错误批次，已更正")
    out.append(case("P13", next_id("因果链溯源"), "因果链溯源", 3, "action(撤销更正已发出告警)",
                    "王叔（P0031）那条回填告警 A-P0031-backfill-01 的读数核对下来是错误批次、已更正，撤销告警并发更正说明",
                    ["撤销更正已发出告警", "AlertEvent", "IngestBatch"],
                    "回填告警（is_backfill）撤销 → retracted；P0031 无已签发方案 → 只写 AlertEvent，committed", r,
                    [("paraphrase", "A-P0031-backfill-01 读数更正了，撤销这条回填告警。"),
                     ("irrelevant_field", "王叔（P0031）那条回填告警 A-P0031-backfill-01 的读数核对下来是错误批次、已更正，撤销告警并发更正说明；他下周去儿子家住。")],
                    "P13 来源案例：回填告警撤销",
                    [{"type": "AlertEvent", "key": "A-P0031-backfill-01", "fields": {"status": "retracted"}}],
                    "同上；P0031 无 PlanSigned（seed）"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-cases", required=True, type=Path)
    ap.add_argument("--out-routes", required=True, type=Path)
    ap.add_argument("--out-sets", type=Path, default=None)
    a = ap.parse_args()
    import yaml
    a.out_cases.mkdir(parents=True, exist_ok=True)
    counters = {}
    for f in a.out_cases.glob("*.yaml"):
        m = re.match(r"(.+)-(\d+)$", f.stem)
        if m:
            counters[m.group(1)] = max(counters.get(m.group(1), 0), int(m.group(2)))

    def next_id(fam):
        counters[fam] = counters.get(fam, 0) + 1
        return f"{fam}-{counters[fam]:02d}"
    docs = build(next_id)
    routes = {}
    for d in docs:
        route = d.pop("_route"); routes[d["q"]] = route
        for v in d["variants"]:
            routes[v["q"]] = route
        (a.out_cases / f"{d['id']}.yaml").write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False), encoding="utf-8")
    a.out_routes.write_text(json.dumps(routes, ensure_ascii=False, indent=1), encoding="utf-8")
    if a.out_sets:
        for p, ids in PROPOSALS.items():
            (a.out_sets / f"{p}-Di.yaml").write_text(yaml.safe_dump({"ids": ids}, allow_unicode=True), encoding="utf-8")
    print(f"写出 {len(docs)} 条提案来源案例 · 路由 {len(routes)} · " + " · ".join(f"{p}: {ids}" for p, ids in PROPOSALS.items()))


if __name__ == "__main__":
    main()
