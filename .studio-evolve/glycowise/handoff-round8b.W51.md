# 交回：W51 标注、落案例与 round 8 check-pool —— 数据组 → 论文小组

> 2026-10-25。按 `handoff-round8.W51.md` 第四节与 `formal-runbook.md` 第 1 节完成。**check-pool 通过**，round 8 可记为 formal 起点 s——判定与台账、`checkpool/s.txt` 由你们按手册第 1 节第 4 步记。详细读数见 `examples/README.md` ①-12 / ①-13。

## 一、check-pool 输出

`checkpool/r8.txt`，与 W51 案例同一次提交（8128cb5，2026-10-25 11:43:56），早于本轮任何归因文件。

- 命令：`holdout_sample.py --cases-dir cases --round 8 --holdout-size 100 --stratify family,tier --merge-min 8 --family-override sets/family-override.yaml --check-pool`
- 跑前核对：`sets/family-override.yaml`、`holdout_sample.py`、`_common.py` 的 sha256 与 v5 头注一致。
- 结果：池 424 ≥ 200，25 层，**并层后不足 8 的层 0 个**。

| 原薄层 | W50 后 | 现在 |
|---|---|---|
| 高血糖与波动×4 | 1 | 13 |
| 产品与机构合规×4 | 4 | 14 |
| 出口签发闸×4 | 5 | 13 |
| 参考与配置×4 | 7 | 11 |

## 二、标注与落案例

- 业务侧标注（40c68d6）：49 条，correct 38 / wrong 10（rule 6 / router 4）/ partial 1；`check_feedback.py` 通过。
- `make_real_cases.py --window 2026-W51`：新增 48，partial 0517 不落 → real 池 376 → 424。tier4 37 / tier3 11。

## 三、各部分进引擎率

| 部分 | 句数 | 进引擎 |
|---|---|---|
| 高血糖与波动 · 转介医师 / 送审 | 12 / 4 | 12 / 4 |
| 产品与机构合规 · 上架 + 服务包 | 10 | 10 |
| 出口签发闸 · 黄医生签 | 8 | 8 |
| 参考与配置 · 非高危放宽 | 4 | 4 |
| 第二组 · 功效话术 | 6 | 5 |
| 第五节 A · 回执不结案 | 4 | 4 |
| 第五节 B · 非分层 N 级 | 2 | 2 |

合计 49/50。唯一没进的是 0538（P0007「吃上以后血糖就平了」），大模型点破疗效承诺后反问。

写法上偏离 brief 三处，评审表第三节写了原因：签发只用黄医生（陈营养师资质已过期）、不写发布宣传素材（seed 无合规素材编号）、送审只写 4 句。送审 4 句标注全判 wrong（router）：路由 3 句编了不存在的 content_id，1 句填了不相干的 c-P0012-plan-02。

## 四、定向补充 12 句的落池

| 组 | 落池 | 标注 |
|---|---|---|
| 功效话术重写（P0045 ×4、P0007 ×2） | 5，tier3（产品与机构合规-r41–r45） | 0509 correct（D9 拒）；0508 / 0510 / 0511 / 0539 wrong，truth_expect = rejected(D9) |
| 回执不结案（P0045 ×2、P0031 ×2） | 3（因果链溯源-r37–r39） | 0507 correct；0506 / 0516 wrong（P22a 误拦），truth_expect = action(响应并回执告警)；0517 partial 不落 |
| 非分层 N 级（P0012、P0066） | 2，tier4（结论层与分层-r40 / r41） | 都 correct，P23a 未误拦 |

## 五、一处 tier 口径请知悉

wrong 案例的 tier 由 truth_expect 推出，而 `action(动作名)` 不区分直接落库和进人审，一律落 tier3。所以 0506 / 0516（回执，应进 HIL）和送审 4 条（审核输出内容，应进 HIL）落了 tier3，同类 correct 案例都在 tier4。共 6 条，只会让 tier4 少计，不影响本次通过。分层规则已随 v5 冻结，要改属于 amend，由你们定。

## 六、约束

数据组没打开归因、提案、台账与裁决文件，没写 `checkpool/s.txt` 与台账。
