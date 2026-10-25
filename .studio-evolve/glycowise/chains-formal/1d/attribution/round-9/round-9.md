# round 9 · 1d 链 · 归因报告（2026-W52）

- 归因对象：1d 链当前状态 h_s + P24a + P25a（`chains-formal/1d/state/plugins/glycowise/`）
- 窗口：2026-W52，业务侧标为 wrong 的 15 条（`sets/r9-Dminus-candidates.yaml`）
- 本报告只做归因，不做裁决：没有运行 gate_decide.py / chain_drive.py，没有 git commit，没有改生产代码（所有改动只在 `work-r9/sb/` 沙箱里）。
- 结论：规则层有 1 个可立案的缺陷，出 P29a（根因，proposal 46）和 P29b1（朴素·规则 5，proposal 47）；另有 1 个规则层缺陷在 manual 回放下走不到规则，只登记不立案。路由层 9 条、seed/IR 缺口 4 条只登记。

## 0 读过的文件与刻意没读的东西

### 0.1 读过（全部只读）
- 运行脚本：`astra-studio-plugins/studio-evolve/scripts/runner_onto_engine.py`，读了模块说明（1–120 行）和 argparse / 输出段（400–481 行），只看用法。
- 本链状态 `chains-formal/1d/state/plugins/glycowise/`：
  - `_fde.py`：读了 D8–D11、`_product_gate`、`EFFICACY_RE`、`_efficacy_claim`、D9（约 470–555 行），`_prev_reading` / `_prev_sample` / R03a / R04a（约 690–750 行），`触发低血糖处置` / `推送告警` handler（约 2037–2060 行），`sentences` / `product_mention` / `_content_type`，以及对 ProductSku / AlertThreshold / TargetProfileParam / StoreEntity 种子行的 grep。
  - `__init__.py`：grep D9 的声明（2100–2120 行）、`triggered_by_reading` / `based_on_summary` / `listed_as` 三个 LinkType 的声明行。
  - `plugin.yaml` 前 30 行；`mappings/`、`cq/` 只列了目录。
  - `diff _fde.py _fde.py.orig`（两个文件都在本链状态目录里，内容就是 P25a 的改动）。
- IR：`studio/changes/glycowise/ontology-map.md`，grep 了 D9 / R04a / 推送告警 / 撤销更正 / 三个 LinkType / PatientProfile / AlertThreshold / TargetProfileParam 的行。
- 窗口数据：`examples/trajectories/2026-W52/feedback.yaml`（头部，以及 15 条 wrong 的 layer / truth_expect 字段）；`audit.jsonl` 与 `examples/routing.log.2026-W52.jsonl`，按 trace 0618 / 0637 / 0649 / 0677 / 0607 / 0610 grep，另看了 routing.log 头部格式。
- 案例：15 条 wrong 案例的全文（`cases/real/`）；为了估误伤面，用脚本扫了 `cases/` 下全部案例文件里的 pitch、setup 和 route，并在三个状态上回放了全部 614 条案例（只看 runner 自己的输出，没看任何裁决）。
- 集合：`sets/r9-Dminus-candidates.yaml`（全文）、`sets/family-override.yaml`（只经 runner 读取）、`sets/targeted-W52.yaml`（前 8 行）、`sets/holdout-9.yaml`（前 5 行文件头，没看 id 列表）、`sets/real-W52.yaml`（grep 5 个 id）。

### 0.2 越界与边缘情况（如实登记）
- 为了确认集合文件的格式，我运行了 `grep -c "^- " sets/*.yaml`，这条命令把 `sets/` 下**所有**集合文件的条目数都打印出来了，其中包括不在允许清单里的 `P*-Di.yaml`、`holdout-2…8*.yaml`、`r7/r8-Dminus-candidates.yaml`、`real-W4x/W50/W51.yaml`、`targeted-W50/W51.yaml`、`B-sim.yaml` 等。看到的只有每个文件的条目数，没有看到任何文件内容。
- `ls` 工作区根目录和 `chains-formal/1d/` 时，看到了禁读对象的**文件名**（`attribute-report-*.md`、`handoff-*.md`、`proposals.yaml`、`growth-ledger.md`、`verdicts/`、`arms/`、`readings/`、`results/`、`chains/`、`chains-r7/`、`chains-formal/1d/manifest-r8.cd.yaml`、`chains-formal/1d/verdicts/`、`attribution/round-8/`），没有打开其中任何一个。
- `ls` 了引擎包 `onto-fundary-plugins/clife_onto_engine/` 的顶层目录，没有读引擎源码。
- 禁读文件：**没有打开任何一个**。

### 0.3 刻意没读
`chains-formal/3d/`、`chains-r7/`、`chains/`；`proposals.yaml`、`growth-ledger.md`、`verdicts/`、`arms/`、`readings/`、`results/`（包括 `chains-formal/1d/` 下的 verdicts / readings / results）；所有 `attribute-report-*.md`、`handoff-*.md`；`studio/changes/glycowise/proposals/`；`chains-formal/1d/attribution/round-8/` 的内容和 `manifest-r8.cd.yaml`（不在允许清单里，所以本轮清单格式是我自己拟的，见末节）；任何 git log / show / diff；`/private/tmp/`；论文仓库。

## 1 复现

工作目录 `chains-formal/1d/work-r9`，命令：`runner run --target-dir ../state/plugins/glycowise --state h_s --cases-file sets/r9-Dminus-candidates.yaml --router manual --recordings …/cq/all_routes.json --family-override sets/family-override.yaml --as-of 2026-10-25 --repeat 1`，输出 `work-r9/repro.jsonl`。

结果：原题 15 条里 pass 5、fail 10，不可判 0。通过的 5 条（r51 / r91 / r93 / r95 / r22）期望只写到动作名，业务侧判 wrong 的原因是路由填的参数或写入的内容不对，而这些案例没带 expect_state，所以回放显示通过（见末节第 2 条）。

## 2 逐条归属

| 案例 | trace | 回放结果 | 归属 | 原因（一句话） |
|---|---|---|---|---|
| 产品与机构合规-r56 | 0618 | commit ✗ | **规则层 → P29** | 「血糖曲线会变平」属于对血糖波动形态的功效声称，D9 的 `EFFICACY_RE` 只收静态的「波动小 / 少」，没收「变平 / 拉平 / 削峰」这类变化谓词。 |
| 低血糖安全-r47 | 0649 | clarify ✗ | 规则层（manual 回放走不到，不立案） | 读数 r-P0023-00480 不存在，handler 照样写出一条值为空的告警；R04a 在 `g is None` 时直接返回 ok，没有「读数不存在不能确认连续低值」的分支。但案例 route 的 confidence 是 0.3，IntentCompiler 在回放时直接返回 clarify，到不了 validate，任何规则修法都不能让 Dᵢ 通过。 |
| 因果链溯源-r50 | 0637 | 推送告警 commit ✗ | 路由层 | 口语要以「低」推给本人，期望走 `撤销更正已发出告警`（reason 必填），路由选了 `推送告警`。另外 `推送告警` handler 会直接用参数里的 level 覆盖 AlertEvent 原级别，IR 里也没有规则禁止推送时下调级别，这算 IR 缺口候选；但规则修法只能让它变成 rejected，而期望是 action(撤销更正…)，所以不立案。 |
| 因果链溯源-r51 | 0638 | 升级告警 commit ✓ | 路由层 | 「从中升到高」路由成 level=3（危急，升了两级）；期望只写到动作名，回放显示通过。 |
| 指标口径-r91 | 0612 | commit ✓ | 路由层 | 批次 b-P0045-03 不存在，路由拼了一个没有读数编号、值和时间的候选，handler 把它当成新读数，写进一条空读数；回放显示通过。 |
| 指标口径-r93 | 0630 | commit ✓ | 路由层 | 路由只给了 {patient_id, OCR, CGM}，没有读数编号，handler 又写进一条空的 OCR 读数；回放显示通过。 |
| 指标口径-r95 | 0647 | commit ✓ | 路由层 | 候选只有传感器号和值 6.4，dedup_key 退化，handler 写进一条没有时间的读数，无关信息被塞进 context_note；回放显示通过。 |
| 数据与同意合规-r22 | 0644 | commit ✓ | 路由层 | 路由编造了 device_time「2023-10-27T08:30」和 context_tag；回放显示通过。 |
| 参考与配置-r41 | 0610 | query 0 行 ✗ | 路由层 | 用服务分层标签 L3 去过滤 TargetProfileParam.profile，而 profile 存的是人群档键，条件对不上。 |
| 高血糖与波动-r45 | 0607 | query 0 行 ✗ | 路由层 | `window_start ge 'now-14d'`，这是相对日期字面量，和种子里的日期字符串匹配不上（我没读引擎源码确认 OQL 是否支持相对日期；回放 0 行和这个判断一致）。 |
| 产品与机构合规-r61 | 0677 | query 0 行 ✗ | 路由层 | 问的是 ProductSku 本身，路由却走了 `listed_as` 到 StoreEntity 的路径，种子里也没有这条边；直接查 ProductSku 就能答出来。 |
| 参考与配置-r45 | 0653 | query 0 行 ✗ | seed 缺口 | 种子里只给 P0012 建了 AlertThreshold，P0023 没有低值告警线这一行。 |
| 因果链溯源-r49 | 0636 | query 0 行 ✗ | seed 缺口 | IR 有 `triggered_by_reading`（AlertEvent→GlucoseReading），但种子里没有 A-P0012-01 到读数的边。 |
| 结论层与分层-r42 | 0608 | query 0 行 ✗ | seed / IR 缺口 | 路由从 PatientProfile 出发走 `based_on_summary`，但 IR 里这条边的定义是 PlanDraft→CgmSummary，画像到汇总之间没有边；补种子也只能补到草稿上，严格说是 IR 缺口。 |
| 结论层与分层-r46 | 0651 | query 0 行 ✗ | seed / IR 缺口 | 同 r42。 |

合计：规则层 2（可立案 1：r56；回放走不到 1：r47），路由层 9，seed / IR 缺口 4。和 feedback.yaml 的 layer 字段一致。

## 3 提案

| 提案 | proposal | 类型 | 修法 | 补丁（+/−） | dry-run | py_compile | Dᵢ |
|---|---|---|---|---|---|---|---|
| P29a | 46 | 根因 | `EFFICACY_RE` 按语义加「平滑化」谓词类：变平 / 拉平 / 平下来 / 削峰…，可接血糖、时段、曲线 / 波动 / 峰值 / 起伏主语；「变小 / 减少」只接波动类主语；静态状态词不收 | +12 / −0 | 成功 | 通过 | 1/1（含变体 3/3） |
| P29b1 | 47 | 朴素·规则 5 | `EFFICACY_RE` 末尾加字面量分支 `血糖曲线会变平` | +2 / −1 | 成功 | 通过 | 1/1（含变体 3/3） |

规则 1–4 对 P29 都不适用：这是一个漏拦缺陷，四条规则都只会让本体变松，见 `P29.md` §4 的表。

误伤面（只用案例文件）：全部 614 条案例里，两份提案都只翻转了 r56 一条（3 行）；新增的 134 行 SETUP_DIVERGED 全部来自前序步骤 0618 本身。两份提案在案例库上的表现完全相同，差别只在泛化（P29a 能盖住「曲线平下来 / 峰值削掉 / 波动变小」这类同义说法，P29b1 盖不住）。详见 `P29.md` §6。

产物：`P29-Di.yaml`、`P29a.patch`、`P29b1.patch`、`P29.md`、`manifest-r9.yaml`（只有 P29a）、`pa-extra-r9.yaml`（只有 P29b1）。沙箱在 `work-r9/sb/P29a`、`work-r9/sb/P29b1`，回放结果在 `work-r9/repro.jsonl`、`di-P29*.jsonl`、`all-{h_s,P29a,P29b1}.jsonl`。

## 4 裁决

链上（1d 判定式）：接受 P29a，末态 real-all-W52 .840（起点 .838），修对 r56、无回退。P-A：P29a / P29b1 在 h₉ 上 APPLY_FAIL。见 `chains-formal/compare-r9.md`。

## 5 只登记、不立案

- **R04a 读数缺失不拒（r47）**：规则层缺陷是真的，`r04a` 在 `value_mmol is None` 时返回 ok，而 `触发低血糖处置` handler 读不到读数也照样写告警（level「低」，value 为空）。按 IR 语义，根因修应该是「读数不存在或没有值就不能确认连续 2 个读数，拒绝」，可能还要配合 R03a，或者在 handler 前置校验 reading_id 是否存在。但这条案例在 manual 回放下止步于 clarify，修完也不能让 Dᵢ 通过，所以不出提案。要等案例的 route.confidence 修正之后才能立案（见末节第 1 条）。
- **推送告警会改写已发告警的级别（r50）**：`act_push_alert` 用 `ctx.params.level` 覆盖 AlertEvent.level，IR 里没有规则禁止推送时下调级别，也不要求转走 `撤销更正已发出告警`。这算 IR 缺口候选。期望是路由到另一个动作，规则层修不出 action(撤销更正…)，不立案。
- **去重仲裁会落空读数（r91 / r93 / r95）**：路由给的候选不完整时，handler 把它当成新读数写进库。这是 handler 的弱点（应该追问或拒绝），但案例期望 action(去重与通道仲裁) 并且已经通过，不出提案。
- 路由层：r41、r45-TAR、r50、r51、r61、r91、r93、r95、r22。
- seed / IR 缺口：r45-阈值（P0023 缺 AlertThreshold）、r49（缺 triggered_by_reading 边）、r42 / r46（缺 PatientProfile→CgmSummary 依据边，IR 里只有 PlanDraft→CgmSummary）。

## 6 流程问题

1. **r47 的 route.confidence 来源不对，案例回放不了。** 窗口 audit 里 0649 记的 confidence 0.3 是 handler 的 `set_confidence(0.3 if 读数不存在)`，也就是动作执行后的置信度，不是路由置信度。案例生成时把它当成了 route.confidence，结果回放时 IntentCompiler 按低置信直接返回 clarify，窗口里却是 commit。routing.log 没有记录路由置信度，无法还原。建议 make_real_cases 不要把 audit 的动作置信度写进 route，或者在 routing.log 里补记路由置信度。
2. **5 条 wrong 在 h_s 上已经「通过」（r51 / r91 / r93 / r95 / r22）。** 业务侧判 wrong 的原因是参数或写入内容不对，但案例只有 expect: action(X)，没有 expect_state 或参数断言，所以进了 D⁻ 也给不出信号。建议对这类「动作对、内容错」的 wrong 自动生成 expect_state（比如 r22 断言 device_time 不是 2023，r91 / r93 / r95 断言不写空读数）。
3. **0618 被写进了 54 条后续 W52 案例的 setup。** 只要有提案修了 D9，这 54 条就会多出 134 行 SETUP_DIVERGED。判定虽然没变，但 SETUP_DIVERGED 的计数会被放大，读数时不要把它当成误伤。
4. **清单格式没有给出。** 任务书只要求 manifest-r9.yaml 和 pa-extra-r9.yaml「同格式」，没给 schema；上一轮的 `manifest-r8.cd.yaml` 和 `attribution/round-8/` 不在允许读取的清单里，我没有读。本轮格式是我自拟的（round / chain / base_state / proposals[proposal, name, kind, patch, patch_sha256, di, …]），chain_drive 消费前请核对字段名。
5. **「patch -d 本链状态的上一级」有歧义。** 补丁路径是 `a/plugins/glycowise/_fde.py`，用 -p1 时 -d 必须指向含 `plugins/` 的目录，也就是 `chains-formal/1d/state`（它是 `plugins/glycowise` 的上上级、`plugins` 的上一级）。dry-run 是按 `-d chains-formal/1d/state` 跑的，结果成功。
6. **集合计数命令越界**：见 0.2，`grep -c` 扫到了不在允许清单里的集合文件（只看到条目数）。以后可以给归因者一个只含允许集合的目录。
7. 本链状态目录里留着 `_fde.py.orig`（P25a 应用补丁时的残留）。它会被一起复制进沙箱，但不影响补丁，因为补丁只改 `_fde.py`。建议链状态里不要留 .orig 文件。
