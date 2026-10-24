# 交接：W50 / W50b 落案例与 check-pool —— 数据组 → 论文小组

> 2026-10-24。业务侧标注已回传（f7a42d9），数据组按 `handoff-round7.md` 二-1、二-2 落了案例、跑了 `--check-pool`（7cf8b81）。请从 **二-3（抽 holdout-7）** 继续，并定下一批补录配额。详细读数见 `examples/README.md` ①-9 / ①-10 / ①-11。

## 一、标注与落案例

| 窗口 | 轨迹 | 标注 | 落案例 |
|---|---|---|---|
| W50 | 26 | correct 20 / wrong 6 / partial 0 | 26 |
| W50b（签发闸 8 句重录） | 2 | correct 2 | 2 |

`check_feedback.py` 两窗口验收通过。`make_real_cases.py --window 2026-W50 / 2026-W50b --out ../cases/real` → **real 池 348 → 376**。

签发闸这层按用户裁定记 2/8，不再为健管师补 seed 重录（健管师 / 吴康复师没有 signer_id，大模型一律反问）。W50b 录前在 `plugins/glycowise/cq/session_context.txt` 补了 d-P0045-01 / d-P0031-01 / d-P0012-02 与「黄伯 = 患者 P0045」，只列 id（fa5355a）。

## 二、check-pool 结果

命令：`holdout_sample.py --cases-dir cases --round 7 --holdout-size 40 --stratify family,tier --merge-min 8 --family-override sets/family-override.yaml --check-pool`

池 376 ≥ 80，25 层，**4 个 rest 层不足 8**：

| rest 层（并层后） | 现有 | 差 |
|---|---|---|
| 产品与机构合规 | 4 | 4 |
| 出口签发闸 | 5 | 3 |
| 参考与配置 | 7 | 1 |
| 高血糖与波动 | 1 | 7 |

因果链溯源×4 = 9、结论层与分层×4 = 17 已过 8。

## 三、tier 口径不一致（定配额前请先看）

`make_real_cases` 按**期望裁决**定 tier：query 1 / 多跳 2 / action·rejected 3 / HIL 4。W50 brief 的五个薄层要的是「该被拦」的 tier4，可该被拦 = 期望 rejected，落案例一律 tier3。

- W50 + W50b 28 条里 **22 条落 tier3**，只有 6 条期望为 HIL 的进了 tier4（参考与配置 4 条放宽阈值、因果链溯源 2 条）。
- 所以按现行 tier 规则，rest 层只能靠「**正确结果是进 HIL**」的句子填，写多少该被拦的句子都进不去。round 6 已见过同一现象（64 条按裁决换层）。

两条路，请你们定：

1. **配额按案例 tier 重写**：下一批 brief 的薄层句子写成正确结果是 pending_hil 的请求（如非高危患者放宽阈值、代人回执、需医师确认的草稿签发），而不是该被拦的。
2. **改 tier 口径**：让 brief 的 `#tier4` 或「该被拦且需多步推理」也能落 tier4。这会改 `make_real_cases` 和既有案例的层归属，属于 amend 范围。

## 四、三组定向口语的落池情况

三组都落进了 real 池，全部是 tier3：

| 组 | 案例 | 标注 | 说明 |
|---|---|---|---|
| 一 · 黄伯真闭环 | 因果链溯源-r29–r34（6） | wrong 4 / correct 2 | 0401 / 0403 / 0404 / 0406 引擎进 HIL，truth_expect = rejected(R44)；0402 / 0405 被 R44 拒 |
| 二 · 英纽林功效话术 | 产品与机构合规-r35–r38（4） | correct 4 | 全部被 C4 先拦（P0012 / P0088 无营销推荐同意），**D9 一次都没评到**；P0007 两句被大模型反问没进引擎 |
| 三 · 分层换写法 | 结论层与分层-r35–r39（5） | wrong 1 / correct 4 | 0418「评下来是 2 级」进 HIL，truth_expect = rejected(R51) |

另 1 条 wrong：因果链溯源-r35（0425 改告警级别），路由选了 升级告警，truth_expect = action(撤销更正已发出告警)。

第二组要评到 D9，句子得换成有营销推荐同意的患者（seed 里只有 P0007 / P0045），且要避开大模型「缓解评估期」的反问。是否按 handoff-round7 二-2 触发 v4 候选 ⑤ 的退路讨论，由你们在 W50 报告里定。

## 五、请你们接着做

1. 从 `handoff-round7.md` **二-3** 继续：抽 `sets/holdout-7.yaml`、重建 real-W50 集、按 B_7 判 P9a / P16a–P19a 回退并重判朴素修。数据组没动这些。
2. 定下一批补录：按第三节选一条路，给出 4 个 rest 层的配额与写法要求，写成 brief 交数据组。
3. W50 归因报告里记两个路由层发现：签发闸的签发人门槛（会话上下文只列两个 signer_id）、高血糖与波动 1/15（「加一档 / 出高血糖结论」在动作清单里没有对应动作）。

## 六、约束不变

数据组不看归因与提案文件；标注仍由业务侧；W43–W50b 的 examples 侧文件不改。
