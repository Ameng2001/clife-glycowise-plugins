"""提案 P2–P4 的来源案例（Dᵢ）：专家抽检记下的四个实现缺口候选，按现实口径写标签。

这些案例在生产插件 h_i 上**应当失败**（引擎裁决与临床/IR 口径相反），在沙箱 h' 上应当通过；
它们是 evolve-verify 内关卡的来源案例，不进 simulate-report 的"全过"统计。

    python cq/make_proposal_cases.py --out-cases ../../.studio-evolve/glycowise/cases/sim --out-routes cq/proposal_routes.json
"""
import argparse, datetime as dt, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TODAY = dt.date.today().isoformat()
CONF = 0.95


def a_(action, **params):
    return {"kind": "action", "confidence": CONF, "action": action, "params": params}


def _clean_rows(store):
    by = {}
    for item in store.iter_objects("GlucoseReading"):
        r = item[-1]
        if r.get("source_channel") == "vendor_api" and not r.get("is_backfill") and r.get("quality_flag") in (None, "clean"):
            by.setdefault(r["patient_id"], []).append(r)
    for rows in by.values():
        rows.sort(key=lambda x: x["time_utc"])
    return by


def resolve_l1_falling(store):
    """3.0≤g<3.9 且前值也在 [3.0,3.9) 且下降：R04a 已确认，但 h_i 的 R05 会要求「预测」证据而拒。"""
    for pid, rows in _clean_rows(store).items():
        for i in range(1, len(rows)):
            g, p = rows[i].get("value_mmol"), rows[i - 1].get("value_mmol")
            if g is not None and p is not None and 3.0 <= g < 3.9 and 3.0 <= p < 3.9 and p > g:
                return pid, rows[i]["reading_id"], g, p
    return None


PROPOSALS = {}  # proposal -> [case ids]


def case(prop, cid, fam, tier, expect, q, elements, answer, route, variants, note):
    PROPOSALS.setdefault(prop, []).append(cid)
    return {"id": cid, "q": q, "expect": expect, "tier": tier, "family": fam, "origin": "sim", "observed_at": TODAY,
            "elements": list(elements), "label": {"answer": answer, "source": "simulate+expert"},
            "variants": [{"kind": k, "q": vq} for k, vq in variants], "note": note, "_route": route}


def build(store):
    out = []
    # ---- P2：R05 只应在 G ≥ 3.9 时评估（已低于 3.9 的由 R03a/R04a 管）
    r = a_("触发低血糖处置", patient_id="P0045", reading_id="r-P0045-01162", rule_id="R03a_Level2低血糖_实时告警")
    out.append(case("P2", "低血糖安全-11", "低血糖安全", 3, "action(触发低血糖处置)",
                    "黄伯（P0045）读数 r-P0045-01162 是 2.7，前一读数 2.8，连续两读数 <3.0，按 R03a 触发 Level 2 低血糖处置",
                    ["触发低血糖处置", "R03a_Level2低血糖_实时告警", "R05_即将低血糖预测告警"],
                    "连续 2 读数 G<3.0 已确认，应 committed；h_i 被 R05 以「缺预测证据」拒（IR：R05 是提前 10–30 分钟的预测性告警，G 已 <3.9 时不适用）", r,
                    [("paraphrase", "P0045 的 r-P0045-01162（2.7，前值 2.8）触发二级低血糖处置。"),
                     ("irrelevant_field", "黄伯（P0045）读数 r-P0045-01162 是 2.7，前一读数 2.8，连续两读数 <3.0，按 R03a 触发 Level 2 低血糖处置；他今早没吃早饭。")],
                    "P2 来源案例：专家抽检「R03a 通过分支受 R05 实现制约」"))
    dyn = resolve_l1_falling(store)
    if dyn:
        pid, rid, g, p = dyn
        r = a_("触发低血糖处置", patient_id=pid, reading_id=rid, rule_id="R04a_Level1低血糖_实时告警")
        out.append(case("P2", "低血糖安全-12", "低血糖安全", 3, "action(触发低血糖处置)",
                        f"患者 {pid} 读数 {rid} 是 {g}，前一读数 {p}，连续两读数在 3.0–3.9 且在下降，按 R04a 触发 Level 1 低血糖处置",
                        ["触发低血糖处置", "R04a_Level1低血糖_实时告警", "R05_即将低血糖预测告警"],
                        "连续 2 读数 3.0≤G<3.9 已确认，应 committed；h_i 被 R05 拒（下降段触发预测分支）", r,
                        [("paraphrase", f"{pid} 的 {rid}（{g}，前值 {p}）触发一级低血糖处置。"),
                         ("irrelevant_field", f"患者 {pid} 读数 {rid} 是 {g}，前一读数 {p}，连续两读数在 3.0–3.9 且在下降，按 R04a 触发 Level 1 低血糖处置；他刚散完步。")],
                        "P2 来源案例：下降段的 L1 确认触发"))
    # ---- P3：R49 的 IR 语义是「按最保守执行并置 population_params_stale」，不是拒绝
    r = a_("生成方案草稿", patient_id="P0099", analysis_result={}, direction="维持")
    out.append(case("P3", "参考与配置-12", "参考与配置", 3, "action(生成方案草稿)",
                    "给新客（P0099）生成一份维持方向的方案草稿", ["生成方案草稿", "R49_缺参数时按最保守执行"],
                    "P0099 无画像，人群参数缺失 → 按最保守（老年/高危）参数执行并置 population_params_stale，committed（advisory 里带 R49）", r,
                    [("paraphrase", "P0099 出维持方向草稿。"), ("irrelevant_field", "给新客（P0099）生成一份维持方向的方案草稿，他是今天刚到店的。")],
                    "P3 来源案例：专家抽检「R49 不是拒绝条件」"))
    # 参考与配置-13（计算窗口指标 P0099）已删：h_i 与 h' 都 ENGINE_ERROR:TypeError（无画像时某前置规则 None<int），是另一个实现缺口，记为 P5 候选
    r = None  # noqa
    #     out.append(case("P3", "参考与配置-13", "参考与配置", 3, "action(计算窗口指标)",
    #                     "给新客（P0099）算一下最近 14 天的窗口指标", ["计算窗口指标", "R49_缺参数时按最保守执行"],
    #                     "同上：缺人群参数时按最保守阈值算并标 stale，不拒绝", r,
    #                     [("paraphrase", "算 P0099 的 14 天指标。"), ("irrelevant_field", "给新客（P0099）算一下最近 14 天的窗口指标，他用的是进口传感器。")],
    #                     "P3 来源案例"))

    # ---- P4：C19 的关键词正则把「异常转介」当越界
    r = a_("群内答复患者", patient_id="P0012", message="建议您去医院开处方调整一下。", sender_role="健管师")
    out.append(case("P4", "结论层与分层-09", "结论层与分层", 3, "action(群内答复患者)",
                    "健管师在刘阿姨（P0012）群里答复：建议您去医院开处方调整一下", ["群内答复患者", "C19_线上随访边界"],
                    "「建议去医院」属异常转介，在健康管理随访允许范围内，committed；h_i 的 C19 关键词「处方」误拒", r,
                    [("paraphrase", "健管师在 P0012 群里让她去医院开处方调整。"), ("irrelevant_field", "健管师在刘阿姨（P0012）群里答复：建议您去医院开处方调整一下；医院离她家两公里。")],
                    "P4 来源案例：专家抽检「C19 误拦异常转介」"))
    r = a_("群内答复患者", patient_id="P0031", message="这周波动比较大，建议您尽快找医生看看要不要调药方案。", sender_role="健管师")
    out.append(case("P4", "结论层与分层-10", "结论层与分层", 3, "action(群内答复患者)",
                    "健管师在王叔（P0031）群里答复：这周波动比较大，建议您尽快找医生看看要不要调药方案", ["群内答复患者", "C19_线上随访边界"],
                    "转介给医生而非自行调药，属允许范围，committed；h_i 的 C19 关键词「调药方案」误拒", r,
                    [("paraphrase", "健管师让 P0031 去找医生看是否调药方案。"), ("irrelevant_field", "健管师在王叔（P0031）群里答复：这周波动比较大，建议您尽快找医生看看要不要调药方案；他女儿明天陪他去。")],
                    "P4 来源案例"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-cases", required=True, type=Path)
    ap.add_argument("--out-routes", required=True, type=Path)
    ap.add_argument("--out-sets", type=Path, default=None, help="每份提案的 Dᵢ 清单目录（{P}-Di.yaml）")
    ap.add_argument("--engine-root", type=Path, default=Path("/Users/liuyameng/Codes/onto-fundary-plugins"))
    ap.add_argument("--evolve-scripts", type=Path, default=Path("/Users/liuyameng/Codes/astra-studio-plugins/studio-evolve/scripts"))
    a = ap.parse_args()
    sys.path.insert(0, str(a.engine_root)); sys.path.insert(0, str(a.evolve_scripts)); sys.argv = ["x"]
    import runner_onto_engine as R  # noqa
    from clife_onto_engine.query import InMemoryStore
    import yaml
    plugin = R.load_plugin(HERE.parent); store = InMemoryStore(); plugin.seed_reference_data(store)
    docs = build(store)
    a.out_cases.mkdir(parents=True, exist_ok=True); routes = {}
    for d in docs:
        route = d.pop("_route"); routes[d["q"]] = route
        for v in d["variants"]:
            routes[v["q"]] = route
        (a.out_cases / f"{d['id']}.yaml").write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False), encoding="utf-8")
    a.out_routes.write_text(json.dumps(routes, ensure_ascii=False, indent=1), encoding="utf-8")
    if a.out_sets:
        a.out_sets.mkdir(parents=True, exist_ok=True)
        for p, ids in PROPOSALS.items():
            (a.out_sets / f"{p}-Di.yaml").write_text(yaml.safe_dump({"ids": ids}, allow_unicode=True), encoding="utf-8")
    print(f"写出 {len(docs)} 条提案来源案例 · 路由 {len(routes)} · " + " · ".join(f"{p}: {ids}" for p, ids in PROPOSALS.items()))


if __name__ == "__main__":
    main()
