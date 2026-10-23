# 正式 run 需要准备的三类数据 —— 真实窗口 2026-W43

本目录只放**真实窗口**：轨迹是 clife-onto-engine `execute` / `ask` 真跑出来的审计记录（参数 ⊆ 动作声明、对象 id 在库里查得到），反馈由业务侧的人标。三类数据分别喂给 evolve 管线的三个入口，缺一类对应的读数就算不出。

| 数据 | 喂给 | 产出 | 判据要求（criteria.yaml） |
|---|---|---|---|
| ① 引擎审计日志（轨迹） | `evolve-attribute`（`config.yaml: trajectory_source`） | 提案流；与 ② 一起落成 `cases/real/` | 15 轮 × 每轮 ≥ 6 条提案 → 每轮窗口 ≥ 20 条有反馈的轨迹 |
| ② 反馈标签 | `evolve-attribute`（`trajectories/{window}/feedback.yaml`） | `cases/real/*.yaml`（外关卡留出集唯一来源） | real 池 ≥ 200 条，family × tier × time_half 每层 ≥ 16 |
| ③ 只读数据源 | `evolve-ground`（`config.yaml: sources` + IR §6 Mapping） | IR §8 Evidence → W_evid 可测 | 每个对象 / 映射 / function 规则一条探测采样 |

## 目录

| 路径 | 是什么 | 真到什么程度 |
|---|---|---|
| `record_window.py` | 网关样例：口语 → 真 Qwen（qwen3.5-plus）路由 → `Session.ask` → `ActionEngine.execute` / OQL，审计落 `SqliteAuditStore`；`export` 子命令从 sqlite 导出并补 trace_id / ts / utterance / cost 四个键 | 就是 `../config.yaml` `trajectory_source.export` 约定的接法；引擎 44d8ce1、插件 0.1.1 均为生产代码 |
| `utterances.2026-W43.yaml` | 喂进去的 42 句口语：golden 28 句 + 仿真库 14 句（都带演示租户对象 id），角色医师，带 `cq/session_context.txt` | 口语是 CQ 原句；`cq_expect` 只是 CQ 的领域期望，给标注人参考，不是标签 |
| `routing.log.2026-W43.jsonl` | 42 句的路由去向全记录 | 7 句被 Qwen 路由成 advise / clarify，不是轨迹，只留在这里 |
| `engine-audit/audit.db`（gitignore） | 引擎 audit 表（24 行）+ 网关 gateway_trace 表（execute 24 / ask 11） | 真 sqlite；`../config.yaml` 的 `export.from` 指向它 |
| `trajectories/2026-W43/audit.jsonl` | ① **35 条真实轨迹**：execute 24（committed 3 / pending_hil 6 / rejected 15）、ask 11 | execute 行 = 引擎 `AuditSnapshot.to_dict()` 原样 + 四个键，一个字段没手改；参数越界 0；cost.tokens 全部来自真实 usage |
| `replay_check.py` | 回放校验：新鲜 seed 上按窗口顺序重新 execute / 重跑 OQL | **35/35 复现**；`--mode preview`（每条独立预演）有 5 条差异，全是窗口内前序写入导致的状态依赖——这就是案例要带 `setup` 的原因 |
| `trajectories/2026-W43/feedback.yaml` | ② **已标注反馈**（`status: reviewed`，reviewer Ameng2001 / 本体负责人，2026-10-23）：correct 26 / wrong 7 / partial 2 | 由 `draft_feedback.py` 起草清单，标签采纳自 `feedback.expert-draft.yaml` 的 35 条建议；wrong 带 truth_expect 与 layer（rule 1 / router 6） |
| `make_real_cases.py` | ①+② → ②' `cases/real/{family}-rNN.yaml`（evolve-attribute 第 1 步的样例实现，幂等） | feedback 不是 `status: reviewed` 或有空 label 就拒绝落；每条案例带 `setup`（窗口内前序落库动作）、`route`（当时真走的意图）、wrong+rule 的 `expect_not` |
| `cases/real/` | 33 条（partial 2 条不落） | 根工作区 `../cases/real/`；h_i 78/99，D⁻ 7 条见 `../attribute-report-2026-W43.md` |
| `config.sources.yaml` | ③ `sources` 段 + 审计导出约定，贴进 `../config.yaml` | 主机名是约定占位：pg-ro / ch-ro 不可达、环境变量未设；唯一真实可达的是上面的 sqlite 审计库 |

## ① 轨迹：`trajectories/2026-W43/audit.jsonl`

一行一次 `execute` / `ask`。字段就是 `AuditSnapshot.to_dict()` 再补四个管线要的键：

| 键 | 来源 | 为什么要 |
|---|---|---|
| `trace_id`、`ts` | 网关注入（内核不读 wall clock） | 反馈标签靠 trace_id 对上；ts 决定 `observed_at` 与 time_half 分层 |
| `utterance` | 路由前的原始口语 | 落成案例的 `q`；没有它只能拿 params 反推，归因精度降级（COARSE_TRAJECTORY） |
| `action`、`inputs_snapshot`、`rules_evaluated`、`decision`、`evidence` | 引擎审计自带 | 分歧点定位：哪一步、哪条规则、裁决是什么 |
| `cost` {steps, tokens, wall_s} | 网关从 LLM 客户端 usage 取 | C 维；没有 tokens 只能按步数计（COST_BY_STEPS） |

ask 行引擎不审计（只读），由网关记编译出的 OQL 原文 + 行数。两个引擎口径：`rules_evaluated` 只记 **violate** 的规则；guard 阶段命中 hard 即返回，不再跑写后规则，所以同一句在不同状态下命中的规则集合可以不同。

录一个新窗口：

```bash
python3 record_window.py run --engine-root ../../../../onto-fundary-plugins --plugin ../../../plugins/glycowise --utterances utterances.<window>.yaml --context-file ../../../plugins/glycowise/cq/session_context.txt --audit-db engine-audit/audit.db --pin-ip 8.140.217.18
python3 record_window.py export --audit-db engine-audit/audit.db --window <window> --out trajectories/<window>/audit.jsonl
python3 replay_check.py --engine-root ../../../../onto-fundary-plugins --plugin ../../../plugins/glycowise --window <window>
python3 draft_feedback.py --window <window>
```

## ② 反馈：`trajectories/2026-W43/feedback.yaml`

每条轨迹一项，`correct / partial / wrong`，由医师 / 健管主管 / 合规官填：

- **引擎拒绝得对也标 correct**：拒绝是正确行为，这类案例是 rejected 口径的真实来源。
- **wrong 必须写 truth**（一句真实根因）和 **truth_expect**（真实应有的裁决，如 `rejected(R42_…)`）：归因器据此找分歧点，落成案例的 `expect` 直接取它。
- `partial` 只用于成本统计，不进 D⁺ / D⁻。
- 标签人要可追溯（`reviewer`），进台账的 contamination_note；填完把 `status` 改成 `reviewed`。
- 标签是私有的，永远不进提示词。
- `suggested` / `suggested_why` 是机器拿 CQ 期望比对引擎裁决的参考，不是标签。

机器比对与 CQ 期望不一致的 9 条，给标注人的线索（不是结论）：

| trace | 口语 | CQ 期望 | 引擎实际 | 线索 |
|---|---|---|---|---|
| 0007 / 0029 / 0031 / 0040 / 0041 / 0042 | 6 句 query | 查到行 | 0 行 | 多数是 Qwen 选了没有该字段的对象或 where 口径不对（如 TAR 字段名、ReviewEvidence 多跳），属路由层；0041 / 0042 seed 里确有 AlertTemplate / HypoState 行 |
| 0008 | 给 P0012 生成方案草稿 | action(生成方案草稿) | rejected(低血糖优先抢占, R14) | P0012 昨夜有 L1 夜间事件，规则层抢占；这条 CQ 期望本身可能要改 |
| 0018 | 群里答复"二甲双胍减到一片" | rejected(D10) | rejected(R51) | guard 阶段 R51 先命中就返回了，D10 在写后规则没机会跑；拒绝得对但命中的不是期望规则 |
| 0022 | OCR 2.8 直接发危急告警 | rejected(R53) | rejected(R56) | 同上：推送告警的 guard 里 R56 排在 R53 前 |

## ②' 落成的真实案例：`cases/real/`

attribute 第 1 步自动从 ①+② 生成，不用手写：`python3 make_real_cases.py --window 2026-W43`。expect 对 correct 取引擎实际裁决（ask→query；committed/pending_hil→action(名)；rejected→rejected(首条 violate 规则)），对 wrong 取 truth_expect；tier 按 query=1、多跳=2、action/rejected=3、HIL=4；family 对仿真库的 10 个 family（指标口径 / 参考与配置 / 因果链溯源 / 低血糖安全 / 高血糖与波动 / 结论层与分层 / 缓解路径 / 出口签发闸 / 产品与机构合规 / 数据与同意合规）；id 用 `{family}-rNN`，与 `cases/sim` 的 `{family}-NN` 不同名（runner 按 id 取案例）。案例自带 `setup`（同窗口前序落库的 execute，runner 先在新鲜 seed 上真跑它们再评判）、`route`（轨迹当时真走的意图，runner 对带 route 的案例不查共享录制——同一句口语 golden 录的参数与窗口不同时以窗口为准）、wrong+rule 的 `expect_not`（业务侧裁定不该响的规则，命中即 fail）。`plugins/glycowise/cq/make_real_routes.py` 仍把窗口意图登记进 `all_routes.json`（`setdefault`，不覆盖 golden），供没有 route 的旧案例或别的 runner 用。

## ①-2 第二个真实窗口：`trajectories/2026-W44/`

同一天录的第二个进化窗口（逻辑窗口号 W44，`record_window.py run --window 2026-W44 --seq-base 100`；ts 如实是 2026-10-23，`--window` 只覆盖窗口标签）。目的：让留出集跨窗口、回退能按 B_{i+1} 算。

| 项 | 值 |
|---|---|
| 口语 | `utterances.2026-W44.yaml` 61 句，全部是仿真库里 W43 没用过的 CQ 原句，按患者分组、按「查 → 出草稿 → 触发/回执/阈值 → 答复」排，让窗口内裁决互相依赖 |
| 轨迹 | **51 条**：execute 28（committed 8 / pending_hil 7 / rejected 13）、ask 23 |
| 非轨迹 | 10 句：clarify 8、advise 1、error 1（`routing.log.2026-W44.jsonl`） |
| 回放 | sequential 51/51 复现；preview 3 条不一致（0119/0120 多出 C22、0158 多出 R49），待标注人看是否前序写入导致 |
| 成本 | 真 Qwen usage 共 415,733 token，均 6,815/句 |
| 反馈 | `trajectories/2026-W44/feedback.yaml` **reviewed**（2026-10-23，标签采纳自专家草案，correct 40 / wrong 9 / partial 2）；专家建议草案 `feedback.expert-draft.yaml`：correct 40 / partial 2 / wrong 9（router 8：0105 / 0115 / 0117 / 0119 / 0121 / 0124 / 0138 / 0154；rule 1：0118 R04a 假阴性——`_prev_reading` 取到 2h15m 前另一段事件的尾巴当「连续 2 读数」）。只供标注人确认，不是标签 |

非轨迹 10 句里值得记的：
- **LLM 路由层预判拒绝 5 句**（0125 戴 6 天判缓解→它自己搬 R01；0129「我来给您诊断」→C19；0130「夜里出事我们第一时间知道」→R54；0131「建议您去医院开处方」→它按 C19 拒，而这正是 P4 已合入生产、引擎会放行的转介句——规则层改了，路由层还在用旧禁令；0134 推送未签发草稿→C9）。与 W43 golden 去钓前的现象同源：规则层能稳定裁决的句子，路由层不稳定。
- **能力清单缺口 2 句**（0140 ABCD 筛查化验分项、0159 平台留存/审计策略）：LabResult 只有通用 value/method，平台级策略对象没暴露——记本体 backlog（新增对象/属性候选，不是规则）。
- **路由到 telemetry 1 句**（0126 平均血糖 → 编译器 `无遥测绑定: CgmSummary` 直接 reject）：Qwen 把一个普通查询判成遥测读数，引擎没有 CgmSummary 的遥测绑定——平台 backlog。
- 0155（群里答复分层 L1）Qwen 问「要我做什么」；0156 走 advise。

## ①-3 第三个真实窗口：`trajectories/2026-W45/`

同一天录的第三个进化窗口（`record_window.py run --window 2026-W45 --seq-base 201`）。103 条 CQ 原句在 W43/W44 已用尽，本窗口全部取仿真库变体：entity_swap（换患者，对象 id 来自 seed）37 句 + paraphrase（同一 CQ 的省略式口语改写）38 句，顺序沿用 W44 的患者分组。目的：把 real 池推向 200，同时看路由层对省略式口语的稳定性。

| 项 | 值 |
|---|---|
| 口语 | `utterances.2026-W45.yaml` 75 句（entity_swap 37 / paraphrase 38） |
| 轨迹 | **63 条**：execute 31（committed 10 / pending_hil 8 / rejected 13）、ask 32（0 行 10 条） |
| 非轨迹 | 12 句：clarify 9、error 3（`routing.log.2026-W45.jsonl`） |
| 回放 | sequential 63/63 复现；preview 3 条不一致（0220/0221 多出 C22、0259 多出 R49），与 W44 同型（execute 与 validate 的语义差） |
| 成本 | 真 Qwen usage 共 513,505 token，均 6,847/句 |
| 反馈 | `trajectories/2026-W45/feedback.yaml` **reviewed**（2026-10-23，标签采纳自专家草案，correct 45 / wrong 13 / partial 5）；专家建议草案 `feedback.expert-draft.yaml`：correct 45 / partial 5 / wrong 13（**router 13，rule 0**：多挂一跳 ×6（0222/0225/0255/0262/0269/0270）、'now-14d' ×3（0239/0271/0272）、枚举字面量 ×2（0268 level='high'、0220 口语「高级」覆盖告警级别）、选错字段 0218、摄入读数 payload 平铺 0273）。只供标注人确认，不是标签 |

非轨迹 12 句里值得记的：
- **生产插件有两个动作只有桩**：0224「健管师让 P0031 去找医生看是否调药方案」路由到动作 `转介医师`、0233「用厂商记录 ID 做去重键」路由到 `去重与通道仲裁`，引擎执行时 `NotImplementedError: … handler 待实现`。这两个动作在 IR §4 有声明、在 `__init__.py` 里挂着桩（同类桩还有 10 个派生函数：MAGE / AGP分位曲线 / wear_ratio / glucose_slope / dedup_hit_rate …），W43/W44 的口语从没路由到它们。这是第一次由真实窗口暴露**实现缺失**（IMPL_MISSING），是下一轮提案流的种子，不是路由问题。
- **路由到 telemetry 1 句**（0227「P0088 的均值血糖读数？」→ `无遥测绑定: CgmSummary`）：与 W44 0126 同因，省略式口语更容易被判成遥测读数——平台 backlog。
- **LLM 路由层预判拒绝 / 追问 9 句**（0226 6 天判缓解、0230「要给她诊断」、0231「夜里出事我们第一时间知道」、0232「去医院开处方」、0235 草稿直发患者、0244「用英纽林逆转」、0245「恭喜您已经逆转了」、0247 L3 包捆英纽林、0260 查 retention_policy）：全部是仿真库 rejected 口径的改写句，路由层继续抢闸，引擎 HARD 规则没被评到——与 W43/W44 现象同源，第三次复现。

## ①-4 第四个真实窗口：`trajectories/2026-W46/`

同一天录的第四个窗口（`record_window.py run --window 2026-W46 --seq-base 301`）。目的：把 real 池推向 200，并补 real 池里最薄的五个 family。80 句全部取仿真库里前三窗口没用过的句子：五个薄 family（缓解路径 / 数据与同意合规 / 因果链溯源 / 结论层与分层 / 出口签发闸）全取 64 句，再补低血糖安全 15、高血糖与波动 1。变体构成 original 9（P7 / P8 新补的 CQ 原句）、paraphrase 29、**irrelevant_field 42**（第一次把带无关从句的口语喂给真路由）。

| 项 | 值 |
|---|---|
| 口语 | `utterances.2026-W46.yaml` 80 句 |
| 轨迹 | **69 条**：execute 52（committed 9 / pending_hil 16 / rejected 27）、ask 17 |
| 非轨迹 | 11 句全是 clarify（`routing.log.2026-W46.jsonl`）：9 句应拒口语被 LLM 抢先反问（D8 ×2、C19、R54 ×2、C6、R51、C9；validate 复核引擎都会拒），2 句判定缓解被抢先，1 句（0326）LLM 声称找不到吴康复师但 seed 里 S-WU 存在 |
| 回放 | sequential 69/69；preview 66/69（0312/0313/0325 多出 C22，与 W44/W45 同型） |
| 成本 | 真 Qwen usage 共 472,907 token，均 5,911/句 |
| 反馈 | `feedback.yaml` **draft（待标注人确认）**；专家建议草案 `feedback.expert-draft.yaml`：correct 39 / partial 6 / wrong 24（**router 14 / rule 5 / seed 5**）。只供标注人确认，不是标签 |

草案里值得记的（标注人未确认前都是候选）：
- **第一次有规则层 wrong**（5 条，全在刚合入的 P8 `去重与通道仲裁`）：无序号的 OCR / 伪差读数（0354/0355 art1、0362–0364 ocr9）按 IR 应落 weak_dedup 回退，R48 却硬拒，除非调用方显式传 `weak_dedup: true`；另 6 条 dup1 / x9 是路由层——LLM 把「序号 SN-P0045-A-01343」填进 `sensor_serial`、没给 `dedup_key` / `time_utc`，补上后实测 dup1 → superseded、x9 → clean。R48 对「有序号没 dedup_key」应派生而不是拒，是下一轮提案的候选，而且是第一个**有争议的**提案：朴素修法（放宽 R48）与根因修法（派生 dedup_key / 回退 weak_dedup）在 Dᵢ 上同样过，S / W 上应分出高下。
- irrelevant_field 的泄漏：无关从句进了面向患者的群消息正文（0322/0346）和 ReferralRecord.question（0307/0378/0379，经同一 actor 的 Session 记忆串到了 original / paraphrase 句）；一句把「市一医院」当成 lab_id 过滤（0303）。
- seed 不一致 5 条 wrong：40 个 LinkType 声明、seed 里 0 条边（0336/0340/0374 合法多跳查 0 行）；Credential 的 holder 装名字、id 在非 IR 字段 holder_id（0381）；tier_label 陈旧（0319）。cred-chen 2026-09-20 到期仍 valid 且签了 plan-P0066-w41。
- 摄入读数平铺 payload 时 IngestBatch record_count=0 仍 committed（0316/0317）；推送告警 level「中级」vs 模板枚举「中」（0312/0313）。

## ③ 数据源：`config.yaml` 的 `sources` 段

完整样例见 `config.sources.yaml`（postgres 55 个对象、clickhouse 7 个对象；密码走 `${GLYCOWISE_PG_RO_PASSWORD}` / `${GLYCOWISE_CH_RO_PASSWORD}`；每个 store 带 `probe.limit: 20` 与超时；文末有 psql / clickhouse-client 连通性自检命令）。evolve-ground 对 IR §6 每一行跑 `SELECT … LIMIT 20` 取样写进 §8；要求只读账号、假名化视图、能从跑管线的机器直连。主机名目前是占位，业务侧开通账号后替换。

## 要多少

| 阶段 | 数量 | 现状 |
|---|---|---|
| 最小可开工（验证接法） | 一个窗口 20 条有反馈轨迹，含 ≥3 条 wrong | W43：35 条真实轨迹已就位，等业务侧标 |
| 正式 run 门槛 | 累计 ≥200 条有反馈轨迹，8 个分层各 ≥16 | 再录 5–6 个真实窗口（每周一个，换一批口语） |
| 全程 | 15 轮 × 3 seed，≥900 条有反馈轨迹 | 约 26 个真实窗口 |

没反馈的轨迹可以多收，但不参与归因。

## 自检记录

- **2026-10-23 第一轮**：第一版手写的 W44 样例经接入试跑判定不是真实数据（9 条参数越界、wrong 标签与引擎行为不符、引用了 seed 里没有的对象 id），连同其落成案例和合成窗口生成器已全部删除。顺带修了一个真问题：real 与 sim 共用 `{family}-NN` 的 id 会在 runner 里互相覆盖，real 改为 `{family}-rNN`。
- **2026-10-23 第二轮**：按硬判据重录 W43（本目录现状）。核查项：35 条口语全是 CQ 原句；参数 / OQL 引用的对象 id 在 seed 的 6970 个对象里逐个查到（仅 3 个是动作要新建的键）；trace_id / ts 落在真跑的那三分钟；feedback 一条未填；根工作区的 trajectories、cases/real、real_routes.json 不存在。
- **2026-10-23 第三轮**：独立复核 W43——`replay_check.py --mode sequential` 在新鲜 seed 上 35/35 复现，24 条 execute 参数全部在动作声明内（越界 0）。`feedback.yaml` 仍是 draft、35 条 label 为空，所以 `cases/real/` 仍为空、attribute 不能开。专家子代理给了一份建议标签 `trajectories/2026-W43/feedback.expert-draft.yaml`（status: expert-draft），只供标注人确认，不是标签。
- **2026-10-23 第四轮**：标签入库（`feedback.yaml` reviewed）→ `cases/real` 33 条 → attribute → verify 走通。两处只有真数据才暴露的坑：① 逐案例新鲜 seed 复现不了窗口状态（0008/0021/0022 判错、0018 的泄漏不出现）→ 案例加 `setup`；② 共享录制按口语键让 golden 参数覆盖了窗口真走的参数 → 案例加 `route`。P5（`_staged: True` 持久化标记跨动作泄漏）3d ACCEPT、real 留出集 20 条，同日确认合入生产（real-all 81/99、B-sim 294/294）；路由层 6 条 wrong 不归本体，记平台 backlog。
- **2026-10-23 第五轮**：录第二个窗口 W44（61 句 → 51 条轨迹，`--window` 覆盖逻辑窗口号）。顺序回放 51/51；preview 3 条差异全是引擎 execute（guard 命中即返回、不评 post 规则）与 validate（全收集）的语义差，不是状态依赖。P5 在新窗口里验证：0113 落库证据包后 0114/0123/0127/0128 的规则命中集合与单独预演一致。专家草案见上表；标注人确认进 `feedback.yaml`（status reviewed）后：`make_real_cases.py --window 2026-W44` → 留出集 round 3 从 W43+W44 池抽（跨窗口）→ P5 在 B_3 上的 `readings/P5-{hi,hp}-B3.json` → `arm_compare.py` 按 B_{i+1} 判回退。
- **2026-10-23 第六轮**：W44 标签入库（`feedback.yaml` reviewed，correct 40 / wrong 9 / partial 2）→ `cases/real` 累计 82 条（修了 `make_real_cases.py` id 正则不认 `-rNN`、覆盖 W43 案例的 bug）→ `holdout-3.yaml` 第一次跨窗口（40 条 / 20 层，W43 19 / W44 21）。P5 在 B_3 上无回退（A .75→.825，W44 两条 HIL 答复 r16/r18 的 R51 泄漏被修）。P6（R04a「前一读数」不看采样间隔）3d ACCEPT、八臂同判，同日确认合入生产（real-all 210/246、B-sim 294/294）；仿真案例 低血糖安全-01 与 real 反馈冲突，选择器加 20 min 间隔条件后重生成，B-sim 98/98。见 `attribute-report-2026-W44.md`。
- **2026-10-23 第七轮**：录第三个窗口 W45（75 句变体 → 63 条轨迹，execute 31 / ask 32；513k token）。顺序回放 63/63；preview 3 条不一致与 W44 同机理（execute 在 guard hard 命中时只审计 guard 违规并返回；guard-soft 违规不进审计）。专家草案：correct 45 / partial 5 / wrong 13，wrong 全在路由层——三类路由错误（多挂一跳、相对时间字面量、枚举字面量）第三个窗口复现，规则层 0 条 wrong。窗口第一次暴露生产插件的**实现缺失**：`转介医师`、`去重与通道仲裁` 两个动作只有桩（0224/0233 NotImplementedError）。专家另记的规则实现偏离 IR 候选（待标注人裁定，未开提案）：R04a 只判前一读数 <3.9 而 IR 要求两读数都在 3.0–3.9（0219，2.8→3.6 的 L2 恢复段也能开 L1 处置）；摄入读数 0 条批次照样 committed、R48 不看顶层 payload（0273）；推送告警去掉 level 后 `_content_type` 不识别为告警、C22 误拒（0220 变体实测）；R55 拦不住「数据已同步到」这类事实性误述（0229，P0045 当天无读数）；seed 两处不一致（A-P0045-02 raised_at 与真实低值读数差一天；cred-chen 到期 33 天仍 valid）。标注人确认进 `feedback.yaml`（status reviewed）后再 `make_real_cases.py --window 2026-W45`。
- **2026-10-23 第八轮**：W45 标签入库（reviewed）→ `cases/real` 累计 140（修了一次把案例写进 `examples/cases/` 的路径错，重跑到根工作区）→ `holdout-4.yaml` 三窗口（40 / 20 层，W43 7 / W44 12 / W45 21）。h_i 351/420，D⁻ 23 全是路由层，**规则层 0 条 → round 4 无提案**。P6 在 B_4 上无回退（A .825→.85，差的只是它自己的 Dᵢ）。`arm_compare` r1–4：P5、P6 都按 B_{r+1} 判，regress 全 0。随后给两个只有桩的动作补 CQ（`cq/make_impl_cases.py`，8 句 + 变体）作 Dᵢ，沙箱补 handler（P8 连带 R02 / R36 / R48）走双关卡：P7 八臂 ACCEPT、P8 七臂 ACCEPT + random REVISE，B_4 两臂逐行相同、B-sim 294/294；同日合入生产，重放后 real-all 351/420、B-sim 294/294 与沙箱逐行相同（`results/*.post-P8.jsonl`）。见 `attribute-report-2026-W45.md` §6。
- **2026-10-23 第九轮**：录第四个窗口 W46（80 句 → 69 条轨迹，execute 52 / ask 17；473k token；顺序回放 69/69）。口语优先补 real 池最薄的五个 family，并第一次喂 irrelevant_field 变体 42 句。专家草案 correct 39 / partial 6 / wrong 24（router 14 / rule 5 / seed 5）——**第一次出现规则层 wrong**：刚合入的 P8 的 R48 对无序号读数硬拒而不是落 weak_dedup 回退；另 6 条去重被拒是 LLM 没填 dedup_key。标签入库（reviewed）→ `cases/real` 累计 **203**，h_i 474/609；`holdout-5.yaml` 四窗口（40 / 20 层）。R48 候选作 P9：根因修法 P9a 与朴素修法 P9b 同走双关卡——Dᵢ 0/15 → 12/15 两份逐行相同，B_5 / B-sim / real-all 也逐行相同，P9a 七臂 ACCEPT + random REVISE，P9b **八臂 ACCEPT**；差别只在落库状态（dup1 superseded vs 当新读数入库），判据读不到。随后 runner 加 `expect_state`（对 validate 暂存对象字段断言），15 条 dedup 案例补落库真值，重判：Dᵢ 上 P9a 12/15、P9b 0/15；但 3d 仍接受 P9b（strict 被 ΔC −0.8 满足：steps 把违规数计成本，放行比拒绝便宜），只有 1d-strict 拒。再做 criteria amend（v3：strict 只认 T/S/W）重判：3d 族 REJECT P9b、1d ACCEPT——第一个分歧集，但 B_5 对其写错盲（regress 0）。两份都未合入。见 `attribute-report-2026-W46.md` §4、`proposals/P9.md`。同日收尾两件：① `holdout_sample --merge-min 8 --check-pool`（family×tier，<8 并入同 family 的 rest 层）复核 real 池前置：203 ≥ 200 ✓，但并层后仍有 8 个 family×rest 层不足 8（产品与机构合规 4 / 低血糖安全 5 / 出口签发闸 3 / 参考与配置 7 / 因果链溯源 7 / 指标口径 7 / 缓解路径 2 / 高血糖与波动 4）——前置仍 **未达**，下一窗口口语要优先补这些 family 的非主 tier。② `cases/real` 里其余 54 条 correct 写类动作案例（16 个动作）补 `expect_state`，期望值只从 IR §4 writes 列 + 路由参数 + 参考数据里的固定事实推出（键含时间戳/当日日期的对象用新加的 `key_prefix`），现 65/203 条带落库断言；h_i 复跑 real-all **471/609**（原 474：唯一新失败是 数据与同意合规-r02「摄入读数」——路由把单条读数平铺进 raw_payload，而 handler 只读 `raw_payload.readings[]`，结果一条读数都没暂存、IngestBatch.record_count=0；reviewed 标签按 C3 放行判了 correct，但落库为空。IR §4 只写 `raw_payload:object`，golden 录制一律用 `readings[]` 形状、这条真实窗口的 Qwen 路由平铺了——归路由层，登记为判据发现，不在本轮修）。另一处是我方推导错：P0007 分层按规格均值估成 L1，reviewed 标签记录 GMI 6.15 → R18 分带应为 L2，已按标签改正。 ③ 用带断言的 B_5 / real-all 重判 P9a/P9b（attempt 4）：B_5 读数与 attempt 3 相同（90→96/120），八臂裁决逐格不变，`arm_compare` regress_rate_diff **仍 0**——P9b 写错的 8 条案例 h_i 本来就不过（硬拒 vs 错写同为 fail），外关卡的回退口径结构上看不见「换一种失败」的朴素修法，只有内关卡成长轴能拒；见 `proposals/P9.md` 第 4 次裁决。
