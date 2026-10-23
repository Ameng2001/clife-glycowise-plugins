# 归因报告 — glycowise · 窗口 2026-W44（round 3）

输入：`trajectories/2026-W44/audit.jsonl`（51 条引擎审计轨迹，61 句口语，真 Qwen 路由）+ `feedback.yaml`（status reviewed，reviewer Ameng2001 / 本体负责人，2026-10-23；标签采纳自 `feedback.expert-draft.yaml` 51 条建议，逐条确认）。
产出：`cases/real/` 新增 49 条（W44 correct 40 + wrong 9；partial 2 条只计成本）→ 累计 **82 条**（W43 33 + W44 49）；`sets/real-all.yaml`（82）、`sets/real-W44.yaml`（49）、`sets/P6-Di.yaml`、`sets/holdout-3.yaml`（第一次跨窗口）；提案 `studio/changes/glycowise/proposals/P6.md` + `P6.patch`。
生产本体 h_i：clife-glycowise-plugins `feat/glycowise-fde-fill`（P2–P5 已合入），引擎 clife-onto-engine main 44d8ce1。路由 manual（真实案例自带窗口当时的意图），repeat 3。

## 1. 反馈 → 案例

| 标签 | 条数 | 落案例 | 说明 |
|---|---|---|---|
| correct | 40 | 40 | expect = 引擎实际裁决 |
| wrong | 9 | 9 | expect = truth_expect；rule 层 1（0118）、router 层 8 |
| partial | 2 | 0 | router 1 + rule 1，只计成本 |

案例生成这轮修了一个会毁数据的 bug：`make_real_cases.py` 给 id 编号的正则不认 `-rNN`，第二个窗口的案例把 W43 的 28 条覆盖掉了；从 git 恢复后改正则重生成，82 条 id 唯一。

## 2. h_i 基线与 D⁺ / D⁻

h_i 在 82 条 × 3 run 上：**207/246**（69/82 案例全过；13 条失败 ×3 稳定，S_consist = S_stable = 1.0）。13 条 = W43 遗留的路由层 6 条 + W44 7 条。W44 的 9 条 wrong 里有 2 条在 h_i 上「通过」：0105（aggregate 不分组返回一行 `{count: 0}`，pass 判据只看有行）、0117（expect 的 query 期望太粗）——说明 pass 判据对路由层错误的灵敏度有限，它们留在库里不计 D⁻。

| D⁻ 案例 | 轨迹 | layer | 现象 | 归因 |
|---|---|---|---|---|
| 低血糖安全-r10 | 0118 | **rule** | R04a 不响、动作 committed；truth rejected(R04a) | **P6**：`_prev_reading` 不看采样间隔，2h15m 前的 2.2 被当成连续确认 |
| 因果链溯源-r01 | 0115 | router | query 0 行 | 「叫不醒」在 SymptomTreatmentRecord 上，Qwen 选了 AlertEvent |
| 指标口径-r14 | 0119 | router | rejected(R56) | 口语「（中级）」被原样传成 level='中级'，覆盖告警自身级别「中」，模板查不到 |
| 因果链溯源-r02 | 0121 | router | query 0 行 | 多挂一跳 triggered_by_reading，seed 无链接实例 |
| 指标口径-r17 | 0124 | router | query 0 行 | 多挂一跳 computed_from |
| 指标口径-r21 | 0138 | router | query 0 行 | `'now-14d'` 字面量（与 W43 0029/0040 同因，第三次出现） |
| 出口签发闸-r05 | 0154 | router | query 0 行 | 多挂一跳 requires_credential |
| W43 遗留 6 条 | 0007/0029/0031/0040/0041/0042 | router | query 0 行 | 见 `attribute-report-2026-W43.md` |

路由层 12 条仍**不归本体**，记平台 backlog；三类重复出现（相对时间字面量 ×3、多挂一跳 ×6、枚举值字面量 ×2），跨两个窗口稳定复现，是 clife-onto-engine 能力清单 / OQL 的问题而不是本体 IR 的问题。

## 3. P5 在下一轮留出集 B_3 上的回退（论文 P-A 协议）

`sets/holdout-3.yaml` 是 round 3 的 B，对 round 2 的 P5 就是 B_{r+1}。把生产 `_fde.py` 反向打 `P5.patch` 得 pre-P5 沙箱，在 B_3 上读数：

| 状态 | A | T_1 | T_3 | T_4 | 失败案例 |
|---|---|---|---|---|---|
| pre-P5（h_i 当时） | 0.750 | 0.5 | 0.9375 | 0.8 | 路由层 7 + 指标口径-r03（Dᵢ，R51 假阳性）+ **指标口径-r16 / r18**（W44 两条 correct 的 HIL 答复，被 0113 落库证据包里的「分层」字样经 R51 误拒）|
| post-P5（现生产） | 0.825 | 0.5 | 1.0 | 1.0 | 路由层 7 |

P5 在它从没见过的窗口上**没有回退，且多修了两条**：泄漏机制在 W44 复现（0113 → 0123/0128），B_{i+1} 第一次有了判回退的意义。`arm_compare.py` 对 P5 用 `readings/P5-{hi,hp}-B3.json` 判 regress（basis next_round），其余 4 条提案仍是同轮 B → `REGRESS_MIXED_B`。

## 4. 提案与裁决

| 提案 | 编辑 | Dᵢ | 内关卡 3d | 外关卡（B = real 40 / 20 层，跨窗口） | 3d 裁决 | 对照臂 |
|---|---|---|---|---|---|---|
| P6 | 实时告警「前一读数」要求间隔 ≤20 min（`_prev_sample`） | 低血糖安全-r10（1 条，9 句） | ΔT_3 +1.0 · ΔW_family +1.0 · ΔA +1.0 · ΔC +1.0（带宽内） | 全 0（A 两臂 0.825） | **ACCEPT** | 八臂同判 ACCEPT（random p=0.6 seed 0 也接受） |

沙箱 h' 其余证据：真实库全集 210/246（只多过 r10）；仿真库 B-sim 98/98；51 条窗口顺序回放里只有 0118 本身改判，其后 31 条带它作 `setup` 前缀的案例标 `SETUP_DIVERGED`（候选拒绝了前缀步，runner 跳过并照判），裁决无一变化。

**已合入生产**（2026-10-23 用户确认后 `git apply P6.patch`）：重跑 real-all 210/246（剩 12 条路由层 wrong）、B-sim 294/294（×3），与沙箱一致。结果文件 `results/real.h_i.post-P6.jsonl`、`results/sim.h_i.post-P6.jsonl`。

## 5. 这轮暴露的方法问题

1. **sim 标签可被 real 反馈推翻**：`cases/sim/低血糖安全-01` 由选择器从旧实现反推、挑中了与 0118 同一条读数作「R04a 通过」，h' 上 97/98。真实标签优先，选择器加同样的间隔条件后改选同序列读数，98/98。sim 库里从实现反推的标签在 real 到来前是不可证伪的，这是 B 必须 real-only 的又一条理由。
2. **`setup` 前缀的语义**：候选 h' 拒绝了某个前缀步时，不能判 SETUP_FAILED（会把一整批案例变成不可判）；runner 改为跳过并打 `SETUP_DIVERGED:<i>:<action>`，照常评判——状态与窗口略有差异，但 31 条无一改判。
3. **留出集的 time_half 退化**：两个窗口都是 2026-10-23 录的（W44 只是逻辑窗口号），`observed_at` 同日，family × tier × time_half 的 20 层实际只有 family × tier。跨窗口是真的（W43 19 / W44 21），跨时间不是。
4. **pass 判据对路由层错误不敏感**：0105 / 0117 两条 wrong 在 h_i 上通过。
5. **Dᵢ 仍是 1 条、提案流仍是 1 份/轮**；八臂同判说明 P6 仍是闸门没机会拒的明牌。区分力要等有争议的提案。
