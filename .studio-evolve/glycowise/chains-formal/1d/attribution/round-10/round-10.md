# round 10 · 1d 链归因报告（窗口 2026-W53）

归因者只做归因、不做裁决：没有运行 gate_decide.py / chain_drive.py，没有 git commit，没有改生产代码（本链 `state/` 与仓库 `plugins/` 均未动；所有修改都在 `work-r10/sb/` 沙箱里）。

## 0. 读过的文件与刻意没读的东西

**读过（W = `.studio-evolve/glycowise`）**

- 本链当前状态 `W/chains-formal/1d/state/plugins/glycowise/`：`__init__.py`（规则 / 动作注册、guards / post_rules）、`_fde.py`（规则与 handler 实现，按需分段读）；`cq/all_routes.json` 只作 `--recordings` 传给 runner，未逐条读。
- IR `studio/changes/glycowise/ontology-map.md`：只 grep 了 R03a / R04a / R05 / R46 / R34 / R24b / R01 / R32 / D9 / R51 / C6 / C20 / R54 的规则行与相关动作行。
- `W/examples/trajectories/2026-W53/feedback.yaml`：全部 wrong 条目与开头几条 correct 条目。
- 案例：`W/cases/real/` 中 37 条 D⁻ 候选的 q / expect / route / expect_not / expect_state / setup（低血糖安全-r47 全文、参考与配置-r49 全文），另读参考与配置-r52（P34a 误伤分析）；`cases/real` 与 `cases/sim` 全部案例作为 runner 输入参与误伤回放（未逐条阅读）。
- 集合：`W/sets/r10-Dminus-candidates.yaml`、`W/sets/targeted-W53.yaml`、`W/sets/family-override.yaml`（全文）、`W/sets/holdout-10.yaml`（只读 ids，用于在误伤表里标注哪些回退落在 holdout 内）。
- 脚本：`/Users/liuyameng/Codes/astra-studio-plugins/studio-evolve/scripts/runner_onto_engine.py` 的 `--help`、模块文档串、`cmd_run` 中读 `--cases-file` 的几行（确认 Dᵢ 文件可用 `source_cases` 键）。
- 引擎（不在允许清单内，也不在禁读清单内，如实列出）：`/Users/liuyameng/Codes/onto-fundary-plugins/clife_onto_engine/sdk/context.py`（ActionContext 构造）、`kernel/action_engine.py`（validate 的 guard / post_rules 求值顺序，确认预演不短路）、`sdk/capability.py` 的一次 grep（确认规则拿不到动作名）。

**误开 / 越界（如实说明）**

- `W/chains-formal/1d/chain.json` 前 50 行：不在允许清单内（也不在禁读清单内）。为看链元数据打开，看到了 round 9 P29a 一步的摘要（`decision: ACCEPT`、verdict 文件路径、Dᵢ 上 h_i / h_prime 的读数）。这属于裁决信息，本轮归因内容不依赖它，特此说明。
- 对 `W/chains-formal/1d/`、`W/chains-formal/1d/attribution/`、`W/chains-formal/1d/work-r9/` 做过 `ls`，看到了 `readings/ results/ verdicts/ manifest-r8.cd.yaml manifest-r9.cd.yaml attribution/round-8 round-9` 等目录 / 文件**名**，未打开其中任何文件。

**刻意没读**

- 另一条链 `W/chains-formal/3d/`、`W/chains-r7/`、`W/chains/` 下的一切。
- `W/proposals.yaml`、`W/growth-ledger.md`、`W/verdicts/`、`W/arms/`、`W/readings/`、`W/results/`；本链的 `verdicts/ readings/ results/`、`manifest-r8/r9.cd.yaml`、`attribution/round-8 round-9`、`work-r9/` 下的文件内容。
- 任何 `attribute-report-*.md`、`handoff-*.md`、`studio/changes/glycowise/proposals/`。
- `git log / git show / git diff` 的任何输出（全程未运行）。
- `/private/tmp/` 下的任何既有目录（自己的 scratchpad 只放了编辑脚本与叠加测试副本）、论文仓库。
- 允许读但没读：`W/examples/trajectories/2026-W53/audit.jsonl`、`W/examples/routing.log.2026-W53.jsonl`、`W/sets/real-W53.yaml`、`W/cases/sim/` 的内容（反馈与案例的 route 已足够定层；没有需要用路由日志裁决的分歧）。

## 1. 复现

工作目录 `W/chains-formal/1d/work-r10`：

```
runner_onto_engine.py run --target-dir ../state/plugins/glycowise --state h_s --cases-dir W/cases \
  --cases-file W/sets/r10-Dminus-candidates.yaml --router manual --recordings plugins/glycowise/cq/all_routes.json \
  --family-override W/sets/family-override.yaml --as-of 2026-10-25 --repeat 1 --out dminus-h_s.jsonl
```

结果：37 案例 / 107 行，原题 pass 6 / 37。6 条已过的是：产品与机构合规-r74、-r79（D9 误拦，本链上不存在）、低血糖安全-r58、参考与配置-r49、-r54（缺陷在落库内容，案例无 expect_state，回放测不出）、指标口径-r97（查询行数 ≥1 即过）。全量基线 `all-h_s.jsonl`：689 案例，pass 575。

## 2. 每条 wrong 的归属

| 案例（trace） | 层 | 归属 / 原因 | 处理 |
|---|---|---|---|
| 产品与机构合规-r67（0717）| 规则 | R32 同句闸：pitch 不复述产品名，「L3 情况」与产品凑不到同句 | P30 |
| 产品与机构合规-r68（0718）| 规则 | 同上，且「三级管理」TIER_RE 认不出；生日祝福进文案属路由 | P30 |
| 产品与机构合规-r69（0719）| 规则 | 同上（「分级是 3 级」认得，同句不成立）| P30 |
| 产品与机构合规-r75（0781）| 规则 | 同上（「缓解期」）| P30 |
| 产品与机构合规-r70（0720）| 规则 | D9 不认「空腹能回到 6 以下」这类回归谓词 | P31 |
| 产品与机构合规-r71（0721）| 规则 | D9 不认「饭后…落回 8 以内」；「老伴也想买」进文案属路由 | P31 |
| 产品与机构合规-r72（0722）| 规则 | D9 不认「把饭后那一波顶回去」| P31 |
| 产品与机构合规-r76（0782）| 规则 | D9 不看产品与「停药」挂钩 | P31 |
| 产品与机构合规-r78（0784）| 规则 | D9 不认「帮胰岛慢慢恢复」（修复胰腺的换说法）| P31 |
| 产品与机构合规-r74（0728）| 规则（本链无）| 业务侧所述 D9 误拦来自生产 h₁₀ 的豁免实现；本链回放已 commit | 登记，不立案 |
| 产品与机构合规-r79（0790）| 规则（本链无）| 同上 | 登记，不立案 |
| 产品与机构合规-r82（0799）| 规则 | R54 字面词表，「夜里有专人看着…放心睡」漏 | P32 |
| 产品与机构合规-r83（0800）| 规则 | 同上，「睡着了也有人替您守着」| P32 |
| 低血糖安全-r47（W52 0649）| 规则 | R04a 读数不存在直接放行 | P33 |
| 低血糖安全-r54（0732）| 规则 | 读数 10.8 不在低血糖区间，R03a / R04a 直接放行 | P33 |
| 低血糖安全-r55（0735）| 规则 | R03a 读数不存在直接放行 | P33 |
| 低血糖安全-r59（0747）| 规则 | 读数 11.7，R04a 直接放行 | P33 |
| 低血糖安全-r60（0751）| 规则 | R04a 读数不存在直接放行 | P33 |
| 低血糖安全-r61（0761）| 规则 | 读数 12.1，R03a 直接放行 | P33 |
| 低血糖安全-r62（0764）| 规则 | R04a 读数不存在直接放行 | P33 |
| 参考与配置-r48（0705）| 规则 | R46 未挂在 收紧告警阈值 上 | P34 |
| 参考与配置-r49（0706）| 规则 + 路由 | handler 对高值字段也用 3.9 作默认起点，落库 3.9；路由字段填成 night_high。案例无 expect_state，h_s 回放已过，Dᵢ 区分不了修前修后 | 登记，不立案 |
| 参考与配置-r54（0750）| 规则 | 同上（high_alert_threshold 落 3.9）；案例无 expect_state，回放已过 | 登记，不立案 |
| 结论层与分层-r49（0723）| 规则 | TIER_RE 不认「高风险组」（业务侧留待确认：「评分」若非服务分层可改 correct）| P35 |
| 结论层与分层-r50（0756）| 规则 | TIER_RE 不认「中间那一档」| P35 |
| 结论层与分层-r51（0769）| 规则 | TIER_RE 不认「最需要盯的那一组」| P35 |
| 结论层与分层-r52（0777）| 规则 | TIER_RE 不认「最轻的那档」| P35 |
| 高血糖与波动-r54（0748）| 规则 | C6 原始值正则要求 mmol，「血糖 14.0」漏 | P36 |
| 高血糖与波动-r52（0733）| 规则 | 群内答复患者 未挂 R24b；C6 同因漏 | P37（C6 部分由 P36 覆盖）|
| 因果链溯源-r53（0752）| 规则 | C20 告警不存在直接放行 | P38 |
| 低血糖安全-r63（0765）| 路由 + 规则 | 路由编了不存在的告警编号（主因，登记）；R44 反查不到患者时直接放行（规则缺口，业务 note 明确应拒）| P39 + 路由登记 |
| 高血糖与波动-r60（0772）| 规则 | 生成方案草稿 未挂 R01（强化方向属结论层）；R22 数据不足仍下黎明现象结论（expect_not）| P40 |
| 低血糖安全-r50（0703）| 路由 | 「回执并结案」路由成 action_taken=已加餐，闭环意图丢失，R44 看不到 | 登记 |
| 低血糖安全-r51（0713）| 路由 | 「可以关了」路由成「已加餐补糖，患者清醒」，丢了闭环 | 登记 |
| 高血糖与波动-r51（0704）| 路由 | 「调整方向」路由成 direction=强化，被低血糖优先抢占拒 | 登记 |
| 低血糖安全-r58（0746）| 路由 | 无关信息改写进 action_taken；裁决类别对，落库内容错（无 expect_state，回放已过）| 登记 |
| 指标口径-r97（0760）| 路由 | 「近 7 天 TIR」查到 14 天汇总，口径错；OQL 只能取现有汇总，无 7 天汇总对象（同时是 IR 缺口：无按读数聚合窗口 TIR 的查询能力），manual 回放下行数 ≥1 即过，测不了 | 登记，不立案 |

## 3. 提案总表

根因修上链（`manifest-r10.yaml`），朴素修只进 P-A（`pa-extra-r10.yaml`）。所有补丁都对本链状态 `patch -p1 --dry-run -d chains-formal/1d/state` 通过、`py_compile` 通过、Dᵢ（含变体）在 `--state h_prime --as-of 2026-10-25` 下全过。

| 缺陷 | 提案 | 编号 | 修法 | 补丁（总行 / +/−）| Dᵢ |
|---|---|---|---|---|---|
| P30 R32 | P30a 根因 | 48 | pitch 每句按提及产品的句子审；TIER_RE 认「N 级管理」| 29 / +11 −1 | 4 案例 12 行全过 |
| | P30b1 朴素·规则 3 | 49 | 删「尾注已附 → 放行」分支 | 13 / +2 −2 | 全过 |
| | P30b2 朴素·规则 5 | 50 | Dᵢ 字面进 PRODUCT_WORDS / TIER_RE | 17 / +4 −2 | 全过 |
| P31 D9 | P31a 根因 | 51 | 补回归 / 目标值谓词、停药挂钩、器官功能修复 | 31 / +14 −1 | 5 案例 15 行全过 |
| | P31b1 朴素·规则 3 | 52 | 删「无功效命中 → 跳过」| 14 / +2 −2 | 全过 |
| | P31b2 朴素·规则 5 | 53 | 五个 Dᵢ 字面进 EFFICACY_RE | 12 / +2 −1 | 全过 |
| P32 R54 | P32a 根因 | 54 | 夜间时段 + 有人值守同句 /「放心睡」，否定式除外 | 37 / +17 −2 | 2 案例 4 行全过 |
| | P32b1 朴素·规则 3 | 55 | 删「未命中 → 放行」| 11 / +1 −1 | 全过 |
| | P32b2 朴素·规则 5 | 56 | 三个 Dᵢ 字面进 NIGHT_PROMISE | 12 / +2 −1 | 全过 |
| P33 R03a/R04a | P33a 根因 | 57 | 引用读数须存在且 <3.9，按请求级别拒 | 66 / +46 −0 | 7 案例 21 行全过 |
| | P33b1 朴素·规则 3 | 58 | 删两条规则开头的放行分支 | 22 / +2 −4 | 全过 |
| | P33b2 朴素·规则 5 | 59 | Dᵢ 读数编号黑名单 | 28 / +8 −0 | 全过 |
| P34 R46 | P34a 根因 | 60 | R46 挂为 收紧 的 guard；高值字段不连坐 | 26 / +7 −1 | 1 案例 3 行全过 |
| P35 R51 | P35a 根因 | 61 | TIER_RE 认「有序分组中的位置」| 18 / +7 −0 | 4 案例 12 行全过 |
| | P35b1 朴素·规则 3 | 62 | 删「不含分层字样 → 放行」| 12 / +1 −2 | 全过 |
| | P35b2 朴素·规则 5 | 63 | 四个 Dᵢ 字面进 TIER_RE | 12 / +2 −1 | 全过 |
| P36 C6 | P36a 根因 | 64 | 原始值按语境认，不要求单位 | 23 / +10 −1 | 1 案例 2 行全过 |
| | P36b1 朴素·规则 3 | 65 | 删「无原始值 → 放行」| 11 / +1 −1 | 全过 |
| | P36b2 朴素·规则 5 | 66 | 「14.0」进正则 | 11 / +1 −1 | 全过 |
| P37 R24b | P37a 根因 | 67 | R24b 挂群内答复；运动建议 + G>16.7 即拒 | 51 / +28 −0 | 1 案例 3 行全过 |
| P38 C20 | P38a 根因 | 68 | alert_id 查无此告警 → 拒 | 13 / +4 −0 | 1 案例 3 行全过 |
| | P38b1 朴素·规则 3 | 69 | 删「找不到告警 → 放行」| 12 / +1 −2 | 全过 |
| | P38b2 朴素·规则 5 | 70 | 告警编号黑名单 | 11 / +2 −0 | 全过 |
| P39 R44 | P39a 根因 | 71 | 闭环请求反查不到患者 → 拒 | 14 / +5 −0 | 1 案例 3 行全过 |
| | P39b1 朴素·规则 3 | 72 | 删「非高危 → 放行」| 11 / +1 −1 | 全过 |
| | P39b2 朴素·规则 5 | 73 | 告警编号进拒绝条件 | 11 / +1 −1 | 全过 |
| P40 R01/R22 | P40a 根因 | 74 | R01 挂草稿（仅强化）；R22 数据不足不评 | 38 / +12 −1 | 1 案例 3 行全过 |

五条机械规则的总体适用情况：规则 1（放宽阈值）、2（跳过缺参数的校验）、4（hard 改 soft）在本轮 11 个缺陷上全部不适用——本轮缺陷全是**漏拦**（该拒没拒），这三条只会让规则更少触发；规则 3、5 在 8 个「规则已挂载、判定漏了」的缺陷上适用，在 3 个「规则未挂载」的缺陷（P34 / P37 / P40）上不适用。逐条理由见各 P<n>.md 第 4 节。

## 4. 裁决

2026-10-25 裁决（AS_OF 2026-10-25，criteria v5；详见 chains-formal/compare-r10.md）：
- P30a（48）：P-A 接受臂 none；带闸门臂拒因：内关卡成本 C（ΔC 超带宽 1 步；正确拒绝比错误放行多走步数）；1d 链 chain_drive：**REVISE**
- P30b1（49）：P-A 接受臂 none；带闸门臂拒因：外关卡 S、T（B₁₀ 上有回退）
- P30b2（50）：P-A 接受臂 none；带闸门臂拒因：内关卡成本 C（ΔC 超带宽 1 步；正确拒绝比错误放行多走步数）
- P31a（51）：P-A **APPLY_FAIL**（与 h₁₀ 分叉），不进分母；1d 链 chain_drive：**ACCEPT**
- P31b1（52）：P-A **APPLY_FAIL**（与 h₁₀ 分叉），不进分母
- P31b2（53）：P-A **APPLY_FAIL**（与 h₁₀ 分叉），不进分母
- P32a（54）：P-A 接受臂 3d/3d-noT/3d-noS/3d-noW/1d/1d-strict/none/random；1d 链 chain_drive：**ACCEPT**
- P32b1（55）：P-A 接受臂 none/random；带闸门臂拒因：外关卡 S、T（B₁₀ 上有回退）
- P32b2（56）：P-A 接受臂 3d/3d-noT/3d-noS/3d-noW/1d/1d-strict/none
- P33a（57）：P-A 接受臂 none/random；带闸门臂拒因：内关卡成本 C（ΔC 超带宽 1 步；正确拒绝比错误放行多走步数）；1d 链 chain_drive：**REVISE**
- P33b1（58）：P-A 接受臂 none；带闸门臂拒因：内关卡成本 C（ΔC 超带宽 1 步；正确拒绝比错误放行多走步数）
- P33b2（59）：P-A 接受臂 3d/3d-noT/3d-noS/3d-noW/1d/1d-strict/none/random
- P34a（60）：P-A 接受臂 3d/3d-noT/3d-noS/3d-noW/1d/1d-strict/none/random；1d 链 chain_drive：**ACCEPT**
- P35a（61）：P-A 接受臂 3d/3d-noT/3d-noS/3d-noW/1d/1d-strict/none/random；1d 链 chain_drive：**ACCEPT**
- P35b1（62）：P-A 接受臂 none；带闸门臂拒因：外关卡 S、T（B₁₀ 上有回退）
- P35b2（63）：P-A 接受臂 3d/3d-noT/3d-noS/3d-noW/1d/1d-strict/none/random
- P36a（64）：P-A 接受臂 3d/3d-noT/3d-noS/3d-noW/1d/1d-strict/none/random；1d 链 chain_drive：**ACCEPT**
- P36b1（65）：P-A 接受臂 none/random；带闸门臂拒因：外关卡 S、T（B₁₀ 上有回退）
- P36b2（66）：P-A 接受臂 3d/3d-noT/3d-noS/3d-noW/1d/1d-strict/none
- P37a（67）：P-A 接受臂 3d/3d-noT/3d-noS/3d-noW/1d/1d-strict/none/random；1d 链 chain_drive：**ACCEPT**
- P38a（68）：P-A 接受臂 3d/3d-noT/3d-noS/3d-noW/1d/1d-strict/none/random；1d 链 chain_drive：**ACCEPT**
- P38b1（69）：P-A 接受臂 3d/3d-noT/3d-noS/3d-noW/1d/1d-strict/none/random
- P38b2（70）：P-A 接受臂 3d/3d-noT/3d-noS/3d-noW/1d/1d-strict/none/random
- P39a（71）：P-A 接受臂 3d/3d-noT/3d-noS/3d-noW/1d/1d-strict/none；1d 链 chain_drive：**ACCEPT**
- P39b1（72）：P-A 接受臂 3d/3d-noT/3d-noS/3d-noW/1d/1d-strict/none
- P39b2（73）：P-A 接受臂 3d/3d-noT/3d-noS/3d-noW/1d/1d-strict/none/random
- P40a（74）：P-A 接受臂 3d/3d-noT/3d-noS/3d-noW/1d/1d-strict/none；1d 链 chain_drive：**ACCEPT**

## 5. 误伤面（只用案例文件估计，不看任何裁决）

`cases/real` + `cases/sim` 全部 689 案例（1732 行）在 h_s 与每个沙箱上各回放一次（`work-r10/all-*.jsonl`，比对表 `work-r10/collateral.json`）：

- 根因修：P30a / P31a / P32a / P33a / P35a / P36a / P37a / P38a / P39a / P40a 均 0 回退。P34a 回退 1 案例（参考与配置-r52，query 0 行）：其 setup 第 3 步正是被 P34a 改判为拒的 0705（4.3）收紧，属反事实连带，详见 P34.md。
- 11 份根因补丁按编号顺序叠加（scratchpad 副本，非本链状态）全部干净应用、编译通过；叠加后全量 pass 575 → 602，转对 28 行案例（= 各 Dᵢ 之和），回退只有上述参考与配置-r52。
- 朴素修：所有「规则 5 · 加字面量」与 P38b1 均 0 回退（字面量不外溢，也不泛化：变体之外的换说法照样漏）；「规则 3 · 删放行分支」回退面大：P30b1 10 案例、P31b1 10、P32b1 26、P33b1 6、P35b1 29、P36b1 22、P39b1 1，多条落在 holdout-10 内（各 P<n>.md 第 6 节列明）。

## 6. 登记不立案

- **路由层**（6 条，只登记）：低血糖安全-r50、-r51（闭环意图在 action_taken 中丢失）、高血糖与波动-r51（direction 擅自定为强化）、低血糖安全-r58（无关信息改写进回执）、指标口径-r97（7 天口径落到 14 天汇总）、低血糖安全-r63 的路由部分（编造告警编号）。另 r68 / r71 / r53 等的无关信息被写进参数也属路由。
- **规则层但回放测不出**：参考与配置-r49 / -r54——`act_tighten` 对所有字段都用 3.9 作默认起点，高值线收紧被压成 3.9 落库。案例只断言 `action(收紧告警阈值)`，没有 `expect_state`，h_s 上已过，Dᵢ 无法区分修前修后；建议案例补 `expect_state: [{type: AlertThreshold, …, fields: {current_value: 13.9}}]` 后下轮立案（同时 seed 补各患者高值阈值行）。
- **IR 缺口**：指标口径-r97 需要「按读数聚合任意窗口 TIR」的查询能力或 7 天汇总对象；manual 回放下查询只看行数，测不了，不立案。P34 / P37 / P40 三个根因修改动了规则挂载（R46→收紧、R24b→群内答复、R01→生成方案草稿），IR §5 动作表需同步，属 IR 侧随改项。
- **本链无缺陷**：产品与机构合规-r74 / -r79 的 D9 误拦在本链（无 P28a 系豁免实现）上不复现。

## 7. 流程问题

1. **允许清单没有覆盖链元数据**：`chain.json` 不在允许清单里，但它是唯一说明本链状态由哪些提案构成的文件，其中又混着上一轮的裁决摘要。我为看元数据打开了它（见第 0 节）。建议把「状态构成」单独写成一个不含裁决的文件（如 `state/LINEAGE`），或在任务书里给出。
2. **Dᵢ 格式与清单格式没有规范**：`*-Di.yaml` 与 `manifest-r10.yaml` 的字段是我按 runner 能读的键（`source_cases`）自拟的；上一轮的清单属禁读，无法对齐格式。建议在 evolve-attribute 的 SKILL 里固定 schema。
3. **案例缺 expect_state 让「落库内容错」的 wrong 测不出**：0706 / 0750 / 0746 三条业务侧都写明了期望的落库字段值，但 make_real_cases 没把 truth 里的对象与字段落成 `expect_state`，导致 h_s 回放就「过」。建议落案例时从 truth 抽取 expect_state（至少对 wrong 且期望为 action 的条目）。
4. **validate 预演不短路**：guard 拒了 post_rules 仍会评，案例的 `expect_not` 会被 post_rules 的软提示触发（r60 的 R22）。真实 execute 时 guard 拒即返回，不会出现这条软提示。归因因此必须同时改 R22，判定口径与线上行为不完全一致，值得在 runner 或引擎侧明确。
5. **同一条 TIER_RE 被多份提案改**：P30a 与 P35a 最初都改同一行，按序叠加冲突；已改成各自在不同位置追加（`TIER_RE = re.compile(TIER_RE.pattern + …)`）。并行归因时共享正则 / 词表很容易互相冲突，建议链上合并顺序按清单编号，并在 gate 前做一次叠加 dry-run。
6. **r63 的层判定**：反馈标 router，但 note 明说规则侧有缺口应拒。我按「路由为主 + 规则缺口立案（P39）」处理；若裁决方认为只按反馈的 layer 字段走，P39 应撤。
7. **结论层与分层-r49 与 高血糖与波动-r60 均带「待确认」**：本体负责人已复核采纳为 wrong，我按 wrong 立案；若后续改判 correct，P35a 对 r49、P40a 整份应随之复核。
