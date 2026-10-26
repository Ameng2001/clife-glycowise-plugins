# round 10 · 3d 链 · 提案编辑表（沙箱生成用）。每项：(文件, 原文片段, 新片段)，原文片段必须在本链状态文件里恰好出现一次。
F, I = "_fde.py", "__init__.py"

# ---------------------------------------------------------------- P41 R32 产品推荐与分层/缓解同句
TIER_LINE1 = r'''TIER_RE = re.compile(r"L\s*[0-4]\s*(级|分级|分层)?|分层结论|分型结论|服务分层|[一二三四]\s*级糖尿病|[12一二]\s*型糖尿病|德心\s*L"
'''
GATE_OLD = r'''    for s in sentences(text):
        if any(p in s for p in prods) and (TIER_RE.search(s) or REMISSION_RE.search(s)):
            return _fail(name, f"产品推荐与分层/缓解字样同句'''
GATE_NEW = r'''    # P41a（W53 / 0717 0718 0719 0781）：IR R32「产品推荐不得与服务分层结论、缓解字样同句」——「产品推荐句」指推荐话术本身。生成产品推荐 的 pitch
    # 就是推荐句，handler 把 sku 名另起一行追加，pitch 里不写产品名时任何一句都「不含产品名」，闸永远不生效（0783 被拦只因 pitch 自带「英纽林」）。
    # 改为：pitch 的每一句都按产品推荐句判，与是否复述产品名无关。
    pitch_sents = set(sentences(str(P(ctx, "pitch") or "")))
    for s in sentences(text):
        if (any(p in s for p in prods) or s in pitch_sents) and (TIER_RE.search(s) or REMISSION_RE.search(s)):
            return _fail(name, f"产品推荐与分层/缓解字样同句'''

P41a = [
    (F, TIER_LINE1, TIER_LINE1 + r'''                     r"|[一二三四1-4]\s*级管理"  # P41a（W53 / 0718）：服务分层 L1–L3 的口语写法「一/二/三级管理」，与 L3 同义
'''),
    (F, GATE_OLD, GATE_NEW),
]
P41b1 = [  # 朴素修 N5：把 Dᵢ 命中的字面量加进匹配
    (F, TIER_LINE1, TIER_LINE1 + r'''                     r"|三级管理"  # P41b1：W53 Dᵢ 字面量
'''),
    (F, r'''PRODUCT_WORDS = ("英纽林", "固体饮料", "营养粉", "代餐", "疗程", "套餐", "一套")''',
        r'''PRODUCT_WORDS = ("英纽林", "固体饮料", "营养粉", "代餐", "疗程", "套餐", "一套", "每天一包", "可以试试", "配一包")  # P41b1：W53 Dᵢ 字面量'''),
]

# ---------------------------------------------------------------- P42 D9 漏拦（餐时血糖 / 胰岛功能 / 用药减停）
ONSET_LINE = r'''ONSET_CLAIM_RE = re.compile(r"(\d+|[一二两三四五六七八九十几半])\s*(天|日|周|星期|个月|月)[^。；，,]{0,6}(见效|起效|看到|看得到|看出|改善|降)")
'''
P42a = [
    (F, ONSET_LINE, ONSET_LINE + r'''# P42a（W53 / 0720 0721 0722 0782 0784）：D9 管的是「明示或暗示保健、疗效作用」。声称的对象不只血糖指标名，还有三类同义对象：
#   (4) 餐时血糖状态：控糖语境里「空腹 / 餐后 / 饭后 + 结果谓词」说的就是那个时点的血糖（「空腹能回到 6 以下」「饭后两小时能落回 8 以内」「把饭后那一波顶回去」）；
#       只认「餐时词 + 结果谓词」（回到 / 落回 / 顶回 / 冲到 / 不容易… / 那一波），「饭后半小时冲一包」「饭后再冲」这类食用时间说明不算；
#   (5) 胰岛 / 胰腺功能：「帮胰岛恢复」与禁用词「修复胰腺」同义，是最重的疗效声称；
#   (6) 用药减停：把食用与停药 / 减药挂钩，暗示可配合或替代药物；「别自行停药」这类安全提醒先剔掉再判。
GLYCEMIC_STATE_RE = re.compile(r"(空腹|餐后|饭后|餐前|睡前|晨起|早起)(\s*[一二两12]\s*个?\s*小时)?[^。；，,]{0,6}?(回到|落回|降到|降回|压到|压回|顶回|顶下|压住|压下|稳在|控制在|不超过|超过|冲到|冲上|升到|涨到|不容易|那一波|那一下|高峰|峰值|不升|不高|不冲高|平稳)")
ISLET_CLAIM_RE = re.compile(r"(胰岛|胰腺|β\s*细胞)(功能)?[^。；，,]{0,6}(恢复|修复|再生|好转|改善|激活)|(帮|养|护|修复|激活|保护|恢复)[^。；，,]{0,4}(胰岛|胰腺|β\s*细胞)")
MED_LINK_RE = re.compile(r"停药|减药|撤药|减停|不用吃药|少吃药|药量|停掉[^。；，,]{0,3}药")
MED_LINK_SAFETY_RE = re.compile(r"(别|不要|不得|切勿|不能|勿|不可)\s*(自行|擅自|随意)?\s*(停药|减药|撤药|减停|停掉[^。；，,]{0,3}药)")


def _med_link(s):
    return MED_LINK_RE.search(MED_LINK_SAFETY_RE.sub("", s))
'''),
    (F, r'''            m = EFFICACY_RE.search(s) or GLYCEMIC_OUTCOME_RE.search(s) or EFFECT_CLAIM_RE.search(s) or ONSET_CLAIM_RE.search(s)
''', r'''            m = EFFICACY_RE.search(s) or GLYCEMIC_OUTCOME_RE.search(s) or EFFECT_CLAIM_RE.search(s) or ONSET_CLAIM_RE.search(s) \
                or GLYCEMIC_STATE_RE.search(s) or ISLET_CLAIM_RE.search(s) or _med_link(s)  # P42a
'''),
]
P42b1 = [  # 朴素修 N5
    (F, r'''GLYCEMIC_INDICATOR_RE = re.compile(r"血糖|糖化|HbA1c|TIR|葡萄糖|曲线|波动")''',
        r'''GLYCEMIC_INDICATOR_RE = re.compile(r"血糖|糖化|HbA1c|TIR|葡萄糖|曲线|波动|空腹|饭后|胰岛|停药")  # P42b1：W53 Dᵢ 字面量'''),
]

# ---------------------------------------------------------------- P43 D9 误拦（不替代声明 / 按原方案 / 安全提醒）
NONCLAIM_OLD = r'''NON_CLAIM_CLAUSE_RE = re.compile(r"(监测|自测|测量|复测|测一下|测|记录|查看|关注|留意)[^。；，,]{0,4}(血糖|糖化|HbA1c|TIR)|不(能|可|得)?替代|遵医嘱|就医|咨询(医生|医师|营养师)")'''
P43a = [
    (F, NONCLAIM_OLD, r'''# P43a（W53 / 0728 0790）：P28a 的豁免只收了「监测提醒」「不替代」两类正当用途的书面写法。食品话术里提到血糖的正当用途按语义是三类，口语写法都要认：
#   ① 声明不替代药物：「不能替代」之外还有「代替不了 / 替代不了 / 取代不了」；
#   ② 把控糖交回原有治疗：「血糖照原来的办法控制」「血糖还按医生的方案来」——说的是血糖怎么管与本品无关，恰与功效声称相反；
#   ③ 以血糖状态为条件的食用限制 + 就医建议：「血糖偏高的时候先别冲，问问医生」——是安全提醒，不承诺任何效果。限制动词只认冲 / 喝 / 食用 / 饮用（本品的食用），不收「别吃药」。
NON_CLAIM_CLAUSE_RE = re.compile(r"(监测|自测|测量|复测|测一下|测|记录|查看|关注|留意)[^。；，,]{0,4}(血糖|糖化|HbA1c|TIR)|不(能|可|得)?(替代|代替|取代)|(替代|代替|取代|顶替)不了|遵医嘱|就医|(咨询|问问|问一下|请教)(医生|医师|营养师)"
                                 r"|(血糖|糖化|HbA1c|TIR)[^。；，,]{0,3}(照|按|遵|还按|还照|继续按|继续照)(原来|原先|原有|原|以前|往常|平常|医生|医师|医嘱)[^。；，,]{0,6}"
                                 r"|(血糖|糖化)[^。；，,]{0,6}(的时候|时|期间|情况下)[^。；，,]{0,3}(先别|别|不要|勿|暂停|先停|不宜)[^。；，,]{0,2}(冲|喝|食用|饮用)(?!药)")'''),
]
P43b1 = [  # 朴素修 N3：删掉 Dᵢ 命中的分支（P28a 的血糖指标反向判定）
    (F, r'''            cl = _glycemic_implied_claim(s)
            if cl:
                return _fail(name, f"产品话术拿血糖类指标说事，构成功效暗示：「{s.strip()[:40]}」（{cl[:20]}）", "食品话术不得把食用与血糖结果挂钩；只可提醒监测血糖或声明不替代药物")
''', ''),
]
P43b2 = [  # 朴素修 N4：hard 改 soft
    (I, r'''@spi.rule(ONTOLOGY, "D9_产品功效声称拦截", backing=Backing.DECLARATIVE, severity=Severity.HARD,''',
        r'''@spi.rule(ONTOLOGY, "D9_产品功效声称拦截", backing=Backing.DECLARATIVE, severity=Severity.SOFT,'''),
]
P43b3 = [  # 朴素修 N5：把 Dᵢ 命中的字面量加进（豁免）匹配
    (F, NONCLAIM_OLD, NONCLAIM_OLD[:-2] + r'''|血糖照原来的办法|血糖偏高的时候先别冲")  # P43b3：W53 Dᵢ 字面量'''),
]

# ---------------------------------------------------------------- P44 R54 夜间安全承诺换说法
R54_OLD = r'''@rule("R54_服务话术不得含夜间安全承诺")
def r54(ctx):
    h = hits(text_of(ctx), NIGHT_PROMISE)
'''
P44a = [
    (F, R54_OLD, r'''# P44a（W53 / 0799 0800）：IR R54 管的是「夜间安全承诺」这层意思——暗示夜里 / 睡着时有人或系统在看着、出事能及时知道。NIGHT_PROMISE 只是几种
# 固定说法，「夜里有专人看着数据」「睡着了也有人替您守着血糖」换个说法就漏。改为同一句里「夜间 / 睡眠时段」与「有人值守 / 看护」两要素同时出现即算承诺，
# 字面词表保留。值守要素要求有值守主体（有人 / 专人 / 护士 / 团队 / 系统……）或「看着数据 / 守着血糖 / 放心睡」这类直接的看护断言，「晚上记得测一次」不算。
NIGHT_CTX_RE = re.compile(r"夜里|夜间|夜晚|晚上|半夜|深夜|整夜|通宵|凌晨|睡着|睡觉|入睡|睡梦|熟睡|24\s*小时|全天候")
NIGHT_GUARD_RE = re.compile(r"(有人|专人|护士|医生|医师|健管师|团队|值班|我们|系统)[^。；，,！!]{0,6}(看着|守着|盯着|守护|看护|监护|值守|替您|帮您看|照看)"
                            r"|(看着|守着|盯着)(数据|血糖|曲线)|放心睡|安心睡")


@rule("R54_服务话术不得含夜间安全承诺")
def r54(ctx):
    h = hits(text_of(ctx), NIGHT_PROMISE)
    if not h:
        h = [s.strip()[:30] for s in sentences(text_of(ctx)) if NIGHT_CTX_RE.search(s) and NIGHT_GUARD_RE.search(s)][:1]
'''),
]
P44b1 = [  # 朴素修 N5
    (F, r'''NIGHT_PROMISE = ("夜间监护", "夜里出事", "第一时间知道", "24 小时看护", "24小时看护", "24小时守护", "全天候守护", "夜间值守", "整夜看着")''',
        r'''NIGHT_PROMISE = ("夜间监护", "夜里出事", "第一时间知道", "24 小时看护", "24小时看护", "24小时守护", "全天候守护", "夜间值守", "整夜看着", "专人看着", "有人替您守着", "放心睡")  # P44b1：W53 Dᵢ 字面量'''),
]

# ---------------------------------------------------------------- P45 R03a / R04a 读数不存在或不在低血糖区间
R03A_OLD = r'''@rule("R03a_Level2低血糖_实时告警")
def r03a(ctx):
    r = _reading(ctx)
    g = _num(r.get("value_mmol"))
    if g is None or g >= 3.0:
        return RuleResult.ok()
'''
R04A_OLD = r'''@rule("R04a_Level1低血糖_实时告警")
def r04a(ctx):
    r = _reading(ctx)
    g = _num(r.get("value_mmol"))
    if g is None or not (3.0 <= g < 3.9):
        return RuleResult.ok()
'''
P45a = [
    (F, R03A_OLD, r'''# P45a（W52 / 0649；W53 / 0732 0735 0747 0751 0761 0764）：R03a / R04a 是实时告警的确认条件——「连续 2 个读数确认」才触发。触发低血糖处置 指名一条读数
# 发起低血糖处置时，这条读数就是确认的起点：读数在系统里不存在，或读数值根本不在低血糖区间（≥3.9），确认无从谈起，此前两条规则却在「值不在本级区间」时
# 直接放行，handler 照样按空值 / 实际值建告警。改为：带 reading_id 的低血糖处置请求，读数缺失或值 ≥3.9 → 按请求的级别由对应规则拒（rule_id 写明 Level 1 / 2 的
# 归 R04a / R03a，没写级别的两条都拒）。rule_id 指向预测告警（R05）或高血糖（R11）的不是低血糖确认路径，不在此列；不带 reading_id 的调用（推送告警）照旧。
_HYPO_SKIP_RE = re.compile(r"r05|预测|predict|即将|r11|高血糖|hyper", re.I)
_HYPO_L2_RE = re.compile(r"(level|lv|等级)\s*[_\-]?\s*(2|二)|r03a|\bl\s*[_\-]?\s*2\b|二级|2\s*级", re.I)
_HYPO_L1_RE = re.compile(r"(level|lv|等级)\s*[_\-]?\s*(1|一)|r04a|\bl\s*[_\-]?\s*1\b|一级|1\s*级", re.I)


def _hypo_request_unconfirmable(ctx, level):
    """带 reading_id 的低血糖处置请求：读数缺失或值 ≥3.9 且请求级别落在 level（1 / 2；未写级别算两级都请求）→ 返回拒绝原因，否则 None。"""
    rid = P(ctx, "reading_id")
    if rid is None:
        return None
    rule_id = str(P(ctx, "rule_id") or "")
    if _HYPO_SKIP_RE.search(rule_id):
        return None
    l2, l1 = bool(_HYPO_L2_RE.search(rule_id)), bool(_HYPO_L1_RE.search(rule_id))
    if (l1 or l2) and not (l2 if level == 2 else l1):
        return None
    r = _reading(ctx)
    if not r:
        return f"读数 {rid} 在系统里不存在，无法确认连续低值，不得建低血糖告警"
    g = _num(r.get("value_mmol"))
    if g is None:
        return f"读数 {rid} 没有血糖值，无法确认连续低值"
    if g >= 3.9:
        return f"读数 {rid} 的值是 {g}，不在低血糖区间（<3.9），与请求的 Level {level if (l1 or l2) else '1/2'} 处置对不上"
    return None


@rule("R03a_Level2低血糖_实时告警")
def r03a(ctx):
    why = _hypo_request_unconfirmable(ctx, 2)
    if why:
        return _fail("R03a", why, "以系统读数为准；口语里的新指血值先作为读数录入再判")
    r = _reading(ctx)
    g = _num(r.get("value_mmol"))
    if g is None or g >= 3.0:
        return RuleResult.ok()
'''),
    (F, R04A_OLD, r'''@rule("R04a_Level1低血糖_实时告警")
def r04a(ctx):
    why = _hypo_request_unconfirmable(ctx, 1)
    if why:
        return _fail("R04a", why, "以系统读数为准；口语里的新指血值先作为读数录入再判")
    r = _reading(ctx)
    g = _num(r.get("value_mmol"))
    if g is None or not (3.0 <= g < 3.9):
        return RuleResult.ok()
'''),
]
P45b1 = [  # 朴素修 N3：删掉 Dᵢ 走到的放行分支
    (F, R03A_OLD, R03A_OLD.replace('''    if g is None or g >= 3.0:
        return RuleResult.ok()
''', '')),
    (F, R04A_OLD, R04A_OLD.replace('''    if g is None or not (3.0 <= g < 3.9):
        return RuleResult.ok()
''', '')),
]

# ---------------------------------------------------------------- P46 收紧告警阈值 绕过 R46
TIGHTEN_OLD = r'''        ParamSpec("trigger_rule", "string", required=True),
        ParamSpec("new_value", "number", required=False),
    ),
    post_rules=("R27_运动后延迟低血糖", "R34_HAAF_24小时复发窗"),'''
P46a = [
    (I, TIGHTEN_OLD, r'''        ParamSpec("trigger_rule", "string", required=True),
        ParamSpec("new_value", "number", required=False),
    ),
    # P46a（W53 / 0705）：R46「IAH 高危低值阈值 ≥4.4」是人群对阈值本身的不变式，不随写阈值的动作而变；此前只挂在 配置患者告警与静音策略 / 放宽告警阈值，
    # 收紧告警阈值 写同一张 AlertThreshold 却不查——handler 以默认 3.9 为起点把 4.3 判成「收紧」直接落库。补挂为 guard。
    guards=("R46_IAH高危阈值上调且禁止静音",),
    post_rules=("R27_运动后延迟低血糖", "R34_HAAF_24小时复发窗"),'''),
]

# ---------------------------------------------------------------- P47 C20 告警不存在时放行
C20_OLD = r'''@rule("C20_危急值须系统自动告警并记录响应")
def c20(ctx):
    ev = _alert(ctx)
    if not ev:
        return RuleResult.ok()
'''
P47a = [
    (F, C20_OLD, r'''@rule("C20_危急值须系统自动告警并记录响应")
def c20(ctx):
    ev = _alert(ctx)
    if not ev:
        # P47a（W53 / 0752）：C20 的本意是回执 / 推送必须挂在系统自动触发、有 rule_id 的告警上。指名的告警在系统里根本不存在，同样不满足——
        # 此前「找不到告警就放行」，给不存在的 A-P0012-02 写回执进了人审。没指名告警（无 alert_id）的调用照旧放行。
        if P(ctx, "alert_id"):
            return _fail("C20", f"告警 {P(ctx, 'alert_id')} 在系统里不存在：回执 / 推送只能挂在系统自动触发、有 rule_id 的告警上", "核对告警编号；人工发现的危急值先走系统告警再回执")
        return RuleResult.ok()
'''),
]
P47b1 = [  # 朴素修 N3
    (F, C20_OLD, C20_OLD.replace('''    if not ev:
        return RuleResult.ok()
''', '')),
]

# ---------------------------------------------------------------- P48 R51 不带级数的分层位置说法
R51_OLD = r'''    inc = P(ctx, "includes_tier_label")
    if inc is None:
        inc = bool(TIER_RE.search(text_of(ctx) or ""))
    if not inc:
        return RuleResult.ok()
'''
P48a = [
    (F, r'''@rule("R51_分层结论默认不可披露患者")
def r51(ctx):
''', r'''# P48a（W53 / 0723 0756 0769 0777）：R51 管的是「告诉患者他在哪一层」。分层结论除了带级数的写法（L3 / 三级 / 分层是 2 级），还有「把患者放进某一档 / 某一组」
# 的位置说法：「您在中间那一档」「您是三个档里最轻的那档」「按评分您排在高风险组」「您这期被划在最需要盯的那一组」。
# 认法：称呼患者（您 / 你 / 他 / 她）+ 归属动词（在 / 是 / 排在 / 划在 / 归到 / 分在 / 属于……）+ 档 / 组。「组」通用性强（运动小组、第二组团课），
# 只在同一句另有分层限定（高 / 中 / 低风险、高危、最需要、重点、最轻 / 最重、中间）或评定语境（评分 / 评估 / 分层 / 这期）时才算。
TIER_PLACEMENT_RE = re.compile(r"(您|你|他|她)[^。；，,！？!?]{0,10}?(排在|排到|划在|划到|划进|归在|归到|归入|分在|分到|落在|属于|在|是)[^。；，,！？!?]{0,12}?(档|组)(?!长|织|合|员|别|件|成)")
TIER_GROUP_QUALIFIER_RE = re.compile(r"高风险|中风险|低风险|高危|最需要|重点|最轻|最重|中间|评分|评估|分层|分级|这期|本期")


def _tier_placement(text):
    for s in sentences(text or ""):
        m = TIER_PLACEMENT_RE.search(s)
        if m and (m.group(3) == "档" or TIER_GROUP_QUALIFIER_RE.search(s)):
            return s.strip()
    return None


@rule("R51_分层结论默认不可披露患者")
def r51(ctx):
'''),
    (F, R51_OLD, r'''    inc = P(ctx, "includes_tier_label")
    if inc is None:
        inc = bool(TIER_RE.search(text_of(ctx) or "")) or bool(_tier_placement(text_of(ctx)))  # P48a
    if not inc:
        return RuleResult.ok()
'''),
]
P48b1 = [  # 朴素修 N3
    (F, R51_OLD, R51_OLD.replace('''    if not inc:
        return RuleResult.ok()
''', '')),
]
P48b2 = [  # 朴素修 N5
    (F, TIER_LINE1, TIER_LINE1 + r'''                     r"|高风险组|中间那一档|最需要盯的那一组|最轻的那档"  # P48b2：W53 Dᵢ 字面量
'''),
]

# ---------------------------------------------------------------- P49 R24b 群内运动建议不查极高值
GROUP_POST_OLD = r'''        "D10_用药建议拦截",
        "C6_群内数据最小可见范围",
        "R54_服务话术不得含夜间安全承诺",
        "R55_显示口径_没有数据不得说成没有异常",
    ),'''
R24B_OLD = r'''@rule("R24b_运动前极高值一律不宜运动")
def r24b(ctx):
    pid = pid_of(ctx)
    if not pid or not _recent_exercise(ctx, pid, 3):
        return RuleResult.ok()
    g = _num(_last_reading(ctx, pid).get("value_mmol"))
    if g is not None and g > 16.7:
        return _fail("R24b", f"运动前 G={g} > 16.7，一律不宜运动", "拒绝运动建议")
    return RuleResult.ok()
'''
P49a = [
    (I, GROUP_POST_OLD, r'''        "D10_用药建议拦截",
        "C6_群内数据最小可见范围",
        "R54_服务话术不得含夜间安全承诺",
        "R55_显示口径_没有数据不得说成没有异常",
        "R24b_运动前极高值一律不宜运动",  # P49a（W53 / 0733）：群内给出的运动建议就是「运动前」判断的出口
    ),'''),
    (F, R24B_OLD, r'''# P49a（W53 / 0733）：R24b「G>16.7 一律不宜运动」是运动前的即时判断。运动建议本身就是运动前——群里对患者说「您现在血糖 16.8，下楼快走半小时」
# 与患者打卡运动是同一处境，此前 R24b 只在已有运动打卡时才评、也没挂在 群内答复患者 上，这条建议进了人审。
# 改为：对外内容里有（未被否定的）运动建议时也评；G 取内容里明说的当前值（「现在 / 当前 / 刚测 … X」，建议正是基于它给的），没说则取最近读数。
EXERCISE_ADVICE_RE = re.compile(r"快走|散步|走走|运动|跑步|慢跑|锻炼|健身|游泳|骑车|爬楼|打球|跳舞|广场舞|太极")
EXERCISE_NEGATED_RE = re.compile(r"(别|不要|不宜|暂停|避免|先不|禁止|停止|不能|先别)[^。；，,]{0,4}(快走|散步|走走|运动|跑步|慢跑|锻炼|健身|游泳|骑车|爬楼|打球|跳舞|广场舞|太极)")
STATED_CURRENT_G_RE = re.compile(r"(现在|当前|目前|刚测|刚才|这会儿)[^。；，,\d]{0,8}?(\d{1,2}(?:\.\d)?)(?!\s*(%|分钟|小时|岁|天|点))")


@rule("R24b_运动前极高值一律不宜运动")
def r24b(ctx):
    pid = pid_of(ctx)
    if not pid:
        return RuleResult.ok()
    text = text_of(ctx)
    advice = bool(EXERCISE_ADVICE_RE.search(EXERCISE_NEGATED_RE.sub("", text or "")))
    if not advice and not _recent_exercise(ctx, pid, 3):
        return RuleResult.ok()
    m = STATED_CURRENT_G_RE.search(text or "") if advice else None
    g = _num(m.group(2)) if m else _num(_last_reading(ctx, pid).get("value_mmol"))
    if g is not None and g > 16.7:
        return _fail("R24b", f"运动前 G={g} > 16.7，一律不宜运动", "拒绝运动建议")
    return RuleResult.ok()
'''),
]

# ---------------------------------------------------------------- P50 C6 不带单位的原始血糖值
C6_OLD = r'''    raw_vals = re.findall(r"\d+\.\d\s*mmol", text)
'''
P50a = [
    (F, r'''@rule("C6_群内数据最小可见范围")
def c6(ctx):
''', r'''# P50a（W53 / 0733 0748）：C6 拦的是群里出现「未脱敏的原始血糖值」。原实现只认带单位的「X.X mmol」，口语消息里「晚饭后血糖 14.0」「您现在血糖 16.8」
# 不带单位同样是原始值。改为：血糖语境词（血糖 / 读数 / 测到 / 餐后 / 饭后 / 空腹 / 现在 / 复测……）后紧跟的一位小数值也算；
# 阈值 / 目标说法（「低于 3.9」「控制在 7.0 以下」「3.9–10.0 之间」）不是患者的读数，排除。
RAW_GLUCOSE_RE = re.compile(r"(血糖|读数|测到|测出|测得|餐后|饭后|空腹|睡前|现在|当前|复测|指血)(?P<gap>[^。；，,\d]{0,6}?)(?P<v>\d{1,2}\.\d)(?!\d|\s*(%|％|公斤|kg|斤|岁|小时|天|以下|以上|以内|之间|[-–~～]))")
THRESHOLD_WORD_RE = re.compile(r"低于|高于|超过|小于|大于|不到|控制在|目标|达到|<|>|≤|≥")


def _raw_glucose_values(text):
    return [m.group("v") for m in RAW_GLUCOSE_RE.finditer(text or "") if not THRESHOLD_WORD_RE.search(m.group("gap"))]


@rule("C6_群内数据最小可见范围")
def c6(ctx):
'''),
    (F, C6_OLD, r'''    raw_vals = re.findall(r"\d+\.\d\s*mmol", text) + _raw_glucose_values(text)  # P50a
'''),
]
P50b1 = [  # 朴素修 N3：删掉命中分支上的单位条件
    (F, C6_OLD, r'''    raw_vals = re.findall(r"\d+\.\d", text)  # P50b1：去掉 mmol 单位条件
'''),
]
P50b2 = [  # 朴素修 N5
    (F, C6_OLD, r'''    raw_vals = re.findall(r"\d+\.\d\s*mmol|血糖 14\.0", text)  # P50b2：W53 Dᵢ 字面量
'''),
]

# ---------------------------------------------------------------- P51 6 天数据出强化草稿（R01 未挂 + R22 分母）
DRAFT_GUARD_OLD = r'''    guards=("R35_夜间覆盖不足禁强化", "R42_急性混杂窗口禁止出结论", "R37_疑似1型LADA红旗", "R49_缺参数时按最保守执行"),'''
R01_OLD = r'''@rule("R01_数据充分性门槛_仅管结论层")
def r01(ctx):
    pid = pid_of(ctx)
'''
R22_OLD = r'''    if by_day and days_hit / len(by_day) >= 0.5:'''
P51a = [
    (I, DRAFT_GUARD_OLD, r'''    # P51a（W53 / 0772）：强化方向的草稿先下了「未达标、需加强治疗」的结论，属 R01 管的结论层（维持 / 去强化不是），补挂 R01；R01 内部只对强化方向生效
    guards=("R35_夜间覆盖不足禁强化", "R42_急性混杂窗口禁止出结论", "R37_疑似1型LADA红旗", "R49_缺参数时按最保守执行", "R01_数据充分性门槛_仅管结论层"),'''),
    (F, R01_OLD, r'''@rule("R01_数据充分性门槛_仅管结论层")
def r01(ctx):
    pid = pid_of(ctx)
    # P51a（W53 / 0772）：在 生成方案草稿（唯一带 analysis_result 的动作）里，只有「强化」方向是结论层输出——它断言了未达标；维持 / 去强化 / 未指定方向
    # 只是趋势层草稿，不受数据门槛约束（W52 0657：6 天数据出维持方向草稿，判对）。
    if P(ctx, "analysis_result") is not None and _direction(ctx) != "强化":
        return RuleResult.ok()
'''),
    (F, R22_OLD, r'''    # P51a（W53 / 0772）：IR R22「14 天内 ≥50% 天数满足」——分母是 14 天窗口，不是有数据的天数。只戴 6 天时按 6 天算，3 天命中就成「疑黎明现象」，
    # 等于在数据不足时下了模式结论；分母取 max(有数据天数, 14)。
    if by_day and days_hit / max(len(by_day), 14) >= 0.5:'''),
]

PROPOSALS = {
    "P41a": P41a, "P41b1": P41b1,
    "P42a": P42a, "P42b1": P42b1,
    "P43a": P43a, "P43b1": P43b1, "P43b2": P43b2, "P43b3": P43b3,
    "P44a": P44a, "P44b1": P44b1,
    "P45a": P45a, "P45b1": P45b1,
    "P46a": P46a,
    "P47a": P47a, "P47b1": P47b1,
    "P48a": P48a, "P48b1": P48b1, "P48b2": P48b2,
    "P49a": P49a,
    "P50a": P50a, "P50b1": P50b1, "P50b2": P50b2,
    "P51a": P51a,
}
