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
| 4 | 2026-W45 | 7 | 1 | 0.571 | — | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | — | 0.900 | — | 2.975 | PASS | PASS | ACCEPT | AUTO/SINGLE_BACKBONE | 3d | sha256:bd9c193ff707d425 | IMPL_MISSING 转介医师（W45 0224）；Dᵢ=3 条新 CQ；八臂同判；已合入 |
| 4 | 2026-W45 | 8 | 1 | 0.571 | — | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | — | 0.900 | — | 2.975 | PASS | PASS | ACCEPT | AUTO/SINGLE_BACKBONE | 3d | sha256:bd9c193ff707d425 | IMPL_MISSING 去重与通道仲裁（W45 0233）+ R02 桩 + R36/R48；Dᵢ=5 条新 CQ；random REVISE；已合入 |
| 5 | 2026-W46 | 9 | 1 | 0.571 | — | 0.875 | 1.000 | 1.000 | 1.000 | 1.000 | — | 0.900 | — | 2.850 | PASS | PASS | ACCEPT | AUTO/SINGLE_BACKBONE | 3d | sha256:bd9c193ff707d425 | P9a 根因修法（R48 缺键放行 + handler 派生键/回退）；Dᵢ=5 real（rule 层）；七臂 ACCEPT、random REVISE；未合入 |
| 5 | 2026-W46 | 10 | 1 | 0.571 | — | 0.875 | 1.000 | 1.000 | 1.000 | 1.000 | — | 0.900 | — | 2.850 | PASS | PASS | ACCEPT | AUTO/SINGLE_BACKBONE | 3d | sha256:bd9c193ff707d425 | P9b 朴素修法（R48 缺键跳过），与 P9a 逐行相同、八臂同判 ACCEPT——判据读不到落库状态；未合入 |
| 5 | 2026-W46 | 9 | 2 | 0.571 | — | 0.875 | 1.000 | 1.000 | 1.000 | 1.000 | — | 0.900 | — | 2.850 | PASS | PASS | ACCEPT | AUTO/SINGLE_BACKBONE | 3d | sha256:6d39653388a2a45a | P9a 第 2 版 + expect_state 判据：Dᵢ 12/15（ΔT_3 +.875）；八臂 ACCEPT；未合入 |
| 5 | 2026-W46 | 10 | 2 | 0.571 | — | 0.875 | 1.000 | 1.000 | 1.000 | 1.000 | — | 0.900 | — | 2.850 | PASS | PASS | ACCEPT | AUTO/SINGLE_BACKBONE | 3d | sha256:6d39653388a2a45a | P9b + expect_state：Dᵢ 0/15（ΔT_3 0、ΔA 0），strict 靠 ΔC −0.8 过 → 3d 仍 ACCEPT；只有 1d-strict REVISE；未合入 |

> round 1 的 P2 / P3 / P4 于 2026-10-23 经用户确认合入生产（重放编辑，案例库 103 条全过）；合入后 h_i 的全库读数：T=(1,1,1,—) A=1.0 S=1.0 W_family=0.909 C=2.93。
> round 2（2026-W43，真实窗口）：P5 来自真实轨迹 0018 + reviewed 反馈归因（`attribute-report-2026-W43.md`），B 第一次是 real-only（`sets/holdout-2.yaml`，20 条 / 16 层）。h_i 在 cases/real 33 条上 78/99（D⁻ 7 = rule 1 + router 6），h' 81/99；sim 98/98 不变。P5 于同日经用户确认合入生产（`git apply proposals/P5.patch`）；合入后 h_i：real-all 81/99（剩 6 条路由层 wrong）、B-sim 294/294。
> round 3（2026-W44，第二个真实窗口）：P6 来自真实轨迹 0118 + reviewed 反馈归因（`attribute-report-2026-W44.md`），B 第一次跨窗口（`sets/holdout-3.yaml`，40 条 / 20 层，W43 19 / W44 21）。h_i 在 cases/real 82 条上 207/246（D⁻ 13 = rule 1 + router 12），h' 210/246；sim 98/98（选择器加采样间隔后重生成）。P5 在 B_3 上按协议判回退：pre-P5 A .75 → post-P5 .825，无回退、泄漏机制在 W44 复现并被修（r16/r18）。P6 于同日经用户确认合入生产（`git apply proposals/P6.patch`）；合入后 h_i：real-all 210/246（剩 12 条路由层 wrong）、B-sim 294/294。
> round 4（2026-W45，第三个真实窗口，75 句仿真变体口语）：cases/real 累计 140，h_i 351/420（D⁻ 23 全是路由层：多挂一跳 12 / 相对时间 6 / 枚举 4 / 其它 5，三窗口稳定复现）；**规则层 D⁻ = 0，本轮无提案**（`attribute-report-2026-W45.md`）。B_4 = `holdout-4.yaml`（40 / 20 层，W43 7 / W44 12 / W45 21）。P6 在 B_4 上按协议判回退：pre-P6 A .825 → post .85，无回退（唯一差异是 P6 自己的 Dᵢ 被抽进 B_4）。非轨迹暴露两个只有桩的动作（转介医师 / 去重与通道仲裁，IMPL_MISSING）→ 补 CQ 口语作 Dᵢ、沙箱补实现，P7 / P8 走双关卡均 ACCEPT（P8 random REVISE），同日合入生产（重放后 real-all / B-sim / Dᵢ 与沙箱逐行相同）。
> round 5（2026-W46，第四个窗口，80 句补薄 family + irrelevant_field 变体）：cases/real 累计 203，h_i 474/609（D⁻ 45：W46 新增 22 = rule 5 / router 14 / seed 5 − 2 过）；**规则层 D⁻ 第一次非零**，落在刚合入的 P8 R48 上 → P9a 根因 / P9b 朴素两份修法同走双关卡：Dᵢ、B_5、B-sim、real-all 两份逐行相同，P9a 七臂 ACCEPT + random REVISE，P9b 八臂 ACCEPT——朴素修法把重复读数当新读数入库，判据（commit / 规则名）读不到落库状态，W_evid 未实现。arms r1–5：9 提案 regress 全 0。两份都未合入。同日 runner 加 `expect_state`（落库状态断言）重判：Dᵢ 上 P9a 12/15、P9b 0/15 分开了，但 3d 仍接受 P9b——strict 项被 ΔC −0.8 单独满足（steps 把违规数计成本），只有 1d-strict 拒。attempt 1 的 verdict 移到 `verdicts/attempt1-pre-state/`（`attribute-report-2026-W46.md` §4、`proposals/P9.md`）。

## 拒绝签名表（归因前必查；命中者不得重复提议）

| round | proposal | deficit_type | elements | regressed_axis | regressed_family | reason |
|-------|----------|--------------|----------|----------------|------------------|--------|

## 留出集记录

| round | file | size | strata | thin |
|-------|------|------|--------|------|
| 5 | holdout-5.yaml | 40 | 20 | no |
| 4 | holdout-4.yaml | 40 | 20 | no |
| 3 | holdout-3.yaml | 40 | 20 | no |
| 2 | holdout-2.yaml | 20 | 16 | no |
