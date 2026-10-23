# 正式 run 需要准备的三类数据 —— 样例

本目录全部是**样例**（患者 id 与数值沿用演示租户 seed，非真实数据），给业务侧照着准备。三类数据分别喂给 evolve 管线的三个入口，缺一类对应的读数就算不出。

| 数据 | 喂给 | 产出 | 判据要求（criteria.yaml） |
|---|---|---|---|
| ① 引擎审计日志（轨迹） | `evolve-attribute`（`config.yaml: trajectory_source`） | 提案流；与 ② 一起落成 `cases/real/` | 15 轮 × 每轮 ≥ 6 条提案 → 每轮窗口 ≥ 20 条有反馈的轨迹 |
| ② 反馈标签 | `evolve-attribute`（`trajectories/{window}/feedback.yaml`） | `cases/real/*.yaml`（外关卡留出集唯一来源） | real 池 ≥ 200 条，family × tier × time_half 每层 ≥ 16 |
| ③ 只读数据源 | `evolve-ground`（`config.yaml: sources` + IR §6 Mapping） | IR §8 Evidence → W_evid 可测 | 每个对象 / 映射 / function 规则一条探测采样 |

## 目录

| 路径 | 是什么 |
|---|---|
| `trajectories/2026-W43/audit.jsonl` | ① **真实窗口**：35 条引擎真跑出来的轨迹（见文末） |
| `trajectories/2026-W44/audit.jsonl` | ① 格式样例（手写，非引擎产出）：20 条轨迹（17 execute：committed 8 · rejected 7 · pending_hil 2；3 ask），覆盖 10 个 family |
| `trajectories/2026-W44/feedback.yaml` | ② 这 20 条的标签：correct 14（含 7 条「拒绝得对」）/ wrong 4 / partial 2，三位标签人可追溯 |
| `cases/real.format-sample/*.yaml` | ②' 的**格式样例**（由 W44 手写样例落成，不是真实案例，不得进 `cases/real/`） |
| `make_real_cases.py` | ①+② → ②' 的样例实现（幂等，按 family 顺延编号），`python3 make_real_cases.py --dry-run` 先看 |
| `config.sources.yaml` | ③ 只读数据源 `sources` 段 + 审计导出约定，贴进 `../config.yaml` |
| `record_window.py` / `replay_check.py` / `draft_feedback.py` | 真实窗口三件套：真跑引擎录轨迹、回放校验、起草待标注清单（见文末「真实窗口 2026-W43」） |
| `gen_synthetic_windows.py` | 按 200 / 900 门槛生成**合成**窗口验证接法与分层（产物 `synthetic/` 已 gitignore，不得混入 `cases/real/`） |

## ① 轨迹：`trajectories/2026-W44/audit.jsonl`

一行一次 `execute` / `ask`。字段就是 clife-onto-engine `AuditSnapshot.to_dict()` 再补四个管线要的键：

| 键 | 来源 | 为什么要 |
|---|---|---|
| `trace_id`、`ts` | 调用方注入（内核不读 wall clock） | 反馈标签靠 trace_id 对上；ts 决定 `observed_at` 与 time_half 分层 |
| `utterance` | 路由前的原始口语 | 落成案例的 `q`；没有它只能拿 params 反推，归因精度降级（COARSE_TRAJECTORY） |
| `action` / `oql`、`inputs_snapshot`、`rules_evaluated`、`decision`、`evidence` | 引擎审计自带 | 分歧点定位：哪一步、哪条规则、裁决是什么 |
| `cost` {steps, tokens, wall_s} | 调用方从 LLM 客户端取 | C 维；没有 tokens 只能按步数计（COST_BY_STEPS） |

引擎侧最省事的接法：把 `SqliteAuditStore` 的 `audit` 表按 `ontology_id='glycowise'` 导出 JSONL，再由网关补 trace_id / utterance / cost。规模：一个进化窗口 20 条，15 轮 × 3 seed 至少 900 条**有反馈**的轨迹；没反馈的可以多，但不参与归因。

## ② 反馈：`trajectories/2026-W44/feedback.yaml`

每条轨迹一项，`correct / partial / wrong`。要点：

- **引擎拒绝得对也标 correct**（样例 0002）：拒绝是正确行为，这类案例是 rejected 口径的真实来源。
- **wrong 必须写 truth**（样例 0003）：真实根因一句话，归因器据此找分歧点；`root_cause_hint` 可选，只当线索。
- `partial` 只用于成本统计，不进 D⁺ / D⁻。
- **wrong 还要给 `truth_expect`**（真实应有的裁决，如 `rejected(R42_…)`）：落成案例的 `expect` 直接取它，归因器不猜。
- 标签人要可追溯（`reviewer`），进台账的 contamination_note；顶层写默认标签人，单条可覆盖（样例里合规类三条由 `u-compliance-01` 标）。
- 标签是私有的，永远不进提示词。

## ②' 落成的真实案例：`cases/real/*.yaml`

attribute 第 1 步自动从 ①+② 生成，不用手写；`make_real_cases.py` 是这一步的样例实现，W44 的 20 条落成 18 条（2 条 partial 不落）：

| family | 落成 | 来源轨迹 |
|---|---|---|
| 低血糖安全 | 3 | 0001 触发处置 ✓ · 0017 闭环（wrong→R44）· 0020 转介 HIL |
| 结论层与分层 | 2 | 0008 R01 拒绝 ✓ · 0009 分层（wrong→R42） |
| 出口签发闸 | 2 | 0002 D11a 拒绝 ✓ · 0012 签发（wrong→D13） |
| 高血糖与波动 | 2 | 0003 强化草稿（wrong→R35）· 0018 维持草稿 ✓ |
| 缓解路径 / 产品与机构合规 / 数据与同意合规 | 各 2 | 一条 committed 或 HIL，一条拒绝得对 |
| 指标口径 / 参考与配置 / 因果链溯源 | 各 1 | query（tier 1 / 1 / 2） |

这里给出样子是为了让业务侧知道反馈最终会变成什么。family 取流程决策点名，要和仿真案例库的 10 个 family 对得上（指标口径 / 参考与配置 / 因果链溯源 / 低血糖安全 / 高血糖与波动 / 结论层与分层 / 缓解路径 / 出口签发闸 / 产品与机构合规 / 数据与同意合规），tier 按 query=1、多跳=2、action/rejected=3、HIL=4。

## ③ 数据源：`config.yaml` 的 `sources` 段

完整样例见 `config.sources.yaml`（两个 store：postgres 55 个对象、clickhouse 7 个对象；密码走 `${GLYCOWISE_PG_RO_PASSWORD}` / `${GLYCOWISE_CH_RO_PASSWORD}`；每个 store 带 `probe.limit: 20` 与超时；文末有 psql / clickhouse-client 连通性自检命令）。贴进 `../config.yaml` 时替换掉 `TODO(FDE)` 的两行。

```yaml
sources:
  - store: postgres            # IR §6 Mapping Hints 里每个 store 一条
    dsn: "postgresql://glycowise_ro:${GLYCOWISE_PG_RO_PASSWORD}@pg-ro.glycowise.internal:5432/glycowise?sslmode=require"
    schema: cgm_pseudo         # 假名化视图
  - store: clickhouse
    dsn: "clickhouse://glycowise_ro:${GLYCOWISE_CH_RO_PASSWORD}@ch-ro.glycowise.internal:9440/glycowise_metrics?secure=true"
```

evolve-ground 对 IR §6 每一行（`store / table / key / columns`）跑 `SELECT … LIMIT 20` 取样写进 §8；要求：只读账号、脱敏视图（患者 id 已假名化）、能从跑管线的机器直连。当前 IR §6 的 table / columns 若与库里不一致会标 `mismatch`，这本身就是正式 run 前要清的债。

## 要多少

| 阶段 | 数量 | 本目录对应 |
|---|---|---|
| 最小可开工（验证接法） | 一个窗口 20 条有反馈轨迹，含 ≥3 条 wrong | `trajectories/2026-W44/`：20 条，wrong 4 |
| 正式 run 门槛 | 累计 ≥200 条有反馈轨迹，tier × time_half 8 个分层各 ≥16 | `python3 gen_synthetic_windows.py --target 200` → 10 个合成窗口，每层 25 |
| 全程 | 15 轮 × 3 seed，≥900 条有反馈轨迹 | `python3 gen_synthetic_windows.py --target 900` → 45 个合成窗口 |

没反馈的轨迹可以多收，但不参与归因。合成窗口只证明管线接法与 `holdout_sample.py` 分层能跑通，**真实 real 池只能来自业务侧标过的轨迹**。

## 接入自检（2026-10-23 第一轮，对 W44 手写样例）

W44 那 20 条不是本引擎跑出来的（9 条参数越界、wrong 标签与引擎行为不符、引用了 seed 里没有的对象 id），数据源不可达，所以**W44 只是格式样例**，其落成的案例已挪到 `cases/real.format-sample/`，不得进 `cases/real/`。同时发现并修了一个真问题：real 与 sim 共用 `{family}-NN` 的 id 会在 runner 里互相覆盖，real 改为 `{family}-rNN`。

## 真实窗口 2026-W43（2026-10-23 第二轮）

按硬判据重做：**轨迹必须是引擎 `execute` / `ask` 真跑出来的审计记录，参数 ⊆ 声明、对象 id 在库里查得到；反馈由业务侧的人标。**

| 文件 | 是什么 | 真到什么程度 |
|---|---|---|
| `record_window.py` | 网关样例：口语 → 真 Qwen（qwen3.5-plus）路由 → `Session.ask` → `ActionEngine.execute` / OQL，审计落 `SqliteAuditStore`，`export` 子命令从 sqlite 导出并补 trace_id / ts / utterance / cost 四个键 | 就是 config.yaml `trajectory_source.export` 约定的那条接法，引擎与插件都是生产代码（engine 44d8ce1，插件 0.1.1） |
| `utterances.2026-W43.yaml` | 喂进去的 42 句口语：golden 28 句 + 仿真库 14 句（都带演示租户对象 id），角色医师，带 `session_context.txt` | 口语是 CQ 原句；`cq_expect` 只是 CQ 里的领域期望，给标注人参考，不是标签 |
| `routing.log.2026-W43.jsonl` | 42 句的路由去向全记录 | 7 句被 Qwen 路由成 advise / clarify，不是轨迹，只留在这里 |
| `engine-audit/audit.db`（gitignore） | 引擎 audit 表 + 网关 gateway_trace 表 | 真 sqlite，`config.yaml` 的 `export.from` 已指向它 |
| `trajectories/2026-W43/audit.jsonl` | **35 条真实轨迹**：execute 24（committed 3 / pending_hil 6 / rejected 15）、ask 11 | execute 行 = 引擎 `AuditSnapshot.to_dict()` 原样 + 四个键，一个字段没手改；参数越界 0 条；cost.tokens 全部来自真实 usage |
| `replay_check.py` | 回放校验：新鲜 seed 上按窗口顺序重新 execute / 重跑 OQL | **35/35 复现**（裁决、命中规则、行数全部一致）。`--mode preview`（每条独立预演）有 5 条差异，全是窗口内前序写入导致的状态依赖，sequential 下消失 |
| `trajectories/2026-W43/feedback.yaml` | **待标注清单**（`status: draft`，35 条 `label: null`） | 每条列了引擎实际裁决与 CQ 期望的机器比对（9 条不一致，建议标注人优先看）；**标签由业务侧填**，填完改 `status: reviewed`，`make_real_cases.py` 在此之前拒绝落案例 |
| `cases/real/` | 空 | 等 reviewed 的反馈才会有 |
| 数据源 `sources` | 仍是约定形状 | pg-ro / ch-ro 主机不可达、环境变量未设；唯一真实可达的只有上面的 sqlite 审计库 |

引擎审计有两个口径要知道：`rules_evaluated` 只记 **violate** 的规则（pass 的不记）；guard 阶段命中 hard 即返回，不再跑写后规则，所以同一句在不同状态下命中的规则集合可以不同（这正是 preview 与 sequential 回放差异的来源）。

机器比对与 CQ 期望不一致的 9 条，给标注人的线索（不是结论）：

| trace | 口语 | CQ 期望 | 引擎实际 | 线索 |
|---|---|---|---|---|
| 0007 / 0029 / 0031 / 0040 / 0041 / 0042 | 6 句 query | 查到行 | 0 行 | 多数是 Qwen 选了没有该字段的对象或 where 口径不对（如 TAR 字段名、ReviewEvidence 多跳），属路由层；0041 / 0042 seed 里确有 AlertTemplate / HypoState 行 |
| 0008 | 给 P0012 生成方案草稿 | action(生成方案草稿) | rejected(低血糖优先抢占, R14) | P0012 昨夜有 L1 夜间事件，规则层抢占；这条 CQ 期望本身可能要改 |
| 0018 | 群里答复"二甲双胍减到一片" | rejected(D10) | rejected(R51) | guard 阶段 R51 先命中就返回了，D10 在写后规则没机会跑；拒绝得对但命中的不是期望规则 |
| 0022 | OCR 2.8 直接发危急告警 | rejected(R53) | rejected(R56) | 同上：推送告警的 guard 里 R56 排在 R53 前 |

下一步只剩业务侧的事：医师 / 健管主管 / 合规官把 `feedback.yaml` 的 35 条标完（含 ≥3 条 wrong 的真实根因）→ `python3 make_real_cases.py --window 2026-W43` 落成 `cases/real/` → `plugins/glycowise/cq/make_real_routes.py` 登记路由 → 外关卡可开。要凑 200 条，照 `utterances.*.yaml` 的样子换一批口语再跑 `record_window.py` 即可，每周一个窗口。
