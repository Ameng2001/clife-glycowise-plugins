# 本体插件校验报告：plugins/glycowise/

- 校验对象：`plugins/glycowise/`（`__init__.py` 4493 行 + `mappings/objects.yaml` + `cq/golden.yaml` + `plugin.yaml`）
- 期望基准：`studio/changes/glycowise/ontology-map.md`（IR，iteration 1）
- 事实基准：`studio/changes/glycowise/decisions/confirmed-facts.md`
- 执行引擎：clife-onto-engine 0.1.0（临时克隆副本，插件按只读方式载入）
- 校验日期：2026-09-05
- 校验人：ontology-validate（只诊断，未修改插件与引擎任何一行）

## 结论先说

**待 FDE 收尾，且 A 段有 1 个 BLOCKER 必须先回改 IR §5 再重编译。**

编译本身的保真度很高：92 条规则、63 个 Action、62 个 Object、40 条 Link、28 个 Function、62 条映射全部按 IR 落地，`guards / post_rules / writes / hil / severity / backing / evaluation / priority / phase` 逐字段比对零偏差。问题不在编译器，在 IR 自身 §4.3 与 §5 两张表没对齐，编译器忠实地照 §5 编，于是 §4.3 单方面声明的三条挂载点被丢掉了。

| 段 | 结论 |
|---|---|
| A 结构完整性 | ❌ 1 个 BLOCKER + 1 项告警。正向引用零悬空，反向有 3 条规则成为死规则 |
| B 治理审计 | ⚠ 7 条治理缺口（与 IR §4.5 声明一致，逐条已核实）+ 5 条对外/凭证类 Action 未设 hil |
| C 剩余 FDE TODO | declarative 全自动 30 / function 待填 62 / Action 待填 63 / seed 待填 1 |
| D 行为 CQ | 28 条：PASS 9 / SKIPPED 19 / **FAIL 0**。无结构性错误 |

---

## A. 结构完整性

### A.1 正向引用：全部解析成功

用引擎注册表逐项核对（不是文本匹配，是 import 后从 `spi.registry` 读出来比）：

| 检查项 | 结果 |
|---|---|
| 63 个 Action 的 `guards` 引用规则是否已声明 | ✅ 零悬空 |
| 63 个 Action 的 `post_rules` 引用规则是否已声明 | ✅ 零悬空 |
| 63 个 Action 的 `writes` 引用对象是否已声明 | ✅ 零悬空 |
| 40 条 Link 的 `from` / `to` 是否已声明对象 | ✅ 零悬空 |
| 28 个 Function 的 `reads` 是否已声明对象 | ✅ 零悬空 |
| 62 条映射与 62 个 Object 是否一一对应 | ✅ 无未映射对象，无孤儿映射 |
| 与 IR §5 Actions 全表逐字段比对 | ✅ 63/63 完全一致，零差异 |
| 与 IR §4.3 Rules 全表的 severity / backing / evaluation | ✅ 92/92 一致 |
| `RULE_BANDS` 的 priority / phase 与 IR §4.1/§4.2 | ✅ 92/92 一致 |

### A.2 ❗BLOCKER：R57 / R58 / R59 注册了但永远不会被评估

```
注册但未被任何 Action 挂载的规则：
  R57_15-15三轮无效强制升级就医
  R58_Level3严重低血糖强制转诊
  R59_老年非典型症状疑似低血糖
```

这三条恰好就是 IR §「专家复核记录」里临床评审**新补建**的三条安全规则——15-15 三轮无效强制就医、Level 3 不看血糖数值强制转诊、老年跌倒/意识模糊联动疑似低血糖。IR 自己在 §4.3 的 `on_actions` 列写明了挂载点：

| 规则 | IR §4.3 声明的挂载点 | IR §5 Actions 表实际有没有 |
|---|---|---|
| R57 | 响应并回执告警、推送告警 | ❌ 两个 Action 的 guards/post_rules 里都没有 R57 |
| R58 | 记录症状与处置、推送告警、转介医师 | ❌ 三个都没有 |
| R59 | 记录症状与处置、生成去强化证据工单 | ❌ 两个都没有 |

编译器读的是 §5，§5 没写，于是编出来的插件里这三条规则有 `RuleDef`、有 `source`、有 `citations`、有骨架函数，但**没有任何执行路径会调用它们**。引擎的 `_eval_rules` 只遍历 Action 声明的 guards/post_rules，规则不挂在任何 Action 上就等于不存在。

为什么这条判 BLOCKER 而不是告警：R58 的语义是「Level 3 严重低血糖命中即强制转诊，不看血糖数值」，R57 是「15-15 三轮无效强制升级就医」。这是低血糖处置链条的末端兜底，IR 自己写的是"这是处置链条最危险的一环，此前 87 条里没有一条兜住"。补建了却接不上线，等于没补。

**修复指引（改 IR，不改插件）**：回 `ontology-map.md` §5 Actions 表，给下列行补 `post_rules`（R57/R58 是 hard、R59 是 soft，全部 function-backed、post_write，应进 post_rules 而非 guards）：

- `响应并回执告警` post_rules 补 `R57_15-15三轮无效强制升级就医`
- `推送告警` post_rules 补 `R57`、`R58_Level3严重低血糖强制转诊`
- `记录症状与处置` post_rules 补 `R58`、`R59_老年非典型症状疑似低血糖`
- `转介医师` post_rules 补 `R58`
- `生成去强化证据工单` post_rules 补 `R59`

补完重跑 `/studio-ontology:compile glycowise`。**不要直接手改 `plugins/glycowise/__init__.py`**——IR 是唯一真源，手改会在下次编译时被覆盖，而且 §4.3 与 §5 的不一致仍然留在 IR 里。

### A.3 告警：元规则「低血糖优先抢占」的覆盖面缺两个出口

IR §4.3 给它的 `on_actions` 是四个：生成方案草稿、生成AGP与指标报告、输出服务分层标签、生成结营报告。插件里只挂到前两个。

缺的两个恰恰是结论层的对外出口。IR §4.1 的第一条硬语义写的是「B1 命中时，B2–B5 产生的任何加强降糖 / 限食 / 增加运动量方向的建议一律抑制并留痕」——`输出服务分层标签` 和 `生成结营报告` 正是 B5 结论层的产物，抑制关系管不到它们，就意味着一个当期出现过 Level 2 低血糖的患者，仍可能拿到一份按 TIR 偏高口径写的分层标签或结营解读。同 A.2，根因在 IR §5 漏写，修法一样。

### A.4 §4.3 与 §5 全面比对：35 条规则的挂载点两表不一致

除上述两处外，还有 32 条规则出现「§5 比 §4.3 挂得更多」的情况（例如 `D11a_签发人资质失效自动冻结` 在 §4.3 声明 3 个挂载点，§5 实际挂在 8 个 Action 上）。这一类是 §5 更完整、§4.3 的 `on_actions` 列没跟上，不影响运行时行为，但让 IR 内部出现了两个互相矛盾的事实来源。

**建议**：把 §4.3 的 `on_actions` 列明确降级为「说明性注释」，或者在下一轮迭代时由 §5 反向重生成。否则下一个读 IR 的人（或下一次编译）不知道该信哪张表——A.2 这个 BLOCKER 就是这么产生的。

---

## B. 治理审计

### B.1 缺依据的规则：实测 7 条，与 IR §4.5 声明的 7 条完全一致

逐条列出（`source` 字段原文取自插件，非 IR 转述）：

| # | 规则名 | 缺什么 | 现有 citations |
|---|---|---|---|
| 1 | `R12_SGLT2i酮症警觉` | 药物机制层面成立，缺 SGLT2i euDKA 的权威指南条目 | research/sources/02 §6.4、§8 R12；behavior-matrix §7.1 G1b |
| 2 | `R22_黎明现象` | 研究文档自标"临床常规定义"，缺权威出处 | research/sources/02 §8 R22 |
| 3 | `R27_运动后延迟低血糖` | Colberg 2016 原文阈值待逐字核对（研究文档 §9 自列待核实第 2 条） | research/sources/02 §8 R27 |
| 4 | `R33_停药观察期反弹预警` | 阈值待临床确认，remission-assessment D4 自标"未经临床签字不得上线" | remission-assessment D4 |
| 5 | `R44_高危用药禁止闭环` | 机制方向由 Endocrine Society 2022 与中国糖尿病防治指南 2024 支持，但"可持续 24–72 小时"这个具体时长两份基准文档均无逐字出处 | daily-monitoring D21；behavior-matrix §6 hypo_state |
| 6 | `D11a_签发人资质失效自动冻结` | 缺《医师法》与营养师注册管理的具体条款号 | review-and-plan D11a；domain-canvas D18 |
| 7 | `C20_危急值须系统自动告警并记录响应` | 医疗质量安全核心制度「危急值报告制度」缺具体文号 | research/sources/04 §6 风险 20；daily-monitoring §2.4 |

**核实结论**：IR §4.5 说 7 条，实际就是这 7 条，一条不多一条不少，规则名与缺口描述也对得上。这 7 条全部是研究文档自己标注待核实、或临床/合规复核时点出无逐字出处的条目，属于**显式缺口**而非建模遗漏。

⚠ 顺带指出一处 IR 内部矛盾：IR §「遗留 TODO(FDE) 清单」T-2 写的是「§4.5 × 6：R12、R22、R27、R33、D11a、C20」，**漏了 R44**。以 §4.5 正文（7 条）与插件实际（7 条）为准，T-2 的数字要改成 7。

### B.2 `source = 通用` 的规则：16 条，判合规不计缺口

按技能定义，`通用`（自明 / 工程口径）算合规。实测 16 条，且全部在括号里注明了工程口径的来源，写法比"通用"两个字扎实：

`R36_active率超100自检`（工程自检口径）、`R48_去重键必须用传感器序号`（confirmed-facts R-1，依据 A1-6）、`R49_缺参数时按最保守执行`（domain-canvas 架构护栏 D2）、`R35_夜间覆盖不足禁强化`（confirmed-facts 一期医源性伤害路径对策 ①）、`R50_夜间低覆盖高危用药进临床队列`（对策 ③）、`R45_紧急告警豁免关键词闸`（C-10）、`R56_告警模板预审冻结`（C-10 配套）、`R52_回填读数不得触发实时告警`（架构护栏 D4）、`R53_低置信通道不得独立触发危急告警`（daily-monitoring D7a）、`D13_签发反橡皮图章检测`（内部质控 SOP）、`R38_告警兜底配置未完成禁止佩戴`（内部 SOP）、`R39_覆盖告知未留痕禁止入组成功`（B-11、B-13）、`R54_服务话术不得含夜间安全承诺`（B-11）、`R40_老年画像禁止仅靠自觉同步`（enrollment D11e）、`R43_落库验证未通过禁止入组成功`（enrollment D11b）、`R55_显示口径_没有数据不得说成没有异常`（B-12）。

注：IR §「完整性自检」写的是 11 条，实测 16 条。差额是 IR 自检时点数不准，不是缺陷——多出来的 5 条也都带了括号说明。

### B.3 citations 覆盖率：92/92 全有，但性质需要说明

零条规则的 `citations` 为空，这一项过。但要提醒一件事：**92 条里有 91 条的 citations 全部指向内部产物**（confirmed-facts / behavior-matrix / domain-canvas / processes / research/sources / 临床复核记录），没有一条指向标准号或法条条款号。

这套 IR 的约定是：权威出处放 `source`，内部可追溯性放 `citations`。这个分工本身合理，但对 clife-onto-engine 的 `export_okf` 有影响——如果 OKF 导出按 `citations` 找权威依据，glycowise 会导出 91 条"引用只到内部文档"的规则。**建议**：要么在 OKF 导出时明确以 `source` 为权威字段，要么在下一轮把合规类规则的法条号从 `source` 冗余一份进 `citations`。这是告警，不是 BLOCKER。

`source` 里带具体法条 / 指南条目的规则共 69 条（92 − 7 缺依据 − 16 通用），覆盖了全部器械经营、PIPL、互联网诊疗、广告法、食品安全法条款以及 ADA / CDS / ATTD / Danne / Endocrine Society / 中国老年糖尿病诊疗指南等临床基准。这一块做得比一般项目扎实。

### B.4 hil 覆盖：40/63 已设，5 条对外/凭证类未设 → 告警

已正确设 hil 的关键动作：`签发方案`（医师/注册营养师/运动康复师）、`输出服务分层标签`（医师·披露授权）、`发布宣传素材` / `生成产品推荐` / `创建服务包SKU` / `上架产品SKU` / `建立厂商云通道对接`（合规官）、`兑现结果承诺`（店长 + 医师联合确认）、`处理数据主体权利请求`（合规官受理）。confirmed-facts B-3（AI 只出草稿、医师签发）与 B-2（服务与产品分离）在 hil 层落得住。

以下 5 条属对外投递或凭证管理，但未设 hil：

| Action | 为什么该告警 | 缓解因素 |
|---|---|---|
| `维护凭证台账` | 资质台账是 D11a 冻结判定的唯一数据源，改台账等于改冻结判定的前提，无人工复核 | post_rules 挂了 D11a 自查 |
| `生成AGP与指标报告` | 报告直接进医师签发流程，属对外凭证 | guards 有 R01、post 有 12 条规则兜 |
| `推送方案至患者` | 患者侧终端投递 | 上游 `签发方案` 已有医师 hil；guards 有 R51/C9 |
| `记录载体覆盖变更并强制告知` | 覆盖状态告知是 B-11 夜间承诺红线的执行动作 | post 有 R54/R55 |
| `撤回同意` | PIPL 权利响应，需级联下游并留痕 | 对照组 `处理数据主体权利请求` 设了合规官 hil，此处未设，两者口径不一致 |

其中 **`撤回同意` 最该补**——同为 PIPL 权利响应，一个设了合规官 hil、一个没设，是口径不一致而不是有意的设计取舍。`维护凭证台账` 次之。其余三条有规则层兜底，可接受，但建议在 IR §5 里留一句说明为什么不设，免得下次复核重新提一遍。

### B.5 附带发现：plugin.yaml 用不了引擎的 `load_manifest`

`plugins/glycowise/plugin.yaml` 的顶层键是 `plugin / ontology_id / provides / kind / counts / fde_todo`，而引擎 `SPI.load_manifest` 读的是 `ontology / schema / mappings / glossary / agents`（见 `clife_onto_engine/sdk/registry.py`）。实测 `spi.load_manifest("plugins/glycowise/plugin.yaml")` 抛 `KeyError: 'ontology'`。

对照引擎自带的 `plugins/grass/plugin.yaml`，它用的是 `ontology: grass` 且填了槽位 5（glossary 术语表）与槽位 6（agents 复核角色）。

实际影响有限——mappings 是 `__init__.py` 第 4493 行 `spi.load_mappings(...)` 自己加载的，import 一次全都在。但两件事值得记下：

1. glycowise 的 plugin.yaml 目前是**纯元数据文件**，引擎不消费它。如果后续走声明式加载路径会直接报错。
2. **七个 SPI 槽位里，槽位 5（glossary 术语表）与槽位 6（agents 复核角色）是空的**。槽位 5 对这个项目其实有用：意图编译器拿它约束 LLM 用规范键，而 glycowise 有大量中英混用的字段（`hypo_risk_med` / `无感知低血糖`、`nocturnal_coverage_pct` / `夜间覆盖率`、`active_pct` / `有效率`），正是键名漂移的高发区。槽位 6 也现成——63 个 Action 里 40 个已经写了 `reviewer_role`，聚合一下就是复核角色表。

这属于编译器的能力边界（当前 compile 只填 1/2/3/4/7 五个槽位），不是本次插件的缺陷，记在这里供下一轮迭代参考。

---

## C. 剩余 FDE TODO

```
declarative 全自动  30 条（规则体由 IR check 全自动生成，已可运行）
function 待填       62 条（全部仍 raise NotImplementedError）
Action 待填         63 个（全部 handler 仍 raise NotImplementedError）
seed 待填            1 处（seed_reference_data 仍为 pass）
```

与 `plugin.yaml` 的 `fde_todo` 声明（62 / 63 / 7 / 1）逐项吻合，编译器没有虚报。

**30 条 declarative 规则确实是活的**——全部 30 条已生成可执行判定体，无一残留 `NotImplementedError`，D 段跑出来的 9 条 PASS 全部来自这一批。

**62 条 function-backed 规则**：函数体全部是 `# TODO(FDE): 查…` 注释 + `raise NotImplementedError`，注释里点名了要查什么对象、什么窗口。四条低血糖规则的 TODO 注释还额外写了「禁止复用另一口径」的硬边界警告（见下方专项核实）。

**63 个 Action handler**：骨架统一为「`ctx.stage_write` 示例注释 + `ctx.set_confidence(0.8)` + `raise NotImplementedError`」。`writes` 声明齐全，FDE 照着 writes 列表补 stage_write 即可，key 命名由 FDE 定。

**`seed_reference_data` 仍为 `pass`** → 告警。它的 docstring 点名了七类参考数据：BannedTermLibrary 禁用词库（D8/D9/D10/D11 依赖）、ChannelRegistry 通道能力与存储地域、DeviceModel 采样间隔/预热/MARD、MetricRegistry 指标口径台账、Credential 资质台账、冻结告警模板库（R56 依赖）、人群目标区间参数表（R28/R31/R46/R49 依赖）。

这一项的实际后果在 D 段看得很清楚：`D8_禁用词拦截` 是 declarative、判定体已生成（`banned_term_hits == 0`），但 `banned_term_hits` 这个数从哪来？从禁用词库比中来。seed 空着，禁用词类规则就算判定体写好了也拦不住真东西。**建议 FDE 把 seed 排在 62 条函数体之前做**——它是一批规则共同的前置依赖，先有数据才好验函数。

---

## D. 行为 CQ（在引擎上实跑）

### 方法说明

`cq/golden.yaml` 的 28 条是自然语言问句 + `expect` 标记，引擎的 `run_cq_suite` 吃的是 `ActionCQ` / `QueryCQ` 结构化对象（对照 `plugins/grass/cq.py`），两者格式不通。本次校验由校验方逐条把问句翻成引擎调用后实跑，未修改插件。

另有一处引擎机制需要说明：63 个 Action 里只有 20 个 `validate_supported=True`，而 `run_cq_suite` 的 action 分支走的是 `engine.validate`，对另外 43 个会直接抛 `ValueError`。因此本次统一走 `engine.execute`（真跑 guard → handler → post_rules 全链），这样更严格，也能真实区分「被规则拦住」与「撞上未填骨架」。

引擎的求值顺序是：授权 → guards（按声明顺序全部求值，不短路）→ handler → post_rules。所以只有当目标规则是 **declarative 且挂在 guards 上、且排在它前面的 guards 也全是 declarative** 时，才能在骨架未填的情况下真跑通。这就是 PASS 与 SKIPPED 的分界线。

### D.1 query 类 7 条 —— 全 PASS

对每条问句构造对应的 OQL 查询，播入一行合成数据后执行：

| # | 问句 | 起点对象 | 结果 |
|---|---|---|---|
| 1 | 最近 14 天 TIR/TBR/CV，数据够不够出结论 | CgmSummary | ✅ PASS（1 行） |
| 2 | 昨夜 00:00–06:00 有无低血糖事件、各持续多久 | HypoEpisode | ✅ PASS（1 行） |
| 3 | 哪些患者夜间有效覆盖率低于 70% | CgmSummary | ✅ PASS（1 行） |
| 4 | 68 岁用胰岛素该按哪套目标区间 | PatientProfile | ✅ PASS（1 行） |
| 5 | 这份 14 天报告能不能用 GMI 判缓解 | CgmSummary | ✅ PASS（1 行） |
| 6 | 读数里多少是回填、多少来自 OCR | GlucoseReading | ✅ PASS（1 行） |
| 7 | 上周哪几份方案停留不到 20 秒就签发 | ReviewEvidence | ✅ PASS（1 行） |

7 条全部能落到已声明的对象类型上，OQL 通过 schema 校验并返回结果。**这说明 Object 层的字段设计确实撑得住这些业务问题**——`nocturnal_coverage_insufficient`、`is_backfill`、`source_channel`、`review_suspicious`、`metric_provenance` 这些字段不是摆设，CQ 问到什么就有什么字段接。第 7 条尤其值得一提：「停留不到 20 秒就签发」这种反橡皮图章的问题能直接查，是因为 `ReviewEvidence` 建了 `dwell_time` 和 `review_suspicious`。

### D.2 action 类 6 条 —— 全 SKIPPED (FDE TODO)

| # | CQ | 实跑结果 |
|---|---|---|
| 1 | action(生成方案草稿) | ⏭ SKIPPED —— 撞 `R42_急性混杂窗口禁止出结论` 骨架 |
| 2 | action(签发方案) | ⏭ SKIPPED —— 撞 `D11a_签发人资质失效自动冻结` 骨架 |
| 3 | action(收紧告警阈值) | ⏭ SKIPPED —— 撞 handler 骨架 |
| 4 | action(生成去强化证据工单) | ⏭ SKIPPED —— 撞 handler 骨架 |
| 5 | action(判定缓解结果) | ⏭ SKIPPED —— 撞 `D11a` 骨架 |
| 6 | action(响应并回执告警) | ⏭ SKIPPED —— 撞 `R44_高危用药禁止闭环` 骨架 |

符合预期。`expect: action(X)` 要求 `committed`，而 committed 的前提是 handler 真的写了东西——63 个 handler 全是骨架，这 6 条在 FDE 填完之前不可能过。**这不是失败，是 FDE 还没干活。**

值得注意的是 6 条里有 4 条不是撞在自己的 handler 上，而是撞在**前置的 function-backed guard** 上（R42、D11a×2、R44）。意味着 FDE 填 handler 之前得先填这几条 guard 规则，否则动作根本走不到 handler。这给 FDE 的实现顺序提了个醒：**guard 类 function-backed 规则应优先于 handler 实现**。

### D.3 rejected 类 15 条 —— PASS 2 / SKIPPED 13 / FAIL 0

| # | CQ 场景 | 期望拦截规则 | 结果 | 说明 |
|---|---|---|---|---|
| 1 | 夜间覆盖 41% 要生成强化草稿 | R35_夜间覆盖不足禁强化 | ⏭ SKIPPED | 同 Action 的前置 guard `R42` 是骨架，先炸；R35 本身是 declarative 已可判 |
| 2 | 才戴 6 天就要发分层结论 | R01_数据充分性门槛_仅管结论层 | ✅ **PASS** | guard 阶段拦住，命中 `['R01', 'R51']` |
| 3 | 方案里写"逆转有望" | D8_禁用词拦截 | ⏭ SKIPPED | D8 是 post_rule，handler 骨架先炸 |
| 4 | 按 L3 分级配英纽林疗程 | R32_产品推荐合规闸 | ⏭ SKIPPED | 撞前置 guard `C4_数据用于产品推荐须单独同意` 骨架 |
| 5 | 健管师改二甲双胍剂量 | D10_用药建议拦截 | ⏭ SKIPPED | D10 自身是 function-backed 骨架 |
| 6 | 过期营养师签发方案 | D11a_签发人资质失效自动冻结 | ⏭ SKIPPED | D11a 自身是 function-backed 骨架 |
| 7 | 未签同意先拉数据 | C3_敏感个人信息单独同意 | ⏭ SKIPPED | C3 自身是 function-backed 骨架 |
| 8 | 回填读数推紧急告警 | R52_回填读数不得触发实时告警 | ⏭ SKIPPED | 撞前置 guard `R56_告警模板预审冻结` 骨架；R52 本身 declarative 已可判 |
| 9 | OCR 识别 2.8 发危急告警 | R53_低置信通道不得独立触发危急告警 | ⏭ SKIPPED | 同上，撞 `R56` |
| 10 | 磺脲患者复测 4.1 即闭环 | R44_高危用药禁止闭环 | ⏭ SKIPPED | R44 自身是 function-backed 骨架 |
| 11 | 服务包写"夜里出事我们第一时间知道" | R54_服务话术不得含夜间安全承诺 | ✅ **PASS** | guard 阶段拦住，命中 `['R54']` |
| 12 | 没数据也发"今天平稳" | R55_显示口径_没有数据不得说成没有异常 | ⏭ SKIPPED | R55 是 post_rule，handler 骨架先炸 |
| 13 | 发前后对比案例到朋友圈 | C16_禁止发布患者前后对比案例 | ⏭ SKIPPED | 撞前置 guard `C17_机构与门诊命名合规` 骨架 |
| 14 | 门店上架 CGM 传感器 | C1_器械经营资质闸 | ⏭ SKIPPED | C1 自身是 function-backed 骨架 |
| 15 | 分型结论直推患者 | R51_分层结论默认不可披露患者 | ⏭ SKIPPED | 撞前置 guard `C9_AI方案禁止直接推送` 骨架 |

**0 条 FAIL。没有任何一条是因为结构性错误跑不了的**——15 条全部走到了引擎里，要么被规则正确拦住，要么撞上明确标注的 `TODO(FDE)` 骨架。没有出现未注册规则、未注册动作、参数契约不符、能力越界这类真问题。

两条 PASS 的含金量值得说一句：

- **CQ#2（戴 6 天发分层结论被拦）** 一次命中两条规则 `R01` + `R51`，说明 `输出服务分层标签` 这个动作的三重 guard（数据充分性 + 妊娠切换 + 披露授权）是真串起来的。而且它反证了 C-11 落对了：R01 在这里以 guard 身份拦住结论层输出，同时——见下方专项核实 2——它没有出现在任何安全告警动作上。
- **CQ#11（服务包写夜间承诺被拦）** 证明 B-11 这条硬红线在运行时是真拦得住的，不是文档约定。

另外 CQ#15 期望的 `R51` 虽然自身 SKIPPED，但它在 CQ#2 里已经实际触发过一次（`命中=['R01','R51']`），所以 R51 的判定体本身是有效的，只是在 `推送方案至患者` 这条路径上被前面的 `C9` 骨架挡住了。

### D.4 一条给 FDE 的实现建议

13 条 SKIPPED 里有 6 条（#1、#4、#8、#9、#13、#15）的目标规则**本身已经是 declarative、判定体现成可用**，纯粹是被同一个 Action 里排在前面的 function-backed guard 挡住了。也就是说，这几条 CQ 距离绿灯只差那一两条前置 guard 的函数体。

按「解锁 CQ 数量 / 实现成本」排，建议 FDE 优先填这 6 条 function-backed guard：

`R56_告警模板预审冻结`（解锁 CQ#8、#9）、`C9_AI方案禁止直接推送`（解锁 #15）、`R42_急性混杂窗口禁止出结论`（解锁 #1 与 action CQ#1）、`C4_数据用于产品推荐须单独同意`（解锁 #4）、`C17_机构与门诊命名合规`（解锁 #13）、`D11a_签发人资质失效自动冻结`（解锁 action CQ#2、#5）。

这 6 条填完，28 条 CQ 里能跑绿的从 9 条涨到 17 条左右，而工作量只有 62 条函数体里的 6 条。剩下的才需要按业务逐条啃。

---

## 本项目三件专项核实

### 1. ✅ 四条低血糖规则确实物理独立（confirmed-facts C-01 / A3-6 / R-4）

这是被临床评审纠正过的错误，重点查。四项证据全部通过：

**① 四个独立注册名、四个独立函数、四个独立行号**

```
R03a_Level2低血糖_实时告警        → 函数 R03a_Level2低血糖_实时告警        __init__.py:1387
R04a_Level1低血糖_实时告警        → 函数 R04a_Level1低血糖_实时告警        __init__.py:1405
R03b_Level2低血糖_回顾事件统计    → 函数 R03b_Level2低血糖_回顾事件统计    __init__.py:1423
R04b_Level1低血糖_回顾事件统计    → 函数 R04b_Level1低血糖_回顾事件统计    __init__.py:1441
```

四个 `RuleDef.impl` 指向四个不同的函数对象，没有共享实现、没有公共 helper、没有靠传参区分口径的写法。

**② 挂载点也是物理分开的，不只是函数分开**

| 规则 | 挂载动作 |
|---|---|
| R03a / R04a（实时口径） | `触发低血糖处置` |
| R03b / R04b（回顾口径） | `统计低血糖事件`、`生成AGP与指标报告`、`生成结营报告` |

实时口径进告警处置链，回顾口径进统计与报告链，**两条链没有交集**。这一点比函数分开更关键——就算将来有人改错了函数体，两条链的入口也不同，不会一改全错。

**③ 优先级带与生效阶段的差异保留完整**

```
R03a: priority 100, phase P2      ← 实时告警，一期不投递（B-13）
R04a: priority 105, phase P2
R03b: priority 110, phase P1+P2   ← 回顾统计，一期核心安全产出
R04b: priority 115, phase P1+P2
```

a 组标 P2、b 组标 P1+P2，和 B-13「一期不做实时告警、但回顾统计是一期核心产出」严丝合缝。

**④ 每条规则的 docstring 里都写死了硬边界警告**

四条规则的 docstring 各有一段「★ 低血糖双口径硬边界」，点名不得与对应的另一条共用判定函数、不得靠传参区分，并注明「混用等于原样重犯已被临床评审纠正过的 C-01 错误」。TODO 注释里还各写了一句「**禁止复用 ≥15min 口径**，与 R03b 必须是两个独立函数签名」这样的具体禁令。

**结论**：C-01 的纠正在编译产物里落住了，而且不是靠约定，是靠函数、挂载链、优先级、阶段标记四层结构同时锁住。FDE 实现时要触碰这条边界，得同时改四个地方，很难悄悄合并。这一条做得好。

### 2. ✅ R01 只挂结论层，未覆盖实时告警与运动类规则（confirmed-facts C-11）

`R01_数据充分性门槛_仅管结论层` 实际挂载点，全部以 **guard** 身份：

```
生成AGP与指标报告 · 输出服务分层标签 · 判定缓解结果 · 生成结营报告 · 兑现结果承诺
post_rules：无
```

五个全部是结论层输出动作：指标报告、服务分层标签、缓解判定、结营报告、结果承诺兑现。**没有一个是安全通道动作。**

反向核实——安全通道的六个动作 `触发低血糖处置` / `推送告警` / `升级告警` / `响应并回执告警` / `更新低血糖状态机` / `统计低血糖事件` 的 guards 与 post_rules 里，**没有出现 R01**。运动类规则 R23 / R24a / R24b / R25 / R26 / R27 所挂的 `记录餐食与运动事件` 与 `推送告警`，guards 里也**没有 R01**。

IR §4.1 的第二条硬语义（R01 不得作为 B1–B4 的前置门）在编译产物里成立。C-11 说的「原设计会静音佩戴早期的夜间 Level 2」这个坑，插件里没有踩。

### 3. ✅ phase=P2 的规则与 Action 全部已生成（confirmed-facts B-13）

**P2 规则 10 条，全部已注册**：R03a、R04a、R05_即将低血糖预测告警、R06_快速下降箭头提示、R23_运动前低值、R24a_运动前高值查酮体、R24b_运动前极高值一律不宜运动、R25_运动中下降、C20_危急值须系统自动告警并记录响应、R38_告警兜底配置未完成禁止佩戴。`RULE_BANDS` 的 phase 标记与 IR §4.3 逐条一致。

**P2 Object 4 个，全部已声明且已映射**：`GatewayDevice`（postgres/gateway_device）、`AlertEscalation`、`AlertSuppressedLog`、`DutyRoster`——四个都在 `mappings/objects.yaml` 里有物理落点，不是只声明不落地。

**P2 Link 3 条，全部已声明**：`bound_gateway`、`escalates_via`、`suppressed_as`。

**P2 Action 已生成**：`升级告警`（description 明写 phase=P2，guard 挂 R38，hil 值班医师，writes AlertEscalation）、`记录载体覆盖变更并强制告知`（description 明写 phase=P2）。

**结论**：B-13「一期不投递实时告警，但结构照建」执行到位。二期启动时不需要重新建模，把 phase=P2 的规则启用、把对应 Action 接上投递通道即可。R-2「把云侧也建成一条 carrier」也落住了——`CarrierRegistry` 标的是一期即建，取值域 `none|patient_phone`，`gateway_box` 留作二期占位。

---

## 修复清单（按优先级）

| 优先级 | 事项 | 落点 | 谁做 |
|---|---|---|---|
| **P0 BLOCKER** | R57/R58/R59 补挂载点（见 A.2 的五行具体改法），改完重编译 | IR §5 Actions 表 | 建模 |
| **P0** | 「低血糖优先抢占」补挂 `输出服务分层标签`、`生成结营报告` | IR §5 Actions 表 | 建模 |
| P1 | 7 条 `TODO(FDE): 补依据` 规则补权威出处（清单见 B.1） | IR §4.3 source 列 | 临床顾问 + 法务 |
| P1 | `seed_reference_data` 填七类参考数据（优先于 62 条函数体） | `__init__.py` | FDE |
| P1 | 优先实现 6 条 function-backed guard（清单见 D.4），性价比最高 | `__init__.py` | FDE |
| P2 | `撤回同意`、`维护凭证台账` 补 hil；其余三条补不设 hil 的理由说明 | IR §5 hil 列 | 建模 + 合规 |
| P2 | §4.3 `on_actions` 列与 §5 对齐，或明确降级为注释（见 A.4） | IR | 建模 |
| P2 | T-2 遗留清单的数字 6 改 7（漏了 R44） | IR §「遗留 TODO(FDE) 清单」 | 建模 |
| P3 | plugin.yaml 改成引擎 `load_manifest` 认的格式，补槽位 5/6（见 B.5） | plugin.yaml / 编译器 | 平台 |
| P3 | OKF 导出明确以 `source` 为权威字段，或把法条号冗余进 `citations`（见 B.3） | 平台 | 平台 |

---

## 附：本次校验没有做的事

- 没有修改 `plugins/glycowise/` 下任何文件。
- 没有修改 clife-onto-engine 内核或其临时副本里的插件拷贝。
- 没有替 FDE 填任何函数体、handler 或参考数据。
- 没有验证 declarative 规则判定体的**临床正确性**（只验证它能跑、能拦）。阈值本身的临床准确性由 B.1 的 7 条待补依据与 confirmed-facts C-14（r2h 切点）覆盖，不在本次校验范围。
