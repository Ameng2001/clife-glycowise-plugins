"""提案 P7 / P8 的来源案例（Dᵢ）：真实窗口 W45 暴露的两个只有桩的动作——转介医师（0224）、去重与通道仲裁（0233）。

口语是给这两个动作补的 CQ（IR §7 此前没有覆盖它们）；在生产插件 h_i 上 handler 抛 NotImplementedError（runner 记 IMPL_MISSING、判不过），
在沙箱 h' 上应按 IR §4 的意图裁决。路由是 manual 录制（CQ 原句 + 变体 → 同一意图），写进 cq/impl_routes.json 并并入 all_routes.json。

    python cq/make_impl_cases.py --out-cases ../../.studio-evolve/glycowise/cases/sim --out-routes cq/impl_routes.json --out-sets ../../.studio-evolve/glycowise/sets
"""
import argparse, datetime as dt, json, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
TODAY = dt.date.today().isoformat()
CONF = 0.95
PROPOSALS = {}


def a_(action, **params):
    return {"kind": "action", "confidence": CONF, "action": action, "params": params}


def case(prop, cid, fam, tier, expect, q, elements, answer, route, variants, note):
    PROPOSALS.setdefault(prop, []).append(cid)
    return {"id": cid, "q": q, "expect": expect, "tier": tier, "family": fam, "origin": "sim", "observed_at": TODAY,
            "elements": list(elements), "label": {"answer": answer, "source": "cq+expert"},
            "variants": [{"kind": k, "q": vq} for k, vq in variants], "note": note, "_route": route}


def cand(**kw):
    base = {"patient_id": "P0045", "unit_raw": "mmol/L", "tz_provenance": "device_reported", "source_channel": "vendor_api", "source_confidence": 0.99,
            "quality_flag": "clean", "is_backfill": False, "data_age": "fresh"}
    base.update(kw)
    base.setdefault("value_raw", base.get("value_mmol"))
    base.setdefault("device_time", base.get("time_utc"))
    return base


def build(next_id):
    out = []
    # ---- P7：转介医师（IR §4：用药类问题一律转医师；写 ReferralRecord；HIL 医师 always；post R22/R33/R58 对转介本身是「依据」不是「拒绝理由」）
    r = a_("转介医师", patient_id="P0088", question_context="李女士问二甲双胍要不要减量")
    out.append(case("P7", next_id("缓解路径"), "缓解路径", 3, "action(转介医师)",
                    "李女士（P0088）在群里问二甲双胍要不要减量，健管师不能答，把问题转介医师",
                    ["转介医师", "D10_用药建议拦截", "ReferralRecord"],
                    "用药类问题（药名 + 减量）健管师与 AI 不得答，应生成 ReferralRecord 转医师并进 HIL（医师接单）；h_i 的 handler 是桩，NotImplementedError", r,
                    [("paraphrase", "P0088 问二甲双胍减不减量，转医师。"),
                     ("irrelevant_field", "李女士（P0088）在群里问二甲双胍要不要减量，健管师不能答，把问题转介医师；她说最近胃口不错。")],
                    "P7 来源案例：W45 0224 路由到只有桩的动作"))
    r = a_("转介医师", patient_id="P0031", question_context="家属记录王叔夜里叫不醒、喂糖水后缓解，请医师复核")
    out.append(case("P7", next_id("低血糖安全"), "低血糖安全", 3, "action(转介医师)",
                    "王叔（P0031）家属记录到夜里叫不醒（sym-P0031-01），按 Level 3 严重低血糖转介医师复核",
                    ["转介医师", "R58_Level3严重低血糖强制转诊", "SymptomTreatmentRecord", "ReferralRecord"],
                    "Level 3（叫不醒）命中即强制就医与医师复核，不看血糖数值；转介本身就是 R58 要求的动作，应 pending_hil 而不是被 R58 以「未转诊」拒掉", r,
                    [("paraphrase", "P0031 叫不醒那次，转医师复核。"),
                     ("irrelevant_field", "王叔（P0031）家属记录到夜里叫不醒（sym-P0031-01），按 Level 3 严重低血糖转介医师复核；家属说他白天精神还行。")],
                    "P7 来源案例：R58 挂在转介医师上的语义"))
    r = a_("转介医师", patient_id="P0007", question_context="周先生停药观察期问能不能把二甲双胍彻底停掉")
    out.append(case("P7", next_id("缓解路径"), "缓解路径", 3, "action(转介医师)",
                    "周先生（P0007）停药观察期里问能不能把二甲双胍彻底停掉，转介医师",
                    ["转介医师", "R33_停药观察期反弹预警", "RemissionClock", "ReferralRecord"],
                    "停药观察期（RemissionClock running）的停药问题转医师；R33 无反弹信号（7 天均值 / GMI / TAR 均未超）→ pending_hil", r,
                    [("paraphrase", "P0007 问能不能停二甲双胍，转医师。"),
                     ("irrelevant_field", "周先生（P0007）停药观察期里问能不能把二甲双胍彻底停掉，转介医师；他这周开始晨跑了。")],
                    "P7 来源案例：R33 挂在转介医师上的语义"))
    # ---- P8：去重与通道仲裁（IR §4：按传感器序号去重，多路自动仲裁；guard R48；post R36 / R02）
    r = a_("去重与通道仲裁", reading_candidate=cand(reading_id="r-P0045-dup1", value_mmol=6.8, time_utc="2026-10-22T23:45", sensor_serial="SN-P0045-A", dedup_key="SN-P0045-A-01343"))
    out.append(case("P8", next_id("数据与同意合规"), "数据与同意合规", 3, "action(去重与通道仲裁)",
                    "厂商接口重推了黄伯（P0045）23:45 那条读数（r-P0045-dup1，序号 SN-P0045-A-01343），做去重仲裁",
                    ["去重与通道仲裁", "R48_去重键必须用传感器序号", "GlucoseReading"],
                    "dedup_key 与库里 r-P0045-01343 相同 → 候选判重复，落库为 superseded（不计入指标），动作 committed", r,
                    [("paraphrase", "P0045 的 r-P0045-dup1（SN-P0045-A-01343）去重。"),
                     ("irrelevant_field", "厂商接口重推了黄伯（P0045）23:45 那条读数（r-P0045-dup1，序号 SN-P0045-A-01343），做去重仲裁；今天天气不错。")],
                    "P8 来源案例：W45 0233 路由到只有桩的动作"))
    r = a_("去重与通道仲裁", reading_candidate=cand(reading_id="r-P0045-x9", value_mmol=6.5, time_utc="2026-10-23T00:00", sensor_serial="SN-P0045-A", dedup_key="SN-P0045-A-01344"))
    out.append(case("P8", next_id("数据与同意合规"), "数据与同意合规", 3, "action(去重与通道仲裁)",
                    "黄伯（P0045）新到一条读数 r-P0045-x9（00:00，6.5，序号 SN-P0045-A-01344），做去重仲裁后入库",
                    ["去重与通道仲裁", "R48_去重键必须用传感器序号", "GlucoseReading"],
                    "序号唯一、±90s 内无其它通道读数 → 新读数 ingested/clean，动作 committed", r,
                    [("paraphrase", "P0045 的 r-P0045-x9（SN-P0045-A-01344）入库。"),
                     ("irrelevant_field", "黄伯（P0045）新到一条读数 r-P0045-x9（00:00，6.5，序号 SN-P0045-A-01344），做去重仲裁后入库；他昨晚睡得早。")],
                    "P8 来源案例：正常新读数"))
    r = a_("去重与通道仲裁", reading_candidate=cand(reading_id="r-P0045-v7", value_mmol=7.1, time_utc="2026-10-23T00:15", sensor_serial=None, dedup_key="vendor-rec-778899"))
    out.append(case("P8", next_id("数据与同意合规"), "数据与同意合规", 3, "rejected(R48_去重键必须用传感器序号)",
                    "黄伯（P0045）的读数 r-P0045-v7 没带传感器序号，用厂商记录 ID vendor-rec-778899 做去重键，做去重仲裁",
                    ["去重与通道仲裁", "R48_去重键必须用传感器序号"],
                    "R48：去重键必须是传感器序号 + 序号；无序号又没置 weak_dedup 兜底 → 拒绝", r,
                    [("paraphrase", "P0045 的 r-P0045-v7 用厂商记录 ID 去重。"),
                     ("irrelevant_field", "黄伯（P0045）的读数 r-P0045-v7 没带传感器序号，用厂商记录 ID vendor-rec-778899 做去重键，做去重仲裁；他今天换了手机。")],
                    "P8 来源案例：R48 拒绝分支"))
    r = a_("去重与通道仲裁", reading_candidate=cand(reading_id="r-P0045-ocr9", value_mmol=6.9, time_utc="2026-10-22T23:45", sensor_serial=None, dedup_key="ocr-P0045-9", weak_dedup=True,
                                                   source_channel="ocr_upload", source_confidence=0.78, tz_provenance="upload_day_assumed", data_age="stale"))
    out.append(case("P8", next_id("数据与同意合规"), "数据与同意合规", 3, "action(去重与通道仲裁)",
                    "黄伯（P0045）家属截图 OCR 出一条 23:45 的 6.9（r-P0045-ocr9，无序号，已标 weak_dedup），与厂商那条做通道仲裁",
                    ["去重与通道仲裁", "R48_去重键必须用传感器序号", "GlucoseReading"],
                    "无序号但置了 weak_dedup → R48 放行；±90s 内已有厂商 vendor_api 读数（置信 0.99 > 0.78）→ OCR 候选判 superseded，动作 committed", r,
                    [("paraphrase", "P0045 的 OCR 读数 r-P0045-ocr9（weak_dedup）仲裁。"),
                     ("irrelevant_field", "黄伯（P0045）家属截图 OCR 出一条 23:45 的 6.9（r-P0045-ocr9，无序号，已标 weak_dedup），与厂商那条做通道仲裁；截图是女儿发的。")],
                    "P8 来源案例：弱去重兜底 + 多通道仲裁"))
    r = a_("去重与通道仲裁", reading_candidate=cand(reading_id="r-P0045-art1", value_mmol=2.4, time_utc="2026-10-22T23:37", sensor_serial="SN-P0045-A", dedup_key="SN-P0045-A-01345"))
    out.append(case("P8", next_id("低血糖安全"), "低血糖安全", 3, "action(去重与通道仲裁)",
                    "黄伯（P0045）23:37 来了一个 2.4 的单点（r-P0045-art1），前后 10 分钟都在 6.8 以上，做去重仲裁",
                    ["去重与通道仲裁", "R02_传感器压迫伪差识别", "GlucoseReading"],
                    "单点 <3.0 且前后 10min 内回升 ≥1.5 → R02 判压迫伪差（soft），读数落库标 noise、不计入事件；动作仍 committed（伪差判定不得抑制 hard 告警）", r,
                    [("paraphrase", "P0045 23:37 的 2.4 单点（r-P0045-art1）去重仲裁。"),
                     ("irrelevant_field", "黄伯（P0045）23:37 来了一个 2.4 的单点（r-P0045-art1），前后 10 分钟都在 6.8 以上，做去重仲裁；他说传感器被压到了。")],
                    "P8 来源案例：R02 伪差分支"))
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
