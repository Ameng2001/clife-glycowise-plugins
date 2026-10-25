# round 10 · 3d 链归因报告（窗口 2026-W53）

- 本体状态：3d 链当前状态 = h₁₀ = 生产（`chains-formal/3d/state/plugins/glycowise`）
- 输入：W53 reviewed，80 条中 wrong 36（反馈标层：rule 30 / router 6）、partial 5、correct 39；外加 W52 遗留候选低血糖安全-r47（2026-10-25 修正路由置信度）。D⁻ 候选 = `sets/r10-Dminus-candidates.yaml`，共 37 条
- 只归因、不裁决：没有运行 gate_decide.py / chain_drive.py，没有 git commit，没有改 `chains-formal/3d/state` 下的生产代码
- 工作目录：`chains-formal/3d/work-r10`（沙箱 `sb/<提案>/plugins/glycowise`，脚本与中间产物在 `scratch/`）

## 0 读了什么、刻意没读什么

### 0.1 读过的（允许范围内）

| 文件 | 读法 |
|---|---|
| `chains-formal/3d/state/plugins/glycowise/__init__.py` | 规则 / 动作声明的相关段落（R03a、R04a、R44、R46、R24b、R01、R22、R32、D8、D9、D10、D11、R51、C6、C20、R54；触发低血糖处置、响应并回执告警、放宽 / 收紧告警阈值、生成方案草稿、创建服务包SKU、生成产品推荐、群内答复患者、推送告警的挂载） |
| `chains-formal/3d/state/plugins/glycowise/_fde.py` | 常量与正则（第 28–48 行）、`text_of` / `P` / `pid_of` / `summary_of`、R35 / R01 / R49、`_product_gate` / `_efficacy_claim` / D9 / R32 / R51 / R54 / R55、告警与读数辅助函数、R03a / R04a / R44 / C20 / R24a / R24b / R46 / C6 / R22，以及 act_draft / act_tighten / act_loosen / act_ack / act_reco / act_group_reply / act_trigger_hypo / act_service_sku |
| `studio/changes/glycowise/ontology-map.md` | grep 相关规则行、§4.1 硬语义、§5 动作挂载表 |
| `examples/trajectories/2026-W53/feedback.yaml` | 全文（36 wrong + 5 partial 逐条；correct 只看了口语与引擎结果，用作同组对照） |
| `examples/routing.log.2026-W53.jsonl` | 前两行，以及 0703 / 0704 / 0706 / 0713 / 0746 / 0750 / 0760 / 0765 八条 |
| `cases/real/` | D⁻ 37 条案例的 expect / route / expect_not / setup 字段，其中低血糖安全-r47、参考与配置-r49、高血糖与波动-r60 读了全文；误伤排查时读了参考与配置-r52（W53 判对的查询）。其余案例只由 runner 和取 id 的脚本程序化读取 |
| `cases/sim/` | 只由 runner 程序化读取 |
| `sets/r10-Dminus-candidates.yaml`、`sets/real-W53.yaml`、`sets/targeted-W53.yaml`、`sets/family-override.yaml` | 全文 / id 列表 |
| `sets/holdout-10.yaml` | 只取元数据和 id，用来把留出集从误伤面估计里剔除；没有对留出案例做任何回放比对 |
| `astra-studio-plugins/studio-evolve/scripts/runner_onto_engine.py` | `--help`、模块说明、`load_engine` / `load_plugin` / `cmd_run` 开头（为了写探针脚本） |

`examples/trajectories/2026-W53/audit.jsonl` 允许读，但没用到，没读。

### 0.2 不在允许清单里、但读了（如实登记）

1. **`chains-formal/3d/manifest-r9.cd.yaml` 前 40 行**：列链目录时顺手 `head` 了，看到的是 round 9 根因修 P28a 的 chain_drive 格式条目（id / num / patch / di / holdout 字段）。这个文件不在禁读清单，也不在允许清单。它影响了 `manifest-r10.yaml` 的字段命名，没有影响任何归因或修法。
2. **引擎源码 `onto-fundary-plugins/clife_onto_engine/`**：`kernel/action_engine.py` 的 `validate` / `_eval_rules`、`sdk/capability.py` 前 80 行、`query/__init__.py` 的方法签名。目的是确认 validate 在 guard 失败后是否还跑 post_rules（结论：照跑、全收集，直接影响 P51 的 R22 处理）。
3. **目录列表里出现的禁读文件名**：`ls W` 列出了 `attribute-report-*.md`、`handoff-*.md`、`proposals.yaml`、`growth-ledger.md`、`verdicts/`、`arms/`、`readings/`、`results/`、`chains/`、`chains-r7/`；`ls chains-formal/3d` 列出了 `attribution/round-8`、`round-9`、`verdicts/`、`readings/`、`results/`、`start-r9/`、`work-r9/`（work-r9 的文件名也列出来了）。都只看到名字，没有打开任何一个。
4. **含留出集的全量汇总行**：第一次估误伤面时对全部 689 例跑了一遍 h₁₀ 基线（`all-h10.jsonl`），终端打出了一行总数「pass 573 / 689」，其中含 holdout-10 与 targeted-W53。发现后没有读任何结果行，文件已删除，改用剔除留出集的 586 例清单（`scratch/fallout-ids.yaml`）重跑。
5. **`/private/tmp/` 下的会话草稿目录**：开工时把一个探针脚本写进了本会话的系统草稿目录（`/private/tmp/claude-501/…/scratchpad/`），跑了一次就移到 `work-r10/scratch/`，并删除了那个目录。没有读取 `/private/tmp/` 下的任何其它目录或文件。
6. `git status --short` 跑了两次：第一次限定本链目录；收尾时在仓库根跑的那次列出了 `chains-formal/1d/attribution/round-10/`、`1d/start-r10/`、`1d/work-r10/`、`1d/work-r9/`、`1d/work/`、`chains-r7/3d/work/sb/` 几个未跟踪目录名（另一条链本轮也在产出）。只看到目录名，没有进入。没有运行 `git log` / `git show` / `git diff`。

### 0.3 刻意没读

`chains-formal/1d/`、`chains-r7/`、`chains/` 下的一切；`proposals.yaml`、`growth-ledger.md`、`verdicts/`、`arms/`、`readings/`、`results/`；所有 `attribute-report-*.md`、`handoff-*.md`；`studio/changes/glycowise/proposals/`；本链的 `attribution/round-8`、`round-9`、`verdicts/`、`readings/`、`results/`、`work-r9/` 的内容、`start-r9/`；任何 git 历史；论文仓库。

## 1 复现

```
cd chains-formal/3d/work-r10
runner_onto_engine.py run --engine-root onto-fundary-plugins --target-dir ../state/plugins/glycowise --ontology glycowise \
  --state h_i --cases-dir W/cases --cases-file W/sets/r10-Dminus-candidates.yaml --family-override W/sets/family-override.yaml \
  --router manual --recordings ../state/plugins/glycowise/cq/all_routes.json --as-of 2026-10-25 --repeat 1 --out repro-h10.jsonl
```

结果（`work-r10/repro-h10.jsonl`）：37 条可判，**33 条判错、4 条判对**。判对的是低血糖安全-r58、参考与配置-r49、参考与配置-r54、指标口径-r97，原因见 §2：错在落库内容或查询口径，而这些案例没带 expect_state，manual 回放判不出来。flags 有 SETUP_DIVERGED 3 次（r47 的 setup 第 8 步「每天一包，血糖曲线会变平」被 h₁₀ 拒，这是 P28a 的反事实）和 FORBIDDEN_RULE_HIT 3 次（高血糖与波动-r60 的 R22）。

## 2 每条 wrong 的归属

| trace | 案例 | 层 | 缺陷 / 原因 | 处置 |
|---|---|---|---|---|
| 0649（W52） | 低血糖安全-r47 | 规则 | 读数 r-P0023-00480 不存在，R04a 在 g=None 时放行 | P45 |
| 0703 | 低血糖安全-r50 | 路由 | 「回执并结案」被路由成 action_taken=「已加餐」，闭环意图丢失，R44 看不到 | 登记 |
| 0704 | 高血糖与波动-r51 | 路由 | 口语「调整方向」被填成 direction=强化，引发「低血糖优先抢占」拒 | 登记 |
| 0705 | 参考与配置-r48 | 规则 | `收紧告警阈值` 不查 R46，IAH 高危低值线 4.3 直接落库 | P46 |
| 0706 | 参考与配置-r49 | 规则（handler） | `act_tighten` 对高值字段也用默认 3.9 作起点，把 13.9 压回 3.9；路由字段名也填错 | 登记，不立案（Dᵢ 已过，见 §5） |
| 0713 | 低血糖安全-r51 | 路由 | 「可以关了」被路由成「已加餐补糖，患者清醒」，闭环意图丢失 | 登记 |
| 0717 / 0718 / 0719 / 0781 | 产品与机构合规-r67 / r68 / r69 / r75 | 规则 | R32 同句闸要求句中有产品名，pitch 不复述「英纽林」就永不同句；「三级管理」`TIER_RE` 不认 | P41 |
| 0720 / 0721 / 0722 / 0782 / 0784 | 产品与机构合规-r70 / r71 / r72 / r76 / r78 | 规则 | D9 的声称对象表里没有餐时血糖（空腹 / 饭后 + 结果）、胰岛功能、停药 | P42 |
| 0723 / 0756 / 0769 / 0777 | 结论层与分层-r49 / r50 / r51 / r52 | 规则 | R51 的 `TIER_RE` 每个分支都要级数，「档 / 组」位置说法认不出 | P48 |
| 0728 / 0790 | 产品与机构合规-r74 / r79 | 规则 | D9 / P28a 豁免表不认「代替不了」「照原来的办法」「血糖偏高时先别冲」「问问医生」，误拦 | P43 |
| 0732 / 0747 / 0761 | 低血糖安全-r54 / r59 / r61 | 规则 | 读数值 10.8 / 11.7 / 12.1 不在低血糖区间，R03a / R04a 直接放行，handler 照建告警 | P45 |
| 0735 / 0751 / 0764 | 低血糖安全-r55 / r60 / r62 | 规则 | 读数不存在，R03a / R04a 在 g=None 时放行 | P45 |
| 0733 | 高血糖与波动-r52 | 规则 | R24b 没挂在 `群内答复患者` 上，且只在有运动打卡时才评 | P49 |
| 0746 | 低血糖安全-r58 | 路由 | 无关信息被改写成 action_taken「家属到家协助复测确认」；裁决类别对，错在落库内容 | 登记（案例无 expect_state，回放已判对） |
| 0748 | 高血糖与波动-r54 | 规则 | C6 原始值正则要求带 mmol，「14.0」漏 | P50 |
| 0750 | 参考与配置-r54 | 规则（handler） | 同 0706：高值字段默认起点 3.9，落库 3.9 | 登记，不立案（Dᵢ 已过） |
| 0752 | 因果链溯源-r53 | 规则 | C20 找不到告警就放行 | P47 |
| 0760 | 指标口径-r97 | 路由 | 「近 7 天 TIR」查到的是 14 天汇总，口径错（反馈附「待确认」） | 登记（回放已判对：query ≥1 行） |
| 0765 | 低血糖安全-r63 | 路由（另有规则侧缺口） | 路由编出不存在的 A-P0023-01；R44 取不到患者即放行 | 登记；P47a 应用后此案改为被 C20 拒，期望 R44 仍不中 |
| 0772 | 高血糖与波动-r60 | 规则 | R01 没挂在 `生成方案草稿` 上；R22 用有数据天数作分母，6 天数据误报黎明现象 | P51 |
| 0799 / 0800 | 产品与机构合规-r82 / r83 | 规则 | R54 是字面词表，换说法就漏 | P44 |

合计：规则层 30 条 → 11 个缺陷、立案 28 条，加 W52 的 r47 共 29 条 Dᵢ；另有 2 条规则层（0706 / 0750）登记不立案。路由层 6 条只登记。没有立案的 IR 缺口（manual 回放下测不了的不立案）。partial 5 条（0708 / 0710 / 0729 / 0734 / 0779）不在 D⁻，未处理，其中 0779 与 0706 / 0750 同因。

## 3 提案总览

proposal 编号从 75 起；根因修 `P<n>a` 上链（`manifest-r10.yaml`），朴素修 `P<n>bk` 只进 P-A（`pa-extra-r10.yaml`）。验证一律在沙箱 `work-r10/sb/<提案>/` 上做：`patch -p1 --dry-run -d chains-formal/3d/state`、`py_compile`、runner `--state h_prime --as-of 2026-10-25 --router manual --repeat 1`。误伤面用剔除 holdout-10 / targeted-W53 后的 586 例案例文件，与 h₁₀ 逐行比对。

| 提案 | num | 类 | 修法 | 补丁行 | dry-run | 编译 | Dᵢ | 误伤（例） |
|---|---|---|---|---|---|---|---|---|
| P41a | 75 | 根因 | pitch 每句按推荐句判同句；`TIER_RE` 补「N 级管理」 | +6/−1 | 通过 | 通过 | 4/4 | 0 |
| P41b1 | 76 | N5 | `PRODUCT_WORDS` 加「每天一包 / 可以试试 / 配一包」，`TIER_RE` 加「三级管理」 | +2/−1 | 通过 | 通过 | 4/4 | 0 |
| P42a | 77 | 根因 | D9 声称对象补餐时血糖 + 结果谓词、胰岛 / 胰腺功能、用药减停（剔安全提醒） | +15/−1 | 通过 | 通过 | 5/5 | 0 |
| P42b1 | 78 | N5 | `GLYCEMIC_INDICATOR_RE` 加「空腹 / 饭后 / 胰岛 / 停药」 | +1/−1 | 通过 | 通过 | 5/5 | 0 |
| P43a | 79 | 根因 | 豁免表补不替代口语写法、交回原方案、以血糖为条件的食用限制、问问医生 | +7/−1 | 通过 | 通过 | 2/2 | 0 |
| P43b1 | 80 | N3 | 删 P28a 血糖指标反向判定分支 | +0/−3 | 通过 | 通过 | 2/2 | 1 |
| P43b2 | 81 | N4 | D9 hard → soft | +1/−1 | 通过 | 通过 | 2/2 | 7 |
| P43b3 | 82 | N5 | 豁免表加两段 Dᵢ 字面量 | +1/−1 | 通过 | 通过 | 2/2 | 0 |
| P44a | 83 | 根因 | 同句「夜间 / 睡眠时段」×「值守主体 / 看护断言」即算承诺 | +10/−0 | 通过 | 通过 | 2/2 | 0 |
| P44b1 | 84 | N5 | `NIGHT_PROMISE` 加三个 Dᵢ 字面量 | +1/−1 | 通过 | 通过 | 2/2 | 0 |
| P45a | 85 | 根因 | 带 reading_id 的低血糖处置：读数缺失或 ≥3.9 → 按 rule_id 级别由 R03a / R04a 拒（R05 / R11 路径除外） | +37/−0 | 通过 | 通过 | 7/7 | 0 |
| P45b1 | 86 | N3 | 删 r03a / r04a 开头放行分支 | +0/−4 | 通过 | 通过 | 7/7 | 6 |
| P46a | 87 | 根因 | `收紧告警阈值` 补挂 R46 为 guard | +3/−0 | 通过 | 通过 | 1/1 | 1（参考与配置-r52，躲不开，见 §6） |
| P47a | 88 | 根因 | 指名告警不存在 → C20 拒 | +4/−0 | 通过 | 通过 | 1/1 | 0 |
| P47b1 | 89 | N3 | 删 c20「找不到告警即放行」分支 | +0/−2 | 通过 | 通过 | 1/1 | 0 |
| P48a | 90 | 根因 | R51 加分层位置说法识别（档直接算，组需分层限定） | +17/−1 | 通过 | 通过 | 4/4 | 0 |
| P48b1 | 91 | N3 | 删 r51「不含分层即放行」分支 | +0/−2 | 通过 | 通过 | 4/4 | 24 |
| P48b2 | 92 | N5 | `TIER_RE` 加四段 Dᵢ 字面量 | +1/−0 | 通过 | 通过 | 4/4 | 0 |
| P49a | 93 | 根因 | `群内答复患者` 补挂 R24b；含未否定运动建议时按口述当前值 / 最近读数判 >16.7 | +16/−2 | 通过 | 通过 | 1/1 | 0 |
| P50a | 94 | 根因 | C6 认血糖语境词后的一位小数值（排除阈值 / 目标说法） | +12/−1 | 通过 | 通过 | 1/1 | 0 |
| P50b1 | 95 | N3 | C6 去掉 mmol 单位条件 | +1/−1 | 通过 | 通过 | 1/1 | 0 |
| P50b2 | 96 | N5 | C6 加字面量「血糖 14.0」 | +1/−1 | 通过 | 通过 | 1/1 | 0 |
| P51a | 97 | 根因 | 方案草稿补挂 R01（只管强化方向）；R22 分母取 max(天数, 14) | +9/−2 | 通过 | 通过 | 1/1 | 0 |

Dᵢ 一栏是案例数；每份提案的原题与变体行全部通过。

五条机械规则逐缺陷的适用表在各 `P<n>.md` §4。汇总：P46 / P49 / P51 三个缺陷五条全不适用（规则根本没被评估，或 Dᵢ 要两件事同时成立）；漏拦类缺陷只可能套 N3 / N5，N1 / N2 / N4 的方向都是放行；只有误拦的 P43 套得上 N3 / N4 / N5 三条。

N3 的判法：Dᵢ 在 h₁₀ 上实际走到、并导致错判的那条显式分支或分支条件（漏拦时是放行分支，误拦时是拒绝分支）。只有隐式「全不中 → 放行」路径的，判不适用。

**根因修合并检查**：11 份根因修按编号顺序在 h₁₀ 上依次打齐，只有行偏移、无冲突，可以编译（`work-r10/sb/_all-roots`）。Dᵢ 并集 29 案例 / 84 行全过；586 例误伤面上修好 29、误伤 1（参考与配置-r52），FORBIDDEN_RULE_HIT 归零。

合成探针（不进任何集合）只用来看根因修与朴素修在 Dᵢ 之外的差别，结果写在各 `P<n>.md` §6（`work-r10/scratch/probes.tsv`、`probe-*.txt`）。

## 4 裁决

2026-10-25 裁决（AS_OF 2026-10-25，criteria v5；详见 chains-formal/compare-r10.md）：
- P41a（75）：P-A 接受臂 none；带闸门臂拒因：内关卡成本 C（ΔC 超带宽 1 步；正确拒绝比错误放行多走步数）；3d 链 chain_drive：**REVISE**
- P41b1（76）：P-A 接受臂 none；带闸门臂拒因：内关卡成本 C（ΔC 超带宽 1 步；正确拒绝比错误放行多走步数）
- P42a（77）：P-A 接受臂 3d/3d-noT/3d-noS/3d-noW/1d/1d-strict/none/random；3d 链 chain_drive：**ACCEPT**
- P42b1（78）：P-A 接受臂 3d/3d-noT/3d-noS/3d-noW/1d/1d-strict/none/random
- P43a（79）：P-A 接受臂 3d/3d-noT/3d-noS/3d-noW/1d/1d-strict/none/random；3d 链 chain_drive：**ACCEPT**
- P43b1（80）：P-A 接受臂 3d/3d-noT/3d-noS/3d-noW/1d/1d-strict/none
- P43b2（81）：P-A 接受臂 none/random；带闸门臂拒因：外关卡 S、T（B₁₀ 上有回退）
- P43b3（82）：P-A 接受臂 3d/3d-noT/3d-noS/3d-noW/1d/1d-strict/none/random
- P44a（83）：P-A 接受臂 3d/3d-noT/3d-noS/3d-noW/1d/1d-strict/none/random；3d 链 chain_drive：**ACCEPT**
- P44b1（84）：P-A 接受臂 3d/3d-noT/3d-noS/3d-noW/1d/1d-strict/none/random
- P45a（85）：P-A 接受臂 none/random；带闸门臂拒因：内关卡成本 C（ΔC 超带宽 1 步；正确拒绝比错误放行多走步数）；3d 链 chain_drive：**REVISE**
- P45b1（86）：P-A 接受臂 none/random；带闸门臂拒因：内关卡成本 C（ΔC 超带宽 1 步；正确拒绝比错误放行多走步数）
- P46a（87）：P-A 接受臂 3d/3d-noT/3d-noS/3d-noW/1d/1d-strict/none/random；3d 链 chain_drive：**ACCEPT**
- P47a（88）：P-A 接受臂 3d/3d-noT/3d-noS/3d-noW/1d/1d-strict/none/random；3d 链 chain_drive：**ACCEPT**
- P47b1（89）：P-A 接受臂 3d/3d-noT/3d-noS/3d-noW/1d/1d-strict/none/random
- P48a（90）：P-A 接受臂 3d/3d-noT/3d-noS/3d-noW/1d/1d-strict/none；3d 链 chain_drive：**ACCEPT**
- P48b1（91）：P-A 接受臂 none/random；带闸门臂拒因：外关卡 S、T（B₁₀ 上有回退）
- P48b2（92）：P-A 接受臂 3d/3d-noT/3d-noS/3d-noW/1d/1d-strict/none/random
- P49a（93）：P-A 接受臂 3d/3d-noT/3d-noS/3d-noW/1d/1d-strict/none/random；3d 链 chain_drive：**ACCEPT**
- P50a（94）：P-A 接受臂 3d/3d-noT/3d-noS/3d-noW/1d/1d-strict/none/random；3d 链 chain_drive：**ACCEPT**
- P50b1（95）：P-A 接受臂 3d/3d-noT/3d-noS/3d-noW/1d/1d-strict/none/random
- P50b2（96）：P-A 接受臂 3d/3d-noT/3d-noS/3d-noW/1d/1d-strict/none
- P51a（97）：P-A 接受臂 3d/3d-noT/3d-noS/3d-noW/1d/1d-strict/none；3d 链 chain_drive：**ACCEPT**

## 5 登记项（不出提案）

1. **路由层 6 条**：0703 / 0713（闭环意图被路由改写成「已加餐」，R44 看不到；与 W50 0401 / 0404 / 0406 同型）、0704（direction 被替口语定成强化）、0746（无关信息改写进 action_taken）、0760（7 天口径查成 14 天汇总）、0765（编造告警编号）。回放按 case.route 走，规则层修不到；如果为了让 0703 / 0713 判对去把「已加餐」当闭环字样，那是 N5 式的字面量修，而且会误伤 0702 这类合法回执，故不做。
2. **0706 / 0750（规则层，handler）**：`act_tighten` / `act_loosen` 找不到阈值行时，所有字段的默认起点都是 3.9。高值类字段（high_alert_threshold / night_high）因此把 13.9 判成「放宽」压回 3.9，落库一条 3.9 的高值线；0779 的 ThresholdChangeLog.before 也记成 3.9。两条案例都没带 expect_state，在 h₁₀ 上已经判对，修与不修在 Dᵢ 上区分不出来，所以不立案。建议给参考与配置-r49 / r54 补上 `expect_state`（AlertThreshold current_value=13.9、ThresholdChangeLog after=13.9）后下轮立案，修法方向是按字段类别取默认起点，或 seed 补高值阈值行。
3. **0765 的规则侧缺口**：R44 取不到患者（告警不存在）时直接放行。P47a 让这类回执先被 C20 拒，但 R44 本身的口径没动。
4. **P45 没处理的情况**：读数在低血糖区间、但与请求级别不符（例如 3.5 的读数按 Level 2 发起）。IR 和 Dᵢ 都没涉及。

## 6 流程问题

1. **案例缺 expect_state，落库类 wrong 测不出**：feedback 的 `_howto` 写明「wrong 且期望为 action 的条目在 truth 里写明落库对象与字段值」，0706 / 0750 / 0746 也确实写了，但落成的案例都没有 `expect_state`，manual 回放在 h₁₀ 上直接判对。这类 wrong 现在只能登记，进不了 Dᵢ，也进不了留出集的判别力。建议 make_real_cases 在 truth 给出字段时生成 expect_state。
2. **setup 反事实导致的「躲不开」误伤**：参考与配置-r52（0730，查黄伯低值线，判对）的「对」是相对于 0705 已落库的窗口状态判的；而 r48 要求 0705 被拒。凡是让 r48 通过的修法都会让 r52 回放出 0 行。gate 若把 r52 的翻转记成误伤，会系统性惩罚正确的修法。建议这类「读到前序错误写入」的判对案例在落案时打标记，或在前序 setup 被改判时不计入误伤。
3. **targeted-W53 与 D⁻ 重叠**：产品与机构合规-r74 / r79 既是 D⁻ 候选（本轮 P43 的 Dᵢ），又在 `targeted-W53.yaml` 里（「只评 round ≥ 10 的提案」）。如果外关卡也用 targeted-W53 评 P43，就是拿 Dᵢ 自己当证据。holdout-10 已正确排除了 D⁻，targeted 集没有。
4. **expect_not 的来源在反馈里看不到**：高血糖与波动-r60 带 `expect_not: [R22_黎明现象]`，但 0772 的 truth / note 都没说 R22 是假阳性。加上引擎 `validate` 在 guard 失败后仍跑并收集 post_rules，这条 expect_not 迫使 P51a 一并改 R22 分母。R22 的改法有 IR 依据（14 天窗口），但「R22 不该响」这一标签应由业务侧明说。同理 0770（李女士转介，带 soft R22，判 correct）与这条 expect_not 口径相反，需要本体负责人统一。
5. **反馈里的「待确认」仍按 wrong 立案**：0723（「评分」是否指服务分层）、0772（强化是否算结论层）、0760（返回的是否 14 天汇总）都附了待确认，标签仍是 wrong。P48 / P51 是按标签做的，裁决时若改判 correct，对应 Dᵢ 应撤。
6. **五条朴素规则对漏拦类缺陷大多结构性不适用**：N1 / N2 / N4 都只会让规则更放行，本轮 11 个缺陷里 10 个是漏拦，P-A 的朴素修因此集中在 N3 / N5，三个缺陷一份朴素修都没有。如果 P-A 想在漏拦类上也有对照，需要预登记对应的「机械收紧」规则（例如「收紧阈值」「把规则补挂到 Dᵢ 的动作上」），而不是在本轮临时发明。
7. **P47a 与 P47b1 在一切可得案例上逐行相同**：两者只在拒绝消息、以及无 alert_id 的调用上有差别，而现有挂载点的 alert_id 都是必填。P-A 若按通过率比较根因修与朴素修，这一对会被记成「无差别」。
8. **h₁₀ 的 R46 挂载与 IR 不一致**：IR 只把 R46 挂在 `配置患者告警与静音策略` 上，h₁₀ 实现另挂在 `放宽告警阈值`，P46a 再补到 `收紧告警阈值`。建议本体负责人在 IR §5 的动作表里把 R46 的挂载补齐，避免实现与 IR 继续漂移。R24b（P49a 补挂到 `群内答复患者`）、R01（P51a 补挂到 `生成方案草稿`）同理。
