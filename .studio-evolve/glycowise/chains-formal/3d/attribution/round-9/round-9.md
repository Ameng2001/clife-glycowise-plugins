# round 9 · 3d 链 · 归因报告（2026-W52）

- 基线：`chains-formal/3d/state/plugins/glycowise/`（h₉ = 生产）
- 窗口：2026-W52，业务侧标 wrong 15 条（`sets/r9-Dminus-candidates.yaml`）
- 本报告只做归因，不做裁决：没有运行 gate_decide.py / chain_drive.py，没有 git commit，没有改生产代码（state 目录只读，所有改动都在 `work-r9/sb/` 沙箱里）。
- 下文路径都相对 `.studio-evolve/glycowise/`。

## 0. 读取清单

### 0.1 读过的

| 文件 / 目录 | 怎么读的 |
|---|---|
| `sets/r9-Dminus-candidates.yaml` | 全文 |
| `cases/real/` 下 15 个 wrong 案例 | 全文（q / expect / label / route / variants / setup） |
| `cases/real/`、`cases/sim/` 全部案例 | 交给 runner 全量回放（估误伤面）；脚本扫描各案例 route / setup 里生成产品推荐 / 审核输出内容 / 发布宣传素材的文本参数，以及 action 型 route 的 confidence |
| `examples/trajectories/2026-W52/feedback.yaml` | 头部 + 全部 wrong 条目（truth_expect / note / layer）；另把 trace_id 与 audit 对照取 label |
| `examples/trajectories/2026-W52/audit.jsonl` | grep t-20261025-0649；脚本筛出生成产品推荐 / 审核输出内容 / 发布宣传素材这几行 |
| `examples/routing.log.2026-W52.jsonl` | 只 grep 了 t-20261025-0649 |
| `chains-formal/3d/state/plugins/glycowise/_fde.py` | 局部：文本工具（P / text_of / sentences / product_mention / staged_outbound / PRODUCT_WORDS / SENT_SPLIT / DISCLAIMER）、D9 / R32 / R03a / R04a / R05 与读数工具、act_reco / act_trigger_hypo / act_push_alert / act_ingest / act_dedup 开头、seed_reference_data 局部（TargetProfileParam / AlertThreshold / AlertEvent / ProductSku / StoreEntity） |
| `chains-formal/3d/state/plugins/glycowise/__init__.py` | 局部：D9 / R04a 的 spi.rule 声明，LinkType 注册（triggered_by_reading / based_on_summary / listed_as 等） |
| `chains-formal/3d/state/plugins/glycowise/plugin.yaml` | 头 20 行（拿 ontology id） |
| `chains-formal/3d/state/plugins/glycowise/cq/` | 只列了目录；all_routes.json 作为 `--recordings` 传给 runner，没打开 |
| `studio/changes/glycowise/ontology-map.md` | grep：D9、R04a、R03a、R05、R53、R52、R11、R01、R45 规则行；摄入读数 / 去重与通道仲裁 / 触发低血糖处置 / 推送告警 / 升级告警 / 撤销更正已发出告警 / 生成产品推荐 动作行；§4.4 低血糖口径说明 |
| `sets/family-override.yaml` | 只作为 `--family-override` 传给 runner |
| `sets/holdout-9.yaml`、`sets/targeted-W52.yaml`、`sets/real-W52.yaml` | 看过元数据与 id 列表（确认 r56 / r47 / r39 属于哪些集合）；P28a 设计定稿之后才看的，没有据此改补丁 |
| `astra-studio-plugins/studio-evolve/scripts/runner_onto_engine.py` | `--help`、`run --help`、前 120 行（模块说明 + freeze_date），grep h_prime |

### 0.2 允许清单之外读过的（不在禁读清单里，如实列出）

- **引擎源码** `onto-fundary-plugins/clife_onto_engine/intent/compiler.py`：只 grep 了 `confidence`，为了确认 r47 回放成 clarify 是因为 `min_confidence = 0.55`。另外列过一次 `clife_onto_engine/` 的目录，并对 oql 相对时间做了一次 grep，那次路径写错了，没有返回内容。
- 目录列表（只看到文件名，没有打开）：`.studio-evolve/glycowise/` 顶层（列表里有 attribute-report-*.md、handoff-*.md、proposals.yaml、growth-ledger.md、verdicts/、arms/、readings/、results/、chains/、chains-r7/ 等名字）；`chains-formal/3d/`（列表里有 attribution/round-8、manifest-r8.cd.yaml、chain.json、verdicts、readings、results、work 等名字）；`sets/`。

### 0.3 刻意没读的

- 禁读清单全部没有打开：`chains-formal/1d/`、`chains-r7/`、`chains/`；`proposals.yaml`、`growth-ledger.md`、`verdicts/`、`arms/`、`readings/`、`results/`；任何 `attribute-report-*.md`、`handoff-*.md`、`studio/changes/glycowise/proposals/`；没有跑过 `git log / show / diff`；`/private/tmp/` 下的任何目录（本次的 r47 临时验证放在 `chains-formal/3d/work-r9/scratch-r47/`，没有用 /private/tmp）；论文仓库。
- 也没有打开：`chains-formal/3d/attribution/round-8/`、`chains-formal/3d/manifest-r8.cd.yaml`、`chains-formal/3d/chain.json`、`chains-formal/3d/work/`。它们不在禁读清单里，但也不在允许清单里。所以 manifest 的格式是我自拟的（见第 6 节）。
- **没有误开禁读文件。**

## 1. 复现

命令（工作目录 `chains-formal/3d/work-r9`）：

```
runner_onto_engine.py run --engine-root onto-fundary-plugins --target-dir chains-formal/3d/state/plugins/glycowise \
  --ontology glycowise --state h_i --cases-dir cases --cases-file sets/r9-Dminus-candidates.yaml \
  --family-override sets/family-override.yaml --repeat 1 --router manual \
  --recordings chains-formal/3d/state/plugins/glycowise/cq/all_routes.json --as-of 2026-10-25 --out work-r9/repro-h9.jsonl
```

结果：15 案例、33 行，原题通过 5 / 15，没有不可判的行。产物 `work-r9/repro-h9.jsonl`。

| 案例 | trace | h₉ 回放 | pass |
|---|---|---|---|
| 产品与机构合规-r56 | 0618 | 生成产品推荐·commit（3 行） | 0 |
| 低血糖安全-r47 | 0649 | **clarify**（3 行） | 0 |
| 高血糖与波动-r45 | 0607 | query·0 行 | 0 |
| 结论层与分层-r42 | 0608 | query·0 行 | 0 |
| 参考与配置-r41 | 0610 | query·0 行 | 0 |
| 因果链溯源-r49 | 0636 | query·0 行 | 0 |
| 因果链溯源-r50 | 0637 | 推送告警·commit | 0 |
| 结论层与分层-r46 | 0651 | query·0 行 | 0 |
| 参考与配置-r45 | 0653 | query·0 行 | 0 |
| 产品与机构合规-r61 | 0677 | query·0 行 | 0 |
| 因果链溯源-r51 | 0638 | 升级告警·commit | **1** |
| 指标口径-r91 | 0612 | 去重与通道仲裁·commit | **1** |
| 指标口径-r93 | 0630 | 去重与通道仲裁·commit | **1** |
| 指标口径-r95 | 0647 | 去重与通道仲裁·commit | **1** |
| 数据与同意合规-r22 | 0644 | 摄入读数·commit | **1** |

最后 5 条在回放里判通过：这几个案例的 expect 只写了动作名，没有 `expect_state`，而错误恰恰在落库内容上（参数错 / 写了空读数 / 时间错三年），runner 判不出来。r47 窗口里是 committed，回放却成了 clarify，见第 2 节。

## 2. 逐条归属

规则层 2（立案 1、登记 1）/ 路由层 9（登记）/ seed 4（登记）。和候选集备注的 rule 2 / router 9 / seed 4 一致。

| 案例 | 层 | 原因（一句话） | 处置 |
|---|---|---|---|
| 产品与机构合规-r56（0618） | **规则** | D9 用「指标 + 列举谓词」判功效声称，「血糖曲线会变平」的「变平」不在谓词表里，漏判 | **立案 P28**（P28a 根因 / P28b1 朴素） |
| 低血糖安全-r47（0649） | **规则** | R04a（和 R03a）在读数不存在时 `g is None → ok`，act_trigger_hypo 读不到读数照样写告警；IR 要求连续 2 个读数确认，没有读数就不能放行 | **登记，不立案**：案例 route.confidence = 0.3，低于 IntentCompiler 的 0.55，回放成 clarify，任何规则修法都不能让 Dᵢ 通过（见第 5 节） |
| 高血糖与波动-r45（0607） | 路由 | OQL 用字面量 `now-14d` 比 window_start，ISO 日期按字符串比较时永远小于它，所以 0 行 | 登记 |
| 参考与配置-r41（0610） | 路由 | 用分层标签 L3 当 TargetProfileParam.profile 过滤（应为 elderly_high_risk） | 登记；另注：P0045 画像 target_profile=elderly，没有标 elderly_high_risk，属于 seed 口径问题，一并登记 |
| 指标口径-r91（0612） | 路由 | 路由凭空拼了不存在的批次 b-P0045-03，候选没有读数号 / 值 / 时间，无关信息写进 device_context | 登记；handler 缺陷见第 5 节 |
| 指标口径-r93（0630） | 路由 | 「那几条」被压成一个没有键的候选，没有展开成逐条，也没有追问 | 登记；同上 |
| 指标口径-r95（0647） | 路由 | 候选只有传感器号和值，没有序号和时间，无关信息写进 context_note | 登记；同上 |
| 因果链溯源-r50（0637） | 路由 | 下调已发出告警的级别应走「撤销更正已发出告警」，路由走了「推送告警」 | 登记；IR 缺口见第 5 节 |
| 因果链溯源-r51（0638） | 路由 | 「从中升到高」应填 level=2，路由填了 3（危急） | 登记；IR 编码不一致见第 5 节 |
| 数据与同意合规-r22（0644） | 路由 | 臆造 device_time 2023-10-27（差三年）和 context_tag | 登记 |
| 产品与机构合规-r61（0677） | 路由 | 为了表达「在架」多挂了一跳 listed_as→StoreEntity，seed 里没有边，0 行；不挂这一跳能查到 2 个 SKU | 登记（反馈也写了拿不准；ProductSku 没有上下架字段） |
| 结论层与分层-r42（0608） | seed（兼路由） | seed 没有任何关系边；而且 based_on_summary 的源类型是 PlanDraft，不是 PatientProfile，路由从 PatientProfile 出发挂这条边本身就是错路径 | 登记。按反馈注语（「查询走了非法路径就改 router」）应改归 router，请复核 |
| 结论层与分层-r46（0651） | seed（兼路由） | 同 r42 | 同上 |
| 因果链溯源-r49（0636） | seed（兼路由） | seed 没有 triggered_by_reading 边；而且 triggered_by_reading 是 AlertEvent→GlucoseReading，从 AlertEvent 出发应走 out，路由写了 in | 登记，同上请复核 |
| 参考与配置-r45（0653） | seed | seed 只给 P0012 建了 AlertThreshold，P0023 没有 | 登记 |

## 3. 提案与验证

详见 `P28.md`。

| 提案 | proposal | 类型 | 修法 | 补丁行数 | dry-run | py_compile | Dᵢ |
|---|---|---|---|---|---|---|---|
| P28a | 44 | 根因 | D9 反向判定：产品话术分句出现血糖类指标即视为功效暗示，只豁免监测提醒和不替代药物 / 遵医嘱声明，豁免按片段剔除 | 37（+17/−0） | 成功 | 通过 | 3/3 |
| P28b1 | 45 | 朴素·规则 5（把 Dᵢ 命中的字面量加进匹配） | GLYCEMIC_OUTCOME_RE 谓词表加「变平」 | 11（+1/−1） | 成功 | 通过 | 3/3 |

朴素规则 1–4 都不适用。原因：D9 这次是漏判，那四条都会让规则更少响，和 Dᵢ 需要的方向相反（逐条理由见 `P28.md` §4）。

误伤面（全部 614 案例，h₉ 对照）：两份提案的 pass 翻转都只有 r56 自己（原题通过 529→530）。P28a 让 r39 在原有 C4 拒绝之外多带一条 D9，仍然通过。两份提案都让 54 个 W52 后续案例的 setup 第 8 步（就是 0618）在候选上被拒，属于预期内的反事实，pass 不变。P28a 有一个推断出来的误伤面：「血糖高时先别吃」这类禁忌提醒会被判成暗示。案例库里没有这样的话术。

沙箱：`chains-formal/3d/work-r9/sb/P28a/`、`sb/P28b1/`；回放产物：`work-r9/Di-P28a.jsonl`、`Di-P28b1.jsonl`、`all-h9.jsonl`、`all-P28a.jsonl`、`all-P28b1.jsonl`。

## 4. 裁决

链上（3d 判定式）：接受 P28a，末态 real-all-W52 .840（起点 .838），修对 r56、无回退。P-A：P28a 七臂 + none 接受、random 拒；P28b1 八臂全接受。见 `chains-formal/compare-r9.md`。

## 5. 登记项（不立案）

### 5.1 规则层缺陷：R04a / R03a 在读数不存在时放行（r47 / 0649）

- 现象：读数 r-P0023-00480 在 seed 里不存在。`r04a` 里 `_reading(ctx)` 返回 `{}`，`g is None` 直接 `ok`。act_trigger_hypo 照样写出 level=「低」、value=None 的 AlertEvent，handler confidence 0.3。窗口里引擎 committed，audit 的 `rules_evaluated` 为空。
- 为什么不立案：案例的 `route.confidence = 0.3`，看起来是从 audit 的动作置信度（handler `set_confidence(0.3)`）抄过来的，不是路由置信度。IntentCompiler 的 `min_confidence = 0.55`，所以回放在路由这一步就成了 clarify，规则根本没有被评估。官方 Dᵢ 在任何规则修法下都过不了。全部真实案例里只有这一条的 action 型 route 置信度低于 0.55。
- 旁证（不算提案、不进清单）：`work-r9/scratch-r47/` 里复制了一份 route.confidence 改成 0.95 的临时案例（`低血糖安全-r47-conf`，不在 `cases/` 里）。h₉ 上 3 行都是 commit，重现了窗口；在 r04a 开头加「给了 reading_id 但读数不存在 → 拒」之后，3 行都拒 R04a，通过。根因修可以这样写：R03a / R04a 对「声称的触发读数不存在」直接拒，handler 读不到读数时不写告警。等案例的置信度修正以后再立案。

### 5.2 handler 缺陷：去重与通道仲裁对无键候选当新读数落库（r91 / r93 / r95）

act_dedup 在候选没有 reading_id 时会生成 `cand-<时间>`。候选既没有序号、值、时间，也找不到重复对象时，判成「新读数」写进一条空读数。IR 的意图是「按传感器序号去重」，没有键的候选应该拒或者追问，不该落库。这三个案例的 expect 只写了 `action(去重与通道仲裁)`，没有 expect_state，回放判通过，没有失败的 Dᵢ，测不了，不立案。建议给这类案例补上 expect_state（不应暂存新的 GlucoseReading），或把 expect 改成追问 / 拒绝。

### 5.3 IR 缺口

- **推送告警可以覆盖已发出告警的级别**（r50）：IR 里推送告警的 `level:string:required` 由调用方给，没有任何规则约束它和触发证据（AlertEvent.level / 读数值）一致，下调也不进人审。窗口里 L1（中）被改成「低」推给患者。按 IR 应走「撤销更正已发出告警」（reason 必填）。案例 expect 是另一个动作，回放的路由是固定的，规则修法测不了，不立案。
- **升级告警的 level 编码和 AlertEvent.level 不一致**（r51）：升级告警 `level:number`（1/2/3），AlertEvent.level 是枚举（低/中/高/危急），IR 没有给出换算表，路由在两套编码之间换算错了。回放判通过，测不了。
- **摄入读数的时间完整性**（r22）：IR 写的是「单位与时间完整性硬校验」，但没有规则检查 device_time 是否明显早于接收时间（差三年）。回放判通过，测不了。

### 5.4 路由层 / seed

见第 2 节表格，只登记。seed 侧有一个共性问题：seed_reference_data 一条关系边都没写，所有带 steps 的查询都必然是 0 行（r42 / r46 / r49，r61 也是）。

## 6. 流程问题

1. **案例的 route.confidence 抄的是动作置信度**：wrong 案例的 route.confidence 和 handler `set_confidence` 的值逐条吻合（r56 0.8 = act_reco，r50 1.0 = act_push_alert，r91/r95 0.95 = act_dedup，r47 0.3 = act_trigger_hypo），看起来 make_real_cases 取的是 audit 里的 `confidence`（动作置信度），不是路由置信度。大多数案例因为数值 ≥0.55 看不出影响，r47 因此回放成 clarify，规则层缺陷没法立案。建议 make_real_cases 从 routing log 取路由置信度；routing log 现在不记这个字段，记不了就填 1.0，或者不让 runner 对 route 套置信度闸。
2. **D⁻ 里有 5 条在 h₉ 上判通过**（r51 / r91 / r93 / r95 / r22）：业务侧判错的点在参数或落库内容，案例只写了 expect 的动作名，没有 expect_state。这些案例进了 D⁻ 也进不了「修后通过」的统计，抽 holdout 时又被排除，等于白白占了位置。建议落案例时按 label 补 expect_state，或单独标出「回放不可判」。
3. **manifest 格式没有规范可依**：允许清单里没有 manifest 格式说明（往轮的 manifest、gate_decide / chain_drive 的用法都不在允许清单里）。`manifest-r9.yaml` / `pa-extra-r9.yaml` 是自拟的自描述格式（proposal / name / kind / patch / di / checks …）。裁决前请核对字段名，和 gate_decide 的读法对一下。
4. **runner 的 `--recordings` 用相对路径会找不到**：任务书写的 `plugins/glycowise/cq/all_routes.json` 是相对 state 目录的，工作目录在 work-r9 时解析不到，本轮用了 state 下的绝对路径。所有 wrong 案例都带 route，不查 recordings，结果不受影响。
5. **seed 与路由的界线**：反馈把 r42 / r46 / r49 归 seed，但三条的 OQL 本身就走了源类型或方向不对的关系，按反馈自己的注语应该改归 router。IntentCompiler 没有拒掉这类非法路径，回放返回 0 行，不是 reject。建议在编译期校验 step 的 link 源类型和方向，这样这类问题能直接在路由层暴露。
6. **SETUP_DIVERGED 的连带面**：wrong 轨迹之后的同窗口案例都把这一步写进了 setup，修掉一条（如 0618）会让后面 54 个案例的 setup 分叉。这次 pass 都没变，但这类分叉会被计进误伤面统计，需要有一个口径：算不算误伤、怎么算。
