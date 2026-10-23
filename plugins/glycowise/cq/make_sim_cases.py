#!/usr/bin/env python3
"""make_sim_cases.py —— 从 glycowise IR 派生仿真案例（evolve-simulate），连同人工转录路由一起写出。

  python3 cq/make_sim_cases.py --out-cases ../../.studio-evolve/glycowise/cases/sim --out-routes cq/sim_routes.json

派生规则（skills/evolve-simulate）：hard 规则 → rejected(R) tier 3；动作 → action(X) tier 3；
root_cause / derivation 关系 → 跨对象 query tier 2；函数 → query tier 1。实参只用 `_fde.seed_reference_data`
里真实存在的 id；标签算不出或 seed 里没有触发条件的规则列在 SKIPPED。每条案例 2–3 个扰动变体
（paraphrase / entity_swap / irrelevant_field），变体与原题共用标签；entity_swap 的路由随实体替换。

路由是 IntentCompiler 的原始 JSON（kind=query 的 oql 只用单起点 where 过滤——seed 没有 put_link，
steps 多跳在内存库上恒为 0 行；跨对象推理由 q 的措辞承担，tier 2 的"多跳"指案例需要跨关系才能答）。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TODAY = "2026-10-23"
CONF = 0.95


def q_(start, where, select, limit=None):
    oql = {"start": start, "where": [{"field": f, "op": o, "value": v} for f, o, v in where], "select": list(select)}
    if limit:
        oql["limit"] = limit
    return {"kind": "query", "confidence": CONF, "oql": oql}


def a_(action, **params):
    return {"kind": "action", "confidence": CONF, "action": action, "params": params}


CASES: list[dict] = []


def case(fam, tier, expect, q, elements, answer, route, variants=(), note=""):
    """variants: [(kind, q, route_or_None)]"""
    CASES.append({"family": fam, "tier": tier, "expect": expect, "q": q, "elements": list(elements), "answer": answer,
                  "route": route, "variants": [(k, vq, vr) for k, vq, vr in variants], "note": note})


def para(q, route=None):
    return ("paraphrase", q, route)


def irr(q, route=None):
    return ("irrelevant_field", q, route)


def swap(q, route):
    return ("entity_swap", q, route)


# ============================================================================ 指标口径（§3 函数 → tier 1 query）
F = "指标口径"
case(F, 1, "query", "黄伯（患者 P0045）最近 14 天高于 10 和高于 13.9 的时间占比各是多少？", ["TAR_L1", "TAR_L2", "CgmSummary"],
     "s-P0045-14d：tar_pct 37.1、tar_l2_pct 3.1（老年 TAR>13.9 上限 10%，未超）",
     q_("CgmSummary", [("patient_id", "eq", "P0045")], ["summary_id", "tar_pct", "tar_l2_pct"]),
     [para("患者 P0045 这两周 TAR 一级和二级分别占多少？"),
      swap("陈阿姨（患者 P0023）最近 14 天高于 10 和高于 13.9 的时间占比各是多少？", q_("CgmSummary", [("patient_id", "eq", "P0023")], ["summary_id", "tar_pct", "tar_l2_pct"])),
      irr("黄伯（患者 P0045）最近 14 天高于 10 和高于 13.9 的时间占比各是多少？他女儿说下周要出差。")])
case(F, 1, "query", "王叔（患者 P0031）这 14 天 TBR 一级和二级（<3.0）各占多少？", ["TBR_L1", "TBR_L2", "CgmSummary"],
     "s-P0031-14d：tbr_pct 4.7、tbr_l2_pct 1.7（老年高危上限 1%，已超）",
     q_("CgmSummary", [("patient_id", "eq", "P0031")], ["summary_id", "tbr_pct", "tbr_l2_pct"]),
     [para("患者 P0031 低于 3.9 和低于 3.0 的时间占比分别是多少？"),
      swap("黄伯（患者 P0045）这 14 天 TBR 一级和二级（<3.0）各占多少？", q_("CgmSummary", [("patient_id", "eq", "P0045")], ["summary_id", "tbr_pct", "tbr_l2_pct"])),
      irr("王叔（患者 P0031）这 14 天 TBR 一级和二级（<3.0）各占多少？另外提醒我下午三点开会。")])
case(F, 1, "query", "陈阿姨（患者 P0023）这两周的平均血糖和变异系数 CV 是多少？", ["MeanGlucose", "CV", "CgmSummary"],
     "s-P0023-14d：mean_glucose 9.81、cv_pct 24.9",
     q_("CgmSummary", [("patient_id", "eq", "P0023")], ["summary_id", "mean_glucose", "cv_pct"]),
     [para("P0023 近 14 天均值血糖多少、波动大不大（CV）？"),
      swap("李女士（患者 P0088）这两周的平均血糖和变异系数 CV 是多少？", q_("CgmSummary", [("patient_id", "eq", "P0088")], ["summary_id", "mean_glucose", "cv_pct"])),
      irr("陈阿姨（患者 P0023）这两周的平均血糖和变异系数 CV 是多少？她家住青秀区。")])
case(F, 1, "query", "黄伯（患者 P0045）14 天报告 s-P0045-14d 的 GMI 是多少？", ["GMI", "CgmSummary"],
     "gmi_pct 7.28",
     q_("CgmSummary", [("summary_id", "eq", "s-P0045-14d")], ["summary_id", "gmi_pct", "mean_glucose"]),
     [para("报告 s-P0045-14d 的血糖管理指标 GMI 读数？"),
      swap("王叔（患者 P0031）14 天报告 s-P0031-14d 的 GMI 是多少？", q_("CgmSummary", [("summary_id", "eq", "s-P0031-14d")], ["summary_id", "gmi_pct", "mean_glucose"])),
      irr("黄伯（患者 P0045）14 天报告 s-P0045-14d 的 GMI 是多少？报告是用 A4 打印的。")])
case(F, 1, "query", "李女士（患者 P0088）戴了几天、有效数据率多少，够不够 14 天 + 70% 的门槛？", ["active_pct", "sufficiency_ok", "CgmSummary"],
     "s-P0088-6d：days 6、active_pct 98.3、sufficiency_ok false",
     q_("CgmSummary", [("patient_id", "eq", "P0088")], ["summary_id", "days", "active_pct", "sufficiency_ok"]),
     [para("P0088 的数据充分性（天数、active%）达标了吗？"),
      swap("周先生（患者 P0007）戴了几天、有效数据率多少，够不够 14 天 + 70% 的门槛？", q_("CgmSummary", [("patient_id", "eq", "P0007")], ["summary_id", "days", "active_pct", "sufficiency_ok"])),
      irr("李女士（患者 P0088）戴了几天、有效数据率多少，够不够 14 天 + 70% 的门槛？她是上周二来的店。")])
case(F, 1, "query", "陈阿姨（患者 P0023）夜间 00–06 点的有效覆盖率是多少？是否标了夜间覆盖不足？", ["nocturnal_coverage_pct", "CgmSummary"],
     "s-P0023-14d：nocturnal_coverage_pct 40.2、nocturnal_coverage_insufficient true",
     q_("CgmSummary", [("patient_id", "eq", "P0023")], ["summary_id", "nocturnal_coverage_pct", "nocturnal_coverage_insufficient"]),
     [para("P0023 夜里的数据覆盖够不够 70%？"),
      swap("王叔（患者 P0031）夜间 00–06 点的有效覆盖率是多少？是否标了夜间覆盖不足？", q_("CgmSummary", [("patient_id", "eq", "P0031")], ["summary_id", "nocturnal_coverage_pct", "nocturnal_coverage_insufficient"])),
      irr("陈阿姨（患者 P0023）夜间 00–06 点的有效覆盖率是多少？是否标了夜间覆盖不足？顺便她问能不能换个颜色的贴片。")])
case(F, 1, "query", "王叔（患者 P0031）连续几晚夜间有效率低于 50%？", ["consecutive_low_night_nights", "nocturnal_coverage_pct", "CgmSummary"],
     "s-P0031-14d：consecutive_low_night_nights 7",
     q_("CgmSummary", [("patient_id", "eq", "P0031")], ["summary_id", "consecutive_low_night_nights", "nocturnal_coverage_pct"]),
     [para("P0031 夜间有效率 <50% 已经连续多少个晚上了？"),
      irr("王叔（患者 P0031）连续几晚夜间有效率低于 50%？他说最近睡得早。")])
case(F, 1, "query", "周先生（患者 P0007）最近 14 天的 TIR 是多少？", ["TIR", "CgmSummary"],
     "s-P0007-14d：tir_pct 97.5",
     q_("CgmSummary", [("patient_id", "eq", "P0007")], ["summary_id", "tir_pct", "days"]),
     [para("P0007 两周目标区间内时间占比多少？"),
      swap("李女士（患者 P0088）最近 14 天的 TIR 是多少？", q_("CgmSummary", [("patient_id", "eq", "P0088")], ["summary_id", "tir_pct", "days"])),
      irr("周先生（患者 P0007）最近 14 天的 TIR 是多少？他下个月要去北京。")])
case(F, 1, "query", "黄伯（患者 P0045）在用哪些药？算不算低血糖高风险用药、是不是无感知低血糖高危？", ["hypo_risk_med", "PatientProfile"],
     "meds [格列齐特]（磺脲，hypo_risk_med true）、is_iah_high_risk true",
     q_("PatientProfile", [("display_name", "eq", "黄伯")], ["display_name", "meds", "is_iah_high_risk", "target_profile"]),
     [para("患者黄伯的用药清单和低血糖风险标记？"),
      swap("王叔（患者 P0031）在用哪些药？算不算低血糖高风险用药、是不是无感知低血糖高危？", q_("PatientProfile", [("display_name", "eq", "王叔")], ["display_name", "meds", "is_iah_high_risk", "target_profile"])),
      irr("黄伯（患者 P0045）在用哪些药？算不算低血糖高风险用药、是不是无感知低血糖高危？他家里养了两只猫。")])
case(F, 1, "query", "我们这边 65 岁以上的患者有哪些？各自按哪套目标人群判？", ["target_profile_of", "PatientProfile"],
     "P0012/P0031/P0023/P0045 → elderly",
     q_("PatientProfile", [("age", "ge", 65)], ["display_name", "age", "target_profile"]),
     [para("列一下老年（≥65）患者和他们的 target_profile。"),
      irr("我们这边 65 岁以上的患者有哪些？各自按哪套目标人群判？今天店里来了个推销的。")])
case(F, 1, "query", "黄伯（患者 P0045）这 14 天有过几次 Level 2（<3.0）低血糖事件？最低到多少？", ["hypo_episode_stats", "HypoEpisode"],
     "HypoEpisode P0045 level L2 若干条，min_value ≈2.6",
     q_("HypoEpisode", [("patient_id", "eq", "P0045"), ("level", "eq", "L2")], ["start_time", "end_time", "min_value", "night_flag"]),
     [para("P0045 的二级低血糖事件列表（起止、最低值）。"),
      swap("王叔（患者 P0031）这 14 天有过几次 Level 2（<3.0）低血糖事件？最低到多少？", q_("HypoEpisode", [("patient_id", "eq", "P0031"), ("level", "eq", "L2")], ["start_time", "end_time", "min_value", "night_flag"])),
      irr("黄伯（患者 P0045）这 14 天有过几次 Level 2（<3.0）低血糖事件？最低到多少？他儿子今天来店里问的。")])
case(F, 1, "query", "李女士（患者 P0088）目前的平均血糖是多少？", ["MeanGlucose", "CgmSummary"],
     "s-P0088-6d：mean_glucose 7.95（仅 6 天，只作趋势）",
     q_("CgmSummary", [("patient_id", "eq", "P0088")], ["summary_id", "mean_glucose", "days"]),
     [para("P0088 的均值血糖读数？"),
      irr("李女士（患者 P0088）目前的平均血糖是多少？她刚换了手机。")])

# ============================================================================ 参考与配置（tier 1 对象查询）
F = "参考与配置"
case(F, 1, "query", "刘阿姨（患者 P0012）的夜间低值告警阈值现在设的是多少？", ["AlertThreshold"],
     "th-P0012-night_low：current_value 3.9",
     q_("AlertThreshold", [("patient_id", "eq", "P0012"), ("field", "eq", "night_low")], ["threshold_id", "current_value", "default_value", "safe_direction"]),
     [para("P0012 的 night_low 阈值当前值？"), irr("刘阿姨（患者 P0012）的夜间低值告警阈值现在设的是多少？她喜欢早上散步。")])
case(F, 1, "query", "危急级告警用的模板是哪条？预审过免责声明和夜间承诺红线了吗？", ["AlertTemplate", "R56_告警模板预审冻结"],
     "tpl-危急：frozen true、pre_reviewed_c22 true、pre_reviewed_r54 true",
     q_("AlertTemplate", [("level", "eq", "危急")], ["template_id", "frozen", "pre_reviewed_c22", "pre_reviewed_r54", "reviewed_at"]),
     [para("查一下「危急」级别的冻结告警模板及其预审状态。"),
      swap("高级告警用的模板是哪条？预审过免责声明和夜间承诺红线了吗？", q_("AlertTemplate", [("level", "eq", "高")], ["template_id", "frozen", "pre_reviewed_c22", "pre_reviewed_r54", "reviewed_at"])),
      irr("危急级告警用的模板是哪条？预审过免责声明和夜间承诺红线了吗？模板是法务上个月改的。")])
case(F, 1, "query", "门店 store-01 有没有医疗器械经营许可？诊疗范围是什么？", ["StoreEntity"],
     "store-01：license_no null、medical_scope []",
     q_("StoreEntity", [("store_id", "eq", "store-01")], ["name", "license_no", "medical_scope", "readiness_ref"]),
     [para("南宁青秀店（store-01）的证照与诊疗范围？"), irr("门店 store-01 有没有医疗器械经营许可？诊疗范围是什么？门口的招牌昨天换了。")])
case(F, 1, "query", "SKU sku-cgm-01 是什么类别？标签核验过了吗？", ["ProductSku"],
     "sku-cgm-01：category 器械引用、label_verified false",
     q_("ProductSku", [("sku_id", "eq", "sku-cgm-01")], ["name", "category", "label_verified", "commission_config"]),
     [para("查产品 sku-cgm-01 的类别与标签核验状态。"),
      swap("SKU sku-ynl-01 是什么类别？标签核验过了吗？", q_("ProductSku", [("sku_id", "eq", "sku-ynl-01")], ["name", "category", "label_verified", "commission_config"])),
      irr("SKU sku-cgm-01 是什么类别？标签核验过了吗？采购说下周到货。")])
case(F, 1, "query", "黄医生的执业证什么时候到期？状态有效吗？", ["Credential"],
     "cred-huang：执业医师，expiry_date 在未来，status valid",
     q_("Credential", [("holder", "eq", "黄医生")], ["credential_id", "credential_type", "expiry_date", "status"]),
     [para("查黄医生的资质记录（类型、到期日、状态）。"),
      swap("陈营养师的注册证什么时候到期？状态有效吗？", q_("Credential", [("holder", "eq", "陈营养师")], ["credential_id", "credential_type", "expiry_date", "status"])),
      irr("黄医生的执业证什么时候到期？状态有效吗？他周三休息。")])
case(F, 1, "query", "王叔（患者 P0031）的用药线索是从哪来的？是否提示低血糖高风险药？", ["MedClassHint"],
     "hint-P0031：hint_source self_report、hypo_risk_med true",
     q_("MedClassHint", [("patient_id", "eq", "P0031")], ["hint_id", "hint_source", "hypo_risk_med", "sglt2i"]),
     [para("P0031 的 MedClassHint 来源和风险标记？"),
      swap("黄伯（患者 P0045）的用药线索是从哪来的？是否提示低血糖高风险药？", q_("MedClassHint", [("patient_id", "eq", "P0045")], ["hint_id", "hint_source", "hypo_risk_med", "sglt2i"])),
      irr("王叔（患者 P0031）的用药线索是从哪来的？是否提示低血糖高风险药？他把药盒放在厨房。")])
case(F, 1, "query", "周先生（患者 P0007）最近一次体测的 BMI 和腰围是多少？", ["BodyMeasurement"],
     "bm-P0007-01：bmi 27.1、waist 96.0",
     q_("BodyMeasurement", [("patient_id", "eq", "P0007")], ["measurement_id", "measured_at", "bmi", "waist", "weight"]),
     [para("P0007 的体测记录（BMI、腰围、体重）。"), irr("周先生（患者 P0007）最近一次体测的 BMI 和腰围是多少？体重秤放在二楼。")])
case(F, 1, "query", "平台登记的数据留存与审计策略是几年？审计开了吗？", ["AuditLog", "C21_数据留存与审计日志"],
     "log-policy：retention_years 3、audit_enabled true",
     q_("AuditLog", [("action", "eq", "retention_policy")], ["log_id", "retention_years", "audit_enabled", "timestamp"]),
     [para("查 retention_policy 的留存年限与审计开关。"), irr("平台登记的数据留存与审计策略是几年？审计开了吗？合规官今天请假。")])
case(F, 1, "query", "禁用词库里「疗效声称」类有哪些词？", ["BannedTermLibrary", "D8_禁用词拦截"],
     "逆转 / 治愈 / 根治 …（category 疗效声称）",
     q_("BannedTermLibrary", [("category", "eq", "疗效声称")], ["term", "category", "version"]),
     [para("列出疗效声称类禁用词。"),
      swap("禁用词库里「用药」类有哪些词？", q_("BannedTermLibrary", [("category", "eq", "用药")], ["term", "category", "version"])),
      irr("禁用词库里「疗效声称」类有哪些词？文案组下午要开会。")])
case(F, 1, "query", "老年且用胰岛素或磺脲的人群，低值告警阈值和 TBR 上限各是多少？", ["TargetProfileParam", "R49_缺参数时按最保守执行"],
     "elderly_high_risk：low_alert_threshold 4.4、tbr_max_pct 1.0",
     q_("TargetProfileParam", [("profile", "eq", "elderly_high_risk")], ["profile", "population", "low_alert_threshold", "tbr_max_pct", "tir_target_pct"]),
     [para("查 elderly_high_risk 这套目标参数。"),
      swap("妊娠人群，低值告警阈值和 TBR 上限各是多少？", q_("TargetProfileParam", [("profile", "eq", "pregnancy")], ["profile", "population", "low_alert_threshold", "tbr_max_pct", "tir_target_pct"])),
      irr("老年且用胰岛素或磺脲的人群，低值告警阈值和 TBR 上限各是多少？指南是去年更新的。")])
case(F, 1, "query", "周先生（患者 P0007）的单独同意书勾了哪些范围？有没有「营销推荐」？", ["ConsentRecord", "C4_数据用于产品推荐须单独同意"],
     "consent-P0007：scope_items 含 营销推荐",
     q_("ConsentRecord", [("patient_id", "eq", "P0007")], ["consent_id", "scope_items", "signed_at", "state"]),
     [para("P0007 的 ConsentRecord 范围清单。"),
      swap("刘阿姨（患者 P0012）的单独同意书勾了哪些范围？有没有「营销推荐」？", q_("ConsentRecord", [("patient_id", "eq", "P0012")], ["consent_id", "scope_items", "signed_at", "state"])),
      irr("周先生（患者 P0007）的单独同意书勾了哪些范围？有没有「营销推荐」？他是用平板签的。")])

# ============================================================================ 因果链溯源（§2 root_cause / derivation 关系 → tier 2 query）
F = "因果链溯源"
case(F, 2, "query", "告警 A-P0045-02 是凌晨 2 点连续 3 读数触发的，把黄伯（P0045）10 月 21 日凌晨那几条低于 3.9 的读数调出来", ["triggered_by_reading", "AlertEvent", "GlucoseReading"],
     "P0045 2026-10-21 02:00–02:45 的 vendor_api 读数（2.8、2.7 …）",
     q_("GlucoseReading", [("patient_id", "eq", "P0045"), ("value_mmol", "lt", 3.9), ("time_utc", "ge", "2026-10-21T00:00"), ("time_utc", "lt", "2026-10-21T06:00")], ["reading_id", "value_mmol", "time_utc", "source_channel"]),
     [para("把触发 A-P0045-02 的那串读数（P0045，10/21 凌晨 <3.9）列出来。"),
      irr("告警 A-P0045-02 是凌晨 2 点连续 3 读数触发的，把黄伯（P0045）10 月 21 日凌晨那几条低于 3.9 的读数调出来，顺便他说贴片有点痒。")])
case(F, 2, "query", "黄伯（P0045）的低血糖告警为什么一直不能闭环？状态机里卡在哪？", ["gates_alert_closure", "HypoState", "AlertEvent"],
     "HypoState P0045：closure_blocked_reason「磺脲使用者：低血糖可持续 24–72 小时」、prolonged_risk true",
     q_("HypoState", [("patient_id", "eq", "P0045")], ["prolonged_risk", "recurrence_window_until", "closure_blocked_reason"]),
     [para("查 P0045 的 HypoState：有没有阻止闭环的原因？"),
      swap("刘阿姨（P0012）的低血糖告警为什么一直不能闭环？状态机里卡在哪？", q_("HypoState", [("patient_id", "eq", "P0012")], ["prolonged_risk", "recurrence_window_until", "closure_blocked_reason"])),
      irr("黄伯（P0045）的低血糖告警为什么一直不能闭环？状态机里卡在哪？值班表今天换人了。")])
case(F, 2, "query", "王叔（P0031）那次「叫不醒」是什么时候、家属做了什么处置？", ["unblocks_closure", "SymptomTreatmentRecord", "R59_老年非典型症状疑似低血糖"],
     "sym-P0031-01：叫不醒 / 家属喂糖水 / 两天前 02:20",
     q_("SymptomTreatmentRecord", [("patient_id", "eq", "P0031")], ["record_id", "symptom_tag", "treatment_action", "recorded_by", "recorded_at"]),
     [para("P0031 的症状与处置记录。"), irr("王叔（P0031）那次「叫不醒」是什么时候、家属做了什么处置？他们家在五楼。")])
case(F, 2, "query", "汇总 s-P0031-14d 是按哪个窗口的读数算的？窗口起止日期？", ["computed_from", "CgmSummary", "GlucoseReading"],
     "window_start / window_end 覆盖最近 14 天",
     q_("CgmSummary", [("summary_id", "eq", "s-P0031-14d")], ["summary_id", "window_start", "window_end", "days", "metric_provenance"]),
     [para("s-P0031-14d 这份汇总的窗口范围和指标来源？"),
      swap("汇总 s-P0045-14d 是按哪个窗口的读数算的？窗口起止日期？", q_("CgmSummary", [("summary_id", "eq", "s-P0045-14d")], ["summary_id", "window_start", "window_end", "days", "metric_provenance"])),
      irr("汇总 s-P0031-14d 是按哪个窗口的读数算的？窗口起止日期？报告要发给他女儿。")])
case(F, 2, "query", "王叔（P0031）夜间（00–06）发生过的低血糖事件各持续多久、最低多少？", ["statistically_derived_from", "HypoEpisode", "R07_夜间低血糖事件"],
     "HypoEpisode P0031 night_flag true 的事件列表",
     q_("HypoEpisode", [("patient_id", "eq", "P0031"), ("night_flag", "eq", True)], ["start_time", "end_time", "min_value", "level"]),
     [para("列 P0031 的夜间低血糖事件（起止、最低值、级别）。"),
      swap("陈阿姨（P0023）夜间（00–06）发生过的低血糖事件各持续多久、最低多少？", q_("HypoEpisode", [("patient_id", "eq", "P0023"), ("night_flag", "eq", True)], ["start_time", "end_time", "min_value", "level"])),
      irr("王叔（P0031）夜间（00–06）发生过的低血糖事件各持续多久、最低多少？他家的网络前天断过。")])
case(F, 2, "query", "方案 plan-P0066-w41 签发时签发人看了多久、改了什么？", ["review_evidence_ref", "PlanSigned", "ReviewEvidence", "D13_签发反橡皮图章检测"],
     "re-plan-P0066-w41：dwell_time 48、diff「补充了睡前加餐说明」",
     q_("ReviewEvidence", [("plan_id", "eq", "plan-P0066-w41")], ["evidence_id", "dwell_time", "diff", "agp_expand_count", "review_suspicious"]),
     [para("plan-P0066-w41 的签发证据（停留时长、修改）。"),
      swap("方案 plan-P0088-w41 签发时签发人看了多久、改了什么？", q_("ReviewEvidence", [("plan_id", "eq", "plan-P0088-w41")], ["evidence_id", "dwell_time", "diff", "agp_expand_count", "review_suspicious"])),
      irr("方案 plan-P0066-w41 签发时签发人看了多久、改了什么？那天店里停电过一次。")])
case(F, 2, "query", "方案 plan-P0066-w41 是 S-CHEN 签的，这位签发人的资质类型和到期日是什么？", ["PlanSigned", "Credential", "D11a_签发人资质失效自动冻结"],
     "cred-chen：注册营养师，expiry_date 33 天前（已过期，status 仍写 valid）",
     q_("Credential", [("holder_id", "eq", "S-CHEN")], ["credential_id", "holder", "credential_type", "expiry_date", "status"]),
     [para("查签发人 S-CHEN 的资质记录。"),
      swap("方案 plan-P0012-w40 是 S-HUANG 签的，这位签发人的资质类型和到期日是什么？", q_("Credential", [("holder_id", "eq", "S-HUANG")], ["credential_id", "holder", "credential_type", "expiry_date", "status"])),
      irr("方案 plan-P0066-w41 是 S-CHEN 签的，这位签发人的资质类型和到期日是什么？她下月要去进修。")])
case(F, 2, "query", "告警 A-P0031-backfill-01 是哪条规则触发的？触发读数是不是回填的？", ["AlertEvent", "R52_回填读数不得触发实时告警"],
     "rule_id R03a、is_backfill true、evidence「回填批次 3 周前读数」",
     q_("AlertEvent", [("alert_id", "eq", "A-P0031-backfill-01")], ["alert_id", "rule_id", "is_backfill", "source_channel", "evidence", "level"]),
     [para("A-P0031-backfill-01 的触发规则与回填标记？"),
      swap("告警 A-P0045-ocr-01 是哪条规则触发的？触发读数是不是回填的？", q_("AlertEvent", [("alert_id", "eq", "A-P0045-ocr-01")], ["alert_id", "rule_id", "is_backfill", "source_channel", "evidence", "level"])),
      irr("告警 A-P0031-backfill-01 是哪条规则触发的？触发读数是不是回填的？回填是昨天上午做的。")])
case(F, 2, "query", "周先生（P0007）的缓解时钟 Day0 是哪天？谁确认的？现在是什么状态？", ["RemissionClock", "R29_缓解判定"],
     "RemissionClock P0007：day0 105 天前、status running、confirmed_by S-HUANG",
     q_("RemissionClock", [("patient_id", "eq", "P0007")], ["day0", "status", "confirmed_by"]),
     [para("P0007 的 RemissionClock 记录。"), irr("周先生（P0007）的缓解时钟 Day0 是哪天？谁确认的？现在是什么状态？他说想报名下期课程。")])
case(F, 2, "query", "周先生（P0007）走缓解路径的 ABCD 筛查化验结果（GADA、空腹和餐后 C 肽）各是多少？", ["LabResult", "R30_缓解适宜人群筛选_ABCD"],
     "lab-P0007-gada 0.4、cpf 1.6、cp2 3.4（抗体阴性、C 肽达标）",
     q_("LabResult", [("patient_id", "eq", "P0007")], ["lab_result_id", "method", "value", "measured_at", "is_ngsp_certified"]),
     [para("列出 P0007 的全部化验结果。"), irr("周先生（P0007）走缓解路径的 ABCD 筛查化验结果（GADA、空腹和餐后 C 肽）各是多少？化验单是在市一医院做的。")])

# ============================================================================ 低血糖安全（B1）
F = "低血糖安全"
case(F, 3, "action(触发低血糖处置)", "__R04A_COMMIT__", ["触发低血糖处置", "R04a_Level1低血糖_实时告警"],
     "连续 2 读数 <3.9 已确认且处于回升段（R05 预测条件不成立），应触发并 committed（级别 中）",
     None, [], note="实参由 seed 动态挑选：3.0≤g<3.9、前值 <3.9 且回升幅度足以使 20 分钟外推 ≥3.9（避开 R05 的预测性告警要求）")
case(F, 3, "rejected(R04a_Level1低血糖_实时告警)", "__R04A_REJECT__", ["触发低血糖处置", "R04a_Level1低血糖_实时告警"],
     "前一读数 ≥3.9 未确认，须连续 2 个读数，被 R04a 拒绝",
     None, [], note="实参由 seed 动态挑选：g∈[3.0,3.9) 且前一读数 ≥3.9")
case(F, 3, "rejected(R52_回填读数不得触发实时告警)", "王叔（P0031）回填上来的读数 r-P0031-00123 是 3.4，按 R04a 触发实时低血糖处置", ["触发低血糖处置", "R52_回填读数不得触发实时告警"],
     "该读数 is_backfill=true，只进统计通道，被 R52 拒绝",
     a_("触发低血糖处置", patient_id="P0031", reading_id="r-P0031-00123", rule_id="R04a_Level1低血糖_实时告警"),
     [para("用 P0031 的回填读数 r-P0031-00123（3.4）走一遍实时低血糖处置。"),
      irr("王叔（P0031）回填上来的读数 r-P0031-00123 是 3.4，按 R04a 触发实时低血糖处置；回填是健管师小李操作的。")])
case(F, 3, "action(推送告警)", "把告警 A-P0012-01（中级）推送给健管师", ["推送告警", "R56_告警模板预审冻结"],
     "套用已冻结模板 tpl-中，committed",
     a_("推送告警", alert_id="A-P0012-01", level="中", targets=["健管师"]),
     [para("A-P0012-01 按中级告警推给健管师。"),
      swap("把告警 A-P0045-02（高级）推送给医师和家属", a_("推送告警", alert_id="A-P0045-02", level="高", targets=["医师", "家属"])),
      irr("把告警 A-P0012-01（中级）推送给健管师，健管师今天在店里值班。")])
case(F, 3, "rejected(R56_告警模板预审冻结)", "把告警 A-P0012-01 按「紧急」级别推送给健管师和家属", ["推送告警", "R56_告警模板预审冻结"],
     "「紧急」没有已冻结的告警模板，不允许现场生成话术，被 R56 拒绝",
     a_("推送告警", alert_id="A-P0012-01", level="紧急", targets=["健管师", "家属"]),
     [para("A-P0012-01 用紧急级推送。"), irr("把告警 A-P0012-01 按「紧急」级别推送给健管师和家属，家属的电话刚更新过。")])
case(F, 3, "action(响应并回执告警)", "健管师回执告警 A-P0045-02：15-15 补碳后复测 4.6，继续观察 24 小时", ["响应并回执告警", "R44_高危用药禁止闭环"],
     "回执不含闭环措辞，committed；R44 不触发",
     a_("响应并回执告警", alert_id="A-P0045-02", responder="健管师", action_taken="15-15 补碳后复测回升，继续观察 24 小时", retest_value=4.6),
     [para("A-P0045-02 回执：补碳复测 4.6，保持观察。"),
      swap("健管师回执告警 A-P0012-01：15-15 补碳后复测 5.1，继续观察 24 小时", a_("响应并回执告警", alert_id="A-P0012-01", responder="健管师", action_taken="15-15 补碳后复测回升，继续观察 24 小时", retest_value=5.1)),
      irr("健管师回执告警 A-P0045-02：15-15 补碳后复测 4.6，继续观察 24 小时；补的是葡萄糖片。")])
case(F, 3, "action(收紧告警阈值)", "黄伯（P0045）24 小时内有 Level 2 事件，按 R34 把夜间低值阈值上调到 4.4", ["收紧告警阈值", "R34_HAAF_24小时复发窗"],
     "收紧方向正确，committed",
     a_("收紧告警阈值", patient_id="P0045", field="night_low", trigger_rule="R34_HAAF_24小时复发窗", new_value=4.4),
     [para("P0045 的 night_low 收紧到 4.4（触发规则 R34）。"),
      swap("王叔（P0031）24 小时内有 Level 2 事件，按 R34 把夜间低值阈值上调到 4.4", a_("收紧告警阈值", patient_id="P0031", field="night_low", trigger_rule="R34_HAAF_24小时复发窗", new_value=4.4)),
      irr("黄伯（P0045）24 小时内有 Level 2 事件，按 R34 把夜间低值阈值上调到 4.4；他家的采集盒放在床头。")])
case(F, 3, "action(放宽告警阈值)", "医师把周先生（P0007）的日间高值告警阈值从 10.0 放宽到 13.9", ["放宽告警阈值", "R46_IAH高危阈值上调且禁止静音"],
     "P0007 成人、无低血糖史、TIR 97.5%，放宽的是高值阈值且不触及低值下限，医师可放宽，committed",
     a_("放宽告警阈值", patient_id="P0007", field="day_high", new_value=13.9),
     [para("P0007 的 day_high 阈值改到 13.9。"), irr("医师把周先生（P0007）的日间高值告警阈值从 10.0 放宽到 13.9，他说白天总被提醒。")],
     note="专家抽检后改措辞：原案例对两晚前有夜间 L2 的老年患者放宽低值到 3.5，临床不现实")
case(F, 3, "rejected(R46_IAH高危阈值上调且禁止静音)", "把黄伯（P0045）的夜间低值告警阈值放宽到 3.9", ["放宽告警阈值", "R46_IAH高危阈值上调且禁止静音"],
     "P0045 是无感知低血糖高危，低值阈值不得低于 4.4，被 R46 拒绝",
     a_("放宽告警阈值", patient_id="P0045", field="night_low", new_value=3.9),
     [para("P0045 的夜间低值阈值调回 3.9。"),
      swap("把王叔（P0031）的夜间低值告警阈值放宽到 4.0", a_("放宽告警阈值", patient_id="P0031", field="night_low", new_value=4.0)),
      irr("把黄伯（P0045）的夜间低值告警阈值放宽到 3.9，他女儿打电话来说的。")])
case(F, 3, "action(生成去强化证据工单)", "给黄伯（P0045）出一份转医师的去强化证据包（14 天）", ["生成去强化证据工单", "R09_TBR超标触发去强化审查"],
     "TBR 2.0% 超老年高危上限 1%，证据包首页标红「低血糖优先」后 committed",
     a_("生成去强化证据工单", patient_id="P0045", window="14d"),
     [para("P0045 的 14 天去强化证据工单。"),
      swap("给刘阿姨（P0012）出一份转医师的去强化证据包（14 天）", a_("生成去强化证据工单", patient_id="P0012", window="14d")),
      irr("给黄伯（P0045）出一份转医师的去强化证据包（14 天），医师明天上午出诊。")])

# ============================================================================ 高血糖与波动（B2 / B3）
F = "高血糖与波动"
case(F, 3, "action(生成方案草稿)", "给黄伯（P0045）生成本期方案草稿，方向维持（基于 s-P0045-14d）", ["生成方案草稿", "低血糖优先抢占"],
     "方向维持，低血糖带命中但不抑制维持方向，committed",
     a_("生成方案草稿", patient_id="P0045", analysis_result={"summary_id": "s-P0045-14d"}, direction="维持"),
     [para("P0045 本期方案草稿，维持方向。"),
      swap("给周先生（P0007）生成本期方案草稿，方向维持（基于 s-P0007-14d）", a_("生成方案草稿", patient_id="P0007", analysis_result={"summary_id": "s-P0007-14d"}, direction="维持")),
      irr("给黄伯（P0045）生成本期方案草稿，方向维持（基于 s-P0045-14d），他下周要去女儿家住。")])
case(F, 3, "rejected(低血糖优先抢占)", "黄伯（P0045）TAR 偏高，给他生成一份加强降糖方向的方案草稿（基于 s-P0045-14d）", ["生成方案草稿", "低血糖优先抢占"],
     "TBR 2.0% 已超老年高危上限且有 L2 事件，低血糖带命中，强化方向被元规则抑制",
     a_("生成方案草稿", patient_id="P0045", analysis_result={"summary_id": "s-P0045-14d"}, direction="强化"),
     [para("P0045 出强化降糖方向的草稿。"), irr("黄伯（P0045）TAR 偏高，给他生成一份加强降糖方向的方案草稿（基于 s-P0045-14d），他最近爱吃糯米饭。")])
case(F, 3, "action(生成方案草稿)", "给陈阿姨（P0023）生成去强化方向的方案草稿（基于 s-P0023-14d）", ["生成方案草稿", "R35_夜间覆盖不足禁强化"],
     "去强化方向不受 R35 限制（夜间覆盖 40% 只禁强化），committed",
     a_("生成方案草稿", patient_id="P0023", analysis_result={"summary_id": "s-P0023-14d"}, direction="去强化"),
     [para("P0023 的草稿，方向去强化。"), irr("给陈阿姨（P0023）生成去强化方向的方案草稿（基于 s-P0023-14d），她用的是甘精胰岛素，晚上睡得早。")])

# ============================================================================ 结论层与分层（B5）
F = "结论层与分层"
case(F, 3, "action(输出服务分层标签)", "给周先生（P0007）按 14 天数据输出内部服务分层标签", ["输出服务分层标签", "R18_CGM服务分层_内部标签"],
     "成人、数据充分、disclosure_approved=true，输出内部标签 committed",
     a_("输出服务分层标签", patient_id="P0007", window="14d"),
     [para("P0007 的德心分层内部标签。"), irr("给周先生（P0007）按 14 天数据输出内部服务分层标签，他明天来店复诊。")])
case(F, 3, "action(输出服务分层标签)", "给刘阿姨（P0012）按 14 天数据输出德心服务分层标签", ["输出服务分层标签", "R18_CGM服务分层_内部标签", "R28_老年目标切换"],
     "P0012 是老年（68 岁），R18 为 soft 规则：告警「elderly 不做德心分层，只出趋势描述」但不阻断提交，动作 committed（标签应为空）",
     a_("输出服务分层标签", patient_id="P0012", window="14d"),
     [para("P0012 的服务分层标签。"),
      swap("给黄伯（P0045）按 14 天数据输出德心服务分层标签", a_("输出服务分层标签", patient_id="P0045", window="14d")),
      irr("给刘阿姨（P0012）按 14 天数据输出德心服务分层标签，她孙子周末要来。")])
case(F, 3, "rejected(R51_分层结论默认不可披露患者)", "健管师在张阿姨（P0066）的群里答复：您本期的服务分层是 L1 级", ["群内答复患者", "R51_分层结论默认不可披露患者"],
     "含分层结论且 P0066 disclosure_approved=false，被 R51 拒绝",
     a_("群内答复患者", patient_id="P0066", message="您本期的服务分层是 L1 级，继续保持。", sender_role="健管师"),
     [para("群里告诉 P0066 她是 L1 分层。"),
      swap("健管师在李女士（P0088）的群里答复：您本期的服务分层是 L1 级", a_("群内答复患者", patient_id="P0088", message="您本期的服务分层是 L1 级，继续保持。", sender_role="健管师")),
      irr("健管师在张阿姨（P0066）的群里答复：您本期的服务分层是 L1 级；群里还有她女儿。")])
case(F, 3, "action(群内答复患者)", "健管师在刘阿姨（P0012）群里答复：今天的数据已经同步到，餐后记得走一走", ["群内答复患者", "R55_显示口径_没有数据不得说成没有异常"],
     "无禁用词、无原始数值、无夜间承诺、当日有数据，committed",
     a_("群内答复患者", patient_id="P0012", message="今天的数据已经同步到了，餐后记得走一走。", sender_role="健管师"),
     [para("在 P0012 群里发一句同步提醒和餐后步行提醒。"),
      swap("健管师在黄伯（P0045）群里答复：今天的数据已经同步到，餐后记得走一走", a_("群内答复患者", patient_id="P0045", message="今天的数据已经同步到了，餐后记得走一走。", sender_role="健管师")),
      irr("健管师在刘阿姨（P0012）群里答复：今天的数据已经同步到，餐后记得走一走；她今天穿了红外套。")])
case(F, 3, "rejected(C6_群内数据最小可见范围)", "健管师在黄伯（P0045）群里答复：您凌晨两点测到 2.7 mmol/L，要注意", ["群内答复患者", "C6_群内数据最小可见范围"],
     "群内出现未脱敏原始血糖值，被 C6 拒绝",
     a_("群内答复患者", patient_id="P0045", message="您凌晨两点测到 2.7 mmol/L，要注意补充碳水。", sender_role="健管师"),
     [para("在 P0045 群里直接报凌晨 2.7 mmol/L 的读数。"),
      swap("健管师在王叔（P0031）群里答复：您凌晨三点测到 2.2 mmol/L，要注意", a_("群内答复患者", patient_id="P0031", message="您凌晨三点测到 2.2 mmol/L，要注意补充碳水。", sender_role="健管师")),
      irr("健管师在黄伯（P0045）群里答复：您凌晨两点测到 2.7 mmol/L，要注意；群公告今天更新了。")])
case(F, 3, "rejected(C19_线上随访边界)", "健管师在刘阿姨（P0012）群里答复：我来给您诊断一下，看这曲线问题不大", ["群内答复患者", "C19_线上随访边界"],
     "健管师在线上随访里做诊断，超出健康教育/生活方式/监测提醒/异常转介范围，被 C19 拒绝",
     a_("群内答复患者", patient_id="P0012", message="我来给您诊断一下，看这曲线问题不大。", sender_role="健管师"),
     [para("健管师在 P0012 群里说要给她诊断。"), irr("健管师在刘阿姨（P0012）群里答复：我来给您诊断一下，看这曲线问题不大；医院离她家两公里。")],
     note="专家抽检后改措辞：原句「建议您去医院开处方调整」属异常转介、现实里允许，但 C19 实现的关键词正则会拒——记为实现缺口候选")
case(F, 3, "rejected(D8_禁用词拦截)", "健管师在周先生（P0007）群里答复：恭喜，您已经逆转了", ["群内答复患者", "D8_禁用词拦截"],
     "「逆转」是禁用词，被 D8 拒绝（P0007 虽达缓解标准，措辞仍不可用）",
     a_("群内答复患者", patient_id="P0007", message="恭喜，您已经逆转了！", sender_role="健管师"),
     [para("群里祝贺 P0007 逆转成功。"),
      swap("健管师在李女士（P0088）群里答复：恭喜，您已经逆转了", a_("群内答复患者", patient_id="P0088", message="恭喜，您已经逆转了！", sender_role="健管师")),
      irr("健管师在周先生（P0007）群里答复：恭喜，您已经逆转了；他太太也在群里。")])
case(F, 3, "rejected(R54_服务话术不得含夜间安全承诺)", "健管师在刘阿姨（P0012）群里答复：放心，夜里出事我们第一时间知道", ["群内答复患者", "R54_服务话术不得含夜间安全承诺"],
     "含夜间安全承诺，被 R54 拒绝",
     a_("群内答复患者", patient_id="P0012", message="放心，夜里出事我们第一时间知道。", sender_role="健管师"),
     [para("在 P0012 群里承诺夜间有人盯着。"),
      swap("健管师在陈阿姨（P0023）群里答复：放心，夜里出事我们第一时间知道", a_("群内答复患者", patient_id="P0023", message="放心，夜里出事我们第一时间知道。", sender_role="健管师")),
      irr("健管师在刘阿姨（P0012）群里答复：放心，夜里出事我们第一时间知道；这是店长让发的。")])

# ============================================================================ 缓解路径（B5）
F = "缓解路径"
case(F, 3, "action(判定缓解结果)", "刘阿姨（P0012）还在吃二甲双胍，也判一下缓解结果（报告 s-P0012-14d）", ["判定缓解结果", "R29_缓解判定"],
     "判定结果为未缓解（在用降糖药、无缓解时钟），判定动作本身 committed",
     a_("判定缓解结果", patient_id="P0012", summary_id="s-P0012-14d"),
     [para("给 P0012 做一次缓解判定。"), irr("刘阿姨（P0012）还在吃二甲双胍，也判一下缓解结果（报告 s-P0012-14d），她问是不是能少吃点药。")],
     note="若 handler 对不达标者直接标 in_remission 则 R29 会拒，按实际裁决修标签")
case(F, 3, "rejected(R01_数据充分性门槛_仅管结论层)", "李女士（P0088）才戴 6 天，用报告 s-P0088-6d 判一下缓解", ["判定缓解结果", "R01_数据充分性门槛_仅管结论层"],
     "6 天未达 14 天门槛，结论层禁出缓解结论，被 R01 拒绝",
     a_("判定缓解结果", patient_id="P0088", summary_id="s-P0088-6d"),
     [para("用 6 天数据给 P0088 判缓解。"), irr("李女士（P0088）才戴 6 天，用报告 s-P0088-6d 判一下缓解，她很着急想知道。")])

# ============================================================================ 出口签发闸（B6）
F = "出口签发闸"
case(F, 3, "rejected(D12_签发人归属分流)", "让吴康复师签发刘阿姨（P0012）的营养方案草稿 d-P0012-01", ["签发方案", "D12_签发人归属分流"],
     "草稿类别为营养，运动康复师只能签运动/教育类，被 D12 拒绝",
     a_("签发方案", draft_id="d-P0012-01", signer_id="吴康复师", decision="approve"),
     [para("d-P0012-01 由吴康复师签。"), irr("让吴康复师签发刘阿姨（P0012）的营养方案草稿 d-P0012-01，他今天刚从外地回来。")])
case(F, 3, "rejected(D9_产品功效声称拦截)", "把待审内容 c-reco-P0012-01 过一下出口审核（内容类型：方案）", ["审核输出内容", "D9_产品功效声称拦截"],
     "内容把英纽林疗程与 L3 分级写在同一句，被 D9 拒绝（R32、C22 同时命中）",
     a_("审核输出内容", content_id="c-reco-P0012-01", content_type="方案"),
     [para("审核 c-reco-P0012-01。"), irr("把待审内容 c-reco-P0012-01 过一下出口审核（内容类型：方案），是小王写的。")])
case(F, 3, "rejected(C9_AI方案禁止直接推送)", "把刘阿姨（P0012）的方案草稿 d-P0012-01 直接推送给患者本人", ["推送方案至患者", "C9_AI方案禁止直接推送"],
     "d-P0012-01 只是草稿、没有 PlanSigned，被 C9 拒绝",
     a_("推送方案至患者", plan_id="d-P0012-01", targets=["P0012"]),
     [para("草稿 d-P0012-01 直接发给 P0012。"), irr("把刘阿姨（P0012）的方案草稿 d-P0012-01 直接推送给患者本人，她在等。")])
case(F, 3, "action(推送方案至患者)", "把已签发的方案 plan-P0012-w40 推送给刘阿姨（P0012）", ["推送方案至患者", "C9_AI方案禁止直接推送"],
     "已签发、签发人资质有效、含免责声明、不含分层结论，committed",
     a_("推送方案至患者", plan_id="plan-P0012-w40", targets=["P0012"]),
     [para("推送 plan-P0012-w40 给 P0012。"),
      swap("把已签发的方案 plan-P0045-w41 推送给黄伯（P0045）", a_("推送方案至患者", plan_id="plan-P0045-w41", targets=["P0045"])),
      irr("把已签发的方案 plan-P0012-w40 推送给刘阿姨（P0012），她习惯用微信看。")])
case(F, 3, "action(生成产品推荐)", "给周先生（P0007）推荐英纽林（sku-ynl-01），话术：作为日常饮食的补充", ["生成产品推荐", "C4_数据用于产品推荐须单独同意"],
     "P0007 勾选了营销推荐、话术不含分层/缓解字样并附尾注，committed",
     a_("生成产品推荐", patient_id="P0007", sku_id="sku-ynl-01", pitch="作为日常饮食的补充，可以试试英纽林。"),
     [para("P0007 的英纽林推荐，话术只说饮食补充。"), irr("给周先生（P0007）推荐英纽林（sku-ynl-01），话术：作为日常饮食的补充；他上次买过一盒。")])
case(F, 3, "rejected(C4_数据用于产品推荐须单独同意)", "给刘阿姨（P0012）推荐英纽林（sku-ynl-01），话术：作为日常饮食的补充", ["生成产品推荐", "C4_数据用于产品推荐须单独同意"],
     "P0012 未单独勾选「营销推荐」，被 C4 拒绝",
     a_("生成产品推荐", patient_id="P0012", sku_id="sku-ynl-01", pitch="作为日常饮食的补充，可以试试英纽林。"),
     [para("给 P0012 配一份英纽林推荐。"),
      swap("给陈阿姨（P0023）推荐英纽林（sku-ynl-01），话术：作为日常饮食的补充", a_("生成产品推荐", patient_id="P0023", sku_id="sku-ynl-01", pitch="作为日常饮食的补充，可以试试英纽林。")),
      irr("给刘阿姨（P0012）推荐英纽林（sku-ynl-01），话术：作为日常饮食的补充；她女儿说可以买。")])
case(F, 3, "rejected(D9_产品功效声称拦截)", "给周先生（P0007）推荐英纽林（sku-ynl-01），话术：坚持用英纽林，逆转就在眼前", ["生成产品推荐", "D9_产品功效声称拦截"],
     "产品与「逆转」同句，被 D9 拒绝（R32 同时命中）",
     a_("生成产品推荐", patient_id="P0007", sku_id="sku-ynl-01", pitch="坚持用英纽林，逆转就在眼前。"),
     [para("P0007 的推荐话术写成「用英纽林逆转」。"), irr("给周先生（P0007）推荐英纽林（sku-ynl-01），话术：坚持用英纽林，逆转就在眼前；文案是营销部给的。")])

# ============================================================================ 产品与机构合规（B7）
F = "产品与机构合规"
case(F, 3, "action(创建服务包SKU)", "创建服务包 SKU pkg-L2-basic（L2 档），内容：血糖监测佩戴指导、每周健管师随访、医师方案签发", ["创建服务包SKU", "C13_服务与产品物理分离"],
     "只含服务、无产品实体、无夜间承诺，committed",
     a_("创建服务包SKU", sku_id="pkg-L2-basic", tier="L2", contents=["血糖监测佩戴指导", "每周健管师随访", "医师方案签发"]),
     [para("新建 L2 档服务包 pkg-L2-basic，三项服务内容。"), irr("创建服务包 SKU pkg-L2-basic（L2 档），内容：血糖监测佩戴指导、每周健管师随访、医师方案签发；定价下周定。")])
case(F, 3, "rejected(C13_服务与产品物理分离)", "创建服务包 SKU pkg-L3-plus（L3 档），内容：每周随访、英纽林一套", ["创建服务包SKU", "C13_服务与产品物理分离"],
     "服务包内容含产品实体「英纽林」，被 C13 拒绝",
     a_("创建服务包SKU", sku_id="pkg-L3-plus", tier="L3", contents=["每周随访", "英纽林一套"]),
     [para("L3 服务包里捆一套英纽林。"), irr("创建服务包 SKU pkg-L3-plus（L3 档），内容：每周随访、英纽林一套；包装盒是绿色的。")])
case(F, 3, "action(上架产品SKU)", "把英纽林 sku-ynl-01 按食品类上架", ["上架产品SKU", "C14_产品标签合规校验"],
     "食品且 label_verified=true，committed",
     a_("上架产品SKU", sku_id="sku-ynl-01", category="食品"),
     [para("上架食品 sku-ynl-01。"), irr("把英纽林 sku-ynl-01 按食品类上架，货架在二楼。")])
case(F, 3, "rejected(C14_产品标签合规校验)", "把新到的代餐粉 sku-dc-01 按食品类上架", ["上架产品SKU", "C14_产品标签合规校验"],
     "sku-dc-01 未核验「固体饮料」字号与警示语，被 C14 拒绝",
     a_("上架产品SKU", sku_id="sku-dc-01", category="食品"),
     [para("上架食品 sku-dc-01。"), irr("把新到的代餐粉 sku-dc-01 按食品类上架，供应商是上海的。")])
case(F, 3, "rejected(C2_网络销售备案与证照公示)", "在线上商城单独频道上架 CGM 传感器 sku-cgm-01", ["上架产品SKU", "C2_网络销售备案与证照公示"],
     "器械类 SKU 无网络销售备案与证照公示，被 C2 拒绝（C1 同时命中）",
     a_("上架产品SKU", sku_id="sku-cgm-01", category="器械引用"),
     [para("线上频道上架 sku-cgm-01。"), irr("在线上商城单独频道上架 CGM 传感器 sku-cgm-01，页面模板用去年的。")])

# ============================================================================ 数据与同意合规（B7 数据）
F = "数据与同意合规"
case(F, 3, "action(摄入读数)", "从厂商接口摄入刘阿姨（P0012）的一条读数：r-P0012-x1，6.3 mmol/L，传感器序号 SN-P0012", ["摄入读数", "R48_去重键必须用传感器序号"],
     "已有血糖数据单独同意、去重键以传感器序号开头，committed",
     a_("摄入读数", channel="vendor_api", raw_payload={"patient_id": "P0012", "readings": [{"reading_id": "r-P0012-x1", "value_raw": 6.3, "unit_raw": "mmol/L", "value_mmol": 6.3, "sensor_serial": "SN-P0012", "dedup_key": "SN-P0012-90001", "device_time": "2026-10-23T08:00", "time_utc": "2026-10-23T00:00", "source_channel": "vendor_api", "source_confidence": 0.99, "quality_flag": "clean", "is_backfill": False}]}),
     [para("P0012 厂商接口新读数 r-P0012-x1（6.3，序号 SN-P0012）入库。"),
      swap("从厂商接口摄入黄伯（P0045）的一条读数：r-P0045-x1，6.8 mmol/L，传感器序号 SN-P0045", a_("摄入读数", channel="vendor_api", raw_payload={"patient_id": "P0045", "readings": [{"reading_id": "r-P0045-x1", "value_raw": 6.8, "unit_raw": "mmol/L", "value_mmol": 6.8, "sensor_serial": "SN-P0045", "dedup_key": "SN-P0045-90001", "device_time": "2026-10-23T08:00", "time_utc": "2026-10-23T00:00", "source_channel": "vendor_api", "source_confidence": 0.99, "quality_flag": "clean", "is_backfill": False}]})),
      irr("从厂商接口摄入刘阿姨（P0012）的一条读数：r-P0012-x1，6.3 mmol/L，传感器序号 SN-P0012；接口今天有点慢。")])
case(F, 3, "rejected(R48_去重键必须用传感器序号)", "摄入刘阿姨（P0012）的读数 r-P0012-x2（6.1），传感器序号 SN-P0012 有，但去重键坚持用厂商记录 ID vendor-77", ["摄入读数", "R48_去重键必须用传感器序号"],
     "有传感器序号却不用它做去重键，被 R48 拒绝（无序号时才允许 ±90s 容差 + weak_dedup 兜底）",
     a_("摄入读数", channel="vendor_api", raw_payload={"patient_id": "P0012", "readings": [{"reading_id": "r-P0012-x2", "value_raw": 6.1, "unit_raw": "mmol/L", "value_mmol": 6.1, "sensor_serial": "SN-P0012", "dedup_key": "vendor-77", "device_time": "2026-10-23T08:15", "time_utc": "2026-10-23T00:15", "source_channel": "vendor_api", "source_confidence": 0.99, "quality_flag": "clean", "is_backfill": False}]}),
     [para("P0012 的读数 r-P0012-x2 有序号 SN-P0012，却用厂商记录 ID 做去重键入库。"), irr("摄入刘阿姨（P0012）的读数 r-P0012-x2（6.1），传感器序号 SN-P0012 有，但去重键坚持用厂商记录 ID vendor-77；厂商说这是旧接口。")],
     note="专家抽检后改措辞：原案例「无序号」应走 weak_dedup 兜底而非拒收")

# 由 seed 动态挑选实参的案例
DYNAMIC = {
    "__R04A_REJECT__": None,
}


NAMES = {"P0045": "黄伯", "P0012": "刘阿姨", "P0031": "王叔"}


def _clean_rows(store):
    import collections
    rd = collections.defaultdict(list)
    for item in store.iter_objects("GlucoseReading"):
        v = item[-1]
        if v.get("source_channel") == "vendor_api" and not v.get("is_backfill"):
            rd[v["patient_id"]].append(v)
    return {p: sorted(rows, key=lambda r: r.get("time_utc") or "") for p, rows in rd.items()}


def resolve_r04a_reject(store):
    """R04a 拒绝案例：g∈[3.0,3.9) 且前一 clean 读数 ≥3.9。"""
    for pid, rows in _clean_rows(store).items():
        if pid not in NAMES:
            continue
        for i in range(1, len(rows)):
            g, pg = rows[i]["value_mmol"], rows[i - 1]["value_mmol"]
            if 3.0 <= g < 3.9 and pg >= 3.9:
                rid = rows[i]["reading_id"]; name = NAMES[pid]
                q = f"{name}（{pid}）读数 {rid} 是 {g}，立刻按 R04a 触发 Level 1 低血糖处置"
                route = a_("触发低血糖处置", patient_id=pid, reading_id=rid, rule_id="R04a_Level1低血糖_实时告警")
                return q, route, [para(f"单条读数 {rid}（{g}）就触发 {pid} 的一级低血糖处置。"),
                                  irr(f"{name}（{pid}）读数 {rid} 是 {g}，立刻按 R04a 触发 Level 1 低血糖处置；今天天气不错。")]
    return None


def resolve_r04a_commit(store):
    """R04a 通过案例：3.0≤g<3.9、前值 <3.9，且回升使 R05 的 20 分钟外推 ≥3.9（g + (g−prev)/15·20 ≥ 3.9）。"""
    for pid, rows in _clean_rows(store).items():
        if pid not in NAMES:
            continue
        for i in range(1, len(rows)):
            g, pg = rows[i]["value_mmol"], rows[i - 1]["value_mmol"]
            if 3.0 <= g < 3.9 and pg < 3.9 and g + (g - pg) / 15 * 20 >= 3.9 and (g - pg) > -1:
                rid = rows[i]["reading_id"]; name = NAMES[pid]
                q = f"{name}（{pid}）读数 {rid} 是 {g}，前一读数 {pg}，按 Level 1 规则 R04a 触发低血糖处置"
                route = a_("触发低血糖处置", patient_id=pid, reading_id=rid, rule_id="R04a_Level1低血糖_实时告警")
                return q, route, [para(f"{pid} 的 {rid}（{g}，前值 {pg}）触发一级低血糖处置流程。"),
                                  irr(f"{name}（{pid}）读数 {rid} 是 {g}，前一读数 {pg}，按 Level 1 规则 R04a 触发低血糖处置；家属说昨晚没吃夜宵。")]
    return None


EXPERT_DELETED = [
    ("低血糖安全：R03a 拒绝分支（P0045 读数 2.6、前值 3.0）", "专家：前值 3.0 + 现值 2.6 已满足连续 2 读数 <3.9，老年 IAH 磺脲使用者凌晨跌到 2.6 现实里必须触发处置（降级为 R04a「中」），引擎整体拒绝与临床口径相反 → 删案例；记为实现缺口候选（R03a 未确认时应降级触发而非拒绝）"),
    ("出口签发闸：c-promo-01 过审核 → rejected(C22)", "专家：可识别患者前后对比素材的首要违规是 C16，不是缺免责声明；按 C16 + 发布宣传素材 已被 golden-26 覆盖 → 删案例"),
    ("高血糖与波动：P0099 维持方向草稿 → rejected(R49)", "专家：R49 的 IR 语义是「按最保守参数继续执行并置 population_params_stale」，不是拒绝；引擎拒绝与 IR intent 不一致 → 删案例；记为实现缺口候选"),
    ("结论层与分层：群内「建议您去医院开处方调整」→ rejected(C19)", "专家：该句属异常转介，在健管师允许范围内；C19 实现的关键词正则（处方）误拒 → 改为真正越界的「我来给您诊断」；原句记为实现缺口候选（规则过宽）"),
]

SKIPPED = [
    ("R03a 通过分支（触发低血糖处置 committed，Level 2）", "实现口径：R05 对已 <3.0 的读数仍要求告警证据含「预测」字样，连续两读数 <3.0 且回升 ≥0.7 的读数对 seed 里不存在；按「不改规则实现」原则删案例，记为实现缺口候选（R05 应只在 g≥3.9 时评估）"),
    ("R42_急性混杂窗口禁止出结论", "seed 无 ClinicalContextEvent"),
    ("R37_疑似1型LADA红旗", "seed 无 lada_flags"),
    ("R27_运动后延迟低血糖", "seed 无运动 ContextEvent"),
    ("R34_HAAF_24小时复发窗（拒绝分支）", "seed 最近 L2 事件距今 >24h，复发窗已过"),
    ("R11_严重高血糖", "seed 无 >16.7 持续 ≥1h 的读数"),
    ("R57_15-15三轮无效强制升级就医", "rounds 由 AlertAck 累计得出，预演不落库无法累计；rounds_15_15 非声明参数"),
    ("R53_低置信通道不得独立触发危急告警（新案例）", "唯一 OCR 告警 A-P0045-ocr-01 已被 golden-22 覆盖；OCR 读数值 4–12 不构成危急"),
    ("R44_高危用药禁止闭环（新案例）", "唯一高危用药告警 A-P0045-02 已被 golden-23 覆盖"),
    ("C15_服务包禁止捆绑分佣", "commission_config 非声明参数"),
    ("C1_器械经营资质闸（创建服务包分支）", "SELL 词表不可见，不构造猜测性实参"),
    ("D13_签发反橡皮图章检测", "soft 规则不阻断提交，无法作为 rejected 标签；query 侧已由 golden-07 覆盖"),
    ("C17_机构与门诊命名合规 / C11 / C16（新案例）", "发布宣传素材只有 c-promo-01 一条素材，已被 golden-26 覆盖；org_name 非声明参数"),
    ("D10_用药建议拦截（审核输出内容分支）", "seed 无含药名剂量的待审内容"),
    ("D11a（判定缓解 / 放宽阈值分支）", "两动作无 signer 参数，资质按调用者角色（医师）退回角色门"),
    ("R17_GMI与HbA1c不一致", "P0007 GMI 6.15 与 HbA1c 6.1 偏差 <0.5"),
    ("R33_停药观察期反弹预警", "P0007 7 天均值 6.59 <8.6，无反弹信号"),
    ("多跳 steps 查询", "seed 未 put_link，内存库 search_around 恒为空；tier 2 以单起点 where 表达跨对象推理"),
    ("未实现的 45 个动作 / 17 条规则", "__init__.py 仍为 NotImplementedError，不生成"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-cases", required=True, type=Path)
    ap.add_argument("--out-routes", required=True, type=Path)
    ap.add_argument("--engine-root", type=Path, default=Path("/Users/liuyameng/Codes/onto-fundary-plugins"))
    ap.add_argument("--evolve-scripts", type=Path, default=Path("/Users/liuyameng/Codes/astra-studio-plugins/studio-evolve/scripts"))
    ap.add_argument("--golden", type=Path, default=HERE / "golden.yaml")
    a = ap.parse_args()

    # 动态实参
    sys.path.insert(0, str(a.engine_root)); sys.path.insert(0, str(a.evolve_scripts))
    sys.argv = ["x"]
    import runner_onto_engine as R  # noqa
    from clife_onto_engine.query import InMemoryStore
    plugin = R.load_plugin(HERE.parent)
    store = InMemoryStore(); plugin.seed_reference_data(store)
    for marker, fn, why in (("__R04A_REJECT__", resolve_r04a_reject, "seed 里找不到 g∈[3.0,3.9) 且前值 ≥3.9 的读数"),
                            ("__R04A_COMMIT__", resolve_r04a_commit, "seed 里找不到回升段的 Level 1 读数对（R05 会要求预测性告警证据）")):
        dyn = fn(store)
        for c in CASES:
            if c["q"] == marker:
                if dyn is None:
                    c["skip"] = why
                else:
                    c["q"], c["route"], c["variants"] = dyn[0], dyn[1], [(k, vq, vr) for k, vq, vr in dyn[2]]

    import yaml
    golden = yaml.safe_load(a.golden.read_text(encoding="utf-8"))
    gitems = golden if isinstance(golden, list) else next(v for v in golden.values() if isinstance(v, list))
    gkeys = {(str(g["expect"]), tuple(sorted(str(x) for x in (g.get("elements") or [])))) for g in gitems}

    a.out_cases.mkdir(parents=True, exist_ok=True)
    routes: dict = {}
    counts: dict = {}
    written = []
    for c in CASES:
        if c.get("skip"):
            continue
        key = (c["expect"], tuple(sorted(c["elements"])))
        if key in gkeys:
            c["skip"] = "与 golden 重复（expect + elements）"; continue
        fam = c["family"]; counts[fam] = counts.get(fam, 0) + 1
        cid = f"{fam}-{counts[fam]:02d}"
        variants = [{"kind": k, "q": vq} for k, vq, _ in c["variants"]]
        doc = {"id": cid, "q": c["q"], "expect": c["expect"], "tier": c["tier"], "family": fam, "origin": "sim", "observed_at": TODAY,
               "elements": c["elements"], "label": {"answer": c["answer"], "source": "simulate"}, "variants": variants}
        if c.get("note"):
            doc["note"] = c["note"]
        (a.out_cases / f"{cid}.yaml").write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding="utf-8")
        routes[c["q"]] = c["route"]
        for k, vq, vr in c["variants"]:
            routes[vq] = vr if vr is not None else c["route"]
        written.append(doc)
    a.out_routes.write_text(json.dumps(routes, ensure_ascii=False, indent=1), encoding="utf-8")
    tiers = {}
    for d in written:
        tiers[d["tier"]] = tiers.get(d["tier"], 0) + 1
    nvar = sum(len(d["variants"]) for d in written)
    print(f"写出 {len(written)} 条案例（tier {dict(sorted(tiers.items()))}；family {len(counts)}：{counts}）· 变体 {nvar} · 路由 {len(routes)} 条 → {a.out_cases} / {a.out_routes}")
    for c in CASES:
        if c.get("skip"):
            print(f"  跳过：{c['q'][:40]} —— {c['skip']}")
    print(f"SKIPPED(FDE TODO / seed 不可达) {len(SKIPPED)} 项：")
    for n, why in SKIPPED:
        print(f"  - {n}：{why}")
    print(f"专家抽检删除 {len(EXPERT_DELETED)} 项：")
    for n, why in EXPERT_DELETED:
        print(f"  - {n}：{why}")


if __name__ == "__main__":
    main()
