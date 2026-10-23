# 正式 run 需要准备的三类数据 —— 样例

本目录全部是**样例**（患者 id 与数值沿用演示租户 seed，非真实数据），给业务侧照着准备。三类数据分别喂给 evolve 管线的三个入口，缺一类对应的读数就算不出。

| 数据 | 喂给 | 产出 | 判据要求（criteria.yaml） |
|---|---|---|---|
| ① 引擎审计日志（轨迹） | `evolve-attribute`（`config.yaml: trajectory_source`） | 提案流；与 ② 一起落成 `cases/real/` | 15 轮 × 每轮 ≥ 6 条提案 → 每轮窗口 ≥ 20 条有反馈的轨迹 |
| ② 反馈标签 | `evolve-attribute`（`trajectories/{window}/feedback.yaml`） | `cases/real/*.yaml`（外关卡留出集唯一来源） | real 池 ≥ 200 条，family × tier × time_half 每层 ≥ 16 |
| ③ 只读数据源 | `evolve-ground`（`config.yaml: sources` + IR §6 Mapping） | IR §8 Evidence → W_evid 可测 | 每个对象 / 映射 / function 规则一条探测采样 |

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
- 标签人要可追溯（`reviewer`），进台账的 contamination_note。
- 标签是私有的，永远不进提示词。

## ②' 落成的真实案例：`cases/real/高血糖与波动-01.yaml`

attribute 第 1 步自动从 ①+② 生成，不用手写；这里给出样子是为了让业务侧知道反馈最终会变成什么。family 取流程决策点名，要和仿真案例库的 10 个 family 对得上（指标口径 / 参考与配置 / 因果链溯源 / 低血糖安全 / 高血糖与波动 / 结论层与分层 / 缓解路径 / 出口签发闸 / 产品与机构合规 / 数据与同意合规），tier 按 query=1、多跳=2、action/rejected=3、HIL=4。

## ③ 数据源：`config.yaml` 的 `sources` 段

```yaml
sources:
  - store: postgres            # IR §6 Mapping Hints 里每个 store 一条
    dsn: "postgresql://ro_user@db.internal:5432/glycowise"   # 只读账号；密码走环境变量，不写文件
    schema: cgm
  - store: clickhouse
    dsn: "clickhouse://ro_user@olap.internal:9000/glycowise_metrics"
```

evolve-ground 对 IR §6 每一行（`store / table / key / columns`）跑 `SELECT … LIMIT 20` 取样写进 §8；要求：只读账号、脱敏视图（患者 id 已假名化）、能从跑管线的机器直连。当前 IR §6 的 table / columns 若与库里不一致会标 `mismatch`，这本身就是正式 run 前要清的债。

## 最小可开工包

1. 一个窗口（20 条有反馈的轨迹，含 ≥ 3 条 wrong）→ 能把 attribute → verify 整段跑一轮，验证接法。
2. 累计 ≥ 200 条有反馈轨迹、8 个分层各 ≥ 16 → 正式 run 的 real 池门槛。
3. 只读数据源 → W_evid 可测。
