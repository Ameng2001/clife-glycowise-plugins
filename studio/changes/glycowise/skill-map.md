# Skill Map: glycowise（一期 · 第 0 层强制预留 + 第 1 层合规准入闸）

> Date: 2026-09-05
> Action: create
> 主导角色：`studio-insight/agents/architect.md`
> 事实基准：`decisions/confirmed-facts.md`（优先级高于本文）
> 上游：`brief.md` §Plugin Candidates · `opportunity-brief.md` §3/§5/§10 · `domain-canvas.md` §1/§6 · `behavior-matrix.md` §10 · `processes/` · `docs/PRD-控糖场景-一期-2026-09-05.md` 第五章
>
> ⚠ 技能定义要求读 `domain-map.md`。本项目走 studio-insight 路线，对应文件是 `domain-canvas.md`（20 个域，区分 Core-差异化与 Core-风险承载），本文按它读。

---

## 0. 本批范围与一句话结论

本批只拆两组：第 0 层六条强制预留（R-1~R-6 + 五条反向约束 ⊘1~⊘5），第 1 层十道合规准入闸（G1~G10）。

结论：**14 个 skill，归成 4 个插件。** 其中 `device-flow-compliance`（G2）判定为不该做成 skill，理由见 §3。

三件必须先说清楚的事：

1. 六条预留里只有 **R-6 有自己的落点**（OP-13 `audit-trail`）。R-1/R-3/R-5 落在 `cgm-ingest`、R-2 落在 `sync-health`、R-4 落在 `hypo-retro`——三个都在被 D-12 阻塞的那一支里。但**它们的不可逆性发生在"契约定成什么样"这一刻，不发生在"代码什么时候写"**。所以本批把这五条做成一个可校验的契约守卫（`reservation-contract-check`），契约现在冻结，实现等 D-12。
2. 第 1 层十项里有三项的主体是组织动作而非代码：G2 器械流转、G8 门店清查的清查部分、G3 话术库的编写与培训部分。§3 逐项分开。
3. R-6 是地基中的地基。它不是"第一个做的 skill"，它是**其余每个 skill 的上线前置条件**——留痕中间件没上线之前，任何写操作都不许上线，因为那段时间里其他闸门"我们拦住了"全都无法举证。依赖图中它是唯一一条对全部 skill 的硬边。

---

## 1. 能力清单（用户故事式）

### 1.1 第 0 层 · 强制预留

| # | 用户故事 | 落点 | 本批是否可做 |
|---|---|---|---|
| R-1 | 作为数据运维，我要让去重键锚在传感器序号上，这样二期两路数据才有共同锚点，GMI 基线不断裂 | `cgm-ingest` | 契约可冻结，实现被 D-12 阻塞 |
| R-2 | 作为数据运维，我要让云侧也算一条 carrier，这样"数据什么时候停了"一期就看得见 | `sync-health` | 同上 |
| R-3 | 作为临床与数据双方，我要把分母、质量谓词、日界时区一次定死并版本化，这样历史指标永远可比 | `cgm-ingest` + `glucose-metrics` | 同上 |
| R-4 | 作为临床，我要实时规则和回顾规则物理分开，这样二期不会重犯 C-01 | `hypo-retro` | 同上 |
| R-5 | 作为数据运维，我要原封不动留住厂商原始载荷，这样归一映射错了还能重算 | `cgm-ingest` | 同上 |
| R-6 | 作为合规官，我要留痕中间件先于任何写操作上线，这样其他闸门的拦截行为可举证 | `audit-trail` | **可做，且必须最先做** |
| ⊘1~⊘5 | 作为数据主体，我要同意不被打包、可分项、可撤回、不被子女代签，我的健康信息不出境 | `consent-ledger` + `family-account` | 一期部分可做（`family-account` 属下批） |

R-1/R-2/R-3/R-5 之所以能在 D-12 未答复时冻结契约：**它们回答的是"键怎么定、口径怎么算、留什么、监控表长什么样"，全部与"传感器能缓存几小时"无关。** D-12 决定的是同步节律与 `minimal-sync-app` 的形态，不决定这四条。R-4 同理，它是规则表的物理切分，与缓存深度无关。

### 1.2 第 1 层 · 合规准入闸

| G | 用户故事 | 覆盖域 |
|---|---|---|
| G1 | 作为患者，我要能分项授权、随时撤回，撤回后系统告诉我监测已停 | D7 |
| G2 | 作为店长，我要在不碰货不收款的前提下把患者交给持证方 | 边界外 X3 |
| G3 | 作为健管师，我要知道这句话能不能说；作为合规官，我要能抽检并留下证据 | D6b |
| G4 | 作为法务，我要 C 包承诺文本未定稿就卖不出去 | D11b |
| G5 | 作为合规官，我要系统生成的每一条对外内容都过一道确定性闸，且拦了什么有账可查 | D6a + D16 |
| G6 | 作为合规官，我要没有资质的人在系统里签不出方案 | D18 |
| G7 | 作为合规官，我要在智能体上线之前完成生成式 AI 备案，并给 AI 产出打上标识 | D14 |
| G8 | 作为店长，我要没做完清查的门店开不出服务包 SKU | D11a |
| G9 | 作为合规官，我要皮肤问题和脱落线索有一条通往器械不良事件上报的出口 | D8a |
| G10 | 作为患者家属，我要应急链末端有一个真实存在、能到场的人 | D4 |

---

## 2. 特征分析（技能第 1.5 步）

> 用户在线但本轮不停下提问。以下判断依据写全，结论一律标「待确认」。

| 特征 | 检测 | 依据 | 下游影响 |
|---|---|---|---|
| **stateful** | ✅ 待确认 | 同意状态机（S10）、凭证台账与到期日（S9）、承诺文本台账、不良事件 10/30 日时限追踪、话术版本台账、审计日志——六类状态全部跨会话持久，且留存 ≥3 年（PIPL 51/55） | 加一个 `init-workspace`，放在必装的 `glycowise-compliance` 里，建 `.glycowise/` 与六类台账骨架；其余三插件共用，不各建一份 |
| **hil-gated** | ✅ 待确认 | 至少五处人工闸：承诺文本法务定稿、门店清查确认单双签、抽检违规的申诉当场放行、不良事件严重性判定、`gate.override_requested` 二次审批 | 每处一个 skill，一个 skill 最多一个闸。`script-library` 与 `script-spotcheck` 因此拆开 |
| **kb-dependent** | ✅ 待确认 | 法条集（PIPL / 广告法 16,17 / 器械条例 41,45 / 器械不良事件办法 14,19 / 生成式 AI 办法 4,7,12 / 食安法 71,73 / 互联网诊疗细则 21）、禁用词与模式库、话术库两层结构、预审冻结模板集 | **不建 companion KB 插件。** 词库与话术库要被确定性匹配器读，不是被 LLM 检索——PRD FR-5.10 明确"确定性匹配为主，LLM 只做召回不做放行"。把它们做成插件级 `references/` 里的数据表 + 版本号，检索式 KB 会把一个硬闸变成一个概率闸 |
| **multi-pipeline** | ✅ 待确认 | 三条入口不同、步骤不同、产出不同的流水线：① **入组准入链**（触发=新患者：consent → emergency-contact → credential → store/outcome）② **内容出口链**（触发=每条拟外发内容：gate → token → 投递准入；旁路是回归集与人工抽检）③ **台账与申报链**（触发=定时/到期/事件：credential 到期、genai 备案、不良事件时限、销毁作业） | 三条各给一个编排 command；跨线共享的 skill 在 §7 单列 |
| **expert-scoped** | ✅ 待确认 | 规划期用 architect；运行期需要 `compliance-officer`（话术边界与法条判定）与 `diabetes-cgm-expert`（不良事件严重性、应急链临床边界）。两者已存在于 `studio/agents/`，但运行时版本要随插件发 | `glycowise-compliance/agents/compliance-officer.md`、`glycowise-safety-admission/agents/clinical-safety-reviewer.md`（规划版的简化拷贝） |

---

## 3. 软件 skill 与组织动作的切分

这批里有三项不是纯代码。硬塞成 skill 会产生两个后果：一是工程排期里出现一个永远做不完的条目，二是——更危险的——**让人以为它被系统拦住了**。domain-canvas 对 D6b 的原话是"本域无法架构强制……不得因 D6a 的存在产生虚假安全感"。

| 项 | 进插件的部分（skill） | 不进插件的部分（SOP / 合同 / 培训） | 判据 |
|---|---|---|---|
| **G2 `device-flow-compliance`** | **无独立 skill**。三处残余各自归位：① 受让方《医疗器械经营许可证》与产品注册证的有效期硬门 → 并入 `credential-gate`（D18 本来就 own `X3 引流 ─╫─ D18`）；② SKU 不得含器械实物 → 并入 `store-readiness-check` 的开通闸；③ 佩戴指导的核对留痕 → 属 `wear-onboarding`（OP-10，本批不含） | 与持证经销商的直发合同、门店动线改造（不碰货、不收款、无库存）、"当面佩戴"改为"佩戴指导服务"的岗位说明与话术、走查 | PRD FR-5.28 的核心逻辑三句全是合同与动线，验收方法是"走查 + 留痕"。一个只能靠走查验收的东西，做成 skill 就是一个必填文本框 |
| **G8 `store-readiness-check`** | 《清查下架确认单》实体化 + **SKU 开通硬门**（未清查不得开通）。硬门是真代码，且不可绕过 | 到店走查、把"血糖分级→产品组合表"物理下架、宣传物料回收、店长与合规双签 | 清查本身发生在货架上。软件能做的是"没有那张签好的单子，SKU 开不出来"——这一半必须是代码 |
| **G3 `script-library`** | 话术库两层结构的台账与版本审批、销售话术单列为受控物料、企微会话存档抽检扫描、申诉当场放行的留痕、撤回更正模板分发 | 话术**编写**、五师**培训**与考核、抽检结果的处置与约谈、员工个人微信号责任告知 | 编写与培训是 week 0 组织并行轨（opportunity-brief §8.2），占店长与培训时间不占工程时间。软件只管"哪一版在生效、谁看过、抽到了什么" |

`device-flow-compliance` 这个名字**不再作为 skill 存在**，但它作为组织动作条目继续在项目计划里排期，week 0 启动。若后续坚持要一个同名 skill，它只会是"引流线索接口 + 证照校验"的薄壳，与 `credential-gate` 重复——**建议并入，待确认**。

---

## 4. 插件边界

### 4.1 为什么不是一个插件

这 13 个软件能力散在六个域（D6a / D6b / D7 / D11a / D11b / D13 / D18 / D8a / D4 / D14），但域不是插件的划分依据。domain-canvas §6 给了一条判据，直接用：

> **领域边界按"说同一种话"划，插件边界按"一起崩溃、一起发布"划。**

按这条判，四个插件：

| 插件 | 覆盖域 | 变更节奏 | 一起崩溃吗 | 独立可装 |
|---|---|---|---|---|
| **`glycowise-compliance`**（必装核心） | D13 + D7 + D6a + D18 + D14 | 机制年级，词库月级，凭证数据日级 | 是——它们共用同一套留痕底座与 `gate_token`，留痕挂了全部失去举证 | 是，且**必装**。其余三个都依赖它的 `audit-trail` 与工作区 |
| **`glycowise-commerce-gate`** | D11a + D11b（+ X3 边界残余） | 随 SKU 与合同变，商务节奏 | 否——它挂了不影响数据与临床链路，只是新 SKU 开不出来 | 是。不卖 C 包的门店可以只装 `store-readiness-check` 那一半 |
| **`glycowise-safety-admission`** | D4 链尾 + D8a 不良事件 | 临床规则年级，几乎不动 | 否 | 是 |
| **`glycowise-script-compliance`** | D6b | **月级**，最快的一个 | 否 | 是 |

### 4.2 三条不合并的理由，逐条说

**D6b 必须单独成包，这是四条里最重要的一条。** 把人工话术合规塞进 `glycowise-compliance`，会让"闸门插件"这个名字覆盖一块**根本没有闸门**的地方。D6a 是架构强制（无 token 不投递），D6b 只有 SOP、培训、抽检。两者放同一个包里，读架构图的人会默认人工渠道也被拦住了——而一期对外触达量的绝大多数恰恰在人工渠道。分包是把这个缺口显式化的最便宜手段。

**变更节奏差三个数量级，不该同发版。** 话术库月级改、词库月级改但要跑回归集、临床安全规则年级改、凭证台账天天有到期但机制不变。把月级和年级打一个包，等于让年级的东西每月承担一次回归风险。

**卸载独立性是真需求。** 只做 A 包的门店没有结果承诺，`outcome-claim-gate` 对它是死代码；试点期只有至心一家店，`store-readiness-check` 的多店逻辑用不上。反过来 `glycowise-compliance` 一天都不能缺。这正好是 Core + Add-on 模式。

### 4.3 架构模式

**Core + Add-on。** `glycowise-compliance` 是唯一的 core，另外三个在 manifest 里声明 `"dependencies": ["glycowise-compliance"]`。

与下批（被 D-12 阻塞的 `glycowise-ingest` / `glycowise-clinical`）的关系：它们也依赖 core 的 `audit-trail`，且必须通过 core 的 `reservation-contract-check`。**本批的 core 是下批开工的前置条件**，不是并行项。

---

## 5. Skills

### 插件一：`glycowise-compliance`（必装核心 · 7 个 skill）

---

#### `init-workspace`

- **Description**：初始化 `.glycowise/` 运行时工作区，建同意、凭证、承诺、不良事件、话术版本、审计六类台账骨架与留存策略配置。
- **Inputs**：门店标识、服务包 SKU 清单、留存策略参数（下限 3 年、上限与销毁周期）、`metric_spec_version` 初值。
- **Outputs**：`.glycowise/config.yaml`、`.glycowise/ledgers/{consent,credential,claim,adverse_event,script,audit}/`、`.glycowise/status.json`。
- **不做什么**：不写任何业务数据；不建血糖相关表（那是 `glycowise-ingest` 的事）；不代替生产库 schema 迁移，只建插件运行时侧的台账与索引。
- **Preconditions**：无。它是唯一一个可以在 `audit-trail` 之前跑的 skill——因为它不产生业务写操作。
- **Complexity**：Moderate（目录与配置脚本）
- **allowed-tools**：Read, Write, Bash, Glob
- **Pipeline**：shared ｜ **HIL**：no ｜ **KB**：留存期限法条表

---

#### `audit-trail` 〔R-6 落点 · 地基中的地基〕

- **Description**：横切留痕中间件的契约、写路径覆盖校验、留存与销毁作业、安全事件 24 小时上报。
- **Inputs**：全部写操作（操作人、角色、凭证、设备、IP、时段、前后值、关联事件）；销毁策略；安全事件工单。
- **Outputs**：`audit_log` 条目；写路径覆盖率报告（未经中间件的写路径清单）；销毁凭证；`security_incident.reported`。
- **不做什么**：不做任何业务判定；不修改被留痕的数据；**不提供关闭开关，也不提供跳过参数**——业务代码无法把它关掉是本 skill 的全部价值。
- **Preconditions**：`init-workspace` 已跑。**反过来，本 skill 是其余每一个 skill 的上线前置条件**：任何产生写操作的能力在留痕中间件覆盖它之前不得上线。
- **不可绕过性**：写路径覆盖率必须是 100%，验收方法见 PRD §5.4（架构测试 + 抽 100 条写操作，未经中间件的写路径数 = 0）。留痕缺失的那段时间事后补不了，这是本 skill 与其他 skill 的性质差别。
- **Complexity**：Script-heavy
- **allowed-tools**：Read, Write, Bash, Glob, Grep, Edit
- **Pipeline**：shared（三条线全部经过）｜ **HIL**：安全事件上报前有一次判定 ｜ **KB**：PIPL 51/55、网安法 21、器械条例可追溯、网络数据安全管理条例 10

---

#### `consent-ledger` 〔G1 · ⊘1~⊘5 落点〕

- **Description**：管理敏感个人信息的分项单独同意、撤回与下游级联停用，并对含个人信息的模型调用做境内硬拦截。
- **Inputs**：同意范围枚举七项；四类分项同意的签署与撤回动作；PIPIA 记录；数据主体权利请求；模型调用元数据（部署地）。
- **Outputs**：`consent` 状态机（S10 唯一写者）；`consent.granted` / `.scope_changed` / `.revoked`；`subject_request.received`；`model_call_log`；`transfer.blocked_cross_border`；撤回后的下游停用指令（枚举到具体下游：停拉取 S1、停触达 S8、指标置不可用 S2、方案 revoked D5、飞书行回收 X4）。
- **不做什么**：不决定数据怎么拉怎么存（D1）；不管输出文本合规（D6a/D6b）；不管主体资质（D18）；不接管门店纸质知情同意的线下签署。
- **Preconditions**：`audit-trail` 已上线；同意书文本经法务确认。
- **不可绕过性 / 反向约束**：
  - ⊘1 同意书**不得预埋二期载体条款**，二期须重新取得（OP-58）。
  - ⊘2 四类**分项单独取得**，不得一揽子勾选：敏感信息处理 / 委托处理与对外提供 / 企微会话存档 / 自动化决策。
  - ⊘3 撤回与同意同样便捷；**不得以拒绝非必要授权为由拒绝服务**。
  - ⊘4 **子女不得代患者同意**——家属授权必须挂在患者本人授权链上。
  - ⊘5 含个人信息的模型调用**一律境内，境外模型禁用**，写死在代码，不做配置项。
  - 撤回强制产出一次**豁免于触达封锁**的告知（"监测已于 X 时停止"）。这条豁免是有意的：老年患者多由子女代操作，"我以为有人在看"是低血糖伤害的经典成因。
- **Complexity**：Script-heavy
- **allowed-tools**：Read, Write, Bash, Glob, Grep, Edit
- **Pipeline**：入组准入链（也是全链路入口）｜ **HIL**：no（撤回不设审批，设审批就违反 ⊘3）｜ **KB**：PIPL 14/15/16/23/24/25/28/29/30/38/40/44–50/55

---

#### `output-compliance-gate` 〔G5〕

- **Description**：对系统生成的一切对外内容做确定性合规检查并签发 `gate_token`，无 token 不投递。
- **Inputs**：任何 `outbound.content.proposed`（日报卡片、草稿摘要、群应答、结营报告、App 文案资源）；词库与模式库当前版本；患者年龄与分层标记。
- **Outputs**：`gate.passed{gate_token}` / `gate.blocked{reason}` / `gate.override_requested`；拦截审计记录（拦了什么、为什么、谁复议）→ `audit-trail`；拦截日志作为 `genai-filing` 的内容安全措施证据。
- **不做什么**：
  - 不生成内容（D5 与各智能体的事）。
  - **不管人工渠道**（→ `script-library`）。
  - **不评估紧急与低血糖处置内容**。这是 C-10 的硬例外：该类话术天然含"胰岛素""磺脲""停"，词库误命中会吃掉致命内容。`template_class='frozen_emergency'` 直接放行，走建库时一次性预审并冻结的模板。`bedtime-low-guard` 的睡前预警话术与第 0 天处置卡同样走这条路径。
  - 若架构上被迫经过闸门，则 **fail-open 且阻断即刻升级至值班人**，并给本 skill 秒级 SLA。闸门不得成为紧急链路的运行时阻断点。
  - **LLM 不做最终裁量**。确定性匹配为主，LLM 只做召回。
- **Preconditions**：`audit-trail` 已上线；词库已数据化并版本化；D16 投递侧已实现 token 硬拒。
- **一期硬词库至少三组**：① 全局硬拦截"夜间监护 / 夜里出事有人知道 / 24 小时看护"（B-11，一期结构性无当夜干预能力）；② ≥65 岁限量类话术硬拦截（OP-20 并入）；③ 功效宣称与结果承诺句式。"缓解"是**语境化闸门不是扁平禁用词**——仅在医师签发的个人方案且附共识定义与随访安排时放行；"逆转/治愈/停药"全局禁用无例外。
- **反向阻断**：双向。既挡"分层 → 产品组合"（R32），也挡"产品名 + 血糖指标的因果表述"。
- **Complexity**：Script-heavy
- **allowed-tools**：Read, Write, Bash, Glob, Grep, Edit
- **Pipeline**：内容出口链 ｜ **HIL**：`override_requested` 的二次审批 ｜ **KB**：互联网诊疗细则 21、食安法 71/73、广告法 17、总局 2021 年第 46 号公告、机构名称规范

---

#### `gate-regression-suite`

- **Description**：用人工标注集回归测试出口闸，双指标输出漏检率与误拦率，词库每次变更必须跑过才准发版。
- **Inputs**：200–500 条人工标注语料（含 C-10 例外样本）；待发布的词库版本；上一版基线指标。
- **Outputs**：漏检率 / 误拦率报告；逐版本不升的趋势；发版放行或拒绝结论。
- **不做什么**：不改词库；不做线上拦截；不评估人工渠道话术（那是 `script-spotcheck` 的覆盖率口径，两套指标不通用）。
- **Preconditions**：`output-compliance-gate` 已有可调用接口；标注集已建立并版本化。
- **拆分理由**：与 `output-compliance-gate` 分开有三条依据——① 触发节奏不同（闸是每条内容跑，回归是每次发版跑）；② 输出服务于一个发布决策，是标准的"输出即决策点"拆分信号；③ 使用者不同（合规官读漏检率，工程读误拦率）。opportunity-brief §5.2 的原话："没有度量的合规能力等于没有合规能力"——**指标必须是漏检率而不是拦截率**，拦截率越高只说明词库越粗。
- **Complexity**：Moderate
- **allowed-tools**：Read, Write, Bash, Glob, Grep
- **Pipeline**：内容出口链（旁路）｜ **HIL**：no ｜ **KB**：标注集本身

---

#### `credential-gate` 〔G6 · 含 G2 的证照残余〕

- **Description**：维护执业与经营凭证台账，做到期预警，并在签发与引流两处设架构硬门。
- **Inputs**：门店《医疗机构执业许可证》与诊疗科目；医师、注册营养师、药师的执业注册、注册机构、有效期；互联网诊疗备案状态；等保三级测评有效期；生成式 AI 备案编号；**X3 受让方的《医疗器械经营许可证》与产品注册证**。
- **Outputs**：`credential.valid` / `.expiring` / `.revoked`；分级授权矩阵（谁能签什么）；签发硬门判定；引流硬门判定。
- **不做什么**：不申办资质（线下工作）；不判断方案内容对不对（D5）；不给健康管理师任何签发入口——健管师是职业技能证书不是执业资格（A2-6）。
- **Preconditions**：`audit-trail` 已上线。**本 skill 必须先于 `signoff-workbench`（OP-06，下批）**——分级授权定义了"谁能签什么"，工作台才知道往哪派任务。反过来做，工作台会先把所有东西都派给医师，然后再改。
- **不可绕过性**：三条硬门是架构强制不是提醒——① 资质失效或科目不符则签不出（一个没有临床营养科目的门店，其"注册营养师"不得签发）；② 受让方证照过期则停止引流；③ 无互联网诊疗备案则限制线上随访内容范围。
- **AI 边界**：AI 只到草稿，医师或注册营养师签发后才推送（B-3）。本 skill 是"签发人有没有资格"这一问的唯一权威，与 `output-compliance-gate` 的"内容能不能说"是两道独立的门，不互相替代。
- **已知缺口**：门店有无注册营养师未确认。无 RD 则分级授权对医师瓶颈（C-07）的缓解为零，须与本地三甲营养科签远程会诊协议。**待确认**。
- **Complexity**：Moderate
- **allowed-tools**：Read, Write, Bash, Glob, Grep
- **Pipeline**：入组准入链 + 台账申报链 ｜ **HIL**：no（到期即失效，不设人工延期）｜ **KB**：医疗机构管理条例实施细则 40–48、器械条例 41/45、A2-6

---

#### `genai-filing` 〔G7〕

- **Description**：管理生成式 AI 算法备案与安全评估材料、核验第三方模型备案资质、给 AI 生成内容打可识别标识。
- **Inputs**：智能体清单与用途说明（AI1–AI6）；第三方模型供应商的备案编号；`output-compliance-gate` 的拦截日志（作为内容安全措施证据）；`consent-ledger` 的 `model_call_log`（证明境内部署）。
- **Outputs**：备案材料包；备案回执归档；第三方模型资质核验结论；深度合成标识注入规则与抽检结果。
- **不做什么**：不做内容过滤（消费 D6a 的日志，不自己拦）；不做备案审批（外部）；不管模型部署地判定（→ `consent-ledger` 的 ⊘5）。
- **Preconditions**：`output-compliance-gate` 已产生可归档的拦截日志。
- **排期特殊性**：**这一项的代价不是罚款是工期。** 备案有审批周期，P0 就要启动、P1 完成，晚了直接卡住全部智能体上线。它在依赖图上很轻，在甘特图上很早。
- **Complexity**：Simple
- **allowed-tools**：Read, Write, Glob, Grep
- **Pipeline**：台账申报链 ｜ **HIL**：材料提交前一次复核 ｜ **KB**：生成式 AI 服务管理暂行办法 4/7/12、深度合成规定 16/17

---

#### `reservation-contract-check` 〔R-1 / R-2 / R-3 / R-4 / R-5 落点〕

- **Description**：冻结五条强制预留的数据契约并持续校验实现是否偏离，把不可逆的决定在开工前一次做对。
- **Inputs**：
  - R-1 去重键定义：`dedup_key = sha1(patient_id|vendor|sensor_sn|reading_type|sensor_reading_seq)`，唯一索引；`vendor_record_id` 只作辅助溯源不进键。
  - R-2 载体三表 schema：`carrier` / `carrier_heartbeat` / `carrier_incident`，云侧作为 `carrier_type='vendor_cloud'` 一行；三信号 + 归因矩阵 + L1–L4 工单 + SLA；`glucose_reading.carrier_id` 建字段不进键。
  - R-3 口径三件套：分母取自 `device_model` 不硬编码 288；`quality_flag='ok'` 的判定谓词集；日界时区取 `patient.home_timezone`。三者共一个 `metric_spec_version`，写进 `metric_provenance` 与每份签发快照。
  - R-4 两条低血糖规则的物理切分：`hypo.level2.event`（回顾，<3.0 持续 ≥15 min，结束条件为回升 ≥3.9 持续 15 min）与 `hypo.level2.alert`（实时，2 连续读数 + 预测性）分两规则、两表、两套阈值；`level1.event` 并建；阈值表建成 per-patient 维度。
  - R-5 原始载荷留存：`ingest_batch` 存响应体；`glucose_reading.raw_value` / `raw_unit`。
- **Outputs**：一份冻结的契约文档（进插件 `references/`）；一组可在 CI 与运行时执行的校验断言；偏离报告。至少包含三条自检信号：`active% > 100%` 红色告警、同 session 内 `sensor_reading_seq` 缺口率、`ingest_batch` 回放重算一致率。
- **不做什么**：**不实现摄入、不实现指标、不实现规则引擎**——那三件在 `glycowise-ingest` / `glycowise-clinical` 里，被 D-12 阻塞。本 skill 只定契约、只做校验。
- **Preconditions**：`audit-trail` 已上线（契约冻结本身要留痕）。D-11a / D-11b 需在走云云路径时先问定；走 SDK 路径时 A1-6 已确认带序号，R-1 直接成立。
- **为什么现在做**：R-5 是**比 R-1 更硬的不可逆**——厂商云历史窗口过期即物理不可得，raw 没存则连重算的输入都没有。R-1 错了会让二期两路无共同锚点，回填重算 → GMI 基线断裂 → 缓解判定的前后对比失效 → C 包结果承诺失去举证基础。这两条的代价都发生在"契约定错"那一刻，与写代码的时间无关，所以不能等 D-12。
- **`active% > 100%` 的局限**：它只能抓"多算"，抓不到"少算"。一期的真实风险恰恰是漏摄入（拉取静默失败、分页游标丢页、回填断点），所以序号缺口率必须配对上线。
- **Complexity**：Moderate
- **allowed-tools**：Read, Write, Bash, Glob, Grep
- **Pipeline**：shared（下批的开工闸）｜ **HIL**：契约冻结时一次拍板 ｜ **KB**：A1-5/A1-6/A1-7、A3-1/A3-2/A3-6/A3-7、Danne 2017 事件定义

---

### 插件二：`glycowise-commerce-gate`（2 个 skill）

---

#### `store-readiness-check` 〔G8 · 含 G2 的 SKU 残余〕

- **Description**：把门店清查下架确认单实体化，并在服务包 SKU 开通处设硬门，未清查不得开通。
- **Inputs**：门店清查确认单（走查结果、下架物料清单、店长与合规双签）；拟开通的 SKU 清单。
- **Outputs**：`store_readiness_check` 记录；SKU 开通放行或拒绝；拒绝原因。
- **不做什么**：**不执行清查**（到店走查、物料下架、宣传稿回收是组织动作）；不审查话术文本（→ `script-library`）；不定承诺条款（→ `outcome-claim-gate`）。
- **Preconditions**：`audit-trail`、`init-workspace` 已就绪；确认单模板经合规定稿。
- **不可绕过性**：未清查门店的 SKU 开通拒绝率必须是 100%。它守的是 B-2（服务与产品物理分离）——"血糖分级→产品组合表"复活一次，B-2 就等于从未执行。
- **SKU 层面兼管一条**：拟开通 SKU 不得含器械实物（B-1，平台不做器械交易）。这是 G2 溶解后归到本 skill 的一条。
- **Complexity**：Moderate
- **allowed-tools**：Read, Write, Bash, Glob
- **Pipeline**：入组准入链 ｜ **HIL**：清查确认单双签 ｜ **KB**：B-1/B-2、食安法 71/73

---

#### `outcome-claim-gate` 〔G4〕

- **Description**：管控结果承诺文本的法务定稿与 C 包可售硬门，只允许承诺过程与服务，不允许承诺疗效。
- **Inputs**：C 包承诺条款草稿；法务定稿状态；ABCD 准入四条判定；GMI 替代 HbA1c 的局限告知文本；退款条款。
- **Outputs**：承诺文本版本台账；C 包 SKU 可售放行或拒绝；前置披露记录（患者签收）。
- **不做什么**：**不做缓解的临床判定**（那是 D2 的 R29）；不做结算（D11b 的另一半）；不做个案疗效宣传的审查（→ `script-library`）；不管系统生成内容的措辞（→ `output-compliance-gate`，两者是独立敞口，出口闸兼管不了合同文本）。
- **Preconditions**：`audit-trail`、`store-readiness-check` 已就绪；法务已介入。
- **硬约束**：**不得承诺 HbA1c 数值，不得承诺停药。** C 包 9,800–12,800 元含结果承诺，等于对疗效的保证性表示（广告法 16：不得保证治愈或承诺有效率）。承诺文本未经法务定稿即销售，等于每一单都留下一份违规广告的书面证据。
- **红线，写死在代码不做配置项**：**"减药"不得进入本域任何位置**——不进承诺条款、不进 KPI 公式、不进结营举证。把减停降糖药变成商业绩效指标，会系统性激励非执业人员诱导患者减药，而减停药正是低血糖风险最集中的动作。同理"对医务人员不设产品销售提成"（反不正当竞争法 7）是红线不是可配置项。
- **Complexity**：Moderate
- **allowed-tools**：Read, Write, Bash, Glob, Grep
- **Pipeline**：入组准入链 ｜ **HIL**：法务定稿 ｜ **KB**：广告法 16、消保法 55、A3-4（ADA 2021 与中国共识 2021 的缓解定义）

---

### 插件三：`glycowise-safety-admission`（2 个 skill）

---

#### `emergency-contact-gate` 〔G10〕

- **Description**：在入组处强制闭合应急链末端，要求本地可到场施救者与门牌地址，缺失不允许开通服务。
- **Inputs**：1–2 名本地可到场施救者的姓名、关系、电话、与患者的距离；门牌地址；施救者培训完成标记；短信回执。
- **Outputs**：应急链完整性判定；服务包开通放行或拒绝；异地施救者场景下的"唯一处置是 120"明示记录。
- **不做什么**：不做告警分发与升级（S4，一期只落 `alert` 记录不分发，二期才启用）；**不承诺任何夜间响应**——一期结构性没有当夜干预能力（B-11、B-13）；不管速效碳水的实物交付（→ `wear-onboarding` 的葡萄糖片签收与 `sensor-lifecycle` 的换传感器补发，都在下批）。
- **Preconditions**：`audit-trail`、`consent-ledger` 已就绪。
- **会被绕开，必须加客观证据**：成单压力下健管师会填自己或同事。**唯一有效的对策是施救者短信回执独立确认**——没有回执的账号不可开通服务包。一个只靠填写来执行的闸门，在成单压力下等于不存在。
- **一条依赖裂缝**：本闸只保证"有人能到场"，不保证"手边有糖"。速效碳水的交付在下批的 OP-10 / OP-23。**缺后者则前者无效**，本 skill 的接口里必须显式声明这个未闭合依赖，不得在文案上表现为"应急链已闭环"。
- **Complexity**：Moderate（短信回执需外部接口）
- **allowed-tools**：Read, Write, Bash, Glob
- **Pipeline**：入组准入链 ｜ **HIL**：no（硬门，无人工豁免）｜ **KB**：医疗质量安全核心制度、15-15 法则、α-糖苷酶抑制剂只能用葡萄糖、老年睡前下限 5.6

---

#### `adverse-event-report` 〔G9〕

- **Description**：给已在采集的器械不良事件线索开一条上报出口，按严重度追踪 10 日 / 30 日时限并与持证方联动。
- **Inputs**：皮肤问题探针命中（OP-10，下批）；传感器脱落记录（OP-23，下批）；健管师人工上报；严重性判定结论。
- **Outputs**：`adverse_event` 记录；严重度分级；上报时限倒计时与逾期告警；与持证方（X2）的联动回执；全程留痕进 `audit-trail`。
- **不做什么**：不做临床处置；不做产品召回决策；不替持证方向监管上报（我方是联动方不是上报主体，除非法定情形）。
- **Preconditions**：`audit-trail` 已上线；与持证方的联动通道已约定。**上游线索源在下批**——本批先把出口与时限机制建好，线索接入等 OP-10/OP-23。
- **为什么不能等**：**我们正在采集不良事件线索却没有出口。** 皮肤问题发生率约 45%。采集了却不上报，比不采集更被动——有记录证明我们知道。
- **Complexity**：Moderate
- **allowed-tools**：Read, Write, Bash, Glob
- **Pipeline**：台账申报链 ｜ **HIL**：严重性判定（严重 10 日 / 一般 30 日，判错时限就错）｜ **KB**：医疗器械不良事件监测和再评价管理办法 14/19

---

### 插件四：`glycowise-script-compliance`（2 个 skill）

---

#### `script-library` 〔G3 软件部分之一〕

- **Description**：维护人工话术库的两层结构与版本审批，把销售话术单列为受控物料，并分发撤回更正模板。
- **Inputs**：临床话术草稿；**销售话术草稿（单独一类）**；合规官审批意见；法条与红线清单。
- **Outputs**：话术库版本（先给"能说什么"再给"不能说什么"）；受控物料清单与生效版本；撤回更正模板；分发与阅读记录。
- **不做什么**：**不编写话术**（合规官与临床写，week 0 组织并行轨）；**不做培训**（培训与考核是组织动作）；不拦截人工发出的字——人手打的字不经过任何系统闸门，这是本域已知的最大合规缺口，必须在文档中显式承认。
- **Preconditions**：`audit-trail` 已上线；week 0 组织轨已启动话术编写。
- **两层结构的顺序不能反**：先给能说什么，再给不能说什么。只给禁令会让一线无话可说，然后自己编。
- **销售话术必须单列**：A/B/C 包销售话术（"缓解""结果承诺""14 天见效"）是最高危违规源，与临床话术分开审批。
- **一期全局硬边界**：话术不得含任何夜间安全承诺（B-11 在一期是确定状态不是临时状态）。低血糖的一期价值是"次日纠因 + 为医师提供减药证据"，把它讲成"实时守护"就是用一个真实能力兑现一个不存在的承诺。
- **Complexity**：Simple（台账与版本，重在 references）
- **allowed-tools**：Read, Write, Glob, Grep
- **Pipeline**：内容出口链（人工分支）｜ **HIL**：话术版本审批 ｜ **KB**：广告法 16/17、医疗广告管理办法、A2-4/A2-5/A2-6、话术库本体

---

#### `script-spotcheck` 〔G3 软件部分之二〕

- **Description**：扫描企微会话存档做人工话术抽检，输出违规命中与覆盖率，并支持一键申诉当场放行且留痕。
- **Inputs**：企微会话存档（须有 ⊘2 中的会话存档单独同意）；生效话术库版本；抽检比例配置。
- **Outputs**：违规命中清单；覆盖率口径（存档全量关键词扫 + 抽检两项分开报）；申诉与放行留痕；撤回更正动作触发。
- **不做什么**：不改话术库（→ `script-library`）；不做人员处置与约谈（组织动作）；不检查系统生成内容（→ `output-compliance-gate`，两套指标不通用）。
- **Preconditions**：`script-library` 已有生效版本；`consent-ledger` 已取得**企微会话存档的单独同意**——没有这一项，抽检本身就是违规处理。
- **拆分理由**：与 `script-library` 之间隔着一个 HIL 边界（申诉当场放行），且角色不同（合规官编审 vs 抽检运行），触发节奏不同（版本月级 vs 抽检周级）。
- **指标口径**：违规率必须说清分母。全量关键词扫和抽检是两个口径，混着报会得出一个好看且没意义的数。
- **Complexity**：Script-heavy（存档拉取与扫描）
- **allowed-tools**：Read, Write, Bash, Glob, Grep
- **Pipeline**：内容出口链（人工分支）｜ **HIL**：申诉当场放行 ｜ **KB**：话术库版本、企微会话存档接口

---

## 6. 数据流

```
                        ┌──────────────────┐
                        │  init-workspace  │  唯一可先于留痕运行的 skill
                        └────────┬─────────┘  （它不产生业务写操作）
                                 │ 产出：.glycowise/ 六类台账骨架
                                 ▼
        ╔════════════════════════════════════════════════════════╗
        ║   audit-trail  〔R-6〕                                  ║
        ║   横切留痕中间件 · 先于任何写操作上线                    ║
        ║   ── 下面每一条实线都是「必须」，不是「可选」 ──         ║
        ╚═╤════╤════╤════╤════╤════╤════╤════╤════╤════╤═════════╝
          │    │    │    │    │    │    │    │    │    │
          ▼    │    │    │    │    │    │    │    │    │
  ┌──────────────┐ │    │    │    │    │    │    │    │
  │consent-ledger│ │    │    │    │    │    │    │    │  ⊘1~⊘5
  │     〔G1〕   │ │    │    │    │    │    │    │    │
  └───┬──────┬───┘ │    │    │    │    │    │    │    │
      │      │     │    │    │    │    │    │    │    │
      │  produces: consent 状态机 · model_call_log
      │      │     ▼    │    │    │    │    │    │    │
      │  ┌───────────────────┐   │    │    │    │    │
      │  │ credential-gate   │   │    │    │    │    │
      │  │      〔G6〕       │   │    │    │    │    │
      │  └────────┬──────────┘   │    │    │    │    │
      │   produces: 分级授权矩阵 · credential.valid
      │           │  ╌╌▶ signoff-workbench（OP-06，下批）
      │           │      │    │    │    │    │    │
      │           ▼      ▼    │    │    │    │    │
      │  ┌────────────────────────┐  │    │    │    │
      │  │ output-compliance-gate │  │    │    │    │
      │  │        〔G5〕          │  │    │    │    │
      │  └───┬──────────────┬─────┘  │    │    │    │
      │      │ gate_token   │ 拦截日志│    │    │    │
      │      ▼              ▼        │    │    │    │
      │  D16 投递准入   ┌──────────────────┐ │    │
      │  （无 token     │  genai-filing    │ │    │
      │    不投递）     │      〔G7〕      │ │    │
      │                 └──────────────────┘ │    │
      │      ▲                               │    │
      │  ┌───┴────────────────┐              │    │
      │  │gate-regression-suite│  发版放行门   │    │
      │  └────────────────────┘              │    │
      │                                      │    │
      │           ┌──────────────────────────┘    │
      │           ▼                               │
      │  ┌────────────────────────┐               │
      │  │ reservation-contract   │  R-1/2/3/4/5  │
      │  │        -check          │  契约冻结与校验│
      │  └────────┬───────────────┘               │
      │           ╎ 校验（下批开工闸）             │
      │           ╎╌╌▶ cgm-ingest / sync-health /  │
      │                glucose-metrics / hypo-retro│
      │                （⚠ 全部被 D-12 阻塞）      │
      │                                           │
      ├──────────────────┬────────────────────────┤
      ▼                  ▼                        ▼
┌──────────────┐ ┌───────────────────┐ ┌──────────────────┐
│emergency-    │ │store-readiness    │ │  script-library  │
│contact-gate  │ │  -check 〔G8〕    │ │      〔G3〕      │
│   〔G10〕    │ └─────────┬─────────┘ └────────┬─────────┘
└──────┬───────┘           │ SKU 开通闸         │ 生效版本
       │                   ▼                    ▼
       │          ┌──────────────────┐ ┌──────────────────┐
       │          │outcome-claim-gate│ │ script-spotcheck │
       │          │      〔G4〕      │ │                  │
       │          └──────────────────┘ └──────────────────┘
       │                                        ▲
       │                              需要 ⊘2 会话存档单独同意
       ▼
┌──────────────────────┐
│ adverse-event-report │  ◀╌╌ 线索源 wear-onboarding / sensor-lifecycle
│        〔G9〕        │      （OP-10 / OP-23，下批）
└──────────────────────┘

图例：实线 = 必须（无上游则下游不能运行）
      ╌╌ 虚线 = 跨批次接口（对端在被 D-12 阻塞的那一支或下批）
```

### 三条最关键的边，写成句子

1. **`audit-trail` → 全部。** 这是唯一一条指向所有 skill 的边。它不是流水线的第一站，它是每一站的开关。没留痕的那段时间，`output-compliance-gate` 的"我们拦住了"、`credential-gate` 的"医师签过"、`consent-ledger` 的"患者同意过"全都无法举证——等于那三道闸在该时段不存在。存量事后补不了，所以不接受"先上功能后补留痕"。
2. **`credential-gate` → `output-compliance-gate` 是弱边，→ `signoff-workbench` 是强边。** 前者只是共享凭证上下文；后者是硬依赖，分级授权定义"谁能签什么"，工作台才知道往哪派任务。
3. **`consent-ledger` → `script-spotcheck` 容易被忽略。** 抽检读的是企微会话存档，而存档属于 ⊘2 四类分项同意之一。没有这一项授权，抽检这个合规动作本身构成违规处理。

---

## 7. 流水线（multi-pipeline 特征的落地）

### 入组准入链
- **入口**：新患者到店，`/glycowise:admit-patient`
- **skills**：`consent-ledger` → `emergency-contact-gate` → `credential-gate`（校验签发人）→ `store-readiness-check` → `outcome-claim-gate`（仅 C 包）
- **产出**：可开通的服务包实例，或一份带具体缺项的拒绝理由
- **硬性**：任何一环拒绝即整链拒绝，无人工豁免通道

### 内容出口链
- **入口**：任何拟对外的内容，`/glycowise:gate-outbound`
- **skills**：`output-compliance-gate` →（发版旁路）`gate-regression-suite`；人工分支 `script-library` → `script-spotcheck`
- **产出**：`gate_token` 或阻断理由；人工渠道的抽检报告
- **例外**：`template_class='frozen_emergency'` 不进本链，走建库时预审冻结

### 台账与申报链
- **入口**：定时任务与到期事件，`/glycowise:compliance-review`
- **skills**：`credential-gate`（到期预警）、`genai-filing`（备案与标识）、`adverse-event-report`（时限追踪）、`audit-trail`（销毁作业与安全事件）
- **产出**：到期清单、备案回执、上报回执、销毁凭证

### 跨线共享
- `audit-trail` — 三条线全经过
- `init-workspace` — 三条线共用工作区
- `reservation-contract-check` — 不属任何一条线，它是下批的开工闸

---

## 8. 复杂度分层

| Skill | 插件 | Tier | 脚本 | MCP | HIL | 备注 |
|---|---|---|---|---|:--:|---|
| `init-workspace` | compliance | Moderate | 目录与配置初始化 | — | no | stateful 标准 skill |
| `audit-trail` | compliance | Script-heavy | 写路径扫描、留存销毁作业、覆盖率报告 | — | 上报判定 | 存量不可补 |
| `consent-ledger` | compliance | Script-heavy | 状态机、撤回级联、出境判定 | — | no | 撤回不设审批（⊘3） |
| `output-compliance-gate` | compliance | Script-heavy | 确定性匹配器、token 签发、词库版本 | — | override | LLM 只召回不放行 |
| `gate-regression-suite` | compliance | Moderate | 标注集评测、双指标 | — | no | 发版放行门 |
| `credential-gate` | compliance | Moderate | 台账、到期预警、授权矩阵 | — | no | 技术极简，价值在不可绕过 |
| `genai-filing` | compliance | Simple | — | — | 材料复核 | 工期风险大于技术风险 |
| `reservation-contract-check` | compliance | Moderate | schema 断言、CI 校验 | — | 契约冻结 | 🔴 不可逆决定 |
| `store-readiness-check` | commerce-gate | Moderate | 确认单实体、SKU 闸 | — | 双签 | 清查本身不在软件内 |
| `outcome-claim-gate` | commerce-gate | Moderate | 文本版本台账、可售闸 | — | 法务定稿 | 减药禁入写死在代码 |
| `emergency-contact-gate` | safety-admission | Moderate | 回执确认、完整性判定 | 短信网关（外部接口） | no | 无回执不开通 |
| `adverse-event-report` | safety-admission | Moderate | 时限倒计时、联动回执 | — | 严重性判定 | 线索源在下批 |
| `script-library` | script-compliance | Simple | — | — | 版本审批 | 重在 references |
| `script-spotcheck` | script-compliance | Script-heavy | 存档拉取与扫描、覆盖率 | 企微会话存档 API | 申诉放行 | 需 ⊘2 授权 |

**需要调用子智能体的**：`adverse-event-report`（严重性判定调临床专家）、`output-compliance-gate` 的召回环节（不做裁量）。
**需要网络访问的**：`genai-filing`（备案系统）、`script-spotcheck`（企微存档）、`emergency-contact-gate`（短信网关）。
**需要项目外文件访问的**：无。

---

## 9. 安全与合规的不可绕过性（每个 skill 都要落到接口里）

四条横切规则，写在这里一次，各 skill 接口里各自复述：

1. **低血糖链路不经合规词库过滤。** 该类话术天然含"胰岛素""磺脲""停"，词库误命中会吃掉致命内容。走建库时一次性预审、冻结、版本化的模板，运行时直接取用。落点：`output-compliance-gate` 的"不做什么"。
2. **紧急告警豁免于闸门。** 若架构上必须过闸，则 fail-open 且阻断即刻升级至值班人，闸门给秒级 SLA。D6a 不得成为紧急链路的运行时阻断点。落点：同上。
3. **AI 只到草稿，医师签发后才推送。** 分型分级结论不直推患者，须有 `tier.disclosure_approved`。两道独立的门：`credential-gate` 管"签发人有没有资格"，`output-compliance-gate` 管"这句话能不能说"，互不替代。
4. **留痕不可关闭。** 业务代码无法把 `audit-trail` 关掉或跳过，这不是配置项。

三条一期特有的边界：

- **一期没有当夜干预能力**（B-13）。服务包、合同、系统文案、人工话术全都不得含夜间安全承诺。这在 `output-compliance-gate` 是全局硬拦截词，在 `script-library` 是硬边界，在 `emergency-contact-gate` 是接口声明。
- **红线写死在代码不做配置项**：血糖派生字段 → SKU 的映射（双向）、减药进 KPI、对医务人员的产品销售提成、境外模型调用。
- **闸门的度量指标是漏检率不是拦截率。** 没有度量的合规能力等于没有合规能力。

---

## 10. 建设顺序

排序有两条，不要混。**法律敞口排序**回答"哪个后置代价大"，**建设顺序**回答"哪个先能开工"。两者不同是正常的。

### 工程轨

```
0.  init-workspace                    无依赖，第一天
1.  audit-trail            〔R-6〕    ══ 其余全部的上线闸 ══
2.  consent-ledger         〔G1〕    无同意 = 零数据摄入
3.  credential-gate        〔G6〕    必须先于下批的 signoff-workbench
4.  output-compliance-gate 〔G5〕
5.  gate-regression-suite            与 4 同批交付，否则 4 没有验收方法
6.  reservation-contract-check       下批开工前必须冻结（🔴 不可逆）
7.  emergency-contact-gate 〔G10〕
8.  store-readiness-check  〔G8〕
9.  outcome-claim-gate     〔G4〕    仅 C 包上架前必须完成
10. adverse-event-report   〔G9〕    出口先建，线索源等下批
11. script-library         〔G3〕    等 week 0 组织轨的话术稿
12. script-spotcheck                 等 11 有生效版本 + ⊘2 授权
```

### 组织并行轨（week 0 启动，占的是店长与培训时间，不是工程时间）

- **G2 器械流转**：与持证经销商的直发合同、门店动线改造、"佩戴指导服务"的岗位说明。**无 skill 产出**，但它是第一单能不能卖的前提。
- **G8 的清查部分**：到店走查、物料下架、宣传稿回收。它决定 `store-readiness-check` 什么时候有单子可收。
- **G3 的编写与培训**：话术两层结构编写、五师培训与考核。它决定 `script-library` 什么时候有内容可管。
- **G7 备案启动**：P0 启动、P1 完成。审批周期长于开发周期，晚了卡住全部智能体上线。

**这条轨的 lead time 比工程长。** 把它们和工程候选混排，会让组织周期变成上线闸门——opportunity-brief §8.2 已经纠正过一次，这里不再犯。

### 与下批的交接

`reservation-contract-check` 的契约文档冻结之日，才是 `glycowise-ingest` 允许开工之时。这条顺序不能倒——契约在实现之后补，等于承认可以改，而 R-1 与 R-5 改不了。

---

## 11. 本批不含什么、为什么

### 被 D-12 阻塞的那一支（**不是遗漏**）

D-12 是传感器芯片侧缓存深度：能存几小时或几天读数。它决定 SDK 路径下患者多久必须同步一次，进而决定 R01（14 天 + ≥70%）能否达标、GMI 能否用于缓解判定、C 包的结果承诺能否成立。**一期第一风险，最高优先级。**

⚠ 提醒一条已被推翻的说法：曾判"走云云对接则 D-12 无关"（C-12），**这是错的**。厂商给的是移动端 SDK，即便走云云，患者侧仍是手机 App 经 BLE 同步，两条路径的同步依从性完全一样；且云云路径下我方还会失去同步过程的可观测性。**D-12 无退路。**

因此本批不含：

| 候选 | 为什么等 D-12 |
|---|---|
| `cgm-ingest`（OP-01） | 摄入形态取决于同步节律。push/pull 双摄入的乱序、重传、断点处理，直接由缓存深度决定 |
| `sync-health`（OP-03） | 断流判定用 `data_age`，而"多久算断流"就是 D-12 的答案 |
| `glucose-metrics`（OP-02） | R01 门槛能否达标取决于同步依从性 |
| `minimal-sync-app`（OP-24） | **形态可能整体变。** 若缓存浅，它就不是"最小同步 App"而是必须常驻的 App，直接跳到二期载体形态 |
| 上述四项的下游价值候选 | `hypo-retro`、`triage-queue`、`discharge-kit`、`daily-card-composer`、`plan-draft`、`retention-signals`、`ppgr-pairing`、`sensor-lifecycle`、`wear-onboarding`、`bedtime-low-guard`、`med-list-freshness`、`family-account`、`exit-record`、`feishu-sync`、`signoff-workbench`、`ocr-triage`、`bg-meter-ble` |

**但 R-1~R-5 的契约不等。** 它们回答的是键怎么定、口径怎么算、留什么、监控表长什么样——四问都与缓存深度无关。`reservation-contract-check` 就是为此存在的：把不可逆的部分现在做对,把可逆的实现留给 D-12 答复后。

### 二期整体不含

前置两条缺一等于零：D-01 载体到位、D-02 夜间值班责任人。有载体没人值班等于凌晨三点的告警发给一个关机的手机；有人值班没载体等于值班的人整夜等一条永远不会来的消息。二期候选（OP-51~OP-59）本批全不拆。

另有 D-18 待答：硅基是否书面允许第三方专用设备承载其 SDK。若为否，采集盒方案整体作废，二期形态要重做。这是授权条款问题不是技术问题。

### 本批内部也有一处未闭合

`emergency-contact-gate` 保证"有人能到场"，不保证"手边有糖"。速效碳水的交付在下批的 `wear-onboarding`（葡萄糖片签收）与 `sensor-lifecycle`（换传感器补发）。**缺后者则前者无效。** 本批交付时必须在接口与文案上显式承认这个缺口，不得表述为"应急链已闭环"。

---

## 12. 待确认（用户在线，本轮不停下提问，集中列此）

| # | 事项 | 影响 | 我的建议 |
|---|---|---|---|
| 1 | 五个插件特征的判定是否认可 | 决定骨架生成内容 | 全部 ✅，理由见 §2 |
| 2 | **`device-flow-compliance` 溶解为组织动作 + 两处并入**，不做独立 skill | G2 的敞口排序第 2，溶解是个大动作 | 建议溶解。若坚持保留，它只会是与 `credential-gate` 重复的薄壳 |
| 3 | 四插件切分是否认可，特别是 D6b 单独成包 | 影响发版与安装粒度 | 建议照做。D6b 与 D6a 同包会制造虚假安全感 |
| 4 | 新增四个名字：`init-workspace`、`reservation-contract-check`、`gate-regression-suite`、`script-spotcheck` | 命名约定要求沿用 brief 已有名字 | 前者是 stateful 标准 skill；后三个是拆分产物，均已给拆分依据 |
| 5 | 不建 companion KB 插件，词库与话术库做成数据表 | 影响 kb-dependent 的下游 | 建议照做。检索式 KB 会把硬闸变成概率闸 |
| 6 | 门店有无注册营养师 | 无 RD 则 `credential-gate` 的分级授权对医师瓶颈缓解为零 | 须与本地三甲营养科签远程会诊协议，成本进 B/C 包 |
| 7 | D-11a / D-11b（云侧序号与传感器标识命名空间） | 走云云路径时决定 R-1 是否成立 | 走 SDK 则两问都不存在。契约冻结前必须问定其一 |
| 8 | `script-spotcheck` 依赖的企微会话存档单独同意（⊘2 第三项）是否已在同意书文本中 | 缺则抽检本身违规 | 法务定稿同意书时一并确认 |

---

## 13. 下一步

运行 `/studio-planner:spec-generate glycowise` 生成规格文件，再确认 build 阶段让 Astra Studio 自动调用 skill-creator。

生成骨架时注意三处：`audit-trail` 的 SKILL.md 要写成"其余 skill 的上线前置"而不是流水线首站；带 HIL 的七个 skill 各注入一个 `## Approval Gate`；`output-compliance-gate` 的骨架必须写死 C-10 例外，不能留给实现者判断。
