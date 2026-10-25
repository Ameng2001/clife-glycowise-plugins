# 交接：W51 补录窗口 —— 论文小组 → 数据组

> 2026-10-25。round 7 已收尾。请按本文写、录、标、落 W51，跑完 check-pool 后交回。任务说明：`examples/utterances.2026-W51.brief.md`（已含第五节追加 6 句）。

## 一、为什么要这一窗口

real 池 376 条，按场景族 × 层分后还有 **4 个层不足 8 条**，formal 开不了：

| 层（并层后的「其余」层） | 现有 | 差 |
|---|---|---|
| 高血糖与波动 | 1 | 7 |
| 产品与机构合规 | 4 | 4 |
| 出口签发闸 | 5 | 3 |
| 参考与配置 | 7 | 1 |

之前没补上，是我们的任务说明把「该被拦的请求」当成第 4 层写了（实际落第 3 层）。W51 说明已改正：这几层要的是**正确结果为「起草后等医师 / 合规官确认」的正常请求**。这一窗口补齐后，round 8 就可能成为 formal 第一轮。

## 二、录制前

1. **生产插件已更新**（glycowise 08c8cf1：合入 P22a、P23a，改了告警闭环与分层识别两条规则）。W51 请在当前生产上录，不要用旧版本。
2. 复核 `plugins/glycowise/cq/session_context.txt`：含 d-P0045-01 / d-P0031-01 / d-P0012-02 / d-P0012-01 四份草稿，签发人只有黄医生、陈营养师（W50b 已补）。
3. 按任务说明写 `examples/utterances.2026-W51.yaml`（约 50 句）和评审表 `utterances.2026-W51.review.md`；第二组 6 句与第五节 6 句在评审表里单列句序。

## 三、录制与导出（同 W50，`--seq-base 500`）

```
python3 record_window.py run --engine-root <onto-fundary-plugins> --plugin <plugins/glycowise> \
  --utterances utterances.2026-W51.yaml --context-file <cq/session_context.txt> \
  --audit-db engine-audit/audit.db --pin-ip 8.140.217.18 --window 2026-W51 --seq-base 500
python3 record_window.py export --audit-db engine-audit/audit.db --window 2026-W51 --out trajectories/2026-W51/audit.jsonl
python3 replay_check.py --engine-root … --plugin … --window 2026-W51
python3 draft_feedback.py --window 2026-W51
```

录完先看各层进引擎率（尤其高血糖与波动、出口签发闸两层，W50 是 1/15、0/8）；哪组没进引擎，记路由层原因。

## 四、标注与落案例

1. 业务侧标注 `trajectories/2026-W51/feedback.yaml`（reviewed、reviewer 填好、label 全非空），`check_feedback.py` 验收。
2. `python3 make_real_cases.py --window 2026-W51 --out ../cases/real`。
3. `holdout_sample.py --cases-dir cases --round 8 --holdout-size 100 --stratify family,tier --merge-min 8 --family-override sets/family-override.yaml --check-pool`——注意 **holdout-size 用 100**（formal 口径；W50 时用的 40 是试运行口径）。
4. 交回：check-pool 输出、各层进引擎率、定向补充 12 句（第二组 6 + 第五节 6）的落池情况。

## 五、约束不变

写口语的同学不看 `cases/real/`、`feedback*.yaml`、`trajectories/`（口语必须在不知道标签的情况下写）；数据组不看归因报告、提案、台账与裁决；标注由业务侧；W43–W50b 的 examples 侧文件不改；不动 `ingestions/`。commit 前缀 `feat(studio-evolve/glycowise)` / `docs(studio-evolve/glycowise)`。
