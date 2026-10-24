# 归因报告 — glycowise · 窗口 2026-W48（round 6 补录窗口）

> 状态：**非轨迹节先出**（2026-10-24）。§4 归因留空，等 `feedback.yaml` reviewed。本窗口与 W47 同属 round 6：holdout-6 在两窗口标注都落案例后一次抽。

输入：`trajectories/2026-W48/audit.jsonl`（68 条：execute 38 = committed 15 / pending_hil 4 / rejected 19；ask 30）+ `routing.log.2026-W48.jsonl`（88 句：轨迹 68、非轨迹 20 = clarify 11 / error 9）+ `feedback.yaml`（draft，68 条 label 全空；机器比对 correct 28 / wrong 24 / 无建议 16——不是标签）。口语按 `utterances.2026-W48.brief.md` 的 8 个薄层配额写，`source` 带 `brief:{family}#tier{N}[#变体]`。回放 sequential 68/68；真 Qwen 601,518 token。生产 h_i 同 W47（9b1959e 的 plugins/glycowise；P9a/b/c、P12/P13 未合入）。

## 1. 非轨迹 20 句

| 类 | 句数 | trace | 去向 | 归属 |
|---|---|---|---|---|
| IMPL_MISSING · C7 | 3 | 0236 / 0272 / 0285（数据与同意合规 t4，「读数导到在线表格」） | error：动作 `写入外部协作工具` 的 guard `C7_患者数据禁止存放非平台工具` 是桩（handler 也是桩） | 本体实现层。**起提案 P14**（§3） |
| IMPL_MISSING · C5 | 3 | 0220 / 0237 / 0283（同层，「接到厂商 ch-cloud-sg-01 通道」） | error：`C5_厂商云对接协议与PIPIA` 桩 | 本体实现层。涉及境外云协议，**只登记**（round 6 交接约束）。注：交接汇报写 C5 4 句，routing.log 里是 3 句 |
| 引擎错 · 平台 | 3 | 0222（夜里几次低血糖事件）/ 0234（出评估结论发本人）/ 0240（睡前低值预警几次） | error：TypeError ×2（Qwen 把数值条件写成字符串；handler 对空字段直接比大小）、不支持的 like 算子 ×1 | 平台 backlog，不归本体、不归路由 |
| LLM 抢闸 · 高血糖与波动 t4 | 4 | 0248 / 0263 / 0269 / 0286（出结论推给本人；0234 同意图但落成引擎 TypeError，计在平台错） | clarify：大模型要求先给数据 / 反问 | 路由层。该层 W47 未要求，12 句进 7 句 |
| LLM 抢闸 · 出口签发闸 t4 | 3 | 0216（d-P0012-01 推到手机）/ 0264（方案发到女儿微信）/ 0288（把别人的方案发给新客） | clarify | 路由层。**换写法有效**：9 句进 6 句，W47 同层 2/10（交接汇报写的「一句没进」与 routing.log 不符，以 log 为准） |
| 反问 · 数据与同意合规 t4 | 3 | 0219（导出到在线表格——大模型说能力清单里没有这个动作）/ 0252 / 0284（按家属授权导入） | clarify | 路由层。0219 与 0236 同意图，一个被反问一个进了桩——路由不稳定 |
| 反问 · 参考与配置 t3 | 1 | 0244（night_low 提到 4.4，在用格列美脲） | clarify | 路由层 |

路由层累计六窗口 74 + 12 = 86 句不归本体。**换写法的证据**（按 `source` 对 routing.log 算）：出口签发闸 t4 从 W47 2/10 到 W48 6/9；数据与同意合规 t4 W47 3/10 → W48 3/12 **没有改善**——不是写法问题，是 C5 / C7 桩吃掉 6 句 + 家属授权类被反问 3 句；tier4 合计 W47 28/50、W48 16/33。写进论文 §6 (a) 时三组数并给：换写法只对「大模型自己拒」那一类有效，对实现缺失无效。

## 2. 分层预估（W47 + W48 上界，source 键 + override 表）

W48 轨迹 family×tier：低血糖安全 t1 10 · 出口签发闸 t1 7 / t4 6 · 参考与配置 t3 11 · 指标口径 t3 11 · 数据与同意合规 t4 3 · 结论层与分层 t1 13 · 高血糖与波动 t4 7。

叠到 203（override 键）+ W47 上界 90 + W48 上界 68 = 361，并层口径（<8 并入同 family rest）：**10 个 family 里 9 个 ✓**，只剩 **数据与同意合规 rest(t4) = 6 ✗**（差 2）。上界假设两窗口 158 条标注后全部落案例（partial 不落会再少；W47 机器比对 wrong 9、W48 wrong 24 都仍落案例，只有 partial 不落）。

| family | 203（override） | +W47 | +W47+W48 |
|---|---|---|---|
| 产品与机构合规 | t3 9 / t4 4 ✗ | t3 9 / t4 13 ✓ | 同 ✓ |
| 低血糖安全 | t3 29 / t4 11 ✓ | t1 3 ✗ | t1 13 ✓ |
| 出口签发闸 | t1 1 / t3 17 / t4 1 ✗ | t1 1 / t4 3 ✗ | t1 8 / t3 27 / t4 9 ✓ |
| 参考与配置 | t1 17 / t3 3 ✗ | t3 3 ✗ | t1 19 / t3 14 ✓ |
| 因果链溯源 | t1 35 ✓ | +t3 13 / t4 9 ✓ | 同 ✓ |
| 指标口径 | t1 22 / t3 1 ✗ | t3 1 ✗ | t1 22 / t3 12 ✓ |
| 数据与同意合规 | t3 19 ✓ | t4 3 ✗ | **t3 19 / t4 6 ✗** |
| 结论层与分层 | t1 1 / t3 9 / t4 10 ✗ | t1 1 ✗ | t1 14 / t3 17 / t4 15 ✓ |
| 缓解路径 | t4 5 ✗ | t1 11 / t3 5 / t4 5 ✓（并层 10） | 同 ✓ |
| 高血糖与波动 | t3 8 / t4 1 ✗ | t4 1 ✗ | t1 10 / t3 8 / t4 8 ✓ |

数据与同意合规 t4 的缺口就是 C5 / C7 的 6 句桩：已录的 error 不会变成轨迹，**P14 已合入（见 §3），W49 brief 补录 C7 类口语 10 句、目标 ≥ 4 句进引擎**即可过 8；C5 类口语在 C5 实现前写了也白写。若标注后 partial 把别的层拉回 8 以下，以标注后 `holdout_sample --check-pool --family-override` 为准。

## 3. IMPL_MISSING 提案 P14（不等标注；不合入生产）

见 `studio/changes/glycowise/proposals/P14.md`。C7 guard + 写入外部协作工具 handler 两处桩一起补（引擎先跑 handler 再评 guard，只补 guard 评不到）。Dᵢ 3 条 tier4 CQ：h_i IMPL_MISSING 0/9，h' rejected(C7) 9/9；B（临时 holdout-5）/ real-all / sim 两臂逐行相同；**八臂同判 ACCEPT**；台账 round 6 第三行。残余：C7 的 DPA / 安全评估半边 IR 无对象可查，只实现了同意项半边。

**2026-10-24 用户裁定合入生产**：`git apply P14.patch`，h_i 基线重算四集（`results/r6.h_i.post-P14.*.jsonl`）与沙箱逐行相同；`__init__.py` 桩 65 → 63。合入后 W49 补录 brief（`examples/utterances.2026-W49.brief.md`）只写数据与同意合规 t4 的 C7 类口语 10 句（目标 ≥ 4 句进引擎），不写 C5 类。**此后 B_6 / real-all 的 h_i 读数以 post-P14 为准**（P12 / P13 仍未合入）。

## 4. 归因（待标注）

留空。标注前的候选（以标注为准）：
- **指标口径 t3 的 11 句全被 R48 拒**：LLM 把序号填进 sensor_serial、不给 dedup_key，与 W46 P9 同因。按 CQ 期望这 11 条是 wrong 候选；若标注 wrong + rule 层，它们就是 B_5 一直缺的 dup 案例——**holdout-6 第一次有能力在留出集上区分 P9a / P9b / P9c**（round 5 第 2–4 次裁决的盲点正是 B 里没有 dup 案例）。P9a 合入与否的决定因此可以等 B_6：先抽 B_6，对三份修法各算一次 regress，再定。
- ask 查 0 行 12 条，全在「回执了没 / 签了没 / 推送了没 / 分层哪天出的 / 谁确认的」状态字段上，seed 对应对象无这些字段或边，与 W46 / W47 同型（seed 层，不归本体）。

## 5. round 5 遗留四项（续 W47 报告 §5）

①（v3 签字）与 ③（W_evid 不可得）不变。② regress_any 不进 v3 不变；②′ 分层键已裁定 source 键 + override。④ P9a：本窗口的 11 条 dup 候选给了新路径——**等 B_6 用真留出集判三份修法再决定合入**，而不是先合入再判回退。
