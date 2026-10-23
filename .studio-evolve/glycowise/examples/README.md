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
| `trajectories/2026-W44/audit.jsonl` | ① 一个完整的最小可开工窗口：20 条轨迹（17 execute：committed 8 · rejected 7 · pending_hil 2；3 ask），覆盖 10 个 family |
| `trajectories/2026-W44/feedback.yaml` | ② 这 20 条的标签：correct 14（含 7 条「拒绝得对」）/ wrong 4 / partial 2，三位标签人可追溯 |
| `cases/real/*.yaml` | ②' 由 ①+② 自动落成的 18 条真实案例（partial 不落） |
| `make_real_cases.py` | ①+② → ②' 的样例实现（幂等，按 family 顺延编号），`python3 make_real_cases.py --dry-run` 先看 |
| `config.sources.yaml` | ③ 只读数据源 `sources` 段 + 审计导出约定，贴进 `../config.yaml` |
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
