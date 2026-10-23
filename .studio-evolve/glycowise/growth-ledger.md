# Growth Ledger — glycowise

> 每轮裁决一行。阈值见 `config.yaml`（β=0.05，window=20，骨干=[default]）。
> MANUAL 与 AUTO 的读数不混比；改阈值要开新账本。`exec` 由 `scripts/gate_decide.py` 写为 `AUTO/{SINGLE_BACKBONE|PANEL}`，`script_hash` 是三个脚本的联合哈希，`gate_mode` 是裁决用的判定模式（3d 为正式；其余是论文对照臂）。

## 读数

| round | window | proposal | attempt | T_1 | T_2 | T_3 | T_4 | S_consist | S_holdout | S_stable | W_evid | W_family | W_elem | C_tok | inner | outer | verdict | exec | gate_mode | script_hash | notes |
|-------|--------|----------|---------|-----|-----|-----|-----|-----------|-----------|----------|--------|----------|--------|-------|-------|-------|---------|------|-----------|-------------|-------|
| 0 | — | baseline | — | | | | | | — | | | | | | — | — | — | | — | | 冷启动基线（v0 编译后、未进化） |
| 1 | pilot-sim·OUTER=SIM_ONLY | 2 | 1 | 1.000 | 1.000 | 1.000 | — | 1.000 | 1.000 | 1.000 | — | 0.818 | — | 2.969 | PASS | PASS | ACCEPT | AUTO/SINGLE_BACKBONE | 3d | sha256:95b29afdbbb39bd2 |  |
| 1 | pilot-sim·OUTER=SIM_ONLY | 3 | 1 | 1.000 | 1.000 | 1.000 | — | 1.000 | 1.000 | 1.000 | — | 0.818 | — | 2.990 | PASS | PASS | ACCEPT | AUTO/SINGLE_BACKBONE | 3d | sha256:95b29afdbbb39bd2 |  |
| 1 | pilot-sim·OUTER=SIM_ONLY | 4 | 1 | 1.000 | 1.000 | 1.000 | — | 1.000 | 1.000 | 1.000 | — | 0.818 | — | 2.990 | PASS | PASS | ACCEPT | AUTO/SINGLE_BACKBONE | 3d | sha256:95b29afdbbb39bd2 |  |
| 2 | 2026-W43 | 5 | 1 | 0.250 | — | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | — | 0.889 | — | 2.950 | PASS | PASS | ACCEPT | AUTO/SINGLE_BACKBONE | 3d | sha256:53025530d1b92ced | Dᵢ=指标口径-r03（real）；B real-only 20；random 臂 REVISE，其余 6 臂同判 |
| 3 | 2026-W44 | 6 | 1 | 0.500 | — | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | — | 0.900 | — | 3.100 | PASS | PASS | ACCEPT | AUTO/SINGLE_BACKBONE | 3d | sha256:0e75946ece4c5597 | Dᵢ=低血糖安全-r10（real）；B real-only 40 / 20 层，跨窗口 W43+W44；八臂同判 ACCEPT；同日确认合入生产（real-all 210/246、B-sim 294/294） |

> round 1 的 P2 / P3 / P4 于 2026-10-23 经用户确认合入生产（重放编辑，案例库 103 条全过）；合入后 h_i 的全库读数：T=(1,1,1,—) A=1.0 S=1.0 W_family=0.909 C=2.93。
> round 2（2026-W43，真实窗口）：P5 来自真实轨迹 0018 + reviewed 反馈归因（`attribute-report-2026-W43.md`），B 第一次是 real-only（`sets/holdout-2.yaml`，20 条 / 16 层）。h_i 在 cases/real 33 条上 78/99（D⁻ 7 = rule 1 + router 6），h' 81/99；sim 98/98 不变。P5 于同日经用户确认合入生产（`git apply proposals/P5.patch`）；合入后 h_i：real-all 81/99（剩 6 条路由层 wrong）、B-sim 294/294。
> round 3（2026-W44，第二个真实窗口）：P6 来自真实轨迹 0118 + reviewed 反馈归因（`attribute-report-2026-W44.md`），B 第一次跨窗口（`sets/holdout-3.yaml`，40 条 / 20 层，W43 19 / W44 21）。h_i 在 cases/real 82 条上 207/246（D⁻ 13 = rule 1 + router 12），h' 210/246；sim 98/98（选择器加采样间隔后重生成）。P5 在 B_3 上按协议判回退：pre-P5 A .75 → post-P5 .825，无回退、泄漏机制在 W44 复现并被修（r16/r18）。P6 于同日经用户确认合入生产（`git apply proposals/P6.patch`）；合入后 h_i：real-all 210/246（剩 12 条路由层 wrong）、B-sim 294/294。

## 拒绝签名表（归因前必查；命中者不得重复提议）

| round | proposal | deficit_type | elements | regressed_axis | regressed_family | reason |
|-------|----------|--------------|----------|----------------|------------------|--------|

## 留出集记录

| round | file | size | strata | thin |
|-------|------|------|--------|------|
| 3 | holdout-3.yaml | 40 | 20 | no |
| 2 | holdout-2.yaml | 20 | 16 | no |
