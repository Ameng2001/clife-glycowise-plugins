# 交接：round 7（W50 窗口）—— 论文小组内部流程，含 RQ-2 独立链

> 2026-10-24 起草。前置：W50 brief 已交数据组（`examples/utterances.2026-W50.brief.md`），录制 → 标注回传后本轮开始。与 round 6 的差别只有一处：**RQ-2 从本轮起走真正的 P-B 独立链**（用户 2026-10-24 裁定 (A)），3d 与 1d 两条链各自归因、各自前进；轮次按 v4 候选 ⑥ 为 round 7–10 四轮。

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
- 两条链的 h_0 都是 `chains/ancestor/`（P2–P4 合入前）。round 1–6 的提案流已用 `chain_drive` 重放到各臂（`chains/{arm}/chain.json`），**两链 round 6 末态相同**（除 random）。round 7 起分叉。
- 消融臂（3d-noT / noS / noW）、1d-strict、none、random 不独立归因，继续重放 3d 链的提案流（RQ-1 / RQ-3 的 P-A 协议不受影响）。

### 3.2 每轮顺序（同一归因者）
| 日 | 做什么 | 产物 |
|---|---|---|
| D0 | 常规流程 1–5 的前三步（落案例、check-pool、抽 B_7）。B_7 两链共用（同 seed）。 | `sets/holdout-7.yaml` |
| D1 | **1d 链归因**：在 `chains/1d/state/` 当前状态上跑 W50 real 集，取 D⁻（只认 reviewed wrong 且归因到规则层），每条 D⁻ 出根因修 + 朴素修，沙箱验证，写 `chains/1d/attribution/round-7.md` 与 `round-7/`。**不打开 `chains/3d/`。** | 1d 的提案与 Dᵢ |
| D1 | `chain_drive.py run --manifest chains/1d/manifest-r7.yaml --gate-mode 1d`：1d 判定式裁决，ACCEPT 合入 1d 链。 | `chains/1d/chain.json` 追加 |
| D2（≥ D1 + 1 天） | **3d 链归因**：同样的输入（同一份 feedback.yaml），在 `chains/3d/state/` 当前状态上做，写 `chains/3d/attribution/round-7.md`。**不打开 `chains/1d/attribution/`。** 报告列出读过的文件。 | 3d 的提案与 Dᵢ |
| D2 | `chain_drive.py run --manifest chains/3d/manifest-r7.yaml --gate-mode 3d`；3d 链的提案同时进 P-A 八臂（`gate_decide` 八个 mode，`--ledger`），供 RQ-1 / RQ-3。 | verdicts、台账行 |
| D3 | 事后比对：两链对同一 D⁻ 的补丁差异（相同 / 不同修法 / 一链没修）写进 W50 报告 §RQ-2，并记 `chains/compare-r7.md`。 | 附录材料 |

### 3.3 为什么是这个顺序
- 先 1d 后 3d：3d 是主链，归因者对它最熟；把 1d 放前面，1d 的归因不受当轮 3d 补丁的影响。3d 归因者知道 1d 修了什么——这一点排除不了，靠留痕与事后比对（论文 §6.2 已写）。
- 两链提案共用编号计数器，链名进台账 notes，避免 verdict 文件撞名。
- 朴素修的生成规则对两链相同（criteria v3 §5 预登记四条）。

### 3.4 末轮（round 10）
两链末态各在三次重抽的留出集与 real-all / B-sim 上出读数（`chain_drive.py summarize`），T3 / F1 / F2 由 `results_tables.py --chains-dir` 排出；T_tier3_gain_diff 与 A_holdout_diff 的 CI 按三次重抽算；tier-3 留出样本合并 < 30 → RQ-2 只报告不判定。

## 四、交付

`attribute-report-2026-W50.md`；`sets/holdout-7.yaml`；P9a / P16a–P19a 的 B_7 回退判定与朴素修重判；两链 `attribution/round-7.md` 与各自提案；`chains/compare-r7.md`；台账 round 7 行；`arms/r1-7/`；论文 README 第 1–3 项更新。
