# 交接：round 6（2026-W47 窗口）—— 给论文小组

> 2026-10-24。上游状态：W47 已真录完并提交（`9b1959e`，分支 `feat/glycowise-fde-fill`）。本文件是给你们的工作 prompt：先做不等标注的部分，标注回来后再走 round 6 正式流程。

## 一、现在手上有什么

| 文件 | 内容 |
|---|---|
| `examples/utterances.2026-W47.yaml` | 126 句，数据准备小组按 `examples/utterances.2026-W47.brief.md` 配额写，13 个配额层全部达标；`source` 已带 `brief:{family}#tier{N}[#变体]`，可以直接当分层键用 |
| `examples/trajectories/2026-W47/audit.jsonl` | **90 条真实轨迹**：execute 64（committed 13 / pending_hil 26 / rejected 25）、ask 26。execute 行是引擎 `AuditSnapshot.to_dict()` 原样 |
| `examples/routing.log.2026-W47.jsonl` | 126 句全部路由去向；36 句非轨迹：clarify 22、advise 3、error 11 |
| `examples/trajectories/2026-W47/feedback.yaml` | `status: draft`，90 条 **label 全空**，等业务侧标。每条带 `engine_actual` / `cq_expect` / `suggested`（机器比对：correct 53 / wrong 9 / 无建议 28）。`suggested` 不是标签，`cq_expect` 是口语小组写的参考，不是真值 |
| 回放 | `replay_check.py --mode sequential`：90/90 复现 |
| 成本 | 真 Qwen usage 856,574 token / 126 句 |

录制中途在第 6 句崩过一次（Qwen 产出带 `Or` 节点的 OQL，网关导出只认 `Cond`），已修并用 `--start 6` 续跑；trace 序号连续、前 5 句原样保留。写论文方法节时这算一次工具缺陷，不是数据缺陷。

## 二、硬约束（和前五轮一样）

- 不要给 `feedback.yaml` 填 label，不要改 reviewer；标注是业务侧的事。
- 不要手改 `trajectories/`、`routing.log`，W43–W46 的任何文件也不动。
- 提案先查 `growth-ledger.md` 的拒绝签名表；归因只认 reviewed 反馈。

## 三、现在就能做（不等标注）

1. **起草 `attribute-report-2026-W47.md` 的非轨迹节**（§非轨迹可以先写，§归因留空）：
   - **遥测误绑 8 句**（0012/0013/0030/0063/0065/0090/0103/0109，CV / 夜间覆盖率 / 最低值类 → `无遥测绑定: CgmSummary`）。W44 0126、W45 0227 之后第三次复现，这次整类口语都中招，高血糖与波动 t1 只剩 TAR / 最高值 / 均值几句落成 ask。归平台 backlog，但要写进论文的「路由层不稳定」证据链。
   - **IMPL_MISSING 3 句**：0021 `确认缓解时钟Day0`、0075 `撤销更正已发出告警`、0121 `C5_厂商云对接协议与PIPIA`，三个动作只有桩，第一次被真实口语路由到。前两个是缓解路径 t1 / 低血糖安全 t1 的正路动作，按 round 4 的 P7/P8 模式可以直接起 IMPL_MISSING 提案（补 CQ 口语作 Dᵢ、沙箱补实现、双关卡），**不需要等标注**。C5 涉及境外云协议，先只登记。
   - **LLM 抢闸 11 句**（出口签发闸 t4：0049/0050/0052/0053/0086/0087/0100/0107/0108 等，草稿直发 / 换人签发），引擎 C9 / D11a 没被评到，第四次复现。另有数据与同意合规 t4 的 0060 / 0098 / 0119 / 0120 被反问而非拒，0094 / 0113 判缓解被抢先。advise 3 句（0019/0020/0067）是「转医师答复」被路由成建议而非 `转介医师`。
2. **分层预估**：用 `utterances.2026-W47.yaml` 的 `source` 对 90 条轨迹算 family×tier，叠到现有 203 条上，按 v3 并层口径（<8 并入同 family 其余 tier）预估 round 5 收尾时还薄的 8 个层（产品与机构合规 4 / 低血糖安全 5 / 出口签发闸 3 / 参考与配置 7 / 因果链溯源 7 / 指标口径 7 / 缓解路径 2 / 高血糖与波动 4）标注后能否过 8。注意出口签发闸 t4 被抢闸 11 句、高血糖与波动 t1 被遥测吃掉 8 句，这两层可能仍薄，提前说要不要补录。
3. **修分层口径本身**：`make_real_cases.py` 目前按口语推断 family（去重类被归「指标口径」）。W47 起 `source` 自带 family，改成优先读 `source`，没有再回退推断；顺手把 W43–W46 的 family 归属复核一遍，差异写进报告。
4. **round 5 遗留的决定**（要么本轮关掉，要么写明延后）：
   - criteria amend v3（strict 只认 T/S/W，ΔC 只做约束）待导师签字；
   - `arm_compare` 的单条口径 `regress_any`（r1–5：3d 0 / 1d 0.100，分歧集单条回退 0.5）要不要进 criteria；
   - W_evid 未实现；
   - P9a 未合入，分歧集 {P9b, P9c} 未合入。round 6 的 B_6 要按协议判 P9a 回退，前提是它已合入生产。

## 四、标注回来后（round 6 正式流程）

1. `feedback.yaml` 变 `status: reviewed`、reviewer 填好、90 条 label 全非空 → `python3 make_real_cases.py --window 2026-W47`（partial 不落）。cases/real 预计 ≈ 290。
2. 抽 `sets/holdout-6.yaml`（40 / 20 层，跨 W43–W47，先过并层口径）。
3. 对 B_6 判上一轮合入提案的回退（P9a，若已合入）。
4. 归因 → `attribute-report-2026-W47.md` §归因 → 提案（P10 起编号；IMPL_MISSING 两条可以与规则层提案并行）→ 双关卡八臂 → `growth-ledger.md` 补 round 6 行 → `chains/F1.md` 补 round 6 F1/T3。
5. 机器比对标 wrong 的 9 条，标注前只当候选：ask 查 0 行 6 条（0006 C 肽、0010 GMI、0029 TAR 分级、0033 人群目标区间、0089 / 0102 TAR，多半是 seed 缺派生字段或边，与 W46 的 seed 不一致同型）；0041 推送中级告警被 R56 冻结；0069 回执不闭环仍被 R44 拒（R44 按 IR 只该管闭环）；0110 6 天数据出内部分层被 R01 拒（R01 门槛按 IR 是对的，更像 `cq_expect` 写错）。若标注结果与此不一致，以标注为准。

## 五、交付

- `attribute-report-2026-W47.md`（非轨迹节先出，归因节标注后补）；
- 分层预估表 + `make_real_cases.py` 的 family 口径修改；
- IMPL_MISSING 提案 P10 / P11 的 Dᵢ 口语与沙箱实现（走双关卡，不合入生产）；
- round 5 四项遗留的决定或延后说明。

提交到当前分支，commit 前缀沿用 `feat(studio-evolve/glycowise)` / `docs(studio-evolve/glycowise)`。
