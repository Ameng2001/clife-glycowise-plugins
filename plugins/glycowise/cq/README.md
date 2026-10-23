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
| 真 Qwen，无上下文 | 只写"做什么" | 带 id | 17/28 → **19/28**（引擎动作名归一化后） |
| 真 Qwen，带上下文 | 只写"做什么" | 带 id | 18/28 → **20/28**（同上） |
| 真 Qwen，无上下文 | 只写"做什么" | 带 id · 去"钓" | **21/28**（live4） |
| 真 Qwen，带上下文 | 只写"做什么" | 带 id · 去"钓" | **23/28**（live4-ctx） |

`live4*`：golden #15/#19/#20 三条 rejected 口语去掉自带的违规事实（"才戴了 6 天"/"注册证过期了"/"还没签单独同意"），原句保留为 `variants[kind=with_fact]`；`session_context.txt` 里对应两行也改为中性（"新戴机患者 = P0088"、"厂商接口新接入的患者 = P0099"）。引擎 main 44d8ce1。无上下文那次录制 #06 两句 LLM 返回了畸形 where（list 而非 dict，TypeError），单独补录一次。

提案 P2–P4（R05 只在 G≥3.9 评估、R49 hard→soft、C19 转介豁免）合入生产后，用同一份 live4 / live4-ctx 录制重放：21/28、23/28 不变。

`live3*` 两行的结果文件按引擎 clife-onto-engine PR #86（commit c244013，动作名 NFKC + 去空白归一化）重算；该 PR 已于 2026-10-23 合并进 main（merge 44d8ce1）。

失败归因（live3 两列为引擎 c244013 重算后）：

| 归因（28 条） | 禁令式·无ctx·无id | 禁令式·有ctx·无id | 做什么·无ctx·无id | 做什么·有ctx·无id | 做什么·无ctx·带id | 做什么·有ctx·带id | 去钓·无ctx | 去钓·有ctx |
|---|---|---|---|---|---|---|---|---|
| pass | 5 | 10 | 8 | 14 | 19 | 20 | 21 | 23 |
| clarify-禁令式/预判拒绝 | 7 | 7 | 3 | 1 | 2 | 3 | 1 | 1 |
| clarify-缺 id/参数或确认追问 | 7 | 6 | 8 | 8 | 2 | 1 | 1 | 0 |
| clarify-LLM 漏输出 confidence | 1 | 0 | 1 | 0 | 1 | 1 | 1 | 1 |
| advise（凭知识作答不查库） | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| query 0 行 | 4 | 2 | 3 | 2 | 1 | 1 | 1 | 1 |
| 选错对象/动作但预演通过 | 1 | 1 | 1 | 0 | 1 | 0 | 1 | 0 |
| 被别的规则拒 | 1 | 0 | 2 | 0 | 0 | 0 | 0 | 0 |
| 动作名多空格（引擎精确匹配） | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |

去钓两列的 variants：无上下文 5/26、有上下文 12/26 通过；三条 `with_fact` 原句在两臂里全部仍被 Qwen 在路由层 clarify 掉（"注册证已过期，无法签发"/"尚未签署单独同意书"/"佩戴仅 6 天不足以分层"），三条去钓后的 q 在两臂里全部落到引擎 reject（R01 / D11a / C3）——同一规则、同一 seed，差别只在口语是否把违规事实说出来。

原句 variants（23 条，无 id）在同一次录制里：无上下文 5/23、有上下文 11/23 通过。

**读法。** rejected 口径：只算引擎层 reject。三步各解决一类失败：
① 描述只写"做什么" → 禁令式 clarify 归零（LLM 不再抢闸）；
② 口语带 id → 缺 id 的 clarify 归零，会话上下文的边际贡献只剩 1 条；
③ 剩下 10 条是三类稳定的 LLM / 引擎行为，与本体无关：
  - advise 2（目标区间、GMI 四前提）：Qwen 凭知识作答不查库；
  - 预判拒绝 2–3（营养师过期、P0099 未签同意、P0088 才 6 天）：口语自己把违规事实说出来了，Qwen 在路由层替规则拒了——这类 golden 的措辞本身在"钓"LLM。**已去钓（live4）**：三条改写后两臂全部落到引擎层 reject，无上下文 19→21、带上下文 20→23；剩下的 #25（"今天还没收到数据，日报先发今天平稳"）同属此类但违规事实就是题意本身，不改；
  - 漏输出 confidence 1（生成方案草稿）、query 0 行 1（ReviewEvidence 查成 PlanSigned 多跳）；动作名多空格 2（"创建服务包 SKU"/"上架产品 SKU"）已由引擎 PR #86 的归一化收回，两条都落到了规则层（R54、C1/C2）。
