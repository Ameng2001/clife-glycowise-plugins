# 归因报告 — glycowise · 窗口 2026-W45（round 4）

输入：`trajectories/2026-W45/audit.jsonl`（63 条引擎审计轨迹：execute 31 / ask 32；75 句仿真库变体口语，真 Qwen 路由）+ `feedback.yaml`（status reviewed，reviewer Ameng2001 / 本体负责人，2026-10-23；标签采纳自 `feedback.expert-draft.yaml` 63 条建议，逐条确认）。
产出：`cases/real/` 新增 58 条（correct 45 + wrong 13；partial 5 条只计成本）→ 累计 **140 条**（W43 33 + W44 49 + W45 58）；`sets/real-all.yaml`（140）、`sets/real-W45.yaml`（58）、`sets/holdout-4.yaml`（三窗口）。反馈路径本轮没有提案（§2）；提案 P7 / P8 来自非轨迹的 error 行（§3、§6）。
生产本体 h_i：clife-glycowise-plugins `feat/glycowise-fde-fill`（P2–P6 已合入），引擎 clife-onto-engine main 44d8ce1。路由 manual，repeat 3。

## 1. 反馈 → 案例

| 标签 | 条数 | 落案例 | 说明 |
|---|---|---|---|
| correct | 45 | 45 | expect = 引擎实际裁决 |
| wrong | 13 | 13 | **全部 layer router**，rule 0 |
| partial | 5 | 0 | router 4 + rule 1（0259：R49 guard-soft 违规被 execute 丢出审计，与 W44 0158 同因） |

## 2. h_i 基线与 D⁻

h_i 在 140 条 × 3 run 上：**351/420**（117/140 案例全过；23 条失败 ×3 稳定，S_consist = S_stable = 1.0）。A = 0.836，T = (0.65, —, 0.966, 1.0)。

23 条失败 = W43 遗留 6 + W44 遗留 6 + W45 11，**全是路由层 wrong**。W45 的 13 条 wrong 里 2 条在 h_i 上「通过」（0218 选错字段但 OQL 有行；0273 payload 平铺但引擎 committed——pass 判据只看裁决在列），不计 D⁻。

| 路由错误类型 | W43 | W44 | W45 | 合计 |
|---|---|---|---|---|
| 多挂一跳（seed 无链接实例 → 0 行） | 2 | 4 | 6 | 12 |
| 相对时间字面量 `'now-14d'` | 2 | 1 | 3 | 6 |
| 枚举值字面量（critical / 中级 / high / 高级） | 1 | 1 | 2 | 4 |
| 年份错 / 选错对象或字段 / payload 形态 | 1 | 2 | 2 | 5 |

三个窗口、三批不同口语（原句 → 原句 → 变体）下同一组路由错误稳定复现，且**省略式口语没有把路由错误放大**（W45 wrong 率 13/63 = 21%，W44 9/51 = 18%，W43 7/35 = 20%）。这 23 条不归本体：多挂一跳要能力清单暴露「哪些关系有实例」或编译器先探路；相对时间要 OQL 支持或编译器改写；枚举值要 `PropertySpec` 带允许值。全部记 clife-onto-engine 平台 backlog。

**规则层 D⁻ = 0 → 本轮归因没有本体侧提案。** 这是真实窗口第一次出现：业务侧 reviewed 反馈里没有一条把错误归到规则实现。两种解释都要写进论文：(a) P2–P6 五轮修完后，CQ 覆盖的规则面在这批口语上已经稳定；(b) 本窗口口语是前两窗 CQ 的变体，覆盖面没有扩大——下一窗要换新 CQ 才能分辨。

## 3. 非轨迹里暴露的实现缺失（提案流的另一个入口）

12 句非轨迹里有 2 句路由到了**只有桩的动作**：0224 `转介医师`、0233 `去重与通道仲裁`（`NotImplementedError: … handler 待实现`；`__init__.py` 里同类桩还有 10 个派生函数）。它们没有审计轨迹、不能走反馈 → 案例 → Dᵢ 的路，但 IR §4 声明了这两个动作，实现缺失（IMPL_MISSING）是本体侧的缺口。提案要走另一条路：先补 CQ（这两个动作的 golden 口语）→ 补 handler → 用 CQ 案例做 Dᵢ。已走通（§6）：给两个动作各补 CQ 口语（`cq/make_impl_cases.py`，P7 3 句、P8 5 句，带变体，manual 路由 `cq/impl_routes.json`），在生产 h_i 上 runner 记 IMPL_MISSING（判不过），沙箱补实现后作 P7 / P8 走双关卡。

专家草案另记的规则偏离 IR 候选（标注人未把它们判成 wrong，所以不是 D⁻）：R04a 只判前一读数 <3.9 而 IR 要两个读数都在 3.0–3.9（0219）；摄入读数 0 条批次照样 committed、R48 不看顶层 payload（0273）；推送告警无 level 时 `_content_type` 不识别为告警致 C22 误拒（0220 变体实测）；R55 的安抚词表拦不住「数据已同步到」类事实性误述（0229）；seed 两处不一致（A-P0045-02 raised_at 与真实低值读数差一天；cred-chen 到期 33 天仍 valid）。

## 4. P6 在下一轮留出集 B_4 上的回退（论文 P-A 协议）

`sets/holdout-4.yaml`：real-only 40 条 / 20 层（family × tier；三窗口 ts 同日，time_half 退化）/ 不 thin，从 140 条候选抽（round 4 无 Dᵢ，不排除；seed 4），**W43 7 / W44 12 / W45 21**。生产 `_fde.py` 反打 `P6.patch` 得 pre-P6 沙箱：

| 状态 | A | T_1 | T_3 | T_4 | 失败案例 |
|---|---|---|---|---|---|
| pre-P6 | 0.825 | 0.571 | 0.9375 | 1.0 | 路由层 6 + 低血糖安全-r10 |
| post-P6（现生产） | 0.850 | 0.571 | 1.0 | 1.0 | 路由层 6 |

无回退。注意两臂唯一的差异就是 P6 自己的 Dᵢ（低血糖安全-r10）——round 4 没有 Dᵢ 可排除，上一轮的 Dᵢ 按协议留在池里，被抽进了 B_4。P6 在 B_4 上「多修一条」不是新证据，只是 Dᵢ 重现；与 P5 在 B_3 上多修 r16/r18（Dᵢ 之外的两条）性质不同。`arm_compare.py` 现在 P5、P6 都按 next-round basis 判，P2–P4 仍同轮 B → `REGRESS_MIXED_B`。

## 6. P7 / P8：实现缺失的提案（Dᵢ 来自新 CQ，不来自反馈）

| 提案 | 编辑 | Dᵢ | 内关卡 3d | 外关卡（B_4 real 40） | 3d 裁决 | 对照臂 |
|---|---|---|---|---|---|---|
| P7 转介医师 | 补 handler（写 ReferralRecord、派医师接单）；R58 / R33 对「本次已转介」短路 | 3 条 CQ（9 句） | ΔT_3 +1 · ΔW_family +1 · ΔA +1 · ΔC +0.33 | 全 0（两臂逐行相同） | **ACCEPT** | 八臂同判 ACCEPT |
| P8 去重与通道仲裁 | 补 handler；R48 兼读 reading_candidate；R02 由桩改实现；R36 缺参数自算 | 5 条 CQ（15 句，含 rejected(R48) 与 R02 伪差分支） | ΔT_3 +1 · ΔW_family +1 · ΔA +1 · ΔC +0.40 | 全 0 | **ACCEPT** | 七臂 ACCEPT，random REVISE |

两份都是 B-sim 294/294、B_4 102/120 两臂逐行相同。**未合入生产。** 发现的连带问题：P8 补 handler 一处不够——它挂的 R02 也是桩、R36 的 declarative 体在参数缺失时 TypeError、R48 不读本动作的参数，三处不一起改动作照样跑不起来；生产 `__init__.py` 里还有 65 处同类桩。runner 相应改为把 NotImplementedError 判成 IMPL_MISSING（不过、可评判），而不是 ENGINE_ERROR（不可判）。

## 5. 方法问题

1. **提案流的第二个入口**：反馈路径在本窗口产出 0 份提案，而非轨迹里有 2 个实现缺失——归因只看 audit.jsonl 会漏掉「动作根本没跑起来」这一类缺口。本轮把 routing.log 的 error 行当 D⁻ 候选（类型 IMPL_MISSING），Dᵢ 由新补的 CQ 构成而不是反馈标签，P7 / P8 走通了双关卡（§6）。这类 Dᵢ 是「构造」的：h_i 上必败（桩），闸门没有机会拒，八臂同判在意料之中。
2. **变体口语的价值在路由层而不在规则层**：W45 的 58 条新案例几乎没有扩大规则覆盖面（规则层 0 条 wrong），但把三类路由错误的复现次数翻了一倍。
3. **real 池 140 < 200**，仍不开正式 run；每层 ≥16 的分层条件也未查（20 层 × 16 = 320 > 200，分层定义与池规模条件本身冲突，要在 criteria 修订时处理）。
4. **跨窗口不跨时间**（三窗口同日）；B_4 含上一轮 Dᵢ。
