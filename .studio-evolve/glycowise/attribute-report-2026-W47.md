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

## 4. 归因（待标注）

留空。标注回来后：`feedback.yaml` → reviewed → `make_real_cases.py --window 2026-W47`（partial 不落；family 按 source）→ `sets/holdout-6.yaml`（先过并层口径）→ 对 B_6 判 P9a 回退（**前提 P9a 已合入生产，目前未合入**）→ 归因 → 规则层提案 P14 起编。

机器比对标 wrong 的 9 条，标注前只当候选：ask 查 0 行 6 条（0006 C 肽、0010 GMI、0029 TAR 分级、0033 人群目标区间、0089 / 0102 TAR，多半 seed 缺派生字段或边）；0041 推送中级告警被 R56 冻结；0069 回执不闭环仍被 R44 拒（R44 按 IR 只该管闭环）；0110 6 天数据出内部分层被 R01 拒（R01 门槛按 IR 是对的，更像 `cq_expect` 写错）。以标注为准。

## 5. round 5 遗留的四项决定

| # | 事项 | 本轮处置 |
|---|---|---|
| ① | criteria amend v3（strict 只认 T / S / W，ΔC 只做约束）待导师签字 | 论文侧 `criteria.yaml` 已按 v3 冻结并用于 round 5 第 3 / 4 次裁决和本轮 P12 / P13；交接文件仍写「待签字」。**需要用户确认**：v3 是否已签字；若未签，本轮所有 3d 判定都标 exploratory（已标） |
| ② | `regress_any` 单条口径要不要进 criteria | **延后，不进 v3**。继续与净口径并排输出（T1 / T2 / metrics），作为 §6 威胁 (d) 的证据；是否进 v4 等 formal 前的 amend 一次性定。另加本轮决定 ②′：**分层键**——用户裁定按 source 键整体重归 W43–W46（override 表，不改文件），见 §2.2 |
| ③ | W_evid 未实现 | **已实现**（astra d07589d：结构分母 §1 Object + §6 Mapping + §4 function Rule，分子 §8 verified 去重），但 glycowise IR 无 §8（ground 未跑，pg-ro / ch-ro 不可达）→ 读数 null，gate_decide 记 `W_EVID_UNAVAILABLE` 只看 W_family。要让 W_evid 非空，得先跑 ground 填 §8——与数据组无关，是引擎侧的事 |
| ④ | P9a 未合入；分歧集 {P9b, P9c} 未合入 | **保持未合入**。B_6 对 P9a 的回退判定按协议要在它合入生产之后；合入与否是用户决定，本轮不动生产。若决定合入，走 `git apply studio/changes/glycowise/proposals/P9a.patch` 后重算 h_i 基线再抽 B_6 |
