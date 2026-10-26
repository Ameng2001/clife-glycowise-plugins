"""glycowise 本体插件 —— 由 studio-ontology 从 ontology-map 编译生成。
bounded_context: 控糖服务（CGM 数据摄入 → 指标 → 临床规则 → 方案签发 → 履约与缓解判定）。仅 import clife_onto_engine.sdk。

注意区分本仓库的两类插件，别混：
  · plugins/glycowise/（本文件）  = clife-onto-engine 的 Python 本体插件，由 /studio-ontology:compile 产出，
    在引擎仓库内被加载，提供 Object/Link/Function/Rule/Action/Mapping/CQ 七个 SPI 槽位。
  · glycowise-compliance/ 等四个 = studio 的 Claude Code 技能插件（skill-map 的产物），是给 Claude Code
    用的 skill/agent 包，与本体引擎无关，两者不共享代码也不互相 import。

编译边界（诚实边界）：declarative 规则的函数体由 check 全自动生成；function-backed 规则体、Action 回写
逻辑、参考数据一律只出骨架 + TODO(FDE)，由 FDE 在 clife-onto-engine 仓库内手填，编译器一行函数体都不编。
"""
from __future__ import annotations
from pathlib import Path as _Path
from . import _fde
from clife_onto_engine.sdk import (
    Backing, EdgeSemantics, Evaluation, HilPolicy, LinkType, ObjectType, ParamSpec,
    PropertySpec, RuleResult, Severity, spi,
)

ONTOLOGY = "glycowise"

# 规则优先级带与生效阶段（IR §4.1/§4.2 的一等字段，随规则一并保留供编排层读取）。
# priority 数值小者先评估、先抢占；phase: P1 一期 / P2 二期 / P1+P2 两期 / 系统级 平台前置。
RULE_BANDS = {
    "低血糖优先抢占": {"priority": 99, "phase": "P1+P2"},
    "R03a_Level2低血糖_实时告警": {"priority": 100, "phase": "P2"},
    "R04a_Level1低血糖_实时告警": {"priority": 105, "phase": "P2"},
    "R03b_Level2低血糖_回顾事件统计": {"priority": 110, "phase": "P1+P2"},
    "R04b_Level1低血糖_回顾事件统计": {"priority": 115, "phase": "P1+P2"},
    "R02_传感器压迫伪差识别": {"priority": 120, "phase": "P1+P2"},
    "R05_即将低血糖预测告警": {"priority": 125, "phase": "P2"},
    "R06_快速下降箭头提示": {"priority": 130, "phase": "P2"},
    "R07_夜间低血糖事件": {"priority": 135, "phase": "P1+P2"},
    "R08_睡前低值预警": {"priority": 140, "phase": "P1+P2"},
    "R09_TBR超标触发去强化审查": {"priority": 145, "phase": "P1+P2"},
    "R10_低血糖无感知线索": {"priority": 148, "phase": "P1+P2"},
    "R46_IAH高危阈值上调且禁止静音": {"priority": 149, "phase": "P1+P2"},
    "R34_HAAF_24小时复发窗": {"priority": 150, "phase": "P1+P2"},
    "R44_高危用药禁止闭环": {"priority": 155, "phase": "P1+P2"},
    "R57_15-15三轮无效强制升级就医": {"priority": 152, "phase": "P1+P2"},
    "R58_Level3严重低血糖强制转诊": {"priority": 153, "phase": "P1+P2"},
    "R59_老年非典型症状疑似低血糖": {"priority": 154, "phase": "P1+P2"},
    "R11_严重高血糖": {"priority": 200, "phase": "P1+P2"},
    "R12_SGLT2i酮症警觉": {"priority": 205, "phase": "P1+P2"},
    "R13_TAR_L2超标": {"priority": 210, "phase": "P1+P2"},
    "R14_TAR_L1超标": {"priority": 215, "phase": "P1+P2"},
    "R15_TIR未达标": {"priority": 220, "phase": "P1+P2"},
    "R22_黎明现象": {"priority": 225, "phase": "P1+P2"},
    "R16a_波动超标_硬": {"priority": 300, "phase": "P1+P2"},
    "R16b_波动偏高_软_中国口径": {"priority": 305, "phase": "P1+P2"},
    "R17_GMI与HbA1c不一致": {"priority": 310, "phase": "P1+P2"},
    "R19_餐后高响应": {"priority": 315, "phase": "P1+P2"},
    "R20_餐后极高响应": {"priority": 320, "phase": "P1+P2"},
    "R21_餐次数据混叠排除": {"priority": 325, "phase": "P1+P2"},
    "R47_跨品牌配对排除": {"priority": 328, "phase": "P1+P2"},
    "R36_active率超100自检": {"priority": 335, "phase": "P1+P2"},
    "R48_去重键必须用传感器序号": {"priority": 340, "phase": "P1+P2"},
    "R23_运动前低值": {"priority": 400, "phase": "P2"},
    "R24a_运动前高值查酮体": {"priority": 405, "phase": "P2"},
    "R24b_运动前极高值一律不宜运动": {"priority": 406, "phase": "P2"},
    "R25_运动中下降": {"priority": 410, "phase": "P2"},
    "R26_餐后步行提醒": {"priority": 415, "phase": "P1+P2"},
    "R27_运动后延迟低血糖": {"priority": 420, "phase": "P1+P2"},
    "R01_数据充分性门槛_仅管结论层": {"priority": 500, "phase": "P1+P2"},
    "R28_老年目标切换": {"priority": 505, "phase": "P1+P2"},
    "R31_妊娠模式切换": {"priority": 510, "phase": "P1+P2"},
    "R42_急性混杂窗口禁止出结论": {"priority": 508, "phase": "P1+P2"},
    "R49_缺参数时按最保守执行": {"priority": 512, "phase": "P1+P2"},
    "R18_CGM服务分层_内部标签": {"priority": 515, "phase": "P1+P2"},
    "R29_缓解判定": {"priority": 520, "phase": "P1+P2"},
    "R30_缓解适宜人群筛选_ABCD": {"priority": 525, "phase": "P1+P2"},
    "R33_停药观察期反弹预警": {"priority": 530, "phase": "P1+P2"},
    "R37_疑似1型LADA红旗": {"priority": 535, "phase": "P1+P2"},
    "R35_夜间覆盖不足禁强化": {"priority": 540, "phase": "P1+P2"},
    "R50_夜间低覆盖高危用药进临床队列": {"priority": 542, "phase": "P1+P2"},
    "R41_器械交易主体与收货合规": {"priority": 545, "phase": "P1+P2"},
    "R32_产品推荐合规闸": {"priority": 600, "phase": "P1+P2"},
    "D8_禁用词拦截": {"priority": 605, "phase": "P1+P2"},
    "C9_AI方案禁止直接推送": {"priority": 610, "phase": "P1+P2"},
    "D9_产品功效声称拦截": {"priority": 615, "phase": "P1+P2"},
    "D10_用药建议拦截": {"priority": 618, "phase": "P1+P2"},
    "D11_未确认分型分级措辞拦截": {"priority": 620, "phase": "P1+P2"},
    "R51_分层结论默认不可披露患者": {"priority": 622, "phase": "P1+P2"},
    "D11a_签发人资质失效自动冻结": {"priority": 625, "phase": "P1+P2"},
    "D12_签发人归属分流": {"priority": 628, "phase": "P1+P2"},
    "R45_紧急告警豁免关键词闸": {"priority": 630, "phase": "P1+P2"},
    "R56_告警模板预审冻结": {"priority": 631, "phase": "P1+P2"},
    "R52_回填读数不得触发实时告警": {"priority": 632, "phase": "P1+P2"},
    "R53_低置信通道不得独立触发危急告警": {"priority": 634, "phase": "P1+P2"},
    "D13_签发反橡皮图章检测": {"priority": 638, "phase": "P1+P2"},
    "C1_器械经营资质闸": {"priority": 650, "phase": "P1+P2"},
    "C2_网络销售备案与证照公示": {"priority": 655, "phase": "P1+P2"},
    "C3_敏感个人信息单独同意": {"priority": 660, "phase": "P1+P2"},
    "C4_数据用于产品推荐须单独同意": {"priority": 665, "phase": "P1+P2"},
    "C5_厂商云对接协议与PIPIA": {"priority": 670, "phase": "P1+P2"},
    "C6_群内数据最小可见范围": {"priority": 675, "phase": "P1+P2"},
    "C7_患者数据禁止存放非平台工具": {"priority": 680, "phase": "P1+P2"},
    "C8_数据出境与境外云禁止": {"priority": 685, "phase": "P1+P2"},
    "C21_数据留存与审计日志": {"priority": 690, "phase": "系统级"},
    "C11_分型输出制度层不得当诊断": {"priority": 700, "phase": "P1+P2"},
    "C12_生成式AI备案与算法备案": {"priority": 705, "phase": "系统级"},
    "C13_服务与产品物理分离": {"priority": 710, "phase": "P1+P2"},
    "C14_产品标签合规校验": {"priority": 715, "phase": "P1+P2"},
    "C15_服务包禁止捆绑分佣": {"priority": 720, "phase": "P1+P2"},
    "C16_禁止发布患者前后对比案例": {"priority": 725, "phase": "P1+P2"},
    "C17_机构与门诊命名合规": {"priority": 730, "phase": "P1+P2"},
    "C18_非医疗机构不得实施诊疗": {"priority": 735, "phase": "P1+P2"},
    "C19_线上随访边界": {"priority": 740, "phase": "P1+P2"},
    "C20_危急值须系统自动告警并记录响应": {"priority": 745, "phase": "P2"},
    "C22_免责声明强制展示": {"priority": 748, "phase": "P1+P2"},
    "R38_告警兜底配置未完成禁止佩戴": {"priority": 750, "phase": "P2"},
    "R39_覆盖告知未留痕禁止入组成功": {"priority": 755, "phase": "P1+P2"},
    "R54_服务话术不得含夜间安全承诺": {"priority": 758, "phase": "P1+P2"},
    "R40_老年画像禁止仅靠自觉同步": {"priority": 760, "phase": "P1+P2"},
    "R43_落库验证未通过禁止入组成功": {"priority": 765, "phase": "P1+P2"},
    "R55_显示口径_没有数据不得说成没有异常": {"priority": 768, "phase": "P1+P2"},
}


# ============================================================================
# §1 Objects —— 62 个
# ============================================================================

# 出处：behavior-matrix §4/§6；domain-canvas D1；daily-monitoring §2.1
spi.registry.add_object(ObjectType(
    name="GlucoseReading", namespace=ONTOLOGY, primary_key="reading_id",
    properties=(
        PropertySpec("patient_id", "string"),  # FDE：对象声明补齐（mappings/objects.yaml 已列）
        PropertySpec("value_raw", "number", required=True, classification="confidential"),
        PropertySpec("unit_raw", "enum", required=True),  # 取值：mmol/L|mg/dL
        PropertySpec("value_mmol", "number", unit="mmol/L"),
        PropertySpec("device_time", "string"),
        PropertySpec("time_utc", "string"),
        PropertySpec("tz_provenance", "enum", required=True),  # 取值：device_reported|vendor_reported|patient_profile_inferred|upload_day_assumed
        PropertySpec("source_channel", "enum"),  # 取值：vendor_api|sdk_ble_direct|ble_gls_1808|ocr_upload|manual_entry|staff_entry
        PropertySpec("source_confidence", "number"),
        PropertySpec("quality_flag", "enum"),  # 取值：clean|warmup|noise|out_of_range|superseded|suspect_duplicate|reattached
        PropertySpec("is_backfill", "boolean"),
        PropertySpec("data_age", "string"),
        PropertySpec("sensor_serial", "string"),
        PropertySpec("dedup_key", "string"),
    ),
    states=("ingested", "quality_tagged", "superseded", "retracted", "corrected"),
    initial_state="ingested",
))

# 出处：behavior-matrix §6
spi.registry.add_object(ObjectType(
    name="IngestBatch", namespace=ONTOLOGY, primary_key="batch_id",
    properties=(
        PropertySpec("channel", "string"),
        PropertySpec("record_count", "number"),
        PropertySpec("status", "enum"),  # 取值：pending|committed|rejected|rolled_back
    ),
    states=("pending", "committed", "rejected", "rolled_back"),
    initial_state="pending",
))

# 出处：behavior-matrix §6；daily-monitoring D1b
spi.registry.add_object(ObjectType(
    name="VendorSummarySnapshot", namespace=ONTOLOGY, primary_key="snapshot_id",
    properties=(
        PropertySpec("vendor", "string", required=True),
        PropertySpec("algo_version", "string", required=True),
        PropertySpec("denominator_def", "string", required=True),
        PropertySpec("metric_provenance", "string"),
    ),
    states=("recorded",),
    initial_state="recorded",
))

# 出处：domain-canvas D1；processes/README
spi.registry.add_object(ObjectType(
    name="ChannelRegistry", namespace=ONTOLOGY, primary_key="channel_id",
    properties=(
        PropertySpec("vendor", "string", required=True),
        PropertySpec("model", "string"),
        PropertySpec("capability_level", "enum", required=True),  # 取值：cloud_api|report_only|pilot|none
        PropertySpec("storage_region", "string", required=True),
        PropertySpec("sampling_interval", "number", unit="分钟", required=True),
        PropertySpec("warmup_minutes", "number"),
        PropertySpec("max_window_days", "number"),
        PropertySpec("rate_limit", "number"),
        PropertySpec("is_incremental_cursor", "boolean"),
        PropertySpec("supports_realtime_alert", "boolean"),
        PropertySpec("observed_latency_p95", "number"),
        PropertySpec("dpa_no", "string"),
    ),
    states=("draft", "active", "deprecated"),
    initial_state="draft",
))

# 出处：behavior-matrix §6；domain-canvas D8a
spi.registry.add_object(ObjectType(
    name="DeviceModel", namespace=ONTOLOGY, primary_key="model_id",
    properties=(
        PropertySpec("vendor", "string", required=True),
        PropertySpec("sampling_interval", "number", unit="分钟"),
        PropertySpec("warmup_minutes", "number"),
        PropertySpec("expiry_days", "number"),
        PropertySpec("calibration_free", "boolean"),
        PropertySpec("native_unit", "string"),
        PropertySpec("mard_pct", "number"),
        PropertySpec("sdk_protocol_version", "string"),
    ),
    states=("active", "deprecated"),
    initial_state="active",
))

# 出处：confirmed-facts B-13、R-2；processes/README。一期取值域只有 none|patient_phone；gateway_box 为二期占位
spi.registry.add_object(ObjectType(
    name="CarrierRegistry", namespace=ONTOLOGY, primary_key="patient_id",
    properties=(
        PropertySpec("carrier_type", "enum", required=True),  # 取值：none|patient_phone|gateway_box
        PropertySpec("last_sync_at", "string"),
        PropertySpec("coverage_window", "string"),
        PropertySpec("supports_local_forced_alert", "boolean"),
        PropertySpec("sync_plan_ref", "ref(SyncPlan)"),
    ),
    states=("registered", "active", "degraded"),
    initial_state="registered",
))

# 出处：behavior-matrix §6。**生效阶段=P2**（confirmed-facts B-13：一期不做采集盒）
spi.registry.add_object(ObjectType(
    name="GatewayDevice", namespace=ONTOLOGY, primary_key="sn",
    properties=(
        PropertySpec("model", "string"),
        PropertySpec("firmware_version", "string"),
        PropertySpec("bound_patient_id", "ref(PatientProfile)"),
        PropertySpec("bound_at", "string"),
        PropertySpec("last_heartbeat_at", "string"),
        PropertySpec("online", "boolean"),
        PropertySpec("unbound_at", "string"),
        PropertySpec("returned_at", "string"),
        PropertySpec("asset_status", "enum"),  # 取值：未配发|在用|已回收|遗失
    ),
    states=("未配发", "已绑定", "在线", "离线", "已解绑", "已归还"),
    initial_state="未配发",
))

# 出处：behavior-matrix §6；domain-canvas D8a
spi.registry.add_object(ObjectType(
    name="SensorSession", namespace=ONTOLOGY, primary_key="session_id",
    properties=(
        PropertySpec("sensor_serial", "string", required=True),
        PropertySpec("vendor", "string"),
        PropertySpec("sensor_model", "string"),
        PropertySpec("placement_time", "string", required=True),
        PropertySpec("warmup_minutes", "number"),
        PropertySpec("expected_sampling_interval", "number", unit="分钟"),
        PropertySpec("expiry_days", "number"),
        PropertySpec("end_reason", "enum"),  # 取值：replaced|fallen_off|expired|failed_at_placement
    ),
    states=("opened", "warmup", "active", "expired", "fallen_off", "replaced", "closed"),
    initial_state="opened",
))

# 出处：behavior-matrix §6；domain-canvas §3.3
spi.registry.add_object(ObjectType(
    name="PatientTimeBaseline", namespace=ONTOLOGY, primary_key="patient_id",
    properties=(
        PropertySpec("patient_phone_tz", "string"),
        PropertySpec("patient_phone_clock_offset", "number"),
        PropertySpec("device_clock_offset", "number"),
        PropertySpec("tz_baseline", "string"),
    ),
    states=("collected", "corrected"),
    initial_state="collected",
))

# 出处：enrollment.md D11e
spi.registry.add_object(ObjectType(
    name="SyncPlan", namespace=ONTOLOGY, primary_key="patient_id",
    properties=(
        PropertySpec("trigger_type", "enum", required=True),  # 取值：到店自动|主动打开|子女协助|同住家属
        PropertySpec("expected_interval", "number", unit="小时"),
        PropertySpec("assist_person", "string"),
    ),
    states=("established", "revised"),
    initial_state="established",
))

# 出处：domain-canvas D7；behavior-matrix §6
spi.registry.add_object(ObjectType(
    name="ConsentRecord", namespace=ONTOLOGY, primary_key="consent_id",
    properties=(
        PropertySpec("patient_id", "required"),
        PropertySpec("scope_items", "list", required=True),
        PropertySpec("version", "string", required=True),
        PropertySpec("signed_at", "string", required=True),
        PropertySpec("ip_device", "string", classification="confidential"),
        PropertySpec("hash", "string"),
        PropertySpec("legacy_import", "boolean"),
    ),
    states=("granted", "scope_changed", "revoked"),
    initial_state="granted",
))

# 出处：domain-canvas D7
spi.registry.add_object(ObjectType(
    name="ConsentRevocation", namespace=ONTOLOGY, primary_key="revocation_id",
    properties=(
        PropertySpec("patient_id", "required"),
        PropertySpec("scope", "list", required=True),
        PropertySpec("revoked_at", "string", required=True),
        PropertySpec("executed_at", "string"),
        PropertySpec("executor", "string"),
    ),
    states=("raised", "executed"),
    initial_state="raised",
))

# 出处：behavior-matrix §5.1
spi.registry.add_object(ObjectType(
    name="ContactConsent", namespace=ONTOLOGY, primary_key="contact_id",
    properties=(
        PropertySpec("patient_id", "required"),
        PropertySpec("contact_person", "string", required=True),
        PropertySpec("confirmed_at", "string"),
        PropertySpec("method", "string"),
    ),
    states=("pending", "confirmed"),
    initial_state="pending",
))

# 出处：behavior-matrix §6
spi.registry.add_object(ObjectType(
    name="VendorGrant", namespace=ONTOLOGY, primary_key="grant_id",
    properties=(
        PropertySpec("vendor", "string", required=True),
        PropertySpec("patient_id", "required"),
        PropertySpec("granted_at", "string"),
        PropertySpec("scope", "list"),
        PropertySpec("expires_at", "string"),
        PropertySpec("status", "enum"),  # 取值：active|revoked|expired
    ),
    states=("active", "revoked", "expired"),
    initial_state="active",
))

# 出处：behavior-matrix §6；domain-canvas D15
spi.registry.add_object(ObjectType(
    name="PatientProfile", namespace=ONTOLOGY, primary_key="patient_id",
    properties=(
        PropertySpec("age", "number", required=True),
        PropertySpec("pregnant", "boolean"),
        PropertySpec("meds", "list", classification="confidential"),
        PropertySpec("health_tier", "enum"),  # 取值：良好|中等|差
        PropertySpec("target_profile", "enum"),  # 取值：adult|elderly|pregnancy
        PropertySpec("is_iah_high_risk", "boolean"),
        PropertySpec("eGFR", "number"),
        PropertySpec("renal_unknown", "boolean"),
        PropertySpec("tier_label", "string"),
        PropertySpec("disclosure_approved", "boolean"),
        PropertySpec("remission_status", "enum"),  # 取值：none|candidate|in_remission|relapsed
        PropertySpec("away_mode", "boolean"),
    ),
    states=("draft", "baseline_complete", "active", "exited"),
    initial_state="draft",
))

# 出处：behavior-matrix §6/§7.1 G1b
spi.registry.add_object(ObjectType(
    name="MedClassHint", namespace=ONTOLOGY, primary_key="hint_id",
    properties=(
        PropertySpec("patient_id", "required"),
        PropertySpec("hint_source", "enum", required=True),  # 取值：self_report|drug_box_photo
        PropertySpec("hypo_risk_med", "boolean"),
        PropertySpec("sglt2i", "boolean"),
    ),
    states=("collected", "confirmed", "discarded"),
    initial_state="collected",
))

# 出处：behavior-matrix §6
spi.registry.add_object(ObjectType(
    name="LabResult", namespace=ONTOLOGY, primary_key="lab_result_id",
    properties=(
        PropertySpec("patient_id", "required"),
        PropertySpec("value", "number", classification="confidential"),
        PropertySpec("method", "string", required=True),
        PropertySpec("lab_id", "string"),
        PropertySpec("is_ngsp_certified", "boolean"),
        PropertySpec("specimen_type", "string"),
        PropertySpec("measured_at", "string", required=True),
    ),
    states=("recorded",),
    initial_state="recorded",
))

# 出处：behavior-matrix §6/§7.1 G10
spi.registry.add_object(ObjectType(
    name="BodyMeasurement", namespace=ONTOLOGY, primary_key="measurement_id",
    properties=(
        PropertySpec("patient_id", "required"),
        PropertySpec("measured_at", "string", required=True),
        PropertySpec("device_id", "string", required=True),
        PropertySpec("protocol_version", "string", required=True),
        PropertySpec("fasting", "boolean"),
        PropertySpec("weight", "number", unit="kg"),
        PropertySpec("waist", "number", unit="cm"),
        PropertySpec("body_fat_pct", "number"),
    ),
    states=("recorded",),
    initial_state="recorded",
))

# 出处：behavior-matrix §6
spi.registry.add_object(ObjectType(
    name="PatientIdentityLink", namespace=ONTOLOGY, primary_key="patient_id",
    properties=(
        PropertySpec("wecom_external_userid", "string"),
        PropertySpec("feishu_record_id", "string"),
        PropertySpec("vendor_account_id", "string"),
    ),
    states=("active", "revoked"),
    initial_state="active",
))

# 出处：behavior-matrix §6；daily-monitoring §2.3b
spi.registry.add_object(ObjectType(
    name="AlertThreshold", namespace=ONTOLOGY, primary_key="threshold_id",
    properties=(
        PropertySpec("patient_id", "required"),
        PropertySpec("field", "string", required=True),
        PropertySpec("current_value", "number", required=True),
        PropertySpec("default_value", "number"),
        PropertySpec("safe_direction", "enum", required=True),  # 取值：收紧|放宽
    ),
    states=("active",),
    initial_state="active",
))

# 出处：同上
spi.registry.add_object(ObjectType(
    name="ThresholdChangeLog", namespace=ONTOLOGY, primary_key="log_id",
    properties=(
        PropertySpec("patient_id", "required"),
        PropertySpec("changed_by", "string", required=True),
        PropertySpec("trigger_rule", "string"),
        PropertySpec("before", "number"),
        PropertySpec("after", "number"),
        PropertySpec("effective_window", "string"),
    ),
    states=("recorded",),
    initial_state="recorded",
))

# 出处：domain-canvas D4；daily-monitoring §2.2/2.4。实时推送分支 **phase=P2**
spi.registry.add_object(ObjectType(
    name="AlertEvent", namespace=ONTOLOGY, primary_key="alert_id",
    properties=(
        PropertySpec("patient_id", "required"),
        PropertySpec("level", "enum", required=True),  # 取值：低|中|高|危急
        PropertySpec("value", "number"),
        PropertySpec("trend", "number"),
        PropertySpec("evidence", "string"),
        PropertySpec("confidence", "number"),
        PropertySpec("rule_id", "string", required=True),
        PropertySpec("is_backfill", "boolean"),
    ),
    states=(
        "raised",
        "acknowledged",
        "value_recovered",
        "escalated",
        "escalated_emergency",
        "resolved",
        "retracted",
    ),
    initial_state="raised",
))

# 出处：daily-monitoring D20
spi.registry.add_object(ObjectType(
    name="AlertAck", namespace=ONTOLOGY, primary_key="ack_id",
    properties=(
        PropertySpec("alert_id", "required"),
        PropertySpec("responder", "string", required=True),
        PropertySpec("responded_at", "string", required=True),
        PropertySpec("action_taken", "string"),
        PropertySpec("retest_value", "number"),
    ),
    states=("recorded",),
    initial_state="recorded",
))

# 出处：daily-monitoring §2.4。**phase=P2**
spi.registry.add_object(ObjectType(
    name="AlertEscalation", namespace=ONTOLOGY, primary_key="escalation_id",
    properties=(
        PropertySpec("alert_id", "required"),
        PropertySpec("level", "number", required=True),
        PropertySpec("escalated_at", "string"),
        PropertySpec("target", "string"),
    ),
    states=("raised", "closed"),
    initial_state="raised",
))

# 出处：behavior-matrix §6 A117b。**phase=P2**
spi.registry.add_object(ObjectType(
    name="AlertSuppressedLog", namespace=ONTOLOGY, primary_key="log_id",
    properties=(
        PropertySpec("alert_id", "required"),
        PropertySpec("reason", "string", required=True),
        PropertySpec("suppressed_at", "string"),
    ),
    states=("recorded",),
    initial_state="recorded",
))

# 出处：domain-canvas D2；daily-monitoring D11。一期核心安全产出：次日医师减药审查证据
spi.registry.add_object(ObjectType(
    name="HypoEpisode", namespace=ONTOLOGY, primary_key="episode_id",
    properties=(
        PropertySpec("patient_id", "required"),
        PropertySpec("start_time", "string", required=True),
        PropertySpec("end_time", "string", required=True),
        PropertySpec("min_value", "number"),
        PropertySpec("level", "enum", required=True),  # 取值：L1|L2
        PropertySpec("night_flag", "boolean"),
    ),
    states=("detected",),
    initial_state="detected",
))

# 出处：behavior-matrix §6；daily-monitoring D12b/D21
spi.registry.add_object(ObjectType(
    name="HypoState", namespace=ONTOLOGY, primary_key="patient_id",
    properties=(
        PropertySpec("prolonged_risk", "boolean"),
        PropertySpec("recurrence_window_until", "string"),
        PropertySpec("closure_blocked_reason", "string"),
    ),
    states=("none", "prolonged_risk", "recurrence_window", "closed"),
    initial_state="none",
))

# 出处：domain-canvas D3；confirmed-facts「一期特有医源性伤害路径」
spi.registry.add_object(ObjectType(
    name="CgmSummary", namespace=ONTOLOGY, primary_key="summary_id",
    properties=(
        PropertySpec("patient_id", "required"),
        PropertySpec("window_start", "string", required=True),
        PropertySpec("window_end", "string", required=True),
        PropertySpec("wear_ratio", "number"),
        PropertySpec("active_pct", "number"),
        PropertySpec("sufficiency_ok", "boolean"),
        PropertySpec("tz_uncertain", "boolean"),
        PropertySpec("brand_changed", "boolean"),
        PropertySpec("metric_provenance", "enum"),  # 取值：self_computed|vendor_reported
        PropertySpec("nocturnal_coverage_pct", "number"),
        PropertySpec("nocturnal_coverage_insufficient", "boolean"),
        PropertySpec("confounded_window", "boolean"),
        PropertySpec("days", "number"),  # FDE：窗口天数
        PropertySpec("tir_pct", "number"), PropertySpec("tbr_pct", "number"), PropertySpec("tbr_l2_pct", "number"),
        PropertySpec("tar_pct", "number"), PropertySpec("tar_l2_pct", "number"), PropertySpec("cv_pct", "number"),
        PropertySpec("gmi_pct", "number"), PropertySpec("mean_glucose", "number"),
        PropertySpec("consecutive_low_night_nights", "number"),
    ),
    states=("computed", "stale", "recomputed", "invalidated"),
    initial_state="computed",
))

# FDE 补：R56 依赖的冻结告警模板库
spi.registry.add_object(ObjectType(
    name="AlertTemplate", namespace=ONTOLOGY, primary_key="template_id",
    properties=(
        PropertySpec("level", "enum", required=True),  # 取值：低|中|高|危急
        PropertySpec("body", "string", required=True),
        PropertySpec("frozen", "boolean"),
        PropertySpec("pre_reviewed_c22", "boolean"),
        PropertySpec("pre_reviewed_r54", "boolean"),
        PropertySpec("reviewed_at", "string"),
    ),
    states=("draft", "frozen", "retired"),
    initial_state="draft",
))

# FDE 补：人群目标区间参数表（R28/R31/R46/R49 依赖；查询「老年患者的目标区间参数」直接命中）
spi.registry.add_object(ObjectType(
    name="TargetProfileParam", namespace=ONTOLOGY, primary_key="profile",
    properties=(
        PropertySpec("population", "string", required=True),
        PropertySpec("age_min", "number"),
        PropertySpec("requires_hypo_risk_med", "boolean"),
        PropertySpec("tir_target_pct", "number"),
        PropertySpec("tbr_max_pct", "number"),
        PropertySpec("tbr_l2_max_pct", "number"),
        PropertySpec("low_alert_threshold", "number"),
        PropertySpec("range_low", "number"),
        PropertySpec("range_high", "number"),
        PropertySpec("source", "string"),
    ),
))

# 出处：domain-canvas D9。`event_type` 禁用 MNT
spi.registry.add_object(ObjectType(
    name="ContextEvent", namespace=ONTOLOGY, primary_key="event_id",
    properties=(
        PropertySpec("patient_id", "required"),
        PropertySpec("event_type", "enum", required=True),  # 取值：meal|exercise|sleep|supplement_checkin|away
        PropertySpec("occurred_at", "string", required=True),
        PropertySpec("meal_time_confidence", "number"),
        PropertySpec("recorded_by", "string"),
    ),
    states=("recorded",),
    initial_state="recorded",
))

# 出处：behavior-matrix §6/§7.1 G7。R10 唯一输入
spi.registry.add_object(ObjectType(
    name="SymptomTreatmentRecord", namespace=ONTOLOGY, primary_key="record_id",
    properties=(
        PropertySpec("patient_id", "required"),
        PropertySpec("alert_id", "string"),
        PropertySpec("symptom_tag", "string"),
        PropertySpec("treatment_action", "string"),
        PropertySpec("recorded_by", "string", required=True),
        PropertySpec("recorded_at", "string", required=True),
    ),
    states=("recorded",),
    initial_state="recorded",
))

# 出处：behavior-matrix §7.1 G9
spi.registry.add_object(ObjectType(
    name="KetoneReading", namespace=ONTOLOGY, primary_key="ketone_id",
    properties=(
        PropertySpec("patient_id", "required"),
        PropertySpec("value_or_qualitative", "string", required=True),
        PropertySpec("measured_at", "string", required=True),
        PropertySpec("method", "enum"),  # 取值：血酮仪|尿酮试纸
    ),
    states=("recorded",),
    initial_state="recorded",
))

# 出处：behavior-matrix §7.1 G6；review-and-plan D2b
spi.registry.add_object(ObjectType(
    name="ClinicalContextEvent", namespace=ONTOLOGY, primary_key="event_id",
    properties=(
        PropertySpec("patient_id", "required"),
        PropertySpec("type", "enum", required=True),  # 取值：急性病|感染发热|激素使用|住院|用药调整
        PropertySpec("start_at", "string", required=True),
        PropertySpec("end_at", "string"),
    ),
    states=("recorded", "closed"),
    initial_state="recorded",
))

# 出处：domain-canvas D10
spi.registry.add_object(ObjectType(
    name="MealResponse", namespace=ONTOLOGY, primary_key="response_id",
    properties=(
        PropertySpec("patient_id", "required"),
        PropertySpec("meal_event_id", "required"),
        PropertySpec("baseline", "number"),
        PropertySpec("delta_p", "number"),
        PropertySpec("time_to_peak", "number", unit="分钟"),
        PropertySpec("iAUC_2h", "number"),
        PropertySpec("r2h", "number"),
        PropertySpec("return_to_baseline", "boolean"),
        PropertySpec("pairing_quality", "number"),
        PropertySpec("cross_brand", "boolean"),
    ),
    states=("computed",),
    initial_state="computed",
))

# 出处：behavior-matrix §6；confirmed-facts D-02。**phase=P2**
spi.registry.add_object(ObjectType(
    name="DutyRoster", namespace=ONTOLOGY, primary_key="roster_id",
    properties=(
        PropertySpec("date", "string", required=True),
        PropertySpec("slot", "string", required=True),
        PropertySpec("responder", "string"),
    ),
    states=("scheduled", "gap_detected"),
    initial_state="scheduled",
))

# 出处：behavior-matrix §6
spi.registry.add_object(ObjectType(
    name="EmergencyContact", namespace=ONTOLOGY, primary_key="contact_id",
    properties=(
        PropertySpec("patient_id", "required"),
        PropertySpec("name", "string", required=True),
        PropertySpec("phone", "string", required=True, classification="confidential"),
        PropertySpec("relation", "string"),
        PropertySpec("can_reach_onsite", "boolean"),
    ),
    states=("registered",),
    initial_state="registered",
))

# 出处：domain-canvas D5
spi.registry.add_object(ObjectType(
    name="PlanDraft", namespace=ONTOLOGY, primary_key="draft_id",
    properties=(
        PropertySpec("patient_id", "required"),
        PropertySpec("content", "string", required=True),
        PropertySpec("template_version", "string"),
        PropertySpec("med_interaction_routed", "boolean"),
        PropertySpec("direction", "enum"),  # 取值：强化|维持|去强化
    ),
    states=("drafted", "gated", "pending_signoff", "rejected"),
    initial_state="drafted",
))

# 出处：domain-canvas D5
spi.registry.add_object(ObjectType(
    name="PlanSigned", namespace=ONTOLOGY, primary_key="plan_id",
    properties=(
        PropertySpec("patient_id", "required"),
        PropertySpec("content_snapshot", "string", required=True),
        PropertySpec("signer_id", "string", required=True),
        PropertySpec("signed_at", "string", required=True),
        PropertySpec("evidence_snapshot", "string", required=True),
        PropertySpec("review_evidence_ref", "string"),
        PropertySpec("evidence_stale", "boolean"),
    ),
    states=("signed", "superseded", "revoked"),
    initial_state="signed",
))

# 出处：remission-assessment D3
spi.registry.add_object(ObjectType(
    name="TaperPlan", namespace=ONTOLOGY, primary_key="taper_id",
    properties=(
        PropertySpec("patient_id", "required"),
        PropertySpec("original_document_hash", "string", required=True),
        PropertySpec("schedule", "string", required=True),
        PropertySpec("relapse_redline", "string"),
    ),
    states=("signed", "active", "completed", "aborted"),
    initial_state="signed",
))

# 出处：domain-canvas D6a
spi.registry.add_object(ObjectType(
    name="ComplianceCheckLog", namespace=ONTOLOGY, primary_key="log_id",
    properties=(
        PropertySpec("model_version", "string"),
        PropertySpec("prompt_version", "string"),
        PropertySpec("hit_rules", "list"),
        PropertySpec("blocked_reason", "string"),
        PropertySpec("target_content_ref", "string"),
    ),
    states=("recorded",),
    initial_state="recorded",
))

# 出处：domain-canvas D6a
spi.registry.add_object(ObjectType(
    name="GateToken", namespace=ONTOLOGY, primary_key="token_id",
    properties=(
        PropertySpec("issued_at", "string", required=True),
        PropertySpec("scope", "string", required=True),
        PropertySpec("expiry", "string", required=True),
    ),
    states=("issued", "consumed", "expired"),
    initial_state="issued",
))

# 出处：domain-canvas D6a/D6b
spi.registry.add_object(ObjectType(
    name="BannedTermLibrary", namespace=ONTOLOGY, primary_key="term_id",
    properties=(
        PropertySpec("term", "string", required=True),
        PropertySpec("category", "string", required=True),
        PropertySpec("version", "string", required=True),
    ),
    states=("active", "deprecated"),
    initial_state="active",
))

# 出处：behavior-matrix §6
spi.registry.add_object(ObjectType(
    name="ComplianceIncident", namespace=ONTOLOGY, primary_key="incident_id",
    properties=(
        PropertySpec("actor", "string", required=True),
        PropertySpec("hit_text_fragment", "string"),
        PropertySpec("recorded_at", "string", required=True),
    ),
    states=("recorded", "escalated"),
    initial_state="recorded",
))

# 出处：domain-canvas D18
spi.registry.add_object(ObjectType(
    name="Credential", namespace=ONTOLOGY, primary_key="credential_id",
    properties=(
        PropertySpec("holder", "string", required=True),
        PropertySpec("credential_type", "string", required=True),
        PropertySpec("registration_no", "string", required=True),
        PropertySpec("expiry_date", "string", required=True),
        PropertySpec("status", "enum"),  # 取值：valid|expiring|revoked|frozen
    ),
    states=("valid", "expiring", "revoked", "frozen"),
    initial_state="valid",
))

# 出处：domain-canvas D11a
spi.registry.add_object(ObjectType(
    name="ServicePackage", namespace=ONTOLOGY, primary_key="package_id",
    properties=(
        PropertySpec("patient_id", "required"),
        PropertySpec("tier", "enum", required=True),  # 取值：A|B|C
        PropertySpec("start_date", "string"),
        PropertySpec("end_date", "string"),
        PropertySpec("wear_days_fulfilled", "number"),
    ),
    states=("pending", "active", "completed", "exited"),
    initial_state="pending",
))

# 出处：behavior-matrix §6
spi.registry.add_object(ObjectType(
    name="ServiceExitRecord", namespace=ONTOLOGY, primary_key="exit_id",
    properties=(
        PropertySpec("patient_id", "required"),
        PropertySpec("exit_at", "string", required=True),
        PropertySpec("exit_stage", "string"),
        PropertySpec("exit_path", "enum"),  # 取值：P1|P2|P3|P4|P5|P6
        PropertySpec("refund_amount", "number"),
        PropertySpec("fulfilled_days", "number"),
        PropertySpec("last_churn_signal", "string"),
    ),
    states=("recorded",),
    initial_state="recorded",
))

# 出处：domain-canvas D11a
spi.registry.add_object(ObjectType(
    name="ChurnSignal", namespace=ONTOLOGY, primary_key="signal_id",
    properties=(
        PropertySpec("patient_id", "required"),
        PropertySpec("code", "string", required=True),
        PropertySpec("severity", "enum"),  # 取值：黄|橙|红
        PropertySpec("applicable", "boolean"),
    ),
    states=("raised", "processed"),
    initial_state="raised",
))

# 出处：review-and-plan D17。"减药"禁入任何字段
spi.registry.add_object(ObjectType(
    name="KpiSettlement", namespace=ONTOLOGY, primary_key="settlement_id",
    properties=(
        PropertySpec("package_id", "required"),
        PropertySpec("safety_gate_passed", "boolean", required=True),
        PropertySpec("tir_delta", "number"),
        PropertySpec("settlement_result", "string"),
    ),
    states=("computed",),
    initial_state="computed",
))

# 出处：remission-assessment D3/D5
spi.registry.add_object(ObjectType(
    name="RemissionClock", namespace=ONTOLOGY, primary_key="patient_id",
    properties=(
        PropertySpec("day0", "string"),
        PropertySpec("status", "enum", required=True),  # 取值：running|reset|stopped
        PropertySpec("confirmed_by", "string"),
    ),
    states=("started", "running", "reset", "stopped"),
    initial_state="started",
))

# 出处：remission-assessment D8
spi.registry.add_object(ObjectType(
    name="RemissionAssessment", namespace=ONTOLOGY, primary_key="assessment_id",
    properties=(
        PropertySpec("patient_id", "required"),
        PropertySpec("status", "enum", required=True),  # 取值：in_remission|not_in_remission
        PropertySpec("evidence_pack_ref", "string", required=True),
        PropertySpec("method_used", "enum", required=True),  # 取值：HbA1c|GMI|FPG
    ),
    states=("assessed",),
    initial_state="assessed",
))

# 出处：enrollment.md D4/D11b/D11c
spi.registry.add_object(ObjectType(
    name="EnrollmentDecision", namespace=ONTOLOGY, primary_key="decision_id",
    properties=(
        PropertySpec("patient_id", "required"),
        PropertySpec("flags", "list"),
        PropertySpec("decided_by", "string", required=True),
        PropertySpec("decided_at", "string", required=True),
        PropertySpec("coverage_disclosed_at", "string"),
        PropertySpec("channel_verified_at_store", "boolean"),
    ),
    states=("decided", "pending_channel", "enrolled"),
    initial_state="decided",
))

# 出处：review-and-plan D13
spi.registry.add_object(ObjectType(
    name="ReviewEvidence", namespace=ONTOLOGY, primary_key="evidence_id",
    properties=(
        PropertySpec("plan_id", "required"),
        PropertySpec("opened_at", "string"),
        PropertySpec("agp_expand_count", "number"),
        PropertySpec("dwell_time", "number", unit="秒"),
        PropertySpec("diff", "string"),
        PropertySpec("review_suspicious", "boolean"),
    ),
    states=("collected",),
    initial_state="collected",
))

# 出处：behavior-matrix §6
spi.registry.add_object(ObjectType(
    name="DeliveryReceipt", namespace=ONTOLOGY, primary_key="receipt_id",
    properties=(
        PropertySpec("target", "string", required=True),
        PropertySpec("channel", "string", required=True),
        PropertySpec("delivered_at", "string"),
        PropertySpec("status", "enum"),  # 取值：requested|delivered|rejected
        PropertySpec("gate_token_ref", "string"),
    ),
    states=("requested", "delivered", "rejected"),
    initial_state="requested",
))

# 出处：behavior-matrix §7.1 G4
spi.registry.add_object(ObjectType(
    name="StoreReadinessCheck", namespace=ONTOLOGY, primary_key="check_id",
    properties=(
        PropertySpec("store_id", "string", required=True),
        PropertySpec("checked_at", "string"),
        PropertySpec("signed_by", "string"),
    ),
    states=("pending", "passed"),
    initial_state="pending",
))

# 出处：behavior-matrix §7.2
spi.registry.add_object(ObjectType(
    name="ReferralRecord", namespace=ONTOLOGY, primary_key="referral_id",
    properties=(
        PropertySpec("patient_id", "required"),
        PropertySpec("question", "string", required=True),
        PropertySpec("referred_to", "string", required=True),
        PropertySpec("referred_at", "string", required=True),
        PropertySpec("replied_at", "string"),
    ),
    states=("recorded", "replied"),
    initial_state="recorded",
))

# 出处：behavior-matrix §7.2；enrollment D2
spi.registry.add_object(ObjectType(
    name="OnsiteTriageRecord", namespace=ONTOLOGY, primary_key="record_id",
    properties=(
        PropertySpec("patient_id", "required"),
        PropertySpec("glucose_value", "number", required=True),
        PropertySpec("tier", "string"),
        PropertySpec("disposition", "string"),
    ),
    states=("recorded",),
    initial_state="recorded",
))

# 出处：behavior-matrix §6
spi.registry.add_object(ObjectType(
    name="PsychNote", namespace=ONTOLOGY, primary_key="note_id",
    properties=(
        PropertySpec("patient_id", "required"),
        PropertySpec("content", "string", classification="confidential"),
    ),
    states=("recorded",),
    initial_state="recorded",
))

# 出处：behavior-matrix §6；confirmed-facts R-3
spi.registry.add_object(ObjectType(
    name="MetricRegistry", namespace=ONTOLOGY, primary_key="metric_id",
    properties=(
        PropertySpec("name", "string", required=True),
        PropertySpec("numerator_def", "string", required=True),
        PropertySpec("denominator_def", "string", required=True),
        PropertySpec("exclusions", "string"),
        PropertySpec("version", "string", required=True),
        PropertySpec("owner", "string", required=True),
    ),
    states=("active", "deprecated"),
    initial_state="active",
))

# 出处：domain-canvas D13。只进不出，≥3 年
spi.registry.add_object(ObjectType(
    name="AuditLog", namespace=ONTOLOGY, primary_key="log_id",
    properties=(
        PropertySpec("actor", "string", required=True),
        PropertySpec("action", "string", required=True),
        PropertySpec("target", "string"),
        PropertySpec("timestamp", "string", required=True),
    ),
    states=("recorded",),
    initial_state="recorded",
))

# 出处：domain-canvas D7
spi.registry.add_object(ObjectType(
    name="DataSubjectRequest", namespace=ONTOLOGY, primary_key="request_id",
    properties=(
        PropertySpec("patient_id", "required"),
        PropertySpec("type", "enum", required=True),  # 取值：查阅|复制|更正|删除|可携|自动化决策解释
        PropertySpec("received_at", "string", required=True),
        PropertySpec("resolved_at", "string"),
    ),
    states=("received", "resolved"),
    initial_state="received",
))

# 出处：domain-canvas D18；enrollment D8
spi.registry.add_object(ObjectType(
    name="StoreEntity", namespace=ONTOLOGY, primary_key="store_id",
    properties=(
        PropertySpec("name", "string", required=True),
        PropertySpec("license_no", "string"),
        PropertySpec("medical_scope", "list"),
        PropertySpec("readiness_ref", "string"),
    ),
    states=("active", "suspended"),
    initial_state="active",
))

# 出处：domain-canvas D11a/X4；behavior-matrix §6
spi.registry.add_object(ObjectType(
    name="ProductSku", namespace=ONTOLOGY, primary_key="sku_id",
    properties=(
        PropertySpec("name", "string", required=True),
        PropertySpec("category", "enum", required=True),  # 取值：服务|食品|器械引用
        PropertySpec("label_verified", "boolean"),
        PropertySpec("commission_config", "string"),
    ),
    states=("draft", "listed", "rejected", "delisted"),
    initial_state="draft",
))

# 出处：domain-canvas D6a/D16
spi.registry.add_object(ObjectType(
    name="OutboundContent", namespace=ONTOLOGY, primary_key="content_id",
    properties=(
        PropertySpec("target_audience", "string", required=True),
        PropertySpec("body", "string", required=True),
        PropertySpec("content_type", "enum", required=True),  # 取值：方案|日报|周报|告警|宣传素材|群内答复
        PropertySpec("gate_token_ref", "string"),
        PropertySpec("disclaimer_attached", "boolean"),
    ),
    states=("drafted", "gated", "blocked", "delivered"),
    initial_state="drafted",
))


# ============================================================================
# §2 Links —— 40 条
# ============================================================================

spi.registry.add_link(LinkType("belongs_to_session", ONTOLOGY, "GlucoseReading", "SensorSession",
                               cardinality="1:N", edge_semantics=EdgeSemantics.DERIVATION))  # 按 device_time 晚绑定解析，可重算
spi.registry.add_link(LinkType("uses_device_model", ONTOLOGY, "SensorSession", "DeviceModel",
                               cardinality="1:N", edge_semantics=EdgeSemantics.DERIVATION))
spi.registry.add_link(LinkType("via_channel", ONTOLOGY, "GlucoseReading", "ChannelRegistry",
                               cardinality="1:N", edge_semantics=EdgeSemantics.DERIVATION))
spi.registry.add_link(LinkType("has_carrier", ONTOLOGY, "PatientProfile", "CarrierRegistry",
                               cardinality="1:1", edge_semantics=EdgeSemantics.DERIVATION))
spi.registry.add_link(LinkType("has_sync_plan", ONTOLOGY, "PatientProfile", "SyncPlan",
                               cardinality="1:1", edge_semantics=EdgeSemantics.DERIVATION))
spi.registry.add_link(LinkType("bound_gateway", ONTOLOGY, "CarrierRegistry", "GatewayDevice",
                               cardinality="1:1", edge_semantics=EdgeSemantics.DERIVATION))  # phase=P2
spi.registry.add_link(LinkType("computed_from", ONTOLOGY, "CgmSummary", "GlucoseReading",
                               cardinality="1:N", edge_semantics=EdgeSemantics.DERIVATION))  # window
spi.registry.add_link(LinkType("statistically_derived_from", ONTOLOGY, "HypoEpisode", "GlucoseReading",
                               cardinality="1:N", edge_semantics=EdgeSemantics.DERIVATION))  # Danne ≥15min 口径，**仅供统计**
spi.registry.add_link(LinkType("triggered_by_reading", ONTOLOGY, "AlertEvent", "GlucoseReading",
                               cardinality="1:N", edge_semantics=EdgeSemantics.ROOT_CAUSE))  # 触发读数即告警成立的根因，溯源可终止；连续 2 读数口径
spi.registry.add_link(LinkType("gates_alert_closure", ONTOLOGY, "HypoState", "AlertEvent",
                               cardinality="1:N", edge_semantics=EdgeSemantics.ROOT_CAUSE))  # closure_blocked_reason 是"能否闭环"的终止判据
spi.registry.add_link(LinkType("escalates_via", ONTOLOGY, "AlertEvent", "AlertEscalation",
                               cardinality="1:N", edge_semantics=EdgeSemantics.DERIVATION))  # phase=P2
spi.registry.add_link(LinkType("acknowledged_by", ONTOLOGY, "AlertEvent", "AlertAck",
                               cardinality="1:1", edge_semantics=EdgeSemantics.DERIVATION))
spi.registry.add_link(LinkType("suppressed_as", ONTOLOGY, "AlertEvent", "AlertSuppressedLog",
                               cardinality="1:1", edge_semantics=EdgeSemantics.DERIVATION))  # phase=P2
spi.registry.add_link(LinkType("gated_by_duty_roster", ONTOLOGY, "AlertEscalation", "DutyRoster",
                               cardinality="1:N", edge_semantics=EdgeSemantics.ROOT_CAUSE))  # 值班链尾留空即安全事故直接根因，不是待查假设
spi.registry.add_link(LinkType("unblocks_closure", ONTOLOGY, "SymptomTreatmentRecord", "AlertEvent",
                               cardinality="1:N", edge_semantics=EdgeSemantics.DERIVATION))  # 判据之一，仍需结合 HypoState
spi.registry.add_link(LinkType("confirms_ketosis", ONTOLOGY, "KetoneReading", "AlertEvent",
                               cardinality="1:N", edge_semantics=EdgeSemantics.ROOT_CAUSE))  # 酮体阳性是终止酮症判断链的客观证据
spi.registry.add_link(LinkType("based_on_summary", ONTOLOGY, "PlanDraft", "CgmSummary",
                               cardinality="1:N", edge_semantics=EdgeSemantics.HYPOTHESIS))  # 草稿依据指标，须经人工复核才成立，不可终止推理
spi.registry.add_link(LinkType("supersedes", ONTOLOGY, "PlanSigned", "PlanDraft",
                               cardinality="1:1", edge_semantics=EdgeSemantics.DERIVATION))
spi.registry.add_link(LinkType("gated_by_token", ONTOLOGY, "OutboundContent", "GateToken",
                               cardinality="1:N", edge_semantics=EdgeSemantics.ROOT_CAUSE))  # 无 token 硬拒投递
spi.registry.add_link(LinkType("requires_credential", ONTOLOGY, "PlanSigned", "Credential",
                               cardinality="1:N", edge_semantics=EdgeSemantics.ROOT_CAUSE))  # 资质失效即签不出，直接根因
spi.registry.add_link(LinkType("gates_delivery", ONTOLOGY, "ComplianceCheckLog", "DeliveryReceipt",
                               cardinality="1:N", edge_semantics=EdgeSemantics.ROOT_CAUSE))  # gate.blocked 直接阻断投递
spi.registry.add_link(LinkType("marks_confounded", ONTOLOGY, "ClinicalContextEvent", "CgmSummary",
                               cardinality="1:N", edge_semantics=EdgeSemantics.ROOT_CAUSE))  # 命中即终止该窗口的分层/续约/缓解资格
spi.registry.add_link(LinkType("feeds_rule_gate", ONTOLOGY, "MedClassHint", "PatientProfile",
                               cardinality="1:N", edge_semantics=EdgeSemantics.HYPOTHESIS))  # 未经医师确认只能作规则开闸的假设性输入，永不作诊疗根因
spi.registry.add_link(LinkType("starts_clock", ONTOLOGY, "TaperPlan", "RemissionClock",
                               cardinality="1:1", edge_semantics=EdgeSemantics.DERIVATION))  # day0
spi.registry.add_link(LinkType("gated_by_meds", ONTOLOGY, "RemissionClock", "PatientProfile",
                               cardinality="1:N", edge_semantics=EdgeSemantics.ROOT_CAUSE))  # 任一降糖药在用即清零，唯一判据
spi.registry.add_link(LinkType("assessed_with_lab", ONTOLOGY, "RemissionAssessment", "LabResult",
                               cardinality="N:N", edge_semantics=EdgeSemantics.DERIVATION))  # 同一方法学配对
spi.registry.add_link(LinkType("assessed_with_gmi", ONTOLOGY, "RemissionAssessment", "CgmSummary",
                               cardinality="1:N", edge_semantics=EdgeSemantics.HYPOTHESIS))  # GMI 是否可用还要核验四条前提，不能直接当根因
spi.registry.add_link(LinkType("triggers_settlement", ONTOLOGY, "ServicePackage", "KpiSettlement",
                               cardinality="1:1", edge_semantics=EdgeSemantics.DERIVATION))
spi.registry.add_link(LinkType("gated_by_safety_gate", ONTOLOGY, "KpiSettlement", "CgmSummary",
                               cardinality="1:N", edge_semantics=EdgeSemantics.ROOT_CAUSE))  # TBR 安全门一票否决
spi.registry.add_link(LinkType("grounded_by_exit", ONTOLOGY, "ChurnSignal", "ServiceExitRecord",
                               cardinality="1:N", edge_semantics=EdgeSemantics.ROOT_CAUSE))  # 退出记录是流失信号真假阳性的 ground truth
spi.registry.add_link(LinkType("requires_consent_enroll", ONTOLOGY, "EnrollmentDecision", "ConsentRecord",
                               cardinality="1:1", edge_semantics=EdgeSemantics.ROOT_CAUSE))  # 无单独同意即挂起，终止入组推理
spi.registry.add_link(LinkType("requires_consent_session", ONTOLOGY, "SensorSession", "ConsentRecord",
                               cardinality="1:N", edge_semantics=EdgeSemantics.ROOT_CAUSE))  # 授权前置于建 session，个人信息处理硬性前提
spi.registry.add_link(LinkType("cascades_from_revocation", ONTOLOGY, "ConsentRevocation", "ConsentRecord",
                               cardinality="1:1", edge_semantics=EdgeSemantics.DERIVATION))
spi.registry.add_link(LinkType("discloses_coverage", ONTOLOGY, "CarrierRegistry", "PatientProfile",
                               cardinality="1:1", edge_semantics=EdgeSemantics.DERIVATION))  # 覆盖状态供出口话术拦截读取
spi.registry.add_link(LinkType("paired_with_meal", ONTOLOGY, "MealResponse", "ContextEvent",
                               cardinality="1:1", edge_semantics=EdgeSemantics.DERIVATION))  # [t-60, t+180] 配对窗
spi.registry.add_link(LinkType("held_by", ONTOLOGY, "Credential", "StoreEntity",
                               cardinality="1:N", edge_semantics=EdgeSemantics.DERIVATION))
spi.registry.add_link(LinkType("gated_by_readiness", ONTOLOGY, "ServicePackage", "StoreReadinessCheck",
                               cardinality="1:N", edge_semantics=EdgeSemantics.ROOT_CAUSE))  # 未完成清查的门店不予开通
spi.registry.add_link(LinkType("listed_as", ONTOLOGY, "ProductSku", "StoreEntity",
                               cardinality="1:N", edge_semantics=EdgeSemantics.DERIVATION))
spi.registry.add_link(LinkType("delivered_as", ONTOLOGY, "OutboundContent", "DeliveryReceipt",
                               cardinality="1:1", edge_semantics=EdgeSemantics.DERIVATION))
spi.registry.add_link(LinkType("audited_by", ONTOLOGY, "AuditLog", "PatientProfile",
                               cardinality="1:N", edge_semantics=EdgeSemantics.DERIVATION))  # 只进不出


# ============================================================================
# §3 Functions（派生量）—— 28 个。只读、无副作用；函数体由 FDE 手填。
# ============================================================================

@spi.function(ONTOLOGY, "TIR", reads=("GlucoseReading", "PatientProfile"))
def TIR(ctx):
    """目标区间内读数占比。区间随 target_profile 切换：adult 3.9–10.0、elderly 3.9–10.0（目标值不同）、pregnancy 3.5–7.8。分子只计 source_channel ∈ {vendor_api, sdk_ble_direct, ble_gls_1808} 且 quality_flag=clean 的读数

    返回：number:百分比。读取：GlucoseReading、PatientProfile。
    """
    return _fde.FUNCTIONS['TIR'](ctx)

@spi.function(ONTOLOGY, "TAR_L1", reads=("GlucoseReading",))
def TAR_L1(ctx):
    """>10.0 mmol/L 时间占比，分子口径同 TIR

    返回：number:百分比。读取：GlucoseReading。
    """
    return _fde.FUNCTIONS['TAR_L1'](ctx)

@spi.function(ONTOLOGY, "TAR_L2", reads=("GlucoseReading",))
def TAR_L2(ctx):
    """>13.9 mmol/L 时间占比，分子口径同 TIR

    返回：number:百分比。读取：GlucoseReading。
    """
    return _fde.FUNCTIONS['TAR_L2'](ctx)

@spi.function(ONTOLOGY, "TBR_L1", reads=("GlucoseReading", "PatientProfile"))
def TBR_L1(ctx):
    """3.0–3.8 mmol/L 时间占比（妊娠切 <3.5），分子口径同 TIR

    返回：number:百分比。读取：GlucoseReading、PatientProfile。
    """
    return _fde.FUNCTIONS['TBR_L1'](ctx)

@spi.function(ONTOLOGY, "TBR_L2", reads=("GlucoseReading",))
def TBR_L2(ctx):
    """<3.0 mmol/L 时间占比

    返回：number:百分比。读取：GlucoseReading。
    """
    return _fde.FUNCTIONS['TBR_L2'](ctx)

@spi.function(ONTOLOGY, "MeanGlucose", reads=("GlucoseReading",))
def MeanGlucose(ctx):
    """窗口内 clean 读数算术均值

    返回：number:mmol/L。读取：GlucoseReading。
    """
    return _fde.FUNCTIONS['MeanGlucose'](ctx)

@spi.function(ONTOLOGY, "GMI", reads=("GlucoseReading", "DeviceModel", "ChannelRegistry", "SensorSession"))
def GMI(ctx):
    """GMI(%) = 3.31 + 0.02392 × mean(mg/dL)（Bergenstal 2018 官方公式，对外只用这一条，不用 uGMI）。四条前提全满足才计算：① 窗口读数 100% 来自单一厂商连续监测通道 ② 全窗口同 vendor 同 sensor_model ③ active% ≥70 且 days ≥14 ④ device_model.mard_pct 已在 channel_registry 登记。任一不满足返回 null，**不得用近似值填空**

    返回：number:百分比。读取：GlucoseReading、DeviceModel、ChannelRegistry、SensorSession。
    """
    return _fde.FUNCTIONS['GMI'](ctx)

@spi.function(ONTOLOGY, "CV", reads=("GlucoseReading",))
def CV(ctx):
    """SD ÷ MeanGlucose × 100

    返回：number:百分比。读取：GlucoseReading。
    """
    return _fde.FUNCTIONS['CV'](ctx)

@spi.function(ONTOLOGY, "SD", reads=("GlucoseReading",))
def SD(ctx):
    """窗口内 clean 读数标准差

    返回：number:mmol/L。读取：GlucoseReading。
    """
    return _fde.FUNCTIONS['SD'](ctx)

@spi.function(ONTOLOGY, "MAGE", reads=("GlucoseReading",))
def MAGE(ctx):
    """平均血糖漂移幅度，取振幅 >1×SD 的有效波动均值

    返回：number:mmol/L。读取：GlucoseReading。
    """
    # TODO(FDE): 实现派生量计算（只读，无副作用）。可用：ctx.get / ctx.find / ctx.search_around
    raise NotImplementedError("MAGE 待实现")

@spi.function(ONTOLOGY, "AGP分位曲线", reads=("GlucoseReading", "SensorSession"))
def AGP分位曲线(ctx):
    """14 天复合曲线：中位数 + 25–75% + 5–95% 分位带 + 逐日曲线，须披露 session 构成

    返回：object。读取：GlucoseReading、SensorSession。
    """
    # TODO(FDE): 实现派生量计算（只读，无副作用）。可用：ctx.get / ctx.find / ctx.search_around
    raise NotImplementedError("AGP分位曲线 待实现")

@spi.function(ONTOLOGY, "active_pct", reads=("GlucoseReading", "ChannelRegistry"))
def active_pct(ctx):
    """**口径固定（confirmed-facts R-3）**：去重后 distinct 读数数 ÷ (窗口天数 × 1440 ÷ expected_sampling_interval)。采样间隔 5 分钟时分母即天数 × 288；公式引用 channel_registry 字段而不是硬编码 288。同一时刻多路只算一次

    返回：number:百分比。读取：GlucoseReading、ChannelRegistry。
    """
    return _fde.FUNCTIONS['active_pct'](ctx)

@spi.function(ONTOLOGY, "wear_ratio", reads=("GlucoseReading", "SensorSession"))
def wear_ratio(ctx):
    """会话覆盖时长 ÷ 窗口总时长。**与 active_pct 不同义，两者不得互相引用**（metric_registry 治理项）

    返回：number:百分比。读取：GlucoseReading、SensorSession。
    """
    # TODO(FDE): 实现派生量计算（只读，无副作用）。可用：ctx.get / ctx.find / ctx.search_around
    raise NotImplementedError("wear_ratio 待实现")

@spi.function(ONTOLOGY, "sufficiency_ok", reads=("GlucoseReading", "ChannelRegistry"))
def sufficiency_ok(ctx):
    """days ≥14 AND active_pct ≥70。只供结论层判定使用

    返回：boolean。读取：GlucoseReading、ChannelRegistry。
    """
    return _fde.FUNCTIONS['sufficiency_ok'](ctx)

@spi.function(ONTOLOGY, "nocturnal_coverage_pct", reads=("GlucoseReading",))
def nocturnal_coverage_pct(ctx):
    """00:00–06:00 窗口内按 active_pct 同口径计算。<70 置 nocturnal_coverage_insufficient，报告首屏显示。TODO(FDE)：夜间窗口边界（00:00–06:00 vs 23:00–07:00）上线前需临床拍板

    返回：number:百分比。读取：GlucoseReading。
    """
    return _fde.FUNCTIONS['nocturnal_coverage_pct'](ctx)

@spi.function(ONTOLOGY, "tz_uncertain", reads=("GlucoseReading",))
def tz_uncertain(ctx):
    """窗口内 tz_provenance 非 device/vendor 来源占比超阈值时置位；命中则按本地时间切分的统计不出正式结论

    返回：boolean。读取：GlucoseReading。
    """
    # TODO(FDE): 实现派生量计算（只读，无副作用）。可用：ctx.get / ctx.find / ctx.search_around
    raise NotImplementedError("tz_uncertain 待实现")

@spi.function(ONTOLOGY, "brand_changed", reads=("SensorSession",))
def brand_changed(ctx):
    """窗口横跨传感器品牌/型号代际变更；命中禁止输出跨期比较结论

    返回：boolean。读取：SensorSession。
    """
    # TODO(FDE): 实现派生量计算（只读，无副作用）。可用：ctx.get / ctx.find / ctx.search_around
    raise NotImplementedError("brand_changed 待实现")

@spi.function(ONTOLOGY, "hypo_episode_stats", reads=("GlucoseReading",))
def hypo_episode_stats(ctx):
    """持续 ≥15 分钟的低血糖事件计数、时长、分级（Danne 2017 口径）。**仅用于回顾统计，永不用于实时触发**——与 R03a/R04a 的连续 2 读数口径物理分开

    返回：object。读取：GlucoseReading。
    """
    return _fde.FUNCTIONS['hypo_episode_stats'](ctx)

@spi.function(ONTOLOGY, "meal_response_calc", reads=("GlucoseReading", "ContextEvent"))
def meal_response_calc(ctx):
    """配对窗 [t−60, t+180]，基线取 [t−60, t−15] 均值；输出 delta_p / time_to_peak / iAUC_2h / r2h / return_to_baseline。基线缺口 <20% 才出结论

    返回：object。读取：GlucoseReading、ContextEvent。
    """
    # TODO(FDE): 实现派生量计算（只读，无副作用）。可用：ctx.get / ctx.find / ctx.search_around
    raise NotImplementedError("meal_response_calc 待实现")

@spi.function(ONTOLOGY, "glucose_slope", reads=("GlucoseReading",))
def glucose_slope(ctx):
    """近 15 分钟线性拟合斜率，供 R05/R06/R25/R26 使用

    返回：number:mmol/L每分钟。读取：GlucoseReading。
    """
    # TODO(FDE): 实现派生量计算（只读，无副作用）。可用：ctx.get / ctx.find / ctx.search_around
    raise NotImplementedError("glucose_slope 待实现")

@spi.function(ONTOLOGY, "sync_gap_risk", reads=("CarrierRegistry", "SyncPlan"))
def sync_gap_risk(ctx):
    """距上次同步超过 sync_plan 预期间隔 ×1.5 时评估距传感器缓存深度还剩多远。TODO(FDE)：缓存深度参数待向硅基问定（confirmed-facts D-12），问定前按 24h 保守假设

    返回：enum:低|中|高。读取：CarrierRegistry、SyncPlan。
    """
    # TODO(FDE): 实现派生量计算（只读，无副作用）。可用：ctx.get / ctx.find / ctx.search_around
    raise NotImplementedError("sync_gap_risk 待实现")

@spi.function(ONTOLOGY, "gmi_hba1c_consistency", reads=("GlucoseReading", "LabResult"))
def gmi_hba1c_consistency(ctx):
    """|GMI − HbA1c| 及一致性布尔值；≥0.5% 提示以实测 HbA1c 为准

    返回：object。读取：GlucoseReading、LabResult。
    """
    # TODO(FDE): 实现派生量计算（只读，无副作用）。可用：ctx.get / ctx.find / ctx.search_around
    raise NotImplementedError("gmi_hba1c_consistency 待实现")

@spi.function(ONTOLOGY, "dedup_hit_rate", reads=("GlucoseReading",))
def dedup_hit_rate(ctx):
    """去重命中率与疑似重复率，供数据质量看板与去重失效自检

    返回：number:百分比。读取：GlucoseReading。
    """
    # TODO(FDE): 实现派生量计算（只读，无副作用）。可用：ctx.get / ctx.find / ctx.search_around
    raise NotImplementedError("dedup_hit_rate 待实现")

@spi.function(ONTOLOGY, "hypo_risk_med", reads=("PatientProfile",))
def hypo_risk_med(ctx):
    """meds ∩ {胰岛素, 磺脲, 格列奈} ≠ ∅

    返回：boolean。读取：PatientProfile。
    """
    return _fde.FUNCTIONS['hypo_risk_med'](ctx)

@spi.function(ONTOLOGY, "target_profile_of", reads=("PatientProfile",))
def target_profile_of(ctx):
    """按 age≥65 / pregnant 解析人群维度，供全部阈值规则读取。**这是入参解析函数，不是分支硬编码**

    返回：enum:adult|elderly|pregnancy。读取：PatientProfile。
    """
    return _fde.FUNCTIONS['target_profile_of'](ctx)

@spi.function(ONTOLOGY, "service_tier_map", reads=("CgmSummary", "PatientProfile"))
def service_tier_map(ctx):
    """德心 L0–L4 服务分层映射（内部标签）。前提：sufficiency_ok=true、非老年、非妊娠、非 confounded_window

    返回：string。读取：CgmSummary、PatientProfile。
    """
    # TODO(FDE): 实现派生量计算（只读，无副作用）。可用：ctx.get / ctx.find / ctx.search_around
    raise NotImplementedError("service_tier_map 待实现")

@spi.function(ONTOLOGY, "churn_signal_coverage", reads=("ChurnSignal", "PatientProfile"))
def churn_signal_coverage(ctx):
    """至少 1 个流失信号可计算的患者比例，按 health_tier/年龄分层；老年组 <50% 即预警"信号体系对该人群失效"

    返回：number:百分比。读取：ChurnSignal、PatientProfile。
    """
    # TODO(FDE): 实现派生量计算（只读，无副作用）。可用：ctx.get / ctx.find / ctx.search_around
    raise NotImplementedError("churn_signal_coverage 待实现")

@spi.function(ONTOLOGY, "away_days", reads=("ContextEvent", "CarrierRegistry"))
def away_days(ctx):
    """away_mode 期间天数。**照常计入 R01 分母**，不得移出

    返回：number:天。读取：ContextEvent、CarrierRegistry。
    """
    # TODO(FDE): 实现派生量计算（只读，无副作用）。可用：ctx.get / ctx.find / ctx.search_around
    raise NotImplementedError("away_days 待实现")


# ============================================================================
# §4 Rules —— 92 条（declarative 全自动 / function-backed 骨架）。
# source + citations 原样保留，供 OKF 导出与 ontology-validate 治理审计。
# ============================================================================

@spi.rule(ONTOLOGY, "低血糖优先抢占", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.POST_WRITE,
          source="中国血糖监测临床应用指南 2021 读图顺序；ATTD 2019 AGP 规范",
          citations=("confirmed-facts A3-2",))
def 低血糖优先抢占(ctx) -> RuleResult:
    """意图：低血糖组命中时抑制同周期内一切加强降糖方向的输出，固定 AGP 读图顺序：低 → 高 → 波动

    优先级 99（B0 元规则 带）· 生效阶段 P1+P2。
    挂载动作：生成方案草稿、生成AGP与指标报告、输出服务分层标签、生成结营报告。
    """
    return _fde.RULES['低血糖优先抢占'](ctx)

@spi.rule(ONTOLOGY, "R03a_Level2低血糖_实时告警", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.POST_WRITE,
          source="国际低血糖研究组 IHSG；ADA Standards 2026 第 6 章 6.15",
          citations=("daily-monitoring D8", "confirmed-facts A3-6、C-01"))
def R03a_Level2低血糖_实时告警(ctx) -> RuleResult:
    """意图：连续 2 个读数确认 G<3.0 即触发，患者/健管师/群立即收到 15-15 处置指引，老年或独居加电话

    优先级 100（B1 低血糖 带）· 生效阶段 P2。
    挂载动作：触发低血糖处置、推送告警。

    ★ 低血糖双口径硬边界：本规则**不得**与 R03b_Level2低血糖_回顾事件统计 共用判定函数、不得靠传参区分口径。
      实时口径（连续 2 个读数 + 预测性告警）与回顾口径（持续 ≥15 分钟 Danne）语义不同，
      混用等于原样重犯已被临床评审纠正过的 C-01 错误（confirmed-facts C-01、A3-6、R-4）。
    """
    return _fde.RULES['R03a_Level2低血糖_实时告警'](ctx)

@spi.rule(ONTOLOGY, "R04a_Level1低血糖_实时告警", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.POST_WRITE,
          source="同 R03a；15-15 法则",
          citations=("daily-monitoring D9", "confirmed-facts A3-6"))
def R04a_Level1低血糖_实时告警(ctx) -> RuleResult:
    """意图：连续 2 个读数确认 3.0≤G<3.9 即触发

    优先级 105（B1 低血糖 带）· 生效阶段 P2。
    挂载动作：触发低血糖处置、推送告警。

    ★ 低血糖双口径硬边界：本规则**不得**与 R04b_Level1低血糖_回顾事件统计 共用判定函数、不得靠传参区分口径。
      实时口径（连续 2 个读数 + 预测性告警）与回顾口径（持续 ≥15 分钟 Danne）语义不同，
      混用等于原样重犯已被临床评审纠正过的 C-01 错误（confirmed-facts C-01、A3-6、R-4）。
    """
    return _fde.RULES['R04a_Level1低血糖_实时告警'](ctx)

@spi.rule(ONTOLOGY, "R03b_Level2低血糖_回顾事件统计", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.POST_WRITE,
          source="Danne 2017 CGM 事件定义",
          citations=("confirmed-facts A3-6、R-4", "research/sources/02 §5.2"))
def R03b_Level2低血糖_回顾事件统计(ctx) -> RuleResult:
    """意图：持续 ≥15 分钟的 G<3.0 计一次事件，用于 TBR 统计与次日医师减药审查；一期是核心安全产出，二期是实时告警 ROI 基线

    优先级 110（B1 低血糖 带）· 生效阶段 P1+P2。
    挂载动作：统计低血糖事件、生成AGP与指标报告、生成结营报告。

    ★ 低血糖双口径硬边界：本规则**不得**与 R03a_Level2低血糖_实时告警 共用判定函数、不得靠传参区分口径。
      实时口径（连续 2 个读数 + 预测性告警）与回顾口径（持续 ≥15 分钟 Danne）语义不同，
      混用等于原样重犯已被临床评审纠正过的 C-01 错误（confirmed-facts C-01、A3-6、R-4）。
    """
    # TODO(FDE): 查连续读数窗口，校验是否存在持续 ≥15min 的 G<3.0 区间（起止均按时长判定）。**禁止复用 R03a 的 2 读数口径**
    # 可用：ctx.get / ctx.find / ctx.search_around（写后可见本次暂存写入）
    raise NotImplementedError("R03b_Level2低血糖_回顾事件统计 待实现")

@spi.rule(ONTOLOGY, "R04b_Level1低血糖_回顾事件统计", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.POST_WRITE,
          source="Danne 2017 CGM 事件定义",
          citations=("confirmed-facts A3-6、R-4",))
def R04b_Level1低血糖_回顾事件统计(ctx) -> RuleResult:
    """意图：持续 ≥15 分钟的 3.0≤G<3.9 计一次事件

    优先级 115（B1 低血糖 带）· 生效阶段 P1+P2。
    挂载动作：统计低血糖事件、生成AGP与指标报告、生成结营报告。

    ★ 低血糖双口径硬边界：本规则**不得**与 R04a_Level1低血糖_实时告警 共用判定函数、不得靠传参区分口径。
      实时口径（连续 2 个读数 + 预测性告警）与回顾口径（持续 ≥15 分钟 Danne）语义不同，
      混用等于原样重犯已被临床评审纠正过的 C-01 错误（confirmed-facts C-01、A3-6、R-4）。
    """
    # TODO(FDE): 查连续读数窗口，校验是否存在持续 ≥15min 的 3.0≤G<3.9 区间
    # 可用：ctx.get / ctx.find / ctx.search_around（写后可见本次暂存写入）
    raise NotImplementedError("R04b_Level1低血糖_回顾事件统计 待实现")

@spi.rule(ONTOLOGY, "R02_传感器压迫伪差识别", backing=Backing.FUNCTION, severity=Severity.SOFT,
          evaluation=Evaluation.POST_WRITE,
          source="Danne 2017 CGM 事件定义",
          citations=("research/sources/02 §8 R02", "domain-canvas §3.6"))
def R02_传感器压迫伪差识别(ctx) -> RuleResult:
    """意图：单点 <3.0 但前后 10min 内回升 ≥1.5，或 15min 内跳变 >5.0，判伪差不计入事件。**伪差判定不得抑制 hard 级告警发出**

    优先级 120（B1 低血糖 带）· 生效阶段 P1+P2。
    挂载动作：去重与通道仲裁、统计低血糖事件。
    """
    return _fde.RULES['R02_传感器压迫伪差识别'](ctx)

@spi.rule(ONTOLOGY, "R05_即将低血糖预测告警", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.POST_WRITE,
          source="Aleppo 2017 趋势箭头共识",
          citations=("research/sources/02 §5.4、§8 R05", "confirmed-facts C-01"))
def R05_即将低血糖预测告警(ctx) -> RuleResult:
    """意图：预测性告警，提前 10–30 分钟提示补 10–15g 碳水并暂停运动。负时延正是二期的价值来源

    优先级 125（B1 低血糖 带）· 生效阶段 P2。
    挂载动作：触发低血糖处置、推送告警。
    """
    return _fde.RULES['R05_即将低血糖预测告警'](ctx)

@spi.rule(ONTOLOGY, "R06_快速下降箭头提示", backing=Backing.DECLARATIVE, severity=Severity.SOFT,
          evaluation=Evaluation.POST_WRITE,
          source="Aleppo 2017 趋势箭头共识",
          citations=("research/sources/02 §5.4",))
def R06_快速下降箭头提示(ctx) -> RuleResult:
    """意图：双下箭且血糖已偏低时提示 15 分钟后复看，不建议大量补碳水以免反跳

    优先级 130（B1 低血糖 带）· 生效阶段 P2。
    挂载动作：推送告警。
    """
    return _fde.RULES['R06_快速下降箭头提示'](ctx)

@spi.rule(ONTOLOGY, "R07_夜间低血糖事件", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.POST_WRITE,
          source="Endocrine Society 2022 低血糖指南；中国老年糖尿病诊疗指南 2024",
          citations=("daily-monitoring D11", "research/sources/02 §8 R07"))
def R07_夜间低血糖事件(ctx) -> RuleResult:
    """意图：00:00–06:00 窗口内持续性低血糖；3 天内 ≥2 次升级医师复核晚间用药与晚餐

    优先级 135（B1 低血糖 带）· 生效阶段 P1+P2。
    挂载动作：统计低血糖事件、生成去强化证据工单。
    """
    return _fde.RULES['R07_夜间低血糖事件'](ctx)

@spi.rule(ONTOLOGY, "R08_睡前低值预警", backing=Backing.FUNCTION, severity=Severity.SOFT,
          evaluation=Evaluation.POST_WRITE,
          source="中国老年糖尿病诊疗指南 2024；门店经验（已修正加餐种类）",
          citations=("research/sources/02 §5.5、§8 R08", "daily-monitoring D12"))
def R08_睡前低值预警(ctx) -> RuleResult:
    """意图：睡前窗口均值低于分层下限且用药含胰岛素或磺脲时，建议 10–15g 含碳水加餐并复测。**加餐种类不得是黄瓜**（门店旧口径已纠正）

    优先级 140（B1 低血糖 带）· 生效阶段 P1+P2。
    挂载动作：推送告警、生成方案草稿。
    """
    return _fde.RULES['R08_睡前低值预警'](ctx)

@spi.rule(ONTOLOGY, "R09_TBR超标触发去强化审查", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.POST_WRITE,
          source="ATTD 2019；中国老年糖尿病诊疗指南 2024",
          citations=("research/sources/02 §5.6、§8 R09", "review-and-plan D3"))
def R09_TBR超标触发去强化审查(ctx) -> RuleResult:
    """意图：报告首行标红「低血糖优先」，并必出低血糖事件明细表置于第一页，提交医师降糖药去强化审查

    优先级 145（B1 低血糖 带）· 生效阶段 P1+P2。
    挂载动作：生成AGP与指标报告、生成去强化证据工单、生成结营报告。
    """
    return _fde.RULES['R09_TBR超标触发去强化审查'](ctx)

@spi.rule(ONTOLOGY, "R10_低血糖无感知线索", backing=Backing.FUNCTION, severity=Severity.SOFT,
          evaluation=Evaluation.POST_WRITE,
          source="Endocrine Society 2022 低血糖指南",
          citations=("research/sources/02 §8 R10", "behavior-matrix §7.1 G7"))
def R10_低血糖无感知线索(ctx) -> RuleResult:
    """意图：Level 2 事件发生但无患者症状标记 ≥2 次/14 天，提示医师评估无感知低血糖

    优先级 148（B1 低血糖 带）· 生效阶段 P1+P2。
    挂载动作：生成去强化证据工单、配置患者告警与静音策略。
    """
    return _fde.RULES['R10_低血糖无感知线索'](ctx)

@spi.rule(ONTOLOGY, "R46_IAH高危阈值上调且禁止静音", backing=Backing.DECLARATIVE, severity=Severity.HARD,
          evaluation=Evaluation.PRE,
          source="Endocrine Society 2022 低血糖指南",
          citations=("confirmed-facts A3-7、C-05",))
def R46_IAH高危阈值上调且禁止静音(ctx) -> RuleResult:
    """意图：无感知低血糖高危人群阈值上调至 4.4 且保留告警，不可一律夜间静音。人群维度是入参不是分支硬编码

    优先级 149（B1 低血糖 带）· 生效阶段 P1+P2。
    挂载动作：配置患者告警与静音策略。
    """
    return _fde.RULES['R46_IAH高危阈值上调且禁止静音'](ctx)

@spi.rule(ONTOLOGY, "R34_HAAF_24小时复发窗", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.POST_WRITE,
          source="Endocrine Society 2022（HAAF 机制）",
          citations=("daily-monitoring D12b",))
def R34_HAAF_24小时复发窗(ctx) -> RuleResult:
    """意图：24 小时内已发生 Level 2 事件即进入 HAAF 高危窗口：阈值上调 4.4、夜间强制人工巡检、当日禁运动建议、医师复核任务

    优先级 150（B1 低血糖 带）· 生效阶段 P1+P2。
    挂载动作：更新低血糖状态机、收紧告警阈值。
    """
    return _fde.RULES['R34_HAAF_24小时复发窗'](ctx)

@spi.rule(ONTOLOGY, "R44_高危用药禁止闭环", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.PRE,
          source="TODO(FDE): 补依据（机制方向由 Endocrine Society 2022 与中国糖尿病防治指南 2024 用药章节支持，但\"可持续 24–72 小时\"这个具体时长在两份基准文档里均无逐字出处）",
          citations=("daily-monitoring D21", "behavior-matrix §6 hypo_state"))
def R44_高危用药禁止闭环(ctx) -> RuleResult:
    """意图：磺脲或长效/预混胰岛素使用者的低血糖不得按一次复测回升就闭环

    优先级 155（B1 低血糖 带）· 生效阶段 P1+P2。
    挂载动作：响应并回执告警。

    # TODO(FDE): 补依据 —— 当前 source 为 TODO(FDE): 补依据（机制方向由 Endocrine Society 2022 与中国糖尿病防治指南 2024 用药章节支持，但"可持续 24–72 小时"这个具体时长在两份基准文档里均无逐字出处）
    """
    return _fde.RULES['R44_高危用药禁止闭环'](ctx)

@spi.rule(ONTOLOGY, "R57_15-15三轮无效强制升级就医", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.POST_WRITE,
          source="国际低血糖研究组 IHSG；15-15 法则；ADA Standards 2026 第 6 章",
          citations=("research/sources/02 §5.1", "daily-monitoring D21", "临床复核补充"))
# 注：IR 原名 R57_15-15三轮无效强制升级就医 含连字符，不是合法 Python 标识符；def 名已规范化，注册名仍是 IR 原名。
def R57_15_15三轮无效强制升级就医(ctx) -> RuleResult:
    """意图：15-15 法则重复 3 轮仍未回升，或症状持续 30–45 分钟，立即升级至就医/120 并通知紧急联系人。**这是处置链条最危险的一环，此前 87 条里没有一条兜住**

    优先级 152（B1 低血糖 带）· 生效阶段 P1+P2。
    挂载动作：响应并回执告警、推送告警。
    """
    return _fde.RULES['R57_15-15三轮无效强制升级就医'](ctx)

@spi.rule(ONTOLOGY, "R58_Level3严重低血糖强制转诊", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.POST_WRITE,
          source="国际低血糖研究组 IHSG Level 3 定义；ADA Standards 2026 第 6 章",
          citations=("research/sources/02 §5.1", "临床复核补充"))
def R58_Level3严重低血糖强制转诊(ctx) -> RuleResult:
    """意图：Level 3（需他人协助的严重低血糖）**定义上不依赖血糖数值**，命中即强制触发就医与医师复核工单，不看当前 G 值

    优先级 153（B1 低血糖 带）· 生效阶段 P1+P2。
    挂载动作：记录症状与处置、推送告警、转介医师。
    """
    return _fde.RULES['R58_Level3严重低血糖强制转诊'](ctx)

@spi.rule(ONTOLOGY, "R59_老年非典型症状疑似低血糖", backing=Backing.FUNCTION, severity=Severity.SOFT,
          evaluation=Evaluation.POST_WRITE,
          source="中国老年糖尿病诊疗指南 2024；Endocrine Society 2022",
          citations=("daily-monitoring D28", "research/sources/02 §5.5", "临床复核补充"))
def R59_老年非典型症状疑似低血糖(ctx) -> RuleResult:
    """意图：老年低血糖常表现为跌倒、意识模糊、叫不醒、胡言乱语，而不是出汗心悸。这类记录若同期 CGM 处于临界低值区间，提示疑似低血糖诱因并推医师复核

    优先级 154（B1 低血糖 带）· 生效阶段 P1+P2。
    挂载动作：记录症状与处置、生成去强化证据工单。
    """
    return _fde.RULES['R59_老年非典型症状疑似低血糖'](ctx)

@spi.rule(ONTOLOGY, "R11_严重高血糖", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.POST_WRITE,
          source="中国糖尿病防治指南 2024（不宜运动阈值）；Colberg 2016 ADA 运动立场",
          citations=("research/sources/02 §8 R11", "daily-monitoring D13"))
def R11_严重高血糖(ctx) -> RuleResult:
    """意图：G>16.7 持续 ≥1h，或 G>13.9 伴口渴多尿恶心，提示查血酮，阳性或有症状转就医，暂停运动与产品推荐

    优先级 200（B2 高血糖 带）· 生效阶段 P1+P2。
    挂载动作：触发低血糖处置、推送告警、生成方案草稿。
    """
    return _fde.RULES['R11_严重高血糖'](ctx)

@spi.rule(ONTOLOGY, "R12_SGLT2i酮症警觉", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.POST_WRITE,
          source="TODO(FDE): 补依据（药物机制层面成立，但需补 SGLT2i euDKA 的权威指南条目）",
          citations=("research/sources/02 §6.4、§8 R12", "behavior-matrix §7.1 G1b"))
def R12_SGLT2i酮症警觉(ctx) -> RuleResult:
    """意图：SGLT2i 使用者在极低碳水、长时间运动或恶心乏力情形下，血糖不高也可能酮症（euDKA）

    优先级 205（B2 高血糖 带）· 生效阶段 P1+P2。
    挂载动作：推送告警、记录酮体。

    # TODO(FDE): 补依据 —— 当前 source 为 TODO(FDE): 补依据（药物机制层面成立，但需补 SGLT2i euDKA 的权威指南条目）
    """
    return _fde.RULES['R12_SGLT2i酮症警觉'](ctx)

@spi.rule(ONTOLOGY, "R13_TAR_L2超标", backing=Backing.FUNCTION, severity=Severity.SOFT,
          evaluation=Evaluation.POST_WRITE,
          source="ATTD 2019",
          citations=("research/sources/02 §8 R13",))
def R13_TAR_L2超标(ctx) -> RuleResult:
    """意图：TAR>13.9 占比超标，生成"哪些时段/餐次贡献最多"的归因分析交医师

    优先级 210（B2 高血糖 带）· 生效阶段 P1+P2。
    挂载动作：生成AGP与指标报告、生成方案草稿。
    """
    return _fde.RULES['R13_TAR_L2超标'](ctx)

@spi.rule(ONTOLOGY, "R14_TAR_L1超标", backing=Backing.DECLARATIVE, severity=Severity.SOFT,
          evaluation=Evaluation.POST_WRITE,
          source="ATTD 2019",
          citations=("research/sources/02 §8 R14",))
def R14_TAR_L1超标(ctx) -> RuleResult:
    """意图：TAR>10.0 占比 ≥25%，给饮食/运动/服药时机建议

    优先级 215（B2 高血糖 带）· 生效阶段 P1+P2。
    挂载动作：生成方案草稿。
    """
    return _fde.RULES['R14_TAR_L1超标'](ctx)

@spi.rule(ONTOLOGY, "R15_TIR未达标", backing=Backing.DECLARATIVE, severity=Severity.SOFT,
          evaluation=Evaluation.POST_WRITE,
          source="ATTD 2019；中国糖尿病防治指南 2024",
          citations=("research/sources/02 §8 R15",))
def R15_TIR未达标(ctx) -> RuleResult:
    """意图：TIR 未达标，把差距换算成小时（每 5% ≈ 1.2h/天）并建议复诊

    优先级 220（B2 高血糖 带）· 生效阶段 P1+P2。
    挂载动作：生成AGP与指标报告、生成方案草稿。
    """
    return _fde.RULES['R15_TIR未达标'](ctx)

@spi.rule(ONTOLOGY, "R22_黎明现象", backing=Backing.FUNCTION, severity=Severity.SOFT,
          evaluation=Evaluation.POST_WRITE,
          source="TODO(FDE): 补依据（研究文档标注为\"临床常规定义\"，需补权威出处）",
          citations=("research/sources/02 §8 R22",))
def R22_黎明现象(ctx) -> RuleResult:
    """意图：03:00 最低值到 07:00 上升明显且无夜间加餐，提示医师调整基础胰岛素或晚餐

    优先级 225（B2 高血糖 带）· 生效阶段 P1+P2。
    挂载动作：生成方案草稿、转介医师。

    # TODO(FDE): 补依据 —— 当前 source 为 TODO(FDE): 补依据（研究文档标注为"临床常规定义"，需补权威出处）
    """
    return _fde.RULES['R22_黎明现象'](ctx)

@spi.rule(ONTOLOGY, "R16a_波动超标_硬", backing=Backing.DECLARATIVE, severity=Severity.HARD,
          evaluation=Evaluation.POST_WRITE,
          source="ATTD 2019",
          citations=("research/sources/02 §8 R16",))
def R16a_波动超标_硬(ctx) -> RuleResult:
    """意图：CV>36% 判波动过大，需联动低血糖与餐后归因

    优先级 300（B3 波动与餐后 带）· 生效阶段 P1+P2。
    挂载动作：生成AGP与指标报告、生成方案草稿。
    """
    return _fde.RULES['R16a_波动超标_硬'](ctx)

@spi.rule(ONTOLOGY, "R16b_波动偏高_软_中国口径", backing=Backing.DECLARATIVE, severity=Severity.SOFT,
          evaluation=Evaluation.POST_WRITE,
          source="中国血糖监测临床应用指南 2021（CV>33% 与低血糖风险升高相关）",
          citations=("research/sources/02 §2.1、§8 R16",))
def R16b_波动偏高_软_中国口径(ctx) -> RuleResult:
    """意图：33% < CV ≤ 36% 提示波动偏高，中国人群本土证据阈值

    优先级 305（B3 波动与餐后 带）· 生效阶段 P1+P2。
    挂载动作：生成AGP与指标报告、生成方案草稿。
    """
    return _fde.RULES['R16b_波动偏高_软_中国口径'](ctx)

@spi.rule(ONTOLOGY, "R17_GMI与HbA1c不一致", backing=Backing.FUNCTION, severity=Severity.SOFT,
          evaluation=Evaluation.POST_WRITE,
          source="Bergenstal 2018；Diabetes Care 2024 GMI 差异评论",
          citations=("research/sources/02 §1.1、§8 R17", "review-and-plan D7"))
def R17_GMI与HbA1c不一致(ctx) -> RuleResult:
    """意图：偏差 ≥0.5% 时提示以实测 HbA1c 为准，标注可能贫血或血红蛋白变异

    优先级 310（B3 波动与餐后 带）· 生效阶段 P1+P2。
    挂载动作：生成AGP与指标报告、判定缓解结果。
    """
    return _fde.RULES['R17_GMI与HbA1c不一致'](ctx)

@spi.rule(ONTOLOGY, "R19_餐后高响应", backing=Backing.FUNCTION, severity=Severity.SOFT,
          evaluation=Evaluation.POST_WRITE,
          source="Howard 2022 CGM 效度与重复性研究",
          citations=("research/sources/02 §4.2、§8 R19",))
def R19_餐后高响应(ctx) -> RuleResult:
    """意图：单餐响应超标，同类餐重复 ≥2 次才触发饮食顺序/份量/搭配/餐后步行建议

    优先级 315（B3 波动与餐后 带）· 生效阶段 P1+P2。
    挂载动作：计算餐后响应、生成方案草稿。
    """
    return _fde.RULES['R19_餐后高响应'](ctx)

@spi.rule(ONTOLOGY, "R20_餐后极高响应", backing=Backing.FUNCTION, severity=Severity.SOFT,
          evaluation=Evaluation.POST_WRITE,
          source="ATTD 2019 分级",
          citations=("research/sources/02 §8 R20",))
def R20_餐后极高响应(ctx) -> RuleResult:
    """意图：餐后响应达到 TAR L2 级别，联动 R13 并推送健管师

    优先级 320（B3 波动与餐后 带）· 生效阶段 P1+P2。
    挂载动作：计算餐后响应、推送告警。
    """
    return _fde.RULES['R20_餐后极高响应'](ctx)

@spi.rule(ONTOLOGY, "R21_餐次数据混叠排除", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.PRE,
          source="Howard 2022 CGM 效度与重复性研究",
          citations=("research/sources/02 §8 R21", "review-and-plan D6"))
def R21_餐次数据混叠排除(ctx) -> RuleResult:
    """意图：与上一餐或加餐间隔 <2h，曲线重叠不可信，该餐不计入个人食物排序

    优先级 325（B3 波动与餐后 带）· 生效阶段 P1+P2。
    挂载动作：计算餐后响应。
    """
    # TODO(FDE): 查该餐与前一餐/加餐记录，校验时间间隔是否 <2h
    # 可用：ctx.get / ctx.find / ctx.search_around（写后可见本次暂存写入）
    raise NotImplementedError("R21_餐次数据混叠排除 待实现")

@spi.rule(ONTOLOGY, "R47_跨品牌配对排除", backing=Backing.DECLARATIVE, severity=Severity.HARD,
          evaluation=Evaluation.PRE,
          source="Howard 2022；ATTD 2019 报告标准化",
          citations=("review-and-plan D6", "behavior-matrix §6 metric_registry"))
def R47_跨品牌配对排除(ctx) -> RuleResult:
    """意图：跨品牌/跨型号代际的读数不得用于个体化餐后结论与跨期比较（跨品牌误分类率约 19%）

    优先级 328（B3 波动与餐后 带）· 生效阶段 P1+P2。
    挂载动作：计算餐后响应、生成AGP与指标报告。
    """
    brand_changed = ctx.params.get("brand_changed")
    cross_brand = ctx.params.get("cross_brand")
    if not (cross_brand is not True and brand_changed is not True):  # ← 取自 IR check，取反即违反条件
        return RuleResult.fail("R47_跨品牌配对排除 未通过", suggestion="须满足：cross_brand is not True and brand_changed is not True")
    return RuleResult.ok()

@spi.rule(ONTOLOGY, "R36_active率超100自检", backing=Backing.DECLARATIVE, severity=Severity.HARD,
          evaluation=Evaluation.POST_WRITE,
          source="通用（工程自检口径）",
          citations=("confirmed-facts R-3",))
def R36_active率超100自检(ctx) -> RuleResult:
    """意图：active% > 100% 是去重失效唯一且极灵敏的自检信号，一期即上线红色告警

    优先级 335（B3 波动与餐后 带）· 生效阶段 P1+P2。
    挂载动作：去重与通道仲裁、计算窗口指标。
    """
    return _fde.RULES['R36_active率超100自检'](ctx)  # 缺 active_pct 参数时按患者 14 天窗口自算（P8）

@spi.rule(ONTOLOGY, "R48_去重键必须用传感器序号", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.PRE,
          source="通用（confirmed-facts R-1 工程决策，依据 A1-6 硅基确认读数默认带传感器侧序号）",
          citations=("confirmed-facts A1-6、R-1",))
def R48_去重键必须用传感器序号(ctx) -> RuleResult:
    """意图：去重键一期就用传感器侧序号，不用厂商记录 ID，也不单独用可空的 device_time。这是四条一期强制预留里唯一不可逆的一条

    优先级 340（B3 波动与餐后 带）· 生效阶段 P1+P2。
    挂载动作：去重与通道仲裁、摄入读数。
    """
    return _fde.RULES['R48_去重键必须用传感器序号'](ctx)

@spi.rule(ONTOLOGY, "R23_运动前低值", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.POST_WRITE,
          source="Colberg 2016 ADA 运动立场；ADA 患者运动指导",
          citations=("research/sources/02 §8 R23", "daily-monitoring D16"))
def R23_运动前低值(ctx) -> RuleResult:
    """意图：运动前 G<5.0 须先补 15–30g 碳水，复测 ≥5.0 才可运动

    优先级 400（B4 运动安全 带）· 生效阶段 P2。
    挂载动作：推送告警、记录餐食与运动事件。
    """
    return _fde.RULES['R23_运动前低值'](ctx)

@spi.rule(ONTOLOGY, "R24a_运动前高值查酮体", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.POST_WRITE,
          source="Colberg 2016 ADA 运动立场",
          citations=("research/sources/02 §8 R24",))
def R24a_运动前高值查酮体(ctx) -> RuleResult:
    """意图：13.9 < G ≤ 16.7：先查酮体，阳性禁运动，阴性仅低–中强度

    优先级 405（B4 运动安全 带）· 生效阶段 P2。
    挂载动作：推送告警、记录酮体。
    """
    return _fde.RULES['R24a_运动前高值查酮体'](ctx)

@spi.rule(ONTOLOGY, "R24b_运动前极高值一律不宜运动", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.POST_WRITE,
          source="中国糖尿病防治指南 2024（不宜运动阈值）；中国 2 型糖尿病运动治疗指南 2024",
          citations=("research/sources/02 §6.1、§8 R11/R24", "临床复核补充"))
def R24b_运动前极高值一律不宜运动(ctx) -> RuleResult:
    """意图：G>16.7 无论酮体阴阳性一律不宜运动。R11 要求持续 ≥1h，而运动前是即时判断，不能等一小时

    优先级 406（B4 运动安全 带）· 生效阶段 P2。
    挂载动作：推送告警。
    """
    return _fde.RULES['R24b_运动前极高值一律不宜运动'](ctx)

@spi.rule(ONTOLOGY, "R25_运动中下降", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.POST_WRITE,
          source="ADA Standards 2026 运动期监测建议；Colberg 2016",
          citations=("research/sources/02 §8 R25",))
def R25_运动中下降(ctx) -> RuleResult:
    """意图：运动期间快速下降或已进入警戒值，提示停止运动并补碳水

    优先级 410（B4 运动安全 带）· 生效阶段 P2。
    挂载动作：推送告警。
    """
    return _fde.RULES['R25_运动中下降'](ctx)

@spi.rule(ONTOLOGY, "R26_餐后步行提醒", backing=Backing.FUNCTION, severity=Severity.SOFT,
          evaluation=Evaluation.POST_WRITE,
          source="Sci Rep 2025 餐后运动研究；Sports Med 2018 餐后运动综述",
          citations=("research/sources/02 §6.3、§8 R26",))
def R26_餐后步行提醒(ctx) -> RuleResult:
    """意图：餐后 15–30 分钟且血糖上行时提示走 10–20 分钟

    优先级 415（B4 运动安全 带）· 生效阶段 P1+P2。
    挂载动作：推送告警。
    """
    return _fde.RULES['R26_餐后步行提醒'](ctx)

@spi.rule(ONTOLOGY, "R27_运动后延迟低血糖", backing=Backing.FUNCTION, severity=Severity.SOFT,
          evaluation=Evaluation.POST_WRITE,
          source="TODO(FDE): 补依据（research/sources/02 §9 待核实清单第 2 条，Colberg 2016 原文阈值待逐字核对）",
          citations=("research/sources/02 §8 R27",))
def R27_运动后延迟低血糖(ctx) -> RuleResult:
    """意图：胰岛素或磺脲使用者当日运动 ≥45 分钟，当晚睡前目标上调 >5.6，夜间告警阈值上调至 4.4

    优先级 420（B4 运动安全 带）· 生效阶段 P1+P2。
    挂载动作：收紧告警阈值、生成方案草稿。

    # TODO(FDE): 补依据 —— 当前 source 为 TODO(FDE): 补依据（research/sources/02 §9 待核实清单第 2 条，Colberg 2016 原文阈值待逐字核对）
    """
    return _fde.RULES['R27_运动后延迟低血糖'](ctx)

@spi.rule(ONTOLOGY, "R01_数据充分性门槛_仅管结论层", backing=Backing.DECLARATIVE, severity=Severity.HARD,
          evaluation=Evaluation.PRE,
          source="ATTD 2019；中国血糖监测临床应用指南 2021",
          citations=("research/sources/02 §8 R01", "confirmed-facts A3-1、C-11", "review-and-plan D1"))
def R01_数据充分性门槛_仅管结论层(ctx) -> RuleResult:
    """意图：14 天 + ≥70% 有效数据不满足则只出趋势描述，禁出达标/分层/缓解结论。**明确不覆盖 R03a/R04a/R05/R11/R23–R25 等安全告警路径**——它不是全局前置门

    优先级 500（B5 人群与结论层 带）· 生效阶段 P1+P2。
    挂载动作：生成AGP与指标报告、输出服务分层标签、判定缓解结果、生成结营报告、兑现结果承诺。

    ★ 本规则只关结论层（达标/分层/缓解/结营/承诺兑现），**不是全局前置门**：
      不覆盖 R03a/R04a/R05/R11/R23–R25 等安全告警路径，安全通道佩戴第 1 天即生效
      （confirmed-facts C-11）。做成全局闸会静音佩戴早期的夜间低血糖。
    """
    return _fde.RULES['R01_数据充分性门槛_仅管结论层'](ctx)

@spi.rule(ONTOLOGY, "R28_老年目标切换", backing=Backing.DECLARATIVE, severity=Severity.HARD,
          evaluation=Evaluation.PRE,
          source="中国老年糖尿病诊疗指南 2024",
          citations=("confirmed-facts A3-5", "research/sources/02 §8 R28"))
def R28_老年目标切换(ctx) -> RuleResult:
    """意图：age≥65 切老年三分层目标：TIR>50%、TBR<1%、TAR>13.9 <10%。人群维度是规则入参

    优先级 505（B5 人群与结论层 带）· 生效阶段 P1+P2。
    挂载动作：入组判定、计算窗口指标、生成AGP与指标报告。
    """
    age = ctx.params.get("age")
    target_profile = ctx.params.get("target_profile")
    if not (age < 65 or target_profile == 'elderly'):  # ← 取自 IR check，取反即违反条件
        return RuleResult.fail("R28_老年目标切换 未通过", suggestion="须满足：age < 65 or target_profile == 'elderly'")
    return RuleResult.ok()

@spi.rule(ONTOLOGY, "R31_妊娠模式切换", backing=Backing.DECLARATIVE, severity=Severity.HARD,
          evaluation=Evaluation.PRE,
          source="ATTD 2019 妊娠目标表",
          citations=("research/sources/02 §1.1、§8 R31",))
def R31_妊娠模式切换(ctx) -> RuleResult:
    """意图：pregnant 切目标区间 3.5–7.8、TIR>70%、TBR<4%，并禁用德心分层与营养产品推荐

    优先级 510（B5 人群与结论层 带）· 生效阶段 P1+P2。
    挂载动作：入组判定、计算窗口指标、输出服务分层标签。
    """
    return _fde.RULES['R31_妊娠模式切换'](ctx)

@spi.rule(ONTOLOGY, "R42_急性混杂窗口禁止出结论", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.POST_WRITE,
          source="research/sources/02 §3.2 分层前提「不在急性病/用药调整期」",
          citations=("review-and-plan D2b", "behavior-matrix §7.1 G6"))
def R42_急性混杂窗口禁止出结论(ctx) -> RuleResult:
    """意图：急性病、感染发热、糖皮质激素等升糖药、住院、用药调整期内的数据不做分层、不出个性化饮食结论、不作缓解或续约依据，只出趋势描述

    优先级 508（B5 人群与结论层 带）· 生效阶段 P1+P2。
    挂载动作：输出服务分层标签、生成方案草稿、判定缓解结果、生成结营报告。
    """
    return _fde.RULES['R42_急性混杂窗口禁止出结论'](ctx)

@spi.rule(ONTOLOGY, "R49_缺参数时按最保守执行", backing=Backing.DECLARATIVE, severity=Severity.SOFT,
          evaluation=Evaluation.PRE,
          source="通用（domain-canvas 架构护栏「D2 不得在缺参数时回落一般成人阈值」）",
          citations=("domain-canvas §3.6", "behavior-matrix §7.1 G1"))
def R49_缺参数时按最保守执行(ctx) -> RuleResult:
    """意图：人群参数缺失时不得回落一般成人阈值，须按最保守（老年/高危）执行并置 population_params_stale

    优先级 512（B5 人群与结论层 带）· 生效阶段 P1+P2。
    挂载动作：计算窗口指标、生成方案草稿、推送告警。
    """
    return _fde.RULES['R49_缺参数时按最保守执行'](ctx)

@spi.rule(ONTOLOGY, "R18_CGM服务分层_内部标签", backing=Backing.FUNCTION, severity=Severity.SOFT,
          evaluation=Evaluation.POST_WRITE,
          source="research/sources/02 §3 德心映射表；中国糖尿病防治指南 2024 诊断切点",
          citations=("confirmed-facts A3-3", "research/sources/02 §3.2、§8 R18"))
def R18_CGM服务分层_内部标签(ctx) -> RuleResult:
    """意图：德心 L0–L4 映射，只作服务分层内部标签，对外措辞"提示区间，需医生确认"，**不得表述为诊断**

    优先级 515（B5 人群与结论层 带）· 生效阶段 P1+P2。
    挂载动作：输出服务分层标签。
    """
    return _fde.RULES['R18_CGM服务分层_内部标签'](ctx)

@spi.rule(ONTOLOGY, "R29_缓解判定", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.POST_WRITE,
          source="ADA 2021 缓解共识；缓解 2 型糖尿病中国专家共识 2021",
          citations=(
              "confirmed-facts A3-4",
              "research/sources/02 §7.1、§8 R29",
              "remission-assessment D6/D8",
          ))
def R29_缓解判定(ctx) -> RuleResult:
    """意图：停用全部降糖药 ≥90 天且 HbA1c<6.5%（GMI<6.5% 可替代）才标记缓解，否则禁用"缓解/逆转"字样

    优先级 520（B5 人群与结论层 带）· 生效阶段 P1+P2。
    挂载动作：判定缓解结果。
    """
    return _fde.RULES['R29_缓解判定'](ctx)

@spi.rule(ONTOLOGY, "R30_缓解适宜人群筛选_ABCD", backing=Backing.FUNCTION, severity=Severity.SOFT,
          evaluation=Evaluation.POST_WRITE,
          source="缓解 2 型糖尿病中国专家共识 2021（ABCD 标准）",
          citations=("research/sources/02 §7.1、§8 R30", "enrollment D5"))
def R30_缓解适宜人群筛选_ABCD(ctx) -> RuleResult:
    """意图：抗体阴性 AND (BMI≥25 或腰围男>90/女>85) AND 空腹 C 肽≥1.1 且餐后 2h C 肽≥2.5 AND 病程≤5 年，四条全满足才可进缓解路径

    优先级 525（B5 人群与结论层 带）· 生效阶段 P1+P2。
    挂载动作：入组判定、判定缓解结果。
    """
    return _fde.RULES['R30_缓解适宜人群筛选_ABCD'](ctx)

@spi.rule(ONTOLOGY, "R33_停药观察期反弹预警", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.POST_WRITE,
          source="TODO(FDE): 补依据（remission-assessment D4 自标\"阈值待临床确认，建议固化为 R33\"，未经临床签字不得上线）",
          citations=("remission-assessment D4",))
def R33_停药观察期反弹预警(ctx) -> RuleResult:
    """意图：停药后血糖恶化或安全事件早期预警，立即推医师并触发病因排查

    优先级 530（B5 人群与结论层 带）· 生效阶段 P1+P2。
    挂载动作：判定缓解结果、转介医师。

    # TODO(FDE): 补依据 —— 当前 source 为 TODO(FDE): 补依据（remission-assessment D4 自标"阈值待临床确认，建议固化为 R33"，未经临床签字不得上线）
    """
    return _fde.RULES['R33_停药观察期反弹预警'](ctx)

@spi.rule(ONTOLOGY, "R37_疑似1型LADA红旗", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.POST_WRITE,
          source="缓解 2 型糖尿病中国专家共识 2021 ABCD-A 项",
          citations=("enrollment D1", "research/sources/02 §7.1"))
def R37_疑似1型LADA红旗(ctx) -> RuleResult:
    """意图：命中即冻结一切减停药与缓解话术、禁推 C 包，先开抗体与 C 肽，结果回报前不解冻

    优先级 535（B5 人群与结论层 带）· 生效阶段 P1+P2。
    挂载动作：入组判定、生成方案草稿、评估可否停药并签发减停计划。
    """
    return _fde.RULES['R37_疑似1型LADA红旗'](ctx)

@spi.rule(ONTOLOGY, "R35_夜间覆盖不足禁强化", backing=Backing.DECLARATIVE, severity=Severity.HARD,
          evaluation=Evaluation.POST_WRITE,
          source="通用（confirmed-facts「一期特有医源性伤害路径」三条对策之一，临床评审新发现）",
          citations=("confirmed-facts §C 末尾对策 ①②", "机会评估"))
def R35_夜间覆盖不足禁强化(ctx) -> RuleResult:
    """意图：夜间有效覆盖 <70% 时置 nocturnal_coverage_insufficient 并在报告首屏显示，**禁止生成任何强化降糖方向的草稿**。夜间缺口会让 TBR 被系统性低估，医师在一个低估了低血糖的数据集上加药，是老年严重低血糖的经典成因

    优先级 540（B5 人群与结论层 带）· 生效阶段 P1+P2。
    挂载动作：生成方案草稿、生成AGP与指标报告。
    """
    return _fde.RULES['R35_夜间覆盖不足禁强化'](ctx)

@spi.rule(ONTOLOGY, "R50_夜间低覆盖高危用药进临床队列", backing=Backing.DECLARATIVE, severity=Severity.HARD,
          evaluation=Evaluation.POST_WRITE,
          source="通用（confirmed-facts「一期特有医源性伤害路径」对策 ③）",
          citations=("confirmed-facts §C 末尾对策 ③",))
def R50_夜间低覆盖高危用药进临床队列(ctx) -> RuleResult:
    """意图：用胰岛素或磺脲，且连续 ≥2 晚夜间有效率 <50% 的患者，进临床队列低血糖分支，**不是挽留队列**

    优先级 542（B5 人群与结论层 带）· 生效阶段 P1+P2。
    挂载动作：生成去强化证据工单。
    """
    return _fde.RULES['R50_夜间低覆盖高危用药进临床队列'](ctx)

@spi.rule(ONTOLOGY, "R41_器械交易主体与收货合规", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.PRE,
          source="医疗器械经营监督管理办法；医疗器械监督管理条例第 40–42 条",
          citations=("enrollment D8", "confirmed-facts B-1", "research/sources/04 §6 风险 1"))
def R41_器械交易主体与收货合规(ctx) -> RuleResult:
    """意图：销售主体须持证、票据抬头与收货人均为患者本人、门店无器械库存记录、无按销量返佣

    优先级 545（B5 人群与结论层 带）· 生效阶段 P1+P2。
    挂载动作：记录到店随机指血分诊、建立传感器会话。
    """
    # TODO(FDE): 查销售主体资质、票据抬头与收货人、门店库存记录与返佣配置
    # 可用：ctx.get / ctx.find / ctx.search_around（写后可见本次暂存写入）
    raise NotImplementedError("R41_器械交易主体与收货合规 待实现")

@spi.rule(ONTOLOGY, "R32_产品推荐合规闸", backing=Backing.DECLARATIVE, severity=Severity.HARD,
          evaluation=Evaluation.POST_WRITE,
          source="广告法第 17 条；食品安全法第 73 条；总局 2021 年第 46 号公告",
          citations=("research/sources/02 §8 R32", "confirmed-facts A2-4、B-2"))
def R32_产品推荐合规闸(ctx) -> RuleResult:
    """意图：产品推荐不得与服务分层结论、"缓解/逆转"字样同句出现，且必须附"固体饮料，不替代药物"尾注

    优先级 600（B6 出口签发闸 带）· 生效阶段 P1+P2。
    挂载动作：生成产品推荐、审核输出内容。
    """
    return _fde.RULES['R32_产品推荐合规闸'](ctx)

@spi.rule(ONTOLOGY, "D8_禁用词拦截", backing=Backing.DECLARATIVE, severity=Severity.HARD,
          evaluation=Evaluation.POST_WRITE,
          source="食品安全法第 71、73 条；广告法第 17、28、55 条；反不正当竞争法第 9 条；总局 2021 年第 46 号公告第 4 条",
          citations=("review-and-plan D8", "research/sources/04 §6 风险 13"))
def D8_禁用词拦截(ctx) -> RuleResult:
    """意图：逆转/治愈/停药/疗程/修复胰腺/降血糖/MNT 医学营养治疗等词一律拦截重写，2 次不过转人工

    优先级 605（B6 出口签发闸 带）· 生效阶段 P1+P2。
    挂载动作：审核输出内容、群内答复患者、发布宣传素材。
    """
    return _fde.RULES['D8_禁用词拦截'](ctx)

@spi.rule(ONTOLOGY, "C9_AI方案禁止直接推送", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.PRE,
          source="互联网诊疗监管细则第 13、21 条；医师法；医疗机构管理条例实施细则第 88 条",
          citations=("research/sources/04 §6 风险 9", "confirmed-facts A2-3、B-3"))
def C9_AI方案禁止直接推送(ctx) -> RuleResult:
    """意图：AI 只出草稿，医师或注册营养师签发后才能推送。这是产品能合法存在的前提

    优先级 610（B6 出口签发闸 带）· 生效阶段 P1+P2。
    挂载动作：推送方案至患者。
    """
    return _fde.RULES['C9_AI方案禁止直接推送'](ctx)

@spi.rule(ONTOLOGY, "D9_产品功效声称拦截", backing=Backing.DECLARATIVE, severity=Severity.HARD,
          evaluation=Evaluation.POST_WRITE,
          source="食品安全法第 71、73 条；广告法第 17、28 条",
          citations=("review-and-plan D9", "research/sources/04 §6 风险 13"))
def D9_产品功效声称拦截(ctx) -> RuleResult:
    """意图：出现营养食品推荐时，与分层或缓解同句即硬拦截，否则强制尾注

    优先级 615（B6 出口签发闸 带）· 生效阶段 P1+P2。
    挂载动作：审核输出内容、生成产品推荐、发布宣传素材。
    """
    return _fde.RULES['D9_产品功效声称拦截'](ctx)

@spi.rule(ONTOLOGY, "D10_用药建议拦截", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.POST_WRITE,
          source="互联网诊疗监管细则第 21 条；医师法（处方权）",
          citations=("review-and-plan D10", "daily-monitoring D26", "research/sources/04 §6 风险 10"))
def D10_用药建议拦截(ctx) -> RuleResult:
    """意图：药名 + 剂量/加减停/换药动词一律硬拦截并转医师任务，健管师与 AI 均不得答

    优先级 618（B6 出口签发闸 带）· 生效阶段 P1+P2。
    挂载动作：审核输出内容、群内答复患者、生成方案草稿。
    """
    return _fde.RULES['D10_用药建议拦截'](ctx)

@spi.rule(ONTOLOGY, "D11_未确认分型分级措辞拦截", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.POST_WRITE,
          source="医疗机构管理条例实施细则第 88 条；ADA/CDS 均无 CGM 诊断条目",
          citations=("confirmed-facts A3-3", "review-and-plan D11", "research/sources/04 §6 风险 11"))
def D11_未确认分型分级措辞拦截(ctx) -> RuleResult:
    """意图：出现"你是 X 型/X 级糖尿病"式确定性措辞须降级或移除；CGM 不能用于诊断

    优先级 620（B6 出口签发闸 带）· 生效阶段 P1+P2。
    挂载动作：审核输出内容、输出服务分层标签。
    """
    return _fde.RULES['D11_未确认分型分级措辞拦截'](ctx)

@spi.rule(ONTOLOGY, "R51_分层结论默认不可披露患者", backing=Backing.DECLARATIVE, severity=Severity.HARD,
          evaluation=Evaluation.PRE,
          source="互联网诊疗监管细则第 21 条；医疗机构管理条例实施细则第 88 条（直推构成无证诊断时适用）",
          citations=("confirmed-facts A2-3、B-3", "behavior-matrix §6/§8", "domain-canvas §3.5 ③"))
def R51_分层结论默认不可披露患者(ctx) -> RuleResult:
    """意图：tier_label 必与 disclosure_approved 同表且默认 false，未经医师披露授权不得直推患者。理由链：直推等于以非诊断手段作出诊断化表述

    优先级 622（B6 出口签发闸 带）· 生效阶段 P1+P2。
    挂载动作：推送方案至患者、输出服务分层标签、群内答复患者。
    """
    return _fde.RULES['R51_分层结论默认不可披露患者'](ctx)

@spi.rule(ONTOLOGY, "D11a_签发人资质失效自动冻结", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.PRE,
          source="TODO(FDE): 补依据（执业资格核验，需补《医师法》与营养师注册管理的具体条款号）",
          citations=("review-and-plan D11a", "domain-canvas D18"))
def D11a_签发人资质失效自动冻结(ctx) -> RuleResult:
    """意图：执业证/多点执业备案/注册证/康复师资质任一过期即自动冻结签发权限，任务转有资质人员

    优先级 625（B6 出口签发闸 带）· 生效阶段 P1+P2。
    挂载动作：签发方案、评估可否停药并签发减停计划、判定缓解结果。

    # TODO(FDE): 补依据 —— 当前 source 为 TODO(FDE): 补依据（执业资格核验，需补《医师法》与营养师注册管理的具体条款号）
    """
    return _fde.RULES['D11a_签发人资质失效自动冻结'](ctx)

@spi.rule(ONTOLOGY, "D12_签发人归属分流", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.PRE,
          source="医师法；临床营养师与康复治疗师执业范围规定",
          citations=("review-and-plan D12", "behavior-matrix §8.1"))
def D12_签发人归属分流(ctx) -> RuleResult:
    """意图：用药或分型 → 医师；营养 → 注册营养师且不含用药；运动 → 康复师起草 + 医师筛查运动禁忌后双签发；教育 → 健管师

    优先级 628（B6 出口签发闸 带）· 生效阶段 P1+P2。
    挂载动作：签发方案。
    """
    return _fde.RULES['D12_签发人归属分流'](ctx)

@spi.rule(ONTOLOGY, "R45_紧急告警豁免关键词闸", backing=Backing.DECLARATIVE, severity=Severity.HARD,
          evaluation=Evaluation.PRE,
          source="通用（domain-canvas 临床评审推翻了\"所有对外输出经统一闸门\"的初稿设计）",
          citations=("confirmed-facts C-10", "domain-canvas §3.6"))
def R45_紧急告警豁免关键词闸(ctx) -> RuleResult:
    """意图：低血糖处置话术天然含"胰岛素/磺脲/停"字样，词库误命中会吃掉致命告警。**只豁免关键词与实体识别类闸门（D8/D9/D10/D11），不豁免 C22 免责尾注与 R54 夜间承诺红线**——这两条改由 R56 在模板预审阶段兜住

    优先级 630（B6 出口签发闸 带）· 生效阶段 P1+P2。
    挂载动作：推送告警。
    """
    return _fde.RULES['R45_紧急告警豁免关键词闸'](ctx)

@spi.rule(ONTOLOGY, "R56_告警模板预审冻结", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.PRE,
          source="通用（confirmed-facts C-10 的配套机制：豁免运行时闸门的前提是模板已过预审）",
          citations=("confirmed-facts C-10、B-11", "domain-canvas §3.6"))
def R56_告警模板预审冻结(ctx) -> RuleResult:
    """意图：告警话术不走运行时闸门，改为模板预先审定并冻结；模板准入时必须一次性满足免责尾注与夜间承诺红线，之后运行时只允许套用已冻结模板，不允许现场生成

    优先级 631（B6 出口签发闸 带）· 生效阶段 P1+P2。
    挂载动作：推送告警。
    """
    return _fde.RULES['R56_告警模板预审冻结'](ctx)

@spi.rule(ONTOLOGY, "R52_回填读数不得触发实时告警", backing=Backing.DECLARATIVE, severity=Severity.HARD,
          evaluation=Evaluation.PRE,
          source="通用（domain-canvas 架构护栏「D4 ⇏ is_backfill 读数」）",
          citations=("domain-canvas §3.6", "behavior-matrix E53"))
def R52_回填读数不得触发实时告警(ctx) -> RuleResult:
    """意图：回填 14 天历史会把三周前的低血糖当实时危急值推进群里。is_backfill 读数只进统计通道

    优先级 632（B6 出口签发闸 带）· 生效阶段 P1+P2。
    挂载动作：推送告警、触发低血糖处置。
    """
    return _fde.RULES['R52_回填读数不得触发实时告警'](ctx)

@spi.rule(ONTOLOGY, "R53_低置信通道不得独立触发危急告警", backing=Backing.DECLARATIVE, severity=Severity.HARD,
          evaluation=Evaluation.PRE,
          source="通用（daily-monitoring D7a 防假危急外呼链）",
          citations=("daily-monitoring D7a", "domain-canvas §3.6"))
def R53_低置信通道不得独立触发危急告警(ctx) -> RuleResult:
    """意图：OCR 与手工录入不得独立触发危急告警，须先指血复测或健管师加急复核确认。未复核的单位误读会制造大量假低血糖

    优先级 634（B6 出口签发闸 带）· 生效阶段 P1+P2。
    挂载动作：推送告警、触发低血糖处置。
    """
    return _fde.RULES['R53_低置信通道不得独立触发危急告警'](ctx)

@spi.rule(ONTOLOGY, "D13_签发反橡皮图章检测", backing=Backing.FUNCTION, severity=Severity.SOFT,
          evaluation=Evaluation.POST_WRITE,
          source="通用（内部质控 SOP，反橡皮图章）",
          citations=("review-and-plan D13", "confirmed-facts C-07"))
def D13_签发反橡皮图章检测(ctx) -> RuleResult:
    """意图：停留 <20 秒标 review_suspicious，连续 10 份零修改触发质控复核。系统不提供"批量全部通过"按钮

    优先级 638（B6 出口签发闸 带）· 生效阶段 P1+P2。
    挂载动作：签发方案。
    """
    return _fde.RULES['D13_签发反橡皮图章检测'](ctx)

@spi.rule(ONTOLOGY, "C1_器械经营资质闸", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.PRE,
          source="医疗器械监督管理条例第 40–42、84 条；医疗器械网络销售监督管理办法",
          citations=("research/sources/04 §6 风险 1", "confirmed-facts A2-1、B-1"))
def C1_器械经营资质闸(ctx) -> RuleResult:
    """意图：门店与平台均无三类经营许可，CGM 交易只能由持证厂商或经销商完成，门店纯引流不碰货不收款

    优先级 650（B7 器械/数据/机构合规 带）· 生效阶段 P1+P2。
    挂载动作：上架产品SKU、创建服务包SKU。
    """
    return _fde.RULES['C1_器械经营资质闸'](ctx)

@spi.rule(ONTOLOGY, "C2_网络销售备案与证照公示", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.PRE,
          source="医疗器械网络销售监督管理办法第 8、11 条",
          citations=("research/sources/04 §6 风险 2",))
def C2_网络销售备案与证照公示(ctx) -> RuleResult:
    """意图：器械类 SKU 须单独频道并展示经营许可证与注册证，无证不上架

    优先级 655（B7 器械/数据/机构合规 带）· 生效阶段 P1+P2。
    挂载动作：上架产品SKU。
    """
    return _fde.RULES['C2_网络销售备案与证照公示'](ctx)

@spi.rule(ONTOLOGY, "C3_敏感个人信息单独同意", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.PRE,
          source="个人信息保护法第 28、29、30 条",
          citations=("confirmed-facts A2-2", "enrollment D9", "research/sources/04 §6 风险 3"))
def C3_敏感个人信息单独同意(ctx) -> RuleResult:
    """意图：血糖与用药属敏感个人信息，须单独同意 + 逐项勾选 + 电子签名 + 时间戳落库，未取得则服务挂起、零数据摄入

    优先级 660（B7 器械/数据/机构合规 带）· 生效阶段 P1+P2。
    挂载动作：摄入读数、建立传感器会话、标记入组成功。
    """
    return _fde.RULES['C3_敏感个人信息单独同意'](ctx)

@spi.rule(ONTOLOGY, "C4_数据用于产品推荐须单独同意", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.PRE,
          source="GB/T 39725 第 7 章；个人信息保护法第 24 条（自动化决策）",
          citations=("research/sources/04 §6 风险 4",))
def C4_数据用于产品推荐须单独同意(ctx) -> RuleResult:
    """意图：营销用途须单独勾选，推荐可关闭，自动化决策提供人工复核入口

    优先级 665（B7 器械/数据/机构合规 带）· 生效阶段 P1+P2。
    挂载动作：生成产品推荐。
    """
    return _fde.RULES['C4_数据用于产品推荐须单独同意'](ctx)

@spi.rule(ONTOLOGY, "C5_厂商云对接协议与PIPIA", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.PRE,
          source="个人信息保护法第 21、23、55 条；网络数据安全管理条例第 12 条",
          citations=("research/sources/04 §6 风险 5",))
def C5_厂商云对接协议与PIPIA(ctx) -> RuleResult:
    """意图：云对接前须签数据接收协议、完成 PIPIA，处理记录保存 3 年

    优先级 670（B7 器械/数据/机构合规 带）· 生效阶段 P1+P2。
    挂载动作：建立厂商云通道对接。
    """
    # TODO(FDE): 查该厂商是否已签数据接收/委托协议，且 PIPIA 评估留痕是否完成
    # 可用：ctx.get / ctx.find / ctx.search_around（写后可见本次暂存写入）
    raise NotImplementedError("C5_厂商云对接协议与PIPIA 待实现")

@spi.rule(ONTOLOGY, "C6_群内数据最小可见范围", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.POST_WRITE,
          source="个人信息保护法第 6 条（最小必要）；医疗卫生机构网络安全管理办法",
          citations=("research/sources/04 §6 风险 6", "behavior-matrix §8.1"))
def C6_群内数据最小可见范围(ctx) -> RuleResult:
    """意图：血糖与用药只在平台内可见，群内只推脱敏卡片；店长退出患者群

    优先级 675（B7 器械/数据/机构合规 带）· 生效阶段 P1+P2。
    挂载动作：群内答复患者、推送方案至患者。
    """
    return _fde.RULES['C6_群内数据最小可见范围'](ctx)

@spi.rule(ONTOLOGY, "C7_患者数据禁止存放非平台工具", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.PRE,
          source="个人信息保护法第 23、51 条；人口健康信息管理办法第 10、16 条",
          citations=("research/sources/04 §6 风险 7", "domain-canvas §3.5 ①"))
def C7_患者数据禁止存放非平台工具(ctx) -> RuleResult:
    """意图：病历式数据须在境内加密可审计的平台内，不得用个人版 SaaS 表格。写入第三方 SaaS 即构成向第三方提供个人信息，故同时适用第 23 条告知义务，不只是第 51 条安全措施

    优先级 680（B7 器械/数据/机构合规 带）· 生效阶段 P1+P2。
    挂载动作：写入外部协作工具。
    """
    return _fde.RULES['C7_患者数据禁止存放非平台工具'](ctx)

@spi.rule(ONTOLOGY, "C8_数据出境与境外云禁止", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.PRE,
          source="个人信息保护法第 38–40 条；人口健康信息管理办法第 10 条；网络数据安全管理条例第 35 条",
          citations=("research/sources/04 §6 风险 8", "enrollment D11a", "domain-canvas D7"))
def C8_数据出境与境外云禁止(ctx) -> RuleResult:
    """意图：服务器须境内且厂商出具书面承诺，否则禁止通道对接；出境拦截范围须覆盖多模态模型调用

    优先级 685（B7 器械/数据/机构合规 带）· 生效阶段 P1+P2。
    挂载动作：建立厂商云通道对接、启用AI生成能力。
    """
    # TODO(FDE): 查 ChannelRegistry.storage_region 与厂商书面承诺文件；模型调用侧校验推理节点所在地
    # 可用：ctx.get / ctx.find / ctx.search_around（写后可见本次暂存写入）
    raise NotImplementedError("C8_数据出境与境外云禁止 待实现")

@spi.rule(ONTOLOGY, "C21_数据留存与审计日志", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.PRE,
          source="互联网诊疗监管细则第 19 条；网络数据安全管理条例第 12 条",
          citations=("research/sources/04 §6 风险 21", "domain-canvas D13"))
def C21_数据留存与审计日志(ctx) -> RuleResult:
    """意图：留存 ≥3 年，操作全程可审计可导出给监管

    优先级 690（B7 器械/数据/机构合规 带）· 生效阶段 系统级。
    挂载动作：摄入读数、签发方案、响应并回执告警。
    """
    return _fde.RULES['C21_数据留存与审计日志'](ctx)

@spi.rule(ONTOLOGY, "C11_分型输出制度层不得当诊断", backing=Backing.DECLARATIVE, severity=Severity.HARD,
          evaluation=Evaluation.POST_WRITE,
          source="医疗机构管理条例实施细则第 88 条；医疗器械软件注册相关规定",
          citations=("research/sources/04 §6 风险 11",))
def C11_分型输出制度层不得当诊断(ctx) -> RuleResult:
    """意图：内部标签不直推患者，宣传不用"诊断/分型确诊"；必要时评估是否走独立软件注册

    优先级 700（B7 器械/数据/机构合规 带）· 生效阶段 P1+P2。
    挂载动作：发布宣传素材、输出服务分层标签。
    """
    return _fde.RULES['C11_分型输出制度层不得当诊断'](ctx)

@spi.rule(ONTOLOGY, "C12_生成式AI备案与算法备案", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.PRE,
          source="生成式人工智能服务管理暂行办法第 17 条；互联网信息服务算法推荐管理规定",
          citations=("research/sources/04 §6 风险 12",))
def C12_生成式AI备案与算法备案(ctx) -> RuleResult:
    """意图：智能体上线前须完成生成式 AI 备案或登记、算法备案，并做内容过滤与日志

    优先级 705（B7 器械/数据/机构合规 带）· 生效阶段 系统级。
    挂载动作：启用AI生成能力。
    """
    # TODO(FDE): 查系统是否已完成生成式 AI 备案登记与算法备案，并核验内容过滤与日志开关
    # 可用：ctx.get / ctx.find / ctx.search_around（写后可见本次暂存写入）
    raise NotImplementedError("C12_生成式AI备案与算法备案 待实现")

@spi.rule(ONTOLOGY, "C13_服务与产品物理分离", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.PRE,
          source="食品安全法第 71、73 条；广告法第 17、28、55 条；总局 2021 年第 46 号公告第 4 条",
          citations=("confirmed-facts A2-4、B-2", "research/sources/04 §6 风险 13"))
def C13_服务与产品物理分离(ctx) -> RuleResult:
    """意图：服务包合同、收款、宣传不含任何产品；食品由医师在 HIS 内单独开具、单独收款

    优先级 710（B7 器械/数据/机构合规 带）· 生效阶段 P1+P2。
    挂载动作：创建服务包SKU、生成产品推荐。
    """
    return _fde.RULES['C13_服务与产品物理分离'](ctx)

@spi.rule(ONTOLOGY, "C14_产品标签合规校验", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.PRE,
          source="总局 2021 年第 46 号公告第 3 条；食品标识监督管理办法",
          citations=("research/sources/04 §6 风险 14",))
def C14_产品标签合规校验(ctx) -> RuleResult:
    """意图：采购前核验"固体饮料"字号与警示语，不合格不上架

    优先级 715（B7 器械/数据/机构合规 带）· 生效阶段 P1+P2。
    挂载动作：上架产品SKU。
    """
    return _fde.RULES['C14_产品标签合规校验'](ctx)

@spi.rule(ONTOLOGY, "C15_服务包禁止捆绑分佣", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.PRE,
          source="广告法第 17 条；反不正当竞争法第 7 条；医疗机构工作人员廉洁从业九项准则",
          citations=("research/sources/04 §6 风险 15",))
def C15_服务包禁止捆绑分佣(ctx) -> RuleResult:
    """意图：服务包只含服务与器械租用；对医务人员不设产品销售提成

    优先级 720（B7 器械/数据/机构合规 带）· 生效阶段 P1+P2。
    挂载动作：创建服务包SKU。
    """
    return _fde.RULES['C15_服务包禁止捆绑分佣'](ctx)

@spi.rule(ONTOLOGY, "C16_禁止发布患者前后对比案例", backing=Backing.DECLARATIVE, severity=Severity.HARD,
          evaluation=Evaluation.POST_WRITE,
          source="医疗广告管理办法第 7 条；广告法第 17、28 条；个人信息保护法第 29 条",
          citations=("research/sources/04 §6 风险 16",))
def C16_禁止发布患者前后对比案例(ctx) -> RuleResult:
    """意图：停发个案对比，改用匿名聚合数据 + 医疗广告审查；患者须书面同意且可撤回

    优先级 725（B7 器械/数据/机构合规 带）· 生效阶段 P1+P2。
    挂载动作：发布宣传素材。
    """
    return _fde.RULES['C16_禁止发布患者前后对比案例'](ctx)

@spi.rule(ONTOLOGY, "C17_机构与门诊命名合规", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.PRE,
          source="医疗机构管理条例实施细则第 40–48 条；2020 年与 2025 年医疗机构名称规范通知",
          citations=("confirmed-facts A2-5", "research/sources/04 §6 风险 17"))
def C17_机构与门诊命名合规(ctx) -> RuleResult:
    """意图："糖尿病逆转中心"类命名与卫健命名规范冲突，须改为"糖尿病（特色）门诊 / 代谢健康管理中心"

    优先级 730（B7 器械/数据/机构合规 带）· 生效阶段 P1+P2。
    挂载动作：设定机构与门诊名称、发布宣传素材。
    """
    return _fde.RULES['C17_机构与门诊命名合规'](ctx)

@spi.rule(ONTOLOGY, "C18_非医疗机构不得实施诊疗", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.PRE,
          source="医疗机构管理条例；基本医疗卫生与健康促进法",
          citations=("research/sources/04 §6 风险 18", "confirmed-facts A2-6"))
def C18_非医疗机构不得实施诊疗(ctx) -> RuleResult:
    """意图：检测 + 判断 + 方案的组合属诊疗行为，须由持证医疗机构实施；健康管理公司只做不涉判断的服务

    优先级 735（B7 器械/数据/机构合规 带）· 生效阶段 P1+P2。
    挂载动作：记录到店随机指血分诊、入组判定。
    """
    # TODO(FDE): 查提供该服务的 StoreEntity 是否持医疗机构执业许可及对应诊疗科目
    # 可用：ctx.get / ctx.find / ctx.search_around（写后可见本次暂存写入）
    raise NotImplementedError("C18_非医疗机构不得实施诊疗 待实现")

@spi.rule(ONTOLOGY, "C19_线上随访边界", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.PRE,
          source="互联网诊疗管理办法；互联网诊疗监管细则第 19 条",
          citations=("research/sources/04 §6 风险 19",))
def C19_线上随访边界(ctx) -> RuleResult:
    """意图：定性为健康管理随访并限制内容，否则须办互联网诊疗备案 + 等保三级

    优先级 740（B7 器械/数据/机构合规 带）· 生效阶段 P1+P2。
    挂载动作：开展线上随访、群内答复患者。
    """
    return _fde.RULES['C19_线上随访边界'](ctx)

@spi.rule(ONTOLOGY, "C20_危急值须系统自动告警并记录响应", backing=Backing.FUNCTION, severity=Severity.HARD,
          evaluation=Evaluation.POST_WRITE,
          source="TODO(FDE): 补依据（医疗质量安全核心制度「危急值报告制度」，需补具体文号）",
          citations=("research/sources/04 §6 风险 20", "daily-monitoring §2.4"))
def C20_危急值须系统自动告警并记录响应(ctx) -> RuleResult:
    """意图：不得依赖群聊人工发现，须系统自动阈值告警直达值班医师与患者并记录响应时间

    优先级 745（B7 器械/数据/机构合规 带）· 生效阶段 P2。
    挂载动作：推送告警、响应并回执告警。

    # TODO(FDE): 补依据 —— 当前 source 为 TODO(FDE): 补依据（医疗质量安全核心制度「危急值报告制度」，需补具体文号）
    """
    return _fde.RULES['C20_危急值须系统自动告警并记录响应'](ctx)

@spi.rule(ONTOLOGY, "C22_免责声明强制展示", backing=Backing.DECLARATIVE, severity=Severity.HARD,
          evaluation=Evaluation.POST_WRITE,
          source="消费者权益保护法第 26 条；个人信息保护法告知义务条款",
          citations=("research/sources/04 §6 风险 22",))
def C22_免责声明强制展示(ctx) -> RuleResult:
    """意图：AI 生成内容固定尾注 + 首次弹窗 + 服务协议明确"非诊疗"，但不得以此免除 AI 错误建议造成损害的责任

    优先级 748（B7 器械/数据/机构合规 带）· 生效阶段 P1+P2。
    挂载动作：审核输出内容、推送方案至患者。
    """
    return _fde.RULES['C22_免责声明强制展示'](ctx)

@spi.rule(ONTOLOGY, "R38_告警兜底配置未完成禁止佩戴", backing=Backing.DECLARATIVE, severity=Severity.HARD,
          evaluation=Evaluation.PRE,
          source="通用（内部 SOP，与二期夜间值班约束一致）",
          citations=("enrollment D8b", "daily-monitoring §2.4"))
def R38_告警兜底配置未完成禁止佩戴(ctx) -> RuleResult:
    """意图：告警接收人、夜间兜底电话、紧急联系人未齐全禁止贴片

    优先级 750（B8 流程操作性 带）· 生效阶段 P2。
    挂载动作：建立传感器会话。
    """
    alert_receiver = ctx.params.get("alert_receiver")
    emergency_contact = ctx.params.get("emergency_contact")
    night_fallback_phone = ctx.params.get("night_fallback_phone")
    if not (alert_receiver is not None and night_fallback_phone is not None and emergency_contact is not None):  # ← 取自 IR check，取反即违反条件
        return RuleResult.fail("R38_告警兜底配置未完成禁止佩戴 未通过", suggestion="须满足：alert_receiver is not None and night_fallback_phone is not None and emergency_contact is not None")
    return RuleResult.ok()

@spi.rule(ONTOLOGY, "R39_覆盖告知未留痕禁止入组成功", backing=Backing.DECLARATIVE, severity=Severity.HARD,
          evaluation=Evaluation.PRE,
          source="通用（confirmed-facts B-11、B-13 分期边界硬红线）",
          citations=("enrollment D11c", "confirmed-facts B-11"))
def R39_覆盖告知未留痕禁止入组成功(ctx) -> RuleResult:
    """意图：患者与家属须签署《覆盖范围告知书》，一期结构性无当夜干预能力，患者必须知情才能做别的安排

    优先级 755（B8 流程操作性 带）· 生效阶段 P1+P2。
    挂载动作：标记入组成功。
    """
    coverage_disclosed_at = ctx.params.get("coverage_disclosed_at")
    if not (coverage_disclosed_at is not None):  # ← 取自 IR check，取反即违反条件
        return RuleResult.fail("R39_覆盖告知未留痕禁止入组成功 未通过", suggestion="须满足：coverage_disclosed_at is not None")
    return RuleResult.ok()

@spi.rule(ONTOLOGY, "R54_服务话术不得含夜间安全承诺", backing=Backing.DECLARATIVE, severity=Severity.HARD,
          evaluation=Evaluation.POST_WRITE,
          source="通用（confirmed-facts B-11 硬红线，一期是确定状态不是临时状态）",
          citations=("confirmed-facts B-11、B-13", "processes/README"))
def R54_服务话术不得含夜间安全承诺(ctx) -> RuleResult:
    """意图：载体与夜间值班未落地前，服务包与对外话术不得含"夜间监护/夜里出事有人知道/24 小时看护"等承诺

    优先级 758（B8 流程操作性 带）· 生效阶段 P1+P2。
    挂载动作：审核输出内容、创建服务包SKU、发布宣传素材、群内答复患者。
    """
    return _fde.RULES['R54_服务话术不得含夜间安全承诺'](ctx)

@spi.rule(ONTOLOGY, "R40_老年画像禁止仅靠自觉同步", backing=Backing.DECLARATIVE, severity=Severity.SOFT,
          evaluation=Evaluation.PRE,
          source="通用（enrollment D11e，同步节律决定一期数据完整性）",
          citations=("enrollment D11e", "confirmed-facts D-12"))
def R40_老年画像禁止仅靠自觉同步(ctx) -> RuleResult:
    """意图：老年画像不得依赖"患者自觉打开 App"，主路径须是到店自动同步或家属协助

    优先级 760（B8 流程操作性 带）· 生效阶段 P1+P2。
    挂载动作：建立同步计划。
    """
    age = ctx.params.get("age")
    trigger_type = ctx.params.get("trigger_type")
    if not (age < 65 or trigger_type != '主动打开'):  # ← 取自 IR check，取反即违反条件
        return RuleResult.fail("R40_老年画像禁止仅靠自觉同步 未通过", suggestion="须满足：age < 65 or trigger_type != '主动打开'")
    return RuleResult.ok()

@spi.rule(ONTOLOGY, "R43_落库验证未通过禁止入组成功", backing=Backing.DECLARATIVE, severity=Severity.HARD,
          evaluation=Evaluation.PRE,
          source="通用（enrollment D11b 离店硬闸）",
          citations=("enrollment D11b",))
def R43_落库验证未通过禁止入组成功(ctx) -> RuleResult:
    """意图：门店内未验证到端到端落库读数不得标记入组成功，服务包计时不启动，48h 不通则协商或退款

    优先级 765（B8 流程操作性 带）· 生效阶段 P1+P2。
    挂载动作：标记入组成功。
    """
    channel_verified_at_store = ctx.params.get("channel_verified_at_store")
    if not (channel_verified_at_store is True):  # ← 取自 IR check，取反即违反条件
        return RuleResult.fail("R43_落库验证未通过禁止入组成功 未通过", suggestion="须满足：channel_verified_at_store is True")
    return RuleResult.ok()

@spi.rule(ONTOLOGY, "R55_显示口径_没有数据不得说成没有异常", backing=Backing.DECLARATIVE, severity=Severity.HARD,
          evaluation=Evaluation.POST_WRITE,
          source="通用（confirmed-facts B-12，行为矩阵与旅程图一致结论；优先级高于本项目几乎所有功能项）",
          citations=("confirmed-facts B-12", "processes/README"))
def R55_显示口径_没有数据不得说成没有异常(ctx) -> RuleResult:
    """意图："没有数据"与"没有异常"在老人端、子女端、健管师队列三处不能长得一样；数据不足时禁止回退到"平稳"措辞

    优先级 768（B8 流程操作性 带）· 生效阶段 P1+P2。
    挂载动作：推送方案至患者、群内答复患者、生成AGP与指标报告。
    """
    return _fde.RULES['R55_显示口径_没有数据不得说成没有异常'](ctx)


# ============================================================================
# §5 Actions —— 63 个。@spi.action 声明齐全，handler 回写逻辑一律骨架 + TODO(FDE)。
# ============================================================================

@spi.action(
    ONTOLOGY, "签署单独同意书",
    description="为患者登记一份单独同意书：记录逐项勾选的范围、电子签名与时间戳，生成 ConsentRecord",
    params=(
        ParamSpec("patient_id", "string", required=True),
        ParamSpec("scope_items", "list", required=True),
        ParamSpec("signature", "string", required=True),
    ),
    post_rules=("C3_敏感个人信息单独同意",),
    writes=("ConsentRecord",),
    validate_supported=True,
    hil=HilPolicy(reviewer_role="患者本人",
                  predicate=lambda confidence, touched_hard: True),
)
def 签署单独同意书(ctx) -> None:
    """患者本人逐项勾选并电子签名，七项范围不得合并

    HIL：患者本人（触发条件 always）。
    写入对象：ConsentRecord。
    """
    # TODO(FDE): 业务回写。逐个 writes 对象补 stage_write，key 命名由 FDE 定：
    # ctx.stage_write("ConsentRecord", f"consentrecord_{ctx.params[...]}", {...})
    # ctx.emit_effect("workitem", on="...", template="...")   # 如需派工单
    ctx.set_confidence(0.8)
    # ctx.add_evidence(source="...")                            # 取自命中规则的 source
    raise NotImplementedError("签署单独同意书 handler 待实现")

@spi.action(
    ONTOLOGY, "撤回同意",
    description="按范围撤回患者已签的同意，记录撤回并级联更新受影响的下游数据项",
    params=(
        ParamSpec("patient_id", "string", required=True),
        ParamSpec("scope", "list", required=True),
    ),
    writes=("ConsentRevocation", "ConsentRecord"),
    validate_supported=True,
    # 与「处理数据主体权利请求」同为 PIPL 权利响应，口径必须一致（validate B.4）
    hil=HilPolicy(reviewer_role="合规官（受理与级联核验）",
                  predicate=lambda confidence, touched_hard: True),
)
def 撤回同意(ctx) -> None:
    """按范围撤回并级联下游，须产出豁免触达封锁的告知

    写入对象：ConsentRevocation、ConsentRecord。
    """
    # TODO(FDE): 业务回写。逐个 writes 对象补 stage_write，key 命名由 FDE 定：
    # ctx.stage_write("ConsentRevocation", f"consentrevocation_{ctx.params[...]}", {...})
    # ctx.stage_write("ConsentRecord", f"consentrecord_{ctx.params[...]}", {...})
    # ctx.emit_effect("workitem", on="...", template="...")   # 如需派工单
    ctx.set_confidence(0.8)
    # ctx.add_evidence(source="...")                            # 取自命中规则的 source
    raise NotImplementedError("撤回同意 handler 待实现")

@spi.action(
    ONTOLOGY, "录入结构化用药清单",
    description="把患者的结构化用药清单（药名、类别标签）写入画像 meds 字段",
    params=(
        ParamSpec("patient_id", "string", required=True),
        ParamSpec("meds_list", "list", required=True),
    ),
    guards=("D11a_签发人资质失效自动冻结",),
    post_rules=("R49_缺参数时按最保守执行",),
    writes=("PatientProfile",),
    validate_supported=True,
    hil=HilPolicy(reviewer_role="医师/药师",
                  predicate=lambda confidence, touched_hard: True),
)
def 录入结构化用药清单(ctx) -> None:
    """医师或药师录入 meds 并打四标签

    HIL：医师/药师（触发条件 always）。
    写入对象：PatientProfile。
    """
    # TODO(FDE): 业务回写。逐个 writes 对象补 stage_write，key 命名由 FDE 定：
    # ctx.stage_write("PatientProfile", f"patientprofile_{ctx.params[...]}", {...})
    # ctx.emit_effect("workitem", on="...", template="...")   # 如需派工单
    ctx.set_confidence(0.8)
    # ctx.add_evidence(source="...")                            # 取自命中规则的 source
    raise NotImplementedError("录入结构化用药清单 handler 待实现")

@spi.action(
    ONTOLOGY, "采集用药线索",
    description="记录患者自报或药盒照片得到的用药线索（MedClassHint），与正式用药清单分开存放",
    params=(
        ParamSpec("patient_id", "string", required=True),
        ParamSpec("hint_source", "string", required=True),
        ParamSpec("photo_ref", "string", required=False),
    ),
    writes=("MedClassHint",),
    validate_supported=True,
)
def 采集用药线索(ctx) -> None:
    """患者自报或药盒照片，仅供规则开闸，与 meds 严格分离

    写入对象：MedClassHint。
    """
    # TODO(FDE): 业务回写。逐个 writes 对象补 stage_write，key 命名由 FDE 定：
    # ctx.stage_write("MedClassHint", f"medclasshint_{ctx.params[...]}", {...})
    # ctx.emit_effect("workitem", on="...", template="...")   # 如需派工单
    ctx.set_confidence(0.8)
    # ctx.add_evidence(source="...")                            # 取自命中规则的 source
    raise NotImplementedError("采集用药线索 handler 待实现")

@spi.action(
    ONTOLOGY, "入组判定",
    description="根据体检与化验结果给出入组决定、服务包选择、缓解路径适宜性与人群目标区间",
    params=(
        ParamSpec("patient_id", "string", required=True),
        ParamSpec("exam_results", "object", required=True),
    ),
    guards=("C18_非医疗机构不得实施诊疗", "R28_老年目标切换", "R31_妊娠模式切换"),
    post_rules=("R30_缓解适宜人群筛选_ABCD", "R37_疑似1型LADA红旗"),
    writes=("EnrollmentDecision", "PatientProfile"),
    validate_supported=True,
    hil=HilPolicy(reviewer_role="医师",
                  predicate=lambda confidence, touched_hard: True),
)
def 入组判定(ctx) -> None:
    """医师判定是否入组、选包、缓解路径适宜性、人群目标区间

    HIL：医师（触发条件 always）。
    写入对象：EnrollmentDecision、PatientProfile。
    """
    # TODO(FDE): 业务回写。逐个 writes 对象补 stage_write，key 命名由 FDE 定：
    # ctx.stage_write("EnrollmentDecision", f"enrollmentdecision_{ctx.params[...]}", {...})
    # ctx.stage_write("PatientProfile", f"patientprofile_{ctx.params[...]}", {...})
    # ctx.emit_effect("workitem", on="...", template="...")   # 如需派工单
    ctx.set_confidence(0.8)
    # ctx.add_evidence(source="...")                            # 取自命中规则的 source
    raise NotImplementedError("入组判定 handler 待实现")

@spi.action(
    ONTOLOGY, "记录到店随机指血分诊",
    description="记录患者到店时的随机指血值并生成分诊记录",
    params=(
        ParamSpec("patient_id", "string", required=True),
        ParamSpec("glucose_value", "number", required=True),
    ),
    guards=("C18_非医疗机构不得实施诊疗", "R41_器械交易主体与收货合规"),
    writes=("OnsiteTriageRecord", "GlucoseReading"),
    validate_supported=True,
    hil=HilPolicy(reviewer_role="护士/前台",
                  predicate=lambda confidence, touched_hard: True),
)
def 记录到店随机指血分诊(ctx) -> None:
    """到店 5 分钟内前置串行，危急值命中即阻断商业流程

    HIL：护士/前台（触发条件 always）。
    写入对象：OnsiteTriageRecord、GlucoseReading。
    """
    # TODO(FDE): 业务回写。逐个 writes 对象补 stage_write，key 命名由 FDE 定：
    # ctx.stage_write("OnsiteTriageRecord", f"onsitetriagerecord_{ctx.params[...]}", {...})
    # ctx.stage_write("GlucoseReading", f"glucosereading_{ctx.params[...]}", {...})
    # ctx.emit_effect("workitem", on="...", template="...")   # 如需派工单
    ctx.set_confidence(0.8)
    # ctx.add_evidence(source="...")                            # 取自命中规则的 source
    raise NotImplementedError("记录到店随机指血分诊 handler 待实现")

@spi.action(
    ONTOLOGY, "建立传感器会话",
    description="为患者绑定一枚传感器（序号、厂商、型号、佩戴时间），按型号取预热参数建立佩戴会话",
    params=(
        ParamSpec("patient_id", "string", required=True),
        ParamSpec("sensor_serial", "string", required=True),
        ParamSpec("vendor", "string", required=True),
        ParamSpec("model", "string", required=True),
        ParamSpec("placement_time", "string", required=True),
    ),
    guards=("C3_敏感个人信息单独同意", "R38_告警兜底配置未完成禁止佩戴", "R41_器械交易主体与收货合规"),
    writes=("SensorSession",),
    validate_supported=True,
)
def 建立传感器会话(ctx) -> None:
    """绑定传感器序号并按型号取预热参数

    写入对象：SensorSession。
    """
    # TODO(FDE): 业务回写。逐个 writes 对象补 stage_write，key 命名由 FDE 定：
    # ctx.stage_write("SensorSession", f"sensorsession_{ctx.params[...]}", {...})
    # ctx.emit_effect("workitem", on="...", template="...")   # 如需派工单
    ctx.set_confidence(0.8)
    # ctx.add_evidence(source="...")                            # 取自命中规则的 source
    raise NotImplementedError("建立传感器会话 handler 待实现")

@spi.action(
    ONTOLOGY, "记录时间基线",
    description="记录患者手机时区与设备时钟偏移，作为后续读数时间校正的基线",
    params=(
        ParamSpec("patient_id", "string", required=True),
        ParamSpec("phone_tz", "string", required=True),
        ParamSpec("clock_offset", "number", required=False),
    ),
    writes=("PatientTimeBaseline",),
    validate_supported=True,
)
def 记录时间基线(ctx) -> None:
    """入组现场唯一采集时机，漏了不可补

    写入对象：PatientTimeBaseline。
    """
    # TODO(FDE): 业务回写。逐个 writes 对象补 stage_write，key 命名由 FDE 定：
    # ctx.stage_write("PatientTimeBaseline", f"patienttimebaseline_{ctx.params[...]}", {...})
    # ctx.emit_effect("workitem", on="...", template="...")   # 如需派工单
    ctx.set_confidence(0.8)
    # ctx.add_evidence(source="...")                            # 取自命中规则的 source
    raise NotImplementedError("记录时间基线 handler 待实现")

@spi.action(
    ONTOLOGY, "建立同步计划",
    description="为患者设置数据同步方式（触发类型、预期间隔、协助人）",
    params=(
        ParamSpec("patient_id", "string", required=True),
        ParamSpec("trigger_type", "string", required=True),
        ParamSpec("expected_interval", "number", required=False),
        ParamSpec("assist_person", "string", required=False),
    ),
    guards=("R40_老年画像禁止仅靠自觉同步",),
    writes=("SyncPlan",),
    validate_supported=True,
)
def 建立同步计划(ctx) -> None:
    """按画像分配同步触发方式，决定一期数据完整性

    写入对象：SyncPlan。
    """
    # TODO(FDE): 业务回写。逐个 writes 对象补 stage_write，key 命名由 FDE 定：
    # ctx.stage_write("SyncPlan", f"syncplan_{ctx.params[...]}", {...})
    # ctx.emit_effect("workitem", on="...", template="...")   # 如需派工单
    ctx.set_confidence(0.8)
    # ctx.add_evidence(source="...")                            # 取自命中规则的 source
    raise NotImplementedError("建立同步计划 handler 待实现")

@spi.action(
    ONTOLOGY, "验证通道连通性",
    description="端到端验证某条数据通道是否已有读数落库，并登记载体信息",
    params=(
        ParamSpec("patient_id", "string", required=True),
        ParamSpec("channel", "string", required=True),
    ),
    post_rules=("R43_落库验证未通过禁止入组成功",),
    writes=("EnrollmentDecision", "CarrierRegistry"),
    validate_supported=True,
    hil=HilPolicy(reviewer_role="健管师现场核验",
                  predicate=lambda confidence, touched_hard: True),
)
def 验证通道连通性(ctx) -> None:
    """离店前端到端验证至少一条读数落库

    HIL：健管师现场核验（触发条件 always）。
    写入对象：EnrollmentDecision、CarrierRegistry。
    """
    # TODO(FDE): 业务回写。逐个 writes 对象补 stage_write，key 命名由 FDE 定：
    # ctx.stage_write("EnrollmentDecision", f"enrollmentdecision_{ctx.params[...]}", {...})
    # ctx.stage_write("CarrierRegistry", f"carrierregistry_{ctx.params[...]}", {...})
    # ctx.emit_effect("workitem", on="...", template="...")   # 如需派工单
    ctx.set_confidence(0.8)
    # ctx.add_evidence(source="...")                            # 取自命中规则的 source
    raise NotImplementedError("验证通道连通性 handler 待实现")

@spi.action(
    ONTOLOGY, "覆盖状态告知",
    description="记录向患者告知当前服务覆盖状态（如夜间无实时干预）的留痕",
    params=(
        ParamSpec("patient_id", "string", required=True),
        ParamSpec("coverage_state", "string", required=True),
    ),
    guards=("R54_服务话术不得含夜间安全承诺",),
    post_rules=("R39_覆盖告知未留痕禁止入组成功",),
    writes=("EnrollmentDecision",),
    validate_supported=True,
    hil=HilPolicy(reviewer_role="健管师",
                  predicate=lambda confidence, touched_hard: True),
)
def 覆盖状态告知(ctx) -> None:
    """当面告知一期无当夜干预能力并签署留痕

    HIL：健管师（触发条件 always）。
    写入对象：EnrollmentDecision。
    """
    # TODO(FDE): 业务回写。逐个 writes 对象补 stage_write，key 命名由 FDE 定：
    # ctx.stage_write("EnrollmentDecision", f"enrollmentdecision_{ctx.params[...]}", {...})
    # ctx.emit_effect("workitem", on="...", template="...")   # 如需派工单
    ctx.set_confidence(0.8)
    # ctx.add_evidence(source="...")                            # 取自命中规则的 source
    raise NotImplementedError("覆盖状态告知 handler 待实现")

@spi.action(
    ONTOLOGY, "标记入组成功",
    description="把患者标记为入组成功并启动服务包计时",
    params=(
        ParamSpec("patient_id", "string", required=True),
    ),
    guards=("R39_覆盖告知未留痕禁止入组成功", "R43_落库验证未通过禁止入组成功", "C3_敏感个人信息单独同意"),
    writes=("EnrollmentDecision", "ServicePackage"),
    validate_supported=True,
)
def 标记入组成功(ctx) -> None:
    """通过全部离店硬闸后才启动服务包计时

    写入对象：EnrollmentDecision、ServicePackage。
    """
    # TODO(FDE): 业务回写。逐个 writes 对象补 stage_write，key 命名由 FDE 定：
    # ctx.stage_write("EnrollmentDecision", f"enrollmentdecision_{ctx.params[...]}", {...})
    # ctx.stage_write("ServicePackage", f"servicepackage_{ctx.params[...]}", {...})
    # ctx.emit_effect("workitem", on="...", template="...")   # 如需派工单
    ctx.set_confidence(0.8)
    # ctx.add_evidence(source="...")                            # 取自命中规则的 source
    raise NotImplementedError("标记入组成功 handler 待实现")

@spi.action(
    ONTOLOGY, "摄入读数",
    description="从指定通道摄入一批原始血糖读数（含患者、读数列表），写入 GlucoseReading 与 IngestBatch",
    params=(
        ParamSpec("channel", "string", required=True),
        ParamSpec("raw_payload", "object", required=True),
    ),
    guards=("C3_敏感个人信息单独同意", "R48_去重键必须用传感器序号"),
    post_rules=("C21_数据留存与审计日志",),
    writes=("GlucoseReading", "IngestBatch"),
    validate_supported=True,
)
def 摄入读数(ctx) -> None:
    """多通道摄入，单位与时间完整性硬校验

    写入对象：GlucoseReading、IngestBatch。
    """
    _fde.ACTIONS['摄入读数'](ctx)

@spi.action(
    ONTOLOGY, "去重与通道仲裁",
    description="对一条候选读数按传感器序号去重，并在多通道间仲裁取舍",
    params=(
        ParamSpec("reading_candidate", "object", required=True),
    ),
    guards=("R48_去重键必须用传感器序号",),
    post_rules=("R36_active率超100自检", "R02_传感器压迫伪差识别"),
    writes=("GlucoseReading",),
    validate_supported=True,
)
def 去重与通道仲裁(ctx) -> None:
    """按传感器序号去重，多路自动仲裁

    写入对象：GlucoseReading。
    """
    _fde.ACTIONS['去重与通道仲裁'](ctx)

@spi.action(
    ONTOLOGY, "OCR读数复核",
    description="对一条 OCR 识别出的读数做人工复核决定（确认 / 否决并重录）",
    params=(
        ParamSpec("reading_id", "string", required=True),
        ParamSpec("decision", "string", required=True),
    ),
    writes=("GlucoseReading",),
    validate_supported=True,
    hil=HilPolicy(reviewer_role="健管师",
                  predicate=lambda confidence, touched_hard: True),
)
def OCR读数复核(ctx) -> None:
    """健管师按决策影响分诊复核，否决走 retract + 新增

    HIL：健管师（触发条件 always）。
    写入对象：GlucoseReading。
    """
    # TODO(FDE): 业务回写。逐个 writes 对象补 stage_write，key 命名由 FDE 定：
    # ctx.stage_write("GlucoseReading", f"glucosereading_{ctx.params[...]}", {...})
    # ctx.emit_effect("workitem", on="...", template="...")   # 如需派工单
    ctx.set_confidence(0.8)
    # ctx.add_evidence(source="...")                            # 取自命中规则的 source
    raise NotImplementedError("OCR读数复核 handler 待实现")

@spi.action(
    ONTOLOGY, "计算窗口指标",
    description="按时间窗计算患者的全套 CGM 派生指标（TIR/TBR/TAR/CV/GMI、有效率、夜间覆盖）并写入 CgmSummary",
    params=(
        ParamSpec("patient_id", "string", required=True),
        ParamSpec("window", "string", required=True),
    ),
    guards=("R28_老年目标切换", "R31_妊娠模式切换", "R49_缺参数时按最保守执行", "R47_跨品牌配对排除"),
    post_rules=("R36_active率超100自检",),
    writes=("CgmSummary",),
    validate_supported=True,
)
def 计算窗口指标(ctx) -> None:
    """计算全套派生量并落 CgmSummary

    写入对象：CgmSummary。
    """
    # TODO(FDE): 业务回写。逐个 writes 对象补 stage_write，key 命名由 FDE 定：
    # ctx.stage_write("CgmSummary", f"cgmsummary_{ctx.params[...]}", {...})
    # ctx.emit_effect("workitem", on="...", template="...")   # 如需派工单
    ctx.set_confidence(0.8)
    # ctx.add_evidence(source="...")                            # 取自命中规则的 source
    raise NotImplementedError("计算窗口指标 handler 待实现")

@spi.action(
    ONTOLOGY, "生成AGP与指标报告",
    description="按窗口生成患者的 AGP 图与指标报告内容",
    params=(
        ParamSpec("patient_id", "string", required=True),
        ParamSpec("window", "string", required=True),
    ),
    guards=("R01_数据充分性门槛_仅管结论层", "R28_老年目标切换"),
    post_rules=(
        "低血糖优先抢占",
        "R09_TBR超标触发去强化审查",
        "R13_TAR_L2超标",
        "R15_TIR未达标",
        "R16a_波动超标_硬",
        "R16b_波动偏高_软_中国口径",
        "R17_GMI与HbA1c不一致",
        "R35_夜间覆盖不足禁强化",
        "R55_显示口径_没有数据不得说成没有异常",
        "R03b_Level2低血糖_回顾事件统计",
        "R04b_Level1低血糖_回顾事件统计",
        "R47_跨品牌配对排除",
    ),
    writes=("CgmSummary", "OutboundContent"),
    validate_supported=True,
)
def 生成AGP与指标报告(ctx) -> None:
    """按先低→再高→再波动顺序组织报告

    写入对象：CgmSummary、OutboundContent。
    """
    # TODO(FDE): 业务回写。逐个 writes 对象补 stage_write，key 命名由 FDE 定：
    # ctx.stage_write("CgmSummary", f"cgmsummary_{ctx.params[...]}", {...})
    # ctx.stage_write("OutboundContent", f"outboundcontent_{ctx.params[...]}", {...})
    # ctx.emit_effect("workitem", on="...", template="...")   # 如需派工单
    ctx.set_confidence(0.8)
    # ctx.add_evidence(source="...")                            # 取自命中规则的 source
    raise NotImplementedError("生成AGP与指标报告 handler 待实现")

@spi.action(
    ONTOLOGY, "记录餐食与运动事件",
    description="记录患者的一次餐食 / 运动 / 睡眠等情境事件及发生时间",
    params=(
        ParamSpec("patient_id", "string", required=True),
        ParamSpec("event_type", "string", required=True),
        ParamSpec("occurred_at", "string", required=True),
    ),
    post_rules=(
        "R23_运动前低值",
        "R24a_运动前高值查酮体",
        "R24b_运动前极高值一律不宜运动",
        "R25_运动中下降",
        "R26_餐后步行提醒",
        "R27_运动后延迟低血糖",
    ),
    writes=("ContextEvent",),
    validate_supported=True,
)
def 记录餐食与运动事件(ctx) -> None:
    """患者或家属打卡，AI 可从群聊抽取

    写入对象：ContextEvent。
    """
    # TODO(FDE): 业务回写。逐个 writes 对象补 stage_write，key 命名由 FDE 定：
    # ctx.stage_write("ContextEvent", f"contextevent_{ctx.params[...]}", {...})
    # ctx.emit_effect("workitem", on="...", template="...")   # 如需派工单
    ctx.set_confidence(0.8)
    # ctx.add_evidence(source="...")                            # 取自命中规则的 source
    raise NotImplementedError("记录餐食与运动事件 handler 待实现")

@spi.action(
    ONTOLOGY, "记录症状与处置",
    description="记录患者一次低血糖相关症状标签及对应处置动作",
    params=(
        ParamSpec("patient_id", "string", required=True),
        ParamSpec("symptom_tag", "string", required=False),
        ParamSpec("treatment_action", "string", required=False),
    ),
    post_rules=(
        "R58_Level3严重低血糖强制转诊",
        "R59_老年非典型症状疑似低血糖",
    ),
    writes=("SymptomTreatmentRecord",),
    validate_supported=True,
)
def 记录症状与处置(ctx) -> None:
    """告警卡片内一键回填，R10 的唯一输入

    写入对象：SymptomTreatmentRecord。
    """
    # TODO(FDE): 业务回写。逐个 writes 对象补 stage_write，key 命名由 FDE 定：
    # ctx.stage_write("SymptomTreatmentRecord", f"symptomtreatmentrecord_{ctx.params[...]}", {...})
    # ctx.emit_effect("workitem", on="...", template="...")   # 如需派工单
    ctx.set_confidence(0.8)
    # ctx.add_evidence(source="...")                            # 取自命中规则的 source
    raise NotImplementedError("记录症状与处置 handler 待实现")

@spi.action(
    ONTOLOGY, "记录酮体",
    description="记录患者一次酮体检测结果（数值或定性）与检测方法",
    params=(
        ParamSpec("patient_id", "string", required=True),
        ParamSpec("value_or_qualitative", "string", required=True),
        ParamSpec("method", "string", required=False),
    ),
    writes=("KetoneReading",),
    validate_supported=True,
)
def 记录酮体(ctx) -> None:
    """R11/R12/R24 的阳性分支唯一输入

    写入对象：KetoneReading。
    """
    # TODO(FDE): 业务回写。逐个 writes 对象补 stage_write，key 命名由 FDE 定：
    # ctx.stage_write("KetoneReading", f"ketonereading_{ctx.params[...]}", {...})
    # ctx.emit_effect("workitem", on="...", template="...")   # 如需派工单
    ctx.set_confidence(0.8)
    # ctx.add_evidence(source="...")                            # 取自命中规则的 source
    raise NotImplementedError("记录酮体 handler 待实现")

@spi.action(
    ONTOLOGY, "记录临床混杂事件",
    description="记录患者的急性病、激素使用、住院、调药期等临床混杂事件及起止时间",
    params=(
        ParamSpec("patient_id", "string", required=True),
        ParamSpec("type", "string", required=True),
        ParamSpec("start_at", "string", required=True),
    ),
    post_rules=("R42_急性混杂窗口禁止出结论",),
    writes=("ClinicalContextEvent",),
    validate_supported=True,
    hil=HilPolicy(reviewer_role="医师/护士",
                  predicate=lambda confidence, touched_hard: True),
)
def 记录临床混杂事件(ctx) -> None:
    """医师或护士录入急性病、激素、住院、调药期

    HIL：医师/护士（触发条件 always）。
    写入对象：ClinicalContextEvent。
    """
    # TODO(FDE): 业务回写。逐个 writes 对象补 stage_write，key 命名由 FDE 定：
    # ctx.stage_write("ClinicalContextEvent", f"clinicalcontextevent_{ctx.params[...]}", {...})
    # ctx.emit_effect("workitem", on="...", template="...")   # 如需派工单
    ctx.set_confidence(0.8)
    # ctx.add_evidence(source="...")                            # 取自命中规则的 source
    raise NotImplementedError("记录临床混杂事件 handler 待实现")

@spi.action(
    ONTOLOGY, "计算餐后响应",
    description="对一次餐食事件配对前后读数，计算餐后血糖响应（PPGR）指标",
    params=(
        ParamSpec("patient_id", "string", required=True),
        ParamSpec("meal_event_id", "string", required=True),
    ),
    guards=("R21_餐次数据混叠排除", "R47_跨品牌配对排除"),
    post_rules=("R19_餐后高响应", "R20_餐后极高响应"),
    writes=("MealResponse",),
    validate_supported=True,
)
def 计算餐后响应(ctx) -> None:
    """配对窗计算 PPGR 五项

    写入对象：MealResponse。
    """
    # TODO(FDE): 业务回写。逐个 writes 对象补 stage_write，key 命名由 FDE 定：
    # ctx.stage_write("MealResponse", f"mealresponse_{ctx.params[...]}", {...})
    # ctx.emit_effect("workitem", on="...", template="...")   # 如需派工单
    ctx.set_confidence(0.8)
    # ctx.add_evidence(source="...")                            # 取自命中规则的 source
    raise NotImplementedError("计算餐后响应 handler 待实现")

@spi.action(
    ONTOLOGY, "输出服务分层标签",
    description="按窗口指标为患者计算内部服务分层标签（L0–L4）并写入画像",
    params=(
        ParamSpec("patient_id", "string", required=True),
        ParamSpec("window", "string", required=True),
    ),
    guards=("R01_数据充分性门槛_仅管结论层", "R31_妊娠模式切换", "R51_分层结论默认不可披露患者"),
    post_rules=(
        "R18_CGM服务分层_内部标签",
        "R42_急性混杂窗口禁止出结论",
        "D11_未确认分型分级措辞拦截",
        "C11_分型输出制度层不得当诊断",
        "低血糖优先抢占",
    ),
    writes=("PatientProfile",),
    validate_supported=True,
    hil=HilPolicy(reviewer_role="医师（披露授权）",
                  predicate=lambda confidence, touched_hard: True),
)
def 输出服务分层标签(ctx) -> None:
    """内部服务分层，默认不可披露患者

    HIL：医师（披露授权）（触发条件 always）。
    写入对象：PatientProfile。
    """
    _fde.ACTIONS['输出服务分层标签'](ctx)

@spi.action(
    ONTOLOGY, "触发低血糖处置",
    description="基于一条读数与命中的规则生成低血糖告警事件与事件记录",
    params=(
        ParamSpec("patient_id", "string", required=True),
        ParamSpec("reading_id", "string", required=True),
        ParamSpec("rule_id", "string", required=True),
    ),
    guards=("R53_低置信通道不得独立触发危急告警", "R52_回填读数不得触发实时告警"),
    post_rules=("R03a_Level2低血糖_实时告警", "R04a_Level1低血糖_实时告警", "R05_即将低血糖预测告警", "R11_严重高血糖"),
    writes=("AlertEvent", "HypoEpisode"),
    validate_supported=True,
)
def 触发低血糖处置(ctx) -> None:
    """一期写事件进次日队列，二期走实时推送

    写入对象：AlertEvent、HypoEpisode。
    """
    _fde.ACTIONS['触发低血糖处置'](ctx)

@spi.action(
    ONTOLOGY, "统计低血糖事件",
    description="按窗口回顾统计患者的低血糖事件（≥15 分钟口径），写入 HypoEpisode",
    params=(
        ParamSpec("patient_id", "string", required=True),
        ParamSpec("window", "string", required=True),
    ),
    post_rules=("R03b_Level2低血糖_回顾事件统计", "R04b_Level1低血糖_回顾事件统计", "R07_夜间低血糖事件", "R02_传感器压迫伪差识别"),
    writes=("HypoEpisode",),
    validate_supported=True,
)
def 统计低血糖事件(ctx) -> None:
    """Danne ≥15 分钟口径的回顾统计，一期核心安全产出

    写入对象：HypoEpisode。
    """
    # TODO(FDE): 业务回写。逐个 writes 对象补 stage_write，key 命名由 FDE 定：
    # ctx.stage_write("HypoEpisode", f"hypoepisode_{ctx.params[...]}", {...})
    # ctx.emit_effect("workitem", on="...", template="...")   # 如需派工单
    ctx.set_confidence(0.8)
    # ctx.add_evidence(source="...")                            # 取自命中规则的 source
    raise NotImplementedError("统计低血糖事件 handler 待实现")

@spi.action(
    ONTOLOGY, "更新低血糖状态机",
    description="根据新事件更新患者的低血糖状态（延长风险、复发观察窗）",
    params=(
        ParamSpec("patient_id", "string", required=True),
        ParamSpec("event", "string", required=True),
    ),
    post_rules=("R34_HAAF_24小时复发窗",),
    writes=("HypoState",),
    validate_supported=True,
)
def 更新低血糖状态机(ctx) -> None:
    """置延长风险与复发窗，closure_blocked_reason 无人可写

    写入对象：HypoState。
    """
    # TODO(FDE): 业务回写。逐个 writes 对象补 stage_write，key 命名由 FDE 定：
    # ctx.stage_write("HypoState", f"hypostate_{ctx.params[...]}", {...})
    # ctx.emit_effect("workitem", on="...", template="...")   # 如需派工单
    ctx.set_confidence(0.8)
    # ctx.add_evidence(source="...")                            # 取自命中规则的 source
    raise NotImplementedError("更新低血糖状态机 handler 待实现")

@spi.action(
    ONTOLOGY, "推送告警",
    description="把一条告警事件按级别推送给指定对象，生成投递回执",
    params=(
        ParamSpec("alert_id", "string", required=True),
        ParamSpec("level", "string", required=True),
        ParamSpec("targets", "list", required=True),
    ),
    guards=(
        "R45_紧急告警豁免关键词闸",
        "R56_告警模板预审冻结",
        "R52_回填读数不得触发实时告警",
        "R53_低置信通道不得独立触发危急告警",
        "R06_快速下降箭头提示",
        "R08_睡前低值预警",
        "R20_餐后极高响应",
        "R23_运动前低值",
        "R24a_运动前高值查酮体",
        "R24b_运动前极高值一律不宜运动",
        "R25_运动中下降",
        "R26_餐后步行提醒",
        "R12_SGLT2i酮症警觉",
        "R49_缺参数时按最保守执行",
    ),
    post_rules=(
        "C20_危急值须系统自动告警并记录响应",
        "R54_服务话术不得含夜间安全承诺",
        "C22_免责声明强制展示",
        "R57_15-15三轮无效强制升级就医",
        "R58_Level3严重低血糖强制转诊",
    ),
    writes=("AlertEvent", "DeliveryReceipt"),
    validate_supported=True,
)
def 推送告警(ctx) -> None:
    """分级推送，紧急告警只套用已预审冻结的模板

    写入对象：AlertEvent、DeliveryReceipt。
    """
    _fde.ACTIONS['推送告警'](ctx)

@spi.action(
    ONTOLOGY, "响应并回执告警",
    description="记录对一条告警的响应：响应人、所做处置、复测值，生成回执",
    params=(
        ParamSpec("alert_id", "string", required=True),
        ParamSpec("responder", "string", required=True),
        ParamSpec("action_taken", "string", required=True),
        ParamSpec("retest_value", "number", required=False),
    ),
    guards=("R44_高危用药禁止闭环", "C21_数据留存与审计日志"),
    post_rules=(
        "C20_危急值须系统自动告警并记录响应",
        "R57_15-15三轮无效强制升级就医",
    ),
    writes=("AlertAck",),
    validate_supported=True,
    hil=HilPolicy(reviewer_role="健管师/值班医师",
                  predicate=lambda confidence, touched_hard: True),
)
def 响应并回执告警(ctx) -> None:
    """健管师或值班医师回执，高危用药不得直接闭环

    HIL：健管师/值班医师（触发条件 always）。
    写入对象：AlertAck。
    """
    _fde.ACTIONS['响应并回执告警'](ctx)

@spi.action(
    ONTOLOGY, "升级告警",
    description="把一条告警升级到更高级别的值班责任人",
    params=(
        ParamSpec("alert_id", "string", required=True),
        ParamSpec("level", "number", required=True),
    ),
    guards=("R53_低置信通道不得独立触发危急告警",),  # P18a：R38 是建立传感器会话的入组规则，误挂；升级到危急级该看来源通道置信（R53）
    writes=("AlertEscalation",),
    validate_supported=True,
    hil=HilPolicy(reviewer_role="值班医师",
                  predicate=lambda confidence, touched_hard: True),
)
def 升级告警(ctx) -> None:
    """逐级升级至值班责任人（phase=P2）

    HIL：值班医师（触发条件 always）。
    写入对象：AlertEscalation。
    """
    _fde.ACTIONS['升级告警'](ctx)

@spi.action(
    ONTOLOGY, "撤销更正已发出告警",
    description="撤销一条已发出的告警并发出更正说明",
    params=(
        ParamSpec("alert_id", "string", required=True),
        ParamSpec("reason", "string", required=True),
    ),
    writes=("AlertEvent", "PlanSigned"),
    validate_supported=True,
    hil=HilPolicy(reviewer_role="触及已签发方案时转签发人",
                  predicate=lambda confidence, touched_hard: touched_hard),
)
def 撤销更正已发出告警(ctx) -> None:
    """上游读数被 retract 或 corrected 时撤销并发更正说明

    HIL：触及已签发方案时转签发人（触发条件 touched_hard）。
    写入对象：AlertEvent、PlanSigned。
    """
    # TODO(FDE): 业务回写。逐个 writes 对象补 stage_write，key 命名由 FDE 定：
    # ctx.stage_write("AlertEvent", f"alertevent_{ctx.params[...]}", {...})
    # ctx.stage_write("PlanSigned", f"plansigned_{ctx.params[...]}", {...})
    # ctx.emit_effect("workitem", on="...", template="...")   # 如需派工单
    ctx.set_confidence(0.8)
    # ctx.add_evidence(source="...")                            # 取自命中规则的 source
    raise NotImplementedError("撤销更正已发出告警 handler 待实现")

@spi.action(
    ONTOLOGY, "放宽告警阈值",
    description="把患者某项告警阈值改到更不容易报警的值（低值类阈值下调、高值类阈值上调）",
    params=(
        ParamSpec("patient_id", "string", required=True),
        ParamSpec("field", "string", required=True),
        ParamSpec("new_value", "number", required=True),
    ),
    guards=("D11a_签发人资质失效自动冻结", "R46_IAH高危阈值上调且禁止静音"),
    writes=("AlertThreshold", "ThresholdChangeLog"),
    validate_supported=True,
    hil=HilPolicy(reviewer_role="医师（唯一可放宽）",
                  predicate=lambda confidence, touched_hard: True),
)
def 放宽告警阈值(ctx) -> None:
    """仅医师可放宽——收紧可自动、放宽仅医师

    HIL：医师（唯一可放宽）（触发条件 always）。
    写入对象：AlertThreshold、ThresholdChangeLog。
    """
    _fde.ACTIONS['放宽告警阈值'](ctx)

@spi.action(
    ONTOLOGY, "收紧告警阈值",
    description="把患者某项告警阈值改到更早报警的值（低值类阈值上调，如夜间低值 3.9→4.4；高值类阈值下调），记录触发来源与前后值",
    params=(
        ParamSpec("patient_id", "string", required=True),
        ParamSpec("field", "string", required=True),
        ParamSpec("trigger_rule", "string", required=True),
        ParamSpec("new_value", "number", required=False),
    ),
    # P34a（W53 / 0705）：R46 约束的是 IAH 高危患者「低值阈值 ≥4.4」这个**结果**，与改阈值走哪个动作无关；只挂在 放宽 / 配置 上，
    #   收紧 动作把低值线写成 4.3（低于 4.4）就绕过了它。收紧 是自动通道（不经医师），更需要这道前置。
    guards=("R46_IAH高危阈值上调且禁止静音",),
    post_rules=("R27_运动后延迟低血糖", "R34_HAAF_24小时复发窗"),
    writes=("AlertThreshold", "ThresholdChangeLog"),
    validate_supported=True,
)
def 收紧告警阈值(ctx) -> None:
    """由确定性规则自动触发，记录并通知医师

    写入对象：AlertThreshold、ThresholdChangeLog。
    """
    _fde.ACTIONS['收紧告警阈值'](ctx)

@spi.action(
    ONTOLOGY, "配置患者告警与静音策略",
    description="按患者人群属性设置告警阈值与夜间静音策略",
    params=(
        ParamSpec("patient_id", "string", required=True),
        ParamSpec("is_iah_high_risk", "boolean", required=False),
        ParamSpec("night_mute_allowed", "boolean", required=False),
    ),
    guards=("R46_IAH高危阈值上调且禁止静音",),
    post_rules=("R10_低血糖无感知线索",),
    writes=("AlertThreshold",),
    validate_supported=True,
    hil=HilPolicy(reviewer_role="医师",
                  predicate=lambda confidence, touched_hard: True),
)
def 配置患者告警与静音策略(ctx) -> None:
    """按人群维度设阈值与静音策略

    HIL：医师（触发条件 always）。
    写入对象：AlertThreshold。
    """
    # TODO(FDE): 业务回写。逐个 writes 对象补 stage_write，key 命名由 FDE 定：
    # ctx.stage_write("AlertThreshold", f"alertthreshold_{ctx.params[...]}", {...})
    # ctx.emit_effect("workitem", on="...", template="...")   # 如需派工单
    ctx.set_confidence(0.8)
    # ctx.add_evidence(source="...")                            # 取自命中规则的 source
    raise NotImplementedError("配置患者告警与静音策略 handler 待实现")

@spi.action(
    ONTOLOGY, "生成方案草稿",
    description="根据患者分析结果生成一份本期健康管理方案草稿（可指定方向：强化 / 维持 / 去强化），写入 PlanDraft 待签发",
    params=(
        ParamSpec("patient_id", "string", required=True),
        ParamSpec("analysis_result", "object", required=True),
        ParamSpec("direction", "string", required=False),
    ),
    guards=("R35_夜间覆盖不足禁强化", "R42_急性混杂窗口禁止出结论", "R37_疑似1型LADA红旗", "R49_缺参数时按最保守执行"),
    post_rules=(
        "低血糖优先抢占",
        "D10_用药建议拦截",
        "R08_睡前低值预警",
        "R11_严重高血糖",
        "R13_TAR_L2超标",
        "R14_TAR_L1超标",
        "R15_TIR未达标",
        "R16a_波动超标_硬",
        "R16b_波动偏高_软_中国口径",
        "R19_餐后高响应",
        "R22_黎明现象",
        "R27_运动后延迟低血糖",
    ),
    writes=("PlanDraft",),
    validate_supported=True,
)
def 生成方案草稿(ctx) -> None:
    """AI 只出草稿，不含用药加减停、不含产品映射、不含分型结论

    写入对象：PlanDraft。
    """
    _fde.ACTIONS['生成方案草稿'](ctx)

@spi.action(
    ONTOLOGY, "审核输出内容",
    description="对一条待发出的内容做合规审核，记录命中项并在通过时签发 gate_token",
    params=(
        ParamSpec("content_id", "string", required=True),
        ParamSpec("content_type", "string", required=True),
    ),
    guards=("R45_紧急告警豁免关键词闸",),
    post_rules=(
        "D8_禁用词拦截",
        "D9_产品功效声称拦截",
        "D10_用药建议拦截",
        "D11_未确认分型分级措辞拦截",
        "R32_产品推荐合规闸",
        "C22_免责声明强制展示",
        "R54_服务话术不得含夜间安全承诺",
    ),
    writes=("ComplianceCheckLog", "GateToken", "OutboundContent"),
    validate_supported=True,
    hil=HilPolicy(reviewer_role="合规官（红线复核）+ 营养师/医师（2 次未过转人工改写）",
                  predicate=lambda confidence, touched_hard: True),
)
def 审核输出内容(ctx) -> None:
    """出口合规闸四道判定，通过才签发 gate_token

    HIL：合规官（红线复核）+ 营养师/医师（2 次未过转人工改写）（触发条件 always）。
    写入对象：ComplianceCheckLog、GateToken、OutboundContent。
    """
    _fde.ACTIONS['审核输出内容'](ctx)

@spi.action(
    ONTOLOGY, "签发方案",
    description="由签发人对一份方案草稿作出签发决定，生成已签发方案与审阅证据",
    params=(
        ParamSpec("draft_id", "string", required=True),
        ParamSpec("signer_id", "string", required=True),
        ParamSpec("decision", "string", required=True),
    ),
    guards=("D11a_签发人资质失效自动冻结", "D12_签发人归属分流", "C21_数据留存与审计日志"),
    post_rules=("D13_签发反橡皮图章检测",),
    writes=("PlanSigned", "ReviewEvidence"),
    validate_supported=True,
    hil=HilPolicy(reviewer_role="医师/注册营养师/运动康复师",
                  predicate=lambda confidence, touched_hard: True),
)
def 签发方案(ctx) -> None:
    """医师或注册营养师签发，AI 与健管师绝对禁写

    HIL：医师/注册营养师/运动康复师（触发条件 always）。
    写入对象：PlanSigned、ReviewEvidence。
    """
    _fde.ACTIONS['签发方案'](ctx)

@spi.action(
    ONTOLOGY, "推送方案至患者",
    description="把一份已签发的方案推送给指定对象，生成投递回执",
    params=(
        ParamSpec("plan_id", "string", required=True),
        ParamSpec("targets", "list", required=True),
    ),
    guards=("C9_AI方案禁止直接推送", "R51_分层结论默认不可披露患者"),
    post_rules=("C6_群内数据最小可见范围", "C22_免责声明强制展示", "R55_显示口径_没有数据不得说成没有异常"),
    writes=("DeliveryReceipt", "OutboundContent"),
    validate_supported=True,
)
def 推送方案至患者(ctx) -> None:
    """已签发且过闸的内容才可推送

    写入对象：DeliveryReceipt、OutboundContent。
    """
    _fde.ACTIONS['推送方案至患者'](ctx)

@spi.action(
    ONTOLOGY, "标记方案证据过期",
    description="把一份已签发方案标记为依据过期，并生成签发人待办",
    params=(
        ParamSpec("plan_id", "string", required=True),
        ParamSpec("window", "string", required=True),
    ),
    writes=("PlanSigned",),
    validate_supported=True,
    hil=HilPolicy(reviewer_role="复核仍需签发人",
                  predicate=lambda confidence, touched_hard: touched_hard),
)
def 标记方案证据过期(ctx) -> None:
    """消费 metrics.invalidated，生成签发人待办

    HIL：复核仍需签发人（触发条件 touched_hard）。
    写入对象：PlanSigned。
    """
    # TODO(FDE): 业务回写。逐个 writes 对象补 stage_write，key 命名由 FDE 定：
    # ctx.stage_write("PlanSigned", f"plansigned_{ctx.params[...]}", {...})
    # ctx.emit_effect("workitem", on="...", template="...")   # 如需派工单
    ctx.set_confidence(0.8)
    # ctx.add_evidence(source="...")                            # 取自命中规则的 source
    raise NotImplementedError("标记方案证据过期 handler 待实现")

@spi.action(
    ONTOLOGY, "生成去强化证据工单",
    description="为患者生成一份转医师的去强化证据包（窗口指标、14 天曲线、用药清单、低血糖事件明细）并创建转介记录",
    params=(
        ParamSpec("patient_id", "string", required=True),
        ParamSpec("window", "string", required=True),
    ),
    post_rules=(
        "R09_TBR超标触发去强化审查",
        "R07_夜间低血糖事件",
        "R10_低血糖无感知线索",
        "R50_夜间低覆盖高危用药进临床队列",
        "R59_老年非典型症状疑似低血糖",
    ),
    writes=("ReferralRecord", "OutboundContent"),
    validate_supported=True,
    hil=HilPolicy(reviewer_role="医师接单",
                  predicate=lambda confidence, touched_hard: True),
)
def 生成去强化证据工单(ctx) -> None:
    """带 14 天曲线 + 用药清单 + 低血糖事件明细转医师

    HIL：医师接单（触发条件 always）。
    写入对象：ReferralRecord、OutboundContent。
    """
    _fde.ACTIONS['生成去强化证据工单'](ctx)

@spi.action(
    ONTOLOGY, "转介医师",
    description="把一个患者问题及上下文转介给医师，生成转介记录",
    params=(
        ParamSpec("patient_id", "string", required=True),
        ParamSpec("question_context", "string", required=True),
    ),
    guards=("D10_用药建议拦截",),
    post_rules=(
        "R22_黎明现象",
        "R33_停药观察期反弹预警",
        "R58_Level3严重低血糖强制转诊",
    ),
    writes=("ReferralRecord",),
    validate_supported=True,
    hil=HilPolicy(reviewer_role="医师",
                  predicate=lambda confidence, touched_hard: True),
)
def 转介医师(ctx) -> None:
    """用药类问题一律转医师，AI 与健管师不得答

    HIL：医师（触发条件 always）。
    写入对象：ReferralRecord。
    """
    _fde.ACTIONS['转介医师'](ctx)

@spi.action(
    ONTOLOGY, "评估可否停药并签发减停计划",
    description="基于证据包评估患者可否停药并签发减停计划",
    params=(
        ParamSpec("patient_id", "string", required=True),
        ParamSpec("evidence_pack", "object", required=True),
    ),
    guards=("D11a_签发人资质失效自动冻结", "R37_疑似1型LADA红旗", "R30_缓解适宜人群筛选_ABCD"),
    writes=("TaperPlan",),
    validate_supported=True,
    hil=HilPolicy(reviewer_role="医师（唯一，AI 绝对禁止建议）",
                  predicate=lambda confidence, touched_hard: True),
)
def 评估可否停药并签发减停计划(ctx) -> None:
    """仅医师，原文快照不可被智能体摘要改写

    HIL：医师（唯一，AI 绝对禁止建议）（触发条件 always）。
    写入对象：TaperPlan。
    """
    # TODO(FDE): 业务回写。逐个 writes 对象补 stage_write，key 命名由 FDE 定：
    # ctx.stage_write("TaperPlan", f"taperplan_{ctx.params[...]}", {...})
    # ctx.emit_effect("workitem", on="...", template="...")   # 如需派工单
    ctx.set_confidence(0.8)
    # ctx.add_evidence(source="...")                            # 取自命中规则的 source
    raise NotImplementedError("评估可否停药并签发减停计划 handler 待实现")

@spi.action(
    ONTOLOGY, "确认缓解时钟Day0",
    description="为患者确认缓解观察的 Day0 日期并启动缓解时钟",
    params=(
        ParamSpec("patient_id", "string", required=True),
        ParamSpec("day0", "string", required=True),
    ),
    writes=("RemissionClock",),
    validate_supported=True,
    hil=HilPolicy(reviewer_role="医师",
                  predicate=lambda confidence, touched_hard: True),
)
def 确认缓解时钟Day0(ctx) -> None:
    """医师另行确认，系统不得自动推断

    HIL：医师（触发条件 always）。
    写入对象：RemissionClock。
    """
    # TODO(FDE): 业务回写。逐个 writes 对象补 stage_write，key 命名由 FDE 定：
    # ctx.stage_write("RemissionClock", f"remissionclock_{ctx.params[...]}", {...})
    # ctx.emit_effect("workitem", on="...", template="...")   # 如需派工单
    ctx.set_confidence(0.8)
    # ctx.add_evidence(source="...")                            # 取自命中规则的 source
    raise NotImplementedError("确认缓解时钟Day0 handler 待实现")

@spi.action(
    ONTOLOGY, "判定缓解结果",
    description="根据停药时长、化验结果与窗口指标判定患者是否达到缓解，写入评估记录",
    params=(
        ParamSpec("patient_id", "string", required=True),
        ParamSpec("lab_result_id", "string", required=False),
        ParamSpec("summary_id", "string", required=False),
    ),
    guards=("R01_数据充分性门槛_仅管结论层", "D11a_签发人资质失效自动冻结"),
    post_rules=(
        "R29_缓解判定",
        "R17_GMI与HbA1c不一致",
        "R30_缓解适宜人群筛选_ABCD",
        "R33_停药观察期反弹预警",
        "R42_急性混杂窗口禁止出结论",
    ),
    writes=("RemissionAssessment",),
    validate_supported=True,
    hil=HilPolicy(reviewer_role="医师（面诊告知，唯一）",
                  predicate=lambda confidence, touched_hard: True),
)
def 判定缓解结果(ctx) -> None:
    """停药 ≥90 天 + HbA1c<6.5%（GMI 可替代但须过四条前提）

    HIL：医师（面诊告知，唯一）（触发条件 always）。
    写入对象：RemissionAssessment。
    """
    _fde.ACTIONS['判定缓解结果'](ctx)

@spi.action(
    ONTOLOGY, "决定复药",
    description="记录患者复药决定并重置缓解时钟",
    params=(
        ParamSpec("patient_id", "string", required=True),
        ParamSpec("evidence", "string", required=True),
    ),
    writes=("RemissionClock",),
    validate_supported=True,
    hil=HilPolicy(reviewer_role="医师",
                  predicate=lambda confidence, touched_hard: True),
)
def 决定复药(ctx) -> None:
    """复药即 remission_clock 清零

    HIL：医师（触发条件 always）。
    写入对象：RemissionClock。
    """
    # TODO(FDE): 业务回写。逐个 writes 对象补 stage_write，key 命名由 FDE 定：
    # ctx.stage_write("RemissionClock", f"remissionclock_{ctx.params[...]}", {...})
    # ctx.emit_effect("workitem", on="...", template="...")   # 如需派工单
    ctx.set_confidence(0.8)
    # ctx.add_evidence(source="...")                            # 取自命中规则的 source
    raise NotImplementedError("决定复药 handler 待实现")

@spi.action(
    ONTOLOGY, "生成结营报告",
    description="为患者生成服务包结营时面对面解读用的报告",
    params=(
        ParamSpec("patient_id", "string", required=True),
        ParamSpec("package_id", "string", required=True),
    ),
    guards=("R01_数据充分性门槛_仅管结论层",),
    post_rules=(
        "R09_TBR超标触发去强化审查",
        "R03b_Level2低血糖_回顾事件统计",
        "R04b_Level1低血糖_回顾事件统计",
        "R42_急性混杂窗口禁止出结论",
        "低血糖优先抢占",
    ),
    writes=("OutboundContent",),
    validate_supported=True,
    hil=HilPolicy(reviewer_role="医师/营养师签发",
                  predicate=lambda confidence, touched_hard: True),
)
def 生成结营报告(ctx) -> None:
    """面对面解读用的人话版报告

    HIL：医师/营养师签发（触发条件 always）。
    写入对象：OutboundContent。
    """
    # TODO(FDE): 业务回写。逐个 writes 对象补 stage_write，key 命名由 FDE 定：
    # ctx.stage_write("OutboundContent", f"outboundcontent_{ctx.params[...]}", {...})
    # ctx.emit_effect("workitem", on="...", template="...")   # 如需派工单
    ctx.set_confidence(0.8)
    # ctx.add_evidence(source="...")                            # 取自命中规则的 source
    raise NotImplementedError("生成结营报告 handler 待实现")

@spi.action(
    ONTOLOGY, "兑现结果承诺",
    description="按依从数据结算一个服务包的结营 KPI",
    params=(
        ParamSpec("package_id", "string", required=True),
        ParamSpec("adherence_data", "object", required=True),
    ),
    guards=("R01_数据充分性门槛_仅管结论层",),
    post_rules=("C13_服务与产品物理分离",),
    writes=("KpiSettlement",),
    validate_supported=True,
    hil=HilPolicy(reviewer_role="店长 + 医师联合确认",
                  predicate=lambda confidence, touched_hard: True),
)
def 兑现结果承诺(ctx) -> None:
    """结营 KPI 结算，TBR 安全门一票否决

    HIL：店长 + 医师联合确认（触发条件 always）。
    写入对象：KpiSettlement。
    """
    # TODO(FDE): 业务回写。逐个 writes 对象补 stage_write，key 命名由 FDE 定：
    # ctx.stage_write("KpiSettlement", f"kpisettlement_{ctx.params[...]}", {...})
    # ctx.emit_effect("workitem", on="...", template="...")   # 如需派工单
    ctx.set_confidence(0.8)
    # ctx.add_evidence(source="...")                            # 取自命中规则的 source
    raise NotImplementedError("兑现结果承诺 handler 待实现")

@spi.action(
    ONTOLOGY, "记录服务退出与退款归因",
    description="记录患者退出服务的原因与退款金额，并关联流失信号",
    params=(
        ParamSpec("patient_id", "string", required=True),
        ParamSpec("exit_reason", "string", required=True),
        ParamSpec("refund_amount", "number", required=False),
    ),
    writes=("ServiceExitRecord", "ChurnSignal"),
    validate_supported=True,
    hil=HilPolicy(reviewer_role="店长确认",
                  predicate=lambda confidence, touched_hard: True),
)
def 记录服务退出与退款归因(ctx) -> None:
    """流失信号误报率评估的 ground truth

    HIL：店长确认（触发条件 always）。
    写入对象：ServiceExitRecord、ChurnSignal。
    """
    # TODO(FDE): 业务回写。逐个 writes 对象补 stage_write，key 命名由 FDE 定：
    # ctx.stage_write("ServiceExitRecord", f"serviceexitrecord_{ctx.params[...]}", {...})
    # ctx.stage_write("ChurnSignal", f"churnsignal_{ctx.params[...]}", {...})
    # ctx.emit_effect("workitem", on="...", template="...")   # 如需派工单
    ctx.set_confidence(0.8)
    # ctx.add_evidence(source="...")                            # 取自命中规则的 source
    raise NotImplementedError("记录服务退出与退款归因 handler 待实现")

@spi.action(
    ONTOLOGY, "创建服务包SKU",
    description="创建一个服务包 SKU（等级、内容清单）",
    params=(
        ParamSpec("sku_id", "string", required=True),
        ParamSpec("tier", "string", required=True),
        ParamSpec("contents", "list", required=True),
    ),
    guards=("C1_器械经营资质闸", "C13_服务与产品物理分离", "C15_服务包禁止捆绑分佣"),
    post_rules=("R54_服务话术不得含夜间安全承诺",),
    writes=("ServicePackage", "ProductSku"),
    validate_supported=True,
    hil=HilPolicy(reviewer_role="合规官审核",
                  predicate=lambda confidence, touched_hard: True),
)
def 创建服务包SKU(ctx) -> None:
    """服务包只含服务，不含任何产品

    HIL：合规官审核（触发条件 always）。
    写入对象：ServicePackage、ProductSku。
    """
    _fde.ACTIONS['创建服务包SKU'](ctx)

@spi.action(
    ONTOLOGY, "上架产品SKU",
    description="把一个产品 SKU（指定类别：服务 / 食品 / 器械引用）上架",
    params=(
        ParamSpec("sku_id", "string", required=True),
        ParamSpec("category", "string", required=True),
    ),
    guards=("C1_器械经营资质闸", "C2_网络销售备案与证照公示", "C14_产品标签合规校验"),
    writes=("ProductSku",),
    validate_supported=True,
    hil=HilPolicy(reviewer_role="合规官审核",
                  predicate=lambda confidence, touched_hard: True),
)
def 上架产品SKU(ctx) -> None:
    """器械一律拒绝；食品须核验标签

    HIL：合规官审核（触发条件 always）。
    写入对象：ProductSku。
    """
    _fde.ACTIONS['上架产品SKU'](ctx)

@spi.action(
    ONTOLOGY, "生成产品推荐",
    description="为患者生成一条产品推荐内容（可附推荐话术 pitch）",
    params=(
        ParamSpec("patient_id", "string", required=True),
        ParamSpec("sku_id", "string", required=True),
        ParamSpec("pitch", "string", required=False),  # FDE：推荐话术，进 R32/D9 闸
    ),
    guards=("C4_数据用于产品推荐须单独同意", "C13_服务与产品物理分离"),
    post_rules=("R32_产品推荐合规闸", "D9_产品功效声称拦截"),
    writes=("OutboundContent",),
    validate_supported=True,
    hil=HilPolicy(reviewer_role="合规官",
                  predicate=lambda confidence, touched_hard: confidence < 0.75),
)
def 生成产品推荐(ctx) -> None:
    """不得与分层或缓解同句，须附固体饮料尾注

    HIL：合规官（触发条件 confidence<0.75）。
    写入对象：OutboundContent。
    """
    _fde.ACTIONS['生成产品推荐'](ctx)

@spi.action(
    ONTOLOGY, "发布宣传素材",
    description="把一条宣传素材发布到指定渠道",
    params=(
        ParamSpec("content_id", "string", required=True),
        ParamSpec("channel", "string", required=True),
    ),
    guards=("C17_机构与门诊命名合规",),
    post_rules=(
        "C16_禁止发布患者前后对比案例",
        "C11_分型输出制度层不得当诊断",
        "D8_禁用词拦截",
        "D9_产品功效声称拦截",
        "R54_服务话术不得含夜间安全承诺",
    ),
    writes=("OutboundContent",),
    validate_supported=True,
    hil=HilPolicy(reviewer_role="合规官",
                  predicate=lambda confidence, touched_hard: True),
)
def 发布宣传素材(ctx) -> None:
    """停发个案对比，命名合规

    HIL：合规官（触发条件 always）。
    写入对象：OutboundContent。
    """
    _fde.ACTIONS['发布宣传素材'](ctx)

@spi.action(
    ONTOLOGY, "群内答复患者",
    description="以指定角色在患者企微群内发一条答复消息",
    params=(
        ParamSpec("patient_id", "string", required=True),
        ParamSpec("message", "string", required=True),
        ParamSpec("sender_role", "string", required=True),
    ),
    guards=("C19_线上随访边界", "R51_分层结论默认不可披露患者"),
    post_rules=(
        "D8_禁用词拦截",
        "D10_用药建议拦截",
        "C6_群内数据最小可见范围",
        "R54_服务话术不得含夜间安全承诺",
        "R55_显示口径_没有数据不得说成没有异常",
    ),
    writes=("OutboundContent", "DeliveryReceipt"),
    validate_supported=True,
    hil=HilPolicy(reviewer_role="五师本人",
                  predicate=lambda confidence, touched_hard: True),
)
def 群内答复患者(ctx) -> None:
    """五师在企微群内的对外发言

    HIL：五师本人（触发条件 always）。
    写入对象：OutboundContent、DeliveryReceipt。
    """
    _fde.ACTIONS['群内答复患者'](ctx)

@spi.action(
    ONTOLOGY, "建立厂商云通道对接",
    description="登记一条厂商云到云数据通道及其授权",
    params=(
        ParamSpec("vendor", "string", required=True),
        ParamSpec("channel_id", "string", required=True),
    ),
    guards=("C5_厂商云对接协议与PIPIA", "C8_数据出境与境外云禁止"),
    writes=("ChannelRegistry", "VendorGrant"),
    validate_supported=True,
    hil=HilPolicy(reviewer_role="合规官",
                  predicate=lambda confidence, touched_hard: True),
)
def 建立厂商云通道对接(ctx) -> None:
    """云到云通道，须境内存储且协议齐备

    HIL：合规官（触发条件 always）。
    写入对象：ChannelRegistry、VendorGrant。
    """
    # TODO(FDE): 业务回写。逐个 writes 对象补 stage_write，key 命名由 FDE 定：
    # ctx.stage_write("ChannelRegistry", f"channelregistry_{ctx.params[...]}", {...})
    # ctx.stage_write("VendorGrant", f"vendorgrant_{ctx.params[...]}", {...})
    # ctx.emit_effect("workitem", on="...", template="...")   # 如需派工单
    ctx.set_confidence(0.8)
    # ctx.add_evidence(source="...")                            # 取自命中规则的 source
    raise NotImplementedError("建立厂商云通道对接 handler 待实现")

@spi.action(
    ONTOLOGY, "写入外部协作工具",
    description="把数据写入飞书等外部协作工具并记审计日志",
    params=(
        ParamSpec("target_system", "string", required=True),
        ParamSpec("payload_ref", "string", required=True),
    ),
    guards=("C7_患者数据禁止存放非平台工具",),
    post_rules=("C6_群内数据最小可见范围",),
    writes=("AuditLog",),
    validate_supported=True,
    hil=HilPolicy(reviewer_role="合规官",
                  predicate=lambda confidence, touched_hard: True),
)
def 写入外部协作工具(ctx) -> None:
    """向飞书等第三方 SaaS 提供数据，属持续对外提供行为

    HIL：合规官（触发条件 always）。
    写入对象：AuditLog。
    """
    _fde.ACTIONS['写入外部协作工具'](ctx)

@spi.action(
    ONTOLOGY, "维护凭证台账",
    description="更新一条执业凭证的台账记录（有效期、状态）",
    params=(
        ParamSpec("credential_id", "string", required=True),
    ),
    post_rules=("D11a_签发人资质失效自动冻结",),
    writes=("Credential",),
    validate_supported=True,
    # 台账是 D11a 冻结判定的唯一数据源，改台账等于改冻结前提，不可无人复核（validate B.4）
    hil=HilPolicy(reviewer_role="合规官（资质台账变更）",
                  predicate=lambda confidence, touched_hard: True),
)
def 维护凭证台账(ctx) -> None:
    """到期即自动冻结签发权限

    写入对象：Credential。
    """
    # TODO(FDE): 业务回写。逐个 writes 对象补 stage_write，key 命名由 FDE 定：
    # ctx.stage_write("Credential", f"credential_{ctx.params[...]}", {...})
    # ctx.emit_effect("workitem", on="...", template="...")   # 如需派工单
    ctx.set_confidence(0.8)
    # ctx.add_evidence(source="...")                            # 取自命中规则的 source
    raise NotImplementedError("维护凭证台账 handler 待实现")

@spi.action(
    ONTOLOGY, "门店清查确认",
    description="记录一家门店的合规清查确认与签字人",
    params=(
        ParamSpec("store_id", "string", required=True),
        ParamSpec("signed_by", "string", required=True),
    ),
    guards=("C18_非医疗机构不得实施诊疗", "C17_机构与门诊命名合规"),
    writes=("StoreReadinessCheck", "StoreEntity"),
    validate_supported=True,
    hil=HilPolicy(reviewer_role="店长签字，合规官抽查",
                  predicate=lambda confidence, touched_hard: True),
)
def 门店清查确认(ctx) -> None:
    """未完成清查的门店不予开通服务包

    HIL：店长签字，合规官抽查（触发条件 always）。
    写入对象：StoreReadinessCheck、StoreEntity。
    """
    # TODO(FDE): 业务回写。逐个 writes 对象补 stage_write，key 命名由 FDE 定：
    # ctx.stage_write("StoreReadinessCheck", f"storereadinesscheck_{ctx.params[...]}", {...})
    # ctx.stage_write("StoreEntity", f"storeentity_{ctx.params[...]}", {...})
    # ctx.emit_effect("workitem", on="...", template="...")   # 如需派工单
    ctx.set_confidence(0.8)
    # ctx.add_evidence(source="...")                            # 取自命中规则的 source
    raise NotImplementedError("门店清查确认 handler 待实现")

@spi.action(
    ONTOLOGY, "门店会话合规抽检",
    description="对门店会话片段做合规抽检并记录事件",
    params=(
        ParamSpec("message_fragment", "string", required=True),
        ParamSpec("actor", "string", required=True),
    ),
    post_rules=("D8_禁用词拦截", "D10_用药建议拦截"),
    writes=("ComplianceIncident",),
    validate_supported=True,
    hil=HilPolicy(reviewer_role="合规官",
                  predicate=lambda confidence, touched_hard: True),
)
def 门店会话合规抽检(ctx) -> None:
    """仅关键词命中片段可读，30 天 ≥3 次停发言权

    HIL：合规官（触发条件 always）。
    写入对象：ComplianceIncident。
    """
    # TODO(FDE): 业务回写。逐个 writes 对象补 stage_write，key 命名由 FDE 定：
    # ctx.stage_write("ComplianceIncident", f"complianceincident_{ctx.params[...]}", {...})
    # ctx.emit_effect("workitem", on="...", template="...")   # 如需派工单
    ctx.set_confidence(0.8)
    # ctx.add_evidence(source="...")                            # 取自命中规则的 source
    raise NotImplementedError("门店会话合规抽检 handler 待实现")

@spi.action(
    ONTOLOGY, "处理数据主体权利请求",
    description="登记并处理患者的数据主体权利请求（查询 / 更正 / 删除等）",
    params=(
        ParamSpec("patient_id", "string", required=True),
        ParamSpec("request_type", "string", required=True),
    ),
    post_rules=("C21_数据留存与审计日志",),
    writes=("DataSubjectRequest",),
    validate_supported=True,
    hil=HilPolicy(reviewer_role="合规官受理",
                  predicate=lambda confidence, touched_hard: True),
)
def 处理数据主体权利请求(ctx) -> None:
    """PIPL 44–50 条法定时限内答复留痕

    HIL：合规官受理（触发条件 always）。
    写入对象：DataSubjectRequest。
    """
    # TODO(FDE): 业务回写。逐个 writes 对象补 stage_write，key 命名由 FDE 定：
    # ctx.stage_write("DataSubjectRequest", f"datasubjectrequest_{ctx.params[...]}", {...})
    # ctx.emit_effect("workitem", on="...", template="...")   # 如需派工单
    ctx.set_confidence(0.8)
    # ctx.add_evidence(source="...")                            # 取自命中规则的 source
    raise NotImplementedError("处理数据主体权利请求 handler 待实现")

@spi.action(
    ONTOLOGY, "记录心理咨询介入",
    description="记录一次心理咨询介入笔记",
    params=(
        ParamSpec("patient_id", "string", required=True),
        ParamSpec("note", "string", required=True),
    ),
    writes=("PsychNote",),
    validate_supported=True,
    hil=HilPolicy(reviewer_role="心理咨询师",
                  predicate=lambda confidence, touched_hard: True),
)
def 记录心理咨询介入(ctx) -> None:
    """最严可见性档

    HIL：心理咨询师（触发条件 always）。
    写入对象：PsychNote。
    """
    # TODO(FDE): 业务回写。逐个 writes 对象补 stage_write，key 命名由 FDE 定：
    # ctx.stage_write("PsychNote", f"psychnote_{ctx.params[...]}", {...})
    # ctx.emit_effect("workitem", on="...", template="...")   # 如需派工单
    ctx.set_confidence(0.8)
    # ctx.add_evidence(source="...")                            # 取自命中规则的 source
    raise NotImplementedError("记录心理咨询介入 handler 待实现")

@spi.action(
    ONTOLOGY, "启用AI生成能力",
    description="登记启用某版本 AI 生成能力及其适用范围",
    params=(
        ParamSpec("model_version", "string", required=True),
        ParamSpec("scope", "string", required=True),
    ),
    guards=("C12_生成式AI备案与算法备案", "C8_数据出境与境外云禁止"),
    writes=("AuditLog",),
    validate_supported=True,
    hil=HilPolicy(reviewer_role="合规官",
                  predicate=lambda confidence, touched_hard: True),
)
def 启用AI生成能力(ctx) -> None:
    """智能体上线前的平台级备案闸

    HIL：合规官（触发条件 always）。
    写入对象：AuditLog。
    """
    # TODO(FDE): 业务回写。逐个 writes 对象补 stage_write，key 命名由 FDE 定：
    # ctx.stage_write("AuditLog", f"auditlog_{ctx.params[...]}", {...})
    # ctx.emit_effect("workitem", on="...", template="...")   # 如需派工单
    ctx.set_confidence(0.8)
    # ctx.add_evidence(source="...")                            # 取自命中规则的 source
    raise NotImplementedError("启用AI生成能力 handler 待实现")

@spi.action(
    ONTOLOGY, "设定机构与门诊名称",
    description="设置门店机构或门诊的名称",
    params=(
        ParamSpec("store_id", "string", required=True),
        ParamSpec("name", "string", required=True),
    ),
    guards=("C17_机构与门诊命名合规",),
    writes=("StoreEntity",),
    validate_supported=True,
    hil=HilPolicy(reviewer_role="合规官",
                  predicate=lambda confidence, touched_hard: True),
)
def 设定机构与门诊名称(ctx) -> None:
    """命名须经卫健核准且不得暗示疗效

    HIL：合规官（触发条件 always）。
    写入对象：StoreEntity。
    """
    # TODO(FDE): 业务回写。逐个 writes 对象补 stage_write，key 命名由 FDE 定：
    # ctx.stage_write("StoreEntity", f"storeentity_{ctx.params[...]}", {...})
    # ctx.emit_effect("workitem", on="...", template="...")   # 如需派工单
    ctx.set_confidence(0.8)
    # ctx.add_evidence(source="...")                            # 取自命中规则的 source
    raise NotImplementedError("设定机构与门诊名称 handler 待实现")

@spi.action(
    ONTOLOGY, "开展线上随访",
    description="向患者发起一次线上随访内容并记录",
    params=(
        ParamSpec("patient_id", "string", required=True),
        ParamSpec("content", "string", required=True),
    ),
    guards=("C19_线上随访边界",),
    post_rules=("D10_用药建议拦截", "D8_禁用词拦截"),
    writes=("ReferralRecord", "OutboundContent"),
    validate_supported=True,
    hil=HilPolicy(reviewer_role="医师或健管师按内容归属",
                  predicate=lambda confidence, touched_hard: True),
)
def 开展线上随访(ctx) -> None:
    """定性为健康管理随访并限制内容

    HIL：医师或健管师按内容归属（触发条件 always）。
    写入对象：ReferralRecord、OutboundContent。
    """
    # TODO(FDE): 业务回写。逐个 writes 对象补 stage_write，key 命名由 FDE 定：
    # ctx.stage_write("ReferralRecord", f"referralrecord_{ctx.params[...]}", {...})
    # ctx.stage_write("OutboundContent", f"outboundcontent_{ctx.params[...]}", {...})
    # ctx.emit_effect("workitem", on="...", template="...")   # 如需派工单
    ctx.set_confidence(0.8)
    # ctx.add_evidence(source="...")                            # 取自命中规则的 source
    raise NotImplementedError("开展线上随访 handler 待实现")

@spi.action(
    ONTOLOGY, "记录载体覆盖变更并强制告知",
    description="记录患者数据载体的覆盖状态变更（解绑 / 离线）并产出告知",
    params=(
        ParamSpec("patient_id", "string", required=True),
        ParamSpec("coverage_state", "string", required=True),
    ),
    post_rules=("R55_显示口径_没有数据不得说成没有异常", "R54_服务话术不得含夜间安全承诺"),
    writes=("CarrierRegistry", "GatewayDevice", "DeliveryReceipt"),
    validate_supported=True,
)
def 记录载体覆盖变更并强制告知(ctx) -> None:
    """解绑或离线必产出告知，豁免于触达封锁（phase=P2）

    写入对象：CarrierRegistry、GatewayDevice、DeliveryReceipt。
    """
    # TODO(FDE): 业务回写。逐个 writes 对象补 stage_write，key 命名由 FDE 定：
    # ctx.stage_write("CarrierRegistry", f"carrierregistry_{ctx.params[...]}", {...})
    # ctx.stage_write("GatewayDevice", f"gatewaydevice_{ctx.params[...]}", {...})
    # ctx.stage_write("DeliveryReceipt", f"deliveryreceipt_{ctx.params[...]}", {...})
    # ctx.emit_effect("workitem", on="...", template="...")   # 如需派工单
    ctx.set_confidence(0.8)
    # ctx.add_evidence(source="...")                            # 取自命中规则的 source
    raise NotImplementedError("记录载体覆盖变更并强制告知 handler 待实现")


# ============================================================================
# seed 桩 与 映射装载
# ============================================================================


def seed_reference_data(store) -> None:
    """TODO(FDE): 写入参考数据，供 function-backed 规则查。至少包括：
    BannedTermLibrary 禁用词库（D8/D9/D10/D11 依赖）、ChannelRegistry 通道能力与存储地域、
    DeviceModel 采样间隔/预热/MARD、MetricRegistry 指标口径台账、Credential 资质台账、
    冻结告警模板库（R56 依赖）、人群目标区间参数表（R28/R31/R46/R49 依赖）。

    参数 store 由引擎注入，实际类型为 clife_onto_engine.query.InMemoryStore。
    此处刻意不做类型标注：编译规则的红线是本插件只 import clife_onto_engine.sdk，
    不碰内核内部模块。需要静态类型时请在 FDE 侧用 TYPE_CHECKING 局部引入。
    """
    _fde.seed_reference_data(store)


spi.load_mappings(ONTOLOGY, _Path(__file__).parent / "mappings" / "objects.yaml")
