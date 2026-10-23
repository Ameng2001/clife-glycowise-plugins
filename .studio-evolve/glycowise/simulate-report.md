# 仿真案例：glycowise

**状态：UNGROUNDED**（`studio/changes/glycowise/ontology-map.md` 无 §8 Evidence，未跑 `/studio-evolve:ground`）。实参全部取自 `plugins/glycowise/_fde.py` 的 seed（患者 P0007/P0012/P0031/P0045/P0088/P0023/P0099、读数 r-P0045-00969 等、汇总 s-*-14d、凭证 cred-*、模板 tpl-*），不是从真实数据采样；标签可信度按 skill 口径降级。生成日 2026-10-23。

```
仿真案例：glycowise
新增 70 条（tier 1/2/3/4 = 23/10/37/0；family 数 10）· 变体 177 个 · 去重丢弃 3（R53 / R44 / C16+发布宣传素材 已被 golden-23/26 覆盖，计入 SKIPPED）· SKIPPED(FDE TODO / seed 不可达) 19
专家抽检：抽 46 条（63%，超 10%），不符 7 条 → 改标签 1、改措辞 3、删 3（原因见下）
案例库现状：real 0 · sim 70（另有 golden 28 条以 golden-* 复制在 cases/sim/ 供同一跑批使用）
提醒：sim 只进内关卡。
下一步：/studio-evolve:cycle glycowise（需先补 ground 与真实轨迹反馈）
```

## 生成器与派生规则

- 生成器：`plugins/glycowise/cq/make_sim_cases.py`（`--out-cases .studio-evolve/glycowise/cases/sim --out-routes cq/sim_routes.json`），可重跑；动态案例（R04a 拒绝/通过分支的读数）在加载 seed 后解析。
- 派生口径（skill Workflow 1）：hard rule → `rejected(R)` tier 3；action → `action(X)` tier 3；root_cause 链 → `query` tier 2（seed 未 `put_link`，多跳降为单起点 where）；function/指标口径 → `query` tier 1。
- 上限按 `config.yaml`：每规则 2、每动作 2、每关系 1、每函数 1；变体每条 2–3 个（paraphrase / entity_swap / irrelevant_field），与原题共用标签。
- 去重：与 `cq/golden.yaml` 按 `expect + 涉及元素` 比对。
- 路由：manual（oracle），247 条写入 `cq/sim_routes.json`；`cq/all_routes.json` = golden 51 + sim 247（无键冲突）。

## tier × family 分布（sim 70）

| family | tier 1 | tier 2 | tier 3 | 合计 |
|---|---|---|---|---|
| 指标口径 | 12 | | | 12 |
| 参考与配置 | 11 | | | 11 |
| 因果链溯源 | | 10 | | 10 |
| 低血糖安全 | | | 10 | 10 |
| 结论层与分层 | | | 8 | 8 |
| 出口签发闸 | | | 7 | 7 |
| 产品与机构合规 | | | 5 | 5 |
| 高血糖与波动 | | | 3 | 3 |
| 缓解路径 | | | 2 | 2 |
| 数据与同意合规 | | | 2 | 2 |
| **合计** | 23 | 10 | 37 | **70** |

tier 4（HIL）为 0：seed 可达的动作里没有带复核闸的实现。

## 专家抽检（diabetes-cgm 领域专家，Agent 调用）

抽 46 条，39 条符合现实口径，7 条不符：

| 案例 | 判定 | 处置 |
|---|---|---|
| 指标口径-01 | 标签写 tar_l2 ≈0，seed 重算为 3.1 | 改标签 |
| 低血糖安全-02（P0045 2.6、前值 3.0 → rejected R03a） | 两读数已连续 <3.9，IAH 高危磺脲使用者必须触发（降级 R04a「中」），引擎整体拒绝与临床相反 | **删**，记实现缺口候选 |
| 低血糖安全-09（P0012 夜低阈值放宽到 3.5） | 两晚前有夜间 L2，临床不现实 | 改措辞：P0007 日高阈值 10.0→13.9 |
| 出口签发闸-03（c-promo-01 → rejected C22） | 首要违规是 C16 而非缺免责声明；C16 已被 golden-26 覆盖 | **删**（去重） |
| 数据与同意合规-02（无序号用厂商 ID → rejected R48） | 无序号应走 weak_dedup 兜底而非拒收 | 改措辞：有序号却坚持用厂商 ID |
| 结论层与分层-06（「建议您去医院开处方调整」→ rejected C19） | 属异常转介，健管师允许；C19 关键词正则误拒 | 改措辞：「我来给您诊断一下」；原句记实现缺口候选 |
| 高血糖与波动-04（P0099 → rejected R49） | R49 语义是按最保守参数继续执行并置 stale，不是拒绝 | **删**，记实现缺口候选 |

未阻断备注 3 条：低血糖安全-01 前值由 params 动态取；低血糖安全-08 的 L2 事件约 45h 前；高血糖与波动-01「维持」方向合法但临床更倾向去强化。

**实现缺口候选（不在本任务改规则实现，交 attribute/verify）**：R03a 未确认时应降级触发而非拒绝；R05 应只在 g≥3.9 时评估「预测」证据；R49 应保守执行而非拒绝；C19 关键词「处方」过宽，误拦异常转介。

## 验证读数（h_i = 当前 main，runner onto-engine，manual 路由，repeat 3，角色 医师）

| 集合 | 案例 | 行 | T_1/T_2/T_3 | A | S_consist | S_stable | W_evid | W_family | C(steps) |
|---|---|---|---|---|---|---|---|---|---|
| sim-only | 70 | 741 | 1.00 / 1.00 / 1.00 | 1.000 | 1.000 | 1.000 | — | 0.800 | 2.97 |
| sim + golden | 98 | 894 | 1.00 / 1.00 / 1.00 | 1.000 | 1.000 | 1.000 | — | 0.818 | 2.99 |

- 原题 + 变体 294 条 ×3 次全部可判、全部通过；不可判 0。
- A = 1.0 是 manual 路由（oracle）的结果，量的是引擎/规则对标签的符合度，不是 LLM 路由能力；LLM 路由的 A 见 `cq/README.md` 的 live 读数（19/28、20/28）。
- S_consist / S_stable 首次可测（repeat 3 + 177 变体）。
- W_family 0.8：指标口径、参考与配置两族只有 tier 1 案例，按定义不计入；补 tier≥2 需要 `put_link` 后的多跳查询。
- W_evid 不可计算（UNGROUNDED）。
- 文件：`results.sim.jsonl`、`readings/h_i-all.json`、`readings/h_i-sim-only.json`、`sim-only.yaml`（案例 id 列表，放在 cases/ 之外以免被 runner 当案例读）。

## SKIPPED(FDE TODO / seed 不可达) 19 项

见 `make_sim_cases.py` 的 `SKIPPED` 列表（R42/R37/R27 无对应 ContextEvent；R11 无 >16.7 读数；R34 复发窗已过；R57 需跨次累计；C15 非声明参数；C1 词表不可见；D13 为 soft；D10 无含剂量内容；D11a 无 signer 参数；R17/R33 seed 无信号；多跳需 put_link；45 个动作 / 17 条规则仍为 NotImplementedError；R53/R44/C16 被 golden 覆盖；R03a 通过分支受 R05 实现制约）。
