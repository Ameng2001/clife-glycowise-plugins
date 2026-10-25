# Round 8 归因报告 · 1d 链 · 2026-W51

- 归因起点：h_s = h₈（formal 起点），`chains-formal/ancestor-s/plugins/glycowise`
- 对象：`sets/r8-Dminus-candidates.yaml` 中 W51 业务侧标 wrong 的 10 条
- 回放口径：`runner_onto_engine.py run --router manual --recordings plugins/glycowise/cq/all_routes.json --family-override sets/family-override.yaml --as-of 2026-10-25 --repeat 1`，工作目录 `chains-formal/1d/work`
- 角色边界：只做归因，不裁决。没有运行 gate_decide.py / chain_drive.py，没有 git commit，没有改生产代码（`plugins/` 与 `ancestor-s/` 都没动，改动只在 `chains-formal/1d/work/sb/` 沙箱里）。

## 0. 读取清单

### 0.1 读过的文件
仓库根 `/Users/liuyameng/Codes/clife-glycowise-plugins`，`W = .studio-evolve/glycowise`。

- 本链状态：`W/chains-formal/ancestor-s/plugins/glycowise/` 下的 `plugin.yaml`（头 20 行）、`__init__.py`（D9 / R44 / C9 的声明段与 RULE_META）、`_fde.py`（常量区、text_of / product_mention / sentences 等工具函数、D8 / D9 / D10 / D11 / R32 / C22 / R44 规则，以及 审核输出内容 / 生成产品推荐 / 响应并回执告警 / 群内答复患者 handler、seed 里的 OutboundContent 一行）；`cq/all_routes.json` 只作 `--recordings` 传给 runner，并用来查案例的录制路由。
- IR：`studio/changes/glycowise/ontology-map.md`，grep 了 D9 / R44 / 响应并回执告警 相关行，读了 §CQ 段（505–545 行）。
- W51 窗口：`W/examples/trajectories/2026-W51/feedback.yaml`（全部 49 条的标签与判语，重点看 0506 / 0507 / 0509 / 0517）、`W/examples/trajectories/2026-W51/audit.jsonl`（0506 / 0508 / 0518 / 0520 四行）、`W/examples/routing.log.2026-W51.jsonl`（0518 / 0520 / 0529 / 0532 四行）。
- 案例：`W/cases/real/` 里 10 条 wrong 的全文；按动作扫了 `W/cases/real` + `W/cases/sim` 全部案例的 id / expect / route.params；读了 产品与机构合规-r35 / r36 / r38 的 label.answer 与 expect_not。
- 集合：`W/sets/r8-Dminus-candidates.yaml`、`real-W51.yaml`、`targeted-W51.yaml`、`holdout-8.yaml`（只取 id 做成员查询）、`family-override.yaml`（头部注释与 grep）。
- 脚本：`/Users/liuyameng/Codes/astra-studio-plugins/studio-evolve/scripts/runner_onto_engine.py`（模块说明与参数定义）。
- **超出允许清单的读取（如实登记）**：
  1. `W/sets/P19-Di.yaml`：为对齐 Dᵢ 文件格式读了全文（只有 `ids: [结论层与分层-r21]` 一行）。它不在允许清单里，也不在禁读清单里。
  2. 引擎 `/Users/liuyameng/Codes/onto-fundary-plugins/clife_onto_engine/`：grep 了 `SOFT|would_commit`，确认 soft 违规不阻断 commit（`kernel/action_engine.py:193`），用来判断朴素规则 4 能不能用。
  3. `git status --short .studio-evolve/glycowise/chains-formal`：只确认没有误写 ancestor-s，不是 log / show / diff。
- 目录列表：`ls W` 与 `ls W/sets` 的输出里出现了禁读文件的**文件名**（attribute-report-*.md、handoff-*.md、proposals.yaml、growth-ledger.md、verdicts/、arms/、readings/、results/，以及往轮的 P*-Di.yaml）。只看到了名字，一个都没打开。

### 0.2 刻意没读的
- `W/chains-formal/3d/`（`ls W/chains-formal` 显示目前没有这个目录）、`W/chains-r7/`、`W/chains/` 下的一切；
- `W/proposals.yaml`、`W/growth-ledger.md`、`W/verdicts/`、`W/arms/`、`W/readings/`、`W/results/`、`W/results.sim.jsonl`；
- 所有 `attribute-report-*.md`、`handoff-*.md`（包括 handoff-round8*.W51.md）、`studio/changes/glycowise/proposals/`；
- `W/formal-runbook.md`、`W/protocol/`、`W/README.md`、`W/config.yaml`（不在允许清单里，没打开；manifest 格式是我按任务书自拟的）；
- 任何 `git log` / `git show` / `git diff` 输出；`/private/tmp/` 下的任何目录；论文仓库。

**有没有误开禁读文件：没有。** 超出允许清单的 3 处读取见 0.1。

## 1. 复现（h_s）

10 条原题全挂（可判 10 / 10），含变体 30 行全挂。结果在 `chains-formal/1d/work/repro-h_s.jsonl`。

| 案例 | trace | 期望 | h_s 实际 |
|---|---|---|---|
| 产品与机构合规-r41 | 0508 | rejected(D9) | action(生成产品推荐)·commit |
| 产品与机构合规-r43 | 0510 | rejected(D9) | commit |
| 产品与机构合规-r44 | 0511 | rejected(D9) | commit |
| 产品与机构合规-r45 | 0539 | rejected(D9) | commit |
| 因果链溯源-r37 | 0506 | action(响应并回执告警) | reject [R44] |
| 因果链溯源-r39 | 0516 | action(响应并回执告警) | reject [R44] |
| 高血糖与波动-r34 | 0518 | action(审核输出内容) | reject [D8, C22] |
| 高血糖与波动-r36 | 0520 | action(审核输出内容) | reject [C22] |
| 高血糖与波动-r39 | 0529 | action(审核输出内容) | reject [C22] |
| 高血糖与波动-r41 | 0532 | action(审核输出内容) | reject [C22] |

## 2. 逐条归属

| 案例 | 归属 | 原因（一句话） |
|---|---|---|
| 产品与机构合规-r41 | 规则层 → P24 | 「饭后血糖不往上冲」是防止升高方向的血糖作用声称，D9 的 EFFICACY_RE 只收「降 / 稳住 / 不升」等字面搭配，漏拦。 |
| 产品与机构合规-r43 | 规则层 → P24 | 「见效快、一周就能看到」是疗效 + 起效时间的医疗用语，EFFICACY_RE 没有疗效 / 起效类，漏拦。 |
| 产品与机构合规-r44 | 规则层 → P24 | 「跟着三餐一起吃，效果更好」在控糖语境里是功效暗示，EFFICACY_RE 没有「效果」类，漏拦。 |
| 产品与机构合规-r45 | 规则层 → P24 | 「餐后不冲高」以时段（餐后）为主语、防升高为谓词，主语与谓词都不在 EFFICACY_RE 里，漏拦。 |
| 因果链溯源-r37 | 规则层 → P25 | R44 的 RISK_CLEARED_RE 把「已经脱离风险」的措辞当成闭环，没看同一回执里的「先别结案、明早再看一次」（value_recovered），整条误拒。 |
| 因果链溯源-r39 | 规则层 → P25 | 同上：「风险排除」被当成闭环，忽略了「继续观察 24 小时」。 |
| 高血糖与波动-r34 | 路由层（登记）+ IR 缺口（登记，不立案） | 口语送审的是一段新写的文本，路由却填了已有内容 c-P0012-plan-02（含「逆转 / 停药」），引擎审错了对象；审核输出内容 只收 content_id，承载不了口语里的文本。 |
| 高血糖与波动-r36 | 路由层（登记）+ IR 缺口（登记，不立案） | 路由填了租户里不存在的 c-P0012-breakfast-01，C22 因空对象读不到免责标记才拒，没审到「鸡蛋加燕麦」这段建议。 |
| 高血糖与波动-r39 | 路由层（登记）+ IR 缺口（登记，不立案） | 同上，c-P0023-dinner-01 不存在。 |
| 高血糖与波动-r41 | 路由层（登记）+ IR 缺口（登记，不立案） | 同上，c-P0088-exercise-01 不存在。 |

## 3. 提案

| 提案 | proposal | 类型 | 修法（一句话） | 补丁行数 | dry-run | py_compile | Dᵢ |
|---|---|---|---|---|---|---|---|
| P24a | 32 | 根因 | 按法条语义把功效声称归成两类（作用声称不分方向、含时段主语；疗效 / 起效用语），改写 EFFICACY_RE | 28（+18 −1） | 成功 | 通过 | 4/4（行 12/12） |
| P24b1 | 33 | 朴素·规则 5 | 把 Dᵢ 原句字面量并进 EFFICACY_RE | 12（+2 −1） | 成功 | 通过 | 4/4（行 12/12） |
| P25a | 34 | 根因 | 「风险已结束」措辞只作闭环推断；回执否定了闭环或保留观察窗时不判闭环，显式闭环词照拦 | 34（+11 −3） | 成功 | 通过 | 2/2（行 6/6） |
| P25b1 | 35 | 朴素·规则 3 | 删掉 RISK_CLEARED_RE 推断分支 | 12（+1 −2） | 成功 | 通过 | 2/2（行 6/6） |
| P25b2 | 36 | 朴素·规则 4 | R44 hard → soft | 11（+1 −1） | 成功 | 通过 | 2/2（行 6/6） |
| P25b3 | 37 | 朴素·规则 5 | Dᵢ 原句片段进放行匹配 | 12（+3 −0） | 成功 | 通过 | 2/2（行 6/6） |

不适用的机械规则：P24 的规则 1–4（漏拦缺陷，放宽 / 跳过 / 删分支 / 降级都只会更松，D9 也没有阈值或命中分支）；P25 的规则 1、2（R44 没有数值阈值，Dᵢ 参数齐全）。理由逐条写在 P24.md / P25.md §4。

链上只走根因修：`manifest-r8.yaml` 只列 P24a、P25a。朴素修列在 `pa-extra-r8.yaml`，只进 P-A。P24a 与 P25a 改的是 `_fde.py` 里不相交的两段，先后打上可以干净合入（已试过）。

## 4. 裁决

链上（1d 判定式，`chains-formal/1d/chain.json`）：接受 P24a, P25a，末态 real-all-W51 .842 / holdout-8 .840 / 仿真集 1.000（h_s：.828 / .840）。P-A 八臂结果见 `chains-formal/compare-r8.md` ①。

## 5. 误伤面（只用案例文件，不看任何裁决）

全部 543 条案例（含变体 1343 行），以 h_s 为基线，h_s 原题通过 465：

| 提案 | 原题通过 | 由挂变过 | 由过变挂 | 由过变挂的案例 |
|---|---|---|---|---|
| P24a | 469 | 4（Dᵢ） | 0 | —（r35 / r36 / r38 在 C4 之外多响 D9，判语写明「D9 也该拦」，通过不变） |
| P24b1 | 469 | 4 | 0 | —（同上） |
| P25a | 467 | 2 | 0 | — |
| P25b1 | 466 | 2 | 1 | 因果链溯源-r29（holdout-8） |
| P25b2 | 461 | 2 | 6 | golden-23；低血糖安全-r02、因果链溯源-r18 / r29 / r30 / r33（holdout-8） |
| P25b3 | 467 | 2 | 0 | — |

在案例集上，根因修跟字面量朴素修（P24a 对 P24b1、P25a 对 P25b3）**分不开**。归因者自拟的探针（`work/probe/cases/`，看过 Dᵢ 之后写的，只算探索性）上：P24a 6/6 + 5/5，P24b1 1/6 + 5/5；P25a 7/7，P25b3 4/7（跟 h_s 一样）。细节见 P24.md / P25.md §6。

## 6. 登记（不立案）

### 6.1 路由层
- **R-W51-1：审核输出内容 的 content_id 张冠李戴 / 凭空编造**（0518 / 0520 / 0529 / 0532）。口语送审的是一段刚写的文本，LLM 路由要么拿租户里已有的另一条内容充数（0518 → c-P0012-plan-02），要么按命名习惯编一个不存在的 id（0520 / 0529 / 0532）。路由校验只查参数齐不齐，不查 content_id 在不在。

### 6.2 IR 缺口
- **I-W51-1：审核输出内容 无法承载口语里的待审文本。** IR 签名是 `content_id:required, content_type:required`，没有正文参数，也没有「先登记一条 OutboundContent 草稿再送审」的前置动作。业务侧期望「审口语里的文本、进合规官 HIL」在现有 IR 下没有合法路由。manual 回放按窗口 route（只带 content_id）走，加了参数或动作也测不到，**按约定不立案**。
- **I-W51-2（相关，顺带登记）：审核输出内容 对不存在的 content_id 没有引用完整性检查。** 现在 C22 以「缺免责尾注」拒空对象，拒因对审核人有误导。修了它，这 3 条照样是拒（只是拒因变了），达不到期望的 commit，所以也不立案。
- **I-W51-3（IR 文档滞后）：ontology-map §D9 的 check 列仍是「not (产品推荐 and (同句分层 or 同句缓解))」。** 功效声称是 P16a 按规则名和法条补进实现的，IR 文字没跟上。P24a 进一步把功效声称的语义类写进实现注释，建议裁决方决定要不要回写 IR。

### 6.3 不在 D⁻ 内但看到的
- 0517（partial，未落案例）：R44 方向对，但路由把「现在没有低血糖风险了」写成「患者自述无低血糖症状」，凭空加了来源。属路由层，跟 R-W51-1 同类（参数内容失真），一并登记。

## 7. 流程问题

1. **「本链当前状态」不在 1d 目录下。** 任务书把 1d 链的 h_s 指向 `chains-formal/ancestor-s/`，而 `chains-formal/1d/` 归因开始时不存在（work / attribution 都是我新建的）。建议在 `chains-formal/1d/` 放一个指向 h_s 的 README 或 state 文件，免得两条链共用 ancestor-s 时有人误改。
2. **案例变体测不到规则泛化。** 带 route 的真实案例，q 和全部 variants 都走同一份路由，pitch / action_taken 逐字相同，所以「含变体 12/12」跟「原题 4/4」证据量一样。根因修与字面量朴素修因此在案例集上无从区分（P24a/P24b1、P25a/P25b3 逐行同结果）。建议外关卡留出集里放**改写过参数**的同义句（targeted 那种），且由没看过 Dᵢ 的人来写。
3. **targeted-W51 与 Dᵢ 重叠。** targeted-W51 的 r41/r43/r44/r45/r37/r39 正是本轮 Dᵢ。按集合注释，它们「只评 round ≥ 8 的提案」，裁决时请确认这几条不会被同时算作 Dᵢ 通过和外关卡通过。
4. **runner `--router manual` 强制要 `--recordings`**，哪怕所有案例都带 route。跑探针时只好传一个空 `{}`。可以放宽成「全部案例带 route 时可省」。
5. **SETUP_DIVERGED 计数随候选变动**（P24：529 → 851；P25b1/b2：529 → 459）。原因是后序案例的 setup 里含有本轮正被修的前序动作（0508 / 0510 / 0511 推荐；R44 相关回执）。不影响判定，但读数里这一项不能拿来比较状态好坏。
6. **r34 的期望本身有张力。** 判语说「文本缺免责尾注（C22）应在送审时补上」，期望却是 `action(审核输出内容)` commit。即使将来 IR 能承载正文，C22 是 hard，缺尾注的文本照样会拒。建议业务侧澄清：期望是「送审时自动补尾注后放行」，还是「C22 拒、但审对对象」。
