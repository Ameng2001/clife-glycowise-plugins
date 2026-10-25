# 交接：W52 窗口（round 9，正式实验第二轮）—— 论文小组 → 数据组

> 2026-10-25。round 8 已结束，3d 链的两条修复 P26a、P27a 已合入生产（ad3c7b6）→ h₉。任务说明：`examples/utterances.2026-W52.brief.md`。

## 一、这一窗口要什么

层已经补齐，正式实验进行中。这一窗口要的是**覆盖面**：十个场景族各 7 句（查询 2 / 直接办或该拦 3 / 起草后等人确认 2），外加 12 句定向口语。目的是让每一轮都有足够的错误案例可归因——正式实验四轮合计要 ≥ 30 份提案，round 8 产出 12 份，后面三轮每轮至少要 8 份左右。

## 二、录制前

1. **在当前生产 h₉ 上录**（glycowise ad3c7b6：合入 P26a、P27a，改了告警结案判断与功效话术识别两条规则）。
2. 会话上下文 `plugins/glycowise/cq/session_context.txt` 不变（四份草稿、签发人只有黄医生）。
3. 写 `examples/utterances.2026-W52.yaml` 与评审表 `utterances.2026-W52.review.md`；定向 12 句单列句序。

## 三、录制与导出（`--seq-base 600`）

```
python3 record_window.py run --engine-root <onto-fundary-plugins> --plugin <plugins/glycowise> \
  --utterances utterances.2026-W52.yaml --context-file <cq/session_context.txt> \
  --audit-db engine-audit/audit.db --pin-ip 8.140.217.18 --window 2026-W52 --seq-base 600
python3 record_window.py export --audit-db engine-audit/audit.db --window 2026-W52 --out trajectories/2026-W52/audit.jsonl
python3 replay_check.py --engine-root … --plugin … --window 2026-W52
python3 draft_feedback.py --window 2026-W52
```

## 四、标注、落案例、check-pool

1. 业务侧标注 `trajectories/2026-W52/feedback.yaml`，`check_feedback.py` 验收。
2. `python3 make_real_cases.py --window 2026-W52 --out ../cases/real`。
3. `holdout_sample.py --cases-dir cases --round 9 --holdout-size 100 --stratify family,tier --merge-min 8 --family-override sets/family-override.yaml --check-pool > checkpool/r9.txt`，**与落案例同一次提交**（正式实验每轮都要留这份记录，且早于归因）。跑前核对三个分层文件的哈希与 v5 头注一致。
4. 交回：check-pool 输出、各族进引擎率、标注统计（correct / wrong / partial，wrong 里 rule / router 各几条）、定向 12 句的落池情况。

## 五、约束不变

写口语的同学不看 `cases/real/`、`feedback*.yaml`、`trajectories/`；数据组不看归因报告、提案、台账与裁决；标注由业务侧；W43–W51 的 examples 侧文件不改；不动 `ingestions/`。commit 前缀 `feat(studio-evolve/glycowise)` / `docs(studio-evolve/glycowise)`。
