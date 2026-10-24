# 交接：round 7（W50 窗口）—— 论文小组内部流程，含 RQ-2 独立链

> 2026-10-24 起草，同日按导师签字意见（paper `proposal/advisor-signoff-2026-10-24.md`）修订。前置：W50 口语集已写好（59 句），seed 已补（f0df4e5），数据组可录。**criteria v4 已 amend、待 freeze；freeze 之前不打开 W50 的任何轨迹 / 路由日志 / 反馈草案**（导师要求 round 7 数据被看过之前签完）。与 round 6 的差别：**formal 从本轮起（round 7–10 四轮，P-A 与 P-B 同），RQ-2 走真正的 P-B 独立链**，3d 与 1d 两条链各自归因、各自前进。

## 一、硬约束（不变）

不碰 `ingestions/`；不改 IR 正文与规则实现，除非用户明确要求合入；不给 `feedback.yaml` 填 label；不手改 `trajectories/`、`routing.log`；W43–W49b 的 examples 侧文件不动；归因只认 reviewed 反馈；提案先查台账拒绝签名表；所有 runner / growth_metrics / holdout_sample 调用带 `--family-override sets/family-override.yaml`；commit 前缀 `feat(studio-evolve/glycowise)` / `docs(studio-evolve/glycowise)`。

## 二、标注回传后的常规流程（与 round 6 相同）

1. `python3 examples/make_real_cases.py --window 2026-W50 --out ../cases/real`（source 优先归 family）。
2. `holdout_sample.py --check-pool --family-override …`：确认 5 个 tier4 薄层是否过 8；三组定向口语是否落进 real 池（按 `source` 数：因果链溯源#tier4 真闭环、产品与机构合规#tier4 功效话术、结论层与分层#tier4 分层写法）。**落不进（LLM 抢闸）→ 触发 v4 候选 ⑤ 的退路讨论**，写进 W50 报告。
3. 抽 `sets/holdout-7.yaml`（40 / 并层 8，seed 7，排除本轮 Dᵢ）。
4. **按 B_7 判上一轮合入提案的回退**：P9a、P16a–P19a 在 B_7 上 h_{pre} vs h_{post}（协议口径 B_{i+1}）；同时把朴素修 P16b / P17b / P18b / P19b 在 B_7 上重判——这是第一次有机会在 real-only 留出集上看到配对分歧。
5. W50 归因报告 `attribute-report-2026-W50.md`（非轨迹节、归因节、提案节、§方法问题）。

## 三、RQ-2 独立链（本轮新增）

### 3.1 链的起点
- **RQ-2 基准 h₇ = 生产 `plugins/glycowise` 在 W50 补 seed 后的提交 f0df4e5**（含 P2–P8、P9a、P14、P16a–P19a 与三份新草稿 seed），两链同一份：round 7 开始时 `cp -r` 到 `chains/3d/state-r7/` 与 `chains/1d/state-r7/`，并记目录哈希。T_tier3_gain 以 h₇ 为第 0 轮。round 1–6 的重放链（`chains/{arm}/chain.json`，祖先 `chains/ancestor/`）只作 F1 试运行曲线，不作 formal 基准。
- 消融臂（3d-noT / noS / noW）、1d-strict、none、random 不独立归因，继续重放 3d 链的提案流（RQ-1 / RQ-3 的 P-A 协议不受影响）。

### 3.2 每轮顺序（同一归因者）
| 日 | 做什么 | 产物 |
|---|---|---|
| D0 | 常规流程 1–5 的前三步（落案例、check-pool、抽 B_7）。B_7 两链共用（同 seed）。 | `sets/holdout-7.yaml` |
| D1 | **先归因的链**（r7、r9 先 1d；r8、r10 先 3d——顺序轮换）：在该链 `state/` 当前状态上跑本轮 real 集，取 D⁻（只认 reviewed wrong 且归因到规则层），每条 D⁻ 出根因修 + 朴素修（朴素修按预登记四条规则机械生成），沙箱验证，写 `chains/{arm}/attribution/round-N.md` 与 `round-N/`。**不打开另一链的目录，不看本臂的 verdicts/ 历史拒绝记录**；报告列出读过的文件。 | 该链的提案与 Dᵢ |
| D1 | `chain_drive.py run --manifest chains/{arm}/manifest-rN.yaml --gate-mode {arm}`：本链判定式裁决，ACCEPT 合入本链。 | `chains/{arm}/chain.json` 追加 |
| D2（≥ D1 + 1 天） | **后归因的链**：同样的输入（同一份 feedback.yaml），在另一链 `state/` 当前状态上做，同样的限制。 | 另一链的提案与 Dᵢ |
| D2 | 后归因链同样 `chain_drive.py run`。**3d 链的提案**（无论先后）同时进 P-A 八臂（`gate_decide` 八个 mode，`--ledger`），供 RQ-1 / RQ-3；回退率按 v4 (f) 同时算「含 / 不含定向补充案例」两版。 | verdicts、台账行 |
| D3 | 事后比对：两链对同一 D⁻ 的补丁差异（相同 / 不同修法 / 一链没修）写进 W50 报告 §RQ-2，并记 `chains/compare-r7.md`。 | 附录材料 |

### 3.3 为什么轮换
- 固定「先 1d 后 3d」会让第二次归因的学习效应系统性偏向 3d（导师意见 §1.1）。轮换：r7、r9 先 1d；r8、r10 先 3d。记忆污染仍排除不了，靠留痕（读过的文件清单）与 D3 事后比对（论文 §6.2）。
- 两链提案共用编号计数器，链名进台账 notes，避免 verdict 文件撞名。
- 朴素修的生成规则对两链相同（criteria v3 §5 预登记四条）。

### 3.4 末轮（round 10）
两链末态各在三次重抽的留出集与 real-all / B-sim 上出读数（`chain_drive.py summarize`），T3 / F1 / F2 由 `results_tables.py --chains-dir` 排出；T_tier3_gain_diff 与 A_holdout_diff 的 CI 按三次重抽算，判定只认 CI 下界（v4 (c)）；**功效不足分支优先**：CI 半宽 > 0.10 或 tier-3 合并 < 30 → 「功效不足、不判定」。RQ-1 / RQ-3 四轮累计 < 30 或接受集 < 30 同记功效不足（v4 (a)）。

## 四、交付

`attribute-report-2026-W50.md`；`sets/holdout-7.yaml`；P9a / P16a–P19a 的 B_7 回退判定与朴素修重判；两链 `attribution/round-7.md` 与各自提案；`chains/compare-r7.md`；台账 round 7 行；`arms/r1-7/`；论文 README 第 1–3 项更新。
