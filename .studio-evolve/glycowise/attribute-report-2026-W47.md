# 归因报告 — glycowise · 窗口 2026-W47（round 6）

> 状态：**非轨迹节先出**（2026-10-24）。§4 归因留空，等 `feedback.yaml` 变 `status: reviewed`、90 条 label 全非空后补。

输入：`trajectories/2026-W47/audit.jsonl`（90 条：execute 64 = committed 13 / pending_hil 26 / rejected 25；ask 26）+ `routing.log.2026-W47.jsonl`（126 句：轨迹 90、非轨迹 36 = clarify 22 / advise 3 / error 11）+ `feedback.yaml`（**status draft，90 条 label 全空**；机器比对 `suggested` correct 53 / wrong 9 / 无建议 28——不是标签）。口语 126 句由数据准备小组按 `examples/utterances.2026-W47.brief.md` 配额写，13 个配额层全部达标，`source` 带 `brief:{family}#tier{N}[#变体]`。回放 `replay_check.py --mode sequential` 90/90；真 Qwen usage 856,574 token / 126 句。
生产 h_i：`feat/glycowise-fde-fill` 9b1959e（P2–P8 已合入；P9a / P9b / P9c **未合入**）。路由 manual，repeat 3。
录制在第 6 句崩过一次（Qwen 产出带 `Or` 节点的 OQL，网关导出只认 `Cond`），已修并 `--start 6` 续跑，前 5 句原样保留——工具缺陷，不是数据缺陷。

## 1. 非轨迹 36 句

| 类 | 句数 | trace | 去向 | 归属 |
|---|---|---|---|---|
| 遥测误绑 | 8 | 0012 / 0013 / 0030 / 0063 / 0065 / 0090 / 0103 / 0109 | error（`无遥测绑定: CgmSummary`）：CV / 夜间最低值 / 夜间有效覆盖率 / 波动类全部中招 | 路由层（平台 backlog）。W44 0126、W45 0227 之后**第三次复现**，这次整类口语都没落轨迹：高血糖与波动 t1 只剩 TAR / 最高值 / 均值几句成 ask；低血糖安全 t1 的夜间最低值 / 覆盖率 3 句同样被吃 |
| IMPL_MISSING | 3 | 0021 / 0075 / 0121 | error（`NotImplementedError`）：`确认缓解时钟Day0`、`撤销更正已发出告警`、`C5_厂商云对接协议与PIPIA` | 本体实现层。三个动作 / 规则只有桩，第一次被真实口语路由到。前两条起 IMPL_MISSING 提案（§3，P12 / P13）；C5 涉及境外云协议，**只登记**，不起提案 |
| LLM 抢闸 | 12 | 出口签发闸 t4 **8**：0049 / 0050 / 0052 / 0053 / 0086 / 0087 / 0100 / 0107；结论层与分层 t4 **4**：0055 / 0083 / 0108（分层标签直发患者 / 家属）、0112（一天数据定分层） | clarify：草稿直发 / 换人签发 / 内部结论直发被大模型在路由层反问或拒掉，引擎 C9 / D11a / R01 没被评到 | 路由层。**第四次复现**。这两层的 tier4 口语写得再多也落不成轨迹，补录要换写法（见 §2） |
| 反问而非拒 | 8 | 数据与同意合规 t4 **6**：0060 / 0099 / 0118 / 0119 / 0120 / 0122；因果链溯源 t4 0098（删处置记录）；产品与机构合规 t4 0126（对比图发公众号） | clarify：无同意摄入、境外通道、他人授权导入、免仲裁入库被反问「请确认同意记录 / 批次」而不是进引擎被 C3 / C5 / R48 拒 | 路由层。数据与同意合规 t4 只剩 3 句进轨迹 |
| 判缓解被抢先 | 2 | 0094 / 0113 | clarify：判定缓解结果 / 记录缓解评估被大模型要求先给化验值 | 路由层 |
| advise | 3 | 0019 / 0020（缓解路径 t3「请医师来答复」）；0067（参考与配置 t1，磺脲人群告警线按哪个人群） | 「转医师答复」被路由成建议文本而不是 `转介医师` 动作；0067 是查询被当成咨询直接作答 | 路由层：P7 补了 handler，路由却没把这类口语送到动作上 |

路由层累计五窗口 49 + 25 = 74 句不归本体。写论文方法节时，遥测误绑与 LLM 抢闸两类是「路由层不稳定」证据链的第 3 / 第 4 次复现，要进 §6 威胁 (a)。

## 2. 分层预估（不等标注）

用 `utterances.2026-W47.yaml` 的 `source` 对 90 条轨迹算 family×tier，**上界**假设 90 条标注后全部落案例（partial 不落会再少），叠到现有 203 条上，按 v3 并层口径（family×tier，<8 的层并入同 family 其余 tier）：

W47 轨迹 family×tier：产品与机构合规 t4 9 · 低血糖安全 t1 3 · 出口签发闸 t3 10 / t4 2 · 参考与配置 t1 2 · 因果链溯源 t3 13 / t4 9 · 数据与同意合规 t4 3 · 结论层与分层 t3 8 / t4 5 · 缓解路径 t1 11 / t3 5 · 高血糖与波动 t1 10。

分层口径本身这一轮修了（§2.1），所以预估给两张表：**现行键**（make_real_cases 按规则 / 动作 / 查询起点推断，现有 203 条就是这么归的）和 **source 键**（口语集自带 family；W43 的 42 条 `golden#NN` 无 family，保留推断）。

| family | 现行键 203 | 现行键 +W47 上界 | source 键 203 | source 键 +W47 上界 |
|---|---|---|---|---|
| 产品与机构合规 | t3 21 / t4 4 ✗ | t3 21 / t4 13 ✓ | t3 9 / t4 4 ✗ | t3 9 / t4 13 ✓ |
| 低血糖安全 | t1 5 / t3 14 / t4 9 ✗ | t1 8 / t3 14 / t4 9 ✓ | t3 29 / t4 11 ✓ | **t1 3** / t3 29 / t4 11 ✗ |
| 出口签发闸 | t1 8 / t3 2 / t4 1 ✗ | t1 8 / t3 12 / **t4 3** ✗ | t1 1 / t3 17 / t4 1 ✗ | **t1 1 / t4 3** / t3 27 ✗ |
| 参考与配置 | t1 7 / t3 13 ✗ | t1 9 / t3 13 ✓ | t1 17 / t3 3 ✗ | t1 19 / **t3 3** ✗ |
| 因果链溯源 | t1 7 ✗ | **t1 7** / t3 13 / t4 9 ✗ | t1 35 ✓ | t1 35 / t3 13 / t4 9 ✓ |
| 指标口径 | t1 49 / t3 23 / t4 7 ✗ | t1 49 / t3 23 / **t4 7** ✗ | t1 22 / t3 1 ✗ | t1 22 / **t3 1** ✗ |
| 数据与同意合规 | t3 10 ✓ | t3 10 / **t4 3** ✗ | t3 19 ✓ | t3 19 / **t4 3** ✗ |
| 结论层与分层 | t3 4 / t4 5 ✓（并层 9） | t3 12 / t4 10 ✓ | t1 1 / t3 9 / t4 10 ✗ | **t1 1** / t3 17 / t4 15 ✗ |
| 缓解路径 | t4 2 ✗ | t1 11 / **t3 5 / t4 2** ✗（并层 7） | t4 5 ✗ | t1 11 / t3 5 / t4 5 ✓（并层 10） |
| 高血糖与波动 | t3 8 / t4 4 ✗ | t1 10 / t3 8 / **t4 4** ✗ | t3 8 / t4 1 ✗ | t1 10 / t3 8 / **t4 1** ✗ |

✓/✗ 是并层后该 family 的 rest 层是否 ≥ 8（rest 为空也算 ✓）。粗体是 W47 标注后仍薄的层。

**结论**：W47 把 round 5 收尾时的 8 个薄层补上了 4 个（现行键下产品与机构合规 / 低血糖安全 / 参考与配置 / 结论层与分层），但两张表都还有 6–7 个 family 不达并层口径，**holdout-6 还开不了**。两张表薄的层不一样，补录前先定键（§2.1 决定 ②）。补录建议（按 source 键）：
- 出口签发闸 t4：8 句被 LLM 抢闸，要补的不是句数是**写法**——不写「直接推」「不签发就发」这类让大模型自己拒的措辞，写成看起来合规的操作（「把 c-reco-P0012-01 推给患者」，草稿状态由引擎查），让 C9 / D11a 真被评到；≥ 6 句。
- 数据与同意合规 t4：被反问 6 句，同样换写法（不在句里提「没同意」「境外」，只给动作与通道名）；≥ 5 句。
- 低血糖安全 t1：夜间最低值 / 覆盖率全被遥测误绑吃掉，补录没用，等平台修 CgmSummary 绑定；或改问 Level 2 事件日期 / 次数类（不走 CgmSummary）≥ 5 句。
- 结论层与分层 t4：4 句被抢闸，现行键下不薄、source 键下 t4 15 够；但「分层标签直发」这类口语从没进过引擎，R01 / 披露规则在真实窗口上零覆盖，补录同样要换写法。
- 高血糖与波动 t4：≥ 7 句（现行键）；source 键下 t4 只有 1 条，brief 没要这层，需补 ≥ 7。
- 参考与配置 t3、指标口径 t3、结论层与分层 t1：source 键下各差 5 / 7 / 7，brief 都没要；现行键下不薄。是否补取决于 §2.1 的键决定。

### 2.1 分层键的修正与 W43–W46 复核

`make_real_cases.py` 的 `family_of` 原来只按反馈项 family → 规则名 → 动作名 → OQL 起点对象推断（去重类因此全归「指标口径」）。本轮改成：反馈项显式 family > **口语集 `source` 自带 family**（`brief:{family}#tier…` / `sim:{family}-NN…`）> 推断回退；落下的案例多带一个 `source` 字段。W47 起 `source` 是唯一分层键。

用新键复核现有 203 条（不改 W43–W46 任何文件，只比对）：182 条 source 可推 family（W44 61 / W45 75 / W46 46），其中 **106 条与现行 family 不一致**；21 条 `golden#NN` 无法推。差异集中在：

| 现行 family → source family | 条数 | 机制 |
|---|---|---|
| 指标口径 → 因果链溯源 | 17 | 因果链溯源的 t1 查询（告警 / 阈值 / 变更溯源）起点对象是指标类，推断全落「指标口径」 |
| 指标口径 → 参考与配置 | 15 | 同上，阈值 / 目标区间 / 设备参数查询 |
| 产品与机构合规 → 出口签发闸 | 11 | 出口审核 / 推荐话术动作命中 C 系列合规规则，按规则名归了产品合规 |
| 参考与配置 → 低血糖安全 | 9 | 低血糖安全的查询读阈值配置 |
| 指标口径 → 数据与同意合规 / 结论层与分层 / 低血糖安全 / 出口签发闸 | 9 / 8 / 8 / 4 | 查询类一律被起点对象吃进指标口径 |
| 出口签发闸 → 因果链溯源 · 低血糖安全 → 因果链溯源 / 缓解路径 / 指标口径 · 高血糖与波动 → 低血糖安全 · 其它 | 7 · 4 / 3 / 1 · 3 · 7 | 规则名归属与口语意图不一致 |

两个键回答的是不同问题：现行键是「引擎在这条案例上**评到了哪个 family 的规则 / 动作**」，source 键是「这句口语**想做哪个 family 的事**」。分层的目的是让留出集按场景覆盖，应当用 source 键；但 holdout-4 / holdout-5 是按现行键抽的，round 1–5 的层 T_k 读数也按现行键。因此：
- W47 起新落的案例按 source 键归 family（已改代码）；
- **W43–W46 的 203 条不重写**（约束）；是否在抽 holdout-6 前用 source 键整体重归（`holdout_sample` 读一张 override 表），是 §5 决定 ②′——**已定**（§2.2）：按 source 键整体重归，holdout-6 用 override 表。

### 2.2 决定 ②′（2026-10-24，用户裁定）：按 source 键整体重归，holdout-6 用 override 表

W43–W46 的 203 条案例**文件不改**，改走覆盖表：`sets/family-override.yaml`（`families: {case_id: family}`，182 条，其中 106 条与文件里的现行 family 不同；21 条 W43 `golden#NN` 口语无 family 列在 `not_covered`，保留现行）。`holdout_sample.py` 新增 `--family-override FILE`，分层前覆盖 family，留出集文件记 `family_override` / `family_overridden`。抽 holdout-6 的命令固定为：

```
holdout_sample.py --cases-dir cases --round 6 --holdout-size 40 --stratify family,tier --merge-min 8 \
    --family-override sets/family-override.yaml --exclude-file <Dᵢ> --ledger growth-ledger.md
```

`--check-pool` 现状（203 条，W47 未落）：并层后 18 层，**7 个 rest 层不足 8**——产品与机构合规 4 / 出口签发闸 2 / 参考与配置 3 / 指标口径 1 / 结论层与分层 1 / 缓解路径 5 / 高血糖与波动 1；不用覆盖表是 8 个。叠 W47 上界后仍薄 7 个（§2 表最右列）。

**补录清单**已写成 `examples/utterances.2026-W48.brief.md`（约 70 句，8 个配额层），配额按「source 键 + W47 上界」的缺口乘以 W47 实测落轨迹率放大：tier1 / tier3 层 ≈ 1.6 倍，tier4 层 ≈ 2.5 倍，并要求 tier4 换写法、低血糖安全 t1 避开 CgmSummary 统计值。若 W47 标注后 partial 较多，缺口会再大，补录前以标注后的 `--check-pool` 为准。

遗留口径差：`growth_metrics` 的 W_family 与层 T_k 读的是结果行里的 family（runner 从案例文件带出），仍是现行键；round 1–5 的读数不重算。要让读数与留出集同键，runner / growth_metrics 也得读 override 表——登记为 amend 候选，不在本轮改。

## 3. IMPL_MISSING 提案 P12 / P13（不等标注；不合入生产）

编号：verdict / 台账里 proposal 9 / 10 / 11 已被 P9a / P9b / P9c 占用，所以这两条从 **P12** 起编（交接文件写的 P10 / P11 对应这里的 P12 / P13）。`growth-ledger.md` 拒绝签名表为空，无命中。

| | P12 `确认缓解时钟Day0` | P13 `撤销更正已发出告警` |
|---|---|---|
| 来源 | 0021（缓解路径 t1 正路动作） | 0075（原句「复测 4.1 了把 A-P0045-02 关掉」更像**回执闭环**，路由到撤销更正是路由层候选；Dᵢ 按动作的 IR §5 语义重写） |
| Dᵢ | 缓解路径-05 / 06 / 07（`sets/P12-Di.yaml`；含 gated_by_meds 分支 P0012 → status reset） | 因果链溯源-11 / 12（`sets/P13-Di.yaml`；实时告警 + 回填告警） |
| expect_state | RemissionClock{day0, status} 真值只从 IR §2 gated_by_meds + seed meds 推 | AlertEvent.status = retracted（IR §1 lifecycle） |
| 修法 | `_fde.py` 追加 handler + `__init__.py` 桩转发（`P12.patch` 40 行） | 同（`P13.patch` 50 行）；触及告警之后签发的 PlanSigned 标 evidence_stale |
| Dᵢ h_i → h' | A 0 → 1.0；T_3 0 → 1.0；W_family 0 → 1.0；C 2.0 不变（都是 1 步到 HIL） | 同 |
| B（临时用 holdout-5，B_6 未抽） | A .750 / T (.571,—,.750,1) / S 1 / W_family .9 / C 2.9，**与 h_i 逐格相同** | 同 |
| real-all 203 / sim 98 | .773 / .990，与 h_i 相同 | 同 |
| 八臂 | 3d / noT / noS / noW / 1d / 1d-strict / none **ACCEPT**，random REVISE（p=0.6 seed 0 的抽签） | **八臂同判 ACCEPT** |

两条都是 round 4 P7 / P8 同型：Dᵢ 从 IMPL_MISSING 变 pending_hil，全集不动。**不合入生产**——等标注回来按 round 6 正式流程（B_6 抽出后重判外关卡）由用户确认。生产 `__init__.py` 现有 65 处 NotImplementedError，这两条合入后 63。W_evid 两侧均不可得（glycowise IR 无 §8，`W_EVID_UNAVAILABLE`），判定只看 W_family。

## 4. 归因（round 6，四窗口合并：W47 / W48 / W49 / W49b；2026-10-24 标注回传 9b63c5e）

标注：162 条 reviewed（reviewer Ameng2001 / 本体负责人，标签由数据组按 IR 规则意图、实现、seed 真值与 sequential 回放逐条判后授权采纳），`check_feedback.py` 四窗口 ✓；correct 107 / partial 17 / wrong 38（router 28 / rule 5 / seed 5）。明细与归并见 `handoff-round6c.labels.md`。

### 4.1 反馈 → 案例

`make_real_cases.py --window …` 四窗口：W47 84（partial 6 不落）、W48 57（partial 11）、W49 1、W49b 3 → **cases/real 203 → 348**。`sets/real-all.yaml`（348）、`real-W47`（84）、`real-W48`（57）、`real-W49`（4，含 W49b）重建。family 自 W47 起按口语集 `source` 归；W43–W46 走 `sets/family-override.yaml`。

**tier 口径的发现**：案例 tier 由引擎实际裁决的类别定（查到→1、执行→3、被拒→4），不是 brief 的层。145 条新案例里 64 条 brief 层与案例 tier 不同——产品与机构合规 / 数据与同意合规 / 高血糖与波动的 brief t4 句被引擎放行、落成 t3（正是 wrong 候选）；出口签发闸 / 因果链溯源 / 结论层与分层的 brief t3 句被规则拦下、落成 t4。因此 §2 用 brief 层算的上界（10 族全 ✓）高估了：`--check-pool --family-override --merge-min 8` 实测 **348 条、25 层、5 个 rest 层仍不足 8**（产品与机构合规 4 / 出口签发闸 5 / 参考与配置 3 / 因果链溯源 7 / 高血糖与波动 1），正式 run 前置 (1) 仍 ✗（池 ≥ 80 ✓）。tier 口径本身不改（「实际裁决的类别」是读数 T_k 的分母定义），登记：下次 brief 的配额要按「引擎会怎么裁」而不是「口语想做什么」反推。

### 4.2 留出集 B_6 与 h_i 基线

`holdout_sample.py --round 6 --holdout-size 40 --stratify family,tier --merge-min 8 --family-override … --exclude-file sets/P9-Di.yaml --exclude <5 条 rule 层 wrong 案例>`：**40 / 25 层，池 338，排除 10**（P9-Di 5 条 real；rule 层 wrong 5 条作为本轮规则层提案的 Dᵢ 预先排除）。W48 的 11 条 dup 案例（指标口径-r80–r90）按比例进了 2 条（r87 / r88）。台账「留出集记录」已加 round 6 行；`sets/holdout-6.yaml` 记 `family_override` / `family_overridden: 106`。

h_i（post-P14 生产）：B_6 **A .825**、T=(.857, —, .706, 1.0)、S 1.0、W_family 1.0、C 3.0（`readings/r6-hi-B6.json`）；real-all 348 A .756、T=(.641, —, .761, 1.0)；IMPL_MISSING 21 行全是因果链溯源-r21 / r22 / r23 路由到 `升级告警` 桩（r21 是 rule 层 R38 误挂，r22 / r23 是路由选错动作，真值是 P13 的 撤销更正已发出告警——P13 未合入，合入也救不了路由选错）。

### 4.3 D⁻ 分层

| layer | 条 | 归因 | 处置 |
|---|---|---|---|
| **rule** | 5（全 W47） | 0026 / 0027 D9 功效声称没拦（实现只查「产品与分层同句」）；0069 R44 否定句「先不闭环」被子串匹配当成闭环 → 假阳性；0079 R38（入组规则）误挂在 升级告警 上对任何参数 fail，该拦的理由是 R53；0115 R51 的 TIER_RE 不认「分层是一级」 | **4 个规则层提案候选 P16–P19**（P15 已被「描述去品牌」占），Dᵢ = 对应 real 案例（已从 B_6 排除）；按配对设计各出根因修 + 朴素修。D9 ×2 与 R44 都只有单窗口样本——round 2–4 的 P5 / P6 / P7 也是单窗口来源，不等复现 |
| router | 28 | 去重仲裁无 dedup_key → R48 硬拒 11（W48，见 4.4）；'now-14d' 字面量 5（第四窗口复现）；多挂一跳 / seed 无边 3；枚举字面量 3（level「中级」第四次）；字段选错 2；选错动作 / 臆造对象 4（含 0251 境外云同步被套成 摄入读数 空批次 committed、0280 波动结论套成已签发方案推送）；丢参数 1 | 不归本体，平台 backlog；累计 **路由层 wrong 49 + 28 = 77 条**、非轨迹 100 句 |
| seed | 5（全 W48） | DeliveryReceipt / based_on_summary 无边、分层确认人无记录、P0066 有 tier_label 无读数 | 演示租户问题，留出集里两臂同败 |

partial 17 条只计成本；其中「推送已签发方案给家属」5 条同型——没有任何规则看接收人身份或患者授权，是**规则缺口**（IR 修订候选，不是实现缺失）。

### 4.4 P9 三份修法在 B_6 上（attempt 4，report-only，不进台账）

| | Dᵢ（P9-Di 5 条 real，15 句） | B_6 A | ΔA | regress_any | 修对 | 3d | 1d |
|---|---|---|---|---|---|---|---|
| h_i | 0/15 | .825 | | | | | |
| P9a 根因修 | **12/15** | .900 | +.075 | 0 | r72 / r87 / r88 | **ACCEPT** | ACCEPT |
| P9b 朴素修（放宽） | 0/15（STATE_MISMATCH 33） | .900 | +.075 | 0 | 同 | **REJECT** | ACCEPT |
| P9c 机械修（删分支） | 0/15（STATE_MISMATCH 39） | .900 | +.075 | 0 | 同 | **REJECT** | ACCEPT |

分歧集仍 {P9b, P9c}，判定与 round 5 第 3 / 4 次相同：3d 靠内关卡 Dᵢ 的落库断言拒，外关卡 B_6 三份修法逐格相同。**B_6 仍然看不见它们的差别，原因换了**：W48 的 11 条 dup 案例是**批次级**请求（参数是 batch_ids / batches / sources + sensor_serial，键名由 LLM 临场发明，批次对象 seed 里不存在），而 IR §4 的 去重与通道仲裁 是**单条读数**动作（reading_candidate.reading_id）。三份修法的 handler 拿到没有 reading_id / 值 / 时间的候选，都走到 verdict=new，暂存一条 `cand-{now}`、value_mmol 为空的幻影读数并 commit——commit 判据下 11 条全「修对」。这和 W46 数据与同意合规-r02 的「空写入被判正确」同型，是第五类盲区的又一实例；更深一层是 **IR 没有声明批次级仲裁动作**，口语想做的事在本体里没有对应物，所以也写不出诚实的 expect_state（没有 IR 声明的 writes 可推）。登记为 IR 修订候选（批次级去重仲裁动作或把 batch 形态并入 reading_candidate 规范），这 11 条案例在 IR 修订前对 P9 分歧集**不构成证据**。

P9a 的两次 3d 裁决（B_5、B_6）都 ACCEPT、两次 regress 0、Dᵢ 12/15——合入与否仍是用户决定（§5 ④）。verdicts：`6-9-4-{3d,1d}`、`6-10-4-*`、`6-11-4-*`。

### 4.5 本轮方法问题（续 W46 报告 §4）

7. **brief 层 ≠ 案例 tier**（4.1）：补薄层的配额按口语意图写，落案例按引擎裁决分层，t4 配额里被放行的那部分恰是 wrong 候选、落成 t3。分层预估要按「预计裁决」算。
8. **批次级请求落到单条动作上**（4.4）：路由把 IR 没有的操作套进最近的动作，handler 不校验参数形态就写幻影对象并 commit。两处可修：IR 补动作声明；handler 对缺 reading_id 的候选 fail（这会让 11 条在三份修法下都变 rejected，B_6 仍不分，但至少不再空写）。后者是实现层提案候选，Dᵢ 可用这 11 条。

### 4.6 规则层提案 P16–P19（配对：根因修 + 朴素修，八臂；2026-10-24）

P9a 先合入生产（§5 ④），h_i 重算：B_6 A .900、real-all .816、sim .990。四条规则层 D⁻ 各出一对（`proposals/P16.md`–`P19.md`；台账 proposal 16–23）：

| 提案 | 修法 | Dᵢ | B_6 | real-all 348 | sim 98 | 3d | 1d | none | random |
|---|---|---|---|---|---|---|---|---|---|
| P16a D9 功效声称 根因 | EFFICACY_RE | 0→6/6 | .900 = | .822（+r26 r27） | .990 | ACCEPT | ACCEPT | ACCEPT | REVISE |
| P16b 朴素 | 两条字面量 | 0→6/6 | = | 同 | 同 | ACCEPT | ACCEPT | ACCEPT | REVISE |
| P17a R44 否定句 根因 | 去否定片段再判 | 0→3/3（state 过） | = | .819（+r15） | .990 | ACCEPT | ACCEPT | ACCEPT | REVISE |
| P17b 朴素 | 删「闭环」关键词 | 0→3/3 | = | 同 | **.980（golden-23 回退）** | ACCEPT | ACCEPT | ACCEPT | REVISE |
| P18a 升级告警 根因 | guard R38→R53 + handler + level 映射 | 0→3/3 | = | .819（+r21） | .990 | ACCEPT | ACCEPT | ACCEPT | REVISE |
| P18b 朴素 | R38 删分支 | **0→0**（仍 IMPL_MISSING） | = | .816 | .990 | **REVISE** | REVISE | ACCEPT | ACCEPT |
| P19a R51 正则 根因 | 分层口语分支 | 0→3/3 | = | .819（+r21） | .990 | ACCEPT | ACCEPT | ACCEPT | ACCEPT |
| P19b 朴素 | 字面量 | 0→3/3 | = | 同 | 同 | ACCEPT | ACCEPT | ACCEPT | ACCEPT |

三个消融臂与 1d-strict 都与 3d 同判。`arms/r1-6/`（`arm_compare` 24 条 × 8 臂）：accept_rate 3d .792 / 1d .958 / none .875 / random .417；regress_rate（净）全臂 0；regress_any 1d .087、none .048、3d 0；分歧集仍只有 round 5 的 {P9b, P9c}。

**这一轮朴素修复臂说明了什么**：
1. 四对里三对（P16 / P17 / P19）根因修与朴素修在 Dᵢ、B_6、real-all 上**逐格相同**，八臂全部同判。朴素修的代价（只认字面量、删关键词）在这三个集合上没有一条案例能暴露——B_6 和 real 池里没有「换一种功效说法」「真正的闭环请求」「分层为二级」这类案例。
2. 唯一暴露的 trade-off 在 **sim**：P17b 让 golden-23（高危用药者要求闭环，应拒 R44）放行。协议规定 sim 禁入留出集（§2 第 1 条），所以外关卡结构上看不见它。这不是判据盲（commit / state 都能判），是**留出集覆盖盲**：real 池来自真实口语，没人真的提过闭环请求。
3. P18b 被带闸门的六臂拒，但原因是它没让 Dᵢ 通过（删了 R38，handler 仍是桩）——none / random 照收，说明无闸门臂会合入什么都没修好的补丁；这是 none 臂的作用，不是三维的。
4. 规则层 D⁻ 单窗口样本的局限：四条候选各 1–2 条案例，Dᵢ 太小，内关卡 ΔT 非 0 即 1，没有梯度。

处置：**根因修 P16a / P17a / P18a / P19a 已于 2026-10-24 由用户确认合入生产**（post-P1x h_i：Dᵢ 全过，B_6 .900 逐案例不变，real-all .816 → .830 只多过四条提案的 5 条 Dᵢ、无回退，sim .990 逐案例不变）；朴素修一律不合入。留出集覆盖盲登记为协议问题：formal 前要么允许标注过的「对抗 sim」进 B 的一个受控子集并单列，要么在 brief 里定向补「trade-off 口语」（真闭环请求、换说法的功效声称）。


## 5. round 5 遗留的四项决定

| # | 事项 | 本轮处置 |
|---|---|---|
| ① | criteria amend v3（strict 只认 T / S / W，ΔC 只做约束）待导师签字 | 论文侧 `criteria.yaml` 已按 v3 冻结并用于 round 5 第 3 / 4 次裁决和本轮 P12 / P13；交接文件仍写「待签字」。**需要用户确认**：v3 是否已签字；若未签，本轮所有 3d 判定都标 exploratory（已标） |
| ② | `regress_any` 单条口径要不要进 criteria | **延后，不进 v3**。继续与净口径并排输出（T1 / T2 / metrics），作为 §6 威胁 (d) 的证据；是否进 v4 等 formal 前的 amend 一次性定。另加本轮决定 ②′：**分层键**——用户裁定按 source 键整体重归 W43–W46（override 表，不改文件），见 §2.2 |
| ③ | W_evid 未实现 | **已实现**（astra d07589d：结构分母 §1 Object + §6 Mapping + §4 function Rule，分子 §8 verified 去重），但 glycowise IR 无 §8（ground 未跑，pg-ro / ch-ro 不可达）→ 读数 null，gate_decide 记 `W_EVID_UNAVAILABLE` 只看 W_family。要让 W_evid 非空，得先跑 ground 填 §8——与数据组无关，是引擎侧的事 |
| ④ | P9a 未合入；分歧集 {P9b, P9c} 未合入 | B_6 已抽，三份修法在 B_6 上重判（§4.4）：P9a 3d 两次 ACCEPT、regress 0；P9b / P9c 3d 仍 REJECT、1d 仍 ACCEPT。**P9a 合入与否等用户决定**；合入则 `git apply P9a.patch` 后重算 h_i，B_6 不必重抽（P9a 的 Dᵢ 已排除） |
