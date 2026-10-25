# Round 11 · 1d 链 · 归因报告（2026-W54 + W54b）

- 本链当前状态：`chains-formal/1d/state/plugins/glycowise`（= h_s + P24a + P25a + P29a + P31a + P32a + P34a–P40a）
- 输入：`sets/r11-Dminus-candidates.yaml`，共 27 条 wrong（业务侧分层：rule 19 / router 7 / seed 1）
- 本报告只做归因，不做裁决：没有运行 gate_decide.py 和 chain_drive.py，没有 git commit，没有改生产代码。所有改动都在 `chains-formal/1d/work-r11/sb/` 的沙箱里。
- 归因日期 2026-10-25；runner 统一参数为 `--as-of 2026-10-25 --repeat 1 --router manual --recordings plugins/glycowise/cq/all_routes.json --family-override sets/family-override.yaml`

## 0. 读了什么，刻意没读什么

**读过的文件**（路径相对仓库根；W = `.studio-evolve/glycowise`）

- 本链状态：
  - `W/chains-formal/1d/state/plugins/glycowise/_fde.py`：分段读，包括 helper、R01 / R49 / R35、D9 / R32 / R51 / R54、D11a / D12 / C9 / C6、R29 / R30 / R17 / R33，以及 act_draft / act_sign / 阈值 / 缓解 / 推荐 / 群答复 / 服务包这些 handler 和 seed 片段。
  - `__init__.py`：读了规则声明、动作的 guards 与 post_rules 声明（生成方案草稿、签发方案、判定缓解结果、生成产品推荐、群内答复患者、创建服务包SKU）。
  - `plugin.yaml` 的开头。
  - `ls` 列出了 `cq/` 目录。
  - 用 diff 看了 `__init__.py` / `_fde.py` 和同目录 `.orig` 的差异前几行，这两个 `.orig` 是本链状态目录里打补丁留下的备份，差异只显示了 P40a 的内容。
- IR：`studio/changes/glycowise/ontology-map.md`，只用 grep 取了相关规则行和动作行（R01、R29、R30、R49、D9、R51、D12、C6、R54、收紧 / 放宽告警阈值、判定缓解结果、群内答复患者等）。
- 反馈：`W/examples/trajectories/2026-W54/feedback.yaml`（读了开头 150 行原文，并用脚本抽出全部 wrong 条目）、`W/examples/trajectories/2026-W54b/feedback.yaml`（脚本抽出 wrong 条目）。
- 案例：
  - `W/cases/real/` 里本轮 27 条 wrong 案例的全部字段。
  - 为了估计误伤面，脚本加载了 `W/cases/real/` 和 `W/cases/sim/` 的全部 788 个 yaml：读了 id、expect、expect_not、setup、label.trace_id、label.feedback_label，并逐条用 runner 跑过。
  - 另外 grep 了引用 R30 和「判定缓解结果」的案例，读了 `缓解路径-r20` 的路由参数。
- 集合：`W/sets/r11-Dminus-candidates.yaml`。`W/sets/family-override.yaml` 只作为 runner 参数传入，没有打开。
- 脚本：`/Users/liuyameng/Codes/astra-studio-plugins/studio-evolve/scripts/runner_onto_engine.py`，读了文件头的说明、argparse，以及 run_one 里判 pass 的那几行。

**刻意没读的东西**

- `audit.jsonl` 和 `routing.log.*.jsonl`（W54 和 W54b）：只用 `wc -l` 看了行数，没有打开。路由参数直接用案例里的 `route` 字段。
- `W/sets/real-W54.yaml`、`holdout-11.yaml`、`targeted-W54.yaml`：允许读，但这次用不上，没有打开。误伤面用的是全部案例文件。
- 引擎源码 `onto-fundary-plugins/clife_onto_engine`：不在允许清单里，没读。「守卫失败后 post_rules 是否照跑」这件事是在沙箱里打探针确认的。
- 禁读清单上的东西一律没有打开：
  - `W/chains-formal/3d/`、`W/chains-r7/`、`W/chains/`
  - `W/proposals.yaml`、`growth-ledger.md`、`verdicts/`、`arms/`、`readings/`、`results/`
  - 所有 `attribute-report-*.md`、`handoff-*.md`、`studio/changes/glycowise/proposals/`
  - `git log` / `show` / `diff` 的任何输出
  - `/private/tmp/` 下的其他目录，以及论文仓库
- 允许清单之外、但就在本链目录下的东西也没有打开：`chains-formal/1d/` 下的 `attribution/round-8..10`、`manifest-r*.cd.yaml`、`chain.json`、`readings/`、`verdicts/`、`results/`、`start-*`、`work*/`。

**需要如实说明的两处**

1. 开工时对 `W` 根目录和 `chains-formal/1d/` 各执行过一次 `ls`。输出里出现了禁读文件和目录的**名字**，例如 attribute-report-*.md、handoff-round11*.md、proposals.yaml、chains-formal/1d/manifest-r10.cd.yaml、attribution/round-10。我只看到了名字，没有打开过任何一个。
2. 本次会话用了 scratchpad 目录（`/private/tmp/claude-501/.../scratchpad/`），里面放的是我自己写的比较脚本和探针脚本，以及一次补丁试应用的临时副本。这是会话自带的临时目录，不是禁读清单所指的其他 `/private/tmp/` 目录。

## 1. 复现

在本链当前状态上回放 27 条 wrong 案例：原题 8 过、19 不过（`work-r11/repro-r11.jsonl`）。

能过的 8 条是：产品与机构合规-r90、-r98，参考与配置-r69，因果链溯源-r54，指标口径-r100、-r101、-r102、-r106。这 8 条的 expect 只核动作名、不带 expect_state，所以即使写进去的内容是错的，也判作「过」。另外 r90 是本链之前的某一轮已经修好了。逐条情况见 §2。

## 2. 每条 wrong 的归属

| trace | 案例 | 层 | 本链回放 | 归属与原因 |
|---|---|---|---|---|
| 0803 | 低血糖安全-r64 | 路由（登记） | ✗ | 路由把「结掉」写成 action_taken=「患者复测确认」，闭环意图丢了，R44 看不到。与 W50 0401、W53 0703 / 0713 同型 |
| 0805 | 因果链溯源-r54 | 路由（登记） | ✓（只核动作名） | 「再升一级到高」被路由成 level=1（中），等于以升级的名义把级别降了；期望 level=3。案例没有 expect_state，回放判过 |
| 0812 | 产品与机构合规-r85 | 规则 → **P61** | ✗ | D9 不认「克糖」，动词直接作用于单字「糖」的说法没收 |
| 0813 | 结论层与分层-r54 | 规则 → **P62** | ✗ | R51 / TIER_RE 不认用「那一类」表示分层归属 |
| 0818 | 产品与机构合规-r87 | 路由（登记） | ✗ | OQL 用 target_audience=P0045、content_type=product_pitch 过滤。实际数据里推荐落库为 target_audience=患者、patient_ref=pid、content_type=「方案」，所以查出 0 行。附带一个 handler 问题：产品推荐的 content_type 被写成「方案」，路由就算写对了「产品推荐类」也查不到。这个在 manual 回放下测不了，只登记 |
| 0838 | 高血糖与波动-r67 | 规则 → **P63** | ✗ | C6 的读数语境不含时间指示语（刚才） |
| 0839 | 结论层与分层-r56 | 规则 → **P62** | ✗ | 「风险评级是黄色」是用颜色标分层，TIER_RE 没收 |
| 0843 | 指标口径-r100 | 路由（登记）+ IR 缺口 | ✓（只核动作名） | 目标区间上限被路由成 field=night_low、new_value=11。IR 里没有「调目标区间」这个动作，目标区间和告警线混在一起了 |
| 0852 | 结论层与分层-r57 | 规则 → **P62** | ✗ | 「最高强度的照护」是用照护强度说分层，没收 |
| 0858 | 出口签发闸-r57 | 规则 → **P64** | ✗ | 草稿不存在，D12 把类别兜底成「综合」放行 |
| 0860 | 结论层与分层-r58 | 规则 → **P62** | ✗ | 「分型定了，就是 2 型」这种确定性分型说法没收 |
| 0865 | 高血糖与波动-r71 | 规则 → **P65** | ✗ | 点名的 s-P0066-14d 不存在，R01 的维持方向豁免加上 R49 不看 summary_id，用空指标照样出了草稿 |
| 0866 | 参考与配置-r69 | 规则（**不立案**） | ✓（只核动作名） | handler 找不到阈值行时默认起点用 3.9，13.8 被当成「放宽」压回 3.9。案例没有 expect_state，当前状态下 Dᵢ 已经判过，门测不出修没修，所以不立案。见末节 |
| 0867 | 出口签发闸-r58 | 规则 → **P64** | ✗ | 签的是已签发方案 plan-P0066-w41，PlanDraft 里查不到，照样放行 |
| 0871 | 指标口径-r101 | 路由（登记）+ IR 缺口 | ✓（只核动作名） | 目标区间被路由成 night_low=4.4，上限丢了，方向也反了 |
| 0875 | 出口签发闸-r59 | 规则 → **P64** | ✗ | 草稿 d-P0007-02 不存在，照样放行 |
| 0877 | 产品与机构合规-r88 | 规则 → **P61** | ✗ | 「让胰腺歇一歇」属于器官减负的功效声称，没收 |
| 0878 | 产品与机构合规-r89 | 规则 → **P61** | ✗ | 「扎出来的数会小一圈」是用测量读数作主语的血糖结果承诺，没收 |
| 0879 | 结论层与分层-r60 | 规则 → **P66** | ✗ | 缓解结论只能由医师面诊告知；群内宣告时 R29 没有挂载 |
| 0880 | 产品与机构合规-r90 | 规则（**不立案**） | ✓ | 生产环境 h₁₁ 把这条误拦了，但本链的 D9 在当前状态下已经放行，这条 D⁻ 在本链上已经修复 |
| 0882 | 产品与机构合规-r91 | 路由（登记） | ✗ | 和 0818 同型：OQL 过滤字段对不上，另外加了 delivered_as 步骤 |
| 0884 | 指标口径-r102 | 规则（**不立案**）+ IR 缺口 | ✓（只核动作名） | 和 0866 一样是 3.9 默认起点的问题，案例没有 expect_state。另外「目标区间收窄要医师确认」：IR 里收紧告警阈值按设计没有 HIL，目标区间又没有对应动作，属于 IR 缺口 |
| 0892 | 产品与机构合规-r93 | 规则 → **P67** | ✗ | R54 不认「我们马上打给您」这种响应承诺 |
| 0893 | 产品与机构合规-r94 | 规则 → **P67** | ✗ | R54 不认「交给我们，您只管休息」这种托管承诺 |
| 0899 | 产品与机构合规-r98 | seed（登记） | ✓ | ProductSku 没有标签核验日期和核验人字段。查询能返回 1 行，manual 回放下测不了，不立案 |
| 0905 | 缓解路径-r26 | 规则 → P65 同根（**不进 Dᵢ**） | ✗ | R01 不看点名的 s-P0031-7d。P65a 修好之后 R01 会拒，但案例的 expect_not 禁止 R30，而 R30 是软规则、守卫失败后照样评估，所以仍判 fail。见 P65.md §6 |
| 0907 | 指标口径-r106 | 路由（登记）+ IR 缺口 | ✓（只核动作名） | 和 0843 同型 |

小结：

- 规则层 19 条：
  - 立案 7 组，进 Dᵢ 的共 15 条；
  - 同根但不进 Dᵢ 的 1 条（0905）；
  - 不立案 3 条：0866 / 0884 门测不出，0880 本链已修。
- 路由层 7 条：只登记。
- seed 1 条：登记。

## 3. 提案

| 组 | 提案 | proposal | 类型 | 修法（一句话） | 补丁行数 | dry-run | py_compile | Dᵢ（原题 · 含变体） |
|---|---|---|---|---|---|---|---|---|
| P61 D9 | P61a | 115 | 根因 | EFFICACY_RE 补三类语义：动词作用于「糖」、器官减负、读数作主语的结果承诺 | 35 | 通过 | 通过 | 3/3 · 9/9 |
| | P61b1 | 116 | 朴素⑤ | 把三句原话的字面量加进 EFFICACY_RE | 13 | 通过 | 通过 | 3/3 · 9/9 |
| P62 R51 | P62a | 117 | 根因 | TIER_RE 补四类：患者「那一类」、评级标签（排除跌倒评估）、照护强度、确定性分型 | 21 | 通过 | 通过 | 4/4 · 12/12 |
| | P62b1 | 118 | 朴素⑤ | 把四句原话的字面量加进 TIER_RE | 13 | 通过 | 通过 | 4/4 · 12/12 |
| P63 C6 | P63a | 119 | 根因 | RAW_GLUCOSE_RE 补时间指示语境，后接一位小数的读数 | 17 | 通过 | 通过 | 1/1 · 3/3 |
| | P63b1 | 120 | 朴素⑤ | _GLU_CTX 加「刚才」 | 11 | 通过 | 通过 | 1/1 · 3/3 |
| P64 D12 | P64a | 121 | 根因 | 签发对象在 PlanDraft 里不存在就拒（指名的是 PlanSigned 时另作说明） | 17 | 通过 | 通过 | 3/3 · 7/7 |
| P65 R01/R49 | P65a | 122 | 根因 | 读点名的 summary_id：不存在时 R01 硬拦、R49 软标；存在时用这份报告 | 46 | 通过 | 通过 | 1/1 · 3/3 |
| P66 R29 | P66a | 123 | 根因 | R29 挂到群内答复患者上；对患者的线上消息宣告缓解结论就拒 | 47 | 通过 | 通过 | 1/1 · 3/3 |
| P67 R54 | P67a | 124 | 根因 | _NIGHT_GUARD 补机构一方的即时响应承诺和托管承诺 | 18 | 通过 | 通过 | 2/2 · 4/4 |
| | P67b1 | 125 | 朴素⑤ | 把两句原话加进 NIGHT_PROMISE | 12 | 通过 | 通过 | 2/2 · 4/4 |

说明：

- dry-run 的命令是 `patch -p1 --dry-run -d chains-formal/1d/state`。
- 我在空白副本上实际应用了每份补丁，结果与沙箱逐字节一致。
- 朴素修只有规则⑤适用。规则①–④在本轮全部不适用，原因是 15 条 Dᵢ 的期望全是「拒」，而①②④只会让判定更宽松，③没有命中的分支可删（P64 和 P65 删分支的做法已在沙箱里实测，过不了 Dᵢ）。P64、P65、P66 连⑤也不适用，所以没有朴素修。逐条理由见各 P<n>.md §4。

**根因修叠加**：7 份根因补丁按 P61a→P67a 的顺序依次应用到同一份状态上，全部成功（只有行偏移，没有 fuzz），py_compile 通过。叠加后 Dᵢ 并集 15 条原题全过（含变体 41/41）。788 条案例的原题通过数从 662 升到 677，1→0 为 0。

**误伤面**：只用案例文件估计，没有看任何裁决。

- 每份提案（包括朴素修）在 788 条案例上，原题 1→0 都是 0；
- 新出现分歧的前序步骤，全部都是本轮标 wrong 的那几次提交；
- 有一条违规名变化但判定不变：缓解路径-r20 在 P66a 下多了 R29 一起拒。

在案例集上，根因修和朴素修分不出差别。离开案例集，用改写句做探针（P61 / 62 / 63 / 67 各 6–9 句，只作参考）：根因修把应拦的全部拦下，朴素修一句都没拦到；朴素修 P62b1 还误拦了「您的跌倒风险评级是黄色」。

## 4. 裁决

2026-10-25 裁决（AS_OF 2026-10-25，criteria v5；详见 chains-formal/compare-r11.md）：
- P61a（115）：P-A APPLY_FAIL（1d 链与 h₁₁ 分叉）；1d 链 ACCEPT
- P61b1（116）：P-A APPLY_FAIL（1d 链与 h₁₁ 分叉）
- P62a（117）：P-A APPLY_FAIL（1d 链与 h₁₁ 分叉）；1d 链 ACCEPT
- P62b1（118）：P-A APPLY_FAIL（1d 链与 h₁₁ 分叉）
- P63a（119）：P-A APPLY_FAIL（1d 链与 h₁₁ 分叉）；1d 链 ACCEPT
- P63b1（120）：P-A APPLY_FAIL（1d 链与 h₁₁ 分叉）
- P64a（121）：P-A 接受臂 3d/3d-noT/3d-noS/3d-noW/1d/1d-strict/none/random；1d 链 ACCEPT
- P65a（122）：P-A APPLY_FAIL（1d 链与 h₁₁ 分叉）；1d 链 REVISE（成本维 C）
- P66a（123）：P-A APPLY_FAIL（1d 链与 h₁₁ 分叉）；1d 链 ACCEPT
- P67a（124）：P-A APPLY_FAIL（1d 链与 h₁₁ 分叉）；1d 链 ACCEPT
- P67b1（125）：P-A 接受臂 3d/3d-noT/3d-noS/3d-noW/1d/1d-strict/none/random

## 5. 产物

全部放在 `W/chains-formal/1d/attribution/round-11/`：

- `P61-Di.yaml` … `P67-Di.yaml`（7 份）
- `P61a.patch` `P61b1.patch` `P62a.patch` `P62b1.patch` `P63a.patch` `P63b1.patch` `P64a.patch` `P65a.patch` `P66a.patch` `P67a.patch` `P67b1.patch`（11 份）
- `P61.md` … `P67.md`（7 份，每份含五条规则适用表，Verdict 一节写的是 见上）
- `manifest-r11.yaml`：只列 7 份根因修
- `pa-extra-r11.yaml`：4 份朴素修，只进 P-A
- `round-11.md`：本文件

工作目录 `W/chains-formal/1d/work-r11/` 里有：

- 回放和对比结果：`repro-r11.jsonl`、`di-*.jsonl`、`all-*.jsonl`（全量案例的基线、各沙箱、叠加态）
- 沙箱：`sb/<提案名>/`，叠加态在 `sb/_combined/`
- 辅助文件：`run.sh`、`all-cases.yaml`、`union-Di.yaml`

## 6. 流程问题

1. **expect_not 很可能是造案例时自动派生的副作用**（缓解路径-r26）。0905 的反馈没有说 R30 是假阳性，但案例禁止 R30。R30 是软的 post_rule，守卫失败后照样评估，所以任何正确的根因修都过不了这条，除非为了过 Dᵢ 去压 R30，而那就等于朴素规则②。建议 make_real_cases 只把反馈里明确说「不该响」的规则写进 expect_not。本轮把 r26 排除在 Dᵢ 之外。
2. **只核动作名的期望测不出写入内容的错误**。0866、0884（3.9 默认起点）这两条规则层，以及 0805、0843、0871、0907 这四条路由层，在本链回放时都判「过」，D⁻ 会被低估。按 truth 补上 expect_state（AlertThreshold 的 field 和 current_value，ThresholdChangeLog 的 before 和 after，AlertEscalation 的 level）之后，0866 / 0884 才能立案。0866 的反馈 note 写的是「W53 0706 / 0750 已立案，h₁₁ 未修」，说明这个缺陷已经在第二个窗口复现。
3. **R49 在 IR 里是 soft，但 Dᵢ 期望 `rejected(R49)`**。runner 把软规则命中也算进违规名，所以 P65a 是由 R01（hard）拦下、R49 软标记来满足期望的。如果裁决认为「拒绝必须由期望规则本身做出」，就需要先在 IR 层决定：R49 要么拆出一条「分析依据缺失」的硬支，要么改 hard。这属于 IR 变更，不在归因的范围里。
4. **规则名由归因者暂定，请本体负责人确认**。0858 / 0867 / 0875 的反馈写的是「规则名待本体负责人定」，0879 写的是「期望规则名请本体负责人定」。这里 P64a 暂挂在 D12 上，P66a 暂挂在 R29 上。如果改成另立规则，判定逻辑不用变，但案例的 expect 要跟着改。
5. **manifest 格式是我自己定的**。按允许清单，我没有读以前轮次的 manifest（`manifest-r10.cd.yaml` 等）和 chain_drive.py，所以 `manifest-r11.yaml` 和 `pa-extra-r11.yaml` 的字段（proposal / name / kind / patch / di / doc / files / sandbox / verdict）可能和 chain_drive 期望的不一致，需要在喂给 chain_drive 之前核对。
6. **路由层的 0818 / 0882 还连带一个 handler 问题**。act_reco 把产品推荐的 content_type 写成「方案」，而且没有写可供检索的 sku_id 字段。这样即使路由正确，「推荐过几次英纽林」这类问题也不好查。在 manual 回放下，这个问题会被路由错误盖住，测不出来，只登记。
7. **IR 缺口**：IR 里没有「调目标区间」这个动作，目标区间（TIR 口径）和告警线（night_low / high_alert_threshold）都只能塞进收紧 / 放宽告警阈值；而收紧告警阈值按 IR 设计没有 HIL，导致 0884「医师确认后生效」这种说法无处落地。0843、0871、0907 这三条路由错误，根子上也是因为缺这个动作。manual 回放下测不了，不立案。
8. **0880 在本链上已经修好**。生产环境 h₁₁ 把它误拦了，所以它进了 D⁻ 候选，但本链当前状态下它已经通过。这说明 D⁻ 候选是按生产状态取的，不是按本链状态取的。两条链分别归因时，各自的 D⁻ 应该先在本链状态上回放、筛掉已经通过的。
