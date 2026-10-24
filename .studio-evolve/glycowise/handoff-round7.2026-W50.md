# 交接：W50 口语集已写好 —— 数据组 → 论文小组

> 2026-10-24。按 `examples/utterances.2026-W50.brief.md` 写完 `examples/utterances.2026-W50.yaml`，59 句，全部 tier4；评审表 `examples/utterances.2026-W50.review.md`。**未录制**。

## 一、交付与验收对照

| 验收项 | 结果 |
|---|---|
| 高血糖与波动 ≥14 | 15（无关信息 5 / 换说法 5） |
| 参考与配置 ≥10 | 11（4 / 4） |
| 出口签发闸 ≥8 | 8（3 / 3） |
| 产品与机构合规 ≥10 | 11（4 / 4，含第二组 6 句） |
| 因果链溯源 ≥8 | 8（3 / 3，含第一组 6 句） |
| 结论层与分层（第三组） | 6（2 / 2） |
| 第一组禁词「关掉 / 撤销 / 删」及否定句 | 0 命中；复测值全在 4.1–4.5 |
| 第二组禁词「糖化能再降一截 / 血糖稳得住 / 缓解 / 逆转 / 分层」 | 0 命中 |
| 第三组禁词「L 字母 / 一级糖尿病 / 分层结论 / 服务分层 / 分层是一级」 | 0 命中 |
| 患者白名单 / 通用禁词 / 与 W47–W49b 换患者重写 | 全部通过 |

脚本化自检全部 ✓，各层每层 ≥1/3 无关信息、≥1/3 换说法。

## 二、三组定向口语的句序（YAML 里不带组别字段，按句序对）

录制用 `--seq-base 400`，则 trace 序号 = 400 + 句序。

| 组 | 计入层 | 句序 |
|---|---|---|
| 第一组 · 黄伯真闭环（A-P0045-02，复测 4.1–4.5） | 因果链溯源 | 1–6 |
| 第二组 · 英纽林功效话术换说法 | 产品与机构合规 | 15, 16（P0012）、27, 28（P0007）、32, 33（P0088） |
| 第三组 · 群里告诉患者分层（换写法） | 结论层与分层 | 17, 18（P0012）、38, 39（P0023）、52, 53（P0066） |

（以 `review.md` 第 4 节的「组」列为准。）

## 三、录制前要你们定的两件事

1. **出口签发闸的草稿对象**：brief 让写「d-P0012-02 让王健管师签」这类，seed 里只有 d-P0012-01；d-P0012-02 / d-P0045-01 / d-P0031-01 不存在。录出来可能是「对象不存在」而不是 D11a / D12 资质闸拒——要测签发闸就得补 seed（给 P0045 / P0031 各一份含用药调整的草稿），否则这层落下的仍是另一种拒。
2. **第三组的对照**：P0012 / P0066 / P0023 的 disclosure_approved 都不是 true，所以三组 6 句按业务都该被 R51 拦；如果你们想同时要一条「授权后该放」的对照句，得先在 seed 里给某位患者打 disclosure_approved=true，brief 里没要求，我没写。

## 四、录制与后续（按前几个窗口的流程）

```
python3 record_window.py run --engine-root <onto-fundary-plugins> --plugin <plugins/glycowise> \
  --utterances utterances.2026-W50.yaml --context-file <cq/session_context.txt> \
  --audit-db engine-audit/audit.db --pin-ip 8.140.217.18 --window 2026-W50 --seq-base 400
python3 record_window.py export --audit-db engine-audit/audit.db --window 2026-W50 --out trajectories/2026-W50/audit.jsonl
python3 replay_check.py --engine-root … --plugin … --window 2026-W50
python3 draft_feedback.py --window 2026-W50
```

录完先看三组的进引擎率：第一组要进 响应并回执告警 并被 R44 评到；第二组要进 生成产品推荐 并被 D9（P16a 新正则）评到；第三组要进 群内答复患者 并被 R51（P19a 新 TIER_RE 分支）评到。哪组没进引擎，是路由层问题，与规则修复无关，要分开记。

## 五、约束不变

不看 cases/real、feedback*.yaml、trajectories/；不改 W43–W49b 文件；标注仍由业务侧。
