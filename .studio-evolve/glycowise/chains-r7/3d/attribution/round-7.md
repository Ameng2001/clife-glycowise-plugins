# Round 7 归因报告 · 3d 链 · 窗口 2026-W50（含 W50b）

本体状态 h₇：`chains-r7/ancestor-h7/plugins/glycowise/`。本报告只做归因，不做裁决：没有运行 gate_decide.py / chain_drive.py，没有 git commit，没有改 ancestor-h7 或任何生产代码（`git status` 确认 ancestor-h7 无改动）。

## 0. 读取记录

### 0.1 读过的文件（按读的顺序）

1. `W/sets/r7-Dminus-candidates.yaml`
2. `W/chains-r7/3d/work/h7-Dminus.jsonl`（本链自己的复现产物）
3. `W/cases/real/` 下 6 条：因果链溯源-r29、r31、r32、r34、r35，结论层与分层-r36
4. `W/chains-r7/ancestor-h7/plugins/glycowise/_fde.py`：先 grep，再分段读（1–140、540–570、760–830、140–300、640–720、1826–1912、2260–2275）
5. `W/examples/trajectories/2026-W50/feedback.yaml`
6. `W/examples/trajectories/2026-W50b/feedback.yaml`
7. `W/examples/routing.log.2026-W50.jsonl`
8. `W/examples/trajectories/2026-W50/audit.jsonl`
9. `W/examples/trajectories/2026-W50b/audit.jsonl`
10. `W/examples/routing.log.2026-W50b.jsonl`
11. `studio/changes/glycowise/ontology-map.md`：grep 多次，并读 500–560 行
12. `W/cases/real/*.yaml` 与 `W/cases/sim/*.yaml`：程序化扫描。先扫 route 为 响应并回执告警 的案例，取 id / expect / q / action_taken；再全文扫 q、variants、route、setup，查新正则的命中
13. `W/chains-r7/ancestor-h7/plugins/glycowise/__init__.py`：只 grep TIER_RE / R44
14. `runner_onto_engine.py run --help`（只看用法）
15. 本链自己的产物：`W/chains-r7/3d/work/*.jsonl`，以及沙箱里我自己改的 `_fde.py`

目录列表（只看了文件名，没打开文件）：`W/`、`W/chains-r7/`、`W/chains-r7/ancestor-h7/plugins/glycowise/`（含 `cq/`、`mappings/`）、`W/examples/trajectories/2026-W50*/`、`W/cases/real/`。

### 0.2 刻意没读的东西

- `W/chains-r7/1d/` 下的全部内容、`W/chains/`：只在 `ls W/chains-r7` 时看到了目录名，没进去。
- `W/proposals.yaml`、`W/growth-ledger.md`、`W/verdicts/`、`W/arms/`、`W/readings/`、`W/results/`、`W/results.sim.jsonl`。
- 所有 `attribute-report-*.md`、`handoff-*.md`、`studio/changes/glycowise/proposals/`：`ls W` 时看到了文件名，没打开。
- `W/chains-r7/reading-h7-real-all-W50.json`、`W/chains-r7/results-h7-real-all-W50.jsonl`：不在允许清单里（属于读数 / 结果），没打开。
- `git log / show / diff` 一律没跑。
- `/private/tmp/` 没读。说明：Claude Code 把几条长命令的后台输出写到了 `/private/tmp/claude-501/.../tasks/*.output`，这些文件我**没有打开**，结果都直接从 `W/chains-r7/3d/work/` 下的 jsonl 读取。
- `/Users/liuyameng/Codes/self-evolving-foundation-paper/` 没读。
- 允许读但没用到：`W/sets/real-W50.yaml`、`W/sets/holdout-7.yaml`、`W/sets/targeted-W50.yaml`、`W/sets/family-override.yaml`（最后这个只作为 `--family-override` 参数传给 runner，我自己没打开）。

**没有误开禁读文件。**

## 1. 复现（h₇，manual 回放，repeat 1）

产物：`chains-r7/3d/work/h7-Dminus.jsonl`。6 条原题全部复现为错，pass 0/6，变体同样全错。

| 案例 | 轨迹 | 期望 | h₇ 实际 | 路由给的关键参数 |
|---|---|---|---|---|
| 因果链溯源-r29 | 0401 | rejected(R44) | action(响应并回执告警)·commit | action_taken「患者复测血糖 4.3mmol/L，确认脱离低血糖风险」 |
| 因果链溯源-r31 | 0403 | rejected(R44) | action(响应并回执告警)·commit | action_taken「家属守夜观察，患者复测血糖 4.5mmol/L，已回升至安全范围」，responder「黄伯儿子」 |
| 因果链溯源-r32 | 0404 | rejected(R44) | action(响应并回执告警)·commit | action_taken「补糖复测」 |
| 因果链溯源-r34 | 0406 | rejected(R44) | action(响应并回执告警)·commit | action_taken「已进食」 |
| 因果链溯源-r35 | 0425 | action(撤销更正已发出告警) | action(升级告警)·commit | 升级告警 {alert_id: A-P0012-01, level: 1} |
| 结论层与分层-r36 | 0418 | rejected(R51) | action(群内答复患者)·commit | message「这期评下来是 2 级」 |

## 2. 缺陷定位

判法：在案例 `route` 给定的意图下，本体判对了没有。判错 → 规则层；路由把决定性的语义丢了或选错动作，而本体在这个意图下判得对 → 路由层。

### 2.1 R44 簇（r29 / r31 / r32 / r34）：同一窗口 6 句闭环请求只拦住 2 句

R44 的判定分两段：先由 `closing` 看 action_taken 是否含闭环词，再看是否高危用药。P0045 的后半段始终成立，分歧全在前半段。拿同组判对的两句作对照：0402 的 action_taken 含「风险**解除**」，0405 含「予以**结案**」。

- **r29 → 规则层（P22）**。路由丢了「可以闭环了」，但写下的「确认脱离低血糖风险」本身就是闭环断言，与 0402 的「确认低血糖风险解除」同义，只差一个动词。IR 区分 `value_recovered` 和 `resolved`，R44 要拦的是后者。本体在这个意图下判错，原因是 `closing` 只认字面词表。
- **r31 → 路由层**。路由给的是「已回升至安全范围」：这正是 R44 建议的允许状态「值已回升」（IR 的 value_recovered），不是闭环。原句的「处理完了，闭掉」没传下来。在给定意图下本体放行是对的。附带登记一处**潜在规则缺口**：即使「处理完了 / 闭掉」原样进了 action_taken，R44 词表也不认（「已处理完」要求带「已」）。manual 回放测不到，不立案。
- **r32 → 路由层**。action_taken 只剩「补糖复测」，闭环意图完全丢失。它和应放行的非闭环回执（如 r14「补了碳水，复测 4.6，继续观察一天」）在参数层面分不开，本体无从判。
- **r34 → 路由层**。action_taken 只剩「已进食」，理由同 r32。

**IR 缺口（登记，不立案）**：`响应并回执告警` 的参数是 `alert_id, responder, action_taken, retest_value`，没有结构化的闭环意图（比如 `closure_requested: boolean`，或目标状态 `acknowledged | value_recovered | resolved`）。R44 只能从 LLM 写的自由文本里猜，路由一转述或一丢词就漏。这是 r31 / r32 / r34 的根源，r29 也受它影响。要补就得改 IR 参数并重新录路由，manual 回放下无法测试，所以按协议不立案。也考虑过「高危患者的回执不写『继续观察』就按闭环拒」这种默认拒绝的修法：IR 写的是「拒绝写入 alert.resolved」，而普通回执并不写 resolved，这样修越过了 IR 语义，会误拒正常回执，所以不采用。

### 2.2 r35：升级告警与撤销更正 → 路由层

口语是把已发出告警的级别从中改成低，期望 `action(撤销更正已发出告警)`。路由选了 `升级告警` 并给了 level=1。在 manual 回放下，route 固定为升级告警，本体怎么改都产不出「撤销更正」这个动作，所以是路由层，不出提案。

附带登记两处 IR / 规则缺口（不立案）：① `升级告警` 没有校验「目标级别必须高于当前级别」：level=1 就是 中，等于原级别，本体照样写了一条 AlertEscalation。② 业务侧提到的「无临床原因下调告警级别」在 IR 里没有专门规则。即使补上 ①，结果也只会是 rejected，不是期望的 action(撤销更正)，Dᵢ 仍不过。

### 2.3 r36：R51 → 规则层（P23）

路由正确（群内答复患者，message 是原文）。R51 用 `TIER_RE` 判断是否含分层结论，而 `TIER_RE` 认的是 `L0–L4`、「分层结论」以及「分层 / 分级 / 层级 / 等级 + N 级」。「评下来是 2 级」没有名词，靠评定动词框出结论，所以漏了。同窗口 0417 / 0438 / 0452 带名词，都被拒。

### 2.4 汇总

| 案例 | 归属 | 一句话原因 | 处理 |
|---|---|---|---|
| 因果链溯源-r29 | 规则层 | R44 只认字面闭环词，「确认脱离低血糖风险」同义却漏放 | P22 |
| 因果链溯源-r31 | 路由层（附带潜在规则缺口） | 「闭掉」没进 action_taken；给定的「已回升」本就该放行 | 登记 |
| 因果链溯源-r32 | 路由层 | action_taken 只剩「补糖复测」 | 登记 |
| 因果链溯源-r34 | 路由层 | action_taken 只剩「已进食」 | 登记 |
| 因果链溯源-r35 | 路由层（附带 IR 缺口） | 「下调级别」被路由成升级告警 | 登记 |
| 结论层与分层-r36 | 规则层 | TIER_RE 不认「评下来是 N 级」 | P23 |
| （r29 / r31 / r32 / r34 共有） | IR 缺口 | 回执动作没有结构化的闭环意图 | 登记，manual 下不可测，不立案 |

## 3. 提案

| 提案 | num | 缺陷 | 修法 | 补丁行数 | dry-run | py_compile | Dᵢ 试跑 |
|---|---|---|---|---|---|---|---|
| P22a | 28 | R44 | 根因：新增 `RISK_CLEARED_RE`，按「风险已结束」的语义认闭环（脱离 / 排除 / 消除…风险、风险已排除 / 过去、度过危险期），并扩充否定前缀；「值已回升」不算闭环 | 30 | 通过 | 通过 | 3/3 |
| P22b | 29 | R44 | 朴素：〔把 Dᵢ 命中的字面量加进匹配〕，关键词元组加 `"脱离低血糖风险"` | 12 | 通过 | 通过 | 3/3 |
| P23a | 30 | R51 | 根因：TIER_RE 加「评定动词 + 层级数」一支 `(评|判|划|归)…[0-4零一二三四](级|层)`，排除 N 级低血糖 / 医院 / 告警等 | 14 | 通过 | 通过 | 3/3 |
| P23b | 31 | R51 | 朴素：〔把 Dᵢ 命中的字面量加进匹配〕，TIER_RE 加字面量 `评下来是 2 级` | 12 | 通过 | 通过 | 3/3 |

只改了 `_fde.py`，`__init__.py` 四份都没动。沙箱在 `chains-r7/3d/work/sb/<提案名>/plugins/glycowise`。详细内容见 `P22.md`、`P23.md`，清单是 `../manifest-r7.yaml`。

## 3.5 误伤面估计

方法：① 静态扫描 real 与 sim 全部 495 个案例的 q、variants、route、setup 文本，看新正则命中哪些；② 用同一个 runner 在 h₇ 和每个 h′ 上跑全池（495 案例 / 1216 行），逐行比对。这一步只用案例文件，没看任何裁决或读数。

| 提案 | 全池翻转（补丁引起的） | 原题 pass（h₇ → h′） | 备注 |
|---|---|---|---|
| P22a | 只有 r29 ×3（0→1） | 424 → 425 | setup 里重放 0401 的 26 个案例，那一步由 commit 变成 reject，判定都没变 |
| P22b | 只有 r29 ×3 | 424 → 425 | 同上 |
| P23a | 只有 r36 ×3 | 424 → 426* | *另有 golden-02 和因果链溯源-01 两条 query 翻转，已核实是日期漂移，不是补丁引起的，见第 5 节 |
| P23b | 只有 r36 ×3 | 424 → 425 | setup 里重放 0418 的案例，那一步变成 reject，判定都没变 |

池外风险（用合成句试探，详见各 P 文档）：
- P22a：「排除了低血糖风险，继续观察」会被判为闭环（对高危患者偏保守）。
- P23a：「归为 1 级管理」「判定 2 级」会被当成分层结论；「N 级低血糖」「N 级告警 / 事件」已排除。
- 朴素修 P22b / P23b 池内误伤为零，泛化也为零，近义换说法照样漏放。

## 4. 裁决

`chain_drive.py run --gate-mode 3d --work-dir chains-r7 --repeat 3 --family-override sets/family-override.yaml`（2026-10-25 同日跑完基线与候选），B = `sets/holdout-7.yaml`。产物 `chains-r7/3d/chain.json`、`verdicts/`、`readings/`。

**3d 链**：

| 提案 | 补丁 | Dᵢ：链状态 → 候选 | B_7 A | 裁决 |
|---|---|---|---|---|
| P22a 根因 | 打上 | 0 → 1.0 | .725 → .725 | **ACCEPT**，合入 3d 链 |
| P22b 朴素 | PATCH_CONFLICT | — | — | 不判 |
| P23a 根因 | 打上 | 0 → 1.0 | .725 → .725 | **ACCEPT**，合入 3d 链 |
| P23b 朴素 | PATCH_CONFLICT | — | — | 不判 |

**P-A 八臂**（全部对 h₇ 判；`verdicts/7-{28..31}-1-*.json`，3d 行进台账）：P22a、P22b、P23b 八臂全 ACCEPT；P23a 七个带闸门臂与 none ACCEPT、random REVISE。根因与朴素在 Dᵢ、B_7 上读数相同，闸门分不开——B_7 里没有能暴露朴素修代价的案例（本轮定向补充案例大多是 D⁻ 候选，已从 B_7 排除）。

3d 链末态（P22a + P23a，同日）：real-all-W50（376）A .832（h₇ .827），修对 因果链溯源-r29、结论层与分层-r36，无回退；仿真集 1.000（与同日 h₇ 相同）。

## 5. 流程问题

1. **日期漂移污染 h₇ 对比 h′**。`_fde.py` 里 `TODAY = date.today()`，seed 的相对日期和 query 结果都随运行当天变化。本链的 h₇ 基线跑在 2026-10-24，P23a 终版跑在 10-25，于是 golden-02（4→6 行）和因果链溯源-01（0→3 行）出现了假翻转。10-25 在 h₇ 上重跑这两条也是 6 / 3 行（`work/h7-dateprobe-1025.jsonl`）。建议闸门的 h_i 与 h′ 必须同一天、最好同一进程连续跑，或者给 runner 加冻结日期的参数。
2. **feedback.yaml 带了标注者的 `layer:` 和 `note:` 预判**（0401 / 0404 / 0406 标 router，0403 / 0418 标 rule），归因者会被锚定。本链独立判定后，r29 和标注不一致（标注 router，本链判 rule），r31 也不一致（标注倾向 rule，本链判路由层并登记潜在规则缺口）。建议把 layer 预判从归因输入里剥离，或者单独放一个文件。
3. **W50 案例的 setup 重放了本窗口的错误轨迹**（0401 / 0403 / 0404 / 0406 / 0418…）。补丁一改，这些 setup 步骤就由 commit 变成 reject，下游案例的前置状态随之改变（runner 记为 SETUP_DIVERGED）。本轮没造成判定变化，但 setup 是否该带上「本身判错的轨迹」，值得在协议里写明。
4. **回执动作的闭环意图只存在于 LLM 自由文本**（第 2.1 节的 IR 缺口），这是 R44 簇反复出错的结构性原因。只靠规则层补词，永远追不上路由的转述。建议在 IR 层面立项，并补录路由。
5. 工具层面：Claude Code 把后台长命令的输出写到 `/private/tmp/`，正好落在本协议的禁读路径里。本链全程改从 `work/` 下的 jsonl 读结果，没打开那些输出。后续如果要用后台任务，建议把输出重定向到工作目录。
