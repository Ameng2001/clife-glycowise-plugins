# 归因报告 — glycowise · 窗口 2026-W43（round 2）

输入：`trajectories/2026-W43/audit.jsonl`（35 条引擎审计轨迹：execute 24 / ask 11）+ `feedback.yaml`（status reviewed，reviewer Ameng2001 / 本体负责人，2026-10-23；标签来自 `feedback.expert-draft.yaml` 的 35 条建议，逐条采纳）。
产出：`cases/real/` 33 条（partial 2 条只计成本不落案例）、`sets/real-all.yaml`、`sets/P5-Di.yaml`、`sets/holdout-2.yaml`、提案 `studio/changes/glycowise/proposals/P5.md` + `P5.patch`。
生产本体 h_i：clife-glycowise-plugins `feat/glycowise-fde-fill`（P2–P4 已合入），引擎 clife-onto-engine main 44d8ce1。路由 manual（真实案例自带窗口当时的意图），repeat 3。

## 1. 反馈 → 案例

| 标签 | 条数 | 落案例 | 说明 |
|---|---|---|---|
| correct | 26 | 26 | expect = 引擎实际裁决 |
| wrong | 7 | 7 | expect = truth_expect；rule 层 1 条另带 `expect_not`（业务侧裁定的假阳性规则） |
| partial | 2 | 0 | 0002（OQL 没带时间窗，13 行是 14 夜全部）、0006（aggregate 不分组）——只计成本 |

案例生成规则这轮新增两项，都是接真实数据才暴露的：
- **`setup`（状态前置）**：同窗口里该轨迹之前所有落库（committed / pending_hil）的 execute 按序进案例，runner 对这类案例单独起新鲜 seed 先真 execute 再评判。没有它，0008 / 0021 / 0022 三条 correct 案例在新鲜 seed 上判错（裁决依赖前序写入），0018 的泄漏也复现不了。
- **`route`（案例自带意图）**：同一句口语在 golden 录制里的参数与窗口里真走的不同（0008 的 direction=强化 是 Qwen 补的、0021 的 level=紧急、0022 的 level=critical），共享录制按口语键会让 golden 覆盖真实——真实案例以窗口为准。

## 2. h_i 基线与 D⁺ / D⁻ 划分

h_i 在 33 条 × 3 run 上：**78/99**（26/33 案例全过；失败 7 条 ×3 稳定，S_consist = S_stable = 1.0）。D⁻ 恰为 7 条 wrong 标签案例，D⁺ 为 26 条 correct。

| D⁻ 案例 | 轨迹 | layer | 现象 | 归因 |
|---|---|---|---|---|
| 指标口径-r03 | 0018 | **rule** | rejected 命中 R51 + D10 + C6；`expect_not: [R51]` 命中 | **P5**：`_staged: True` 持久化标记让 R51 读到 0011 落库的证据包正文（跨动作、跨患者） |
| 出口签发闸-r01 | 0007 | router | query 0 行 | Qwen 在 ReviewEvidence 上多挂一跳 supersedes（链两端都不是它），seed 无链接实例 |
| 指标口径-r04 | 0029 | router | query 0 行 | where `window_end >= 'now-14d'` 字面字符串，引擎不解析相对时间 |
| 指标口径-r05 | 0031 | router | query 0 行 | device_time 区间年份写成 2023 |
| 指标口径-r06 | 0040 | router | query 0 行 | 同 0029（`'now-14d'`） |
| 指标口径-r07 | 0041 | router | query 0 行 | where `level == 'critical'`，模板库级别是中文「危急」 |
| 指标口径-r08 | 0042 | router | query 0 行 | 从 HypoState 多跳 gates_alert_closure，seed 无链接实例；单跳即可答 |

路由层 6 条**不归本体**：都是 LLM 把意图编译错（相对时间字面量 2、多挂一跳 2、年份 1、枚举值英文化 1），引擎按错 OQL 如实返回 0 行。它们不是 IR 元素缺失——`now-14d` 要引擎 OQL 支持相对时间或编译器改写；`critical`→「危急」要把属性的允许值暴露进能力清单，而 `PropertySpec` 目前没有枚举值字段。两项都记为**平台 backlog**（clife-onto-engine），不开本体提案。这 6 条留在 `cases/real` 里（两臂同败，不影响 Δ），留出集也不排除它们。

D⁺ 26 条共性（ρ≥0.6 的高频元素）：推送告警 / 群内答复患者 / 生成方案草稿 三个动作各 ≥3 条，告警族规则 R52/R53/R56/R58 在 5 条 rejected 里成对出现——都是本轮**守住了**的面，不提议改。

## 3. 提案与裁决

| 提案 | 编辑 | Dᵢ | 内关卡 3d | 外关卡（B = real 20 / 16 层） | 3d 裁决 | 对照臂 |
|---|---|---|---|---|---|---|
| P5 | 暂存标记 `_staged: True` → 按执行令牌；规则只认本次暂存行 | 指标口径-r03（1 条，6 句） | ΔT_3 +1.0 · ΔW_family +1.0 · ΔA +1.0 · ΔC −1.0 | 全 0，ΔC −0.05 | **ACCEPT** | 3d-noT/noS/noW、1d、1d-strict、none 同判 ACCEPT；random REVISE |

沙箱 h' 其余证据：真实库全集 81/99（只多过 r03）；仿真库 B-sim 98/98 不变；窗口 35 条顺序回放 32 条裁决不变、3 条变化全是同一机制归位（0015 R51 假阳性消失、0016 C22 不再被泄漏正文里的免责声明蒙过、0018 即 Dᵢ），三条案例的 expect 规则都仍命中。

**未合入生产**。合入由人确认后 `git apply studio/changes/glycowise/proposals/P5.patch`，再重跑 `sets/real-all.yaml` 与 `sets/B-sim.yaml` 确认。

## 4. 这轮暴露的方法问题（进论文「诚实边界」）

1. **逐案例、新鲜 seed 的验证对状态依赖缺陷是盲的**：没有 `setup` 前，0018 在 h_i 上就「通过」（D10 也命中，pass 判据只看期望规则是否在列）。真实窗口的裁决三成以上依赖前序写入（35 条里 5 条 preview 不一致 + 2 条泄漏），仿真库 0 条——这是 sim 与 real 的本质差异之一。
2. **pass 判据对「多响了一条规则」不敏感**：rejected(X) 只要 X 在列就过，假阳性规则藏在旁边。`expect_not` 由业务侧反馈给出，不是从引擎输出反推。
3. **留出集 20 条全来自同一天同一窗口**（time_half 分层退化成同日前后半），不 thin 只是数量判据；跨窗口的 B 要等 W44+。
4. **Dᵢ 仍是 1 条**，内关卡 ΔT_3 = +1.0 是构造使然；但这是第一份来自真实轨迹 + 业务反馈归因、而非专家抽检倒推的提案，且 B 第一次是 real-only。
