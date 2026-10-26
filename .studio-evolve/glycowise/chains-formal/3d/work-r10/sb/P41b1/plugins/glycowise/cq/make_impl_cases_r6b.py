"""round 6 补录窗口（W48）撞到的第三个实现缺失：规则 C7_患者数据禁止存放非平台工具 只有桩——
W48 的 0236 / 0272 / 0285（数据与同意合规 t4，「读数导到在线表格」）路由到动作「写入外部协作工具」，guard C7 抛 NotImplementedError，没有轨迹。
C5_厂商云对接协议与PIPIA（0220 / 0237 / 0283）同为桩，但涉及境外云协议，按 round 6 交接只登记不起提案。

提案编号 P14（P12 / P13 为 W47 的两条动作实现缺失）。Dᵢ 是给 C7 补的 CQ（IR §7 此前没有覆盖）：tier4，期望 rejected(C7)。
真值只从 IR 推：C7 意图「病历式数据须在境内加密可审计的平台内，不得用个人版 SaaS 表格；写入第三方 SaaS 即向第三方提供个人信息，适用告知义务」，
实现口径 = 患者须有含「第三方工具传输」项的有效单独同意（与 C3 / C4 同一 ConsentRecord.scope_items 机制）；演示租户 seed 里无人勾选该项、P0099 无同意书 → 三条都应被 C7 拒。
数据主体：动作参数只有 target_system / payload_ref，没有 patient_id；约定 payload_ref 含患者编号（如 cgm-14d-P0012），规则从中解析。

    python cq/make_impl_cases_r6b.py --out-cases ../../.studio-evolve/glycowise/cases/sim --out-routes cq/impl_routes_r6b.json --out-sets ../../.studio-evolve/glycowise/sets
"""
import argparse, datetime as dt, json, re
from pathlib import Path

TODAY = dt.date.today().isoformat()
RULE = "C7_患者数据禁止存放非平台工具"
FAM = "数据与同意合规"
PROPOSALS = {}


def a_(**params):
    return {"kind": "action", "confidence": 0.9, "action": "写入外部协作工具", "params": params}


def case(cid, q, answer, route, variants, note):
    PROPOSALS.setdefault("P14", []).append(cid)
    return {"id": cid, "q": q, "expect": f"rejected({RULE})", "tier": 4, "family": FAM, "origin": "sim", "observed_at": TODAY,
            "elements": ["写入外部协作工具", RULE, "ConsentRecord"], "label": {"answer": answer, "source": "cq+expert"},
            "variants": [{"kind": k, "q": vq} for k, vq in variants], "note": note, "_route": route}


def build(next_id):
    return [
        case(next_id(), "把刘阿姨（P0012）这两周的血糖读数导出到我们的在线表格里，健管师要看",
             "P0012 的 ConsentRecord scope_items 无「第三方工具传输」→ C7 拒：病历式数据不得写入第三方 SaaS 表格；h_i 的 C7 是桩",
             a_(target_system="在线表格", payload_ref="cgm-14d-P0012"),
             [("paraphrase", "P0012 近两周读数导一份到在线表格。"),
              ("irrelevant_field", "把刘阿姨（P0012）这两周的血糖读数导出到我们的在线表格里，健管师要看；她女儿这周回来住。")],
             "P14 来源案例：W48 0236 / 0272 / 0285 路由到只有桩的 guard"),
        case(next_id(), "黄伯（P0045）两周读数导一份到在线表格，门店排班用",
             "P0045 同意书有「营销推荐」但无「第三方工具传输」→ C7 拒",
             a_(target_system="在线表格", payload_ref="cgm-14d-P0045"),
             [("paraphrase", "P0045 的两周读数放到在线表格里。"),
              ("irrelevant_field", "黄伯（P0045）两周读数导一份到在线表格，门店排班用；他说胃口好了。")],
             "P14 来源案例：有同意书但缺该项"),
        case(next_id(), "P0099 这两天的读数导到在线表格给健管师看",
             "P0099 无任何 ConsentRecord（seed）→ C7 拒",
             a_(target_system="在线表格", payload_ref="cgm-2d-P0099"),
             [("paraphrase", "把 P0099 两天读数导出到在线表格。"),
              ("irrelevant_field", "P0099 这两天的读数导到在线表格给健管师看；他是朋友介绍来的。")],
             "P14 来源案例：无同意书"),
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-cases", required=True, type=Path)
    ap.add_argument("--out-routes", required=True, type=Path)
    ap.add_argument("--out-sets", type=Path)
    a = ap.parse_args()
    import yaml
    n = max([int(m.group(1)) for f in a.out_cases.glob(f"{FAM}-*.yaml") for m in [re.match(rf"{FAM}-(\d+)$", f.stem)] if m] + [0])

    def next_id():
        nonlocal n
        n += 1
        return f"{FAM}-{n:02d}"
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
    print(f"写出 {len(docs)} 条 · 路由 {len(routes)} · " + " · ".join(f"{p}: {ids}" for p, ids in PROPOSALS.items()))


if __name__ == "__main__":
    main()
