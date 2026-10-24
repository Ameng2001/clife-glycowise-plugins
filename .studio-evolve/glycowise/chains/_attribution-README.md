# chains/{arm}/attribution/ —— 独立链归因留痕（round 7 起，RQ-2 走 P-B 真链）

每条独立链（`3d/`、`1d/`）在每轮各归因一次，产物放本目录：

```
chains/{arm}/attribution/
├── round-7.md          # 归因报告：输入 / 读过与未读的文件 / D⁻ 定位 / 候选缺陷 / 决定修什么 / 时间戳
├── round-7/            # 本轮本链的补丁与 Dᵢ
│   ├── P{num}.patch    # 相对 repo 根，对「本链当前状态」可 git apply --check
│   ├── P{num}.md       # 提案文档（P7/P14 格式）
│   └── P{num}-Di.yaml  # ids 列表（朴素修的 Dᵢ 必带 expect_state）
└── ...
```

规则（与 `handoff-round7.md` 第三节一致）：
1. **顺序轮换**：r7、r9 先 1d 后 3d；r8、r10 先 3d 后 1d；两次间隔 ≥ 1 天、不回看另一链、**不看本臂 `verdicts/` 的历史拒绝记录**。报告里列出本次读过的文件清单（v4 (b)）。
2. 归因输入相同：本轮窗口的 `trajectories/*/feedback.yaml`（reviewed）、`routing.log`、`cases/real`、本链当前状态 `chains/{arm}/state/`。
3. 每个规则层 D⁻ 固定产 1 条根因修 + 1 条朴素修（预登记规则，不挑）；IMPL_MISSING 入口的提案另计。
4. 提案编号：两链共用一个计数器（台账 proposal 列），避免撞号；链名写进 verdict 与台账 notes。
5. 裁决用 `chain_drive.py run --manifest chains/{arm}/manifest-r7.yaml --gate-mode {arm}`，每链一份 manifest，只含本链本轮的提案；消融臂与 random 继续用 3d 链的提案流重放。
