# 交接：W54 窗口（round 11，正式实验第四轮 = 最后一轮）—— 论文小组 → 数据组

> 2026-10-25。round 10 已结束，3d 链 8 份修复已合入生产（ae0e174）→ h₁₁。任务说明：`examples/utterances.2026-W54.brief.md`。

## 一、这一轮的要点

- **写法沿用 W53**（规则边界上的请求），去掉两类已经写够的请求，第五节换一批定向句。
- **新增第六节「补四个格子」**：round 10 的 check-pool 有 4 个格子并层后不足 8（产品与机构合规×1、指标口径×4、数据与同意合规×1、缓解路径×3）。正式实验结束后，还要从案例池里抽 B₁₂ 和 RQ-2 的三次重抽样，这四格不补厚就抽不出来。每格写 9 句，留出被标 wrong 或 partial 不落池的余量。
- **这是最后一个窗口。** 交回后论文小组做 round 11 的两链归因与裁决，再由论文小组抽 B₁₂ 并做 RQ-2 的重抽样。之后不需要再录新窗口；如果 B₁₂ 仍有格子不足 8，会另行通知。

## 二、录制（在 h₁₁ 上，`--seq-base 800`）

```
python3 record_window.py run --engine-root <onto-fundary-plugins> --plugin <plugins/glycowise> \
  --utterances utterances.2026-W54.yaml --context-file <cq/session_context.txt> \
  --audit-db engine-audit/audit.db --pin-ip 8.140.217.18 --window 2026-W54 --seq-base 800
python3 record_window.py export --audit-db engine-audit/audit.db --window 2026-W54 --out trajectories/2026-W54/audit.jsonl
python3 replay_check.py --engine-root … --plugin … --window 2026-W54
python3 draft_feedback.py --window 2026-W54
```

会话上下文不变。W53 的轨迹编号到 0800，这次从 0801 起。录制前请确认生产已是 ae0e174。

## 三、标注、落案例、check-pool

1. 业务侧标注，`check_feedback.py` 验收。**标 wrong 时写清落库应该是什么样**（哪个对象、哪个字段），不要只写期望动作名。
2. **标注里拿不准的条目，请在交回里单列「待确认」并给出倾向**，不要只在 feedback 里留「待确认」字样。W53 有三条（0723、0760、0772）是这样留下的，后面没法核实。W53 的文件不改。
3. `python3 make_real_cases.py --window 2026-W54 --out ../cases/real`
4. `holdout_sample.py --cases-dir cases --round 11 --holdout-size 100 --stratify family,tier --merge-min 8 --family-override sets/family-override.yaml --check-pool > checkpool/r11.txt`，与落案例同一次提交；跑前核对三个分层文件的哈希与 v5 头注一致。
5. 交回 `handoff-round11b.W54.md`，内容包括：
   - check-pool 输出，**特别列出四个格子补后的条数**；
   - 各节进引擎率；
   - 标注统计（wrong 里 rule / router / seed 各几条）；
   - 第五节 8 句的落池情况；
   - 待确认条目。

## 四、约束不变

写口语的同学不看 `cases/real/`、`feedback*.yaml`、`trajectories/`。数据组不看归因报告、提案、台账与裁决。标注由业务侧完成。W43–W53 的 examples 侧文件不改。不动 `ingestions/`。
