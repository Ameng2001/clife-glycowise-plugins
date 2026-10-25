"""glycowise · FDE 实现层 —— 规则体、动作回写、派生函数、参考/演示数据。

编译器（studio-ontology compile）只出骨架；本模块是 FDE 手填的那一半。`__init__.py` 里每条
function-backed 规则 / Action handler / Function 的函数体只剩一行转发到这里的 RULES / ACTIONS /
FUNCTIONS 字典；declarative 规则也改为转发——编译器生成的声明式函数体直接 `ctx.params.get(x) >= 70`，
参数缺省时抛 TypeError，这里统一做了 None 兜底与**从图谱派生**（params 有就用 params，没有就查对象）。

红线不变：本模块只 import `clife_onto_engine.sdk`。store 以鸭子类型使用（put_object / get_object）。

口径来源（优先级：控糖本体五元组清单.xlsx 指标口径 > IR §4 规则意图 > 本模块默认值）：
  TIR 3.9–10.0（妊娠 3.5–7.8）；TBR L1 <3.9、L2 <3.0；TAR L1 >10.0、L2 >13.9；CV = SD/mean；
  GMI% = 3.31 + 0.02392 × mean(mg/dL)；数据充分性 days ≥14 且 active_pct ≥70；
  夜间窗口 00:00–06:00（IR 口径；xlsx 用 23:00–06:00 近似，上线前临床拍板）；
  老年/高危 TBR 目标 <1%，一般成人 <4%；去重键 = 传感器序号 + 序号。
"""
from __future__ import annotations

import itertools
import math
import random
import re
import weakref
from datetime import date, datetime, timedelta

from clife_onto_engine.sdk import RuleResult

# ----------------------------------------------------------------------------- 常量 / 词表
TODAY = date.today()
TRUSTED_CHANNELS = ("vendor_api", "sdk_ble_direct", "ble_gls_1808")
HYPO_RISK_MEDS = ("胰岛素", "磺脲", "格列美脲", "格列齐特", "格列本脲", "格列吡嗪", "格列喹酮",
                  "格列奈", "瑞格列奈", "那格列奈", "预混", "甘精", "地特", "德谷", "门冬", "赖脯", "优泌林", "诺和")
DRUG_NAMES = HYPO_RISK_MEDS + ("二甲双胍", "阿卡波糖", "达格列净", "恩格列净", "卡格列净", "西格列汀",
                               "利格列汀", "沙格列汀", "吡格列酮", "司美格鲁肽", "利拉鲁肽", "度拉糖肽", "降糖药")
DOSE_RE = re.compile(r"(\d+(\.\d+)?\s*(mg|毫克|片|粒|单位|u|U|ml)|[一二两三四五六七八九十半]\s*(片|粒|单位)|加量|减量|加到|减到|减成|停掉|停用|停药|换成|改用|换药|加一|减一)")
DEFAULT_BANNED = ("逆转", "治愈", "根治", "停药", "疗程", "修复胰腺", "降血糖", "医学营养治疗", "MNT", "不用吃药", "摆脱药物")
NIGHT_PROMISE = ("夜间监护", "夜里出事", "第一时间知道", "24 小时看护", "24小时看护", "24小时守护", "全天候守护", "夜间值守", "整夜看着")
REASSURING = ("平稳", "没有异常", "一切正常", "血糖正常", "今天正常", "状态良好", "没问题")
TIER_RE = re.compile(r"L\s*[0-4]\s*(级|分级|分层)?|分层结论|分型结论|服务分层|[一二三四]\s*级糖尿病|[12一二]\s*型糖尿病|德心\s*L"
                     r"|(分层|分级|层级|等级)\s*(是|为|属于|定为|评为|：|:)?\s*[一二三四1-4]\s*级"  # P19a（W47 / 0115）：「分层是一级」类口语写法，与 L1 同义
                     # P23a（W50 / 0418）：没有「分层/分级」名词、靠评定动词框出的结论（「评下来是 2 级」「评为二级」「划到三级」「归为 1 级」）同样是
                     # 分层结论；排除「N 级低血糖 / 三级医院 / 告警级别」等非分层用法。不收裸「定」（「约定 2 层」「一定 3 层」会误中）
                     r"|(评|判|划|归)(下来|出来|定|为|成|到|作|是|了|在|\s){0,4}[0-4零一二三四]\s*(级|层)(?!\s*(低血糖|高血糖|医院|告警|警报|事件|护理|风险|甲等|乙等))")
REMISSION_RE = re.compile(r"缓解|逆转")
DIAG_CERTAIN_RE = re.compile(r"确诊|诊断为|你是\s*[12一二]\s*型糖尿病|您是\s*[12一二]\s*型糖尿病|属于\s*L\s*[0-4]|已经是糖尿病")
PRODUCT_WORDS = ("英纽林", "固体饮料", "营养粉", "代餐", "疗程", "套餐", "一套")
DEVICE_WORDS = ("CGM", "传感器", "血糖仪", "动态血糖")
SELL_WORDS = ("上架", "卖", "销售", "售卖", "出售", "收款", "下单")
SENT_SPLIT = re.compile(r"[。！？；\n]")


# ----------------------------------------------------------------------------- 小工具
def _dt(s):
    """ISO 日期/时间字符串 → datetime；解析不了返回 None。"""
    if s is None:
        return None
    if isinstance(s, datetime):
        return s
    if isinstance(s, date):
        return datetime(s.year, s.month, s.day)
    try:
        return datetime.fromisoformat(str(s).replace("Z", ""))
    except ValueError:
        return None


def _num(v):
    try:
        return None if v is None else float(v)
    except (TypeError, ValueError):
        return None


def P(ctx, *keys, default=None):
    """嵌套读 params：P(ctx, "analysis_result", "night_coverage")。"""
    cur = ctx.params
    for k in keys:
        if not isinstance(cur, dict) or k not in cur or cur[k] is None:
            return default
        cur = cur[k]
    return cur


def pid_of(ctx):
    """从 params 解析患者：patient_id → alert_id → draft_id → plan_id → raw_payload → content_id。"""
    pid = P(ctx, "patient_id")
    if pid:
        return str(pid)
    a = P(ctx, "alert_id")
    if a:
        ev = ctx.get("AlertEvent", str(a)) or {}
        if ev.get("patient_id"):
            return str(ev["patient_id"])
    d = P(ctx, "draft_id")
    if d:
        dr = ctx.get("PlanDraft", str(d)) or {}
        if dr.get("patient_id"):
            return str(dr["patient_id"])
    p = P(ctx, "plan_id")
    if p:
        ps = ctx.get("PlanSigned", str(p)) or ctx.get("PlanDraft", str(p)) or {}
        if ps.get("patient_id"):
            return str(ps["patient_id"])
    rp = P(ctx, "raw_payload", "patient_id")
    if rp:
        return str(rp)
    c = P(ctx, "content_id")
    if c:
        oc = ctx.get("OutboundContent", str(c)) or {}
        if oc.get("patient_ref"):
            return str(oc["patient_ref"])
    return None


def profile_of(ctx, pid=None):
    pid = pid or pid_of(ctx)
    return (ctx.get("PatientProfile", pid) or {}) if pid else {}


def summary_of(ctx, pid=None):
    """该患者最新一份 CgmSummary（按 window_end）。"""
    pid = pid or pid_of(ctx)
    if not pid:
        return {}
    rows = ctx.find("CgmSummary", lambda r: r.get("patient_id") == pid)
    return max(rows, key=lambda r: str(r.get("window_end", ""))) if rows else {}


def readings_of(ctx, pid, days=None, clean_only=False):
    since = (datetime.combine(TODAY, datetime.min.time()) - timedelta(days=days)) if days else None

    def ok(r):
        if r.get("patient_id") != pid:
            return False
        if clean_only and (r.get("source_channel") not in TRUSTED_CHANNELS or r.get("quality_flag") not in (None, "clean")):
            return False
        if since is not None:
            t = _dt(r.get("time_utc"))
            if t is None or t < since:
                return False
        return True
    return ctx.find("GlucoseReading", ok)


def episodes_of(ctx, pid, days=14):
    since = datetime.combine(TODAY, datetime.min.time()) - timedelta(days=days)
    return [e for e in ctx.find("HypoEpisode", lambda r: r.get("patient_id") == pid)
            if (_dt(e.get("start_time")) or since) >= since]


def meds_of(ctx, pid):
    meds = list(profile_of(ctx, pid).get("meds") or [])
    return meds


def hypo_risk(ctx, pid):
    if pid is None:
        return False
    if any(any(k in str(m) for k in HYPO_RISK_MEDS) for m in meds_of(ctx, pid)):
        return True
    hints = ctx.find("MedClassHint", lambda r: r.get("patient_id") == pid and r.get("hypo_risk_med") is True)
    return bool(hints)


def is_elderly(prof):
    age = _num(prof.get("age"))
    return prof.get("target_profile") == "elderly" or (age is not None and age >= 65)


def tbr_limit(prof, high_risk=False):
    return 1.0 if (is_elderly(prof) or high_risk or prof.get("health_tier") == "差") else 4.0


def tir_target(prof):
    if prof.get("target_profile") == "pregnancy" or prof.get("pregnant") is True:
        return 70.0
    return 50.0 if is_elderly(prof) else 70.0


def text_of(ctx):
    """本次要被审的文本：params 文本字段 + 引用对象正文 + 本次暂存的对外内容。"""
    parts = []
    for k in ("message", "content", "body", "question", "text", "copy", "name", "pitch"):
        v = P(ctx, k)
        if isinstance(v, str):
            parts.append(v)
    for k in ("contents", "targets"):
        v = P(ctx, k)
        if isinstance(v, (list, tuple)):
            parts.extend(str(x) for x in v)
    ar = P(ctx, "analysis_result")
    if isinstance(ar, dict):
        parts.extend(str(v) for v in ar.values() if isinstance(v, str))
    c = P(ctx, "content_id")
    if c:
        oc = ctx.get("OutboundContent", str(c)) or {}
        parts.append(str(oc.get("body") or ""))
    d = P(ctx, "draft_id")
    if d:
        parts.append(str((ctx.get("PlanDraft", str(d)) or {}).get("content") or ""))
    p = P(ctx, "plan_id")
    if p:
        ps = ctx.get("PlanSigned", str(p)) or ctx.get("PlanDraft", str(p)) or {}
        parts.append(str(ps.get("content_snapshot") or ps.get("content") or ""))
    s = P(ctx, "sku_id")
    if s:
        sku = ctx.get("ProductSku", str(s)) or {}
        parts.append(str(sku.get("name") or ""))
    so = staged_outbound(ctx)  # 本次暂存的对外内容正文（post_write 规则审的就是它）
    if so.get("body"):
        parts.append(str(so["body"]))
    return "\n".join(x for x in parts if x)


def sentences(text):
    return [s for s in SENT_SPLIT.split(text or "") if s.strip()]


def banned_terms(ctx):
    rows = ctx.find("BannedTermLibrary", lambda r: r.get("status", "active") != "deprecated")
    terms = [r["term"] for r in rows if r.get("term")]
    return terms or list(DEFAULT_BANNED)


def hits(text, terms):
    return [t for t in terms if t and t in (text or "")]


def product_mention(ctx, text):
    names = [r.get("name") for r in ctx.find("ProductSku", lambda r: r.get("category") == "食品") if r.get("name")]
    return hits(text, tuple(names) + PRODUCT_WORDS)


def _content_type(ctx):
    ct = P(ctx, "content_type")
    if ct:
        return str(ct)
    if P(ctx, "alert_id") is not None and P(ctx, "level") is not None:
        return "告警"
    c = P(ctx, "content_id")
    if c:
        return str((ctx.get("OutboundContent", str(c)) or {}).get("content_type") or "")
    return ""


_EXEC_TOKENS = weakref.WeakKeyDictionary()   # Capability 对象 → 本次执行令牌（对象一回收，条目自动消失）
_EXEC_SEQ = itertools.count(1)


def exec_token(ctx):
    """本次执行（一次 execute / validate）的令牌。handler 暂存写入时盖在 `_staged` 上，规则只认带同一令牌的行。

    P5（2026-W43 / 0018）：以前写死 `_staged: True`，commit 后原样持久化进库，于是后续任何动作的 `find(_staged)` 都把历史行
    当成「本次暂存」——R51 隔 7 条轨迹、跨患者读到 0011 落库的证据包正文而误拒。令牌按执行递增，历史行的旧令牌永远对不上。
    """
    try:
        tok = _EXEC_TOKENS.get(ctx)
    except TypeError:  # 不可弱引用 / 不可哈希的 ctx（测试桩）：退化为对象身份
        return id(ctx)
    if tok is None:
        tok = _EXEC_TOKENS[ctx] = next(_EXEC_SEQ)
    return tok


def is_staged(ctx, r):
    """这一行是不是**本次执行**暂存的（而非历史执行落库后残留的 `_staged` 标记）。"""
    return r.get("_staged") == exec_token(ctx)


def staged_outbound(ctx):
    """本次暂存的对外内容（post_write 规则里可见）。"""
    rows = ctx.find("OutboundContent", lambda r: is_staged(ctx, r))
    return rows[-1] if rows else {}


# ----------------------------------------------------------------------------- 指标（纯函数，seed 与 Function 共用）
def metrics_from_values(values, profile="adult"):
    """values: mmol/L 列表（clean 读数）。返回 dict(tir, tbr, tbr_l2, tar, tar_l2, cv, sd, mean, gmi)。空 → 全 None。"""
    vals = [float(v) for v in values if v is not None]
    if not vals:
        return {k: None for k in ("tir", "tbr", "tbr_l2", "tar", "tar_l2", "cv", "sd", "mean", "gmi")}
    lo, hi = (3.5, 7.8) if profile == "pregnancy" else (3.9, 10.0)
    n = len(vals)
    mean = sum(vals) / n
    sd = math.sqrt(sum((v - mean) ** 2 for v in vals) / n)
    pct = lambda cond: round(100.0 * sum(1 for v in vals if cond(v)) / n, 1)
    return {
        "tir": pct(lambda v: lo <= v <= hi), "tbr": pct(lambda v: v < 3.9), "tbr_l2": pct(lambda v: v < 3.0),
        "tar": pct(lambda v: v > 10.0), "tar_l2": pct(lambda v: v > 13.9),
        "cv": round(100.0 * sd / mean, 1) if mean else None, "sd": round(sd, 2), "mean": round(mean, 2),
        "gmi": round(3.31 + 0.02392 * mean * 18.016, 2),
    }


def episodes_from_readings(rows, min_minutes=15):
    """持续 ≥15 分钟的 <3.9 连续段 → HypoEpisode 行（回顾口径，Danne 2017）。"""
    rows = sorted((r for r in rows if r.get("value_mmol") is not None and _dt(r.get("time_utc"))), key=lambda r: r["time_utc"])
    out, run = [], []

    def flush():
        if not run:
            return
        t0, t1 = _dt(run[0]["time_utc"]), _dt(run[-1]["time_utc"])
        dur = (t1 - t0).total_seconds() / 60 + 15  # 采样间隔 15 min，末点也算满一格
        if dur >= min_minutes:
            mn = min(r["value_mmol"] for r in run)
            out.append({"patient_id": run[0]["patient_id"], "start_time": t0.isoformat(timespec="minutes"),
                        "end_time": (t1 + timedelta(minutes=15)).isoformat(timespec="minutes"), "min_value": round(mn, 1),
                        "level": "L2" if mn < 3.0 else "L1", "night_flag": 0 <= t0.hour < 6, "duration_min": int(dur)})
    for r in rows:
        if r["value_mmol"] < 3.9:
            if run and (_dt(r["time_utc"]) - _dt(run[-1]["time_utc"])).total_seconds() > 20 * 60:
                flush(); run = []
            run.append(r)
        else:
            flush(); run = []
    flush()
    return out


def nocturnal_coverage(rows, days):
    """00:00–06:00 窗口按 15 min 采样应有 24 点/夜；实际 clean 点数 / 应有点数。"""
    night = [r for r in rows if (_dt(r.get("time_utc")) or datetime.min).hour < 6 and r.get("quality_flag") in (None, "clean")]
    expected = max(days, 1) * 24
    return round(min(100.0, 100.0 * len(night) / expected), 1)


def consecutive_low_nights(rows, days, threshold=50.0):
    by_day = {}
    for r in rows:
        t = _dt(r.get("time_utc"))
        if t and t.hour < 6 and r.get("quality_flag") in (None, "clean"):
            by_day[t.date()] = by_day.get(t.date(), 0) + 1
    start = TODAY - timedelta(days=days)
    best = cur = 0
    for i in range(days):
        d = start + timedelta(days=i + 1)
        cov = 100.0 * by_day.get(d, 0) / 24
        cur = cur + 1 if cov < threshold else 0
        best = max(best, cur)
    return best


# ----------------------------------------------------------------------------- 规则实现
RULES = {}


def rule(name):
    def deco(fn):
        RULES[name] = fn
        return fn
    return deco


def _fail(name, msg, sugg=""):
    return RuleResult.fail(f"{name}：{msg}", suggestion=sugg)


def _direction(ctx):
    d = P(ctx, "direction") or P(ctx, "plan_direction") or P(ctx, "analysis_result", "direction")
    if d is None:
        st = ctx.find("PlanDraft", lambda r: is_staged(ctx, r))
        d = st[-1].get("direction") if st else None
    d = str(d or "").lower()
    if d in ("强化", "intensify", "intensification", "加强", "加强降糖", "up"):
        return "强化"
    if d in ("去强化", "deintensify", "de-intensify", "减量", "down"):
        return "去强化"
    return "维持" if d else None


def _night_cov(ctx, pid):
    v = P(ctx, "nocturnal_coverage_pct")
    if v is None:
        v = P(ctx, "analysis_result", "night_coverage")
        if v is None:
            v = P(ctx, "analysis_result", "nocturnal_coverage_pct")
    v = _num(v)
    if v is not None:
        return v * 100 if v <= 1.0 else v
    return _num(summary_of(ctx, pid).get("nocturnal_coverage_pct"))


@rule("R35_夜间覆盖不足禁强化")
def r35(ctx):
    pid = pid_of(ctx)
    cov, direction = _night_cov(ctx, pid), _direction(ctx)
    if direction != "强化":
        return RuleResult.ok()
    if cov is None:
        return _fail("R35", "夜间覆盖率未知，按 R49 最保守口径禁止强化方向草稿", "先计算窗口指标（含 nocturnal_coverage_pct）再出草稿")
    if cov < 70:
        return _fail("R35", f"夜间有效覆盖 {cov:.0f}% < 70%，TBR 被系统性低估，禁止生成强化降糖方向的草稿",
                     "改为维持/去强化方向，或先补夜间数据（载体同步）再评估")
    return RuleResult.ok()


@rule("R01_数据充分性门槛_仅管结论层")
def r01(ctx):
    pid = pid_of(ctx)
    s = summary_of(ctx, pid)
    days = _num(P(ctx, "days")) or _num(s.get("days"))
    active = _num(P(ctx, "active_pct")) or _num(s.get("active_pct"))
    if days is None or active is None:
        return _fail("R01", "没有窗口指标（days / active_pct），结论层不出结论", "先跑「计算窗口指标」")
    if days < 14 or active < 70:
        return _fail("R01", f"佩戴 {days:.0f} 天、有效数据 {active:.0f}%，未达 14 天 + ≥70%，只出趋势描述，禁出达标/分层/缓解结论",
                     "继续佩戴至 14 天且有效率 ≥70% 后再出结论")
    return RuleResult.ok()


@rule("R49_缺参数时按最保守执行")
def r49(ctx):
    pid = pid_of(ctx)
    prof = profile_of(ctx, pid)
    age = P(ctx, "age") if P(ctx, "age") is not None else prof.get("age")
    tier = P(ctx, "health_tier") if P(ctx, "health_tier") is not None else prof.get("health_tier")
    tp = P(ctx, "target_profile") if P(ctx, "target_profile") is not None else prof.get("target_profile")
    if not prof and pid:
        return _fail("R49", f"患者 {pid} 没有画像，人群参数缺失", "先建立 PatientProfile（age / health_tier / target_profile）")
    if age is not None and tier is None and tp != "elderly":
        return _fail("R49", "有年龄但缺 health_tier，且未按最保守人群（elderly）执行", "补 health_tier 或显式置 target_profile=elderly 并标 population_params_stale")
    return RuleResult.ok()


@rule("R42_急性混杂窗口禁止出结论")
def r42(ctx):
    pid = pid_of(ctx)
    if not pid:
        return RuleResult.ok()
    s = summary_of(ctx, pid)
    ws, we = _dt(s.get("window_start")), _dt(s.get("window_end"))
    evs = ctx.find("ClinicalContextEvent", lambda r: r.get("patient_id") == pid)
    for e in evs:
        st, en = _dt(e.get("start_at")), _dt(e.get("end_at"))
        if st is None:
            continue
        overlaps = (we is None or st <= we) and (en is None or ws is None or en >= ws)
        if overlaps:
            return _fail("R42", f"窗口内存在临床混杂事件「{e.get('type')}」（{e.get('start_at')}～{e.get('end_at') or '进行中'}），不做分层/不出结论",
                         "置 confounded_window，只出趋势描述；混杂期结束 14 天后重评")
    return RuleResult.ok()


@rule("R37_疑似1型LADA红旗")
def r37(ctx):
    prof = profile_of(ctx)
    flags = prof.get("lada_flags") or []
    if flags:
        return _fail("R37", f"疑似 1 型 / LADA 红旗：{list(flags)}，冻结减停药与缓解话术", "先开抗体与 C 肽，结果回报前不解冻")
    return RuleResult.ok()


@rule("低血糖优先抢占")
def hypo_first(ctx):
    pid = pid_of(ctx)
    if not pid:
        return RuleResult.ok()
    prof, s = profile_of(ctx, pid), summary_of(ctx, pid)
    tbr = _num(s.get("tbr_pct"))
    eps = episodes_of(ctx, pid, 14)
    hit = (tbr is not None and tbr >= tbr_limit(prof, hypo_risk(ctx, pid))) or any(e.get("level") == "L2" for e in eps)
    if hit and _direction(ctx) == "强化":
        return _fail("低血糖优先抢占", f"低血糖带已命中（TBR {tbr}% / L2 事件 {sum(1 for e in eps if e.get('level') == 'L2')} 次），抑制一切加强降糖方向输出",
                     "读图顺序 低→高→波动：先处理低血糖，草稿方向改为维持或去强化")
    return RuleResult.ok()


def _drug_dose_sentences(text):
    out = []
    for s in sentences(text):
        if any(d in s for d in DRUG_NAMES) and DOSE_RE.search(s):
            out.append(s.strip())
    return out


@rule("D10_用药建议拦截")
def d10(ctx):
    if _content_type(ctx) == "告警":
        return RuleResult.ok()  # R45：告警话术豁免关键词闸
    bad = _drug_dose_sentences(text_of(ctx))
    if bad:
        return _fail("D10", f"出现药名 + 剂量/加减停/换药表述：「{bad[0][:40]}」，健管师与 AI 均不得给用药建议", "删除该句，转医师任务（转介医师）")
    return RuleResult.ok()


@rule("D8_禁用词拦截")
def d8(ctx):
    if _content_type(ctx) == "告警":
        return RuleResult.ok()
    h = hits(text_of(ctx), banned_terms(ctx))
    if h:
        return _fail("D8", f"命中禁用词 {h}", "重写去掉禁用词；2 次不过转人工改写")
    return RuleResult.ok()


@rule("D11_未确认分型分级措辞拦截")
def d11(ctx):
    if DIAG_CERTAIN_RE.search(text_of(ctx) or ""):
        return _fail("D11", "出现「确诊 / 你是 X 型糖尿病 / 属于 LX」式确定性措辞，CGM 不能用于诊断", "降级为「提示区间，需医生确认」")
    return RuleResult.ok()


def _product_gate(ctx, name):
    text = text_of(ctx)
    prods = product_mention(ctx, text)
    if not prods:
        return RuleResult.ok()
    for s in sentences(text):
        if any(p in s for p in prods) and (TIER_RE.search(s) or REMISSION_RE.search(s)):
            return _fail(name, f"产品推荐与分层/缓解字样同句：「{s.strip()[:40]}」", "产品与分层结论、缓解/逆转字样分句分段，或删除产品推荐")
    return None


EFFICACY_RE = re.compile(r"(降|控|稳|调节|改善|逆转|治|根治)[^。；，,]{0,6}(血糖|糖化|胰岛|HbA1c|并发症)|(血糖|糖化)[^。；，,]{0,6}(稳得住|稳住|降|正常|达标|不升)|疗程|坚持(吃|用|服)[^。；，,]{0,8}(个月|周|天)")


def _efficacy_claim(ctx, name):
    """P16a（W47 / 0026 0027）：IR D9「产品功效声称拦截」——食品不得声称降糖/控糖/疗程等功效。实现原来只查「产品与分层/缓解同句」（那是 R32 的事），
    功效声称本身没查。按 D9 名义补：产品提及 + 同句含功效/疗程表述 → 拒。"""
    text = text_of(ctx)
    prods = product_mention(ctx, text)
    if not prods:
        return None
    for s in sentences(text):
        if any(p in s for p in prods) or P(ctx, "pitch"):
            m = EFFICACY_RE.search(s)
            if m:
                return _fail(name, f"产品话术含功效/疗程声称：「{s.strip()[:40]}」（{m.group(0)}）", "食品不得声称降糖、控糖、疗程效果；改为中性描述或删除")
    return None


@rule("D9_产品功效声称拦截")
def d9(ctx):
    return _product_gate(ctx, "D9") or _efficacy_claim(ctx, "D9") or RuleResult.ok()


@rule("R32_产品推荐合规闸")
def r32(ctx):
    r = _product_gate(ctx, "R32")
    if r is not None:
        return r
    text = text_of(ctx)
    if product_mention(ctx, text):
        attached = P(ctx, "disclaimer_attached")
        if attached is None:
            attached = ("固体饮料" in text and "不替代药物" in text) or bool(staged_outbound(ctx).get("disclaimer_attached"))
        if attached is not True:
            return _fail("R32", "产品推荐缺少「固体饮料，不替代药物」尾注", "附固定尾注后再出")
    return RuleResult.ok()


@rule("R51_分层结论默认不可披露患者")
def r51(ctx):
    pid = pid_of(ctx)
    inc = P(ctx, "includes_tier_label")
    if inc is None:
        inc = bool(TIER_RE.search(text_of(ctx) or ""))
    if not inc:
        return RuleResult.ok()
    appr = P(ctx, "disclosure_approved")
    if appr is None:
        appr = profile_of(ctx, pid).get("disclosure_approved")
    if appr is not True:
        return _fail("R51", f"内容含分层/分型结论，患者 {pid or '?'} 的 disclosure_approved 不是 true，不得直推患者", "由医师在面诊后授权披露（disclosure_approved=true）")
    return RuleResult.ok()


@rule("R54_服务话术不得含夜间安全承诺")
def r54(ctx):
    h = hits(text_of(ctx), NIGHT_PROMISE)
    if h:
        return _fail("R54", f"对外话术含夜间安全承诺 {h}，载体与夜间值班未落地前为硬红线", "删除承诺性表述，改为「数据同步后由健管师在工作时间复核」")
    return RuleResult.ok()


@rule("R55_显示口径_没有数据不得说成没有异常")
def r55(ctx):
    pid = pid_of(ctx)
    text = text_of(ctx)
    has = P(ctx, "has_data")
    if has is None and pid:
        today = TODAY.isoformat()
        has = bool(readings_of(ctx, pid, days=1)) or any(str(r.get("time_utc", "")).startswith(today) for r in readings_of(ctx, pid))
    reassuring = P(ctx, "contains_reassuring_wording")
    if reassuring is None:
        reassuring = bool(hits(text, REASSURING))
    if has is not True and reassuring:
        return _fail("R55", "当日没有数据却使用「平稳 / 没有异常」措辞——「没有数据」不得长成「没有异常」", "改为「今天还没有收到数据，请检查同步」")
    return RuleResult.ok()


@rule("C16_禁止发布患者前后对比案例")
def c16(ctx):
    c = P(ctx, "content_id")
    oc = (ctx.get("OutboundContent", str(c)) or {}) if c else {}
    text = text_of(ctx)
    ident = P(ctx, "contains_identifiable_patient")
    if ident is None:
        ident = oc.get("contains_identifiable_patient")
    if ident is None:
        ident = bool(oc.get("patient_ref")) or bool(re.search(r"阿姨|叔|先生|女士|患者|P\d{4}", text))
    comp = P(ctx, "is_before_after_comparison")
    if comp is None:
        comp = oc.get("is_before_after_comparison")
    if comp is None:
        comp = bool(re.search(r"前后对比|对比图|之前.*之后|before.*after", text))
    if ident and comp:
        return _fail("C16", "宣传素材是可识别患者的前后对比案例", "改用匿名聚合数据并走医疗广告审查；个案须书面同意且可撤回")
    return RuleResult.ok()


@rule("C11_分型输出制度层不得当诊断")
def c11(ctx):
    aud = P(ctx, "audience") or P(ctx, "channel") or ""
    public = str(aud) in ("public", "朋友圈", "公众号", "视频号", "抖音", "小红书", "宣传") or P(ctx, "content_id") is not None and _content_type(ctx) == "宣传素材"
    claim = P(ctx, "contains_diagnostic_claim")
    if claim is None:
        claim = bool(DIAG_CERTAIN_RE.search(text_of(ctx) or "")) or ("诊断" in text_of(ctx))
    if public and claim:
        return _fail("C11", "面向公众的内容含「诊断 / 分型确诊」表述", "改为「提示区间」或删除")
    return RuleResult.ok()


@rule("C22_免责声明强制展示")
def c22(ctx):
    if _content_type(ctx) == "告警":
        tpl = _alert_template(ctx)
        if tpl and tpl.get("pre_reviewed_c22") is True:
            return RuleResult.ok()
        return _fail("C22", "告警模板未经免责尾注预审", "在模板预审（R56）时一次性通过 C22")
    attached = P(ctx, "disclaimer_attached")
    excl = P(ctx, "disclaimer_excludes_liability")
    so = staged_outbound(ctx)
    c = P(ctx, "content_id")
    oc = (ctx.get("OutboundContent", str(c)) or {}) if c else {}
    if attached is None:
        attached = so.get("disclaimer_attached", oc.get("disclaimer_attached"))
    if excl is None:
        excl = so.get("disclaimer_excludes_liability", oc.get("disclaimer_excludes_liability", False))
    if attached is not True:
        return _fail("C22", "AI 生成的对外内容缺免责尾注", "附固定尾注「本内容为健康管理建议，非诊疗；用药调整请遵医嘱」")
    if excl is True:
        return _fail("C22", "免责声明试图免除 AI 错误建议造成损害的责任", "删除免责条款中的责任豁免表述")
    return RuleResult.ok()


@rule("R45_紧急告警豁免关键词闸")
def r45(ctx):
    applied = P(ctx, "keyword_gates_applied")
    if _content_type(ctx) == "告警" and applied is True:
        return _fail("R45", "告警话术被套了关键词闸门，会吃掉含「胰岛素/磺脲/停」字样的致命告警", "告警走 R56 模板预审，不走运行时关键词闸")
    return RuleResult.ok()


def _alert(ctx):
    a = P(ctx, "alert_id")
    return (ctx.get("AlertEvent", str(a)) or {}) if a else {}


def _alert_template(ctx):
    t = P(ctx, "template_id")
    if t:
        return ctx.get("AlertTemplate", str(t)) or {}
    level = P(ctx, "level") or _alert(ctx).get("level")
    rows = ctx.find("AlertTemplate", lambda r: r.get("level") == level and r.get("frozen") is True)
    return rows[0] if rows else {}


def _reading(ctx):
    rid = P(ctx, "reading_id")
    return (ctx.get("GlucoseReading", str(rid)) or {}) if rid else {}


def _prev_reading(ctx, r):
    pid, t = r.get("patient_id"), _dt(r.get("time_utc"))
    if not pid or t is None:
        return {}
    rows = [x for x in ctx.find("GlucoseReading", lambda x: x.get("patient_id") == pid and x.get("reading_id") != r.get("reading_id"))
            if _dt(x.get("time_utc")) and _dt(x["time_utc"]) < t]
    return max(rows, key=lambda x: x["time_utc"]) if rows else {}


SAMPLE_GAP_MAX_MIN = 20  # CGM 采样 5–15 min；超过这个间隔的「上一条」不属于同一采样序列，不算连续读数


def _prev_sample(ctx, r, max_gap_min=SAMPLE_GAP_MAX_MIN):
    """实时告警口径的「前一读数」：时间上最近、且与本读数间隔 ≤ max_gap_min 的那条；间隔更长（丢点、断连）→ 视为无前一读数。

    P6（2026-W44 / 0118）：`_prev_reading` 只取时间最近的一条，不看间隔，P0031 02:15 的 3.8 把 2h15m 前 00:00 另一段 L2 事件的
    尾巴 2.2 当成「连续 2 读数确认」，R04a 放行了单点触发——IR 写的是「连续 2 个读数（间隔 ≥5min）」，连续指同一采样序列。
    """
    prev = _prev_reading(ctx, r)
    pt, t = _dt(prev.get("time_utc")), _dt(r.get("time_utc"))
    if not prev or pt is None or t is None or (t - pt).total_seconds() > max_gap_min * 60:
        return {}
    return prev


def _staged_alert(ctx):
    rows = ctx.find("AlertEvent", lambda r: is_staged(ctx, r))
    return rows[-1] if rows else {}


@rule("R03a_Level2低血糖_实时告警")
def r03a(ctx):
    r = _reading(ctx)
    g = _num(r.get("value_mmol"))
    if g is None or g >= 3.0:
        return RuleResult.ok()
    prev = _num(_prev_sample(ctx, r).get("value_mmol"))
    ev = _staged_alert(ctx) or _alert(ctx)
    if prev is None or prev >= 3.0:
        return _fail("R03a", f"G={g} <3.0 但前一读数 {prev} 未确认（无前一读数或间隔 >{SAMPLE_GAP_MAX_MIN}min 不算连续），实时告警须连续 2 个读数确认", "等下一读数确认后再触发")
    if ev and ev.get("level") not in ("高", "危急"):
        return _fail("R03a", f"连续 2 读数 G<3.0，告警级别应为高/危急，实际 {ev.get('level')}", "升级并附 15-15 处置指引")
    return RuleResult.ok()


@rule("R04a_Level1低血糖_实时告警")
def r04a(ctx):
    r = _reading(ctx)
    g = _num(r.get("value_mmol"))
    if g is None or not (3.0 <= g < 3.9):
        return RuleResult.ok()
    prev = _num(_prev_sample(ctx, r).get("value_mmol"))
    if prev is None or prev >= 3.9:
        return _fail("R04a", f"G={g} 在 3.0–3.9 但前一读数 {prev} 未确认（无前一读数或间隔 >{SAMPLE_GAP_MAX_MIN}min 不算连续），须连续 2 个读数", "等下一读数确认")
    return RuleResult.ok()


@rule("R05_即将低血糖预测告警")
def r05(ctx):
    r = _reading(ctx)
    g = _num(r.get("value_mmol"))
    prev = _prev_reading(ctx, r)
    pg, pt, t = _num(prev.get("value_mmol")), _dt(prev.get("time_utc")), _dt(r.get("time_utc"))
    if g is None or pg is None or pt is None or t is None or t <= pt:
        return RuleResult.ok()
    if g < 3.9:  # P2：已低于 3.9 的读数由 R03a/R04a 实时触发管，预测性告警不适用
        return RuleResult.ok()
    slope15 = (g - pg) / ((t - pt).total_seconds() / 60) * 15  # mmol/L per 15 min
    if g < 5.0 and (slope15 <= -1 or g + slope15 / 15 * 20 < 3.9):
        ev = _staged_alert(ctx) or _alert(ctx)
        if not ev or "预测" not in str(ev.get("evidence", "")):
            return _fail("R05", f"G={g} 且 15 分钟斜率 {slope15:.2f}，预计 20 分钟内 <3.9，应发预测性告警（补 10–15g 碳水、暂停运动）", "evidence 标注「预测」")
    return RuleResult.ok()


@rule("R56_告警模板预审冻结")
def r56(ctx):
    tpl = _alert_template(ctx)
    if not tpl:
        return _fail("R56", f"级别「{P(ctx, 'level')}」没有已冻结的告警模板，不允许现场生成告警话术", "先在模板库预审并冻结该级别模板")
    if not (tpl.get("pre_reviewed_c22") is True and tpl.get("pre_reviewed_r54") is True):
        return _fail("R56", f"模板 {tpl.get('template_id')} 预审未同时通过 C22 与 R54", "补模板预审")
    return RuleResult.ok()


@rule("R52_回填读数不得触发实时告警")
def r52(ctx):
    bf = P(ctx, "is_backfill")
    if bf is None:
        bf = (_alert(ctx) or _reading(ctx) or _staged_alert(ctx)).get("is_backfill")
    if bf is True:
        return _fail("R52", "触发读数是回填数据（is_backfill），只进统计通道，不得作为实时告警推送", "撤回该告警；回填期的低血糖进 HypoEpisode 回顾统计")
    return RuleResult.ok()


LEVEL_NUM = {3: "危急", 2: "高", 1: "中", 0: "低"}


@rule("R53_低置信通道不得独立触发危急告警")
def r53(ctx):
    ev = _alert(ctx) or _staged_alert(ctx)
    rd = _reading(ctx)
    level = P(ctx, "level") or ev.get("level")
    if isinstance(level, (int, float)):  # P18a：升级告警 的 level 是数字（IR §4 ParamSpec number），AlertEvent.level 是枚举；按 3→危急 2→高 对齐
        level = LEVEL_NUM.get(int(level), level)
    if level is None and _num(rd.get("value_mmol")) is not None:
        level = "高" if _num(rd["value_mmol"]) < 3.0 else "中"
    if level not in ("危急", "高"):
        return RuleResult.ok()
    ch = P(ctx, "source_channel") or ev.get("source_channel") or rd.get("source_channel")
    conf = _num(P(ctx, "source_confidence")) if P(ctx, "source_confidence") is not None else _num(ev.get("source_confidence", rd.get("source_confidence")))
    confirmed = ev.get("confirmed_by_fingerstick") is True or P(ctx, "confirmed_by_fingerstick") is True
    if confirmed:
        return RuleResult.ok()
    if ch not in TRUSTED_CHANNELS or conf is None or conf < 0.95:
        return _fail("R53", f"来源通道 {ch or '未知'}（置信 {conf}）不得独立触发{level}告警", "先指血复测或健管师加急复核确认后再推")
    return RuleResult.ok()


# P22a：「低血糖风险已结束」式断言（闭环的语义形态，区别于「值已回升」）。否定形态（未脱离 / 没有排除）在 r44 里先剔除。
RISK_CLEARED_RE = re.compile(r"(脱离|排除|消除)\s*(了)?\s*(低血糖)?\s*(的)?\s*(风险|危险)|(风险|危险)\s*(已经|已)?\s*(排除|消除|过去)"
                             r"|(度过|渡过)\s*(了)?\s*危险期")


@rule("R44_高危用药禁止闭环")
def r44(ctx):
    pid = pid_of(ctx)
    act = str(P(ctx, "action_taken") or "")
    # P17a（W47 / 0069）：否定式的闭环提法（「先不闭环」「暂不关闭」「不要结案」）不是闭环请求；去掉被否定的片段后再判
    act_eff = re.sub(r"(先不|暂不|不要|不用|不予|无需|尚未|还没|没有|并未|未|别|不)\s*(闭环|关闭|结案|解除|脱离|排除|消除|close|resolve)", "", act)
    closing = any(k in act_eff for k in ("闭环", "关闭", "resolved", "resolve", "close", "结案", "解除", "恢复正常", "已处理完"))
    # P22a（W50 / 0401）：闭环 = 把告警判为 resolved / HypoState 判为 closed，即宣称「低血糖风险已结束」；IR 允许的只是
    # value_recovered（「值已回升」+ 保持复发观察窗）。「确认脱离低血糖风险」与 0402 的「确认低血糖风险解除」同义，
    # 只是换了动词，此前因不在字面词表里漏放。按「风险已结束」的语义认，而不是逐个补词。
    if not closing:
        closing = bool(RISK_CLEARED_RE.search(act_eff))
    if not closing:
        return RuleResult.ok()
    hs = (ctx.get("HypoState", pid) or {}) if pid else {}
    if hypo_risk(ctx, pid) or hs.get("closure_blocked_reason") or hs.get("prolonged_risk") is True:
        reason = hs.get("closure_blocked_reason") or f"用药含 {[m for m in meds_of(ctx, pid) if any(k in str(m) for k in HYPO_RISK_MEDS)]}"
        return _fail("R44", f"{reason}：磺脲/长效或预混胰岛素使用者的低血糖可持续 24–72 小时，不得按一次复测回升就闭环",
                     "标记为「值已回升」并保持 24h 复发观察窗，由医师决定是否闭环")
    return RuleResult.ok()


@rule("C21_数据留存与审计日志")
def c21(ctx):
    pol = ctx.find("AuditLog", lambda r: r.get("action") == "retention_policy")
    if not pol:
        return _fail("C21", "系统未登记数据留存与审计策略", "在 AuditLog 登记 retention_policy（≥3 年、全操作审计）")
    p = pol[-1]
    if _num(p.get("retention_years")) is None or _num(p.get("retention_years")) < 3 or p.get("audit_enabled") is not True:
        return _fail("C21", f"留存 {p.get('retention_years')} 年 / 审计 {p.get('audit_enabled')}，未满足 ≥3 年与全操作审计", "调整存储策略")
    return RuleResult.ok()


@rule("C20_危急值须系统自动告警并记录响应")
def c20(ctx):
    ev = _alert(ctx)
    if not ev:
        return RuleResult.ok()
    if not ev.get("rule_id") or ev.get("manual_report") is True:
        return _fail("C20", "该告警不是系统阈值自动触发（无 rule_id 或为人工群聊上报）", "危急值须系统自动告警直达值班医师并记录响应时间")
    acks = ctx.find("AlertAck", lambda r: r.get("alert_id") == P(ctx, "alert_id"))
    if P(ctx, "responder") is not None and not any(a.get("responded_at") for a in acks):
        return _fail("C20", "回执未记录响应时间戳", "AlertAck.responded_at 必填")
    return RuleResult.ok()


@rule("R57_15-15三轮无效强制升级就医")
def r57(ctx):
    a = P(ctx, "alert_id")
    acks = ctx.find("AlertAck", lambda r: r.get("alert_id") == a) if a else []
    rounds = _num(P(ctx, "rounds_15_15"))
    if rounds is None:
        rounds = sum(1 for x in acks if "15-15" in str(x.get("action_taken", "")) or "补碳" in str(x.get("action_taken", "")))
    retest = _num(P(ctx, "retest_value"))
    act = str(P(ctx, "action_taken") or "")
    escalated = any(k in act for k in ("升级", "就医", "120", "转诊"))
    if rounds >= 3 and retest is not None and retest < 3.9 and not escalated:
        return _fail("R57", f"15-15 法则已 {int(rounds)} 轮，复测 {retest} 仍 <3.9，必须升级就医/120 并通知紧急联系人", "升级告警至 escalated_emergency")
    pid = pid_of(ctx)
    if pid:
        sym = ctx.find("SymptomTreatmentRecord", lambda r: r.get("patient_id") == pid and r.get("alert_id") == a)
        if sym and _num(sym[-1].get("symptom_duration_min")) and _num(sym[-1].get("symptom_duration_min")) >= 30 and not escalated:
            return _fail("R57", "症状持续 ≥30 分钟仍未升级就医", "升级告警至 escalated_emergency")
    return RuleResult.ok()


def _referral_staged(ctx, pid):
    """本次执行是否已为该患者暂存一条转医师的 ReferralRecord（P7：转介本身就是 R58 / R33 要求的动作，不能反过来拒掉转介）。"""
    return any(is_staged(ctx, r) and r.get("patient_id") == pid and r.get("referred_to") == "医师"
               for r in ctx.find("ReferralRecord", lambda r: r.get("patient_id") == pid))


@rule("R58_Level3严重低血糖强制转诊")
def r58(ctx):
    pid = pid_of(ctx)
    a = P(ctx, "alert_id")
    if not pid:
        return RuleResult.ok()
    sym = ctx.find("SymptomTreatmentRecord", lambda r: r.get("patient_id") == pid and (a is None or r.get("alert_id") in (None, a)))
    l3 = [s for s in sym if any(k in str(s.get("symptom_tag", "")) for k in ("需他人协助", "意识", "抽搐", "昏迷", "叫不醒"))]
    if l3 and not _referral_staged(ctx, pid) and not any("转诊" in str(s.get("treatment_action", "")) or "就医" in str(s.get("treatment_action", "")) for s in l3):
        return _fail("R58", f"Level 3 严重低血糖标记 {[s.get('symptom_tag') for s in l3]}，不看血糖数值，强制就医与医师复核", "触发转介医师 + 紧急联系人")
    return RuleResult.ok()


def _recent_exercise(ctx, pid, hours=24):
    since = datetime.now() - timedelta(hours=hours)
    return [e for e in ctx.find("ContextEvent", lambda r: r.get("patient_id") == pid and r.get("event_type") in ("运动", "exercise"))
            if (_dt(e.get("occurred_at")) or datetime.min) >= since]


def _last_reading(ctx, pid):
    rows = readings_of(ctx, pid, days=2, clean_only=False)
    rows = [r for r in rows if _dt(r.get("time_utc"))]
    return max(rows, key=lambda r: r["time_utc"]) if rows else {}


@rule("R06_快速下降箭头提示")
def r06(ctx):
    ev = _alert(ctx)
    g, slope = _num(P(ctx, "G")) or _num(ev.get("value")), _num(P(ctx, "slope")) or _num(ev.get("trend"))
    if g is not None and slope is not None and slope <= -2 and g < 7.0 and "15 分钟" not in text_of(ctx):
        return _fail("R06", f"双下箭（{slope}）且 G={g} 偏低，提示 15 分钟后复看、勿大量补碳水", "告警附复看提示")
    return RuleResult.ok()


@rule("R08_睡前低值预警")
def r08(ctx):
    pid = pid_of(ctx)
    if not pid or not hypo_risk(ctx, pid):
        return RuleResult.ok()
    prof = profile_of(ctx, pid)
    rows = [r for r in readings_of(ctx, pid, days=1, clean_only=True) if 21 <= (_dt(r["time_utc"]) or datetime.min).hour <= 23]
    if not rows:
        return RuleResult.ok()
    mean = sum(r["value_mmol"] for r in rows) / len(rows)
    floor = {"良好": 5.0, "中等": 5.6, "差": 8.3}.get(prof.get("health_tier"), 5.0) if is_elderly(prof) else 5.0
    if mean < floor:
        return _fail("R08", f"睡前窗口均值 {mean:.1f} 低于分层下限 {floor}，且用药含胰岛素/磺脲", "建议 10–15g 含碳水加餐并复测（不得是黄瓜）")
    return RuleResult.ok()


@rule("R11_严重高血糖")
def r11(ctx):
    pid = pid_of(ctx)
    if not pid:
        return RuleResult.ok()
    rows = sorted((r for r in readings_of(ctx, pid, days=2, clean_only=True) if _dt(r.get("time_utc"))), key=lambda r: r["time_utc"])
    run = 0
    hit = False
    for r in rows:
        run = run + 1 if r["value_mmol"] > 16.7 else 0
        if run >= 4:  # 15 min × 4 = 1h
            hit = True
            break
    if not hit:
        sym = ctx.find("SymptomTreatmentRecord", lambda r: r.get("patient_id") == pid and any(k in str(r.get("symptom_tag", "")) for k in ("口渴", "多尿", "恶心")))
        hit = bool(sym) and any(r["value_mmol"] > 13.9 for r in rows)
    if hit and "血酮" not in text_of(ctx):
        return _fail("R11", "G>16.7 持续 ≥1h（或 >13.9 伴症状），输出须提示查血酮并暂停运动与产品推荐", "草稿加入血酮检查提示，阳性或有症状转就医")
    return RuleResult.ok()


def _summary_metric(ctx, pid, key):
    v = P(ctx, key)
    if v is None:
        v = summary_of(ctx, pid).get({"TIR": "tir_pct", "TBR": "tbr_pct", "TAR_L1": "tar_pct", "TAR_L2": "tar_l2_pct", "CV": "cv_pct", "GMI": "gmi_pct"}.get(key, key))
    return _num(v)


@rule("R13_TAR_L2超标")
def r13(ctx):
    pid = pid_of(ctx)
    v = _summary_metric(ctx, pid, "TAR_L2")
    lim = 10.0 if is_elderly(profile_of(ctx, pid)) else 5.0
    if v is not None and v >= lim:
        return _fail("R13", f"TAR>13.9 占比 {v}% ≥ {lim}%，需按时段/餐次归因交医师", "生成归因分析附在草稿")
    return RuleResult.ok()


@rule("R14_TAR_L1超标")
def r14(ctx):
    v = _summary_metric(ctx, pid_of(ctx), "TAR_L1")
    if v is not None and v >= 25:
        return _fail("R14", f"TAR>10.0 占比 {v}% ≥ 25%", "给饮食/运动/服药时机建议")
    return RuleResult.ok()


@rule("R15_TIR未达标")
def r15(ctx):
    pid = pid_of(ctx)
    v = _summary_metric(ctx, pid, "TIR")
    tgt = tir_target(profile_of(ctx, pid))
    if v is not None and v < tgt:
        return _fail("R15", f"TIR {v}% 未达 {tgt:.0f}%，差距约 {((tgt - v) / 5) * 1.2:.1f} h/天", "建议复诊")
    return RuleResult.ok()


@rule("R16a_波动超标_硬")
def r16a(ctx):
    v = _summary_metric(ctx, pid_of(ctx), "CV")
    if v is not None and v > 36:
        return _fail("R16a", f"CV {v}% > 36%，波动过大", "联动低血糖与餐后归因后再出草稿")
    return RuleResult.ok()


@rule("R16b_波动偏高_软_中国口径")
def r16b(ctx):
    v = _summary_metric(ctx, pid_of(ctx), "CV")
    if v is not None and 33 < v <= 36:
        return _fail("R16b", f"CV {v}% 在 33–36%，波动偏高（中国人群口径）", "提示关注")
    return RuleResult.ok()


@rule("R19_餐后高响应")
def r19(ctx):
    pid = pid_of(ctx)
    mrs = ctx.find("MealResponse", lambda r: r.get("patient_id") == pid) if pid else []
    bad = [m for m in mrs if (_num(m.get("delta_p")) or 0) >= 2.8 or m.get("return_to_baseline") is False]
    if len(bad) >= 2:
        return _fail("R19", f"同类餐高响应 {len(bad)} 次", "给饮食顺序/份量/搭配/餐后步行建议")
    return RuleResult.ok()


@rule("R20_餐后极高响应")
def r20(ctx):
    pid = pid_of(ctx)
    mrs = ctx.find("MealResponse", lambda r: r.get("patient_id") == pid) if pid else []
    if any((_num(m.get("delta_p")) or 0) >= 4.4 for m in mrs[-3:]):
        return _fail("R20", "餐后响应达 TAR L2 级别", "联动 R13 并推送健管师")
    return RuleResult.ok()


@rule("R22_黎明现象")
def r22(ctx):
    pid = pid_of(ctx)
    if not pid:
        return RuleResult.ok()
    rows = readings_of(ctx, pid, days=14, clean_only=True)
    by_day = {}
    for r in rows:
        t = _dt(r.get("time_utc"))
        if t:
            by_day.setdefault(t.date(), []).append((t, r["value_mmol"]))
    days_hit = 0
    for d, pts in by_day.items():
        at3 = [v for t, v in pts if t.hour == 3]
        at7 = [v for t, v in pts if t.hour == 7]
        if at3 and at7 and min(at7) - min(at3) >= 1.1:
            days_hit += 1
    if by_day and days_hit / len(by_day) >= 0.5:
        return _fail("R22", f"14 天中 {days_hit} 天 03:00→07:00 上升 ≥1.1，疑黎明现象", "提示医师调整基础胰岛素或晚餐")
    return RuleResult.ok()


@rule("R23_运动前低值")
def r23(ctx):
    pid = pid_of(ctx)
    if not pid or not _recent_exercise(ctx, pid, 3):
        return RuleResult.ok()
    g = _num(_last_reading(ctx, pid).get("value_mmol"))
    if g is not None and g < 5.0:
        return _fail("R23", f"运动前 G={g} < 5.0", "先补 15–30g 碳水，复测 ≥5.0 再运动")
    return RuleResult.ok()


@rule("R24a_运动前高值查酮体")
def r24a(ctx):
    pid = pid_of(ctx)
    if not pid or not _recent_exercise(ctx, pid, 3):
        return RuleResult.ok()
    g = _num(_last_reading(ctx, pid).get("value_mmol"))
    if g is not None and 13.9 < g <= 16.7 and not ctx.find("KetoneReading", lambda r: r.get("patient_id") == pid):
        return _fail("R24a", f"运动前 G={g} 在 13.9–16.7，尚无酮体记录", "先查酮体，阳性禁运动")
    return RuleResult.ok()


@rule("R24b_运动前极高值一律不宜运动")
def r24b(ctx):
    pid = pid_of(ctx)
    if not pid or not _recent_exercise(ctx, pid, 3):
        return RuleResult.ok()
    g = _num(_last_reading(ctx, pid).get("value_mmol"))
    if g is not None and g > 16.7:
        return _fail("R24b", f"运动前 G={g} > 16.7，一律不宜运动", "拒绝运动建议")
    return RuleResult.ok()


@rule("R25_运动中下降")
def r25(ctx):
    ev = _alert(ctx)
    pid = pid_of(ctx)
    if not pid or not _recent_exercise(ctx, pid, 2):
        return RuleResult.ok()
    g, slope = _num(ev.get("value")), _num(ev.get("trend"))
    if (slope is not None and slope <= -1.5) or (g is not None and g < 4.4):
        return _fail("R25", f"运动中 G={g} / 斜率 {slope}", "提示停止运动并补碳水")
    return RuleResult.ok()


@rule("R26_餐后步行提醒")
def r26(ctx):
    pid = pid_of(ctx)
    if not pid:
        return RuleResult.ok()
    now = datetime.now()
    meals = [m for m in ctx.find("ContextEvent", lambda r: r.get("patient_id") == pid and r.get("event_type") in ("餐食", "meal"))
             if _dt(m.get("occurred_at")) and 15 <= (now - _dt(m["occurred_at"])).total_seconds() / 60 <= 30]
    slope = _num(_alert(ctx).get("trend"))
    if meals and slope is not None and slope > 1:
        return _fail("R26", "餐后 15–30 分钟且血糖上行", "提示走 10–20 分钟")
    return RuleResult.ok()


@rule("R27_运动后延迟低血糖")
def r27(ctx):
    pid = pid_of(ctx)
    if not pid or not hypo_risk(ctx, pid):
        return RuleResult.ok()
    long_ex = [e for e in _recent_exercise(ctx, pid, 24) if (_num(e.get("duration_min")) or 0) >= 45]
    if not long_ex:
        return RuleResult.ok()
    th = _night_threshold_after(ctx, pid)
    if th is not None and th < 4.4:
        return _fail("R27", f"当日运动 ≥45 分钟且用药含胰岛素/磺脲，夜间告警阈值 {th} 应上调至 4.4", "收紧夜间阈值至 4.4，睡前目标 >5.6")
    return RuleResult.ok()


def _night_threshold_after(ctx, pid):
    rows = ctx.find("AlertThreshold", lambda r: r.get("patient_id") == pid and r.get("field") in ("night_low", "夜间低值"))
    staged = [r for r in rows if is_staged(ctx, r)]
    row = staged[-1] if staged else (rows[-1] if rows else None)
    return _num(row.get("current_value")) if row else None


@rule("R46_IAH高危阈值上调且禁止静音")
def r46(ctx):
    pid = pid_of(ctx)
    prof = profile_of(ctx, pid)
    iah = P(ctx, "is_iah_high_risk") if P(ctx, "is_iah_high_risk") is not None else prof.get("is_iah_high_risk")
    if iah is not True:
        return RuleResult.ok()
    field = str(P(ctx, "field") or "")
    th = _num(P(ctx, "alert_threshold")) if P(ctx, "alert_threshold") is not None else (_num(P(ctx, "new_value")) if ("low" in field or "低" in field) else _night_threshold_after(ctx, pid))
    mute = P(ctx, "night_mute_allowed")
    if mute is True or (th is not None and th < 4.4):
        return _fail("R46", f"无感知低血糖高危患者 {pid}：低值阈值 {th} 不得低于 4.4，且不可夜间静音（night_mute_allowed={mute}）", "阈值 ≥4.4 并保留夜间告警")
    return RuleResult.ok()


@rule("R34_HAAF_24小时复发窗")
def r34(ctx):
    pid = pid_of(ctx)
    if not pid:
        return RuleResult.ok()
    l2 = [e for e in episodes_of(ctx, pid, 2) if e.get("level") == "L2" and (_dt(e.get("start_time")) or datetime.min) >= datetime.now() - timedelta(hours=24)]
    if not l2:
        return RuleResult.ok()
    th = _night_threshold_after(ctx, pid)
    if th is not None and th < 4.4:
        return _fail("R34", f"24h 内有 L2 事件（HAAF 高危窗），阈值 {th} 不得低于 4.4", "阈值上调 4.4、夜间人工巡检、当日禁运动建议、医师复核")
    return RuleResult.ok()


@rule("R12_SGLT2i酮症警觉")
def r12(ctx):
    pid = pid_of(ctx)
    if not pid:
        return RuleResult.ok()
    sglt = any("列净" in str(m) for m in meds_of(ctx, pid)) or bool(ctx.find("MedClassHint", lambda r: r.get("patient_id") == pid and r.get("sglt2i") is True))
    if not sglt:
        return RuleResult.ok()
    sym = ctx.find("SymptomTreatmentRecord", lambda r: r.get("patient_id") == pid and any(k in str(r.get("symptom_tag", "")) for k in ("恶心", "乏力", "极低碳水")))
    long_ex = [e for e in _recent_exercise(ctx, pid, 24) if (_num(e.get("duration_min")) or 0) >= 90]
    if (sym or long_ex) and "酮" not in text_of(ctx):
        return _fail("R12", "SGLT2i 使用者出现酮症风险情形，血糖不高也可能 euDKA", "提示查酮体")
    return RuleResult.ok()


@rule("R09_TBR超标触发去强化审查")
def r09(ctx):
    pid = pid_of(ctx)
    if not pid:
        return RuleResult.ok()
    prof, s = profile_of(ctx, pid), summary_of(ctx, pid)
    tbr, tbr2 = _num(s.get("tbr_pct")), _num(s.get("tbr_l2_pct"))
    eps = episodes_of(ctx, pid, 14)
    hit = (tbr is not None and tbr >= tbr_limit(prof, hypo_risk(ctx, pid))) or (tbr2 is not None and tbr2 >= 1) or any(e.get("level") == "L2" for e in eps)
    if not hit:
        return RuleResult.ok()
    so = staged_outbound(ctx)
    if not (so.get("first_page_hypo_table") is True and "低血糖优先" in str(so.get("body", ""))):
        return _fail("R09", f"TBR {tbr}% / L2 {sum(1 for e in eps if e.get('level') == 'L2')} 次已超标，证据包首行须标红「低血糖优先」并把低血糖事件明细表置于第一页", "按 hypo_episode_stats 回顾口径生成明细表")
    return RuleResult.ok()


@rule("R07_夜间低血糖事件")
def r07(ctx):
    pid = pid_of(ctx)
    if not pid:
        return RuleResult.ok()
    night3 = [e for e in episodes_of(ctx, pid, 3) if e.get("night_flag") is True]
    if len(night3) < 2:
        return RuleResult.ok()
    refs = ctx.find("ReferralRecord", lambda r: is_staged(ctx, r) and r.get("patient_id") == pid)
    if not any("晚间用药" in str(r.get("question", "")) for r in refs):
        return _fail("R07", f"3 天内夜间低血糖事件 {len(night3)} 次，须升级医师复核晚间用药与晚餐", "转介问题须含「复核晚间用药与晚餐」")
    return RuleResult.ok()


@rule("R10_低血糖无感知线索")
def r10(ctx):
    pid = pid_of(ctx)
    if not pid:
        return RuleResult.ok()
    l2 = [e for e in episodes_of(ctx, pid, 14) if e.get("level") == "L2"]
    sym = ctx.find("SymptomTreatmentRecord", lambda r: r.get("patient_id") == pid)
    silent = [e for e in l2 if not any(abs((_dt(s.get("recorded_at")) - _dt(e["start_time"])).total_seconds()) <= 2 * 3600 for s in sym if _dt(s.get("recorded_at")))]
    if len(silent) >= 2 and not (staged_outbound(ctx).get("iah_suspected") is True):
        return _fail("R10", f"14 天内 {len(silent)} 次 L2 事件无症状标记，提示评估无感知低血糖", "证据包标注 IAH 线索")
    return RuleResult.ok()


@rule("R50_夜间低覆盖高危用药进临床队列")
def r50(ctx):
    pid = pid_of(ctx)
    if not pid:
        return RuleResult.ok()
    hr = P(ctx, "hypo_risk_med") if P(ctx, "hypo_risk_med") is not None else hypo_risk(ctx, pid)
    nights = _num(P(ctx, "consecutive_low_night_nights"))
    if nights is None:
        nights = _num(summary_of(ctx, pid).get("consecutive_low_night_nights"))
    if nights is None:
        nights = consecutive_low_nights(readings_of(ctx, pid, days=14), 14)
    if not (hr and nights >= 2):
        return RuleResult.ok()
    queue = P(ctx, "queue")
    if queue is None:
        refs = ctx.find("ReferralRecord", lambda r: is_staged(ctx, r) and r.get("patient_id") == pid)
        queue = refs[-1].get("queue") if refs else None
    if queue != "clinical_hypo":
        return _fail("R50", f"胰岛素/磺脲使用者连续 {int(nights)} 晚夜间有效率 <50%，须进临床队列低血糖分支（不是挽留队列）", "ReferralRecord.queue = clinical_hypo")
    return RuleResult.ok()


@rule("R59_老年非典型症状疑似低血糖")
def r59(ctx):
    pid = pid_of(ctx)
    prof = profile_of(ctx, pid)
    if not pid or not is_elderly(prof):
        return RuleResult.ok()
    sym = [s for s in ctx.find("SymptomTreatmentRecord", lambda r: r.get("patient_id") == pid)
           if any(k in str(s.get("symptom_tag", "")) for k in ("跌倒", "意识模糊", "叫不醒", "胡言乱语"))]
    if not sym:
        return RuleResult.ok()
    rows = readings_of(ctx, pid, days=14, clean_only=True)
    for s in sym:
        t = _dt(s.get("recorded_at"))
        near = [r for r in rows if t and _dt(r.get("time_utc")) and abs((_dt(r["time_utc"]) - t).total_seconds()) <= 3600]
        if any(r["value_mmol"] < 4.4 for r in near) and staged_outbound(ctx).get("atypical_hypo_suspected") is not True:
            return _fail("R59", f"老年非典型症状「{s.get('symptom_tag')}」同期 CGM 处于临界低值区间，疑似低血糖诱因", "推医师复核并在证据包标注")
    return RuleResult.ok()


def _credential_of(ctx, holder):
    if not holder:
        return None
    rows = ctx.find("Credential", lambda r: r.get("holder") == holder or r.get("holder_id") == holder)
    return rows[-1] if rows else None


def _signer(ctx):
    return P(ctx, "signer_id") or P(ctx, "assessor_id") or P(ctx, "changed_by")


@rule("D11a_签发人资质失效自动冻结")
def d11a(ctx):
    signer = _signer(ctx)
    cred = _credential_of(ctx, signer) if signer else None
    if cred is None and signer:
        cred = _credential_of(ctx, ctx.actor.id)
    if cred is None and not signer:
        cred = _credential_of(ctx, ctx.actor.id)
        if cred is None:
            if ctx.actor.role in ("医师", "注册营养师", "运动康复师", "康复师", "医生"):
                return RuleResult.ok()  # 无凭证台账记录时退回角色门：仅签发类角色可过
            return _fail("D11a", f"调用者 {ctx.actor.id}（{ctx.actor.role}）没有签发资质记录", "由持有效执业资质的医师/注册营养师签发")
    if cred is None:
        return _fail("D11a", f"签发人 {signer} 没有资质记录", "补录 Credential 或改由有资质人员签发")
    exp = _dt(cred.get("expiry_date"))
    if cred.get("status") not in (None, "valid", "expiring") or (exp is not None and exp.date() < TODAY):
        return _fail("D11a", f"签发人 {signer or ctx.actor.id} 的{cred.get('credential_type')}（{cred.get('registration_no')}）已于 {cred.get('expiry_date')} 到期（台账状态 {cred.get('status')}），签发权限自动冻结",
                     "任务转有资质人员；资质更新后解冻")
    return RuleResult.ok()


_SIGN_SCOPE = {"执业医师": None, "医师": None, "注册营养师": {"营养", "教育", "综合"}, "运动康复师": {"运动", "教育"}, "康复师": {"运动", "教育"}, "健管师": {"教育"}}


@rule("D12_签发人归属分流")
def d12(ctx):
    d = P(ctx, "draft_id")
    draft = (ctx.get("PlanDraft", str(d)) or {}) if d else {}
    cat = draft.get("category")
    if cat is None:
        c = str(draft.get("content", ""))
        cat = "用药" if any(x in c for x in DRUG_NAMES) else "分型" if TIER_RE.search(c) else "运动" if "运动" in c and "饮食" not in c else "营养" if "饮食" in c or "营养" in c else "综合"
    signer = _signer(ctx)
    cred = _credential_of(ctx, signer) if signer else _credential_of(ctx, ctx.actor.id)
    ctype = (cred or {}).get("credential_type") or ctx.actor.role
    scope = _SIGN_SCOPE.get(ctype, set())
    if scope is None:
        return RuleResult.ok()
    if cat not in scope:
        return _fail("D12", f"「{cat}」类方案不能由{ctype}签发", "用药/分型 → 医师；营养 → 注册营养师；运动 → 康复师起草 + 医师双签；教育 → 健管师")
    if cat == "运动" and not ctx.find("ReviewEvidence", lambda r: r.get("plan_id") == d and r.get("physician_screened") is True):
        return _fail("D12", "运动类方案缺医师运动禁忌筛查记录", "医师筛查后双签发")
    return RuleResult.ok()


@rule("D13_签发反橡皮图章检测")
def d13(ctx):
    signer = _signer(ctx) or ctx.actor.id
    evs = sorted(ctx.find("ReviewEvidence", lambda r: r.get("signer_id") == signer), key=lambda r: str(r.get("opened_at", "")))
    recent = evs[-10:]
    quick = [e for e in recent if _num(e.get("dwell_time")) is not None and _num(e.get("dwell_time")) < 20]
    zero_diff = sum(1 for e in recent if not e.get("diff"))
    if quick or (len(recent) >= 10 and zero_diff >= 10):
        return _fail("D13", f"签发人 {signer} 近期 {len(quick)} 份停留 <20 秒、{zero_diff} 份零修改", "标 review_suspicious，触发质控复核")
    return RuleResult.ok()


@rule("C9_AI方案禁止直接推送")
def c9(ctx):
    p = P(ctx, "plan_id")
    ps = (ctx.get("PlanSigned", str(p)) or {}) if p else {}
    if not ps:
        return _fail("C9", f"{p} 不是已签发方案（无 PlanSigned），AI 草稿禁止直推患者", "先由医师或注册营养师签发")
    cred = _credential_of(ctx, ps.get("signer_id"))
    if cred is None or cred.get("status") not in (None, "valid", "expiring") or not ps.get("signed_at") or not ps.get("evidence_snapshot"):
        return _fail("C9", "签发记录不完整（签发人资质/时间戳/依据快照）", "补齐后推送")
    return RuleResult.ok()


@rule("C6_群内数据最小可见范围")
def c6(ctx):
    text = text_of(ctx)
    raw_vals = re.findall(r"\d+\.\d\s*mmol", text)
    if raw_vals or _drug_dose_sentences(text):
        return _fail("C6", "群内内容含未脱敏原始血糖值或药名剂量", "群内只推脱敏卡片，明细在平台内可见")
    return RuleResult.ok()


@rule("C19_线上随访边界")
def c19(ctx):
    text = text_of(ctx)
    referral = re.search(r"(建议|请|需要|尽快|最好).{0,8}(去医院|就医|复诊|找医生|转诊|挂号)", text)  # P4：异常转介在允许范围内
    if re.search(r"诊断|开处方|处方|开药|调药方案", text) and not referral:
        return _fail("C19", "随访内容超出健康教育/生活方式/监测提醒/异常转介范围", "定性为健康管理随访；超范围须互联网诊疗备案 + 等保三级")
    return RuleResult.ok()


def _device_license_holder(ctx):
    return [c for c in ctx.find("Credential", lambda r: "医疗器械经营" in str(r.get("credential_type", "")) and r.get("status") in (None, "valid"))]


@rule("C1_器械经营资质闸")
def c1(ctx):
    cat = str(P(ctx, "category") or "")
    s = P(ctx, "sku_id")
    sku = (ctx.get("ProductSku", str(s)) or {}) if s else {}
    text = text_of(ctx)
    is_device = any(k in cat for k in ("器械", "CGM", "传感器")) or sku.get("category") == "器械引用" or (hits(text, DEVICE_WORDS) and hits(text, SELL_WORDS))
    if not is_device:
        return RuleResult.ok()
    if not _device_license_holder(ctx):
        return _fail("C1", "门店与平台均无《医疗器械经营许可证》（三类），CGM 交易只能由持证厂商或经销商完成", "门店纯引流不碰货不收款；SKU 改为「器械引用」指向持证方")
    return RuleResult.ok()


@rule("C2_网络销售备案与证照公示")
def c2(ctx):
    cat = str(P(ctx, "category") or "")
    s = P(ctx, "sku_id")
    sku = (ctx.get("ProductSku", str(s)) or {}) if s else {}
    if not (any(k in cat for k in ("器械", "CGM", "传感器")) or sku.get("category") == "器械引用"):
        return RuleResult.ok()
    if not ctx.find("Credential", lambda r: "网络销售备案" in str(r.get("credential_type", "")) and r.get("status") in (None, "valid")):
        return _fail("C2", "器械类 SKU 无网络销售备案与证照公示", "单独频道并公示经营许可证与注册证")
    return RuleResult.ok()


@rule("C14_产品标签合规校验")
def c14(ctx):
    s = P(ctx, "sku_id")
    sku = (ctx.get("ProductSku", str(s)) or {}) if s else {}
    cat = str(P(ctx, "category") or sku.get("category") or "")
    if cat == "食品" and sku.get("label_verified") is not True:
        return _fail("C14", f"食品 SKU {s} 未核验「固体饮料」字号与警示语", "采购前核验标签，不合格不上架")
    return RuleResult.ok()


@rule("C13_服务与产品物理分离")
def c13(ctx):
    contents = P(ctx, "contents")
    if isinstance(contents, (list, tuple)):
        text = "\n".join(str(x) for x in contents)
        if product_mention(ctx, text):
            return _fail("C13", f"服务包内容含产品实体 {product_mention(ctx, text)}", "服务包只含服务与器械租用；食品由医师在 HIS 内单独开具、单独收款")
    if P(ctx, "bundle_with_service") is True:
        return _fail("C13", "产品推荐与服务包捆绑", "分开收款与宣传")
    return RuleResult.ok()


@rule("C15_服务包禁止捆绑分佣")
def c15(ctx):
    cfg = str(P(ctx, "commission_config") or "")
    if any(k in cfg for k in ("医务", "医师", "医生", "营养师", "健管师")):
        return _fail("C15", "分佣配置关联医务人员账号", "对医务人员不设产品销售提成")
    return RuleResult.ok()


@rule("C17_机构与门诊命名合规")
def c17(ctx):
    text = text_of(ctx) + " " + str(P(ctx, "org_name") or "")
    if re.search(r"逆转中心|治愈中心|根治", text):
        return _fail("C17", "名称含「逆转/治愈」等暗示疗效用语，与卫健命名规范冲突", "改为「糖尿病（特色）门诊 / 代谢健康管理中心」")
    return RuleResult.ok()


@rule("C3_敏感个人信息单独同意")
def c3(ctx):
    pid = pid_of(ctx)
    if not pid:
        return _fail("C3", "无法确定数据主体（缺 patient_id）", "摄入载荷须带 patient_id")
    cons = [c for c in ctx.find("ConsentRecord", lambda r: r.get("patient_id") == pid) if c.get("state", "granted") != "revoked"]
    need = {"血糖数据"}
    ok = [c for c in cons if need <= set(c.get("scope_items") or []) and c.get("signed_at")]
    if not ok:
        return _fail("C3", f"患者 {pid} 未取得血糖数据的单独同意（逐项勾选 + 电子签名 + 时间戳），零数据摄入", "先完成「签署单独同意书」，服务挂起")
    return RuleResult.ok()


@rule("C4_数据用于产品推荐须单独同意")
def c4(ctx):
    pid = pid_of(ctx)
    cons = [c for c in ctx.find("ConsentRecord", lambda r: r.get("patient_id") == pid) if c.get("state", "granted") != "revoked"] if pid else []
    if not any("营销推荐" in (c.get("scope_items") or []) for c in cons):
        return _fail("C4", f"患者 {pid} 未单独勾选「营销推荐」用途", "单独同意后再生成推荐，并提供关闭与人工复核入口")
    return RuleResult.ok()


def _pressure_artifact(ctx, r):
    """R02 口径：单点 <3.0 但前后 10min 内回升 ≥1.5，或 15min 内跳变 >5.0 → 传感器压迫伪差。返回命中描述或 None。"""
    g, t, pid = _num(r.get("value_mmol")), _dt(r.get("time_utc")), r.get("patient_id")
    if g is None or t is None or g >= 3.0 or not pid:
        return None
    rows = [x for x in ctx.find("GlucoseReading", lambda x: x.get("patient_id") == pid and x.get("reading_id") != r.get("reading_id"))
            if _dt(x.get("time_utc")) and _num(x.get("value_mmol")) is not None]
    near10 = [x for x in rows if abs((_dt(x["time_utc"]) - t).total_seconds()) <= 600]
    near15 = [x for x in rows if abs((_dt(x["time_utc"]) - t).total_seconds()) <= 900]
    if any(_num(x["value_mmol"]) - g >= 1.5 for x in near10):
        return "前后 10min 内回升 ≥1.5"
    if any(abs(_num(x["value_mmol"]) - g) > 5.0 for x in near15):
        return "15min 内跳变 >5.0"
    return None


@rule("R02_传感器压迫伪差识别")
def r02(ctx):
    r = P(ctx, "reading_candidate")
    if not isinstance(r, dict):
        rid = P(ctx, "reading_id")
        r = ctx.get("GlucoseReading", str(rid)) if rid else None
    if not isinstance(r, dict):
        return RuleResult.ok()
    hit = _pressure_artifact(ctx, r)
    if hit:
        return _fail("R02", f"读数 {r.get('reading_id')}={r.get('value_mmol')} 疑为传感器压迫伪差（{hit}），不计入低血糖事件", "标 noise；伪差判定不抑制 hard 级告警")
    return RuleResult.ok()


@rule("R36_active率超100自检")
def r36(ctx):
    """IR check：active_pct <= 100。P8：去重与通道仲裁没有 active_pct 参数——按候选读数所属患者近 14 天（含本次暂存）自算，>100% 即去重失效。"""
    a = _num(P(ctx, "active_pct"))
    if a is None:
        pid = pid_of(ctx) or (P(ctx, "reading_candidate", "patient_id") if isinstance(P(ctx, "reading_candidate"), dict) else None)
        if not pid:
            return RuleResult.ok()
        rows = readings_of(ctx, str(pid), days=14, clean_only=True)
        a = round(100.0 * len(rows) / (14 * 96), 1)
    if a > 100:
        return _fail("R36", f"active% = {a} > 100，去重失效信号", "停止入库，检查 dedup_key 与通道仲裁")
    return RuleResult.ok()


@rule("R48_去重键必须用传感器序号")
def r48(ctx):
    rows = P(ctx, "raw_payload", "readings") or []
    c = P(ctx, "reading_candidate")
    if isinstance(c, dict):
        rows = list(rows) + [c]
    for r in rows:
        if not isinstance(r, dict):
            continue
        sn, dk = str(r.get("sensor_serial") or ""), str(r.get("dedup_key") or "")
        # P9a（W46 / 0354–0364）：IR R48 的三种形态——有序号没键 → handler 按序号派生；无序号无键 → ±90 秒容差兜底并置 weak_dedup；
        # 只有「给了键却不是序号构成」（厂商记录 ID、单独 device_time）才是违规。
        if not dk:
            continue
        if not sn or not dk.startswith(sn):
            if r.get("weak_dedup") is True and not sn:
                continue
            return _fail("R48", f"读数 {r.get('reading_id')} 的 dedup_key 不是「传感器序号 + 序号」", "无序号时才允许 ±90 秒容差兜底并置 weak_dedup")
    return RuleResult.ok()


@rule("R31_妊娠模式切换")
def r31(ctx):
    prof = profile_of(ctx)
    preg = P(ctx, "pregnant") if P(ctx, "pregnant") is not None else prof.get("pregnant")
    if preg is not True:
        return RuleResult.ok()
    tp = P(ctx, "target_profile") or prof.get("target_profile")
    tier_enabled = P(ctx, "service_tier_enabled")
    if tp != "pregnancy" or tier_enabled is not False:
        return _fail("R31", "妊娠患者须切 pregnancy 目标区间并禁用德心分层与营养产品推荐", "target_profile=pregnancy，service_tier_enabled=false")
    return RuleResult.ok()


@rule("R18_CGM服务分层_内部标签")
def r18(ctx):
    pid = pid_of(ctx)
    prof, s = profile_of(ctx, pid), summary_of(ctx, pid)
    if is_elderly(prof) or prof.get("pregnant") is True or s.get("confounded_window") is True:
        return _fail("R18", "elderly / pregnancy / 混杂窗口不做德心分层", "只出趋势描述")
    return RuleResult.ok()


def _remission_criteria(ctx, pid):
    """返回 (meets, detail)。停药 ≥90 天 ∧ 无降糖药 ∧ (HbA1c<6.5 近 3 月 NGSP 或 GMI<6.5 且四条前提)。"""
    clock = ctx.get("RemissionClock", pid) or {}
    d0 = _dt(clock.get("day0"))
    days = (datetime.combine(TODAY, datetime.min.time()) - d0).days if d0 else None
    meds = [m for m in meds_of(ctx, pid) if any(k in str(m) for k in DRUG_NAMES)]
    labs = [l for l in ctx.find("LabResult", lambda r: r.get("patient_id") == pid and str(r.get("method", "")).lower().startswith("hba1c"))
            if _dt(l.get("measured_at")) and (datetime.combine(TODAY, datetime.min.time()) - _dt(l["measured_at"])).days <= 92]
    hba1c = min((_num(l.get("value")) for l in labs if _num(l.get("value")) is not None), default=None)
    s = summary_of(ctx, pid)
    gmi = _num(s.get("gmi_pct"))
    premises = (s.get("sufficiency_ok") is True and s.get("brand_changed") is not True and s.get("tz_uncertain") is not True
                and s.get("metric_provenance") == "self_computed")
    method = "HbA1c" if hba1c is not None else ("GMI" if (gmi is not None and premises) else None)
    glyc_ok = (hba1c is not None and hba1c < 6.5) or (hba1c is None and gmi is not None and premises and gmi < 6.5)
    meets = bool(days is not None and days >= 90 and clock.get("status") == "running" and not meds and glyc_ok)
    return meets, {"days": days, "meds": meds, "hba1c": hba1c, "gmi": gmi, "premises": premises, "method": method}


@rule("R29_缓解判定")
def r29(ctx):
    pid = pid_of(ctx)
    if not pid:
        return RuleResult.ok()
    meets, d = _remission_criteria(ctx, pid)
    staged = ctx.find("RemissionAssessment", lambda r: is_staged(ctx, r) and r.get("patient_id") == pid)
    claimed = staged[-1].get("status") if staged else None
    if claimed == "in_remission" and not meets:
        return _fail("R29", f"缓解判定不成立：停药 {d['days']} 天、在用降糖药 {d['meds']}、HbA1c {d['hba1c']} / GMI {d['gmi']}（前提 {d['premises']}）", "禁用「缓解/逆转」字样；继续观察")
    if REMISSION_RE.search(text_of(ctx) or "") and not meets:
        return _fail("R29", "未达缓解标准却使用「缓解/逆转」字样", "删除该表述")
    return RuleResult.ok()


@rule("R17_GMI与HbA1c不一致")
def r17(ctx):
    pid = pid_of(ctx)
    if not pid:
        return RuleResult.ok()
    _, d = _remission_criteria(ctx, pid)
    if d["hba1c"] is not None and d["gmi"] is not None and d["premises"] and abs(d["gmi"] - d["hba1c"]) >= 0.5:
        return _fail("R17", f"GMI {d['gmi']} 与实测 HbA1c {d['hba1c']} 偏差 ≥0.5%，以实测为准，标注可能贫血或血红蛋白变异", "报告标注")
    return RuleResult.ok()


@rule("R30_缓解适宜人群筛选_ABCD")
def r30(ctx):
    pid = pid_of(ctx)
    if not pid:
        return RuleResult.ok()
    prof = profile_of(ctx, pid)
    labs = ctx.find("LabResult", lambda r: r.get("patient_id") == pid)
    val = lambda m: next((_num(l.get("value")) for l in labs if str(l.get("method", "")).lower() == m.lower()), None)
    a = val("GADA") is not None and val("GADA") <= 1.0
    bm = ctx.find("BodyMeasurement", lambda r: r.get("patient_id") == pid)
    waist = _num(bm[-1].get("waist")) if bm else None
    bmi = _num(bm[-1].get("bmi")) if bm else None
    b = (bmi is not None and bmi >= 25) or (waist is not None and waist > (85 if prof.get("sex") == "F" else 90))
    c = (val("C-peptide fasting") or 0) >= 1.1 and (val("C-peptide 2h") or 0) >= 2.5
    dx = _dt(prof.get("diagnosed_at"))
    d = dx is not None and (datetime.combine(TODAY, datetime.min.time()) - dx).days <= 5 * 365
    if not (a and b and c and d):
        return _fail("R30", f"ABCD 未全满足：抗体阴性 {a} / 体型 {b} / C 肽 {c} / 病程≤5 年 {d}", "不进缓解路径")
    return RuleResult.ok()


@rule("R33_停药观察期反弹预警")
def r33(ctx):
    pid = pid_of(ctx)
    if not pid:
        return RuleResult.ok()
    clock = ctx.get("RemissionClock", pid) or {}
    if clock.get("status") != "running":
        return RuleResult.ok()
    s = summary_of(ctx, pid)
    rows = readings_of(ctx, pid, days=7, clean_only=True)
    m7 = metrics_from_values([r["value_mmol"] for r in rows])
    signals = []
    if m7["mean"] is not None and m7["mean"] >= 8.6:
        signals.append(f"7 天平均葡萄糖 {m7['mean']} ≥ 8.6")
    if _num(s.get("gmi_pct")) is not None and _num(s.get("gmi_pct")) >= 7.0:
        signals.append(f"GMI {s.get('gmi_pct')} ≥ 7.0")
    if m7["tar"] is not None and m7["tar"] >= 50:
        signals.append(f"TAR {m7['tar']}% ≥ 50%")
    if any(True for e in episodes_of(ctx, pid, 14)):
        signals.append("停药后低血糖事件")
    if signals and not _referral_staged(ctx, pid):
        return _fail("R33", f"停药观察期反弹预警：{signals}", "立即推医师并触发病因排查")
    return RuleResult.ok()


# ----------------------------------------------------------------------------- Function 实现（只读派生）
FUNCTIONS = {}


def function(name):
    def deco(fn):
        FUNCTIONS[name] = fn
        return fn
    return deco


def _window_values(ctx):
    pid = pid_of(ctx)
    days = int(_num(P(ctx, "days")) or 14)
    prof = profile_of(ctx, pid)
    rows = readings_of(ctx, pid, days=days, clean_only=True) if pid else []
    return [r["value_mmol"] for r in rows], prof, rows, days


for _name, _key in (("TIR", "tir"), ("TAR_L1", "tar"), ("TAR_L2", "tar_l2"), ("TBR_L1", "tbr"), ("TBR_L2", "tbr_l2"),
                    ("MeanGlucose", "mean"), ("GMI", "gmi"), ("CV", "cv"), ("SD", "sd")):
    def _mk(key):
        def fn(ctx):
            vals, prof, _, _ = _window_values(ctx)
            return metrics_from_values(vals, prof.get("target_profile") or "adult")[key]
        return fn
    FUNCTIONS[_name] = _mk(_key)


@function("active_pct")
def fn_active(ctx):
    _, _, rows, days = _window_values(ctx)
    return round(min(100.0, 100.0 * len(rows) / (days * 96)), 1)


@function("sufficiency_ok")
def fn_suff(ctx):
    _, _, rows, days = _window_values(ctx)
    return days >= 14 and fn_active(ctx) >= 70


@function("nocturnal_coverage_pct")
def fn_night(ctx):
    _, _, rows, days = _window_values(ctx)
    return nocturnal_coverage(rows, days)


@function("hypo_episode_stats")
def fn_eps(ctx):
    _, _, rows, _ = _window_values(ctx)
    eps = episodes_from_readings(rows)
    return {"count": len(eps), "l2": sum(1 for e in eps if e["level"] == "L2"), "night": sum(1 for e in eps if e["night_flag"]),
            "total_minutes": sum(e["duration_min"] for e in eps)}


@function("hypo_risk_med")
def fn_hrm(ctx):
    return hypo_risk(ctx, pid_of(ctx))


@function("target_profile_of")
def fn_tp(ctx):
    prof = profile_of(ctx)
    if prof.get("pregnant") is True:
        return "pregnancy"
    return "elderly" if is_elderly(prof) else "adult"


# ----------------------------------------------------------------------------- Action handler 实现
ACTIONS = {}


def action(name):
    def deco(fn):
        ACTIONS[name] = fn
        return fn
    return deco


def _now():
    return datetime.now().isoformat(timespec="minutes")


DISCLAIMER = "本内容为健康管理建议，非诊疗行为；用药调整请遵医嘱。"


@action("生成方案草稿")
def act_draft(ctx):
    pid = str(ctx.params["patient_id"])
    prof, s = profile_of(ctx, pid), summary_of(ctx, pid)
    direction = _direction(ctx) or "维持"
    tir, tbr, tar, cv = s.get("tir_pct"), s.get("tbr_pct"), s.get("tar_pct"), s.get("cv_pct")
    lines = [f"【{pid} 本期方案草稿 · 方向：{direction}】",
             f"近 {s.get('days', '?')} 天 TIR {tir}% / TBR {tbr}% / TAR {tar}% / CV {cv}%（有效数据 {s.get('active_pct')}%，夜间覆盖 {s.get('nocturnal_coverage_pct')}%）。"]
    if tbr is not None and tbr >= tbr_limit(prof, hypo_risk(ctx, pid)):
        lines.append("低血糖优先：先处理低血糖时段，本期不加强降糖。")
    if tar is not None and tar >= 25:
        lines.append("餐后高值较多：建议调整进餐顺序（先菜后饭）、控制主食份量，餐后 15–30 分钟步行 10–20 分钟。")
    if cv is not None and cv > 33:
        lines.append("波动偏高：固定三餐时间与份量，记录餐食以便餐后归因。")
    lines.append("睡前加餐如需要请选含碳水 10–15g 的食物并复测。")
    lines.append(DISCLAIMER)
    content = "\n".join(lines)
    key = f"draft-{pid}-{s.get('window_end', TODAY.isoformat())}"
    ctx.stage_write("PlanDraft", key, {"patient_id": pid, "content": content, "template_version": "fde-0.1", "med_interaction_routed": False,
                                       "direction": direction, "category": "综合", "_staged": exec_token(ctx)})
    ctx.set_confidence(0.9 if s else 0.6)
    ctx.add_evidence(summary_id=s.get("summary_id"), tir=tir, tbr=tbr, tar=tar, cv=cv)
    ctx.emit_effect("workitem", on="committed", template="方案签发任务", draft_id=key, reviewer="医师/注册营养师")


@action("签发方案")
def act_sign(ctx):
    d = str(ctx.params["draft_id"])
    draft = ctx.get("PlanDraft", d) or {}
    signer = str(ctx.params["signer_id"])
    key = f"plan-{d}"
    dwell = _num(P(ctx, "dwell_time"))
    ctx.stage_write("ReviewEvidence", f"re-{key}", {"plan_id": key, "opened_at": _now(), "agp_expand_count": P(ctx, "agp_expand_count") or 1,
                                                    "dwell_time": dwell, "diff": P(ctx, "diff") or "", "review_suspicious": bool(dwell is not None and dwell < 20),
                                                    "signer_id": signer, "_staged": exec_token(ctx)})
    ctx.stage_write("PlanSigned", key, {"patient_id": draft.get("patient_id"), "content_snapshot": draft.get("content", ""), "signer_id": signer,
                                        "signed_at": _now(), "evidence_snapshot": f"summary:{(summary_of(ctx, draft.get('patient_id')) or {}).get('summary_id')}",
                                        "review_evidence_ref": f"re-{key}", "evidence_stale": False, "decision": ctx.params.get("decision"), "_staged": exec_token(ctx)})
    ctx.set_confidence(1.0)
    ctx.add_evidence(draft_id=d, signer=signer)


def _threshold_row(ctx, pid, field):
    rows = ctx.find("AlertThreshold", lambda r: r.get("patient_id") == pid and r.get("field") == field and not is_staged(ctx, r))
    return rows[-1] if rows else None


@action("收紧告警阈值")
def act_tighten(ctx):
    pid, field = str(ctx.params["patient_id"]), str(ctx.params["field"])
    row = _threshold_row(ctx, pid, field) or {"threshold_id": f"th-{pid}-{field}", "current_value": 3.9, "default_value": 3.9, "safe_direction": "收紧"}
    before = _num(row.get("current_value"))
    after = _num(P(ctx, "new_value"))
    if after is None:
        after = round((before or 3.9) + 0.5, 1)
    # 「收紧」= 更早报警：低值类阈值上调、高值类阈值下调；方向不对就不动
    low_field = "low" in field or "低" in field
    if before is not None and ((low_field and after < before) or (not low_field and after > before)):
        after = before
    ctx.stage_write("AlertThreshold", row.get("threshold_id", f"th-{pid}-{field}"),
                    {**{k: v for k, v in row.items() if k != "_staged"}, "patient_id": pid, "field": field, "current_value": after, "safe_direction": "收紧", "_staged": exec_token(ctx)})
    ctx.stage_write("ThresholdChangeLog", f"tcl-{pid}-{field}-{_now()}", {"patient_id": pid, "changed_by": ctx.actor.id, "trigger_rule": ctx.params.get("trigger_rule"),
                                                                           "before": before, "after": after, "effective_window": "即时", "_staged": exec_token(ctx)})
    ctx.emit_effect("notify", on="committed", to="医师", message=f"{pid} {field} 阈值 {before}→{after}")
    ctx.set_confidence(1.0)


@action("放宽告警阈值")
def act_loosen(ctx):
    pid, field = str(ctx.params["patient_id"]), str(ctx.params["field"])
    row = _threshold_row(ctx, pid, field) or {"threshold_id": f"th-{pid}-{field}", "current_value": 3.9, "default_value": 3.9, "safe_direction": "收紧"}
    before, after = _num(row.get("current_value")), _num(ctx.params["new_value"])
    ctx.stage_write("AlertThreshold", row.get("threshold_id", f"th-{pid}-{field}"),
                    {**{k: v for k, v in row.items() if k != "_staged"}, "patient_id": pid, "field": field, "current_value": after, "safe_direction": "放宽", "_staged": exec_token(ctx)})
    ctx.stage_write("ThresholdChangeLog", f"tcl-{pid}-{field}-{_now()}", {"patient_id": pid, "changed_by": ctx.actor.id, "trigger_rule": "医师手动放宽",
                                                                           "before": before, "after": after, "effective_window": "即时", "_staged": exec_token(ctx)})
    ctx.set_confidence(1.0)


@action("生成去强化证据工单")
def act_deintensify(ctx):
    pid = str(ctx.params["patient_id"])
    prof, s = profile_of(ctx, pid), summary_of(ctx, pid)
    eps = episodes_of(ctx, pid, 14)
    l2 = [e for e in eps if e.get("level") == "L2"]
    night3 = [e for e in episodes_of(ctx, pid, 3) if e.get("night_flag")]
    hr = hypo_risk(ctx, pid)
    nights = _num(s.get("consecutive_low_night_nights"))
    if nights is None:
        nights = consecutive_low_nights(readings_of(ctx, pid, days=14), 14)
    sym = ctx.find("SymptomTreatmentRecord", lambda r: r.get("patient_id") == pid)
    silent = [e for e in l2 if not any(_dt(x.get("recorded_at")) and abs((_dt(x["recorded_at"]) - _dt(e["start_time"])).total_seconds()) <= 7200 for x in sym)]
    atyp = [x for x in sym if any(k in str(x.get("symptom_tag", "")) for k in ("跌倒", "意识模糊", "叫不醒", "胡言乱语"))]
    table = "\n".join(f"  {e.get('start_time')}～{e.get('end_time')} 最低 {e.get('min_value')} {e.get('level')}{'（夜间）' if e.get('night_flag') else ''}" for e in eps) or "  （无）"
    body = "\n".join([
        f"★ 低血糖优先 —— {pid} 去强化证据包（{s.get('window_start')}～{s.get('window_end')}）",
        f"第一页·低血糖事件明细（hypo_episode_stats 回顾口径，{len(eps)} 次，其中 L2 {len(l2)} 次、夜间 {sum(1 for e in eps if e.get('night_flag'))} 次）：",
        table,
        f"14 天指标：TIR {s.get('tir_pct')}% / TBR {s.get('tbr_pct')}%（L2 {s.get('tbr_l2_pct')}%）/ TAR {s.get('tar_pct')}% / CV {s.get('cv_pct')}% / 夜间覆盖 {s.get('nocturnal_coverage_pct')}%",
        f"用药清单：{meds_of(ctx, pid)}（高危用药：{'是' if hr else '否'}）",
        f"3 天内夜间事件 {len(night3)} 次" + ("，请复核晚间用药与晚餐" if len(night3) >= 2 else ""),
        f"无症状 L2 事件 {len(silent)} 次" + ("，提示评估无感知低血糖（IAH）" if len(silent) >= 2 else ""),
        (f"老年非典型症状 {[x.get('symptom_tag') for x in atyp]} 同期临界低值，疑似低血糖诱因" if atyp else ""),
        "14 天曲线：见附件 AGP。", DISCLAIMER,
    ])
    question = "请做降糖药去强化审查" + ("；复核晚间用药与晚餐" if len(night3) >= 2 else "")
    queue = "clinical_hypo" if (hr and nights >= 2) or l2 else "physician_review"
    ctx.stage_write("OutboundContent", f"evidence-{pid}-{s.get('window_end', TODAY.isoformat())}",
                    {"target_audience": "医师", "body": body, "content_type": "方案", "disclaimer_attached": True, "first_page_hypo_table": True,
                     "iah_suspected": len(silent) >= 2, "atypical_hypo_suspected": bool(atyp), "patient_ref": pid, "_staged": exec_token(ctx)})
    ctx.stage_write("ReferralRecord", f"ref-{pid}-{_now()}", {"patient_id": pid, "question": question, "referred_to": "医师", "referred_at": _now(),
                                                                "queue": queue, "_staged": exec_token(ctx)})
    ctx.set_confidence(0.9 if s else 0.5)
    ctx.add_evidence(episodes=len(eps), l2=len(l2), tbr=s.get("tbr_pct"), nights_low=nights)
    ctx.emit_effect("workitem", on="committed", template="医师接单", patient_id=pid, queue=queue)


@action("转介医师")
def act_refer(ctx):
    """P7（W45 / 0224）：IR §4「用药类问题一律转医师，AI 与健管师不得答」。写一条 ReferralRecord（referred_to 医师），
    带上 Level 3 / 停药观察期 / 用药问题 三个上下文标记，派医师接单工单；HIL 医师 always 由动作声明决定。"""
    pid = str(ctx.params["patient_id"])
    q = str(ctx.params.get("question_context") or "")
    sym = ctx.find("SymptomTreatmentRecord", lambda r: r.get("patient_id") == pid)
    l3 = [s for s in sym if any(k in str(s.get("symptom_tag", "")) for k in ("需他人协助", "意识", "抽搐", "昏迷", "叫不醒"))]
    clock = ctx.get("RemissionClock", pid) or {}
    watch = clock.get("status") == "running"
    drug_q = bool(_drug_dose_sentences(q)) or any(d in q for d in DRUG_NAMES)
    tags = [t for t, on in (("Level3严重低血糖", bool(l3)), ("停药观察期", watch), ("用药问题", drug_q)) if on]
    queue = "clinical_hypo" if l3 else ("remission_watch" if watch else "physician_review")
    ctx.stage_write("ReferralRecord", f"ref-{pid}-{_now()}", {"patient_id": pid, "question": q, "referred_to": "医师", "referred_at": _now(),
                                                                "queue": queue, "context_tags": tags, "_staged": exec_token(ctx)})
    ctx.set_confidence(0.9)
    ctx.add_evidence(level3=bool(l3), remission_watch=watch, drug_question=drug_q, queue=queue)
    ctx.emit_effect("workitem", on="committed", template="医师接单", patient_id=pid, queue=queue)


@action("判定缓解结果")
def act_remission(ctx):
    pid = str(ctx.params["patient_id"])
    meets, d = _remission_criteria(ctx, pid)
    status = "in_remission" if meets else "not_in_remission"
    ctx.stage_write("RemissionAssessment", f"ra-{pid}-{TODAY.isoformat()}",
                    {"patient_id": pid, "status": status, "evidence_pack_ref": f"lab:{P(ctx, 'lab_result_id') or '-'};summary:{P(ctx, 'summary_id') or summary_of(ctx, pid).get('summary_id')}",
                     "method_used": d["method"] or "HbA1c", "detail": {k: v for k, v in d.items() if k != "method"}, "_staged": exec_token(ctx)})
    ctx.set_confidence(0.95 if d["method"] == "HbA1c" else 0.8)
    ctx.add_evidence(**{k: (v if not isinstance(v, list) else list(v)) for k, v in d.items()})
    ctx.emit_effect("workitem", on="committed", template="医师面诊告知", patient_id=pid, status=status)


@action("响应并回执告警")
def act_ack(ctx):
    a = str(ctx.params["alert_id"])
    ctx.stage_write("AlertAck", f"ack-{a}-{_now()}", {"alert_id": a, "responder": ctx.params["responder"], "responded_at": _now(),
                                                       "action_taken": ctx.params.get("action_taken"), "retest_value": P(ctx, "retest_value"), "_staged": exec_token(ctx)})
    ctx.set_confidence(1.0)


def _tier_label(s):
    gmi, tar = _num(s.get("gmi_pct")), _num(s.get("tar_pct"))
    if gmi is None:
        return None
    if gmi < 5.7:
        return "L0"
    if gmi < 6.1:
        return "L1"
    if gmi < 6.5:
        return "L2"
    if gmi < 7.5 and (tar or 0) < 50:
        return "L3"
    return "L4"


@action("输出服务分层标签")
def act_tier(ctx):
    pid = str(ctx.params["patient_id"])
    prof, s = profile_of(ctx, pid), summary_of(ctx, pid)
    label = _tier_label(s)
    ctx.stage_write("PatientProfile", pid, {**{k: v for k, v in prof.items() if k != "_staged"}, "tier_label": label,
                                            "disclosure_approved": prof.get("disclosure_approved", False), "_staged": exec_token(ctx)})
    ctx.set_confidence(0.85 if s.get("sufficiency_ok") else 0.4)
    ctx.add_evidence(summary_id=s.get("summary_id"), gmi=s.get("gmi_pct"), tier=label)


@action("审核输出内容")
def act_gate(ctx):
    c = str(ctx.params["content_id"])
    oc = ctx.get("OutboundContent", c) or {}
    text = oc.get("body", "")
    hit_rules = []
    if hits(text, banned_terms(ctx)):
        hit_rules.append("D8_禁用词拦截")
    if _drug_dose_sentences(text):
        hit_rules.append("D10_用药建议拦截")
    if DIAG_CERTAIN_RE.search(text):
        hit_rules.append("D11_未确认分型分级措辞拦截")
    if hits(text, NIGHT_PROMISE):
        hit_rules.append("R54_服务话术不得含夜间安全承诺")
    for s in sentences(text):
        if product_mention(ctx, s) and (TIER_RE.search(s) or REMISSION_RE.search(s)):
            hit_rules.append("R32_产品推荐合规闸"); break
    ctx.stage_write("ComplianceCheckLog", f"ccl-{c}-{_now()}", {"model_version": "rules-fde-0.1", "prompt_version": "-", "hit_rules": hit_rules,
                                                                "blocked_reason": "；".join(hit_rules), "target_content_ref": c, "_staged": exec_token(ctx)})
    if not hit_rules:
        ctx.stage_write("GateToken", f"gt-{c}", {"issued_at": _now(), "scope": c, "expiry": (datetime.now() + timedelta(days=7)).isoformat(timespec="minutes"), "_staged": exec_token(ctx)})
        ctx.stage_write("OutboundContent", c, {**oc, "gate_token_ref": f"gt-{c}", "state": "gated", "_staged": exec_token(ctx)})
    ctx.set_confidence(1.0)
    ctx.add_evidence(content_id=c, hit_rules=hit_rules)


@action("生成产品推荐")
def act_reco(ctx):
    pid, sku_id = str(ctx.params["patient_id"]), str(ctx.params["sku_id"])
    sku = ctx.get("ProductSku", sku_id) or {}
    pitch = P(ctx, "pitch")  # 调用方给的推荐话术原样进闸（R32/D9 审的就是这句）
    body = f"{pitch}\n固体饮料，不替代药物。\n{DISCLAIMER}" if pitch else f"为您推荐 {sku.get('name', sku_id)}，可作为日常饮食的补充。\n固体饮料，不替代药物。\n{DISCLAIMER}"
    ctx.stage_write("OutboundContent", f"reco-{pid}-{sku_id}", {"target_audience": "患者", "body": body, "content_type": "方案", "disclaimer_attached": True,
                                                                 "patient_ref": pid, "_staged": exec_token(ctx)})
    ctx.set_confidence(0.8)


@action("群内答复患者")
def act_group_reply(ctx):
    pid = str(ctx.params["patient_id"])
    msg = str(ctx.params["message"])
    ctx.stage_write("OutboundContent", f"grp-{pid}-{_now()}", {"target_audience": "患者群", "body": msg, "content_type": "群内答复",
                                                               "disclaimer_attached": DISCLAIMER in msg, "patient_ref": pid, "sender_role": ctx.params.get("sender_role"), "_staged": exec_token(ctx)})
    ctx.set_confidence(0.9)


@action("摄入读数")
def act_ingest(ctx):
    payload = ctx.params.get("raw_payload") or {}
    rows = payload.get("readings") or []
    pid = payload.get("patient_id")
    n = 0
    for r in rows:
        if not isinstance(r, dict) or r.get("reading_id") is None:
            continue
        ctx.stage_write("GlucoseReading", str(r["reading_id"]), {**r, "patient_id": pid, "_staged": exec_token(ctx)})
        n += 1
    ctx.stage_write("IngestBatch", f"batch-{ctx.params.get('channel')}-{_now()}", {"channel": ctx.params.get("channel"), "record_count": n, "status": "pending", "_staged": exec_token(ctx)})
    ctx.set_confidence(1.0)


def _normalize_time(s, date_hint=None):
    """P9a：路由层常把 device_time 给成 'HH:MM'；补上今天（或 date_hint）的日期，能解析的原样返回。"""
    s = str(s or "")
    if _dt(s):
        return s
    import re as _re
    m = _re.fullmatch(r"(\d{1,2}):(\d{2})", s.strip())
    if m:
        d = str(date_hint or _now())[:10]
        return f"{d}T{int(m.group(1)):02d}:{m.group(2)}"
    return s


@action("去重与通道仲裁")
def act_dedup(ctx):
    """P8（W45 / 0233）：IR §4「按传感器序号去重，多路自动仲裁」。
    强键（sensor_serial + 序号）相同 → 重复，候选落库为 superseded；弱键（weak_dedup）→ ±90s 容差内有读数即重复；
    强键不同但 ±90s 内有其它通道读数 → 多通道仲裁，source_confidence 高者为准，低者 superseded；
    R02 口径的压迫伪差 → quality_flag noise（不计入事件，不抑制告警）。"""
    c = dict(ctx.params.get("reading_candidate") or {})
    rid = str(c.get("reading_id") or f"cand-{_now()}")
    pid = str(c.get("patient_id") or pid_of(ctx) or "")
    if not pid and c.get("sensor_serial"):  # P9a：候选没带患者 id 时按传感器序号反查（序号归属患者是 IR 的事实，不是路由的事）
        sn0 = str(c["sensor_serial"])
        owner = [r for r in ctx.find("GlucoseReading", lambda r: r.get("sensor_serial") and (sn0 == r.get("dedup_key") or sn0.startswith(str(r.get("sensor_serial")))))]
        pid = str(owner[0].get("patient_id")) if owner else ""
    c["reading_id"], c["patient_id"] = rid, pid
    c.setdefault("quality_flag", "clean")
    # P9a：IR 字段归一——value_raw/unit_raw → value_mmol；device_time → time_utc；有序号没键 → 键 = 序号；无序号无键 → weak_dedup 回退
    if c.get("value_mmol") is None and c.get("value_raw") is not None:
        c["value_mmol"] = c.get("value_raw") if str(c.get("unit_raw") or "mmol/L").lower().startswith("mmol") else round(_num(c.get("value_raw")) / 18.0, 1)
    if not c.get("time_utc") and c.get("device_time"):
        hint = c.get("date_hint")
        if not hint:  # 路由只给 'HH:MM' 时，按该患者库里最新读数的日期补（上传日假设，IR tz_provenance=upload_day_assumed）
            latest = sorted((str(r.get("time_utc") or "") for r in ctx.find("GlucoseReading", lambda r: r.get("patient_id") == pid)), reverse=True)
            hint = latest[0][:10] if latest else None
        c["time_utc"] = _normalize_time(c.get("device_time"), hint)
        if hint and not _dt(str(c.get("device_time"))):
            c.setdefault("tz_provenance", "upload_day_assumed"); c["tz_provenance"] = "upload_day_assumed"
    sn = str(c.get("sensor_serial") or "")
    if not c.get("dedup_key"):
        if sn:
            c["dedup_key"] = sn
        else:
            c["weak_dedup"] = True
    dk, t = c.get("dedup_key"), _dt(c.get("time_utc"))
    others = [r for r in ctx.find("GlucoseReading", lambda r: r.get("patient_id") == pid and r.get("reading_id") != rid)]
    dup = [r for r in others if dk and r.get("dedup_key") == dk]
    near = [r for r in others if t and _dt(r.get("time_utc")) and abs((_dt(r["time_utc"]) - t).total_seconds()) <= 90]
    verdict, ref = "new", None
    if dup:
        verdict, ref = "duplicate", dup[0]["reading_id"]
    elif c.get("weak_dedup") is True and near:
        verdict, ref = "weak_duplicate", near[0]["reading_id"]
    elif near:
        best = max(near, key=lambda r: _num(r.get("source_confidence")) or 0.0)
        if (_num(c.get("source_confidence")) or 0.0) > (_num(best.get("source_confidence")) or 0.0):
            verdict, ref = "arbitrated_wins", best["reading_id"]
            ctx.stage_write("GlucoseReading", str(best["reading_id"]), {**best, "quality_flag": "superseded", "superseded_by": rid, "_staged": exec_token(ctx)})
        else:
            verdict, ref = "arbitrated_loses", best["reading_id"]
    if verdict in ("duplicate", "weak_duplicate", "arbitrated_loses"):
        c["quality_flag"], c["superseded_by"] = "superseded", ref
    else:
        hit = _pressure_artifact(ctx, c)
        if hit:
            c["quality_flag"], c["artifact_reason"] = "noise", hit
    ctx.stage_write("GlucoseReading", rid, {**c, "_staged": exec_token(ctx)})
    ctx.set_confidence(0.95 if c.get("sensor_serial") else 0.8)
    ctx.add_evidence(verdict=verdict, ref=ref, quality_flag=c["quality_flag"])


@action("触发低血糖处置")
def act_trigger_hypo(ctx):
    pid, rid = str(ctx.params["patient_id"]), str(ctx.params["reading_id"])
    r = ctx.get("GlucoseReading", rid) or {}
    g = _num(r.get("value_mmol"))
    level = "高" if (g is not None and g < 3.0) else ("中" if (g is not None and g < 3.9) else "低")
    ctx.stage_write("AlertEvent", f"A-{pid}-{rid}", {"alert_id": f"A-{pid}-{rid}", "patient_id": r.get("patient_id", pid), "level": level, "value": g,
                                                     "trend": None, "evidence": f"读数 {rid}（{r.get('source_channel', '未知通道')}）", "confidence": _num(r.get("source_confidence")) or 0.0,
                                                     "rule_id": ctx.params.get("rule_id"), "is_backfill": r.get("is_backfill"), "source_channel": r.get("source_channel"),
                                                     "source_confidence": r.get("source_confidence"), "raised_at": _now(), "_staged": exec_token(ctx)})
    ctx.set_confidence(0.9 if r else 0.3)
    ctx.add_evidence(reading_id=rid, value=g, found=bool(r))


@action("推送告警")
def act_push_alert(ctx):
    a = str(ctx.params["alert_id"])
    ev = ctx.get("AlertEvent", a) or {}
    tpl = _alert_template(ctx)
    ctx.stage_write("AlertEvent", a, {**ev, "level": ctx.params.get("level", ev.get("level")), "template_id": tpl.get("template_id"), "_staged": exec_token(ctx)})
    for t in ctx.params.get("targets") or []:
        ctx.stage_write("DeliveryReceipt", f"dr-{a}-{t}", {"target": str(t), "channel": "app", "delivered_at": None, "status": "requested", "gate_token_ref": None, "_staged": exec_token(ctx)})
    ctx.set_confidence(1.0)


@action("推送方案至患者")
def act_push_plan(ctx):
    p = str(ctx.params["plan_id"])
    ps = ctx.get("PlanSigned", p) or {}
    ctx.stage_write("OutboundContent", f"push-{p}", {"target_audience": "患者", "body": ps.get("content_snapshot", ""), "content_type": "方案",
                                                     "disclaimer_attached": DISCLAIMER in str(ps.get("content_snapshot", "")), "patient_ref": ps.get("patient_id"), "_staged": exec_token(ctx)})
    for t in ctx.params.get("targets") or []:
        ctx.stage_write("DeliveryReceipt", f"dr-{p}-{t}", {"target": str(t), "channel": "app", "delivered_at": None, "status": "requested", "gate_token_ref": None, "_staged": exec_token(ctx)})
    ctx.set_confidence(1.0)


@action("创建服务包SKU")
def act_service_sku(ctx):
    sid = str(ctx.params["sku_id"])
    ctx.stage_write("ProductSku", sid, {"name": f"控糖服务包·{ctx.params.get('tier')}", "category": "服务", "label_verified": True,
                                        "commission_config": P(ctx, "commission_config") or "none", "contents": list(ctx.params.get("contents") or []), "_staged": exec_token(ctx)})
    ctx.stage_write("ServicePackage", f"pkg-{sid}", {"patient_id": None, "tier": ctx.params.get("tier"), "start_date": None, "end_date": None, "wear_days_fulfilled": 0, "_staged": exec_token(ctx)})
    ctx.set_confidence(0.9)


@action("上架产品SKU")
def act_list_sku(ctx):
    sid = str(ctx.params["sku_id"])
    sku = ctx.get("ProductSku", sid) or {"name": sid}
    ctx.stage_write("ProductSku", sid, {**sku, "category": ctx.params.get("category", sku.get("category")), "state": "listed", "_staged": exec_token(ctx)})
    ctx.set_confidence(0.9)


@action("发布宣传素材")
def act_publish(ctx):
    c = str(ctx.params["content_id"])
    oc = ctx.get("OutboundContent", c) or {}
    ctx.stage_write("OutboundContent", c, {**oc, "channel": ctx.params.get("channel"), "content_type": oc.get("content_type", "宣传素材"), "state": "gated", "_staged": exec_token(ctx)})
    ctx.set_confidence(0.9)


# ----------------------------------------------------------------------------- 参考数据 + 演示租户数据
def _gen_readings(rng, pid, days, mean, sd, *, night_drop=0.0, backfill_days=0, ocr_n=0, hypo_nights=(), floor=2.2):
    """15 min 采样，days 天到今天 00:00；night_drop 为夜间 00–06 的随机丢点比例；hypo_nights 指定哪些天（距今天数）夜里 02:00 起 45 min 低血糖。"""
    rows = []
    end = datetime.combine(TODAY, datetime.min.time())
    start = end - timedelta(days=days)
    t, i = start, 0
    sn = f"SN-{pid}-A"
    while t < end:
        hour = t.hour + t.minute / 60
        base = mean + 1.6 * math.sin((hour - 9) / 24 * 2 * math.pi) + (1.8 if 12 <= hour <= 14 or 18.5 <= hour <= 20.5 else 0)
        v = max(floor, rng.gauss(base, sd))
        day_ago = (end - t).days
        if day_ago in hypo_nights and 2.0 <= hour < 2.75:
            v = rng.uniform(2.6, 3.6)
        v = max(2.2, min(22.0, round(v, 1)))
        drop = (0 <= t.hour < 6) and rng.random() < night_drop
        if not drop:
            r = {"reading_id": f"r-{pid}-{i:05d}", "patient_id": pid, "value_raw": v, "unit_raw": "mmol/L", "value_mmol": v,
                 "device_time": t.isoformat(timespec="minutes"), "time_utc": t.isoformat(timespec="minutes"), "tz_provenance": "device_reported",
                 "source_channel": "vendor_api", "source_confidence": 0.99, "quality_flag": "clean",
                 "is_backfill": day_ago >= days - backfill_days and backfill_days > 0, "data_age": "fresh",
                 "sensor_serial": sn, "dedup_key": f"{sn}-{i:05d}"}
            rows.append(r)
        t += timedelta(minutes=15); i += 1
    for k in range(ocr_n):
        tt = end - timedelta(days=rng.randint(1, days - 1), hours=rng.randint(7, 21))
        rows.append({"reading_id": f"r-{pid}-ocr{k:02d}", "patient_id": pid, "value_raw": round(rng.uniform(4, 12), 1), "unit_raw": "mmol/L",
                     "value_mmol": round(rng.uniform(4, 12), 1), "device_time": tt.isoformat(timespec="minutes"), "time_utc": tt.isoformat(timespec="minutes"),
                     "tz_provenance": "upload_day_assumed", "source_channel": "ocr_upload", "source_confidence": 0.78, "quality_flag": "suspect_duplicate",
                     "is_backfill": False, "data_age": "stale", "sensor_serial": None, "dedup_key": f"ocr-{pid}-{k}", "weak_dedup": True})
    return rows


def _summary_from(pid, rows, days, prof):
    clean = [r for r in rows if r["source_channel"] in TRUSTED_CHANNELS and r["quality_flag"] == "clean"]
    m = metrics_from_values([r["value_mmol"] for r in clean], prof)
    end = datetime.combine(TODAY, datetime.min.time())
    active = round(min(100.0, 100.0 * len(clean) / (days * 96)), 1)
    return {"summary_id": f"s-{pid}-{days}d", "patient_id": pid, "window_start": (end - timedelta(days=days)).date().isoformat(),
            "window_end": (end - timedelta(days=1)).date().isoformat(), "days": days, "wear_ratio": round(active / 100, 2), "active_pct": active,
            "sufficiency_ok": days >= 14 and active >= 70, "tz_uncertain": False, "brand_changed": False, "metric_provenance": "self_computed",
            "nocturnal_coverage_pct": nocturnal_coverage(clean, days), "nocturnal_coverage_insufficient": nocturnal_coverage(clean, days) < 70,
            "confounded_window": False, "consecutive_low_night_nights": consecutive_low_nights(clean, days),
            "tir_pct": m["tir"], "tbr_pct": m["tbr"], "tbr_l2_pct": m["tbr_l2"], "tar_pct": m["tar"], "tar_l2_pct": m["tar_l2"],
            "cv_pct": m["cv"], "gmi_pct": m["gmi"], "mean_glucose": m["mean"]}


def seed_reference_data(store) -> None:
    """参考数据（词库 / 模板 / 人群参数 / 资质 / 审计策略）+ 一个演示租户的患者数据。

    患者数据按**今天**相对生成（15 min 采样），指标由 metrics_from_values 从读数真实聚合，不手填。
    """
    rng = random.Random(20261023)
    put = store.put_object
    d = lambda n: (TODAY - timedelta(days=n)).isoformat()

    # --- 词库 / 模板 / 人群参数 ---
    for i, (term, cat) in enumerate([("逆转", "疗效声称"), ("治愈", "疗效声称"), ("根治", "疗效声称"), ("停药", "用药"), ("疗程", "产品"), ("修复胰腺", "疗效声称"),
                                      ("降血糖", "食品功效"), ("医学营养治疗", "诊疗"), ("MNT", "诊疗"), ("不用吃药", "用药"), ("摆脱药物", "用药")]):
        put("BannedTermLibrary", f"bt-{i:02d}", {"term_id": f"bt-{i:02d}", "term": term, "category": cat, "version": "2026.10", "status": "active"})
    for level, body in (("低", "您的血糖略低，请留意并适时补充含碳水食物。"), ("中", "检测到低血糖，请按 15-15 法则补充 15g 碳水并 15 分钟后复测。"),
                        ("高", "检测到持续低血糖，请立即补充碳水并联系健管师；如出现意识改变请拨打 120。"), ("危急", "危急：血糖极低，请立即处置并拨打 120，已通知值班医师与紧急联系人。")):
        put("AlertTemplate", f"tpl-{level}", {"template_id": f"tpl-{level}", "level": level, "body": body + DISCLAIMER, "frozen": True,
                                             "pre_reviewed_c22": True, "pre_reviewed_r54": True, "reviewed_at": d(30)})
    for prof, pop, age_min, req_med, tir, tbr, tbr2, low in (("adult", "一般成人", 18, False, 70, 4.0, 1.0, 3.9), ("elderly", "老年（≥65）", 65, False, 50, 1.0, 0.0, 3.9),
                                                             ("elderly_high_risk", "老年 + 胰岛素/磺脲", 65, True, 50, 1.0, 0.0, 4.4), ("pregnancy", "妊娠", 18, False, 70, 4.0, 1.0, 3.5)):
        put("TargetProfileParam", prof, {"profile": prof, "population": pop, "age_min": age_min, "requires_hypo_risk_med": req_med, "tir_target_pct": tir,
                                         "tbr_max_pct": tbr, "tbr_l2_max_pct": tbr2, "low_alert_threshold": low, "range_low": 3.5 if prof == "pregnancy" else 3.9,
                                         "range_high": 7.8 if prof == "pregnancy" else 10.0, "source": "ATTD 2019；中国老年糖尿病诊疗指南 2024"})
    # --- 资质 / 审计策略 ---
    put("Credential", "cred-huang", {"credential_id": "cred-huang", "holder": "黄医生", "holder_id": "S-HUANG", "credential_type": "执业医师", "registration_no": "1104502023xxxx", "expiry_date": d(-700), "status": "valid"})
    put("Credential", "cred-chen", {"credential_id": "cred-chen", "holder": "陈营养师", "holder_id": "S-CHEN", "credential_type": "注册营养师", "registration_no": "RD-2021-xxxx", "expiry_date": d(33), "status": "valid"})
    put("Credential", "cred-wu", {"credential_id": "cred-wu", "holder": "吴康复师", "holder_id": "S-WU", "credential_type": "运动康复师", "registration_no": "PT-2022-xxxx", "expiry_date": d(-400), "status": "valid"})
    put("AuditLog", "log-policy", {"log_id": "log-policy", "actor": "system", "action": "retention_policy", "target": "all", "timestamp": d(90), "retention_years": 3, "audit_enabled": True})
    put("StoreEntity", "store-01", {"store_id": "store-01", "name": "代谢健康管理中心·南宁青秀店", "license_no": None, "medical_scope": [], "readiness_ref": None})
    put("ProductSku", "sku-ynl-01", {"sku_id": "sku-ynl-01", "name": "英纽林", "category": "食品", "label_verified": True, "commission_config": "none"})
    put("ProductSku", "sku-cgm-01", {"sku_id": "sku-cgm-01", "name": "CGM 传感器（14 天）", "category": "器械引用", "label_verified": False, "commission_config": "none"})

    # --- 患者：画像 ---
    patients = {
        "P0012": {"display_name": "刘阿姨", "age": 68, "sex": "F", "pregnant": False, "meds": ["二甲双胍"], "health_tier": "中等", "target_profile": "elderly", "is_iah_high_risk": False,
                  "eGFR": 72, "renal_unknown": False, "tier_label": "L2", "disclosure_approved": False, "remission_status": "none", "away_mode": False, "diagnosed_at": d(6 * 365)},
        "P0031": {"display_name": "王叔", "age": 72, "sex": "M", "pregnant": False, "meds": ["格列美脲", "二甲双胍"], "health_tier": "中等", "target_profile": "elderly", "is_iah_high_risk": True,
                  "eGFR": 61, "renal_unknown": False, "tier_label": "L3", "disclosure_approved": False, "remission_status": "none", "away_mode": False, "diagnosed_at": d(11 * 365)},
        "P0007": {"display_name": "周先生", "age": 52, "sex": "M", "pregnant": False, "meds": [], "health_tier": "良好", "target_profile": "adult", "is_iah_high_risk": False,
                  "eGFR": 95, "renal_unknown": False, "tier_label": "L1", "disclosure_approved": True, "remission_status": "candidate", "away_mode": False, "diagnosed_at": d(3 * 365)},
        "P0023": {"display_name": "陈阿姨", "age": 66, "sex": "F", "pregnant": False, "meds": ["甘精胰岛素"], "health_tier": "中等", "target_profile": "elderly", "is_iah_high_risk": False,
                  "eGFR": 68, "renal_unknown": False, "tier_label": "L3", "disclosure_approved": False, "remission_status": "none", "away_mode": False, "diagnosed_at": d(9 * 365)},
        "P0088": {"display_name": "李女士", "age": 58, "sex": "F", "pregnant": False, "meds": ["二甲双胍"], "health_tier": "良好", "target_profile": "adult", "is_iah_high_risk": False,
                  "eGFR": 88, "renal_unknown": False, "tier_label": None, "disclosure_approved": False, "remission_status": "none", "away_mode": False, "diagnosed_at": d(2 * 365)},
        "P0045": {"display_name": "黄伯", "age": 70, "sex": "M", "pregnant": False, "meds": ["格列齐特"], "health_tier": "差", "target_profile": "elderly", "is_iah_high_risk": True,
                  "eGFR": 55, "renal_unknown": False, "tier_label": "L3", "disclosure_approved": False, "remission_status": "none", "away_mode": False, "diagnosed_at": d(14 * 365)},
        "P0066": {"display_name": "张阿姨", "age": 63, "sex": "F", "pregnant": False, "meds": [], "health_tier": "良好", "target_profile": "adult", "is_iah_high_risk": False,
                  "eGFR": 90, "renal_unknown": False, "tier_label": "L1", "disclosure_approved": False, "remission_status": "none", "away_mode": False, "diagnosed_at": d(365)},
        "P0099": {"display_name": "新客", "age": 61, "sex": "M", "pregnant": False, "meds": [], "health_tier": None, "target_profile": None, "is_iah_high_risk": False,
                  "eGFR": None, "renal_unknown": True, "tier_label": None, "disclosure_approved": False, "remission_status": "none", "away_mode": False, "diagnosed_at": None},
    }
    for pid, p in patients.items():
        put("PatientProfile", pid, {"patient_id": pid, **p})
    # 同意书（P0099 没有；P0007 含营销推荐）
    for pid in ("P0012", "P0031", "P0007", "P0023", "P0088", "P0045", "P0066"):
        items = ["血糖数据", "用药信息", "体测数据", "紧急联系人", "厂商云对接", "数据留存", "健康档案"] + (["营销推荐"] if pid in ("P0007", "P0045") else [])
        put("ConsentRecord", f"consent-{pid}", {"consent_id": f"consent-{pid}", "patient_id": pid, "scope_items": items, "version": "v2.1", "signed_at": d(40) + "T10:00", "hash": f"sha256:{pid}", "legacy_import": False, "state": "granted"})
    put("MedClassHint", "hint-P0045", {"hint_id": "hint-P0045", "patient_id": "P0045", "hint_source": "drug_box_photo", "hypo_risk_med": True, "sglt2i": False})
    put("MedClassHint", "hint-P0031", {"hint_id": "hint-P0031", "patient_id": "P0031", "hint_source": "self_report", "hypo_risk_med": True, "sglt2i": False})

    # --- 患者：读数 → 汇总 / 低血糖事件（真实聚合） ---
    specs = {
        "P0012": dict(days=14, mean=8.4, sd=1.7, night_drop=0.08, hypo_nights=(1,), floor=3.7),                       # 昨夜一次 L1 夜间事件
        "P0031": dict(days=14, mean=7.9, sd=2.3, night_drop=0.55, backfill_days=3, ocr_n=12, hypo_nights=(1, 2, 5, 9)),  # 去强化对象：TBR 高、夜间覆盖低
        "P0007": dict(days=14, mean=6.2, sd=0.9, night_drop=0.05, floor=4.3),                                          # 缓解候选
        "P0023": dict(days=14, mean=9.1, sd=2.0, night_drop=0.6, floor=3.7),                                           # 夜间覆盖 ~41%
        "P0088": dict(days=6, mean=7.6, sd=1.4, night_drop=0.05, floor=4.0),                                           # 才戴 6 天
        "P0045": dict(days=14, mean=8.8, sd=2.1, night_drop=0.2, hypo_nights=(1, 3), floor=3.5),
    }
    for pid, sp in specs.items():
        rows = _gen_readings(rng, pid, **sp)
        for r in rows:
            put("GlucoseReading", r["reading_id"], r)
        s = _summary_from(pid, rows, sp["days"], patients[pid]["target_profile"] or "adult")
        put("CgmSummary", s["summary_id"], s)
        for k, e in enumerate(episodes_from_readings([r for r in rows if r["source_channel"] in TRUSTED_CHANNELS])):
            put("HypoEpisode", f"ep-{pid}-{k:02d}", {"episode_id": f"ep-{pid}-{k:02d}", **e})
    # 老年非典型症状（P0031 一次「叫不醒」，与第 2 天夜间事件同期）
    put("SymptomTreatmentRecord", "sym-P0031-01", {"record_id": "sym-P0031-01", "patient_id": "P0031", "alert_id": None, "symptom_tag": "叫不醒", "treatment_action": "家属喂糖水",
                                                    "recorded_by": "家属", "recorded_at": d(2) + "T02:20"})
    # 告警 / 阈值 / 低血糖状态机
    put("AlertThreshold", "th-P0012-night_low", {"threshold_id": "th-P0012-night_low", "patient_id": "P0012", "field": "night_low", "current_value": 3.9, "default_value": 3.9, "safe_direction": "收紧"})
    put("AlertEvent", "A-P0012-01", {"alert_id": "A-P0012-01", "patient_id": "P0012", "level": "中", "value": 3.6, "trend": -0.8, "evidence": "r-P0012 02:15 连续 2 读数 <3.9", "confidence": 0.97,
                                     "rule_id": "R04a_Level1低血糖_实时告警", "is_backfill": False, "source_channel": "vendor_api", "source_confidence": 0.99, "raised_at": d(1) + "T02:15"})
    put("AlertEvent", "A-P0045-02", {"alert_id": "A-P0045-02", "patient_id": "P0045", "level": "高", "value": 3.2, "trend": -1.2, "evidence": "r-P0045 02:00 连续 3 读数 <3.9", "confidence": 0.98,
                                     "rule_id": "R03a_Level2低血糖_实时告警", "is_backfill": False, "source_channel": "vendor_api", "source_confidence": 0.99, "raised_at": d(1) + "T02:00"})
    put("AlertEvent", "A-P0031-backfill-01", {"alert_id": "A-P0031-backfill-01", "patient_id": "P0031", "level": "危急", "value": 2.9, "trend": None, "evidence": "回填批次 3 周前读数", "confidence": 0.9,
                                              "rule_id": "R03a_Level2低血糖_实时告警", "is_backfill": True, "source_channel": "vendor_api", "source_confidence": 0.99, "raised_at": d(1) + "T09:00"})
    put("AlertEvent", "A-P0045-ocr-01", {"alert_id": "A-P0045-ocr-01", "patient_id": "P0045", "level": "危急", "value": 2.8, "trend": None, "evidence": "OCR 截图识别 2.8", "confidence": 0.6,
                                         "rule_id": "R03a_Level2低血糖_实时告警", "is_backfill": False, "source_channel": "ocr_upload", "source_confidence": 0.78, "raised_at": d(0) + "T08:30"})
    put("HypoState", "P0045", {"patient_id": "P0045", "prolonged_risk": True, "recurrence_window_until": d(-1) + "T02:00", "closure_blocked_reason": "磺脲使用者：低血糖可持续 24–72 小时"})
    put("HypoState", "P0012", {"patient_id": "P0012", "prolonged_risk": False, "recurrence_window_until": None, "closure_blocked_reason": None})
    # 方案草稿 / 已签发方案 / 签发证据（上周有两份停留 <20 秒）
    put("PlanDraft", "d-P0012-01", {"draft_id": "d-P0012-01", "patient_id": "P0012", "content": "【P0012 本期方案草稿 · 方向：维持】\n先菜后饭、控制主食份量，餐后步行 15 分钟；睡前如需加餐选含碳水 10–15g 食物并复测。\n" + DISCLAIMER,
                                    "template_version": "fde-0.1", "med_interaction_routed": False, "direction": "维持", "category": "营养"})
    # 2026-10-24 W50 补 seed（round 7 出口签发闸 tier4 用例需要含用药调整的草稿；此前只有 d-P0012-01 营养类）。只增对象，不改既有对象。
    put("PlanDraft", "d-P0045-01", {"draft_id": "d-P0045-01", "patient_id": "P0045", "content": "【P0045 本期方案草稿 · 方向：调整】\n夜间低血糖反复，建议格列齐特晚餐前剂量减半并复测一周；睡前加餐含碳水 10–15g。\n" + DISCLAIMER,
                                    "template_version": "fde-0.1", "med_interaction_routed": True, "direction": "调整", "category": "用药"})
    put("PlanDraft", "d-P0031-01", {"draft_id": "d-P0031-01", "patient_id": "P0031", "content": "【P0031 本期方案草稿 · 方向：减药】\n餐后与空腹均达标两周，建议二甲双胍由每日三次减为两次，两周后复评。\n" + DISCLAIMER,
                                    "template_version": "fde-0.1", "med_interaction_routed": True, "direction": "减药", "category": "用药"})
    put("PlanDraft", "d-P0012-02", {"draft_id": "d-P0012-02", "patient_id": "P0012", "content": "【P0012 本期方案草稿 · 方向：调整】\n餐后峰值偏高，建议加用阿卡波糖随餐；饮食与步行方案沿用上期。\n" + DISCLAIMER,
                                    "template_version": "fde-0.1", "med_interaction_routed": True, "direction": "调整", "category": "用药"})
    for pid, plan, dwell, diff, when, signer in (("P0088", "plan-P0088-w41", 12, "", d(6), "S-HUANG"), ("P0045", "plan-P0045-w41", 15, "", d(5), "S-HUANG"),
                                                  ("P0012", "plan-P0012-w40", 95, "调整了餐后步行时长", d(12), "S-HUANG"), ("P0066", "plan-P0066-w41", 48, "补充了睡前加餐说明", d(4), "S-CHEN")):
        put("PlanSigned", plan, {"plan_id": plan, "patient_id": pid, "content_snapshot": f"{pid} 方案（已签发）\n{DISCLAIMER}", "signer_id": signer, "signed_at": when + "T15:00",
                                 "evidence_snapshot": f"summary:s-{pid}-14d", "review_evidence_ref": f"re-{plan}", "evidence_stale": False})
        put("ReviewEvidence", f"re-{plan}", {"evidence_id": f"re-{plan}", "plan_id": plan, "opened_at": when + "T14:58", "agp_expand_count": 0 if dwell < 20 else 2, "dwell_time": dwell,
                                            "diff": diff, "review_suspicious": dwell < 20, "signer_id": signer})
    # 含分层结论的已签发方案（R51 用例：P0012 disclosure_approved=false，不得直推患者）
    put("PlanSigned", "plan-P0012-tier", {"plan_id": "plan-P0012-tier", "patient_id": "P0012", "content_snapshot": "刘阿姨本期服务分层结论：L2 级（内部标签）。\n" + DISCLAIMER,
                                         "signer_id": "S-HUANG", "signed_at": d(3) + "T16:00", "evidence_snapshot": "summary:s-P0012-14d", "review_evidence_ref": "re-plan-P0012-tier", "evidence_stale": False})
    put("ReviewEvidence", "re-plan-P0012-tier", {"evidence_id": "re-plan-P0012-tier", "plan_id": "plan-P0012-tier", "opened_at": d(3) + "T15:40", "agp_expand_count": 2, "dwell_time": 70, "diff": "改了措辞", "review_suspicious": False, "signer_id": "S-HUANG"})
    # 缓解时钟 / 化验（P0007）
    put("RemissionClock", "P0007", {"patient_id": "P0007", "day0": d(105), "status": "running", "confirmed_by": "S-HUANG"})
    for lid, method, val, when, ngsp in (("lab-P0007-hba1c", "HbA1c", 6.1, d(8), True), ("lab-P0007-gada", "GADA", 0.4, d(100), True),
                                         ("lab-P0007-cpf", "C-peptide fasting", 1.6, d(100), True), ("lab-P0007-cp2", "C-peptide 2h", 3.4, d(100), True)):
        put("LabResult", lid, {"lab_result_id": lid, "patient_id": "P0007", "value": val, "method": method, "lab_id": "LAB-NN-01", "is_ngsp_certified": ngsp, "specimen_type": "venous", "measured_at": when})
    put("BodyMeasurement", "bm-P0007-01", {"measurement_id": "bm-P0007-01", "patient_id": "P0007", "measured_at": d(9), "device_id": "scale-01", "protocol_version": "v1", "fasting": True, "weight": 82.0, "waist": 96.0, "bmi": 27.1, "body_fat_pct": 28.0})
    # 对外内容（待审 / 宣传）
    put("OutboundContent", "c-P0012-plan-02", {"content_id": "c-P0012-plan-02", "target_audience": "患者", "body": "刘阿姨最近血糖降得不错，逆转有望，可以准备停药了。继续保持饮食与运动。",
                                               "content_type": "方案", "gate_token_ref": None, "disclaimer_attached": False, "patient_ref": "P0012"})
    put("OutboundContent", "c-reco-P0012-01", {"content_id": "c-reco-P0012-01", "target_audience": "患者", "body": "根据您的 L3 分级，为您配一套英纽林疗程，坚持使用效果更好。",
                                               "content_type": "方案", "gate_token_ref": None, "disclaimer_attached": False, "patient_ref": "P0012"})
    put("OutboundContent", "c-promo-01", {"content_id": "c-promo-01", "target_audience": "公众", "body": "刘阿姨佩戴 14 天前后血糖对比图：从波动到平稳，看得见的改变。",
                                          "content_type": "宣传素材", "gate_token_ref": None, "disclaimer_attached": False, "patient_ref": "P0012",
                                          "contains_identifiable_patient": True, "is_before_after_comparison": True})


@rule("C7_患者数据禁止存放非平台工具")
def c7(ctx):
    """P14（W48 / 0236 0272 0285）：IR「病历式数据须在境内加密可审计的平台内，不得用个人版 SaaS 表格；写入第三方 SaaS 即向第三方提供个人信息」。
    口径与 C3 / C4 同机制：数据主体须有含「第三方工具传输」项、已签名、未撤销的 ConsentRecord。动作参数无 patient_id，约定 payload_ref 含患者编号。
    目标系统是否完成安全评估 / 签署 DPA 在 IR 里没有对象可查，留给 IR 修订（见 P14.md Risk）。"""
    target = str(P(ctx, "target_system") or "")
    ref = str(P(ctx, "payload_ref") or "")
    m = re.search(r"P\d{4}", ref)
    pid = pid_of(ctx) or (m.group(0) if m else None)
    if not pid:
        return _fail("C7", f"无法确定数据主体（payload_ref={ref!r} 不含患者编号）", "外传载荷须可定位到患者；病历式数据不得写入第三方协作工具")
    cons = [c for c in ctx.find("ConsentRecord", lambda r: r.get("patient_id") == pid) if c.get("state", "granted") != "revoked"]
    ok = [c for c in cons if "第三方工具传输" in (c.get("scope_items") or []) and c.get("signed_at")]
    if not ok:
        return _fail("C7", f"患者 {pid} 未取得向第三方协作工具（{target or '未指明'}）传输数据的单独同意项；病历式数据须留在境内加密可审计的平台内",
                     "先登记含「第三方工具传输」的单独同意，并确认目标系统已完成安全评估与 DPA；否则改用平台内视图")
    return RuleResult.ok()


@action("写入外部协作工具")
def act_write_external(ctx):
    """P14 配套：动作本身也是桩，guard C7 之前引擎先跑 handler，桩抛错就评不到 C7。按 IR §4 writes AuditLog（actor / action / target / timestamp）；
    HIL 合规官 always 由动作声明决定。handler 不做任何外传——外传是 commit 后的效应，这里只留审计痕。"""
    target = str(ctx.params.get("target_system", ""))
    ref = str(ctx.params.get("payload_ref", ""))
    log_id = f"audit-ext-{target}-{ref}"
    ctx.stage_write("AuditLog", log_id, {"log_id": log_id, "actor": ctx.actor.id, "action": "写入外部协作工具", "target": f"{target}:{ref}",
                                        "timestamp": _now(), "_staged": exec_token(ctx)})
    ctx.set_confidence(0.8)
    ctx.add_evidence(target_system=target, payload_ref=ref)


@action("升级告警")
def act_escalate(ctx):
    """P18a（W47 / 0079）：IR §4 升级告警 writes AlertEscalation{alert_id, level, escalated_at, target}；HIL 值班医师 always 由声明决定。
    guard 换成 R53 后 handler 不能再是桩（引擎先跑 handler 再评 guard）。"""
    a = str(ctx.params["alert_id"]); lvl = ctx.params["level"]
    ctx.stage_write("AlertEscalation", f"esc-{a}-{_now()}", {"escalation_id": f"esc-{a}-{_now()}", "alert_id": a, "level": lvl, "escalated_at": _now(),
                                                             "target": "值班医师", "_staged": exec_token(ctx)})
    ctx.set_confidence(0.8)
    ctx.add_evidence(alert_id=a, level=lvl, alert_level=(ctx.get("AlertEvent", a) or {}).get("level"))
