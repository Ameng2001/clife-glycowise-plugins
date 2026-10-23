# glycowise 黄金问题集（CQ）与路由录制

| 文件 | 是什么 |
|---|---|
| `golden.yaml` | 28 条黄金问题（7 query / 6 action / 15 rejected）。q 带演示租户对象 id，原始省略 id 的口语保留在 `variants[kind=original]`（23 条） |
| `make_cases.py` | golden → `runner/cases/`（带 variants；替代 runner 的 golden-to-cases） |
| `make_golden_routes.py` → `golden_routes.json` | **人工转录**的理想路由（ReplayLLMClient 格式），衡量"规则 + 回写"层 |
| `record_live_routes.py` | 真 Qwen 录制端。`--pin-ip` 只在本进程钉 DNS（绕本机代理 fake-ip 误路由，不改系统设置）；`--context-file` 把会话上下文作 memory_text 喂给编译器 |
| `golden_routes.live.json` / `.live.diff.md` | 真 Qwen（qwen3.5-plus，role=医师）**无会话上下文**录制 + 与人工转录对账 |
| `golden_routes.live-ctx.json` / `.live-ctx.diff.md` | 真 Qwen **带会话上下文**（`session_context.txt`：患者/告警/内容 id 对号表）录制 + 对账 |
| `golden_routes.live2*.json` / `.diff.md` | 同上两份，但动作 description 已全部改写成只写"做什么"；`live`/`live-ctx` 是改写前的对照 |
| `golden_routes.live3*.json` / `.diff.md` | 口语带 id 之后的两份（q + 23 条原句 variants 都录，51 键） |
| `runner/cases/` | studio-evolve runner 案例目录（golden-to-cases 产出） |
| `runner/results.jsonl` · `metrics.json` | 人工转录路由 × 3 run 的结果与 growth_metrics 读数 |
| `runner/results.live*.jsonl` | 四份真路由各 1 run 的结果 |

## 路由读数（2026-10-23）

| 路由来源 | 动作描述 | 口语 | A（pass/可判） |
|---|---|---|---|
| 人工转录 | — | 带 id | 84/84（×3 run），23 条原句 variants 69/69 |
| 真 Qwen，无上下文 | 禁令式（原编译产物） | 无 id | 5/28 |
| 真 Qwen，带上下文 | 禁令式 | 无 id | 10/28 |
| 真 Qwen，无上下文 | 只写"做什么" | 无 id | 8/28 |
| 真 Qwen，带上下文 | 只写"做什么" | 无 id | 14/28 |
| 真 Qwen，无上下文 | 只写"做什么" | 带 id | **17/28** |
| 真 Qwen，带上下文 | 只写"做什么" | 带 id | **18/28** |

失败归因：

| 归因（28 条） | 禁令式·无ctx·无id | 禁令式·有ctx·无id | 做什么·无ctx·无id | 做什么·有ctx·无id | 做什么·无ctx·带id | 做什么·有ctx·带id |
|---|---|---|---|---|---|---|
| pass | 5 | 10 | 8 | 14 | 17 | 18 |
| clarify-禁令式/预判拒绝 | 7 | 7 | 3 | 1 | 2 | 3 |
| clarify-缺 id/参数或确认追问 | 7 | 6 | 8 | 8 | 2 | 1 |
| clarify-LLM 漏输出 confidence | 1 | 0 | 1 | 0 | 1 | 1 |
| advise（凭知识作答不查库） | 2 | 2 | 2 | 2 | 2 | 2 |
| query 0 行 | 4 | 2 | 3 | 2 | 1 | 1 |
| 选错对象/动作但预演通过 | 1 | 1 | 1 | 0 | 1 | 0 |
| 被别的规则拒 | 1 | 0 | 2 | 0 | 0 | 0 |
| 动作名多空格（引擎精确匹配） | 0 | 0 | 0 | 1 | 2 | 2 |

原句 variants（23 条，无 id）在同一次录制里：无上下文 5/23、有上下文 10/23 通过。

**读法。** rejected 口径：只算引擎层 reject。三步各解决一类失败：
① 描述只写"做什么" → 禁令式 clarify 归零（LLM 不再抢闸）；
② 口语带 id → 缺 id 的 clarify 归零，会话上下文的边际贡献只剩 1 条；
③ 剩下 10 条是三类稳定的 LLM / 引擎行为，与本体无关：
  - advise 2（目标区间、GMI 四前提）：Qwen 凭知识作答不查库；
  - 预判拒绝 2–3（营养师过期、P0099 未签同意、P0088 才 6 天）：口语自己把违规事实说出来了，Qwen 在路由层替规则拒了——这类 golden 的措辞本身在"钓"LLM；
  - 漏输出 confidence 1（生成方案草稿）、query 0 行 1（ReviewEvidence 查成 PlanSigned 多跳）、**动作名多空格 2**（"创建服务包 SKU"/"上架产品 SKU"，编译器精确匹配判清单外——引擎侧缺归一化，是现在最便宜的 2 分）。
