# glycowise 黄金问题集（CQ）与路由录制

| 文件 | 是什么 |
|---|---|
| `golden.yaml` | 28 条黄金问题（7 query / 6 action / 15 rejected），由 ontology-map §7 编译 |
| `make_golden_routes.py` → `golden_routes.json` | **人工转录**的理想路由（ReplayLLMClient 格式），衡量"规则 + 回写"层 |
| `record_live_routes.py` | 真 Qwen 录制端。`--pin-ip` 只在本进程钉 DNS（绕本机代理 fake-ip 误路由，不改系统设置）；`--context-file` 把会话上下文作 memory_text 喂给编译器 |
| `golden_routes.live.json` / `.live.diff.md` | 真 Qwen（qwen3.5-plus，role=医师）**无会话上下文**录制 + 与人工转录对账 |
| `golden_routes.live-ctx.json` / `.live-ctx.diff.md` | 真 Qwen **带会话上下文**（`session_context.txt`：患者/告警/内容 id 对号表）录制 + 对账 |
| `golden_routes.live2*.json` / `.diff.md` | 同上两份，但动作 description 已全部改写成只写"做什么"（commit 见 git log）；`live`/`live-ctx` 是改写前的对照 |
| `runner/cases/` | studio-evolve runner 案例目录（golden-to-cases 产出） |
| `runner/results.jsonl` · `metrics.json` | 人工转录路由 × 3 run 的结果与 growth_metrics 读数 |
| `runner/results.live*.jsonl` | 四份真路由各 1 run 的结果 |

## 路由读数（2026-10-23）

| 路由来源 | 动作描述 | A（pass/可判） |
|---|---|---|
| 人工转录 | — | 84/84（×3 run） |
| 真 Qwen，无上下文 | 禁令式（原编译产物） | 5/28 |
| 真 Qwen，带上下文 | 禁令式 | 10/28 |
| 真 Qwen，无上下文 | 只写"做什么" | 8/28 |
| 真 Qwen，带上下文 | 只写"做什么" | **14/28** |

失败归因（每格 = 28 条里的条数）：

| 归因 | 禁令式描述·无上下文 | 禁令式描述·有上下文 | 只写做什么·无上下文 | 只写做什么·有上下文 |
|---|---|---|---|---|
| pass | 5 | 10 | 8 | 14 |
| clarify-禁令式（系统规则禁止/您确认要…） | 7 | 6 | 2 | 0 |
| clarify-缺 id/参数 | 8 | 7 | 10 | 9 |
| advise（凭知识作答不查库） | 2 | 2 | 2 | 2 |
| query 0 行 | 4 | 2 | 3 | 2 |
| 选错对象/动作但预演通过 | 1 | 1 | 1 | 0 |
| 被别的规则拒 | 1 | 0 | 2 | 0 |
| 动作名写错（清单外） | 0 | 0 | 0 | 1 |

**读法。** rejected 口径定为"只算引擎层 reject"。① 把 63 条动作 description 从禁令（"器械一律拒绝"、"仅医师可放宽"）改成只写"做什么"后，
禁令式 clarify 基本消失，LLM 不再在路由层抢闸，剩下的 clarify 几乎全是口语缺 id / 参数——这是 golden 口语本身的省略，不是路由错。
② 会话上下文把缺 id 的 clarify 再砍掉一半，但 Qwen 会转成"您是指 P0088 吗？"式的确认追问，仍判 clarify。
③ 两条 advise（目标区间、GMI 四前提）与几条 query 0 行（患者名当 id、`now-14d` 字面量、ReviewEvidence 查成 PlanSigned 多跳）是稳定的 LLM 行为，与描述无关。
④ 一条"上架产品 SKU"（多了空格）被编译器判清单外：动作名精确匹配，缺归一化——引擎侧问题，记在这里不在本仓库修。

把 rejected 用例全部打到引擎规则层，还需要 golden 口语自带 id（或 runner 支持多轮把 clarify 的追问补答），这是下一步。
