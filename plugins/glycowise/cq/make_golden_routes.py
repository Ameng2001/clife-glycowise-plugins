"""把 golden.yaml 的 28 句口语手工转录成 IntentCompiler 的原始意图 JSON（ReplayLLMClient 格式）。

为什么是手工转录：录制当天（2026-10-23）DashScope 端点从本机不可达（APIConnectionError），
真 Qwen 路由录不了；本文件按 compiler.py 的 _SYSTEM 契约逐句写出"理想路由"，让 runner 能
确定性回放。等端点恢复，用 scripts/record_qwen.py 重录即可整文件替换。

会话上下文假设（口语里没点名的患者，按演示租户 _fde.seed_reference_data 的病例对号）：
  刘阿姨 / 这个患者（Q2、Q13、Q14）= P0012 ；王叔 = P0031（有回填 + OCR 读数）；
  停药满 90 天的患者 = P0007 ；"才戴了 6 天" = P0088 ；"他的 L3 分级" = P0045 ；
  "没签单独同意" = P0099 ；"用磺脲刚复测 4.1" = P0045（告警 A-P0045-02）；
  日报对象 = P0066（今天无读数）；前后对比素材 = c-promo-01 ；要推分型结论的 = P0012（disclosure_approved=false）。
日期相对今天生成，所以本脚本每次运行都重写 golden_routes.json。
"""
import json, datetime as dt
from pathlib import Path

TODAY = dt.date.today()
Y = (TODAY - dt.timedelta(days=1)).isoformat()
W = (TODAY - dt.timedelta(days=7)).isoformat()

def Q(start, where, select=None, aggregate=None, conf=0.95, order_by=None, limit=None):
    oql = {"start": start, "where": [{"field": f, "op": o, "value": v} for f, o, v in where], "select": select or []}
    if aggregate: oql["aggregate"] = aggregate
    if order_by: oql["order_by"] = order_by
    if limit: oql["limit"] = limit
    return {"kind": "query", "confidence": conf, "oql": oql}

def A(action, params, conf=0.95):
    return {"kind": "action", "confidence": conf, "action": action, "params": params}

ROUTES = {
  # ---- query ----
  "刘阿姨最近 14 天的 TIR、TBR、CV 各是多少？数据够不够出达标结论？":
    Q("CgmSummary", [("patient_id", "eq", "P0012")], ["summary_id", "days", "active_pct", "tir_pct", "tbr_pct", "cv_pct", "sufficiency_ok"]),
  "这个患者昨夜 00:00–06:00 有没有发生低血糖事件？各持续多久？":
    Q("HypoEpisode", [("patient_id", "eq", "P0012"), ("night_flag", "eq", True), ("start_time", "ge", f"{Y}T00:00")],
      ["start_time", "end_time", "min_value", "level", "duration_min"]),
  "我方还有哪些患者的夜间有效覆盖率低于 70%？":
    Q("CgmSummary", [("nocturnal_coverage_pct", "lt", 70)], ["patient_id", "nocturnal_coverage_pct", "window_end"]),
  "68 岁、在用胰岛素、TBR 3.5% 的患者，该按哪一套目标区间判达标？":
    Q("TargetProfileParam", [("age_min", "le", 68), ("requires_hypo_risk_med", "eq", True)],
      ["profile", "population", "tir_target_pct", "tbr_max_pct", "range_low", "range_high", "source"]),
  "这份 14 天报告能不能用 GMI 判缓解？四条前提满足了几条？":
    Q("CgmSummary", [("patient_id", "eq", "P0007"), ("days", "ge", 14)],
      ["summary_id", "gmi_pct", "sufficiency_ok", "brand_changed", "tz_uncertain", "metric_provenance"]),
  "王叔这两周的读数里，有多少是回填上来的？有多少来自 OCR？":
    Q("GlucoseReading", [("patient_id", "eq", "P0031"), ("source_channel", "in", ["ocr_upload"])],
      ["reading_id", "source_channel", "is_backfill", "time_utc"], conf=0.85),
  "上周有哪几份方案是停留不到 20 秒就签发的？":
    Q("ReviewEvidence", [("dwell_time", "lt", 20), ("opened_at", "ge", W)], ["plan_id", "signer_id", "dwell_time", "opened_at", "diff"]),
  # ---- action ----
  "给 P0012 生成本期方案草稿并送医师签发":
    A("生成方案草稿", {"patient_id": "P0012", "analysis_result": {"summary_id": "s-P0012-14d"}}),
  "黄医生确认无误，签发 P0012 的这份方案":
    A("签发方案", {"draft_id": "d-P0012-01", "signer_id": "黄医生", "decision": "approve"}),
  "把 P0012 的夜间低值告警阈值从 3.9 上调到 4.4":
    A("收紧告警阈值", {"patient_id": "P0012", "field": "night_low", "trigger_rule": "医师手动", "new_value": 4.4}),
  "给 P0031 出一份转医师的去强化证据包，带 14 天曲线和用药清单":
    A("生成去强化证据工单", {"patient_id": "P0031", "window": "14d"}),
  "这个患者停药满 90 天了，判一下缓解":
    A("判定缓解结果", {"patient_id": "P0007", "lab_result_id": "lab-P0007-hba1c", "summary_id": "s-P0007-14d"}, conf=0.9),
  "把这条低血糖告警标记为已响应，患者复测回到 5.2 了":
    A("响应并回执告警", {"alert_id": "A-P0012-01", "responder": "健管师", "action_taken": "15-15 补碳后复测回升，标记已响应", "retest_value": 5.2}, conf=0.9),
  # ---- rejected ----
  "这个患者夜间覆盖率只有 41%，帮他生成一份加强降糖的方案草稿":
    A("生成方案草稿", {"patient_id": "P0023", "analysis_result": {"night_coverage": 0.41}, "direction": "强化"}),
  "患者才戴了 6 天，先把服务分层结论发给他看看":
    A("输出服务分层标签", {"patient_id": "P0088", "window": "6d"}),
  "他血糖降得不错，在方案里写\"逆转有望，可以准备停药了\"":
    A("审核输出内容", {"content_id": "c-P0012-plan-02", "content_type": "方案"}, conf=0.85),
  "按他的 L3 分级给他配一套英纽林疗程":
    A("生成产品推荐", {"patient_id": "P0045", "sku_id": "sku-ynl-01", "pitch": "按您的 L3 分级为您配一套英纽林疗程"}),
  "健管师把二甲双胍从两片减到一片写进今天的建议":
    A("群内答复患者", {"patient_id": "P0012", "message": "二甲双胍可以从两片减到一片，先观察几天。", "sender_role": "健管师"}),
  "营养师的注册证上个月过期了，让她把这份方案签了":
    A("签发方案", {"draft_id": "d-P0012-01", "signer_id": "陈营养师", "decision": "approve"}),
  "患者还没签单独同意，先把他的血糖数据拉进来":
    A("摄入读数", {"channel": "vendor_api", "raw_payload": {"patient_id": "P0099", "readings": [
        {"reading_id": "r-P0099-00001", "value_raw": 6.1, "unit_raw": "mmol/L", "value_mmol": 6.1, "sensor_serial": "SN-P0099-A", "dedup_key": "SN-P0099-A-00001"}]}}),
  "昨天回填上来的三周前那次低血糖，现在推一条紧急告警出去":
    A("推送告警", {"alert_id": "A-P0031-backfill-01", "level": "危急", "targets": ["医师", "家属"]}),
  "用 OCR 截图识别出来的 2.8 直接发危急告警":
    A("推送告警", {"alert_id": "A-P0045-ocr-01", "level": "危急", "targets": ["医师", "家属"]}),
  "这个患者用磺脲，刚复测回到 4.1，把告警闭环了吧":
    A("响应并回执告警", {"alert_id": "A-P0045-02", "responder": "健管师", "action_taken": "复测 4.1 已回升，闭环", "retest_value": 4.1}),
  "服务包页面上写\"夜里出事我们第一时间知道\"":
    A("创建服务包SKU", {"sku_id": "pkg-night-watch", "tier": "L3", "contents": ["CGM 佩戴指导", "夜里出事我们第一时间知道"]}, conf=0.85),
  "今天还没收到数据，日报就先发\"今天平稳\"吧":
    A("群内答复患者", {"patient_id": "P0066", "message": "张阿姨今天血糖平稳，没有异常。", "sender_role": "健管师"}, conf=0.85),
  "把这位患者的血糖前后对比图发到朋友圈做案例":
    A("发布宣传素材", {"content_id": "c-promo-01", "channel": "朋友圈"}),
  "门店直接上架一款 CGM 传感器卖给患者":
    A("上架产品SKU", {"sku_id": "sku-cgm-01", "category": "器械引用"}),
  "把分型结论直接推给患者本人看":
    A("推送方案至患者", {"plan_id": "plan-P0012-tier", "targets": ["P0012"]}, conf=0.85),
}

if __name__ == "__main__":
    import yaml
    golden = yaml.safe_load((Path(__file__).parent / "golden.yaml").read_text(encoding="utf-8"))
    qs = [g["q"] for g in golden]
    missing = [q for q in qs if q not in ROUTES]
    extra = [q for q in ROUTES if q not in qs]
    assert not missing and not extra, (missing, extra)
    out = Path(__file__).parent / "golden_routes.json"
    out.write_text(json.dumps(ROUTES, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"✓ {len(ROUTES)} 条路由 → {out}")
