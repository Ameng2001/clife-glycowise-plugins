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
| `replay_check.py` | 回放校验：新鲜 seed 上按窗口顺序重新 execute / 重跑 OQL | **35/35 复现**；`--mode preview`（每条独立预演）有 5 条差异，全是窗口内前序写入导致的状态依赖 |
| `trajectories/2026-W43/feedback.yaml` | ② **待标注清单**（`status: draft`，35 条 `label: null`），由 `draft_feedback.py` 生成 | 每条列了引擎实际裁决与 CQ 期望的机器比对（9 条不一致）；**标签由业务侧填** |
| `make_real_cases.py` | ①+② → ②' `cases/real/{family}-rNN.yaml`（evolve-attribute 第 1 步的样例实现，幂等） | feedback 不是 `status: reviewed` 或有空 label 就拒绝落 |
| `cases/real/` | 空 | 等 reviewed 的反馈 |
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

attribute 第 1 步自动从 ①+② 生成，不用手写：`python3 make_real_cases.py --window 2026-W43`。expect 对 correct 取引擎实际裁决（ask→query；committed/pending_hil→action(名)；rejected→rejected(首条 violate 规则)），对 wrong 取 truth_expect；tier 按 query=1、多跳=2、action/rejected=3、HIL=4；family 对仿真库的 10 个 family（指标口径 / 参考与配置 / 因果链溯源 / 低血糖安全 / 高血糖与波动 / 结论层与分层 / 缓解路径 / 出口签发闸 / 产品与机构合规 / 数据与同意合规）；id 用 `{family}-rNN`，与 `cases/sim` 的 `{family}-NN` 不同名（runner 按 id 取案例）。落成后用 `plugins/glycowise/cq/make_real_routes.py` 把轨迹里真走过的意图登记为 manual 路由供 runner 回放。

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
