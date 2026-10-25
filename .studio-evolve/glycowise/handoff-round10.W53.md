# 交接：W53 窗口（round 10，正式实验第三轮）—— 论文小组 → 数据组

> 2026-10-25。round 9 已结束，3d 链修复 P28a 已合入生产（57a8b67）→ h₁₀。任务说明：`examples/utterances.2026-W53.brief.md`。

## 一、为什么这次要换写法

正式实验每轮要从错误案例里找出「系统规则判错」的缺陷来出提案。W52 按覆盖面写，15 条错误里只有 2 条是规则判错（其余是大模型路由或演示数据问题），这一轮只出了 4 份提案。正式实验还剩两轮，样本量已经很紧。W53 改为**多写落在规则边界上的请求**：临界数值、不存在或状态不对的对象、叠加条件、新说法。查询只写 4 句（查询类的错几乎都在路由和演示数据上）。约 100 句。

## 二、落案例脚本已修（请知悉）

`examples/make_real_cases.py` 的 `route_of`（论文组 2026-10-25 修）：路由置信度原来取轨迹顶层的 `confidence`，那其实是动作执行后 handler 自设的置信度（读数不存在时会设 0.3），不是路由意图的置信度；回放时低于路由门槛 0.55 就会变成追问，规则评不到。现在一律取 0.95（进了轨迹的请求录制时都已过路由门槛）。引擎只在路由门槛处用这个值，所以对其他案例的回放结果没有影响。

**r47 已按修正后的脚本重新落池**：`cases/real/低血糖安全-r47.yaml` 只改了路由置信度 0.3 → 0.95（附说明字段）。用新脚本把 W52 整窗重新落到临时目录逐条比对过：71 条除编号和置信度外完全相同，原值低于门槛的只有 r47。其余 W52 案例保持原样。**W53 起落案例用新脚本即可，不需要回头重落旧窗口。**

## 三、录制（在 h₁₀ 上，`--seq-base 700`）

```
python3 record_window.py run --engine-root <onto-fundary-plugins> --plugin <plugins/glycowise> \
  --utterances utterances.2026-W53.yaml --context-file <cq/session_context.txt> \
  --audit-db engine-audit/audit.db --pin-ip 8.140.217.18 --window 2026-W53 --seq-base 700
python3 record_window.py export --audit-db engine-audit/audit.db --window 2026-W53 --out trajectories/2026-W53/audit.jsonl
python3 replay_check.py --engine-root … --plugin … --window 2026-W53
python3 draft_feedback.py --window 2026-W53
```

会话上下文不变。任务说明第二节用到了陈营养师（资质已过期，签发人编号 S-CHEN 在会话里），和编造的读数编号，录制时照写，不要因为「明知会被拦」而跳过。

## 四、标注、落案例、check-pool

1. 业务侧标注，`check_feedback.py` 验收。**标 wrong 时请尽量写清落库应该是什么样**（哪个对象、哪个字段）：W52 有 5 条 wrong 只写了期望动作名，回放时判成了「通过」。
2. `python3 make_real_cases.py --window 2026-W53 --out ../cases/real`（新脚本）。
3. `holdout_sample.py --cases-dir cases --round 10 --holdout-size 100 --stratify family,tier --merge-min 8 --family-override sets/family-override.yaml --check-pool > checkpool/r10.txt`，与落案例同一次提交；跑前核对三个分层文件哈希。
4. 交回：check-pool 输出、各节进引擎率、标注统计（wrong 里 rule / router / seed 各几条）、第五节 6 句落池情况。

## 五、约束不变

写口语的同学不看 `cases/real/`、`feedback*.yaml`、`trajectories/`；数据组不看归因报告、提案、台账与裁决；标注由业务侧；W43–W52 的 examples 侧文件不改（`make_real_cases.py` 与 r47 的修正由论文组完成并已说明）；不动 `ingestions/`。
