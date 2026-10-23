# glycowise 黄金问题集（CQ）与路由录制

| 文件 | 是什么 |
|---|---|
| `golden.yaml` | 28 条黄金问题（7 query / 6 action / 15 rejected），由 ontology-map §7 编译 |
| `make_golden_routes.py` → `golden_routes.json` | **人工转录**的理想路由（ReplayLLMClient 格式），衡量"规则 + 回写"层 |
| `record_live_routes.py` | 真 Qwen 录制端。`--pin-ip` 只在本进程钉 DNS（绕本机代理 fake-ip 误路由，不改系统设置）；`--context-file` 把会话上下文作 memory_text 喂给编译器 |
| `golden_routes.live.json` / `.live.diff.md` | 真 Qwen（qwen3.5-plus，role=医师）**无会话上下文**录制 + 与人工转录对账 |
| `golden_routes.live-ctx.json` / `.live-ctx.diff.md` | 真 Qwen **带会话上下文**（`session_context.txt`：患者/告警/内容 id 对号表）录制 + 对账 |
| `runner/cases/` | studio-evolve runner 案例目录（golden-to-cases 产出） |
| `runner/results.jsonl` · `metrics.json` | 人工转录路由 × 3 run 的结果与 growth_metrics 读数 |
| `runner/results.live.jsonl` · `results.live-ctx.jsonl` | 两份真路由各 1 run 的结果 |

## 三份路由的读数（2026-10-23）

| 路由来源 | A（pass/可判） | 失败归因 |
|---|---|---|
| 人工转录 | 84/84（×3 run） | — |
| 真 Qwen，无上下文 | 5/28 | clarify 15（LLM 在路由层自行拒绝或追问 id）、query 0 行 4（患者名当 id、字段猜错）、advise 2（口径问题直接作答不查库）、选错动作 1（收紧→放宽，已改描述）、对象不符 1 |
| 真 Qwen，带上下文 | 10/28 | clarify 13、query 0 行 2、advise 2、选错对象 1 |

**主要发现：LLM 抢闸。** 15 条 rejected 用例里，真 Qwen 大多在路由层就以 clarify 拒掉（"系统规则禁止…您确认要强制执行吗？"），
引擎的 HARD 规则根本没被评到。原因是 manifest 里暴露给 LLM 的动作 `description` 写成了禁令（"器械一律拒绝"、"仅医师可放宽"），
LLM 把闸门抢在手里。这恰好反过来说明：**本体规则层能稳定裁决的用例，LLM 路由层并不能稳定复现**——A=1.0 衡量的只有规则层。
后续两个方向：① 动作 description 只写"做什么"，把"能不能做"留给规则（可一次性改写并重录对比）；② golden 的 rejected 用例应把
"路由层拒绝"也算作一种通过口径（engine 层 reject ∪ 路由层 clarify-with-reason），否则 A 低估了系统整体的拒绝能力。

两条 advise（Q4 目标区间、Q5 GMI 四前提）是 LLM 基于知识直接作答——不查库但答案方向正确；golden 把它们标为 query 是口径之争。
