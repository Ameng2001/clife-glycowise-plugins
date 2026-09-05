# Behavior Matrix: glycowise（控糖场景）

> Created: 2026-09-04 · 主导角色：architect（studio-insight）
> 输入：`brief.md`、`domain-canvas.md`（D1–D18 / X1–X5）、`processes/`（四份流程 + README）、`personas/`（7 份）、`research/sources/05` §1.6 字段级 schema、`research/sources/02` §8 规则库 R01–R32
> **已完成专家评审（技能第 7 步）**：cgm-data-integration-expert（12 条）、diabetes-cgm-expert（16 条）、data-analyst（17 条）。本文是**评审后修订版**——评审推翻了初稿的一条核心结论与三条安全设计，见 §0.1 与 §12。
> **⚠️ 2026-09-04 前提变更（评审后）**：硅基 CGM 接入已商务确认，形态是**厂商给 SDK 或蓝牙协议**，粒度是**原始读数（5–15 分钟点）**。这推翻了"厂商无自助 API、Phase 0 全走降级通道"的原始判断。约束随之从**通道**转移到**载体**，§11 已整体改写为「载体可用性影响分析」（主线）+「降级通道兜底」（次线）。
> 技能第 8 步 Validate 未执行（用户不在线），待确认见 §13。

---

## 0. 这份矩阵怎么读

矩阵的价值不在"填满格子"，而在**格子的空处**：只读不写的实体暴露外部依赖，只有副作用没有输出的动作暴露可追溯性断裂，只读不写的角色暴露被架空的岗位。§7 缺口分析与 §11 降级分析是本文的结论段，§5 只是它的证据。

**三套贯穿全文的标记**

| 列 | 取值 | 含义 |
|---|---|---|
| **P0 无载体** | ✅ 可用 / ⚠️ 降级或有条件 / ❌ 失效 | **前提变更后本列语义已重定义**：厂商通道已不是约束，**载体才是**。本列现表示"在**无 7×24 常驻载体**（仅小程序前台 + 降级通道兜底）条件下"该动作的命运。**配齐家庭网关或原生 App 后，本列绝大多数 ❌/⚠️ 转为 ✅**——逐载体的完整对照见 §11.2 |
| **Skill 形态** | `U` user-invocable skill ／ `A` 自动触发 skill ／ `S` 定时任务 ／ `H` hook（架构强制闸门）／ `—` 非插件能力 | 汇总见 §10 |
| **域** | D1–D18 / X1–X8 | 对应 `domain-canvas.md` 的领域归属 |

`H`（hook）意味着"不过就发不出去"的架构强制，不是调用方自觉。全文共 **10 处 `H`**，见 §10。

### 0.1 被推翻的五条初稿判断

| 初稿判断 | 修订后 | 推翻者 |
|---|---|---|
| **厂商无自助 API，P0 全走降级通道；`active%` 恒为 0，R01 结构性不通过；GMI 不可用于缓解判定** | **前提已变更。** 硅基接入商务确认，**SDK / 蓝牙协议 + 原始读数（5–15 min 点）**。⇒ 指标层自建成立（TIR/TBR/CV/GMI/AGP、餐后配对、R18 分级映射）、32 条规则可完整落地、R01 可真正达标、GMI 可用于缓解判定、实时低血糖链路成立。**但约束整体转移到"载体"**：SDK/蓝牙是**设备侧直连**，需 7×24 常驻采集载体，而当前形态（企微 + 小程序）**无后台常驻**。§11 整体改写 | **项目前提变更（2026-09-04）** |
| P0 数据源 = 截图 OCR + 指血 BLE + 手工录入 | 评审已指出该前提被写窄（`vendor_export` / `aggregator_api` 未计入）；**前提变更后，这三条通道退为载体故障与厂商中断时的兜底**，不删除，见 §11.3 | 数据对接专家 §12.1-1 + 前提变更 |
| `alert.resolved` 需人工回执或指血复核即可闭环 | **不够**。上游 daily-monitoring 的 `hypo_prolonged_risk`（磺脲/长效胰岛素**任何复测值都不得闭环**）与 `hypo_recurrence_window`（HAAF 24h 窗口）在初稿中整体丢失——矩阵相对上游**净削弱**了安全约束 | 临床专家 §12.2-2 |
| 告警阈值"上调可自动、下调仅医师" | **把数值方向等同于安全方向，是错的**。高血糖/酮症阈值上调 = 更少告警 = 更危险。不变式改为**"收紧可自动，放宽仅医师"** | 临床专家 §12.2-4 |
| `source_confidence <0.95` 一律不进患者侧告警 | **方向性不对称错误**。低值方向假阳性代价是多吃 15 g 碳水，假阴性代价是昏迷。P0 主力通道置信度天然 <0.95，这条把仅剩的保护也关掉了。改为**低值方向无论置信度一律推患者本人固定科普模板**，不进的是升级链与统计 | 临床专家 §12.2-3 |

---

## 1. Actor 清单

### 1.1 User（人）

| ID | Actor | 描述 | 资格/权限性质 |
|---|---|---|---|
| U1 | 老年 T2D 患者（刘阿姨型） | 68 岁，病程 20 年，胰岛素 + 多药，独居或半独居 | 数据主体 |
| U2 | 中年新诊断/糖前期患者（陈先生型） | 51 岁在职，BMI 28，可能在用 GLP-1。自主上传与打卡的主力 | 数据主体 |
| U3 | 子女/家属（李女士型） | 异地代付、代决策、代收告警。**当前无正式账号** → 直接导致 S5/S11 两个流失信号不可计算（§7.3） | 受授权第三方（需 D7 同意项④） |
| U4 | 健康管理师（小韦型） | 居家闭环的唯一承重墙 | **职业技能证书，非执业资格**。不得疾病判断/用药指导/代填用药清单 |
| U5 | 门诊医师 | 入组判定、分层、目标区间、用药、去强化审查、停药与缓解判定、危急二级兜底 | 执业医师（受 D18 资质闸约束） |
| U6 | 注册营养师 | 基线膳食评估、膳食方案签发 | 不参与入组判定与分层；方案不得含用药内容 |
| U7 | 店长/区中心站长 | 引流、商务、经营看板、承诺兑现。**产品上线的否决者** | 不入患者群、不接触血糖与用药明细、不代收器械款 |
| U8 | 运动康复师 | 运动方案起草（需医师筛查禁忌后双签发） | 运动康复资质 |
| U9 | 心理咨询师 | "指标改善但主观感受差"的兜底 | 咨询资质 |
| U10 | 合规官 / DPO / 法务 | **增补**。D6b 抽检、D7 主体权利与出境判定、D13 留存销毁、D18 凭证台账。不建模则这四个 Core-风险域无人操作 | 合规职能 |
| U11 | 数据/运维工程 | **增补**。`channel_registry` / `device_model` 唯一写者；死信队列、`orphan_reading`、时钟漂移的唯一承接人 | 平台内部 |
| U12 | 前台/护士 | **增补**。到店 5 分钟随机指血与化验采样 | 门店岗位 |
| U13 | 药师 | **临床专家增补**。结构化用药清单的录入与 `med_class_hint → meds` 的确认。医师是唯一硬瓶颈，把低判断量高录入量的工作全压给他，实际结果是不录或乱录——而 `meds` 是 R08/R12/R27/R29/R30 全部规则的输入 | 执业药师（若门店无药师，须显式承认由 U5 兼任并承认瓶颈） |

### 1.2 AI Agent

| ID | Actor | 归属域 | 硬约束 |
|---|---|---|---|
| AI1 | 健康分析智能体 | D3+D2 表达层 | **只接收结构化指标，不接收 288 点原始序列**；输出禁止自由文本诊断 |
| AI2 | 方案生成智能体 | D5 | 禁生成分型分级、用药加减停、疗效承诺、分层→产品映射。**＋药—方案交互约束**：`meds ∩ {胰岛素, 磺脲} ≠ ∅` 时，任何下调碳水/热量或上调运动量的草稿**强制路由医师签发**，不得走营养师单签；`meds ∋ SGLT2i` 时**禁止生成极低碳水/生酮方向结构**（euDKA）。`meds` 为空（P0 常态）时按存在这两类药处理 |
| AI3 | 审核智能体（合规闸门） | D6a | 闸门规则**必须确定性**；紧急告警走预审冻结模板，**不过运行时闸** |
| AI4 | 社群应答智能体 | D9 | **P0–P1 只入不出**；用药/疗效硬阻断转介；危急表述跳过全部分类。**依赖 X3 会话存档能力 + 逐患者同意项**（§11.2） |
| AI5 | 行为分析智能体 | D9+D10 | 同类餐 <2–3 次不出个体化结论；配对**显式排除 X4 SKU 事件** |
| AI6 | 多模态解析适配器 | D1 适配器 | **增补为独立 actor**：P0 主力通道且是 D7 出境判定对象。脱敏在送模型之前；模型部署地受治理。拆两个动作：单点抽取 / **曲线序列抽取** |

### 1.3 System

| ID | Actor | 归属域 | 描述 |
|---|---|---|---|
| S1 | 数据摄入服务 | D1 | Adapter(fetch→map) → Normalizer → Dedup → **通道优先级仲裁** → SessionLinker → QualityTagger → Store。`quality_flag` / `artifact_suspected` 全域唯一写者 |
| S2 | 指标计算服务 | D3 | `wear_ratio` / `effective_data_ratio` / `sufficiency_ok` 唯一计算者 |
| S3 | 规则引擎 | D2 | **三通道**（评审修订，见下） |
| S4 | 告警分发与升级服务 | D4 | 去抖/限流/路由/三级升级/SLA 台账。**不经任何 LLM** |
| S5 | 流失预警服务 | D11a+D12 | S1–S12 信号与分档 |
| S6 | 传感器会话管理服务 | D8a | `sensor_session` 状态机、`device_model` 目录（**含 MARD**）、预热、到期 |
| S7 | 审计日志服务 | D13 | 留存下限 ≥3 年 + 上限销毁 + 安全事件 24h 上报 |
| S8 | 触达与投递服务 | D16 | **无 `gate_token` 或无触达同意 → 硬拒并记 D13** |
| S9 | 资质与凭证监控 | D18 | 到期预警与签发硬门 |
| S10 | 同意与授权状态机 | D7 | 撤回下游级联执行者 |
| **S11** | **载体采集与在线监测服务** | **D1 + D8a** | **前提变更新增**。在网关/App/穿戴上运行硅基 SDK 或蓝牙协议采集原始点；上报载体心跳；重连时补传缓存并标 `data_age`。**它是 D1 的上游而不是 D1 的一部分**——D1 在平台侧，S11 在患者家里，两者之间是一段可能整夜断开的链路 |

**S3 的三通道（评审推翻初稿的双通道）**

| 通道 | 规则 | 受 R01？ | 依据 |
|---|---|---|---|
| ① 实时事件通道 | R02→R03/R04→R05/R06→R11、R12、R23–R26 | **否** | 5 分钟粒度原始流与 slope；佩戴第 1 天生效 |
| ② **低血糖证据通道** | **R09、R10、R07 累积计数、`hypo_episode` 汇总** | **否** | 低血糖是**存在性证据**，不需要代表性。一个只戴 8 天的患者 TBR<3.0 达 5% 是无可争议的用药过量证据。压在 R01 后面 = 让"数据不够"成为"不看低血糖"的理由 |
| ③ 达标与分层通道 | R13–R18、R22、R29、R30 | **是** | 需要代表性才成立的统计结论 |
| — 归属补全 | R19/R20/R21（餐后）挂①，R28/R31（人群切换）为②③的前置参数，R32（产品闸）归 D6a | — | 初稿这几条未写进任何通道 |

> 文案上必须区分"**我们不敢说你达标**"（受 R01）与"**我们确认你低过**"（免 R01）。P0 下若沿用初稿的双通道，全平台**永远不会有一次去强化审查被触发**——而那是矩阵里唯一防止老年人被降糖药打低的临床动作。

### 1.4 External

| ID | Actor | 定性 | 接口 |
|---|---|---|---|
| X1 | CGM 厂商云 | 集成 | 云到云授权（`vendor_api`）**或机构端账号导出**（`vendor_export`）；对硅基已非主路径，退为补数与对账 |
| **X1a** | **硅基 SDK / 蓝牙协议** | **集成（主通道，商务已确认）** | **设备侧直连**：厂商提供 SDK 或私有蓝牙协议，我方在载体上实现采集，得到**原始读数 5–15 min 点**。`source_channel=ble_cgm_sdk`，`source_confidence=1.0`。<br>⚠️ **它不是"云到云"，是"设备到载体"**——没有载体就没有数据，厂商谈成不等于数据到得了平台。<br>⚠️ SDK 版本与协议版本须入 `device_model` 并纳入 A79 的适配器版本治理；协议随固件变更会静默失效 |
| **X10** | **家庭蓝牙网关（设备）** | **集成（候选载体，实物资产）** | 常驻居家、通电即工作、零操作，最适合老年场景。上报 CGM 读数 + **自身心跳**。<br>⚠️ **是我方需管理的实物资产**：配发 / 绑定 / 心跳 / 故障置换 / **归还**，见 `gateway_device` 实体与 §8 权限行。<br>⚠️ **法务待确认**：中继三类器械数据的网关是否构成"医疗器械附件"。若构成，则与 X2「门店不碰货」的红线冲突，须改由持证方配发。见 §13 |
| X11 | 穿戴桥接（华为 WATCH 4 等） | 集成（候选载体） | 硅基已支持；经华为 Health Kit 回流。覆盖时段 = **佩戴时段**，夜间摘表则为 0 |
| X2 | 持证器械经销商/厂商 | **排除**（4 接口） | ①引流线索 out ②设备激活回执 in ③到期提醒 out ④不良事件回传 |
| X3 | 企业微信 | 集成 | `external_userid` + 投递 + **会话存档**（AI4 的唯一输入，机器人 webhook 只出不进） |
| X4 | 飞书多维表格 | 集成（P2 退役） | 只写不读；**仅聚合运营指标，不含个人标识** |
| X5 | 门店 HIS | 集成 | 诊断、处方、用药医嘱、检验。**用药类别读入 P1 就需要** |
| X6 | 指血血糖仪 | 集成 | GATT 0x1808；小程序 BLE 仅前台运行 |
| X7 | 短信 / 语音外呼服务商 | 集成 | **增补**。内容**不得含血糖数值、疾病名、用药信息** |
| X8 | 检验科 / 外送化验 | 集成 | **增补**。HbA1c / C 肽 / 抗体来源；**方法学必须区分**（POCT vs 实验室法，差异可达 0.5%，而缓解阈值是 6.5%） |
| X9 | 聚合中间层（糖动 CGMcare） | 集成 | 多品牌中间层（`aggregator_api`）；接第二家厂商时的备选。增加一层数据合规责任，须纳入 D7 出境与受托方台账 |

**合计**：User 13 · AI Agent 6 · System **11**（新增 S11 载体采集服务）· External 12 = **42 个 actor**。

**通道枚举更新**（D1 通道属性表新增一项、语义重排）：
`ble_cgm_sdk`（**新，主通道**，设备侧直连，conf 1.0，实时性取决于载体）· `vendor_api` · `vendor_export` · `aggregator_api` · `ble_gls_1808`（指血）· `ocr_upload` / `ocr_curve` · `manual_entry` / `staff_entry` · `huawei_health`（穿戴桥接）

---

## 2. 动作表

⚠️ **频率栏的可信度**（data-analyst §12.3-8/9）：标 `[实测]` 的有依据；标 `[目标]` 的来自 brief 的目标值而非现状；标 `[未估]` 的是占位符，**必须在上线前观测**，不得作为容量规划输入。

### 2.1 患者与家属（U1/U2/U3）

| # | Actor | 动作 | 频率 | 触发 | P0 |
|---|---|---|---|---|---|
| A01 | U1/U2 | 到店分诊登记、接受随机指血筛查 | 入组一次 | 到店 | ✅ |
| A02 | U1/U2 | 阅读同意书、逐项勾选、电子签名 | 入组一次 | 主动 | ✅ |
| A03 | U1/U2 | 在持证方渠道下单购买 CGM | 入组一次 | 门店引流 | ✅ |
| A04 | U1/U2 | 在厂商 App 内完成机构数据授权 | 入组一次 | 主动 | ❌ 无 `cloud_api` 则不存在 |
| A04b | U1/U2 | 从厂商 App/机构端导出原始数据文件并上传 | 每周 1–2 次 `[未估]` | 提醒 | ⚠️ 兜底通道 |
| **A04c** | **U1/U2/U3** | **家庭网关通电、联网（配网一次）、保持在线** | 一次 + 持续 | 配发 | ❌ **无载体即无此动作——这是整条夜间链路的物理起点** |
| **A04d** | **U1/U2/U3** | **服务结束后归还网关设备** | 结营一次 | 结营 | — 资产回收 |
| **A04e** | **U1/U2** | 打开小程序前台同步（无载体时的唯一采集动作） | 每日数次 `[未估]` | 主动/提醒 | ⚠️ **传感器缓存会一次性回填，数据最终会到，但告警从未发出**——见 §11.1 |
| A05 | U1/U2 | 佩戴传感器（本人/家属操作，健管师指导） | 每 14 天 | 到期换新 | ✅ |
| A06 | U1/U2 | 上传血糖截图 / AGP PDF | 1–3 次/天 `[未估]` | 提醒 | ✅ **P0 主力** |
| A07 | U1/U2 | 指血测量并同步（BLE，需前台打开小程序） | 7 点/日 `[目标]` | SOP | ⚠️ **复合成功率 ≈0.9⁷≈48%**，见 §11.4 |
| A08 | U1/U2 | 群内发餐食照片/打卡 | 每餐（**老年近 0**） | 主动 | ✅ |
| A09 | U1/U2 | 群内提问 | `[未估]` | 主动 | ⚠️ 依赖会话存档 |
| A10 | U1/U2 | 接收告警并按 15-15 处置、复测 | 事件驱动 | 推送 | ⚠️ |
| A10b | U1/U2 | **一键回填处置动作与症状标记** | 每次告警 | 告警卡片 | ✅ **新增，R10 与 `alert.resolved` 判据的唯一输入** |
| A10c | U1/U2 | **血酮/尿酮自测并录入** | 事件驱动 | R11/R12/R24 | ✅ **新增，否则酮体红线永远触发不了** |
| A11 | U1/U2 | 回复随访、确认方案已读 | 每周 | 推送 | ✅ |
| A12 | U1/U2 | 到店听解读、复测体重腰围 HbA1c | 14 天首报 + 每 3 月 | 预约 | ✅ |
| A13 | U1/U2 | 执行医师减停计划并打卡 | C 包停药期每日 | 计划签发 | ✅ |
| A14 | U1/U2 | 发起授权撤回（逐项） | 随时 | 主动 | ✅ |
| A15 | U1/U2 | 行使数据主体权利 | 罕见 | 主动 | ✅ |
| A16 | U1/U2 | 续约/升级/结营决策 | 包周期末 | 商务 | ✅ |
| A17 | U3 | 代约、陪同、代付、代读同意书 | 入组 + 续约 | 主动 | ✅ |
| A18 | U3 | 家属查看授权、接收家属版卡片与告警 | 持续 | 授权后 | ⚠️ 内容降级 |
| A19 | U3 | 危急时接外呼、代联系、**到场施救** | 事件驱动 | 升级链 | ❌ 夜间链路失效 |
| A20 | U3 | 监督减停计划、陪同复测 | C 包期 | 计划 | ✅ |

### 2.2 健康管理师（U4）

| # | 动作 | 频率 | 触发 | P0 |
|---|---|---|---|---|
| A21 | 分诊登记与带检 | 5–15 次/周 `[实测]` | 到店 | ✅ |
| A22 | 讲解服务包、签服务合同 | 5–15 次/周 | 入组 | ✅ |
| A23 | 佩戴指导 + 首次教育 + **贴敷部位轮换与皮肤评估** | 每次换新 | 佩戴 | ✅ |
| A24 | 建企微群、配置告警接收人与夜间兜底电话 | 入组一次 | 入组 | ✅ |
| A25 | **复核 OCR 队列** | **12–180 条/天**（区间跨一个数量级，`needs_review_rate` 未知） | `reading.needs_review` | ✅ **P0 瓶颈** |
| A26 | 工作台巡检 | 每日多次 | 主动 | ✅ |
| A27 | 接收告警并响应、点击「已处理」 | 事件驱动 | `alert.raised` | ⚠️ |
| A28 | 记录处置动作与患者复测值 | 每次告警 | 响应后 | ✅ |
| A29 | 工作台手工录入读数 | 每日 | 患者口头报数 | ✅ **不计入"自动入库"KPI 分子** |
| A30 | 补录 `context_event` | 每日 | 口述 | ✅ |
| A31 | 静默回访、`away_mode` 登记 | `[未估]` | `data.silent_24h` | ✅ **须防滥用，见 §7.2 B9** |
| A32 | 传感器到期/脱落跟进 | 每 14 天 | `sensor.expired` | ✅ |
| A33 | 用药/疗效问题**转介医师** | `[未估]` | AI4 硬阻断 | ✅ |
| A34 | 停药期每周随访（不得对停药发表意见） | C 包每周 | 排程 | ✅ |
| A35 | 备复盘材料、预约到店、48h 未读跟进 | 每月/每周 | 排程 | ✅ |
| A36 | 执行分工任务、发教育类模板内容 | 持续 | 复盘结论 | ✅ |
| A37 | 商务沟通续约（**医师适宜性结论后**） | 包周期末 | 解锁 | ✅ |
| A38 | 承诺兑现的商务执行 | C 包末 | D11 判定 | ✅ |
| A39 | 流失信号响应（黄72h/橙24h必电话/红4h） | `[未估]` | `churn_signal` | ⚠️ 老年组近乎失明，§11.4 |
| A39b | 从厂商机构端账号批量导出并上传 | 每周 | 排程 | ⚠️ 兜底通道 |
| **A39c** | **网关配发、现场配网、绑定患者、验证首条读数落库** | 入组一次 | 入组 | — **载体部署动作** |
| **A39d** | **网关离线跟进**（`gateway.offline` → 电话指导重连 → 上门 → 置换） | 事件驱动 | 心跳中断 | — **网关掉线 = 安全网掉线，与告警同级** |
| **A39e** | **结营时回收网关、解绑并确认归还** | 结营一次 | 结营 | — 解绑须触发覆盖状态变更告知 |

### 2.3 医师 / 药师 / 营养师 / 康复师 / 心理师

| # | Actor | 动作 | 频率 | P0 |
|---|---|---|---|---|
| A40 | U5 | 急症红旗与 1 型/LADA 红旗筛查 | 每次入组 | ✅ |
| A41 | **U5/U13** | 结构化用药清单录入（**健管师不得代填**）+ **四标签**：`hypo_risk_med` / `sglt2i` / **`symptom_masking_med`（β 阻滞剂）** / `other` | 入组 + 变更 | ✅ |
| A41b | U4/U1/AI6 | **采集 `med_class_hint`（患者自报 / 药盒照片）** | 入组 | ✅ **新增，见 §7.1 G1b** |
| A42 | U5 | 开具检验单（HbA1c / C 肽 / 抗体 / **eGFR** / 酮体） | 入组 + 复测 | ✅ |
| A43 | U5 | 入组判定 + ABCD 筛选 + 选包 | 每次入组 | ✅ |
| A44 | U5 | 目标区间 + `health_tier` 落库 + 控制下限 | 入组 + 调整 | ✅ |
| A45 | U5 | 降糖药去强化审查（TBR 超标 24h / L2 事件 72h） | 事件驱动 | ✅ **改挂②低血糖证据通道后，无载体亦可用**（次日回填即触发） |
| A46 | U5 | 危急告警二级兜底 | 夜间事件 | ❌ |
| A47 | U5 | 回答用药类转介 | `[未估]` **医师总负载从未 sizing** | ✅ |
| A48 | U5 | **告警阈值放宽（任何方向）—— 仅医师** | 罕见 | ✅ |
| A49 | U5 | 签发含用药/分型的方案 | 每月/人 | ⚠️ 依据变薄、责任不变 |
| A50 | U5 | 逐屏解读 AGP | 首报 + 节点 | ✅ AGP 成立（回填数据完整） |
| A51 | U5 | 五师复盘、升级适宜性判断 | 每月 | ✅ |
| A52 | U5 | 运动禁忌筛查 + 双签发 | 运动方案时 | ✅ |
| A53 | U5 | 评估可否停药、签发减停计划原文快照 | C 包一次 | ✅ |
| A54 | U5 | 确认 `remission_clock` Day 0 | C 包一次 | ✅ |
| A55 | U5 | 反弹时决定是否复药 | 事件驱动 | ✅ |
| A56 | U5 | 缓解判定与签发、面诊告知 | C 包一次 | ✅ **有载体则 GMI 可用、停药期监测成立**；无载体时判定可用、**过程监测失效** |
| A57 | U5 | 复核 `plan.evidence_stale` | 事件驱动 | ✅ |
| A58 | U6 | 基线膳食评估 | 每次入组 | ✅ |
| A59 | U6 | 签发纯膳食方案（**不含用药，且不得越过药—方案交互路由**） | 每月/人 | ⚠️ |
| A60 | U8 | 起草运动方案 | 按需 | ✅ |
| A61 | U9 | 介入主观感受差个案 + **落 `psych_note`** | 按需 | ✅ |

### 2.4 店长 / 合规官 / 运维 / 前台

| # | Actor | 动作 | 频率 | P0 |
|---|---|---|---|---|
| A62 | U7 | 引流（不碰货不收款） | 持续 | ✅ |
| A63 | U7 | 查看经营看板 | 每日 | ⚠️ 须用 `wear_days_fulfilled`，不得用 `wear_ratio` |
| A64 | U7 | 商务、**退款协商与退出归因（写 `service_exit_record`）** | 按需 | ✅ **新增写动作** |
| A65 | U7 | 承诺兑现裁量、红色流失信号处置 | 按需 | ✅ |
| A66 | U7 | 存量违法物料清查下架 + 签字确认单 | 上线一次 | ✅ **系统内需 `store_readiness_check`** |
| A67 | U10 | 话术库维护、**抽检（须定抽样率与置信区间）** | 每月 | ✅ |
| A68 | U10 | 禁用词库与模式库版本维护 | 每月 | ✅ |
| A69 | U10 | 出境判定与硬拦截（含**多模态模型部署地**） | 项目级 | ✅ **P0 第一天** |
| A70 | U10 | 主体权利受理与答复 | 罕见 | ✅ |
| A71 | U10 | PIPIA 编制与重评 | 事件驱动 | ✅ |
| A72 | U10 | 凭证台账维护 | 事件驱动 | ✅ |
| A73 | U10 | 留存上限与销毁作业审批 | 每季 | ✅ |
| A74 | U10 | 安全事件响应与 24h 上报 | 事件驱动 | ✅ |
| A75 | U10 | 存量患者授权补签 + 月度合规报表 | 每月 | ✅ |
| A65b | U7 | **网关资产台账与未归还催收** | 每月 | — |
| A76 | U11 | `channel_registry` 维护（**不含 MARD**；新增 `carrier_type` / `supports_realtime_alert` 逐载体取值） | 项目级 + 每周实测 | ✅ **P0 前置** |
| A77 | U11 | `device_model` 目录维护（**含 MARD、SDK/协议版本、固件兼容矩阵**） | 每款型号 | ✅ |
| A79b | U11 | **SDK/蓝牙协议版本升级与固件兼容回归**（协议随固件变更会**静默失效**） | 事件驱动 | — **新增，是主通道的存活前提** |
| A79c | U11 | **网关远程解绑 / 故障置换 / 固件升级** | 事件驱动 | — |
| A78 | U11 | 死信队列、`orphan_reading`、时钟漂移、通道故障 | 每日 | ✅ |
| A79 | U11 | 适配器版本发布与派生列重算 | 项目级 | ✅ |
| A80 | U12 | 到店 5 分钟随机指血（前置串行安全闸） | 每次到店 | ✅ |
| A81 | U12 | 化验采样送检 | 入组 + 复测 | ✅ |
| A81b | U4 | **体测采集（同一台门店设备、同一协议）** | 入组 + 每月 | ✅ **新增，承诺兑现的唯一量化判据** |

### 2.5 AI Agent

| # | Actor | 动作 | 频率 | P0 |
|---|---|---|---|---|
| A82a | AI6 | **单点/表格读数抽取**（含单位与时间判定） | 上百次/天 | ✅ **P0 主力** |
| A82b | AI6 | **曲线序列抽取**（App 首页 6–8h 曲线、AGP 逐日曲线页） | 每张图 | ⚠️ 兜底通道；不入 `active%`，可进 AGP 与"疑似 `hypo_episode`" |
| A83 | AI1 | 结构化分析结论 JSON | 每次复盘 | ⚠️ |
| A84 | AI1 | 每日日报文案（仅非危急路径） | 每日 06:00 | ⚠️ **数据不足时禁止回退到"平稳"** |
| A85 | AI2 | 方案草稿（**受药—方案交互约束**） | 每月/人 | ⚠️ |
| A86 | AI2 | 结营报告草稿、停药期简报 | 包末 / 每 30 天 | ⚠️ |
| A87 | AI3 | 四道合规闸 | 每条对外文本 | ✅ |
| A88 | AI3 | 签发 `gate_token` / 产出拦截日志 | 同上 | ✅ |
| A89 | AI4 | 意图分类 + **危急表述识别**（含老年不典型词） | 持续 | ⚠️ **依赖会话存档同意** |
| A90 | AI4 | 餐食抽取为 `context_event` | 每餐 | ⚠️ 同上 |
| A91 | AI4 | 用药/疗效硬阻断转介 | `[未估]` | ⚠️ 同上 |
| A92 | AI5 | 餐后配对（排除 SKU 事件） | 每餐 | ⚠️ 取决于连续通道 |
| A93 | AI5 | 依从性与流失信号解读 | 每周 | ⚠️ |

### 2.6 System

| # | Actor | 动作 | 频率 | P0 |
|---|---|---|---|---|
| **A150** | **S11 载体采集服务（新增 System actor）** | **经硅基 SDK/蓝牙协议从传感器读取原始点并上传** | **每 5–15 分钟** | ❌ **无载体则整个动作不存在** |
| **A151** | **S11** | **载体心跳与在线状态监测 → `gateway.offline` / `carrier.stale`** | 每 5 分钟 | ❌ |
| **A152** | **S11** | **载体缓存补传与 `data_age` 标注**（传感器缓存回填一次性到达） | 重连时 | ✅ **数据到得了，告警到不了——见 §11.1** |
| A94 | S1 | 定时拉取厂商云（`vendor_api`，对硅基已非主路径） | 每 5 分钟 | ❌ |
| A94b | S1 | `vendor_export` / `aggregator_api` 文件批量摄入 | 每周 | ⚠️ 兜底 |
| A95 | S1 | 归一（单位/三层时间/`tz_provenance` 必填硬校验） | 每条读数 | ✅ |
| A96 | S1 | 幂等去重（`time_utc(分钟)` 自然键 + **可空列哨兵值**） | 每条读数 | ⚠️ **初稿写法在 P0 完全失效，见 §12.1-3** |
| A96b | S1 | **跨通道近似去重**（同患者 ±2min 内值差 ≤0.2 → `suspect_duplicate`） | 每条读数 | ✅ **新增** |
| A96c | S1 | **通道优先级仲裁 → `reading.superseded`**（按 `source_confidence` 排序，非硬编码 API>OCR） | 每条读数 | ✅ **新增，P0→P1 迁移窗口的关键** |
| A97 | S1 | 会话归属（按 `device_time` 落区间，晚绑定可重算） | 每条读数 | ✅ |
| A98 | S1 | 质量打标 `quality_flag` / `artifact_suspected`（**唯一写者**） | 每条读数 | ✅ |
| A99 | S1 | 斜率计算 | 每条读数 | ❌ 但**趋势箭头可从截图抽取**（厂商已算好） |
| A100 | S1 | 单位合理性硬规则（>33.3 判 mg/dL 候选） | 每条 OCR | ✅ |
| A101 | S1 | 入站背压：配额、限速、退避、死信、**`data_age` 分档** | 持续 | ✅ **压力源从厂商云换成患者上传与模型 API，背压一样需要** |
| A102 | S1 | 更正级联（`corrected/superseded/retracted/review_approved`） | 每次复核否决/补数 | ✅ **P0 高频主路径** |
| A103 | S2 | 滚动窗口批算（24h/7d/14d，日报 06:00） | 每日 + 滚动 | ⚠️ |
| A104 | S2 | `wear_ratio` / `sufficiency_ok`（唯一计算者） | 每窗口 | ✅ **有载体则回填数据照常达标**；纯兜底期不通过 |
| A105 | S2 | 置位 `tz_uncertain` / `brand_changed` / `metric_provenance` | 每窗口 | ⚠️ |
| A106 | S2 | AGP 渲染 + session 构成披露 | 每次复盘 | ⚠️ |
| A107 | S2 | `metrics.invalidated{window}` | 事件驱动 | ✅ |
| A108 | S3 | **①实时通道**规则（求值顺序 `R02 → R03/R04 → R05/R06 → 其余`） | 每条读数 | ⚠️ **低值方向不受置信度门限** |
| A108b | S3 | **②低血糖证据通道**（R09/R10/R07 累积，免 R01） | 每窗口 | ✅ **新增通道** |
| A109 | S3 | **③达标与分层通道**（受 R01） | 每窗口 | ✅ **回填数据照常成立**——无载体损失的是当夜干预，不是次日结论 |
| A110 | S3 | `hypo_episode` 判定（≥15 min 事件口径） | 事件驱动 | ⚠️ |
| A110b | S3 | **`hypo_state` 状态机**：`prolonged_risk`（磺脲/长效胰岛素）+ `recurrence_window`（HAAF 24h） | 事件驱动 | ✅ **新增，初稿整体丢失** |
| A111 | S3 | 人群参数切换（R28/R31/缺参数→最保守） | 每次评估 | ✅ |
| A112 | S3 | `alert_threshold` **自动收紧**（R10/R27/HAAF/`health_tier`/`symptom_masking_med`） | 事件驱动 | ✅ |
| A113 | S4 | 去抖 + 令牌桶限流（**H 级低血糖不占桶、不受去抖、可抢占**） | 每条告警 | ✅ |
| A114 | S4 | 分级推送（**低值方向无论置信度推患者本人固定模板**） | 每条告警 | ⚠️ |
| A115 | S4 | SLA 计时与三级升级链 | 每条危急 | ❌ 夜间失效 |
| A116 | S4 | T+15min 复测自动检查 | 每次危急 | ⚠️ |
| A117 | S4 | 撤销/补发告警 | 事件驱动 | ✅ |
| A117b | S4 | **`alert_suppressed_log` 留痕**（任何被限流或去抖抑制的告警） | 每次抑制 | ✅ **新增，否则限流是黑洞** |
| A118 | S5 | S1–S12 计算与分档（**相对基线信号须加基线有效性前置**） | 每日 | ⚠️ |
| A119 | S5 | `away_mode` 期间暂停 S3/S7/S8/S9 计分 | 事件驱动 | ✅ |
| A120 | S6 | `sensor_session` 状态机 | 每 14 天 | ⚠️ |
| A121 | S6 | **OCR–指血一致性校验**（原"校准比对"，P0 语义重定义） | 每次指血 | ⚠️ **P0 唯一的跨通道客观对拍手段** |
| A122 | S6 | `sensor.expired` 三次提醒 | 每 14 天 | ⚠️ |
| A123 | S7 | 全域审计归集 | 每次操作 | ✅ |
| A123b | S7 | **告警时延聚合**（P50/P90/超时率/未闭环存量与老化天数） | 每日 | ✅ **新增，brief SC2 要"可测量"不只"可追溯"** |
| A124 | S7 | 到期销毁作业 + 凭证 | 每季 | ✅ |
| A125 | S8 | **投递准入硬拒** | 每条投递 | ✅ |
| A126 | S8 | 物理投递与送达回执 | 持续 | ✅ |
| A127 | S8 | 飞书 06:30 同步（仅聚合，无个人标识） | 每日 | ✅ |
| A128 | S9 | 凭证到期预警与签发权自动冻结 | 事件驱动 | ✅ |
| A128b | S9 | **值班链尾具名持续校验**（非入组一次性） | 每日 | ✅ **第 10 个 `H`** |
| **A128c** | **S9** | **夜间覆盖真实性校验**：载体离线 >N 小时 或 无 7×24 载体 → 置 `no_realtime_night_coverage=true`、强制告知患者与家属、D6a 拦截一切夜间安全承诺话术 | 每日 + 事件 | ✅ **第 11 个 `H`（前提变更新增）** |
| A129 | S10 | 同意状态机与七项范围、`opt_out` | 事件驱动 | ✅ |
| A130 | S10 | 撤回级联执行（含飞书行回收） | 事件驱动 | ✅ |
| A131 | S10 | **豁免于触达封锁的撤回告知** | 每次撤回 | ✅ |
| A132 | S10 | `vendor_grant` 每日校验 | 每日 | ❌ |
| A133 | S1/S6 | 数据静默检测（**P0 口径改为"无上传"**） | 每日 09:00 | ⚠️ |
| A133b | S1 | **数据质量看板批算**（见 §9.4） | 每日 | ✅ **新增** |

### 2.7 External

| # | Actor | 动作 | P0 无载体 |
|---|---|---|---|
| **A146** | **X1a** | **传感器按 5–15 min 产生读数并经蓝牙广播/连接供载体读取；本地缓存未上传点** | ✅ 传感器一直在测 |
| **A147** | **X1a** | **SDK / 协议版本变更（随固件）** | — **静默失效风险，需 A79b 回归** |
| **A148** | **X10** | **网关中继读数 + 上报自身心跳** | ❌ 无网关则不存在 |
| **A149** | **X11** | **穿戴设备经华为 Health Kit 回流读数** | ⚠️ 覆盖 = 佩戴时段，夜间摘表则 0 |
| A134 | X1 | 提供读数 / 仅提供 AGP 报告（退为补数与对账） | ⚠️ |
| A135 | X1 | token 刷新 / 故障 / 限流 | ❌ |
| A136 | X2 | 收款、开票、直邮至患者本人 | ✅ |
| A137 | X2 | 回传设备激活回执 | ⚠️ **是否愿给未定** |
| A138 | X2 | 接收不良事件回传并履行上报义务 | ✅ |
| A139 | X3 | `external_userid`、群关系、投递、**会话存档** | ⚠️ 存档能力与同意项 |
| A140 | X4 | 接收每日聚合运营指标 | ✅ |
| A141 | X5 | 提供诊断/处方/用药/检验（P1 即需） | ✅（若接口存在） |
| A142 | X5 | 接收 FHIR Bundle 导出（P2） | — |
| A143 | X6 | GATT 0x1808 上报指血读数 | ⚠️ 复合成功率 ≈48% |
| A144 | X7 | 短信/语音外呼（脱敏模板） | ✅ |
| A145 | X8 | HbA1c / C 肽 / 抗体报告（**须带方法学**） | ✅ **P0 下是主要客观证据** |
| A153 | X9 | 多品牌聚合中间层供数 | ⚠️ 接第二家厂商时的备选 |

---

## 3. 事件映射表

`⚡` 实时通道 · `🩸` 低血糖证据通道（免 R01）· `▤` 达标与分层通道（受 R01）

| # | 动作 | 事件 | 消费者 | 通道 |
|---|---|---|---|---|
| E01 | A02 | `consent.granted` / `.scope_changed` | S1、S8、S7 | — |
| E02 | A14 | `consent.revoked` | S10 级联 → S1/S8/S2/D5/X4；**并强制产出豁免告知** | — |
| E03 | A15 | `subject_request.received` | U10、S7 | — |
| E04 | A69 | `transfer.blocked_cross_border` | S7、U10、AI6 | — |
| E05 | A06/A07/A29/A94/A94b | `reading.ingested{data_age, source_channel, confidence}` | S3、S2、S5 | ⚡ |
| E06 | A82a/b | `reading.needs_review{reason}` | S8→U4 复核队列（**按决策影响分诊**，§9.1） | — |
| E07 | A25 | `reading.review_approved` / `.corrected` / `.retracted` | **S2 → `metrics.invalidated` → S3 重判 → S4 撤销 → D5 `plan.evidence_stale`** | 回流链 |
| E07b | **A96c** | **`reading.superseded{by_channel}`** | S2、S3 | **自动仲裁，非人工复核** |
| E08 | A97 | `session.recomputed` | S2 窗口重算 | 回流链 |
| E09 | A95 | `clock.drift_detected` | U11（**不回改历史 `time_utc`**） | — |
| E10 | A101 | `batch.rejected` | U11 死信队列 | — |
| E11 | A99/A82b | `trend.computed`（**P0 下来自截图箭头抽取，非回归拟合**） | S3（R05/R06/R25 唯一输入） | ⚡ |
| E12 | A96/A120 | `device.serial_observed` | S6 | — |
| E13 | A120 | `session.opened` / `.warmup_window` / `.closed` / `sensor.replaced` | S1、S2 | — |
| E14 | A122 | `sensor.expired` | S4、U4、X2 | — |
| E15 | A121 | **`ocr_value_disputed{delta_pct}`**（原 `calibration.mismatch`） | S1 → **整张原图退回重解析**、U4 | — |
| E16 | A05/A23 | `device.adverse_event_reported` | X2（法定上报义务）、S7 | — |
| E17 | A103 | `metrics.computed{window, wear_ratio, sufficiency_ok, tz_uncertain, brand_changed, metric_provenance}` | S3、AI1 | ▤ |
| E18 | A107 | `metrics.invalidated{window}` | S3、D5 | 回流链 |
| E19 | A106 | `agp.generated` | U5、AI1 | ▤ |
| E20 | A108/A108b/A109 | `rule.triggered{rule_id, level, evidence, channel}` | S4（H 级）、D5、U5 | ⚡/🩸/▤ |
| E21 | A110 | `hypo_episode.detected` | S2 统计、U5 | 🩸 |
| E21b | **A110b** | **`hypo_state.prolonged_risk_set` / `.recurrence_window_opened` / `.closure_blocked`** | S4（**阻止闭环**）、S3（阈值收紧）、U5（复核任务） | 🩸 |
| E22 | A109 | `tier.classified` / `service_need.classified` | D15（与 `disclosure_approved` 同表，默认 false）、D11a | ▤ |
| E23 | A109 | `remission.candidate` | U5 | ▤ |
| E24 | A113 | `alert.raised{level, confidence, direction}` | S8、U4、U3 | ⚡ |
| E24b | **A117b** | **`alert.suppressed{reason}`** | S7、§9.4 看板 | — |
| E25 | A115 | `alert.escalated` → `alert.escalated_emergency` | U4→U5→U1→U3；S7 | ⚡ |
| E26 | A27 | `alert.acknowledged` | S4、S7 时延台账 | — |
| E27 | A116 | `alert.value_recovered`（**降级提醒，非解除**） | S4 → 未闭环清单 → 晨会 | — |
| E28 | A28 | `alert.resolved` | S4 闭环、S7。**`hypo_state.closure_blocked` 时不得产生** | — |
| E29 | A133 | `data.silent_24h` | S4、U4 | — |
| E30 | A08/A30/A90 | `context_event.recorded` / `meal.photo_parsed` | AI5、S3 | — |
| E30b | **A10b** | **`symptom_tag.recorded` / `treatment_action.recorded`** | S3（R10 唯一输入）、S4（`alert.resolved` 判据） | 🩸 |
| E30c | **A10c** | **`ketone_reading.recorded`** | S3（R11/R12/R24 的"阳性"分支唯一输入） | ⚡ |
| E31 | A92 | `meal_response.computed` / `ppgr.insufficient_n` | S3、AI1 | ▤ |
| E32 | A85 | `plan.drafted` | AI3 | — |
| E32b | **A85** | **`plan.med_interaction_routed`**（药—方案交互命中 → 强制医师签发） | D5 路由 | — |
| E33 | A87/A88 | `gate.passed{gate_token}` / `gate.blocked{reason}` / `gate.override_requested` | S8、S7、D14 备案证据 | — |
| E34 | A49/A59 | `plan.signed` + 不可变依据快照 | S8、S3（阈值回灌）、S7 | — |
| E35 | A57 | `plan.evidence_stale` | D12 → U5 复核 | 回流链 |
| E36 | — | `plan.revoked` / `superseded` | S8、S7 | — |
| E37 | A49 | `tier.disclosure_approved` | D15、D11a、AI3 | — |
| E38 | A128 | `credential.valid` / `.expiring` / `.revoked` | **D5 签发硬门**、X2 引流硬门 | — |
| E38b | **A128b** | **`duty_roster.gap_detected`** | **H 阻断 → 该时段转"无夜间覆盖"并强制告知患者与家属** | — |
| E39 | A16/A22 | `package.purchased` / `milestone.due` / `package.completed` | S5、U4、U7 | — |
| E39b | **A64** | **`service_exit.recorded{stage, path, refund}`** | S5、U7、留存曲线看板 | — |
| E40 | A118 | `churn_signal.raised{code, severity, applicable}` | U4、U7（仅 S4/S10） | — |
| E41 | A53 | `taper_plan.signed`（原文快照 + hash） | S8（**不复述药名剂量**）、S7 | — |
| E42 | A54 | `remission_clock.started{day0}` / `.reset` | S3、S2、U5 | — |
| E43 | A56 | `remission.assessed{status, evidence_pack}` | D15（**不进对外物料接口**）、S7 | — |
| E44 | A67 | `compliance_incident.recorded` | U7 抄送、U10、S7；30 天 ≥3 次 → 停发言权 | — |
| E45 | A74 | `security_incident.reported`（24h） | U10 → 监管 | — |
| E46 | A125 | `delivery.rejected{reason}` | S7；**紧急链路上须立即升级至值班人** | — |
| E47 | A31 | `away_mode.entered` / `.exited` | S5 暂停计分；**S2 照常计入 R01 分母** | — |
| E48 | A132 | `vendor_grant.revoked` | S1、U4、`channel_degraded` | — |
| E49 | A76 | `channel.capability_changed` | S1 排程、S2 分母、S4 SLA、D5 话术、**逐患者 `reporting_tier` 重算** | — |
| **E50** | **A39c** | **`gateway.bound{sn, patient}`** | S11 启动采集、S9 覆盖状态重算、`patient_channel_binding` | — |
| **E51** | **A151** | **`gateway.offline{since}` / `carrier.stale`** | **S9 → `H`⑪ 覆盖状态变更 + 强制告知**、U4 A39d 跟进、D6a 话术降级 | — |
| **E52** | **A39e/A79c** | **`gateway.unbound{reason}`** | **同上；解绑不得静默生效** | — |
| **E53** | **A152** | **`readings.backfilled{count, span, max_data_age}`**（载体重连缓存补传） | S2 指标（**照常纳入**）、S3 **②低血糖证据通道 + ③汇总通道照常**、S4 **按 `data_age` 分档不发实时告警** | 🩸/▤ |
| **E54** | **A79b** | **`sdk_protocol.version_changed`** | U11 回归、`device_model`、**采集静默失效风险告警** | — |

**观察**：E07/E07b/E08/E18/E35 组成的**回流链**在 P0 是高频主路径（每次复核否决都要撤销告警、重算指标、通知签发人），不是异常路径。E21b 与 E30b/E30c 是本次评审新增的三条**安全事件**，初稿全部缺失。

---

## 4. 数据追踪表（动作级读写）

| 动作 | Reads | Writes |
|---|---|---|
| A02 | 条款模板、共享清单版本 | `consent_record`（快照 + hash + 版本 + 签名）、`audit_log` |
| A14 | `consent_record` | `consent_revocation`；触发下游级联 |
| A41 | — | `patient_profile.meds` + **四标签** |
| A41b | 药盒照片 | **`med_class_hint`**（与 `meds` 严格分离，仅供 S3 开闸） |
| A43/A44 | 体测、化验（**含 eGFR**）、`patient_profile` | `enrollment_decision`、`health_tier`、目标区间版本、`service_package` |
| A03/A136 | — | `device_transaction_ref`（**只存订单号引用**） |
| A05/A120 | `device_model`、`channel_registry` | `sensor_session`（**时间基线已迁出**）、`wear_site_record` |
| A06/A82a/A82b | `channel_registry` | `media_asset`（原图 + 脱敏图）、`ingest_batch`、候选 `glucose_reading`（曲线读数带 `sampling_interval_inferred`） |
| A07/A143 | `device_clock_offset` | `glucose_reading{smbg, ble_gls_1808}` |
| A25 | 候选读数 + 原图 | **retract + 新增修正记录**（`value_raw`/`unit_raw` 不可变，不得原地改）、回流事件 |
| A94–A98 | `channel_registry`、`device_model`、`sensor_session`、`consent_record` | `glucose_reading`、`ingest_batch`、`quality_flag`、`artifact_suspected` |
| A96 | 已有读数 | `dedup_key`（`time_utc(分钟)`；可空列用哨兵值） |
| A96c | `channel_registry.source_confidence` 排序 | `reading.superseded{by_channel}` |
| A103–A105 | 干净读数、`sensor_session`、`device_model` | `cgm_summary{wear_ratio, sufficiency_ok, tz_uncertain, brand_changed, metric_provenance, renal_unknown}` |
| A108/A108b/A109 | 读数、`trend`、`cgm_summary`、`patient_profile{age,pregnant,meds,eGFR,health_tier}`、**`med_class_hint`**、`alert_threshold` | `rule_hit`、`hypo_episode`、`hypo_state`、`tier_label`(+`disclosure_approved=false`) |
| A112/A48 | 规则命中 / 临床判断 | `alert_threshold`（每字段带 `safe_direction`）、`threshold_change_log` |
| A113/A114 | `rule_hit`、`duty_roster`、`channel_registry` | `alert_event` |
| A117b | 抑制决策 | **`alert_suppressed_log`** |
| A27/A28 | `alert_event`、**`hypo_state`** | `alert_ack`；`closure_blocked` 时**不得写 `alert.resolved`** |
| A115 | `alert_event`、`duty_roster`、`emergency_contact`、`contact_consent` | `alert_escalation` |
| A10b | 告警卡片 | **`symptom_tag`、`treatment_action`**（写入 `context_event`） |
| A10c | — | **`ketone_reading`** |
| A81b | 门店设备直采 | **`body_measurement{measured_at, device_id, protocol_version, fasting, 体重/腰围/体脂}`** |
| A81/A145 | 标本 | **`lab_result{value, method, lab_id, is_ngsp_certified, specimen_type}`** |
| A92 | `context_event`、读数（**排除 SKU**） | `meal_response` |
| A85 | `analysis_result`、模板库、**`meds`/`med_class_hint`** | `plan_draft`；命中药—方案交互则 `plan.med_interaction_routed` |
| A87/A88 | 文本、词库、`disclosure_approved` | `compliance_check_log`、`gate_token` |
| A49/A59 | 草稿、`cgm_summary`、`credential`、审阅证据 | `plan_signed` + 不可变快照、`review_evidence` |
| A125/A126 | `gate_token`、触达同意、`patient_identity_link` | `delivery_receipt` 或 `delivery.rejected` |
| A118 | `cgm_summary`、**`delivery_receipt`（S7 分母改用已送达）**、`alert_ack`、`context_event`、群互动 | `churn_signal{code, severity, applicable}` |
| A64 | 合同、履约 | **`service_exit_record{exit_at, exit_stage, exit_path(P1–P6), refund_amount, fulfilled_days, last_churn_signal}`** |
| A53/A54 | `meds`、证据包 | `taper_plan`（原文 + hash）、`remission_clock` |
| A56 | `lab_result`（**同一方法学配对**）、GMI 四条件、`device_model.MARD` | `remission_assessment`、`remission_status` |
| A61 | 复盘输入 | **`psych_note`**（受最严可见性档约束） |
| A66 | — | **`store_readiness_check`** → 服务包开通闸 |
| A67/A68 | — | `phrase_library`、`banned_term_library`、`compliance_incident` |
| A72 | — | `credential` |
| A76/A77 | — | `channel_registry`（通道属性）／ `device_model`（**含 MARD**） |
| A123b | `alert_event`、`alert_ack` | 时延聚合指标 |
| A133b | 全量质量字段 | **数据质量看板指标（§9.4）** |
| 全部 | — | `audit_log`（横切，只进不出） |

---

## 5. 完整行为矩阵

按四个流程分段。为控制篇幅，只保留有事件或有写入的行；纯读取归 §8。

### 5.1 流程一 · 入组

| Actor | 动作 | 事件 | Data In | Data Out | 域 | P0 | Skill |
|---|---|---|---|---|---|---|---|
| U12 | A80 到店 5min 随机指血 | — | — | `glucose_reading{smbg}`、**`onsite_triage_record`** | D1 | ✅ | `U` |
| U5 | A40 红旗筛查（急症 / 1型·LADA） | — | 主诉、病程、BMI、体重轨迹 | `enrollment_decision.flags` | D15 | ✅ | `U` |
| U5/U13 | A41 结构化用药清单 + 四标签 | — | — | `patient_profile.meds` | D15 | ✅ | `U`（**健管师不可见此技能**） |
| U4/AI6 | A41b 采集 `med_class_hint` | — | 药盒照片/自报 | `med_class_hint`（未经医师确认） | D15 | ✅ | `A` **仅供 S3 开闸** |
| U12/X8 | A81/A145 化验 | — | 标本 | `lab_result{method, is_ngsp_certified}` | X8 | ✅ | `—` |
| U5 | A43 入组判定 + ABCD(R30) | — | 化验、体测、病程 | `enrollment_decision`、`service_package` | D11a | ✅ | `U` 齐全性预填卡片 |
| U5 | A44 目标区间 + `health_tier` | — | age、合并症、ADL、认知、**eGFR** | `health_tier` + 目标区间版本 | D15/D2 | ✅ | `U` 老年三分层向导 |
| U1/U2 | A02 逐项勾选签同意书 | `consent.granted` | 条款 + 共享清单 | `consent_record` | D7 | ✅ | **`H` ①同意闸** |
| U1/U2 | A03 持证方下单 | — | 引流码 | `device_transaction_ref` | X2 | ✅ | `—` |
| S9 | 校验经销商证照 | `credential.valid` | `credential` | 放行/停止引流 | D18 | ✅ | **`H` ④** |
| U4 | A24 配置告警接收人 + 夜间兜底 + 紧急联系人 | — | — | `duty_roster`、`emergency_contact` | D4/D12 | ✅ | **`H` ⑦未配齐阻断佩戴** |
| U3 | 紧急联系人本人确认 | — | 短信链接 | `contact_consent` | D7 | ✅ | `A` **未确认不得外呼** |
| U4/U5 | **配发血酮仪/尿酮试纸 + 现场教学** | — | `meds`/病程/DKA 史 | 配发留痕 | D11a | ✅ | **`H` ⑨**（`sglt2i`／胰岛素／病程>10y／DKA 史 → 佩戴前置硬闸） |
| U4 | A23 佩戴指导 + 安全认知四条 + 部位评估 | — | — | **`education_record`**、`wear_site_record` | D11a | ✅ | `U` |
| S6 | A120 建 session | `session.opened` | `device_model`、`channel_registry` | `sensor_session` | D8a | ⚠️ 手工录 SN | `A` |
| S1 | **采集时间基线** | — | 手机时区、时钟偏差 | **`patient_time_baseline`（患者属性，非 session）** | D1/D15 | ✅ | `A` |
| U1/U2 | A04 厂商 App 授权 | — | — | `vendor_grant` | X1/D7 | ❌ | `—` |
| S1 | 通道能力查表 + 绑定 | `channel.capability_changed` | `channel_registry` | **`patient_channel_binding` + `reporting_tier`** | D1 | ✅ | `A` |
| S1 | 通道连通性验证（离店闸） | — | 实测 1 条读数 | `enrolled_pending_channel` 或 E1 | D1 | ✅ | **`H` ⑥** |
| S1 | 建档与团队分配 | — | 全部基线 | `patient_profile`、`patient_identity_link` | D15 | ✅ | `A` |
| U4 | 建企微群（店长不入群） | — | `external_userid` | 群 + webhook key 入 KMS | D16 | ✅ | `A` |
| S10 | **会话存档同意项判定** | — | `consent_record` | 未勾选 → `no_community_safety_net=true` **并强制告知** | D7 | ✅ | **`H`（并入①）** |
| U10 | A75 存量患者补签 | `consent.granted{legacy}` | 历史数据源表 | `legacy_import=true`；未签则封存 | D7 | ✅ | `H` + `S` |
| U7 | A66 存量物料清查 | — | — | **`store_readiness_check`** → 开通闸 | D6b/D11a | ✅ | **`H` ⑤（并入 SKU 闸）** |

### 5.2 流程二 · 日常监测与告警

| Actor | 动作 | 事件 | Data In | Data Out | 域 | P0 | Skill |
|---|---|---|---|---|---|---|---|
| S1 | A94 定时拉取厂商云 | `reading.ingested` | 游标 | `glucose_reading` | D1 | ❌ | `S` |
| U4/U1 | **A39b/A04b 机构端导出并上传** | `reading.ingested` | 导出文件 | `glucose_reading{vendor_export, conf=1.0}` | D1 | ⚠️ 兜底/对账 | `U` 批量导入 |
| U1/U2 | A06 上传截图/PDF | — | — | `media_asset` | D17 | ✅ | `U` |
| AI6 | A82a 单点抽取 | `reading.needs_review` | 脱敏图 | 候选读数 conf ≤0.9 | D1 | ✅ | `A` |
| AI6 | **A82b 曲线序列抽取** | `reading.ingested{ocr_curve}` | 脱敏图 | 曲线读数 conf ≤0.7 + `metric_provenance=ocr_curve_estimated` | D1 | ⚠️ **不入 `active%`、不触发告警、可进 AGP 与"疑似"`hypo_episode`** | `A` |
| S1 | A100 单位合理性硬规则 | `batch.rejected` | 候选读数 | 硬阻断 → 复核 | D1 | ✅ | **`H` ⑧** |
| X6 | A143 指血 BLE | `reading.ingested` | GATT 0x1808 | `glucose_reading{smbg}` | D1 | ⚠️ 全天完整率≈48% | `A` |
| U4 | A29 手工录入 | `reading.ingested` | 口述 | `glucose_reading{manual}` | D1 | ✅ | `U` |
| S1 | A95–A98 归一/去重/仲裁/会话/打标 | `reading.ingested{data_age}` | 主数据 | 落库 + `quality_flag` | D1 | ✅ | `A` |
| S1 | **A96b/A96c 近似去重 + 通道仲裁** | `reading.superseded` | `source_confidence` 排序 | `suspect_duplicate` / `superseded` | D1 | ✅ | `A` |
| S1 | A99/A82b 趋势 | `trend.computed` | 截图箭头（P0）/ 回归（P1） | `trend` | D1 | ⚠️ | `A` |
| S6 | A121 **OCR–指血一致性校验** | `ocr_value_disputed` | 指血 vs 同日 ±15min OCR 值 | 差异>20% 或 >3.0 → **整张原图退回重解析** | D8a | ⚠️ **P0 唯一跨通道客观对拍** | `A` |
| U4 | A25 OCR 复核（**按决策影响分诊**） | 回流事件 | 候选 + 原图 | retract + 修正记录 | D1/D12 | ✅ **瓶颈** | `U` 批量复核台 |
| S2 | A107 消费回流 | `metrics.invalidated` | 回流事件 | `cgm_summary.stale` + 重算 | D3 | ✅ | `A` |
| S4 | A117 撤销已发告警 | — | `metrics.invalidated` | 更正卡片 | D4 | ✅ | `A` |
| S3 | A108 ①实时通道（**R02 先于 R03/R04**） | `rule.triggered` | 读数 + `trend` + `meds`/`med_class_hint` + `health_tier` | `rule_hit`、`artifact_suspected` | D2 | ⚠️ | `A` |
| S3 | **A108b ②低血糖证据通道（免 R01）** | `rule.triggered{R09/R10/R07}` | `hypo_episode` 累积 + `symptom_tag` | `rule_hit` → **A45 去强化审查** | D2 | ✅ **新增** | `A` |
| S3 | A110 `hypo_episode` | `hypo_episode.detected` | 连续读数 ≥15min | `hypo_episode` | D2 | ⚠️ | `A` |
| S3 | **A110b `hypo_state` 状态机** | `hypo_state.*` | `meds ∩ {磺脲, 长效/预混胰岛素}`；24h 内 L2 | `prolonged_risk` / `recurrence_window_until` / `closure_blocked_reason` | D2 | ✅ **新增** | `A` |
| S3 | A112 阈值**收紧**（含 `symptom_masking_med` → R10 直接成立） | — | 规则命中 | `alert_threshold`、`threshold_change_log` | D2 | ✅ | `A` |
| U5 | A48 阈值**放宽（任何方向）** | — | 临床判断 | 同上 | D2 | ✅ | `U`（**仅医师**） |
| S4 | A113 去抖 + 限流 | — | `rule_hit`、告警状态 | 排队/抑制/**H 级低血糖抢占不占桶** | D4 | ✅ | `A` |
| S4 | **A117b 抑制留痕** | `alert.suppressed` | 抑制决策 | `alert_suppressed_log` | D4 | ✅ **新增** | `A` |
| S4 | A114 分级推送 | `alert.raised` | 预审冻结模板 | 投递请求；**低值方向无论 conf 推患者本人固定模板** | D4 | ⚠️ | `A` **不经 LLM** |
| S8 | A125 投递准入 | `delivery.rejected` | `gate_token` / 触达同意 | 投递或硬拒 | D16 | ✅ | **`H` ③** |
| U1/U2 | A10/A10b 处置 + **一键症状与补糖回填** | `symptom_tag.recorded` | 固定 15-15 话术 | 复测读数 + `treatment_action` | D4/D9 | ✅ | `U` **告警卡片内** |
| U1/U2 | **A10c 酮体自测录入** | `ketone_reading.recorded` | 试纸/血酮仪 | `ketone_reading` | D9 | ✅ | `U` |
| U4 | A27/A28 响应回执 | `alert.acknowledged` | `alert_event` + **`hypo_state`** | `alert_ack`；**`closure_blocked` 时不得闭环** | D4 | ⚠️ | `U` |
| S4 | A116 T+15min 复测检查 | — | 近期读数 | 再推 + @健管师 | D4 | ⚠️ | `S` |
| S4 | 解除判定 | `alert.resolved` / `.value_recovered` | 人工回执或指血 + `hypo_state` | 闭环 / **未闭环清单** / **`monitoring_extended`** | D4 | ⚠️ | `A` |
| S4 | A115 三级升级链 | `alert.escalated` → `_emergency` | `duty_roster`、`emergency_contact` | `alert_escalation` | D4 | ❌ 夜间失效 | `S` |
| S9 | **A128b 值班链尾具名持续校验** | `duty_roster.gap_detected` | `duty_roster` | 阻断 + 转"无夜间覆盖"+ 强制告知 | D4/D18 | ✅ | **`H` ⑩** |
| S1/S6 | A133 静默检测（P0 口径="无上传"） | `data.silent_24h` | gap 清单 | 提醒 + 任务 | D1 | ⚠️ | `S` |
| U4 | A31 静默回访 + `away_mode` | `away_mode.entered` | — | `away_days`（**有上限、超限需 U7 审批**） | D11a | ✅ | `U` |
| S6 | A122 到期三次提醒 | `sensor.expired` | `sensor_session` | 提醒 → X2 | D8a | ⚠️ | `S` |
| AI4 | A89 意图分类 + **危急表述识别** | — | 会话存档 | 意图标签；**老年不典型表述（跌倒/叫不醒/胡言乱语/抽搐）直接进 Level 3 处置链，不得要求先复测** | D9 | ⚠️ **依赖存档同意** | `A` |
| AI4 | A90 餐食抽取 | `context_event.recorded` | 群消息 | `context_event` | D9 | ⚠️ | `A` |
| AI4 | A91 用药/疗效硬阻断 | — | 意图命中 | 固定话术 + 医师任务（附近 72h 上下文）+ **`referral_record`** | D9/D6a | ⚠️ | `H` |
| U5 | A47 回答用药问题 | — | 转介任务 | 医师本人回复 + **`clinical_reply_record`** | D5 | ✅ | `U` |
| AI5 | A92 餐后配对 | `meal_response.computed` | `context_event` + 读数 | `meal_response` | D10 | ⚠️ | `A` |
| S2 | A103 06:00 批算 | `metrics.computed` | 干净读数 | `cgm_summary` | D3 | ⚠️ | `S` |
| AI1 | A84 日报文案 | — | `cgm_summary` | 日报草稿（**数据不足禁写"平稳"**） | D3 | ⚠️ | `A` |
| S8 | A127 飞书 06:30 | — | 聚合运营指标 | X4 表行 | D16 | ✅ | `S` |
| U10 | A67 人工话术监测与抽检 | `compliance_incident.recorded` | 会话存档关键词命中片段 | `compliance_incident` | D6b | ✅ | `A` + `U` |
| S5 | A118 流失信号 | `churn_signal.raised` | 多源（**S7 分母 = 已送达**） | `churn_signal{applicable}` | D11a | ⚠️ | `S` |
| U4 | A39 流失响应 | — | `churn_signal` | 挽留动作记录 | D12 | ⚠️ | `U` |
| U7/U4 | **A64 退出归因** | `service_exit.recorded` | 合同、履约、末次信号 | **`service_exit_record`** | D11a | ✅ **新增** | `U` |
| S10 | A129–A131 授权变更与撤回 | `consent.revoked` | `consent_record` | 级联 + **豁免告知** | D7 | ✅ | `H` + `A` |
| U11 | A78 死信/孤儿/漂移 | — | 运维告警 | 修复（**仅元数据**） | D1 | ✅ | `U` 运维台 |
| S1 | **A133b 数据质量看板批算** | — | 全量质量字段 | §9.4 指标集 | D1/D12 | ✅ **新增** | `S` |

### 5.3 流程三 · 周期复盘与方案调整

| Actor | 动作 | 事件 | Data In | Data Out | 域 | P0 | Skill |
|---|---|---|---|---|---|---|---|
| S2 | A104 R01 门槛判定 | `metrics.computed` | 连续读数 ÷ 期望条数 | `sufficiency_ok` | D3 | ✅ 有载体即可达标；纯兜底期不通过 | `H` 门槛闸（**仅约束通道③**） |
| S2 | A106 AGP 渲染 + session 构成披露 | `agp.generated` | 14 天读数 | AGP + `sensor_bias_suspected` | D3 | ⚠️ | `A` |
| S3 | 目标区间选择（R28/R31） | — | `patient_profile` | 阈值集 | D2 | ✅ | `A` |
| U4/U5 | **登记急性混杂因素** | — | 感染/激素/住院/用药调整 | **`clinical_context_event`** | D2 | ✅ **新增，否则 `confounded_window` 永不命中** | `U` |
| S3 | `confounded_window` 判定 | — | `clinical_context_event` | 窗口标记 | D2 | ✅ | `A` |
| S3 | **A108b 低血糖证据（R09/R10）** | `rule.triggered` | `hypo_episode` 累积 | 去强化审查任务 | D2 | ✅ **免 R01** | `A` |
| U5 | A45 去强化审查 | — | **低血糖事件明细表（报告第一页）** | 用药调整 → X5 | D5/X5 | ✅ | `U` |
| S3 | A109 达标与分层规则（R13–R18/R22） | `rule.triggered` | `cgm_summary` | `rule_hit` | D2 | ⚠️ | `A` |
| S3 | GMI 计算（四条前提，任一不满足 → null） | — | `source_channel`、`active%`、品牌一致性、**`device_model.MARD`** | `gmi` 或 null | D3 | ⚠️ | `A` |
| S3 | R17 GMI–HbA1c 一致性 | — | GMI + `lab_result`（**同一方法学**） | 标注 | D2 | ⚠️ | `A` |
| S3 | R18 / 服务需求分层 | `tier.classified` | 指标 | `tier_label` + `disclosure_approved=false` | D2/D15 | ⚠️ | `A` |
| AI5 | A92 餐后个性化门槛 | `ppgr.insufficient_n` | 同类餐≥2–3 次 + 间隔≥2h + `cross_brand=false` | 个体食物排序（内部） | D10 | ⚠️ | `A` |
| AI1 | A83 分析结论 JSON | — | `cgm_summary`、`rule_hit`、`meal_response` | `analysis_result` | D3 | ⚠️ | `A` |
| AI2 | A85 方案草稿 | `plan.drafted` / **`plan.med_interaction_routed`** | `analysis_result` + 模板 + **`meds`** | `plan_draft` | D5 | ⚠️ | `A` |
| AI3 | A87 四道闸 | `gate.passed` / `.blocked` | 草稿、词库、`disclosure_approved` | `compliance_check_log` + `gate_token` | D6a | ✅ | **`H` ②可单测组件** |
| U6/U5 | 2 次不过后人工改写 | — | 拦截命中项 | 改写 + prompt 缺陷清单 | D6a | ✅ | `U` |
| S9 | A128 签发人资质校验 | `credential.valid` | `credential` | 放行或**自动冻结签发权** | D18 | ✅ | **`H` ④** |
| U5 | A49 医师签发 | `plan.signed` | 草稿 + AGP + 命中规则 + 依据快照 | `plan_signed` + `review_evidence` | D5 | ⚠️ | `U`（**无"全部通过"按钮**） |
| U6 | A59 营养师签发 | `plan.signed` | 同上 | `plan_signed` | D5 | ⚠️ **不得越过药—方案交互路由** | `U` |
| U8+U5 | A60+A52 运动双签发 | `plan.signed` | 禁忌筛查 + R23/R24 | `plan_signed` | D5 | ✅ | `U` |
| U4 | A36 教育模板内容（免签） | — | 模板库 | 群消息 | D6b/D16 | ✅ | `U` |
| S8 | A126 投递 | — | `gate_token` + 触达同意 | `delivery_receipt` | D16 | ✅ | `A` |
| S3 | 阈值回灌流程二 | — | `plan_signed` | `alert_threshold` 更新 | D2 | ✅ | `A` |
| U4 | A35 48h 未读跟进 | — | **已送达但未读**清单 | 跟进记录 | D12 | ✅ | `S`+`U` |
| U5 | A50 到店逐屏解读 | — | AGP 或趋势 | 解读记录 + 复测 | D5 | ⚠️ | `—` |
| U4 | **A81b 体测采集** | — | 门店设备直采 | **`body_measurement`** | D11a | ✅ **新增** | `A` |
| U5+五师 | A51 五师复盘 | — | 全量 | 下周期目标 + 分工 | D12 | ⚠️ | `U` 复盘看板 |
| U9 | A61 心理介入 | — | 主观感受 | **`psych_note`** | D12 | ✅ | `U` |
| AI2 | A86 结营报告 | — | 全周期 | 结营报告（**聚合，禁个案对比**） | D11b | ⚠️ | `A` |
| S5/U7 | A65 KPI 达标判定（**安全门一票否决**） | — | TBR 安全门 + 有效性 | `kpi_settlement` | D11b | ✅ 有载体则 TBR 安全门可算；无载体需代理指标（§11.4） | `A` **红线写死** |
| U5 | 升级适宜性判断（先于商务） | — | 指标 + ABCD + 意愿 | 适宜性结论落库 | D5 | ✅ | `H`（并入商务解锁） |

### 5.4 流程四 · 缓解判定与退出

| Actor | 动作 | 事件 | Data In | Data Out | 域 | P0 | Skill |
|---|---|---|---|---|---|---|---|
| S3 | R30 ABCD 复核 | — | 抗体、C 肽、BMI/腰围、病程 | 适宜性维持或退出 | D2 | ✅ | `A` |
| U5 | A53 评估可否停药 + 签发减停计划 | `taper_plan.signed` | 强化期证据包 | `taper_plan`（原文 + hash） | D5 | ✅ | `U`（**AI 不得建议**） |
| S3 | **C 包 P0 准入四条硬闸** | — | SMBG 频次承诺、血酮仪已配发教学完成、家属已确认为紧急联系人、`reporting_tier` 已告知 | 不齐则 `remission_clock` **不得启动** | D2/D11a | ✅ **新增**；有载体时第①条改为"载体在线率达标" | **`H`（并入⑨）** |
| S8 | 减停期固定模板提醒 | — | `taper_plan` | "第 N 天，请按医师原方案执行"（**不复述药名剂量**） | D16 | ✅ | `S`+`H` |
| U5 | A54 确认 Day 0 | `remission_clock.started` | 医师确认 | `remission_clock` | D5 | ✅ | `U` |
| S3 | 反弹监测 R33 | `rule.triggered` | 连续 7 天均值 ≥8.6 / TAR / **停药后任一 L1 低血糖** / 体重+酮体 | 推医师 | D2 | ✅ 有载体则 R33 完整成立；无载体用指血序列降级版，**不得标称 GMI** | `A` |
| U5 | A55 决定是否复药 | `remission_clock.reset` | 反弹证据 | 计时清零 | D5 | ✅ | `U` |
| S8 | 复测前 14 天启动 CGM 提醒 | `milestone.due` | `remission_clock` | 排程锁定 | D11a | ⚠️ | `S` **最易漏的排程依赖** |
| X8 | A145 复测 | — | 标本 | `lab_result{method}` | X8 | ✅ **P0 主要客观证据** | `—` |
| S3 | GMI 替代资格四条判定 | — | 100% 连续通道、同品牌同型号、active%≥70、**`device_model.MARD` ≤10%** | 允许/禁止用 GMI | D2/D3 | ⚠️ | `H` |
| U5 | A56 缓解判定与签发 | `remission.assessed` | `lab_result`（**同方法学配对**）+ `remission_evidence_pack` | `remission_assessment` | D5 | ✅ 有载体则判定与过程监测均成立（GMI 可用）；**无载体时判定可用、过程监测失效** | `U` |
| U5 | 面诊告知（缓解≠治愈） | — | 判定结论 | 告知留痕 | D5 | ✅ | `—` |
| U7/U4 | A38 承诺兑现判定 | — | 佩戴率 / 触点 / 打卡 / **`body_measurement`** | `kpi_settlement` | D11b | ⚠️ | `U` |
| S10 | A14 撤回/结营授权处理 | `consent.revoked` | 患者意愿 | 停处理、解绑、退群、删群内卡片 | D7 | ✅ | `H` |
| S7 | 分类删除/匿名化（诊疗记录例外） | — | 数据分类 | 删除或匿名化 + 凭证 | D13 | ✅ | `S` |
| U1/U2 | A15 数据可携导出 | `subject_request.received` | 全量 | FHIR-style / CSV | D7 | ✅ | `U` |
| U10 | 聚合成效数据集纳入 | — | 二次使用授权 | 聚合集（带样本量 + 口径 + 时间窗） | D11b | ⚠️ | `A` **严禁个案对比** |

---

## 6. 数据实体归属图

`W` = 写者（**粗体 = 唯一写者**）。任务清单要求的 18 个实体全部在列；**＋** = 本次评审增补（共 30 个）。

| 实体 | Written by | Read by | 关键约束 | 域 |
|---|---|---|---|---|
| `glucose_reading` | **S1**（唯一物理写者） | S2,S3,S4,S6,AI1,AI5,U4,U5,U11 | `value_raw`/`unit_raw` **不可变**；更正走 retract+新增，不得原地改 | D1 |
| `quality_flag` / `artifact_suspected` ＋ | **S1**（唯一） | S2（只过滤，永不重推导）, S3, U4 | — | D1 |
| `ingest_batch` | S1, AI6 | U11, S7 | 可整批回滚 | D1 |
| `media_asset` ＋ | U1,U2,U4 | AI6（**只见脱敏图**）, U4（原图需授权）, S7 | 分层存储 + 短时效签名 | D17 |
| `vendor_report` / `vendor_summary_snapshot` ＋ | S1, AI6 | U5, U4 | **不进 D3**；强制携带 `vendor, algo_version, 分母定义`；界面须标"非本平台口径、不可与历史比较" | D1 |
| `channel_registry` ＋ | **U11**（唯一） | S1,S2,S3,S4,S6,S10 | **通道级属性**：`capability_level / storage_region / sampling_interval / rate_limit / is_incremental_cursor / supports_realtime_alert / observed_latency_p95 / DPA 编号`。**MARD 已迁出** | D1 |
| `device_model` ＋ | **U11**（唯一） | S1,S2（分母）,S3（GMI 准入）,S6 | 采样率/预热/寿命/品牌/原生单位/**MARD** | D8a |
| **`patient_channel_binding` + `carrier_type` + `reporting_tier` + `night_coverage`** ＋ | S1（验证时）, U11, U4（配发时） | S2,S3,S4,D5 话术,D11b,D6a,S9 | **逐患者**的通道 × **载体**画像、报告口径与**夜间覆盖真实状态**。D6a 拦"达标/TIR"与拦"夜间监护承诺"都是逐患者开关 | D1 |
| **`gateway_device`** ＋ | **U4**（配发/绑定/回收）· **U7**（资产台账/催收）· **U11**（远程解绑/置换/固件） | U1/U3（仅在线状态）, S4, S9, S11 | `{sn, model, firmware, bound_patient, bound_at, last_heartbeat_at, online, unbound_at, returned_at, asset_status}`。<br>**硬约束**：解绑或离线 >N 小时必须产出 **`gateway.unbound` / `gateway.offline`** 并**强制触发夜间覆盖状态变更告知**（豁免于触达封锁，同 `consent.revoked` 逻辑）——**否则患者不知道安全网已经撤了，这正是"我以为有人在看"的经典成因** | D8a/D11a |
| `sensor_session` | **S6**（唯一） | S1,S2,S3,U4,U5 | 归属为晚绑定可重算属性；**时间基线已迁出** | D8a |
| **`patient_time_baseline`** ＋ | **S1**（唯一） | S1 归一, S2 | 患者属性非传感器属性；`clock_offset` 留在 session | D1/D15 |
| `calibration` → **OCR–指血一致性记录** ＋ | S6 | U4,U5,§9.4 看板 | P0 语义 = 验 OCR 对不对，不是验传感器准不准 | D8a |
| `wear_site_record` ＋ | U4 | U4,U5,S6 | 同部位 <28 天复用 → 提示；脂肪增生是 `sensor_bias_suspected` 的真实病因 | D8a |
| `context_event` | U1,U2,U3,U4,AI4 | AI5,S3,S2 | `event_type` **禁用 "MNT"**，用 `supplement_checkin` | D9 |
| **`symptom_tag` / `treatment_action`** ＋ | **U1/U2/U3**（告警卡片一键） | S3（R10 唯一输入）, S4（`resolved` 判据） | 无它则 R10 永不触发、且分不清"补糖回升"与"伪差解除" | D9/D4 |
| **`ketone_reading`** ＋ | U1/U2/U3 | S3 | R11/R12/R24 的"阳性"分支唯一输入 | D9 |
| **`clinical_context_event`** ＋ | U5/U4 | S3 | 急性病/感染/激素/住院/用药调整期；无它 `confounded_window` 永不命中 | D2 |
| `meal_response` ＋ | **AI5**（唯一） | AI1,U6,S3 | 配对**显式排除 X4 SKU** | D10 |
| `hypo_episode` ＋ | **S3**（唯一） | S2,U5,S4 | 事件定义唯一归 D2 | D2 |
| **`hypo_state`** ＋ | **S3**（唯一） | S4（**阻止闭环**）, U4（只读）, U5 | `prolonged_risk`（磺脲/长效胰岛素）· `recurrence_window_until`（HAAF 24h）· `closure_blocked_reason`（**无人可写**） | D2 |
| `cgm_summary` | **S2**（唯一） | S3,AI1,U4,U5,D5,D11b,S5 | `wear_ratio`/`sufficiency_ok` 唯一计算者；`renal_unknown` | D3 |
| `patient_profile`（`health_tier`/`meds` 四标签/`eGFR`/抗体/C肽/`away_mode`/`remission_status`/`tier_label`+`disclosure_approved`） | U5/U13（临床）, U4（非临床）, X5（只读镜像） | 全域 | **健管师禁写 `meds` 与 `health_tier`**；`tier_label` 必与 `disclosure_approved` 同表且默认 false | D15 |
| **`med_class_hint`** ＋ | U4/U1/AI6 | **仅 S3** | 患者自报/药盒照片；**与 `meds` 严格分离**；永不展示患者、永不进方案话术、永不用于用药建议。它让 R12 在 P0 能工作而不越 §21 红线 | D15 |
| **`lab_result`** ＋ | U12/X8/U5 | S3, D5, D11b | 必带 `method / lab_id / is_ngsp_certified / specimen_type`；R29 与聚合举证**只接受同方法学配对**，跨方法标 `evidence_incomparable` | X8/D15 |
| **`body_measurement`** ＋ | **U4**（门店设备直采） | S5(S12), D11b, U5 | 必带 `device_id / protocol_version / fasting`；承诺兑现**只认同设备同协议配对** | D11a |
| `patient_identity_link` ＋ | S1 | S8,X3,X4 | — | D15 |
| `consent_record` | **S10**（唯一，U1/U2 签署） | S1,S2,S5,S8,S10,U10,D11a,D12 | 七项独立勾选**不得合并**；**会话存档为独立项**，未勾选 → `no_community_safety_net` | D7 |
| `consent_revocation` ＋ | **S10**（唯一） | 全部下游 | 必产出**豁免于触达封锁**的告知 | D7 |
| `contact_consent` ＋ | S10 | S4, X7 | 未确认前**不得外呼** | D7 |
| `vendor_grant` ＋ | S1, S10 | S1 | 每日校验 | D7/X1 |
| `alert_threshold` ＋ | S3（自动**收紧**）, **U5**（唯一可**放宽**） | S3, S4 | 每字段带 `safe_direction`；**收紧/放宽 ≠ 数值上下** | D2 |
| `threshold_change_log` ＋ | S3, U5 | U5, S7 | — | D2 |
| `alert_event` | **S4**（唯一） | U4,U5,U3,S7,S5 | `data_age` 分档控制告警资格；**低值方向不受 conf 门限** | D4 |
| `alert_ack` | U4, U5 | S4,S7,S5,U7（**仅聚合**） | `hypo_state.closure_blocked` 时不得产生 `resolved` | D4 |
| `alert_escalation` ＋ | **S4**（唯一） | U10,U7,S7 | 全程审计 | D4 |
| **`alert_suppressed_log`** ＋ | **S4**（唯一） | S7, §9.4 看板 | 任何被限流或去抖抑制的告警必须留痕，否则限流是黑洞 | D4 |
| **`alert_false_positive_log`** ＋ | S4/U4 | §9.4 看板 | **误报率 = 低血糖安全网的存活率指标**，比响应时延更重要 | D4 |
| `duty_roster` ＋ | U7/U4 排班 | S4, S9 | **任一时段留空即 `H` 阻断**；夜间链尾必须具名 | D4/D12 |
| `emergency_contact` ＋ | U1/U2 登记 | S4, X7 | 需 `contact_consent` | D4/D15 |
| `plan_draft` | **AI2**（唯一） | AI3,U5,U6,U8 | 药—方案交互命中则强制医师路由 | D5 |
| **`plan_signed`** | **U5/U6/U8**（唯一；**AI 绝对禁写**） | S8,S3,S7,U4 | 不可变依据快照 + `review_evidence` | D5 |
| `taper_plan` ＋ | **U5**（唯一） | S8（只渲染原文）,U1,U3 | 原文快照 + hash；**智能体不得摘要改写** | D5 |
| `compliance_check_log` | **AI3**（唯一） | U10,S7,D14 备案证据 | 含模型/prompt 版本、拦截历史 | D6a |
| `gate_token` ＋ | **AI3**（唯一签发） | S8 | 无 token 硬拒 | D6a/D16 |
| `banned_term_library` / `phrase_library` ＋ | **U10**（唯一） | AI3,U4,U7 | 数据化可版本化。**"睡前吃根黄瓜"须入库** | D6a/D6b |
| `compliance_incident` ＋ | S7/AI 扫描, U10 | U7, U10 | 30 天 ≥3 次 → 停发言权 | D6b |
| `credential` ＋ | **U10**（唯一） | S9, D5 闸, X2 闸 | 到期即冻结 | D18 |
| `service_package` | U7/U4, S5（履约） | U1,U3,U7,S5,D11b | 合同**不含器械（含租赁）** | D11a |
| **`service_exit_record`** ＋ | **U4/U7**（唯一） | S5, U7, 留存曲线看板 | `exit_stage / exit_path(P1–P6) / refund_amount / fulfilled_days / last_churn_signal`。**脱落率、退款率、90 天完成率的唯一来源，也是流失信号误报率评估的 ground truth** | D11a |
| `device_transaction_ref` ＋ | U4 记录 | U10, S7 | 只存订单号引用 | X2 |
| `churn_signal` | **S5**（唯一） | U4, U7（仅 S4/S10） | 相对基线信号须带 `applicable` 标记，基线不足时不得静默判负 | D11a |
| `kpi_settlement` ＋ | **S5/U7** | U7,U10,财务 | **"减药"禁入**；不设产品销售提成 | D11b |
| `remission_clock` ＋ | **U5**（唯一确认） | S3,S2,S8 | 不由系统推断 | D5 |
| `remission_assessment` | **U5**（唯一） | U1,U3,S7,D11b | `in_remission` **不进对外物料接口** | D5 |
| `enrollment_decision` ＋ | **U5**（唯一） | U4,U7,S7 | — | D11a |
| `review_evidence` ＋ | S（自动采集） | U10 质控 | `review_suspicious` 计入抽查池 | D5 |
| `delivery_receipt` ＋ | **S8**（唯一） | S4,S5,U4 | **S7 流失信号的分母** | D16 |
| **`store_readiness_check`** ＋ | **U7**（唯一） | D11a 开通闸 | 未完成清查的门店不予开通服务包 | D6b/D11a |
| **`referral_record` / `clinical_reply_record` / `education_record` / `onsite_triage_record` / `psych_note` / `model_call_log`** ＋ | 各自动作 | U10, S7 | 见 §7.2 的可追溯性缺口 | 多域 |
| **`metric_registry`** ＋ | **U10/U11**（唯一） | 全部看板与合同话术 | `{指标名, 分子, 分母, 排除项, 版本, owner}`。看板与话术**只能引用注册过的指标**——`wear_ratio` vs `wear_days_fulfilled` 同名不同义的根治 | D3/D12 |
| `audit_log` | 全域（只进不出） | U10, 监管 | ≥3 年**下限** + **上限销毁 + 凭证** | D13 |
| `pipia_record` ＋ | **U10**（唯一） | 监管 | 六类触发事件 15 工作日内重评 | D7/D13 |
| `data_subject_request` ＋ | S10/U10 | U10 | PIPL 44–50 | D7 |

---

## 7. 缺口分析

### 7.1 只读不写的实体

| 实体 | 判定 | 处置 |
|---|---|---|
| **G1 用药医嘱/诊断/处方** | **有意的外部依赖，且是红线** | 保持。但 **P1 必须打通读入**；读不到则 D2 长期跑最保守阈值 + `population_params_stale` |
| **G1b SGLT2i 的存在性** | **"最保守阈值"在酮症方向不成立**：没有任何血糖阈值能替代"这个人在用 SGLT2i"这个事实，R12 是纯 `meds` 门控规则，`meds` 为空时恒不触发，而 euDKA 的血糖可以是正常的。P0 下整个 SGLT2i 人群在酮症方向裸奔 | **新增 `med_class_hint`**（患者自报/药盒照片），与 `meds` 严格分离，仅供 S3 开闸。§9.2 的禁令精确化为"不得**生成或修改**用药清单"，而非"不得采集用药信息" |
| **G2 化验值** | 有意，但当前无入口 | 定性：由**医师或护士（U12）**录入，**不由健管师**；D12 加录入项；必须带方法学 |
| **G3 `device_model` 参数（含 MARD）** | 外部依赖，可接受 | 纳入版本管理 |
| **G4 《清查下架确认单》** | **真缺口**。系统内无实体，无法阻止未清查门店开通服务包 | 新增 `store_readiness_check`，接入服务包开通闸 |
| **G5 器械激活回执** | 外部依赖 + 单点风险 | 拿不到则 `sensor_session` 全靠手工录 SN |
| **G6 急性混杂因素** | **真缺口**。`confounded_window` 要读它，无人写它 | 新增 `clinical_context_event` |
| **G7 症状/处置标记** | **真缺口**。R10 的唯一输入、`alert.resolved` 判据的核心 | 告警卡片内一键回填 `symptom_tag` + `treatment_action` |
| **G8 `eGFR`** | **不是普通人群参数**：<45 是二甲双胍减量线、<30 是停用线；肾功能下降者磺脲与胰岛素清除减慢、低血糖风险倍增 | 应为 `health_tier` 与 `alert_threshold` 的**强制输入**；缺失时置 `renal_unknown=true` 并在签发卡片首行提示 |
| **G9 酮体检测结果** | **真缺口**。R11/R12/R24 的输出都是"查血酮"，但系统里没有"阳性"这个输入 | 新增 `ketone_reading`；配发前移到入组并设为 `H` |
| **G10 体测数据** | **真缺口**。40+ 实体里无一承载体重腰围，而 GMI 在 P0 不可用之后，**体重成了 S12 与 9,800 元承诺兑现事实上唯一的量化判据** | 新增 `body_measurement`，含测量协议；承诺兑现只认同设备同协议配对 |

### 7.2 只有副作用、没有持久化的动作

| # | 动作 | 断裂点与后果 | 处置 |
|---|---|---|---|
| B1 | A33 转介用药问题 | 无转介时点与原始问法 → 无法举证"我们确实没答" | `referral_record` |
| B2 | A23 安全认知四条复述 | 无实体 → 患者说"没人告诉我 CGM 慢 15 分钟"时无法举证 | `education_record` |
| B3 | A47 医师群内回复用药 | 这是**诊疗行为**，却不在 `plan_signed` 体系内、无签发留痕 | `clinical_reply_record`，与会话存档双份 |
| B4 | A66/A67/A75 线下合规动作 | 无法逐项审计 | 见 G4；抽检与补签同样需实体 |
| B5 | A80 到店随机指血 | **判定结果**（三档分级与处置）无记录，现场转急诊查不到 | `onsite_triage_record` |
| B6 | A10 患者按 15-15 处置 | 无处置动作记录 → 分不清"补糖回升"与"伪差解除" | 见 G7 |
| B7 | A19 家属到场施救 | 外呼了子女，是否到场无回执 → 未闭环清单说不清 | 外呼回执结构化 |
| B8 | A69 出境判定 | 只在配置层，**每次模型调用是否命中拦截无逐次记录**——P0 主力通道恰是多模态模型，这是最需要举证的一条 | `model_call_log{部署地, 是否出境, 数据类别}` |
| **B9** | **A31 `away_mode` 登记** | **反向缺口**：健管师 KPI 与流失工单量挂钩，她有明确动机把沉默患者标为"外出"。字段无上限、无审批、无监测 → 流失预警在数据上表现良好、现实中失效 | `away_days` 设单次与年度上限（超限需 U7 审批）；监测**按健管师的 `away_mode` 使用率分布**，离群者进质控抽查池 |
| **B10** | **A64 退出与退款** | **全矩阵无退出终态实体**。persona 07 的整篇立论是"CGM 的真实死因是脱落"，产品围绕这个前提设计，却测不出脱落率、退款率、90 天完成率 | `service_exit_record`（见 §6）；看板首指标 = **分阶段留存曲线（第 5/14/30/90/180 天），按 persona 分层** |

### 7.3 只有读没有写的角色

| 角色 | 判定 |
|---|---|
| **U7 店长** | **有意，且必须保持**。他是否决者不是使用者；给他写权限就是给"分层→产品"复活的接口。新增的 `service_exit_record` 与 `store_readiness_check` 是他仅有的两处写入，都是合规/商业性质 |
| **U9 心理咨询师** | 初稿只有一个动作且无写入 → 已补 `psych_note`，否则该角色在系统里等于不存在 |
| **U3 子女/家属** | **真缺口，且有连锁后果**：无账号 = 无埋点主体 = **S5（子女端关通知）与 S11（子女端进入续费页未支付）两个信号不可计算**。而 S11 是红色档、是 P5 费用路径唯一的前置信号，也被 §11 一度列为"P0 可用" | 
| **AI1/AI4/AI5** | **有意**。AI 不得写任何终态实体 |
| **U10 合规官** | 抽检要读群内会话，与最小必要冲突 → 限定为**关键词命中片段**，不是全量会话 |

### 7.4 四条结构性缺口

1. **G-A 回流链在 P0 是主路径，却按异常路径设计。** 每次复核否决都要撤销告警、重算指标、通知签发人。推到 P1 就意味着 P0 长期"数据修好了、错误结论还在患者手里"。
2. **G-B 幂等去重在 P0 完全不生效。** 初稿把自然键改成 `device_time`——而 `device_time` 与 `device_id` 在 schema 里**都是可空的**，可空列进唯一索引则 NULL 之间不冲突。而没有 `device_time` 的恰好是 OCR、手工录入、指血这三条 P0 全部通道。P0 最典型的重复（患者传截图 + 健管师又按口头报数录一遍 + BLE 同步撞车 + 截图时段重叠）一条都拦不住，直接污染均值、TBR 计数与告警去抖。
3. **G-C 三条安全约束在初稿中丢失或写反**：`hypo_prolonged_risk`、`hypo_recurrence_window`、阈值安全方向。矩阵相对上游流程**净削弱**了安全，见 §0.1。
4. **G-D 人工渠道（D6b）是全矩阵唯一没有 `H` 的合规路径。** `D12 → 五师 → 患者` 这条线上 AI3 一个字都管不到；`compliance_incident` 只能事后发现。A36/A37/A47/A33 四个高频动作全走这条线。无法用技术封堵，必须显式承认。

---

## 8. 权限矩阵（角色 × 实体 × 读/写/禁止）

**两级写权限记号**（评审修订，解决 §6"唯一写者"与本节"谁能发起写"的冲突）：
`W!` = 直接写 · `W→S1` = 经 S1 提交（携带操作人身份，S1 落审计并校验）· `R` 可读 · `R*` 仅脱敏/聚合可读 · `—` 无权限 · **`✗` 明令禁止**

| 实体 | U1/U2 | U3 家属 | U4 健管师 | U5 医师 | U13 药师 | U6 营养师 | U8 运动 | U9 心理 | U7 店长 | U10 合规 | U11 运维 | AI1/2/4/5 | AI3 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `glucose_reading` 值字段 | R | R（授权④） | `W→S1` | `W→S1` | — | R | R* | — | **✗** | R*（审计） | **✗ 值字段** | R（结构化） | — |
| `glucose_reading` 元数据（`session_id`/`tz_provenance`/`dedup_key`） | — | — | — | — | — | — | — | — | **✗** | R | `W→S1` | — | — |
| `quality_flag` | — | — | `W→S1` | `W→S1` | — | — | — | — | **✗** | R | `W→S1` | — | — |
| `media_asset` 原图 | R(本人) | — | R（需授权） | R | — | — | — | — | **✗** | R | R | **✗ 原图** | — |
| `cgm_summary` | R | R*（大字卡片） | R | R | — | R | R* | R* | **✗ 个人级**；R* 聚合 | R* | R | R | — |
| `hypo_episode` | R | R | R | R | R | R | R | — | **✗** | R* | — | R | — |
| **`hypo_state`** | — | — | **R only** | R | R | R | — | — | **✗** | R | — | — | — |
| ↳ `closure_blocked_reason` | — | — | **✗** | **✗** | **✗** | **✗** | **✗** | **✗** | **✗** | R | **✗** | **✗** | — |
| `patient_profile.meds` | R | R（授权④） | **✗ W**；R | `W!` | `W!` | R（方案不得含用药） | R | — | **✗ 全部** | R* | — | R（规则参数） | R |
| `med_class_hint` | `W!`（自报） | `W!` | `W!` | R | `W!`（确认→`meds`） | **✗** | **✗** | — | **✗** | R | — | **✗ 除 AI6 采集** | **✗** |
| `patient_profile.health_tier` | — | — | **✗ W**；R | `W!` | — | R | R | — | **✗** | R | — | R | R |
| `patient_profile.tier_label` | **✗**（披露前） | **✗** | R（内部） | `W!`（披露授权） | — | R | — | — | **✗** | R | — | R；**✗ 直推患者** | R |
| `remission_status` | R（经告知） | R | R | `W!` | — | R | — | — | **✗ 用于营销** | R | — | **✗ 主动使用"缓解"** | R |
| `lab_result` | R | R | **✗ W**；R | `W!` | R | R | — | — | **✗** | R* | — | R | — |
| `body_measurement` | R | R | `W!` | R | — | R | R | R | R*（聚合） | R* | — | R | — |
| `ketone_reading` / `symptom_tag` | `W!` | `W!` | `W!` | R | — | R | — | — | **✗** | R* | — | R | — |
| `consent_record` | `W!`(签署/撤回) | R（仅代签家属查看项） | R；**✗ W** | R | — | R | — | — | R*（是否已授权） | `W!` | — | R（开闸条件） | R |
| `alert_event` | R | R（授权④） | `W→S4`(响应) | `W→S4` | R | R | — | — | **✗ 个人级**；R* 响应率 | R* | R | R（AI4 识别） | **✗ 阻断紧急告警** |
| `alert_ack` | — | — | `W!` | `W!` | — | — | — | — | **R*（仅聚合响应率）** | R | — | **✗** | — |
| `alert_escalation` | — | R（被外呼方） | R | R | — | — | — | — | **R*（仅聚合）** | R | — | **✗** | — |
| **`duty_roster`** | — | — | `W!`（排班） | R | — | — | — | — | `W!`（排班） | R | — | **✗** | — |
| ↳ **任一时段留空 → `H` 阻断**：该时段转"无夜间覆盖"并强制告知患者与家属 | | | | | | | | | | | | | |
| **`gateway_device`** 绑定/解绑 | R（在线状态） | R（在线状态） | **`W!`**（现场配发、绑定、回收解绑） | R | — | — | — | — | **`W!`**（资产台账、归还催收；**✗ 绑定患者身份之外的读数字段**） | R（审计） | **`W!`**（远程解绑、故障置换、固件） | **✗** | — |
| ↳ **解绑/离线必产出告知**：`gateway.unbound` / `gateway.offline` → **强制向患者与家属推送夜间覆盖状态变更**（豁免于触达封锁）。解绑**不得静默生效** | | | | | | | | | | | | | |
| ↳ `returned_at` / `asset_status`：U4 `W!`（现场回收）· U7 `W!`（催收结案）· U11 **✗**（运维不碰资产状态） | | | | | | | | | | | | | |
| **`night_coverage`**（派生） | R（**必须可见**） | R（**必须可见**） | R | R | — | R | — | — | R*（覆盖率聚合） | R | R | R（D6a 放行条件） | R |
| `emergency_contact` | `W!` | R（本人条目） | **R only** | R | — | — | — | — | **✗** | R | — | **✗** | — |
| `contact_consent` | — | `W!`（本人确认） | R | R | — | — | — | — | **✗** | R | — | **✗** | — |
| `alert_threshold` | **✗** | **✗** | **✗ W** | **`W!`（唯一可放宽）** | — | — | — | — | **✗** | R | — | **✗** | — |
| ↳ 不变式：**收紧（增加告警量）可自动；放宽（减少告警量）仅医师**。每字段带 `safe_direction` | | | | | | | | | | | | | |
| `plan_draft` | — | — | R | `W!`(改) | — | `W!`(改) | `W!` | — | **✗** | R* | — | **`W!`（仅 AI2）**；**✗ 越过药—方案交互路由** | R |
| **`plan_signed`** | R（推送后） | R | R；**✗ W** | **`W!`** | **✗** | **`W!`**（不含用药） | **`W!`**（双签发） | — | **✗** | R（审计） | — | **✗ 绝对禁写** | R |
| `taper_plan` | R（原文） | R | R；**✗ 改写** | **`W!`** | R | **✗** | — | — | **✗** | R | — | **✗ 摘要/改写/复述药名** | R |
| `compliance_check_log` | — | — | — | R | — | R | — | — | — | R | — | — | **`W!`** |
| `gate_token` | — | — | — | — | — | — | — | — | — | R | — | — | **`W!`（唯一）** |
| `banned_term_library` | — | — | R | R | R | R | — | — | R | **`W!`** | — | R | R |
| `service_package` | R | R | `W!`(履约) | R | — | — | — | — | **`W!`（商务）** | R | — | R | — |
| **`service_exit_record`** | R（本人） | R | **`W!`** | R | — | — | — | — | **`W!`** | R | — | — | — |
| `churn_signal` | **✗** | **✗** | `W!`(处置) | R | — | — | — | — | **R*（仅 S4/S10 服务进度档）** | R* | — | R（AI5） | — |
| `kpi_settlement` | R（本人条款） | R | R* | R | — | — | — | — | **`W!`** | R | — | — | — |
| `remission_assessment` | R（经面诊） | R | R | **`W!`** | — | R | — | — | **✗ 用于物料** | R | — | **✗** | R |
| `psych_note` | **✗** | **✗** | **✗** | R | — | — | — | **`W!`** | **✗** | R* | — | **✗** | — |
| `credential` | — | — | — | R（本人） | R（本人） | R（本人） | R（本人） | R | R（门店级） | **`W!`** | — | — | — |
| `channel_registry` / `device_model` | — | — | R | R | — | — | — | — | R*（能力等级） | R | **`W!`** | R | — |
| `metric_registry` | — | — | R | R | — | R | — | — | R | **`W!`** | **`W!`** | R | — |
| `audit_log` | R（本人，PIPL 44） | — | — | R（本人操作） | R（本人） | R（本人） | — | — | — | **R 全量** | R*（技术日志） | — | — |
| `compliance_incident` | — | — | R（本人被记） | R | R | R | — | — | **R（抄送）** | **`W!`** | — | — | — |
| `context_event` | `W!` | `W!`(代录) | `W!` | R | R | R | R | R | **✗** | R* | — | **`W!`（AI4 抽取）** | — |
| 群内会话原文 | 本人 | — | 参与群 | 参与群 | — | 参与群 | — | — | **✗ 不入患者群** | **R*（仅关键词命中片段）** | — | R（AI4） | — |

### 8.1 三条合规要求的落点

| 要求 | 矩阵落点 | 强制方式 |
|---|---|---|
| **店长不看血糖与用药，只看服务进度** | 店长列：`glucose_reading` / `cgm_summary` 个人级 / `meds` / `alert_event` 个人级 / `context_event` / 群会话 / `psych_note` 全 **✗** | D7 字段级可见性矩阵（D12 只渲染不定义）+ 退出患者群 + 聚合看板替代 |
| **健管师不写任何用药类字段** | 健管师列：`meds` **✗W**、`health_tier` **✗W**、`lab_result` **✗W**、`taper_plan` **✗改写**、`alert_threshold` **✗W** | 表单层不出现该字段 + 后端字段级 ACL + 审计告警 |
| **AI 不得写 `plan_signed`** | AI 列：`plan_signed` / `taper_plan` / `remission_assessment` / `alert_ack` / `duty_roster` 全 **✗** | D5 状态机：`signed` 转移**只接受携带有效 `credential` 的自然人签名** |

### 8.2 最容易被违反的三条

1. **健管师在企微单聊里回答用药问题。** 权限矩阵拦得住她写 `meds`，**拦不住她打字**。而"只读"意味着她**看得见**药名剂量，被患者追问时凭这个回答几乎是必然的。这是全矩阵最容易被违反的一条，且违反时不留任何系统痕迹（除非会话存档关键词命中）——而会话存档本身在 P0 是个**逐患者可拒绝**的同意项。
2. **店长通过健管师间接获知血糖。** 技术上店长看不到；组织上他是健管师的直接上级。退群 + 看板替代解决的是系统可见性，不是组织可见性。
3. **医师"批量全部通过"式签发。** 反橡皮图章约束（无批量按钮、<20 秒标 `review_suspicious`、连续 10 份零修改触发质控）是**唯一**能区分"签发"与"盖章"的机制。它不是权限问题，是权限被行使质量的问题。

---

## 9. 自动化机会

### 9.1 可自动化

| 当前人工动作 | 自动化形态 | 前置条件 |
|---|---|---|
| 健管师听语音抄飞书表 | A94/A94b/A143 摄入管道 | 通道可用（P0 部分兑现） |
| **OCR 复核队列（12–180 条/天）** | **按决策影响分诊，而非提高置信度**（见下） | 见下 |
| 指标计算与 AGP 渲染 | A103/A106 定时任务 | — |
| 静默检测、到期提醒、SLA 计时与升级、限流去抖 | 定时任务 + 状态机 | — |
| ABCD 齐全性检查、体测结构化入档 | 工作台预填卡片（医师 1 分钟确认） | **解开医师这个唯一硬瓶颈** |
| 授权留痕全链路 | 必须自动化 | 否则举证不能 |
| 禁用词/药名实体/功效句式匹配 | AI3 的**确定性规则部分** | **不能只靠 LLM 判断** |
| 复测前 14 天 CGM 启动、年度 HbA1c 排程 | 定时任务 | — |
| `remission_clock` 与用药状态一致性校验 | 状态机 | 依赖 `meds` |
| 撤回级联（含飞书行回收） | 状态机 | — |
| 凭证到期预警与签发权冻结、**值班链尾持续校验** | 定时任务 + 硬门 | 技术简单，价值在不可绕过 |
| **`hypo_state` 状态机与闭环阻断** | 状态机 | 新增，见 §0.1 |

**OCR 复核台的正确前置条件（评审推翻初稿）**：初稿写的是"提高解析置信度"——而这在 P0 不是可控变量（模型能力就那样，截图质量取决于老年患者怎么拍）。真正可控的是**复核什么**：

- **强制复核**（规则确定性、可单测）：① 落在任一告警阈值 ±1.0 带内（<4.9 或 >12.9）② `>33.3` 单位可疑 ③ 跨零点/日期歧义 ④ 与同刻指血差 >20%（`ocr_value_disputed`）⑤ 同图内时间序列非单调或时间戳倒错 ⑥ 整图置信度 <0.7。
- **其余走抽检 + 事后回溯**：随机 5% 人工复核；`ocr_value_disputed` 率超阈值时自动把该批次或该患者全部读数拉回强制复核。
- 一条落在 5.0–9.0 的读数，无论解析对错都不改变任何决策。逐条看图是把复核成本平摊在了 90% 无决策影响的读数上。**分诊后复核量可降至两成，且被砍掉的那部分按定义不影响任何决策。**

### 9.2 因法规或安全**绝对不能**自动化

| 动作 | 依据 | 边界 |
|---|---|---|
| **一切用药决定**（加/减/停/换药、剂量） | 互联网诊疗监管细则 §21 | AI 与健管师**均**不得答。**但禁令的边界是"不得生成或修改用药清单"，不是"不得采集用药信息"**——`med_class_hint` 的采集是信息采集，不是用药指导 |
| **方案签发** | 同上 | `signed` 转移只接受携带有效 `credential` 的自然人签名 |
| **药—方案交互的越权** | 医源性低血糖 / euDKA | `meds ∩ {胰岛素,磺脲} ≠ ∅` 时下调碳水或上调运动量**必须医师签发**；`meds ∋ SGLT2i` 时禁生成极低碳水/生酮结构。**禁令只写"不许说药"，AI 就会绕开药直接动饮食和运动——那是伤害路径，且完全不触碰用药红线** |
| **停药决策与减停计划** | §21 + LADA 误分类 | 系统只承载与提醒，**不生成、不建议、不修改**；提醒不复述药名剂量 |
| **缓解判定的最终结论与告知** | ADA 2021 / 中国共识 | 必须医师面诊；不允许"先告诉患者可能缓解了" |
| **危急兜底的最后一环** | 医疗质量安全核心制度 | 升级链可自动化，**链尾必须是具名自然人**；`duty_roster` 留空即阻断 |
| **`alert.resolved` 解除** | CGM 滞后 5–15 min + MARD 8–10% | 纯 CGM 回升只出 `alert.value_recovered`。**且 `hypo_prolonged_risk=true` 时（磺脲/长效或预混胰岛素），任何回执与任何复测值都不得闭环**——只能转 `monitoring_extended`，24h 后由医师或健管师电话确认才可关闭。这类低血糖可持续 24–72 小时，"吃了 15 g 糖、复测 4.2、闭环"是老年低血糖死亡最经典的路径 |
| **告警阈值放宽** | 安全方向不对称 | **收紧可自动，放宽仅医师**——不是"上调可自动"（高血糖/酮症阈值上调 = 更少告警 = 更危险） |
| **入组与否、分层、目标区间** | CGM 不可诊断 | 可自动化的只有齐全性检查与预填 |
| **紧急告警话术生成** | 词库误命中会吃掉致死告警 | 固定模板 + 预审冻结，不经 LLM、不过运行时闸。**H 级低血糖告警不占令牌桶、不受去抖抑制、可抢占同一接收人的 S 级告警** |
| **社群自动回复（P0–P1）** | 出口无闸门 | 只入不出 |
| **同意书的解释与确认** | PIPL 29 | 需人当面讲清 |
| **"减药"作为任何自动化指标** | 反不正当竞争法 §7 + 临床安全 | **禁入**承诺条款、KPI 公式、结营举证。红线写死在代码 |
| **分层 → 产品组合映射** | 食安法 71/73、广告法 17、R32 | 双向硬阻断 |

### 9.3 五个"看起来能自动化、其实不能"的陷阱

- **自动判定 `away_mode` 并把该时段移出 R01 分母**——工程上自然，临床上是作弊。
- **用 CGM 回升自动闭环告警**——见上表。
- **让 LLM 做合规闸门的最终裁量**——匹配部分必须确定性；LLM 只能做召回，不能做放行。
- **用"OCR 复核通过率"当质量指标**——健管师面对上百条队列时的最优策略是全部点通过，通过率会永远漂亮。真实指标只能是 `ocr_value_disputed`（跨通道一致性率）。
- **把 `source_confidence` 的模型自报分数当作准确率**——0.95 阈值必须用**实测错误率**校准，需要一个人工标注集。

### 9.4 缺失的度量动作（data-analyst）

| 看板 | 必备指标 |
|---|---|
| **数据质量** | `quality_flag` 分布 · 通道占比 · **`ocr_value_disputed` 率（跨通道一致性）** · 复核否决率 · 更正级联触发频次 · **`dedup_hit_rate` 与 `suspected_duplicate_rate`**（截图时段重叠会导致重复计数，且能刷高"入库读数"KPI） |
| **告警安全网** | **误报率（`alert_false_positive_log`）—— 低血糖安全网的存活率指标，比响应时延更重要** · 被抑制告警量（`alert_suppressed_log`） · 响应时延 P50/P90 · 超时率 · 未闭环存量与老化天数 |
| **投递漏斗** | `outbound 尝试 → gate 通过率 → 投递准入通过率 → 送达率 → 打开率`。任一环骤降是先于流失信号的领先指标 |
| **模型质量回归** | **闸门回归集**（200–500 条人工标注含历史违规话术，每次词库/模型变更必跑）→ **漏检率 / 误拦率**双指标。漏检才是合规事故，而现在漏检率永远未知。OCR 同理建标注集 |
| **留存与流失** | **分阶段留存曲线（第 5/14/30/90/180 天），按 persona 分层** · 退款率 · `signal_coverage_rate = 至少 1 个信号可计算的患者比例`，**按 `health_tier` / 年龄分层**（老年组若 <50%，S5 服务对主流人群无效） · 按健管师的 `away_mode` 使用率分布 |
| **工时与容量** | A25/A27/A29 三个动作上埋 `task_duration`（**判断净工时方向的唯一手段**） · 复核队列日增量/存量/滞留时长 + **存量上限告警** · 医师工单量与处理时长**直方图**（不是均值，A47 分布必然长尾） |
| **口径治理** | `metric_registry` + 患者档案上的 `cohort_id` / `rule_version` / `sop_version` 标记——**阈值和 SOP 一改版，前后效果对比全是混杂，改进有没有效永远说不清** |

---

## 10. Skill 映射提示（汇总）

| 形态 | 数量 | 代表能力 |
|---|---|---|
| **`U`** | ~26 | OCR 分诊复核台、签发工作台、老年三分层向导、ABCD 预填卡片、用药录入（医师/药师专属）、告警一键已处理 + 症状回填、阈值放宽（医师专属）、运维台、复盘看板、机构端批量导入、**网关配发与绑定**、**网关离线跟进**、退出归因、数据可携导出 |
| **`A`** | ~34 | 单点抽取、曲线抽取、归一/去重/仲裁/会话/打标、三通道规则引擎、`hypo_state` 状态机、去抖限流与抑制留痕、更正级联、OCR–指血一致性校验、**载体采集与缓存补传**、餐后配对、分析 JSON、方案草稿、意图与危急表述识别 |
| **`S`** | ~17 | 5 分钟拉取、06:00 批算、06:30 飞书同步、09:00 静默检测、每日流失信号、每日数据质量看板、每日值班链尾校验、**每日夜间覆盖真实性校验**、**载体心跳监测**、`vendor_grant` 校验、到期三次提醒、复测前 14 天提醒、年度 HbA1c 排程、季度销毁、月度合规报表、告警时延聚合 |
| **`H`** | **11** | ① D7 同意闸（含会话存档同意项判定）② D6a 出口闸 + `gate_token` ③ D16 投递准入硬拒 ④ D18 签发资质硬门 ⑤ SKU 上架 + `store_readiness_check` 开通闸 ⑥ **离店通道 × 载体联合验证**（现场须看到经载体端到端落库的真实读数）⑦ 告警接收人未配齐阻断佩戴 ⑧ 单位合理性硬阻断 ⑨ 血酮仪配发前置 + C 包准入四条 ⑩ 值班链尾具名持续校验 ⑪ **夜间覆盖真实性闸（前提变更新增）**：载体离线或无 7×24 载体 → 置 `no_realtime_night_coverage`、强制告知、D6a 拦截一切夜间安全承诺 |
| **`—`** | ~15 | 线下器械交易、面诊解读、五师复盘、物料清查、教育复述确认、外呼执行 |

**插件拆分建议**

| 插件 | 覆盖域 | 独立可装 |
|---|---|---|
| **`glycowise-carrier` 载体采集**（新增） | **S11 + D8a 设备侧** | **是——它跑在网关/App 上，不在平台机房**；与平台之间是一段可能整夜断开的链路，必须独立可测、可监控、可降级 |
| `glycowise-ingest` 摄入与质量 | D1 + D8a + D17 | 是（通道可插拔） |
| `glycowise-clinical` 指标与规则引擎 | D2 + D3 + D10 | 是（**三通道，实时与低血糖证据通道独立部署**） |
| `glycowise-safety` 告警与紧急响应 | D4 + D16 投递准入 | 是（**不依赖 D3**） |
| `glycowise-compliance` 闸门与治理 | D6a + D7 + D13 + D18 | 是（必装） |
| `glycowise-workbench` 五师协同 | D12 + D5 + D11a/b + D9 | 否（顶层编排） |

---

## 11. 载体可用性影响分析（主线）+ 降级通道兜底（次线）

### 11.0 约束已经换了位置

原始判断是「厂商无自助 API → P0 全走降级通道 → 数据不充分」。硅基接入商务确认后，这条链上的**第一环解开了，第二环换了**：

```
旧约束：  传感器 ──✗厂商无API✗──▶ 平台
新约束：  传感器 ──蓝牙/SDK──▶ 【载体】──✗谁来7×24跑✗──▶ 平台
                                  ↑
                          企微+小程序无后台常驻
```

**得到了什么**（原始读数 5–15 min 点，`source_channel=ble_cgm_sdk`，conf 1.0）：

| 能力 | 状态 |
|---|---|
| 指标层自建：TIR / TAR / TBR / 平均葡萄糖 / GMI / CV / SD / AGP 分位曲线 | ✅ **成立**，不再是"只能展示厂商算好的汇总"；`metric_provenance=self_computed` |
| R01 数据充分性（14 天 + ≥70%）| ✅ **可真正达标**——`active%` 分子的封闭清单争议（§12.1-1）随之消解，`ble_cgm_sdk` 是无争议的连续监测通道 |
| 报告口径 | ✅ 脱离长期 `trend_only`，可出正式达标结论与 R18 分级映射 |
| GMI 用于缓解判定 | ✅ **成立**（四条前提中的①"100% 来自单一厂商连续通道"由 `ble_cgm_sdk` 满足；②③④仍须逐条校验，MARD 取自 `device_model`）|
| 餐后响应配对（D10 全域）、R19/R20/R21/R26 | ✅ 成立 |
| 32 条规则 R01–R32 | ✅ 可完整落地（**含此前因缺 slope 而失效的 R05/R06/R25**）|
| 实时低血糖告警链路 | ⚠️ **成立，但完全取决于载体** —— 见 §11.1 |

**新约束**：SDK / 蓝牙协议是**设备侧直连**。厂商谈成 ≠ 数据到得了平台。中间多了一个必须 7×24 运行、装在患者家里、不由我方机房托管的**载体**。而当前产品形态（企业微信 + 小程序）**没有后台常驻能力**——小程序必须在前台才能连蓝牙。

### 11.1 夜间 Level 2 低血糖链路的断点分析

这是本节要回答的核心问题。完整链路 11 步，**没有 7×24 载体时，断点在第 2 步**：

```
① 传感器测得 G<3.0（5 min 粒度）          ✅ 传感器一直在测，且本地缓存
       │
       ▼
② 载体经蓝牙接收                      ◀━━━━━ ✗ 断点：人睡着了，小程序不在前台
       │
       ▼
③ 载体上传平台                             （②断则③不存在）
④ S1 摄入 → reading.ingested
⑤ S3 实时通道 R03 判定
⑥ S4 alert.raised → 去抖限流
⑦ S8 投递（企微 / 短信 / 外呼）
⑧ U4 夜班健管师响应
⑨ U5 值班医师二级兜底
⑩ U1 补糖 / U3 家属到场施救
⑪ 复测回升 → alert.resolved
```

#### 静默失效的准确含义

**数据最终会到，告警从未发出。** 患者第二天早上打开小程序，传感器把整夜缓存一次性回填。按 A101 的 `data_age` 分档，这批读数落入"纯历史"档 → **只入指标、不产生任何事件**。于是：

- 14 天报告上的**夜间 TBR 是准确的**，AGP 夜间分位带是完整的，`hypo_episode` 计数是对的；
- 但那一夜的 Level 2 事件，**当时没有任何人知道**。

**这是本矩阵里最危险的一种失败形态**：指标层看起来完美无缺，安全层完全为零，而且从数据上看不出区别。它比"数据缺失"危险得多——数据缺失至少会触发 `data.silent_24h`，而这里数据是齐的。

#### 逐 actor 的静默失效清单（无 7×24 载体时）

| Actor | 动作 | 命运 | 备注 |
|---|---|---|---|
| **X10 网关 / S11 载体采集** | A150/A148 接收与上传 | **❌ 动作不存在** | 断点本身 |
| S11 | A151 心跳监测 | ❌ | 无载体则无心跳可监测 |
| S1 | A99 `trend.computed` | **❌ 实时失效** | 回填数据算斜率无临床意义 → **R05/R06/R25 预测性告警全失效**（对老年人最有价值的一类，症状不典型，到阈值时往往已跌倒）|
| S3 | A108 ①实时通道 R03/R04 | **❌ 静默失效** | 读数被 `data_age` 排除，规则**不报错、不告警、不留痕** |
| S4 | A113/A114 告警产生与推送 | ❌ | 无触发源 |
| S4 | A117b 抑制留痕 | ❌ | 连被抑制的记录都没有 —— **失效不可见** |
| S4 | A115 三级升级链（15/25/35 min） | ❌ | 无触发源 |
| S4 | A116 T+15min 复测自动检查 | ❌ | 同上 |
| S4 | `alert.resolved` / `value_recovered` | ❌ | 无告警可闭环 |
| **U4 健管师** | **A27 夜间告警响应** | **❌ 且组织上不可见** | **值班表照排、人照守夜、一整夜不会响一次。夜班岗位在制度上存在、在功能上为零**——这是最危险的组织性错觉，也是 §7.2 B9 那类"指标好看、业务恶化"的最严重版本 |
| **U5 值班医师** | A46 二级兜底 | ❌ | 同上 |
| **U3 家属** | A19 接外呼、到场施救 | ❌ | 链路终点，也是**唯一能救命的那一步** |
| U1/U2 | A10 按 15-15 处置 | ❌ | 无人叫醒他 |
| U1/U2 | A10b 症状与补糖回填 | ❌ | 连带 R10（低血糖无感知）的输入也没了 |
| S3 | A110b `hypo_state`（HAAF 窗口 / 磺脲不得闭环） | **❌ 实时侧** | 状态机因无实时事件而不开启；**次日回填后可事后补建 `hypo_episode`，但 24h HAAF 收紧窗口已经过去了** |

#### 仍然成立的（无载体时的残余安全网）

| 能力 | 为什么仍成立 | 价值 |
|---|---|---|
| **R08 睡前低值预警** | 21:00–23:00 患者**还醒着**，小程序可前台同步；只需一个睡前读数 + `health_tier` + `meds` | **无载体条件下唯一的夜间低血糖一级预防（事前）**。见 §11.4 |
| **R07 夜间低血糖事件的次日发现** | 回填数据照常进 `hypo_episode` 与 TBR 统计；②低血糖证据通道**免 R01** | 次日 06:30 汇总推健管师；3 天内 ≥2 次 → 医师复核晚间用药。**是事后的，但能驱动 A45 去强化审查——纠正病因** |
| **AI4 危急表述识别** | 不依赖 CGM 数据，依赖群里有人说话 | 事后的、且依赖会话存档同意；老年不典型词（跌倒/叫不醒/胡言乱语/抽搐）直接进 Level 3 |
| 全部汇总与分层能力 | 回填数据是完整的 | 报告、方案、缓解判定不受影响 |

> **一句话**：无载体时失去的是**当夜的干预**，保留的是**次日的纠因**。对一次可能致死的夜间 Level 2，这两者不能互相替代。

### 11.2 五种载体的对照

| 载体 | 7×24 常驻 | 覆盖时段 | 老年零操作 | 端到端延迟 | 新建成本 | 主要失效模式 |
|---|---|---|---|---|---|---|
| **家庭蓝牙网关**（X10） | ✅ 设备级常驻 | **居家 100%，外出 0%** | ✅ **最适合本项目主力人群** | 秒–分钟 | 硬件 + 物流 + **归还与资产管理** | 患者外出即失联；断电/断路由；网关掉线**无人察觉**（须 A151 心跳）；法务定性未决 |
| **原生 App**（新建） | ⚠️ 受 OS 后台限制 | 随身，近全时段 | ❌ 老年安装/授权/保活门槛高 | 秒–分钟 | **新建 App + 上架 + 备案**，产品形态变更 | Android 厂商杀后台；iOS 蓝牙后台需特定 background mode 且审核敏感；老年机型兼容 |
| **穿戴桥接**（X11 华为 WATCH 4） | ✅ 设备侧常驻 | **佩戴时段；夜间摘表则 0** | ⚠️ 需患者本就有华为表 | 分钟 | 中（走 Health Kit） | **夜间摘表 = 夜间无覆盖**，而夜间正是要保的时段；数据颗粒度与回流延迟受 Health Kit 约束 |
| **硅基自家 App 旁路** | ⚠️ 取决于其后台策略 | 其 App 存活时段 | ⚠️ 患者需多装一个 App | 取决于旁路方式 | 低 | **我方不控制**；其 App 被杀即断；旁路取数的授权路径与处理者定性需法务确认 |
| **无载体**（仅小程序前台） | ❌ | 患者主动打开时 | ❌ | **小时级** | 0 | **§11.1 整条夜间链路静默失效** |

**组合策略（建议，待确认）**：网关保居家夜间（覆盖最该保的时段与人群）+ 小程序前台保外出补数 + 指血 BLE 保网关故障期。**穿戴桥接不能作为老年场景的唯一载体**——它在夜间的覆盖率恰好取决于一个我们无法控制的习惯（睡觉戴不戴表）。

**逐载体的能力对照**（相对 §5 各表的 P0 列）：

| 动作/事件 | 网关 | 原生 App | 穿戴桥接 | 硅基 App 旁路 | 无载体 |
|---|---|---|---|---|---|
| A150 载体采集、A148 中继 | ✅ | ✅ | ⚠️ 佩戴时 | ⚠️ | ❌ |
| A99 `trend.computed` → R05/R06/R25 | ✅ | ✅ | ⚠️ | ⚠️ | ❌ |
| A108 ①实时通道 R03/R04 | ✅ 居家 | ✅ | ⚠️ 夜间摘表则失效 | ⚠️ | ❌ |
| A115 三级升级链 · A116 T+15 复测 | ✅ 居家 | ✅ | ⚠️ | ⚠️ | ❌ |
| A110b `hypo_state` 实时侧 | ✅ | ✅ | ⚠️ | ⚠️ | ❌ 仅事后补建 |
| U4 A27 夜间响应 · U5 A46 · U3 A19 | ✅ 居家 | ✅ | ⚠️ | ⚠️ | ❌ |
| **外出时段的实时告警** | **❌** | ✅ | ⚠️ | ⚠️ | ❌ |
| A103–A106 指标与 AGP · R01 达标 | ✅ | ✅ | ✅ | ✅ | ✅ 回填 |
| A92 餐后配对 · R18 分级 · GMI 缓解判定 | ✅ | ✅ | ✅ | ✅ | ✅ 回填 |
| A108b ②低血糖证据通道 → A45 去强化 | ✅ | ✅ | ✅ | ✅ | ✅ 回填 |
| R08 睡前低值预警 | ✅ | ✅ | ✅ | ✅ | ✅ |
| A151 心跳可监测性 | ✅ | ✅ | ⚠️ | ❌ **不可监测** | — |

> 最后一行值得单独看：**硅基 App 旁路的失效是不可观测的**。我们既不控制它的存活，也拿不到它的心跳——只能通过"数据停了"反推，而那与"患者摘了传感器"在数据上没有区别。这条载体不适合承载任何安全承诺。

### 11.3 降级通道兜底（次线，保留不删）

截图 OCR、指血 BLE（GLS 0x1808）、健管师手工录入**不再是主通道，但仍是必需的兜底**，触发场景有四类：

| 场景 | 兜底通道 | 说明 |
|---|---|---|
| **载体故障期**（网关断电/断网、App 被杀、表没戴、等待置换） | 指血 BLE + 小程序前台同步 | 最高频的兜底场景。A39d 网关离线跟进期间，患者必须有可用的测量与上报手段 |
| **患者外出**（网关覆盖为 0） | 小程序前台同步 + 指血 | `away_mode` 期间的唯一数据来源；**照常计入 R01 分母**（§9.3 陷阱一） |
| **厂商中断**（SDK/协议随固件静默失效、合作变更） | 截图 OCR + 指血 + 手工录入 | E54 `sdk_protocol.version_changed` 的应急路径；A79b 回归未通过时全量回落 |
| **患者已在别处买了别家传感器**（跨品牌） | 截图 OCR | 流程一 X5：标 `cross_brand=true`，禁跨期比较结论 |

因此以下能力**不得删除**，且仍受原有全部约束：A06/A82a/A82b 截图与曲线抽取 · A07/A143 指血 BLE · A29 手工录入 · A25 OCR 分诊复核台（§9.1）· A121 OCR–指血一致性校验 · A100 单位合理性硬阻断 · A102 更正级联 · D7a 通道告警资格约束（**OCR/manual 不得独立触发危急告警**，但低值方向仍推患者本人固定模板，§0.1）。

**兜底期的口径变化**：`active%` 分子只计连续监测读数，兜底通道的点不进分子。所以**兜底期越长，R01 越可能不通过** —— 这恰恰是正确的行为：它让"网关坏了三周没人管"这件事在报告口径上显形，而不是被指血数据掩盖过去。`patient_channel_binding.reporting_tier` 应随载体状态动态重算（E51 → E49）。

### 11.4 量化（前提变更后更新）

| 判断 | 量化 | 说明 |
|---|---|---|
| **数据时间覆盖率** | **有载体：接近 288 点/天（100%）**；无载体（7 点指血 + 1–3 张截图）：7–15 点/天 = **2.4–5%，22:00–06:00 ≈ 0%** | 这个对比本身就是载体投资的 ROI 论证，也是写进知情同意书最有力的一句话 |
| **网关的居家覆盖** | 覆盖 = 患者在家的时间比例。老年独居人群通常 >85%，但**需实测**——外出、住院、走亲戚都是缺口，且缺口分布与 `away_mode` 高度重合 | 决定网关方案的实际有效性 |
| **穿戴桥接的夜间覆盖** | = **夜间戴表比例**，需实测。若 <50%，它对本项目最核心的夜间 Level 2 场景无效 | 决定它能否单独作为载体 |
| **告警链路人工可用时段** | 健管师工作时段 9:00–18:00 = **37.5%**。**载体解决的是"数据到不到"，解决不了"夜里有没有人接"**——`duty_roster` 与 `H`⑩ 仍然是独立前提 | 两者缺一，夜间链路都不成立 |
| BLE 指血 7 点/日复合成功率 | 0.9⁷ ≈ **48%**（兜底期口径） | A07 标记维持 ⚠️ |
| **"消灭手抄"的净收益** | 前提变更后**方向转正但仍需验证**：主通道自动入库 → A29 手工录入与 A25 复核量都大幅下降。但 A25 不会归零（兜底期仍有截图），且**新增 A39c/A39d 网关配发与离线跟进的工时**。公式更新为：`净工时/人日 = 原手抄工时 − (复核条数×单条耗时 + 残留手工录入 + 追传催促 + 网关部署与运维工时)` | 仍须在 A25/A27/A29/A39c/A39d 上埋 `task_duration` |
| 老年组流失信号覆盖 | 不变：相对基线信号对老年近乎失明；`signal_coverage_rate` 须按年龄分层。**但新增一个高质量的绝对量信号：`gateway.offline` 时长** | 它对老年组同样有效，且不依赖打卡行为 |
| 容量模型 | 不变：5–15 人/周 × 90 天 ≈ 稳态 65–195 人/店。**新增网关资产维度**：在管人数 = 在外网关数，需台账、置换备品与归还率 | 12 周爬坡表须增列网关列 |

### 11.5 话术边界（前提变更后收紧与放开）

**放开**（原禁令解除）：
- 可以出 TIR / 达标结论 / R18 分级 / AGP —— **但仍受 R01 逐窗口约束，且 `reporting_tier` 是逐患者开关**（兜底期患者仍是 `trend_only`）。
- 可以用 GMI 参与缓解判定 —— **仍须四条前提逐条校验**，任一不满足则 `GMI=null`，不得用近似值填空。
- 可以承诺"自动同步" —— **但只对已配载体的患者，且须说明覆盖边界**（网关 = 居家；穿戴 = 佩戴时）。

**收紧**（新增，全部由 `H`⑪ 与 D6a 逐患者执行）：
1. **夜间监护承诺与载体状态强绑定。** `night_coverage=false` 的患者（无载体 / 网关离线 >N 小时 / 穿戴且夜间未佩戴），一切"夜间有人看着""低血糖会叫醒您"类话术**逐患者拦截**。
2. **网关解绑或离线必须主动告知患者与家属**，豁免于触达封锁。**安全网撤了而患者不知道，比从来没有安全网更危险**——这与 D7 `consent.revoked` 的告知义务是同一条理由（"我以为有人在看"是低血糖伤害的经典成因）。
3. **外出时段不得承诺覆盖**（网关方案）。`away_mode` 期间自动降级话术。
4. **载体覆盖率须进结营举证的口径说明**：一份"TIR 改善 15pp"的报告，若其中三周是兜底通道，必须披露。

**必须写进合同与入组话术的三条**：
- 该患者的载体形态、覆盖时段与**不覆盖的时段**；
- 网关故障时的兜底手段与响应时限（A39d 的 SLA）；
- **载体到位 ≠ 夜间有人接**：夜间响应还取决于 `duty_roster`，两者是独立的两件事。

### 11.6 载体选型未定时，哪些事现在就能做

不依赖载体决策、且不会因选型改变而返工的：D7 授权与出境判定 · D6a/D6b 双层话术闸 · D13 审计 · D18 资质与值班链尾校验 · 摄入层质量工程（去重 G-B 修复、通道仲裁、`quality_flag`、更正级联）· ②低血糖证据通道 + R08 + `hypo_state` · `channel_registry` / `device_model` / `metric_registry` 三张主数据 · OCR 分诊复核台与一致性校验（兜底期长期需要）。

会因选型改变而返工的：S11 载体采集服务的实现形态 · `gateway_device` 资产流程（若不选网关则整块不需要）· 告警 SLA 的对外承诺口径 · 服务包成本模型（网关硬件 + 归还率）· 小程序 vs 原生 App 的产品形态决策。

## 12. 专家评审记录（技能第 7 步）

三位专家以独立子代理身份、基于各自角色定义与原始材料评审了草稿。评审**推翻了初稿的一条核心结论与三条安全设计**（§0.1），并新增 30 个数据实体、5 个动作类别、1 个规则通道、1 个 `H` 闸。以下为逐条处置。

### 12.1 cgm-data-integration-expert（通道现实性与数据可信度）

| # | 意见 | 处置 |
|---|---|---|
| 1 | **§11 的前提把 D1 已定义的 `vendor_export` 与 `aggregator_api` 两条 P0 可用通道静默删掉了**。它们产出真正的连续读数、不需要 BD 谈判。§11 的全部结论都是从这个被写窄的前提推出的——"一个被写窄的前提正在决定产品能不能卖" | **采纳**。曾据此把 §11 改为情形 A/B 双轨并新增 A04b/A39b/A94b。**此后项目前提变更（硅基 SDK 已确认），该争议基本消解**——`ble_cgm_sdk` 是无争议的连续监测通道；这三个动作退为兜底与对账，见 §11.3 |
| 2 | AI6 被建模成"截图 → 单点读数"，但**截图里本来就有曲线**，AGP PDF 有逐日曲线页。这直接推翻三条 ❌ 的理由；且趋势箭头厂商已算好，抽取比回归拟合更可信 | **采纳**。A82 拆为 A82a 单点 / A82b 曲线；曲线读数不进 `active%`、不触发告警，但可进 AGP 与"疑似 `hypo_episode`"；A99 改为"箭头可抽取、斜率不可算" |
| 3 | **`dedup_key` 用了可空字段**。初稿改用 `device_time`，而它与 `device_id` 在 schema 里都可空，可空列进唯一索引则 NULL 之间不冲突 → **P0 三条通道的去重完全失效**，且与两份上游文档不一致 | **采纳（结构性）**。统一回 `time_utc(分钟)`；可空列用哨兵值；新增 A96b 跨通道近似去重；列为 §7.4 G-B |
| 4 | `reading.superseded` 被挂在人工复核上，实际是**自动的通道优先级仲裁**（S1 触发）。贴错标签导致这条逻辑无人实现，而 P0→P1 迁移窗口里它最关键 | **采纳**。新增 A96c 与 E07b，按 `source_confidence` 排序而非硬编码 |
| 5 | **`is_backfill` 在 P0 是最尖锐的规则冲突**：OCR 读数本质上全是回填，D4 硬约束照字面执行则一条告警都发不出；不执行则 14 天 AGP 会把三周前的低血糖当实时推进群。两份文档各自自洽、合起来无解 | **采纳**。二值 `is_backfill` 换为 `data_age` 三档阈值（按通道配置）；§11.2 的"入站背压 ❌"改为 ✅ |
| 6 | §11 把 AI4 危急表述识别标 ✅ 并称"P0 唯一有效安全网"，但它的唯一输入是会话存档——而 §13 自己列着"PIPL 需单独同意、口径未定"，且是**逐患者可拒绝**的 | **采纳**。改为 ⚠️；新增 `no_community_safety_net` 标记与强制告知；§11.3 的结论相应退一步 |
| 7 | 时区基线挂在 `sensor_session` 上，但纯 OCR 患者根本没有 session。**它是患者属性不是传感器属性**——`tz_uncertain` 恒真有一半是建模位置错误造成的 | **采纳**。新增 `patient_time_baseline`（患者级），`clock_offset` 留在 session |
| 8 | **MARD 放错了表**：它是传感器**型号**指标不是通道指标。放在 `channel_registry` 会炸成笛卡尔积或被迫取平均——而 GMI 替代 HbA1c 是本产品法律后果最重的判断 | **采纳**。MARD 迁入 `device_model`；GMI 第四条前提改为"该 session 的 `device_model.MARD` 已登记且 ≤10%" |
| 9 | 缺"**这个患者当前实际走什么通道**"的实体。报告口径、告警承诺、入组话术、KPI 口径全是逐患者的 | **采纳**。新增 `patient_channel_binding` + `reporting_tier`；D6a 拦"达标/TIR"改为逐患者开关 |
| 10 | **§8 权限矩阵与 §6 单写者约束互相打架**（§6 说 S1 唯一写者，§8 给了四个写者）。`quality_flag` 的单写者收敛是这份矩阵为数不多的硬架构成果，就这么被拆掉了 | **采纳**。§8 改用 `W!` / `W→S1` 两级记号；所有人类角色对读数与 `quality_flag` 一律 `W→S1`；并明确复核修正走 **retract + 新增**，不得原地改（否则不可变留存与复核修正必有一条被牺牲） |
| 11 | **校准比对判 ❌ 的理由不成立**。P0 下患者既传截图又做指血，同刻两值是有的；用途从"传感器准不准"变为"OCR 读得对不对"——**P0 唯一的跨通道客观对拍手段** | **采纳**。A121 语义重定义为 OCR–指血一致性校验，产出 `ocr_value_disputed` → 整张原图重解析；作为 §9.4 数据质量看板头号指标 |
| 12 | **OCR 复核台的前置条件写反了方向**。"提高解析置信度"在 P0 不可控；可控的是**复核什么**——落在 5.0–9.0 的读数无论对错都不改变任何决策，逐条看图是把成本平摊在 90% 无决策影响的读数上 | **采纳**。§9.1 改为六条强制复核规则 + 5% 抽检回溯，复核量可降至两成；§9.3 补"不要用复核通过率当质量指标"的陷阱 |

### 12.2 diabetes-cgm-expert（临床安全与规则）

> 专家的总结：**"如果只能改三条：第 2 条（磺脲/长效胰岛素不得闭环 + HAAF 窗口丢失）、第 3 条（低置信低值不推患者）、第 1 条（R09 被 R01 卡死）。这三条都不依赖厂商通道、都在 P0 就能落地，且每一条对应的都是老年患者的直接身体伤害。"**

| # | 意见 | 处置 |
|---|---|---|
| 1 | **R09/R10 被归入受 R01 的汇总通道是错的**。R01 管的是"需要代表性才成立的统计结论"，但**低血糖是存在性证据**。P0 下 R01 恒 false 意味着**全平台永远不会有一次去强化审查被触发**——而那是矩阵里唯一防止老年人被降糖药打低的临床动作 | **采纳（结构性）**。S3 从双通道改为**三通道**，新增**低血糖证据通道**（R09/R10/R07 累积，免 R01）；A45 改挂该通道，P0 标记从 ⚠️ 改 ✅ |
| 2 | **上游的 `hypo_prolonged_risk` 与 `hypo_recurrence_window` 在矩阵里整体消失**，HAAF 只作为一个裸词出现。按矩阵字面，健管师拿到一个 4.2 的指血就能点"已处理"结案——而磺脲/长效胰岛素低血糖可持续 24–72 小时，这是老年低血糖死亡最经典的路径。**矩阵相对上游净削弱了安全约束** | **采纳（推翻初稿）**。新增 `hypo_state` 实体（S3 唯一写者）+ A110b 状态机 + E21b 事件；§9.2 补"任何回执与任何复测值都不得闭环，只能转 `monitoring_extended`"；§8 补该行且 `closure_blocked_reason` **无人可写** |
| 3 | **`conf<0.95` 不进患者侧对低值方向是方向性错误**。低血糖假阳性代价是多吃 15 g 碳水（老年人近零伤害），假阴性代价是昏迷。P0 主力通道置信度天然 <0.95 → **平台看到 2.8 却因置信度不够而不告诉患者本人** | **采纳（推翻初稿）**。按方向拆门限：低值方向无论置信度一律推患者本人固定科普模板；不进的是升级链、TBR 台账、`hypo_episode` |
| 4 | **"上调可自动、下调仅医师"把数值方向等同于安全方向**。高血糖/酮症阈值上调 = 更少告警 = 更危险，而"告警太吵就自动放宽"正是工程直觉最容易做的事 | **采纳（推翻初稿）**。不变式改为"**收紧可自动，放宽仅医师**"；`alert_threshold` 每字段带 `safe_direction` |
| 5 | **限流与去抖没有为低血糖设抢占豁免**。AGP 读图顺序不只是阅片习惯，它是**引擎的优先级契约**，而矩阵只把它落在人工解读上。06:00 批算后一批软提醒会占满令牌桶，Level 2 排在队尾 | **采纳**。明确 H 级低血糖不占桶、不受去抖、可抢占；新增 `alert_suppressed_log`（否则限流是黑洞） |
| 6 | **AI2 缺"药—方案交互"整类约束**。禁令都写"不许说药"，AI 就绕开药直接动饮食和运动——**胰岛素/磺脲剂量不变 + 大幅下调碳水 + 增加运动 = 医源性低血糖**，完全不触碰用药红线。SGLT2i + 极低碳水 = euDKA | **采纳**。AI2 硬约束与 §9.2 各补一条；营养师单签发受同一路由约束；新增 `plan.med_interaction_routed` 事件 |
| 7 | **血酮仪只在流程四配发**，但 R11/R12/R24 对全部患者从第一天生效。没有检测手段的"请查血酮"临床价值为零，且训练患者忽略高级别告警 | **采纳**。配发前移到入组并设为 `H`（`sglt2i`／胰岛素／病程>10y／DKA 史）；新增 `ketone_reading` 实体与 A10c |
| 8 | **"最保守阈值"在酮症方向不成立**。没有任何血糖阈值能替代"这个人在用 SGLT2i"这个事实，euDKA 血糖可以正常。P0 下整个 SGLT2i 人群在酮症方向裸奔。**且这是该自动化却被过度禁掉的一条**——入组时让患者带药盒拍照是信息采集，不是用药指导 | **采纳**。新增 `med_class_hint`（与 `meds` 严格分离，仅供 S3 开闸，永不展示患者/永不进方案）；§9.2 禁令精确化为"不得**生成或修改**用药清单" |
| 9 | 缺 **`symptom_masking_med`（β 阻滞剂）** 标签——它掩盖低血糖交感症状，这类患者**从第一天起就应视为高危无感知**，用"无症状记录 ≥2 次"判 IAH 是错的。**eGFR 也不是普通人群参数**（<45 二甲双胍减量、<30 停用；肾功能下降者磺脲与胰岛素清除减慢） | **采纳**。三标签扩为四标签；R10 触发条件加 `OR symptom_masking_med 存在`；eGFR 升为强制输入，缺失置 `renal_unknown` 并在签发卡片首行提示 |
| 10 | **R08 睡前低值预警在 §11 三分类里完全没出现**，而它是 P0 唯一可执行的夜间低血糖一级预防：只需一个睡前指血 + `health_tier` + 用药，三样 P0 全有。危急表述识别是**事后**的，R08 是**事前**的 | **采纳**。§11.2 ✅ 段落单列；A07 的 7 点 SOP 明确写死 21:00–23:00 睡前点为 `hypo_risk_med` 患者必测点；"睡前吃根黄瓜"入 `banned_term_library` |
| 11 | **R26 在整份矩阵里一次都没出现**——它是 30 条规则里收益/风险比最高的一条（零用药、零合规风险、老年依从性最好）。说明动作表按"告警"和"报告"两条线扫，漏掉了"行为微干预"这一类。R19–R21/R28/R31/R32 也都没写进任何通道 | **采纳**。§1.3 补全通道归属 |
| 12 | **"缓解判定 ✅"与"R33 ❌"并列，是全文最危险的一处组合**。ADA 定义的那 3 个月停药期本身是无药无监测的高风险期，而停药后失代偿的 LADA 患者正是酮症高发人群。单独标 ✅ 会让团队认为 C 包在 P0 可以照卖 | **采纳**。改为"⚠️ 判定可用、过程监测失效"；新增 C 包 P0 准入四条硬闸；R33 给出指血序列降级版 |
| 13 | **§8 完全没有 `duty_roster` / `emergency_contact` / `contact_consent` / `alert_ack` / `alert_escalation` 五行**——三级升级链的全部人身承接点不在权限模型里。谁能把值班人删成空？矩阵没答案 = 默认可改。A24 的 `H` 只是入组一次性检查 | **采纳**。§8 补五行；新增第 10 个 `H`：值班链尾具名**持续**校验（A128b + E38b） |
| 14 | **§8 给 U11 运维在 `glucose_reading` 上写权限，与"S1 唯一写者"冲突且"修复"边界未定义**。非临床角色改血糖值且不走更正级联 = 被静默抹掉的低血糖事件 | **采纳**。U11 权限收窄为**元数据修复**（`session_id`/`tz_provenance`/`dedup_key`），`value_raw`/`unit_raw`/`value_mmol` 一律 ✗ |
| 15 | **R02 没有 reading 级伪差标记，也没规定它必须先于 R03/R04 求值**。夜间压迫伪差 → 凌晨 2 点外呼异地子女 → 患者第二天关掉全部告警。**误报的真正代价不是打扰，是患者从此关闭了唯一的安全网，而这个后果不可见** | **采纳**。明确求值顺序 `R02 → R03/R04 → R05/R06 → 其余`；`artifact_suspected` 写者归 S1；新增 `alert_false_positive_log`，**误报率 = 低血糖安全网的存活率指标** |
| 16 | **缺药师这个 Actor**（§9.2 自己写了"归医师/药师"却没建模）——把低判断量高录入量的工作全压给唯一瓶颈，结果一定是不录或乱录。**缺贴敷部位轮换与皮肤评估**——同部位反复佩戴产生脂肪增生导致读数系统性偏差；而"皮肤主诉"只作为流失信号存在，**被当成了商业信号而不是临床事件** | **采纳**。新增 U13 药师；A23 产出扩展 `wear_site_record`（同部位 <28 天提示）；皮肤主诉同时写入临床侧 |
| 补 | 对 §12.2 原第 6 条的补充：A89 只做"意图分类"不够——识别到老年不典型表述后须**直接进入 Level 3 处置链，且不得要求患者先复测血糖再升级**（对叫不醒的人要求先扎手指等于没有这条规则） | **采纳**，A89 行内注明 |

### 12.3 data-analyst（可测量性与数据质量）

| # | 意见 | 处置 |
|---|---|---|
| 1 | **初稿提的替代 KPI 本身是错的**：分子含健管师手工录入，而 brief 的原话是"替代手工录入"——把手抄搬进工作台表单在这个公式里算达标，**可以靠健管师加班"做出来"** | **采纳**。改为 `患者侧自助通道读数 ÷ 全部入库读数`，并单独报 `manual_entry_share`（目标是随时间下降） |
| 2 | **"人均 60 人"的分母从未定义**：`enrolled_pending_channel`、`away_mode` 中、已过期未换新的患者算不算"在管"？也没定计量单位与快照时点 | **采纳**，§13 |
| 3 | **"只记录不触发跑 2 周"的方法不成立**：(a) 算不出误报率，因为**系统里没有"谁真的脱落了"这个 ground truth**；(b) 2 周短于半数信号的定义窗（S4/S10/S12 在 2 周内不可能产生一个样本） | **采纳**。改为 6–8 周影子运行 + 只对短窗信号回校；ground truth 由新增的 `service_exit_record` 提供 |
| 4 | **brief SC5 与 §9.2 红线正面冲突**："结营举证（TIR 改善、体重、**减药**）"——TIR 在 P0 无正式结论、体重无实体、减药被明令禁止度量。**三分之三不可测**，而它是 9,800 元包的举证基础 | **采纳**。§13 A 段登记"brief SC5 需修订"；建议改为"静脉 HbA1c 变化（配对检验 N≥30）+ 体重变化率 + 佩戴履约天数" |
| 5 | **SC4"所有输出通过合规闸门"分母不可知**：可测的 `compliance_check_log ÷ 系统 outbound` 恒等于 100%，是自证。真实分母含 D6b 人工渠道——而那正是 §8.2 排第一的违规路径 | **采纳**。拆两指标：系统侧报 `gate.blocked 率` 与 override 申请率；人工侧报会话存档抽检违规率，**必须定抽样率、抽样单元与置信区间**（建议每健管师每月 ≥200 条随机消息，报点估计 + 95% CI）。"每月抽检"没有抽样量就不是统计，是安慰 |
| 6 | **全矩阵无退出/退款实体**，A64 在数据追踪表里没有任何行。persona 07 的整篇立论是"真实死因是脱落"，产品围绕这个前提设计，**却测不出脱落率、退款率、90 天完成率** | **采纳**。新增 `service_exit_record` 与 A64 写动作；看板首指标 = 分阶段留存曲线按 persona 分层 |
| 7 | **流失预警对老年患者近乎失明**——S3/S6/S7/S8/S9 全是相对个人基线的变化率，而老年打卡基线近 0，相对变化数学上不可定义。**老年是高危、脱落成本最高、预警覆盖最差的人群；整套挽留机制只对陈先生型有效** | **采纳**。所有相对基线信号加 `applicable` 前置；老年分层单设绝对量信号；新增 `signal_coverage_rate` 按 `health_tier`/年龄分层 |
| 8 | **S5/S11 依赖"子女端"事件，而家属无账号 = 无埋点主体 = 这两个信号当前不可计算**。而 S11 是红色档、是 P5 费用路径唯一前置信号，且被 §11 一度列为"P0 可用" | **采纳**。§7.3 把家属账号从一般缺口升级为 S5/S11 的硬前置；§11.2 修正 |
| 9 | **S7 混淆了"没打开"和"没送达"**：`delivery_receipt` 已存在却没进信号定义。推送失败/被折叠/被 A125 硬拒都会被记成"患者在回避"——**会产生系统性错误干预**（对没收到消息的人打电话说"注意到您最近没看报告"） | **采纳**。S7 分母改为已确认送达；新增投递漏斗看板（`尝试 → gate → 准入 → 送达 → 打开`），任一环骤降是先于流失信号的领先指标 |
| 10 | **A25 的"上百条/天"是三个乐观假设叠出来的**，真实区间 12–180 条/天，跨一个数量级；而 `needs_review_rate` 完全未知。这个数字是 §7.4 G-A、§9.1、净工时三处结论的共同基础 | **采纳**。频率改为区间并标注未知；建议上线前用 50–100 张真实截图离线跑分定 `needs_review_rate`；上线后做成日更指标 + **队列存量上限告警** |
| 11 | **"每周数次"被用作五个动作的频率，等于没有估计；医师负载从未 sizing**。A47 + A49 + A45 + A46 全文没有一处加总过。若 A47 真是 3 次/人/周，医师每周 200–600 条转介——**"五师共管"在人力上是否成立从未被算过** | **采纳**。频率栏加 `[实测]/[目标]/[未估]` 标记；§11.4 补医师负载问题；建议出工单量与处理时长**直方图**（不是均值，A47 分布必然长尾） |
| 12 | **门店入组速率从未换算成稳态在管人数**：5–15/周 × 90 天 ≈ 65–195 人 = 1.1–3.3 名健管师，爬坡期与稳态期复核量差 3 倍 | **采纳**。§11.4 补 12 周爬坡表要求 |
| 13 | **§11.3 与净工时判断自相矛盾**：一处说"消灭手抄是 P0 最大的确定收益"，一处说"净效应方向未定"。而这是全文唯一的正向价值主张，会直接进销售话术 | **采纳**。改为条件式 + 给出公式；**必须在 A25/A27/A29 埋 `task_duration`** |
| 14 | **四处可量化却只做定性**：数据时间覆盖率 2.4–5%（夜间≈0）、健管师时段覆盖 37.5%、BLE 全天完整率 0.9⁷≈48%、结营安全门的代理指标 | **采纳**。§11.4 全部量化；**A07 的 P0 标记从 ✅ 降为 ⚠️** |
| 15 | **体重/腰围/体成分没有实体、没有唯一写者、没有测量口径**，却是承诺兑现的判据。GMI 在 P0 不可用之后，**体重成了 S12 与 9,800 元承诺事实上唯一的量化判据**。5% 阈值下，设备/着衣/空腹的 1–2% 噪声足以翻转结论 | **采纳**。新增 `body_measurement` + A81b；承诺兑现只认同设备同协议配对 |
| 16 | **HbA1c 的方法学未区分**，而 P0 把它抬成了主要客观证据。非 NGSP 认证的 POCT 与实验室法差异可达 0.5%，而缓解阈值是 6.5%——**一个口径问题会直接翻转有合同后果的结论** | **采纳**。新增 `lab_result{method, lab_id, is_ngsp_certified, specimen_type}`；R29 与聚合举证只接受同方法学配对，跨方法标 `evidence_incomparable` |
| 17 | **厂商报告上的 TIR 与平台的 `trend_only` 双口径并存，无任何处置**。P0 主力通道恰是印着厂商 TIR 的 AGP 截图，医师和患者都会看到；D6a 拦得住系统文本，拦不住医师面诊时口头引用 | **采纳**。`vendor_summary_snapshot` 强制携带 `vendor, algo_version, 分母定义`；呈现界面强制标注"非本平台口径、不可与历史比较"；写进 A50 解读脚本与 D6a 例外规则 |
| 18 | **缺三类度量**：模型质量回归对账（闸门**漏检率**永远未知，而漏检才是合规事故）、告警时延聚合（只做到"可追溯"未做到 brief 要的"可测量"）、指标口径主数据化 + `cohort_id`/`rule_version` 标记（**阈值一改版，前后对比全是混杂，改进有没有效永远说不清**） | **采纳**。§9.4 新增完整看板清单；新增 A123b、A133b、`metric_registry` |
| 19 | **`away_mode` 是一个可以被健管师用来抑制自己工单的字段**，且无上限、无审批、无监测。健管师 KPI 与流失工单量挂钩，她有明确动机把沉默患者标为"外出"——**指标好看、业务恶化的经典模式** | **采纳**。§7.2 B9；设单次与年度上限（超限需 U7 审批）+ 按健管师使用率分布做质控 |
| 20 | **截图重叠上传的重复计数无度量**：`device_time` 是 OCR 从图上读出来的，读偏一分钟就二次入库；且**重复上传可以刷高"入库读数"KPI 的分子** | **采纳**（与 §12.1-3 同源）。看板增列 `dedup_hit_rate` 与 `suspected_duplicate_rate`；OCR 通道做"值+近似时间"软去重 |

---

## 13. 待确认（技能第 8 步 Validate 未执行，用户不在线）

### A. 头号问题：**载体选型**（决定产品形态、成本模型与能否做任何夜间安全承诺）

1. **选哪种载体，或哪几种的组合？** 家庭蓝牙网关 / 原生 App / 穿戴桥接 / 硅基 App 旁路。建议组合"网关保居家夜间 + 小程序前台保外出 + 指血保故障期"，但需商业与产品拍板。**这一条不定，§5 各表的 P0 列、告警 SLA 的对外承诺、服务包成本模型、以及要不要新建一个 App，全部悬空。**
2. **法务：中继三类器械数据的家庭网关是否构成"医疗器械附件"？** 若构成，则与 X2「门店不碰货、不收款」的红线冲突，网关须改由持证方配发，整个 `gateway_device` 资产流程的责任主体要换人。
3. **网关的资产与成本模型**：单台成本、备品率、归还率、未归还处置、物流与上门配网的人力。它直接改写服务包成本结构（原成本模型只算了 CGM）。
4. **穿戴桥接的夜间戴表比例**需实测。若 <50%，它不能单独作为老年场景的载体。
5. **硅基 SDK / 蓝牙协议的具体形态**：SDK 支持哪些宿主（Android / iOS / 嵌入式 Linux 网关）？协议是否随固件变更？是否有版本兼容承诺？—— 决定 A79b 的回归成本与 E54 的失效频率。
6. **多模态模型部署地** —— 兜底通道仍走多模态解析，出境判定第一天就要定。
7. `active%` 分子规则是否随之更新为"**采样间隔 ≤15 min 的连续监测读数**"（纳入 `ble_cgm_sdk` 与 `vendor_export`）。前提变更后这条争议基本消解，但**上游两份流程文档的文字仍需同步修订**。

### B. 会改变矩阵结构的

5. 新增实体是否采纳：`hypo_state`、`med_class_hint`、`ketone_reading`、`body_measurement`、`lab_result`（含方法学）、`clinical_context_event`、`symptom_tag`、`service_exit_record`、`patient_channel_binding`（含 `carrier_type` / `night_coverage`）、**`gateway_device`**、`store_readiness_check`、`metric_registry`、`patient_time_baseline`。
5b. **`H`⑪ 夜间覆盖真实性闸的阈值**：网关离线多久算"夜间无覆盖"？建议 4 小时（跨越一个完整睡眠段的一半），需临床确认。
5c. **网关离线跟进（A39d）的 SLA**：谁在什么时限内响应？夜间掉线是否需要立即外呼？——它与 `alert_escalation` 的 SLA 是同一量级的安全承诺，不是运维工单。
6. **U3 家属的正式账号形态**（企微家属身份 vs 小程序账号）——它是 S5/S11 两个流失信号的硬前置，不只是"一个缺口"。
7. **U13 药师是否存在**？若门店无药师，须显式承认由医师兼任并承认瓶颈。
8. **化验值与 eGFR 的录入主体**：X5 HIS 接口 or 医师/护士手工录？**不能是健管师**。
9. **`brief` SC5 需修订**（"减药"与 §9.2 红线冲突，三个指标三分之三不可测）；SC4 需拆为系统侧与人工侧两个指标。

### C. 需要法务/合规拍板的

10. **群内会话存档的关键词监听**（S1/S11 流失信号 + D6b 违规监测 + **AI4 危急表述识别**）涉及对患者对话的自动分析，PIPL 需单独同意，告知口径未定。**它同时是 P0 安全叙事的前提。**
11. **合规官读取会话内容的范围**：全量 vs 仅关键词命中片段（最小必要下应为后者）。
12. **聚合数据的最小样本量与统计口径**（店长 `R*` 与结营举证共用）。N=3 的"聚合"就是个案。
13. **抽检的抽样率、抽样单元与目标置信区间**。

### D. 需要一手数据校准的

14. **`needs_review_rate`**：上线前用 50–100 张真实截图离线跑分。它决定 A25 是 12 还是 180 条/天，进而决定复核台的产品形态与 P0 人力模型。
15. **健管师工时基线**：手抄耗时 vs 复核耗时。**净效应方向未定**，而"消灭手抄"是 P0 唯一的正向价值主张。
16. **医师周负载基线**（A47+A49+A45+A46 加总）——决定"五师共管"在人力上是否成立。
17. **12 周爬坡容量表**（在管人数 / 日复核量 / 日告警量 / 签发量 / FTE）。
18. **BLE 单次同步成功率**——决定 A07 的全天完整率。
19. **S1–S12 阈值**：6–8 周影子运行，只对短窗信号回校；ground truth 靠 `service_exit_record`。
20. **`review_suspicious` 的 20 秒阈值**：前 4 周只采集不判定，建立正常签发时长基线。
21. **`source_confidence` 0.95 阈值**：必须用人工标注集的实测错误率校准，不能沿用模型自报分数。
22. **X2 是否愿给设备激活回执**：拿不到则 `sensor_session` 全靠手工录 SN。

### E. 从上游继承、本环节无法解决的

23. 夜间值班安排（`duty_roster` 链尾具名）——在 P0 它本来就失效，这一矛盾需产品口径拍板。
24. 医师签发 SLA 与超时兜底。
25. 《数据留存与销毁矩阵》——目前只明确 `consent_record ≥3 年`。
26. **R33 反弹判定阈值**需内分泌医师确认后固化进规则库。
