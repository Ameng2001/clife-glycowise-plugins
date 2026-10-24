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
| 5 | 2026-W46 | 9 | 3 | 0.571 | — | 0.875 | 1.000 | 1.000 | 1.000 | 1.000 | — | 0.900 | — | 2.850 | PASS | PASS | ACCEPT | AUTO/SINGLE_BACKBONE | 3d | sha256:cc1e4b90a1eda661 | P9a 第 2 版，v3 判定式（strict 不计 ΔC）：读数同 attempt 2；八臂 ACCEPT；2026-10-24 round 6 用户确认合入（B_6 重判 3d ACCEPT、regress 0；post-P9a h_i B_6 .900 / real-all .816） |
| 5 | 2026-W46 | 10 | 3 | 0.571 | — | 0.875 | 1.000 | 1.000 | 1.000 | 1.000 | — | 0.900 | — | 2.850 | FAIL | PASS | REJECT | AUTO/SINGLE_BACKBONE | 3d | sha256:cc1e4b90a1eda661 | P9b，v3 判定式：3d 族四臂 REJECT（T/S/W 无改善），1d ACCEPT、1d-strict REJECT——第一个分歧集；B_5 对其写错盲（regress 0）；未合入 |
| 5 | 2026-W46 | 9 | 4 | 0.571 | — | 0.875 | 1.000 | 1.000 | 1.000 | 1.000 | — | 0.900 | — | 2.850 | PASS | PASS | ACCEPT | AUTO/SINGLE_BACKBONE | 3d | sha256:bc2c318b53068be5 | | P9a 第 2 版，attempt 4：B_5 写类案例全带 expect_state 后重跑（h_i 90/120、h' 96/120 与 attempt 3 相同），八臂 ACCEPT 不变；real-all 501/609、0 回退 |
| 5 | 2026-W46 | 10 | 4 | 0.571 | — | 0.875 | 1.000 | 1.000 | 1.000 | 1.000 | — | 0.900 | — | 2.850 | FAIL | PASS | REJECT | AUTO/SINGLE_BACKBONE | 3d | sha256:bc2c318b53068be5 | | P9b 朴素修法，attempt 4：B_5 带 expect_state 重跑读数不变，3d 族 REJECT / 1d ACCEPT 同 attempt 3；B_5 与 real-all 对 h_i 仍 0 回退——它写错的 dup 案例在 h_i 上本来就不过（拒绝 vs 错写，同为失败），regress 口径看不见 |
| 5 | 2026-W46 | 11 | 1 | 0.571 | — | 0.812 | 1.000 | 1.000 | 1.000 | 1.000 | — | 0.900 | — | 2.825 | FAIL | PASS | REVISE | AUTO/SINGLE_BACKBONE | 3d | sha256:bc2c318b53068be5 | | P9c 朴素修法（amend §5「删命中的规则分支」：R48 拒绝分支整段删除）：Dᵢ 0/15（无键重复仍错写），B_5 90→93/120（r73/r74 修对、数据与同意合规-r08 由对变错），real-all 471→465（+3 −5），sim 294→291；3d 族 REVISE（无严格改善）、1d ACCEPT、1d-strict REVISE；B_5 净 A +0.025 → arm_compare regress 0——净口径盖住了单条回退 |
| 6 | 2026-W47 | 12 | 1 | 0.571 | — | 0.750 | 1.000 | 1.000 | 1.000 | 1.000 | — | 0.900 | — | 2.900 | PASS | PASS | ACCEPT | AUTO/SINGLE_BACKBONE | 3d | sha256:11a7a4c24504c27a |  |
| 6 | 2026-W47 | 13 | 1 | 0.571 | — | 0.750 | 1.000 | 1.000 | 1.000 | 1.000 | — | 0.900 | — | 2.900 | PASS | PASS | ACCEPT | AUTO/SINGLE_BACKBONE | 3d | sha256:11a7a4c24504c27a |  |
| 6 | 2026-W48 | 14 | 1 | 0.571 | — | 0.750 | 1.000 | 1.000 | 1.000 | 1.000 | — | 0.900 | — | 2.900 | PASS | PASS | ACCEPT | AUTO/SINGLE_BACKBONE | 3d | sha256:b1cf36ede8ac2674 | 已合入生产（2026-10-24 用户确认 `git apply`；post-P14 h_i 在 Dᵢ 9/9、B_5 90/120、real-all 471/609、B-sim 291/294，与沙箱逐行相同；`results/r6.h_i.post-P14.*.jsonl`） |
| 6 | 2026-W47 | 16 | 1 | 0.857 | — | 0.882 | 1.000 | 1.000 | 1.000 | 1.000 | — | 1.000 | — | 2.925 | PASS | PASS | ACCEPT | AUTO/SINGLE_BACKBONE | 3d | sha256:b1cf36ede8ac2674 | P16a 根因修 D9 功效声称（W47 0026/0027）；八臂 7 ACCEPT / random REVISE；2026-10-24 用户确认合入生产（post-P1x h_i：B_6 .900 不变、real-all .830、sim .990 不变）|
| 6 | 2026-W47 | 17 | 1 | 0.857 | — | 0.882 | 1.000 | 1.000 | 1.000 | 1.000 | — | 1.000 | — | 2.925 | PASS | PASS | ACCEPT | AUTO/SINGLE_BACKBONE | 3d | sha256:b1cf36ede8ac2674 | P16b 朴素修 D9 字面量；与 P16a 逐格相同；未合入 |
| 6 | 2026-W47 | 18 | 1 | 0.857 | — | 0.882 | 1.000 | 1.000 | 1.000 | 1.000 | — | 1.000 | — | 2.925 | PASS | PASS | ACCEPT | AUTO/SINGLE_BACKBONE | 3d | sha256:b1cf36ede8ac2674 | P17a 根因修 R44 否定句；2026-10-24 用户确认合入生产（post-P1x h_i：B_6 .900 不变、real-all .830、sim .990 不变）|
| 6 | 2026-W47 | 19 | 1 | 0.857 | — | 0.882 | 1.000 | 1.000 | 1.000 | 1.000 | — | 1.000 | — | 2.925 | PASS | PASS | ACCEPT | AUTO/SINGLE_BACKBONE | 3d | sha256:b1cf36ede8ac2674 | P17b 朴素修 R44 删「闭环」关键词；B_6/real 无回退但 sim golden-23 回退（闸门看不见）；未合入 |
| 6 | 2026-W47 | 20 | 1 | 0.857 | — | 0.882 | 1.000 | 1.000 | 1.000 | 1.000 | — | 1.000 | — | 2.925 | PASS | PASS | ACCEPT | AUTO/SINGLE_BACKBONE | 3d | sha256:b1cf36ede8ac2674 | P18a 根因修 升级告警 guard R38→R53 + handler；2026-10-24 用户确认合入生产（post-P1x h_i：B_6 .900 不变、real-all .830、sim .990 不变）|
| 6 | 2026-W47 | 21 | 1 | 0.857 | — | 0.882 | 1.000 | 1.000 | 1.000 | 1.000 | — | 1.000 | — | 2.925 | FAIL | PASS | REVISE | AUTO/SINGLE_BACKBONE | 3d | sha256:b1cf36ede8ac2674 | P18b 朴素修 R38 删分支；Dᵢ 仍 IMPL_MISSING → 带闸门臂全 REVISE，none/random ACCEPT；未合入 |
| 6 | 2026-W47 | 22 | 1 | 0.857 | — | 0.882 | 1.000 | 1.000 | 1.000 | 1.000 | — | 1.000 | — | 2.925 | PASS | PASS | ACCEPT | AUTO/SINGLE_BACKBONE | 3d | sha256:b1cf36ede8ac2674 | P19a 根因修 TIER_RE 分层口语写法；八臂同判；2026-10-24 用户确认合入生产（post-P1x h_i：B_6 .900 不变、real-all .830、sim .990 不变）|
| 6 | 2026-W47 | 23 | 1 | 0.857 | — | 0.882 | 1.000 | 1.000 | 1.000 | 1.000 | — | 1.000 | — | 2.925 | PASS | PASS | ACCEPT | AUTO/SINGLE_BACKBONE | 3d | sha256:b1cf36ede8ac2674 | P19b 朴素修 TIER_RE 字面量；与 P19a 逐格相同；八臂同判；未合入 |

> round 1 的 P2 / P3 / P4 于 2026-10-23 经用户确认合入生产（重放编辑，案例库 103 条全过）；合入后 h_i 的全库读数：T=(1,1,1,—) A=1.0 S=1.0 W_family=0.909 C=2.93。
> round 2（2026-W43，真实窗口）：P5 来自真实轨迹 0018 + reviewed 反馈归因（`attribute-report-2026-W43.md`），B 第一次是 real-only（`sets/holdout-2.yaml`，20 条 / 16 层）。h_i 在 cases/real 33 条上 78/99（D⁻ 7 = rule 1 + router 6），h' 81/99；sim 98/98 不变。P5 于同日经用户确认合入生产（`git apply proposals/P5.patch`）；合入后 h_i：real-all 81/99（剩 6 条路由层 wrong）、B-sim 294/294。
> round 3（2026-W44，第二个真实窗口）：P6 来自真实轨迹 0118 + reviewed 反馈归因（`attribute-report-2026-W44.md`），B 第一次跨窗口（`sets/holdout-3.yaml`，40 条 / 20 层，W43 19 / W44 21）。h_i 在 cases/real 82 条上 207/246（D⁻ 13 = rule 1 + router 12），h' 210/246；sim 98/98（选择器加采样间隔后重生成）。P5 在 B_3 上按协议判回退：pre-P5 A .75 → post-P5 .825，无回退、泄漏机制在 W44 复现并被修（r16/r18）。P6 于同日经用户确认合入生产（`git apply proposals/P6.patch`）；合入后 h_i：real-all 210/246（剩 12 条路由层 wrong）、B-sim 294/294。
> round 4（2026-W45，第三个真实窗口，75 句仿真变体口语）：cases/real 累计 140，h_i 351/420（D⁻ 23 全是路由层：多挂一跳 12 / 相对时间 6 / 枚举 4 / 其它 5，三窗口稳定复现）；**规则层 D⁻ = 0，本轮无提案**（`attribute-report-2026-W45.md`）。B_4 = `holdout-4.yaml`（40 / 20 层，W43 7 / W44 12 / W45 21）。P6 在 B_4 上按协议判回退：pre-P6 A .825 → post .85，无回退（唯一差异是 P6 自己的 Dᵢ 被抽进 B_4）。非轨迹暴露两个只有桩的动作（转介医师 / 去重与通道仲裁，IMPL_MISSING）→ 补 CQ 口语作 Dᵢ、沙箱补实现，P7 / P8 走双关卡均 ACCEPT（P8 random REVISE），同日合入生产（重放后 real-all / B-sim / Dᵢ 与沙箱逐行相同）。
> round 5（2026-W46，第四个窗口，80 句补薄 family + irrelevant_field 变体）：cases/real 累计 203，h_i 474/609（D⁻ 45：W46 新增 22 = rule 5 / router 14 / seed 5 − 2 过）；**规则层 D⁻ 第一次非零**，落在刚合入的 P8 R48 上 → P9a 根因 / P9b 朴素两份修法同走双关卡：Dᵢ、B_5、B-sim、real-all 两份逐行相同，P9a 七臂 ACCEPT + random REVISE，P9b 八臂 ACCEPT——朴素修法把重复读数当新读数入库，判据（commit / 规则名）读不到落库状态，W_evid 未实现。arms r1–5：9 提案 regress 全 0。两份都未合入。同日 runner 加 `expect_state`（落库状态断言）重判：Dᵢ 上 P9a 12/15、P9b 0/15 分开了，但 3d 仍接受 P9b——strict 项被 ΔC −0.8 单独满足（steps 把违规数计成本），只有 1d-strict 拒。随后 criteria amend（v3：strict 只认 T/S/W，ΔC 只做约束；待导师签字）重判：3d 族 REJECT P9b、1d 仍 ACCEPT——第一个分歧集，但 B_5 没有 dup1 案例、regress 判 0。attempt 1 / 2 的 verdict 分别在 `verdicts/attempt1-pre-state/`、`verdicts/attempt2-pre-amend/`（`attribute-report-2026-W46.md` §4、`proposals/P9.md`）。 收尾：holdout_sample 并层口径复核 real 池前置——203 ≥ 200 但 8 个 family×rest 层 <8，仍未达；其余 54 条 correct 写类案例补 expect_state（65/203），h_i real-all 474 → 471/609（`readings/h_i-real-r5-state-all.json`，A .773），唯一新失败 数据与同意合规-r02 摄入读数空写入（路由平铺 payload，归路由层）。

## 拒绝签名表（归因前必查；命中者不得重复提议）

| round | proposal | deficit_type | elements | regressed_axis | regressed_family | reason |
|-------|----------|--------------|----------|----------------|------------------|--------|

## 留出集记录

| round | file | size | strata | thin |
|-------|------|------|--------|------|
| 6 | holdout-6.yaml | 40 | 25 | no |
| 5 | holdout-5.yaml | 40 | 20 | no |
| 4 | holdout-4.yaml | 40 | 20 | no |
| 3 | holdout-3.yaml | 40 | 20 | no |
| 2 | holdout-2.yaml | 20 | 16 | no |
