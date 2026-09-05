# CGM 数据临床解读标准与算法规则调研（供"健康分析智能体"规则库使用）

调研日期：2026-09-04
调研对象：国际/中国指南、共识、核心论文（均经 WebSearch/WebFetch 核对；未能抓到原文的条目标注【待核实】）
读者：数联天下产品/算法团队；至心医养、德心医养门店医护

> 单位约定：本文以 mmol/L 为主，括注 mg/dL。换算 1 mmol/L = 18 mg/dL。
> 术语：TIR 目标范围内时间；TAR 高于范围时间；TBR 低于范围时间；TITR 严格范围内时间(3.9–7.8)；GMI 葡萄糖管理指标；CV 变异系数；AGP 动态葡萄糖图谱；PPGR 餐后血糖响应。

---

## 0. 一页结论

1. **国际与中国口径基本一致**：核心指标（TIR/TAR/TBR/CV/GMI）和目标值（普通成人 TIR>70%、TBR<4%、TBR<3.0 <1%、CV≤36%；老年/高危 TIR>50%、TBR<1%）来自 ATTD 2019 国际共识，中国 2021 血糖监测指南、2024 老年糖尿病指南、2024 防治指南均直接采纳；中国特色是 CV 阈值有本土证据（>33% 与低血糖风险相关）、老年目标按健康状态三分层给出具体指血阈值。
2. **数据充分性是所有规则的前置门槛**：14 天佩戴 + ≥70% 有效数据，不满足则只做"趋势提示"，不做"结论判定"。
3. **AGP 读图顺序固定**：先看低血糖 → 再看高血糖 → 再看波动。规则引擎的优先级应照此排序，低血糖规则永远抢占。
4. **德心的"糖前期/轻度/中度/中重度"指血分级可以映射到 CGM**，但只能作为"产品方案分层"内部规则，不能对外表述为诊断；CGM 不能用于糖尿病诊断（ADA/CDS 均无此项）。
5. **PPGR 分析可落地**：基线（餐前 30–60 min 均值 / 滚动 4h 均值）、峰值增幅、达峰时间、2h iAUC、2h 回落，已有可复现算法；但"个性化饮食建议改善硬终点"的证据强度为中等偏弱（PREDICT/Zeevi 为预测模型 + 短期 RCT，中国队列仅 60–70 人）。
6. **运动规则的安全阈值国际清晰**（<5.0 补碳水；>13.9 查酮体；酮体阳性禁运动），中国 2024 运动指南全文未能抓取，阈值需产品上线前逐字核对。
7. **"缓解"有硬定义**：停药 ≥3 个月 HbA1c<6.5%（ADA 2021、中国 2021 共识一致），CGM 估算 GMI<6.5% 可作替代。DiRECT 2 年 36%、5 年 13%；Virta 2 年 ITT "逆转" 53.5%，"缓解"仅 17.6%。任何"逆转"宣传都应挂靠这个定义。

---

## 1. 国际标准：ATTD 国际共识（2019）与后续更新

### 1.1 核心指标与目标值

来源：Battelino T, et al. Clinical Targets for CGM Data Interpretation: Recommendations From the International Consensus on Time in Range. *Diabetes Care* 2019;42:1593–1603. [PMC6973648](https://pmc.ncbi.nlm.nih.gov/articles/PMC6973648/)；[Diabetes Care 原文](https://diabetesjournals.org/care/article/42/8/1593/36184/)。ADA、EASD、AACE、ISPAD、JDRF 等背书。

**10 个临床核心指标（Table 2）**：① 佩戴天数；② CGM 有效时间百分比；③ 平均葡萄糖；④ GMI；⑤ 血糖变异 %CV；⑥ TAR Level 2（>13.9 / >250）；⑦ TAR Level 1（10.1–13.9 / 181–250）；⑧ TIR（3.9–10.0 / 70–180）；⑨ TBR Level 1（3.0–3.8 / 54–69）；⑩ TBR Level 2（<3.0 / <54）。

**目标值（Table 3/4，逐字）**：

| 人群 | TIR | TAR L1+L2 | TAR L2 | TBR L1+L2 | TBR L2 | CV |
|---|---|---|---|---|---|---|
| T1D/T2D 成人（非妊娠） | >70%（>16h48m）3.9–10.0 | <25%（<6h）>10.0 | <5%（<1h12m）>13.9 | <4%（<1h）<3.9 | <1%（<15min）<3.0 | ≤36% |
| 老年 / 高危 | >50%（>12h）3.9–10.0 | <50%（含）>10.0 | <10%（<2h24m）>13.9 | <1%（<15min）<3.9 | — | ≤36% |
| 妊娠 T1D | >70% 于 3.5–7.8（63–140） | <25% >7.8 | — | <4% <3.5 | <1% <3.0 | — |
| 妊娠 GDM / T2D | 同样用 3.5–7.8 范围，但共识明确"证据不足，不给出百分比" | | | | | |

**关键换算**："TIR 每提高 10%（≈2.4 h/天）对应 HbA1c 下降约 0.5%"（同文）；每 5% TIR ≈ 1.2 h/天。

**GMI 公式**：GMI(%) = 3.31 + 0.02392 × 平均葡萄糖(mg/dL)；GMI(mmol/mol) = 12.71 + 4.70587 × 平均葡萄糖(mmol/L)。来源：Bergenstal RM, et al. *Diabetes Care* 2018. [PubMed 30224348](https://pubmed.ncbi.nlm.nih.gov/30224348/)。注意 2024 年有文献指出 GMI 与实测 HbA1c 存在系统性差异，提出更新公式 uGMI = 1/(15.36/MG + 0.0425)（[Diabetes Care 2024 评论](https://diabetesjournals.org/care/article/47/6/906/154177/)），产品可同时输出两者但对外只用官方 GMI。

### 1.2 数据充分性

ATTD 2019："recommend 14 days" 佩戴，"recommend 70% of data from 14 days"（[PMC6973648](https://pmc.ncbi.nlm.nih.gov/articles/PMC6973648/)）。ADA 2026 Standards 7.9 要求所有 CGM 提供标准化单页报告（AGP）（[PMC12690173](https://pmc.ncbi.nlm.nih.gov/articles/PMC12690173)）。

### 1.3 AGP 报告标准构成

ATTD 2019 描述标准 AGP 报告 = 全部核心指标与目标条 + 14 天复合葡萄糖曲线（中位数、25–75%、5–95% 带）+ 每日曲线，并将范围命名为 Very High(L2)/High(L1)/Target/Low(L1)/Very Low(L2)。中国 2021 血糖监测指南给出读图顺序：**先识别低血糖，再看高血糖，最后看波动**（[PMC9786627 英文版](https://pmc.ncbi.nlm.nih.gov/articles/PMC9786627/)）。国内另有《动态葡萄糖图谱报告临床应用专家共识（2023版）》【全文未抓取，待核实其"读图步骤"细节】。

### 1.4 TITR（严格范围 3.9–7.8）现状

- 健康人参考：Shah VN 2019（153 名非糖尿病人）中位 TITR 3.9–7.8 = 96%（IQR 93–98），平均葡萄糖 98–99 mg/dL（>60 岁 104），CV 17±3%，>7.8 时间中位 2.1%（30 min/天）。[来源](https://scholarlycommons.henryford.com/endocrinology_articles/66/)
- TITR 目标值：2023 年 Battelino 等临床试验共识把 TITR 列为补充指标；目前建议 >50%（[PMC11965008](https://pmc.ncbi.nlm.nih.gov/articles/PMC11965008/)），另有主张 >70%。ATTD 2025 仍在辩论，**尚未纳入正式临床目标共识**（[Medscape 2025](https://www.medscape.com/viewarticle/should-time-tight-range-be-primary-diabetes-goal-2025a100073q)）。→ 规则库中 TITR 只作"进阶/缓解期"软指标。

---

## 2. 中国标准

### 2.1 《中国血糖监测临床应用指南（2021年版）》（CDS）

中华糖尿病杂志 2021;13(10):936–948；英文版 *Chin Med J* 2022 [PMC9786627](https://pmc.ncbi.nlm.nih.gov/articles/PMC9786627/)。
- TIR 定义：24 h 内葡萄糖在 3.9–10.0 mmol/L 的时间；推荐大多数 T1DM/T2DM TIR>70%、TBR<3.9 <4%、TBR<3.0 <1%。
- 老年/高危、妊娠目标"参照 2019 国际共识"（TIR>50%/TBR<1%；妊娠 3.5–7.8）——指南解读明确列出了这些人群的表（[thepaper 解读](https://m.thepaper.cn/baijiahao_16156936)、[壹生解读](https://cmtopdr.com/post/detail/9457c729-3761-48e1-a638-662ecc83652b)）。
- **中国特色阈值**：指南引用中国人群数据 "CV >33% 与低血糖风险升高相关"（国际为 ≤36%）。
- 数据充分性："至少 14 天有效 CGM 数据"；未写 70%（沿用国际）。
- CGM 适应证：胰岛素强化治疗者；问题性低血糖（频发、夜间、无感知）。
- 明确"GMI 取代 eA1c"。
- 后续：《持续葡萄糖监测临床应用专家共识 2024》（国际内分泌代谢杂志 2024;44(6)，2024-11-20 发布，含门诊/住院/读图 7 类问题）【全文登录墙，具体数值未核实】。

### 2.2 《中国糖尿病防治指南（2024版）》（CDS，2024-12-31 发布）

- 一般成人 T2DM：HbA1c<7.0%，空腹 4.4–7.0 mmol/L，非空腹 <10.0 mmol/L；老年、低血糖高危、预期寿命短、严重并发症者放宽（[丁香园指南页](https://drugs.dxy.cn/pc/clinicalGuidelines/pC7RJoNHj1YANrh50uWaVA==?ky=AC)、[壹生 7 大更新要点](https://www.cmtopdr.com/post/detail/84aba646-718c-416e-bcad-7532fa003818)）。
- TIR：推荐大多数 T1/T2 患者 TIR>70%（同上）。
- 短期胰岛素强化治疗目标：空腹/餐前 4.4–6.0，餐后 2h 4.4–8.0 mmol/L。
- T1DM：HbA1c<7.0%，低血糖高风险者 <7.5%。
- 糖尿病前期（沿用 WHO/CDS）：IFG 6.1–6.9，IGT 餐后 2h 7.8–11.0 mmol/L；糖尿病：空腹 ≥7.0 或 2h ≥11.1（与德心分级的 6.1/7.0/7.8/11.1 边界一致）。
- 对比 ADA 2026：糖前期 FPG 100–125 mg/dL（5.6–6.9）、2h 140–199、A1C 5.7–6.4%（[Guideline Central 摘要](https://www.guidelinecentral.com/guideline/14119/)）。**中美 IFG 下限不同（6.1 vs 5.6）**，规则库用中国口径。

### 2.3 《中国老年糖尿病诊疗指南（2024版）》

英文版 *Aging Med* 2024 [PMC10985780](https://pmc.ncbi.nlm.nih.gov/articles/PMC10985780/)；中文版协和医学杂志 [链接](https://xhyxzz.pumch.cn/article/doi/10.12290/xhyxzz.2024-0347)。

**按健康状态三分层（逐字）**：

| 分层 | HbA1c（不用低血糖风险药） | HbA1c（用低血糖风险药） | 空腹/餐前 mmol/L | 睡前 mmol/L |
|---|---|---|---|---|
| 良好 | <7.5% | 7.0–7.5% | 5.0–7.2（用药 5.0–8.3） | 5.0–8.3 |
| 中等 | <8.0% | 7.5–8.0% | 5.0–8.3 | 5.6–10.0 |
| 差 | <8.5% | 8.0–8.5% | 5.6–10.0 | 8.3–13.9（用药） |

**老年 CGM 目标（逐字）**：TIR 3.9–10.0 >50%（>12h）；TBR<3.9 <1%（<15min）；TAR>13.9 <10%（<144min）；CV ≤36%。
**用药提示**：使用低血糖高风险药物者"HbA1c 不应过低，需设控制下限"；强调"简约治疗""去强化"。
**运动**：每周 5–7 天最好每天；"餐后 1 小时"开始；每餐后约 20 min；餐前运动须先按血糖水平补充碳水；运动前中后加强血糖监测，注意头晕、心悸、乏力、手抖、出汗。

### 2.4 中国 vs 国际差异汇总

| 项目 | 国际（ATTD/ADA） | 中国（CDS 2021/2024） | 规则库采用 |
|---|---|---|---|
| CV 阈值 | ≤36% | ≤36%，但引用 >33% 即低血糖风险升高 | 33% 软提醒、36% 硬阈 |
| IFG 下限 | 5.6 | 6.1 | 6.1（对外）；5.6 内部"关注" |
| 老年分层 | 按并发症/预期寿命笼统 | 三层含具体空腹/睡前指血值 | 采用中国三层表 |
| 数据充分性 | 14 天 + 70% | ≥14 天 | 14 天 + 70% |
| TBR 老年 | <1% | <1% | 一致 |
| 缓解定义 | HbA1c<6.5% 停药≥3 月 | 同 | 一致 |

---

## 3. 德心"高血糖分级"到 CGM 指标的映射

### 3.1 德心原规则（指血）

| 级别 | 空腹 | 餐后 2h | 备注 |
|---|---|---|---|
| 糖前期 | 6.1–7.0 | 7.8–11.1 | |
| 轻度 | 7.0–8.0 | 7.8–11.1 | |
| 中度 | 8.0–10.0 | 11.1–16.7 | 部分并发症 |
| 中重度 | >10 | >16.7 | 多种并发症 |

这套边界的 6.1/7.0/7.8/11.1 与 CDS 诊断切点吻合；8.0/10.0/16.7 为经验分层（16.7 与 CDS "血糖>16.7 不宜运动"的急性并发症阈值相同）。

### 3.2 建议的 CGM 等价映射（可计算）

前提：满足 14 天/70% 数据；**不在急性病/用药调整期**。定义：
- `FG_cgm` = 每日 04:00–07:00（或起床前 1h）窗口中位数，再取 14 天中位数；
- `PP2h_cgm` = 每餐"餐开始 +120 min"点值，取 14 天所有主餐的 75 分位（用 75 分位而非中位数，对齐"餐后峰值管理"的保守取向）；
- 辅助：TAR>10.0、TAR>13.9、TIR、GMI、平均葡萄糖。

| CGM 分层 | FG_cgm | PP2h_cgm | 辅助条件（任一） | 对应德心级别 |
|---|---|---|---|---|
| L0 正常 | <6.1 | <7.8 | TITR>70%，TAR>7.8 <10% | 不入产品分层 |
| L1 糖前期样 | 6.1–6.9 | 7.8–11.0 | GMI 5.7–6.4%；TAR>10.0 <10% | 糖前期 |
| L2 轻度 | 7.0–7.9 | 7.8–11.0 | GMI 6.5–7.0%；TIR ≥70% | 轻度 |
| L3 中度 | 8.0–10.0 | 11.1–16.7 | GMI 7.0–8.5%；TIR 50–70%；TAR>13.9 5–10% | 中度 |
| L4 中重度 | >10.0 | >16.7 | GMI >8.5%；TIR <50%；TAR>13.9 >10% | 中重度 |

分层冲突时取**更严重**一级（与德心"多病共存优先最重"一致）。

### 3.3 临床合理性与局限

支持：
- CGM 平均葡萄糖与 HbA1c 线性相关（GMI 公式基础），且 CGM 能捕捉指血/OGTT 漏掉的异常：Hall 2018 "glucotypes" 中 30 名标准检测"正常"者有 16 名在标准餐后进入糖前期/糖尿病范围；严重波动型中 9/23 未被 FPG/OGTT/HbA1c 诊断（[PLOS Biology](https://journals.plos.org/plosbiology/article?id=10.1371/journal.pbio.2005143)）。
- 健康人 CGM 基线（TITR 96%、>7.8 仅 2%）提供了 L0 边界（Shah 2019）。

局限（必须写入产品免责与医生审核流程）：
1. **CGM 测组织间液葡萄糖，不是血浆葡萄糖**，且有 5–15 min 生理滞后与 MARD ≈ 8–10% 误差；诊断切点（6.1/7.0/7.8/11.1）是基于静脉血浆的，**没有任何指南允许用 CGM 做糖尿病/糖前期诊断**（ADA 2026 第 2 章诊断标准只列 FPG/OGTT/A1C；CDS 同）。
2. 餐后 2h 指血是"某一餐固定时点"，CGM 的 PP2h 是"每餐"，统计口径不同（用 75 分位会系统偏高）。
3. 早晨黎明现象会抬高 FG_cgm；睡前加餐会压低。
4. 德心 8.0/10.0/16.7 边界无外部指南背书，只能定位为"服务分层规则"。
5. 老年人应改用老年三分层目标，不用此表判"轻/中/重"。

→ 输出话术：对外只说"CGM 提示您的血糖处于 X 水平区间，建议由医生结合静脉血/糖化确认"。

---

## 4. 餐后血糖响应（PPGR）分析规则

### 4.1 指标定义与计算（可直接编码）

以下定义综合 Zeevi 2015、Berry 2020、Howard 2022 CGM 效度研究、Levels 公开方法、MAGE 原始定义：

| 指标 | 定义 | 计算 | 来源 |
|---|---|---|---|
| 餐前基线 B | 餐开始前 30–60 min 的 CGM 均值（Levels 用前 1 h 均值；"spike"判定用前 4 h 滚动均值） | mean(G[t0−60, t0]) | [Levels](https://support.levels.com/article/548-understanding-glucose-spikes) |
| 峰值 P / 增幅 ΔP | 餐后 0–180 min 最大值；ΔP = P − B | max(G[t0, t0+180]) | Brand-Miller 2009 GI 曲线形状研究 |
| 达峰时间 Tpeak | argmax 距 t0 的分钟数 | | 同上 |
| 2h iAUC | 以基线为零线的梯形法增量面积（只计正部分或 net 面积需注明） | Σ trapezoid(max(G−B,0)) 0–120 min | Howard 2022 [PMC9170468](https://pmc.ncbi.nlm.nih.gov/articles/PMC9170468/)；Zeevi 2015 |
| 2h 回落 R2h | G(t0+120) − B | | |
| 餐后波动幅度 | 峰谷差（peak − 后续 nadir，0–180 min） | | Brand-Miller "MAGE" 餐后用法 |
| 日 MAGE | 24h 内所有 >1 SD 的升降幅度平均值（Service 1970） | 需算法（EasyGV / 开源整数非线性法）[PMC5863323](https://pmc.ncbi.nlm.nih.gov/articles/PMC5863323/) | |
| "血糖尖峰"事件 | ΔP ≥ 30 mg/dL（1.7 mmol/L）且 P > 109 mg/dL（6.1）（Levels）；或 P >7.8/10.0 按目标范围 | | Levels |
| 上升斜率 | ΔG/Δt，>2 mg/dL/min 视为快速上升（Levels 评分扣分起点） | | Levels |

有效餐次筛选：Howard 2022 只纳入"餐间隔 ≥3–4 h"的餐，避免曲线重叠；建议规则：前一餐/加餐距本餐 <2 h 则本餐 PPGR 标记为"混合，不参与个体化统计"。

### 4.2 PPGR 分级（建议阈值，供产品调参）

| 级别 | ΔP | 2h 回落 | 峰值绝对值 | 动作 |
|---|---|---|---|---|
| 好 | <1.7 mmol/L | 回到 B±0.5 | <7.8 | 记录为"友好餐" |
| 可接受 | 1.7–2.8 | 120 min 内回落 | <10.0 | 无动作 |
| 高响应 | 2.8–4.4 或 Tpeak>90 min | 120 min 未回落 | 10.0–13.9 | 饮食调整建议（顺序/搭配/份量） |
| 极高 | >4.4 | 180 min 未回落 | >13.9 | 触发 TAR L2 规则 + 提交健管师 |

阈值来源：健康人 >7.8 时间仅 2%（Shah 2019）；ATTD 10.0/13.9 分级；1.7/2.8/4.4 为 30/50/80 mg/dL，30 mg/dL 沿用 Levels，50/80 为经验分箱【需用平台数据校准】。

### 4.3 饮食–血糖配对分析方法论要点

- **Zeevi 2015（Cell，800 人，46,898 餐）**：相同餐次个体间差异大；用血液参数、饮食、体型、活动、肠道菌群训练梯度提升模型预测 PPGR；100 人独立验证；盲法 RCT 显示算法饮食显著降低餐后响应（[Cell](https://www.cell.com/fulltext/S0092-8674(15)01481-6)）。
- **PREDICT 1（Berry 2020，Nat Med，1,002 人，14 天，8 种标准餐）**：模型预测血糖 r=0.77、甘油三酯 r=0.47；双胞胎设计显示遗传贡献小（[Nat Med](https://www.nature.com/articles/s41591-020-0934-0)）。
- **CGM 用于餐次排序的效度（Howard 2022）**：同品牌两枚传感器 iAUC0–2h CV 3.7–4.1%、r=0.97、餐次排序 Kendall τ 0.87、误分类 5%；**跨品牌**（Libre vs Dexcom）CV 12.5–16.6%、r=0.56、误分类 19%；**同一人同一标准餐不同日** CV 约 30%。结论：单次 PPGR 不可靠，需重复 ≥2–3 次；跨品牌数据不可直接比较。
- **中国队列**：上海 67 名 T2DM（均龄 61，2,463 次观测，约 13 天），个体化模型预测"下一餐 PPG 是否高于个人均值" F1 均值 75.9%（个体 20–100%），特征为既往 PPG、时段、饮食克数、用药时间（[Sci Rep 2025 / PMC12271334](https://pmc.ncbi.nlm.nih.gov/articles/PMC12271334/)）；另有上海 69 人队列预测"易感性"（medRxiv 2024）。另见 2025 年"CGM 引导个性化饮食改善中国糖前期/T2DM 代谢结局 RCT"（ResearchGate 预印/摘要，[链接](https://www.researchgate.net/publication/401433200)）【全文未核实】。
- **Levels / Zoe 商业方法**：Levels 用 4 h 滚动基线 + 30 mg/dL 尖峰 + 斜率/AUC 扣分；Zoe 用标准餐（松饼/OGTT）校准后给食物评分。两者均未公布硬终点 RCT。

### 4.4 证据强度（GRADE 式自评）

| 主张 | 强度 | 说明 |
|---|---|---|
| 同一食物在不同个体 PPGR 差异大 | 高 | 多队列一致 |
| CGM 能可靠给个人的餐次排序 | 中 | 需同品牌、重复测 |
| 基于 PPGR 的个性化饮食短期降低餐后血糖 | 中 | Zeevi RCT 1 周；PREDICT 后续 ZOE METHOD RCT 公开细节有限 |
| 个性化饮食改善 HbA1c/体重等中期终点 | 低–中 | 中国 RCT 摘要级证据 |
| 改善并发症/硬终点 | 无 | |

→ 产品措辞："帮助您找到更适合自己的吃法"，不得表述为"治疗"。

---

## 5. 低血糖与告警规则

### 5.1 分级（国际低血糖研究组 IHSG，ADA 2026 第 6 章、Endocrine Society 2022 沿用）

- Level 1：<3.9 且 ≥3.0 mmol/L（<70 且 ≥54 mg/dL）——警戒值，无论有无症状均有临床意义。
- Level 2：<3.0 mmol/L（<54）——神经低糖症状阈值，需立即处理。
- Level 3：需他人协助的严重事件（意识/躯体功能改变），不设血糖数值。
来源：[ADA 2026 Sec 6](https://diabetesjournals.org/care/article/49/Supplement_1/S132/163927/)；[Endocrine Society 2022](https://academic.oup.com/jcem/article-abstract/108/3/529/6880627)。

### 5.2 CGM 低血糖"事件"定义

Danne 2017 国际共识及 2023 临床试验共识：<3.9（或 <3.0）**连续 ≥15 min** 计为一次事件；事件结束 = 连续 15 min ≥3.9。（[HypoDE 综述 PMC6610605](https://pmc.ncbi.nlm.nih.gov/articles/PMC6610605/)）。单点 <3.9 不算事件（可能是压迫伪差）。

### 5.3 处理："15–15 法则"

≤3.9 mmol/L：进食 15 g 快速碳水（3–4 片葡萄糖片或 120 ml 含糖饮料）→ 15 min 复测 → 未达标重复；3 轮仍 <3.9 或症状持续 30–45 min 立即就医。ADA 2026 6.15：首选含葡萄糖碳水，避免高脂高蛋白食物；6.16：胰岛素使用者/高危者处方胰高糖素。（[好大夫科普](https://www.haodf.com/neirong/wenzhang/8167341025.html)、[Guideline Central](https://www.guidelinecentral.com/guideline/14119/)）

### 5.4 趋势箭头

- 箭头定义（Dexcom/Libre 通用 7 箭头）：水平 <1 mg/dL/min；斜向 1–2；单竖箭 2–3（Libre：>2）；双竖箭 >3 mg/dL/min（即 30 min 预计变化 >90 mg/dL）。来源：[Dexcom 说明](https://www.dexcom.com/en-us/all-access/dexcom-cgm-explained/trend-arrow-and-treatment-decisions)、Aleppo 2017 [J Endocr Soc](https://academic.oup.com/jes/article/1/12/1445/4642923)。
- Aleppo 2017 成人共识：餐后 2 h 内不据箭头做纠正；下降箭头优先"补碳水预防"而非减胰岛素；箭头调整表仅用于胰岛素使用者。
- 预测性告警：以 "当前值 + 斜率 × 20~30 min" 预测 <3.9 触发"即将低血糖"。

### 5.5 夜间低血糖

- 定义：发生于夜间/睡眠中的低血糖事件（Endocrine Society）。CGM 分析常用固定窗口（临床试验共识使用 00:00–05:59）【原文未抓取，待核实】。
- 德心现行经验"睡前 <5.0 少量加餐（黄瓜/无糖酸奶）"：与老年指南睡前下限（良好组 5.0、中等 5.6、差组 8.3 mmol/L）方向一致，但**加餐种类应改为含 10–15 g 碳水**（黄瓜几乎无碳水，无法预防夜间低血糖）。

### 5.6 老年人群特殊注意

- 目标：TBR<3.9 <1%（老年指南 2024、ADA 2026 6.3c）。
- 用磺脲/胰岛素者设血糖**下限**（老年指南）：良好组空腹不低于 5.0、睡前不低于 5.0。
- 老年低血糖症状不典型（可表现为跌倒、意识模糊），Endocrine Society 2022 强推 CGM 用于低血糖无感知者。
- 触发"去强化"审查：14 天内 ≥1 次 Level 2 事件或 TBR ≥1% → 提示医生复核降糖药。

---

## 6. 运动对血糖的影响规则

### 6.1 运动量与类型（ADA 2026 第 5 章，5.34–5.38）

- 有氧 ≥150 min/周中–高强度，≥3 天/周，不连续 2 天不动；体能好者 75 min/周高强度可替代。
- 抗阻 2–3 次/周，非连续日。
- 久坐每 30 min 打断。
- 老年人加柔韧 + 平衡训练 2–3 次/周。
来源：[Guideline Central 2026 摘要](https://www.guidelinecentral.com/guideline/14119/)。
- 中国老年指南 2024：每周 5–7 天，餐后 1 h 开始，每餐后约 20 min。

### 6.2 有氧 vs 抗阻 对餐后血糖

系统综述（T2DM，Sports Med 2018）：餐后有氧运动使短期血糖 AUC 下降 3.4–26.6%、24h 高血糖发生率降 11.9–65%；抗阻（2 项研究）AUC 降 30%、24h 高血糖降 35%；最稳定获益为 ≥45 min 中等强度有氧（[PubMed 29396781](https://pubmed.ncbi.nlm.nih.gov/29396781/)）。两者长期均有效，抗阻的急性证据较少。

### 6.3 餐后散步时机

- 餐后越早越好：系统综述与 2025 Sci Rep 研究显示"餐后立即 10 min 步行"优于"餐后 30 min 再走 30 min"，因为后者已错过血糖上升期（[Sci Rep 2025](https://www.nature.com/articles/s41598-025-07312-y)；[PMC10036272](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10036272/)）。
- 中国老年指南说"餐后 1 h"——这是保守的安全口径（防餐后低血压/消化不适），产品可折中："餐后 15–30 min 起步、轻–中强度 15–20 min"。

### 6.4 运动前后血糖阈值

| 运动前血糖 | 动作 | 来源 |
|---|---|---|
| <5.0 mmol/L（<90 mg/dL） | 先补 15–30 g 碳水，复测后再运动（胰岛素/磺脲使用者尤其） | Colberg 2016 ADA 立场声明 Table 3【原文 403，数值为广泛引用版本，待逐字核实】；ADA 患者页写 "<100 mg/dL 吃约 15 g 碳水"（[diabetes.org](https://diabetes.org/health-wellness/fitness/exercise-and-type-1)） |
| 5.0–13.9 | 可运动 | 同上 |
| >13.9（250 mg/dL） | 查酮体；酮体中–大量阳性禁运动；无酮体且自觉良好可低–中强度 | Colberg 2016（搜索摘要确认"moderate-to-large ketones 不运动"、"高强度延迟至 <250 mg/dL"） |
| >16.7 mmol/L | 中国 CDS 指南列为"不宜运动"情形之一（伴急性并发症、反复低血糖、波动大同列）【中国 2024 运动指南全文未能抓取，待核实】 | CDS 2020/2024 |
| 运动中 | 每 30 min 关注一次 CGM；<3.9 停止并按 15-15 处理 | ADA 2026 监测建议 |
| 运动后 | 低血糖风险可延续至运动后 24 h（尤其夜间），胰岛素使用者当晚睡前需 >5.6 | Colberg 2016【待核实】 |

用药交互：磺脲/胰岛素使用者运动低血糖风险高；SGLT2i（达格列净）使用者高强度/长时间运动或低碳饮食时警惕**血糖不高的酮症**，应查血酮而非只看血糖（德心患者用药清单含达格列净，须建规则）。

---

## 7. "糖尿病缓解/逆转"定义与证据

### 7.1 定义

- **ADA 2021 国际共识**（Riddle MC 等，Diabetes Care 2021;44:2438；同期发表于 JCEM/Diabetologia/Diabet Med）：停用降糖药 **≥3 个月** 后 HbA1c <6.5%（48 mmol/mol）；HbA1c 不可靠时用 FPG <7.0 mmol/L 或 **CGM 估算 HbA1c(GMI) <6.5%** 替代；不再用"部分/完全缓解""治愈""逆转"等词；缓解后至少每年复查 HbA1c。（[Diabetes Care](https://diabetesjournals.org/care/article/44/10/2438/138556/)、[ADA 新闻稿](https://diabetes.org/newsroom/international-experts-outline-diabetes-remission-diagnosis-criteria)）
- **《缓解2型糖尿病中国专家共识》（2021，邹大进/张征/纪立农，中国全科医学/中国糖尿病杂志）**：定义同 ADA（停药 ≥3 月 HbA1c<6.5%；替代 FPG<7.0 或 CGM 估算 HbA1c<6.5%）；**ABCD 评估适合人群**：A 抗体阴性（GADA 等）；B BMI ≥25 或腰围男>90/女>85 cm；C 空腹 C 肽 ≥1.1 ng/ml、餐后 2h C 肽 ≥2.5 ng/ml；D 病程 ≤5 年。干预路径：限能量平衡饮食/极低热量/生酮饮食；奥利司他 BMI≥27 用 12–24 周；GLP-1RA 等联合 8–12 周；HbA1c≥10% 或 FPG≥11.1 先 2 周胰岛素强化；BMI≥32.5 可代谢手术。（[chinagp](https://www.chinagp.net/CN/10.12114/j.issn.1007-9572.2021.01.105)、[壹生解读](https://www.cmtopdr.com/post/detail/988cd768-dc47-4cbf-a944-803fb40854c2)）

### 7.2 证据

| 研究 | 干预 | 结果 | 来源 |
|---|---|---|---|
| DiRECT（英国基层，n=298） | 825–853 kcal/d 代餐 12–20 周 + 逐步复食 + 维持 | 1 年缓解 46%；**2 年 36%**，减重 ≥10 kg 者 81% 缓解；平均减重 7.6 kg | [Lancet D&E 2019](https://www.thelancet.com/journals/landia/article/PIIS2213-8587(19)30068-3/abstract) |
| DiRECT 5 年延伸 | 继续低强度支持 | 5 年 85 人中 13% 缓解；2 年时缓解者 26% 仍缓解；平均减重 6.1 kg | [Lancet D&E 2024](https://www.thelancet.com/journals/landia/article/PIIS2213-8587(23)00385-6/fulltext) |
| Virta（美国，远程持续照护 + 营养性酮症，n=262，非随机） | 极低碳水 + 远程医生/教练 | 2 年保留率 74%；HbA1c −0.9%；减重 −11.94 kg；**"逆转"(HbA1c<6.5% 仅二甲双胍) ITT 53.5%、完成者 37.8%；"缓解" ITT 17.6%、完全缓解 6.7%**；胰岛素剂量 −81% | [Front Endocrinol 2019](https://www.frontiersin.org/journals/endocrinology/articles/10.3389/fendo.2019.00348/full) |
| Virta 5 年 | 同 | 122 人完成；缓解 20%，逆转 32.5% | [DRCP 2024](https://www.sciencedirect.com/science/article/pii/S0168822724008088) |

启示：
1. "逆转"在 Virta 定义里**允许保留二甲双胍**，与 ADA/中国"缓解"定义不同，两者数字不可混用；门店宣传若用"逆转率"必须注明定义。
2. 缓解与减重幅度强相关（DiRECT ≥10 kg → 81%），产品应以体重轨迹为核心中间指标。
3. 5 年持续缓解率低（13–20%），服务包应设计为"缓解 + 维持"两阶段，并每年复查 HbA1c。
4. MNT 固体饮料（英纽林）无任何缓解证据，规则库中不得把产品推荐与"缓解"结论挂钩（见简报合规风险）。

---

## 8. 规则候选表（30 条）

严重级别：**H 硬阻断**（智能体必须输出并升级人工，且阻止其他推荐）/ **S 软提醒**（生成建议、可被覆盖）/ **G 门槛**（不满足则降级输出）。
公式变量：G(t) 当前值；slope（mg/dL/min，取最近 15 min 线性拟合）；窗口默认 14 天；`active%` 有效数据比；`age`, `health_tier`（老年三层）, `meds` 用药集合。

> ### ⚠ 修订说明（2026-09-05，本体建模复核）
>
> **1. R03/R04 原文把实时触发与回顾统计并成一条**（"持续 ≥15 min（或 2 个连续读数）"），这是 C-01 错误的源头。已拆为四条独立规则：
> - **R03a / R04a 实时告警**：连续 2 个读数即触发 + 预测性告警（斜率外推）。目标是在跌破阈值**之前**报出。
> - **R03b / R04b 回顾性事件统计**：低于阈值**持续 ≥15 min**（Danne 2017 口径），用于事后统计事件次数与 TBR，**防压迫伪差**。
>
> 两者**必须物理分开实现**，四个独立函数签名。共用一个"低血糖检测"函数靠传参区分，等于把这个错误写回代码。
>
> **2. R19 的 `R2h≥1.7` 待核**：1.7 是 §4.2 中 ΔP 的分界值，被挪用到 R2h（2h 回落 = G(t0+120) − B）上，无独立依据。上线前须由临床确认 R2h 的正确切点，不得沿用。
>
> **3. 本表缺三条临床上必须有的规则**（本体建模复核补建）：15-15 法则三轮无效强制升级就医、Level 3 不看血糖数值强制转诊、老年跌倒/意识模糊联动疑似低血糖。见 `studio/changes/glycowise/ontology-map.md`。

| # | 规则名 | 触发条件（可计算） | 输出动作 | 级别 | 依据 |
|---|---|---|---|---|---|
| R01 | 数据充分性门槛 | `days<14 OR active%<70` | 仅输出趋势描述，禁止输出分层/达标结论；提示补足佩戴 | G | ATTD 2019；CDS 2021 |
| R02 | 传感器异常/压迫伪差 | 单点 <3.0 但前后 10 min 内回升 ≥1.5 mmol/L；或 15 min 内跳变 >5 mmol/L | 标记可疑，建议指血复核，不计入事件 | S | Danne 2017 事件定义（≥15 min）|
| R03a | Level 2 低血糖**实时告警** | `G<3.0` 连续 2 个读数（+ 斜率外推预测性告警） | 立即推送患者+健管师+群：15 g 碳水，15 min 复测；老年/独居加电话 | H | IHSG；ADA 2026 6.15 |
| R04a | Level 1 低血糖**实时告警** | `3.0≤G<3.9` 连续 2 个读数 | 推送：15 g 碳水，15 min 复测 | H | 同上；15-15 法则 |
| R05 | 即将低血糖预测 | `G<5.0 AND slope≤−1` 或 `G + slope×20 < 3.9` | 提前提示补 10–15 g 碳水；暂停运动 | H | Aleppo 2017；箭头定义 |
| R06 | 快速下降箭头 | `slope ≤ −2`（单/双下箭）且 G<7.0 | 提示 15 min 后复看，不进食大量碳水以免反跳 | S | Aleppo 2017 |
| R07 | 夜间低血糖事件 | 00:00–06:00 内 <3.9 ≥15 min | 次日晨推送健管师；三天内 ≥2 次 → 医生复核晚间用药/晚餐 | H | Endocrine Society 2022；老年指南 |
| R08 | 睡前低值预警 | 睡前窗口(21:00–23:00) 均值 < 下限（老年良好 5.0 / 中等 5.6 / 差 8.3；非老年 5.0）且 `meds ∩ {胰岛素,磺脲}≠∅` | 建议 10–15 g 含碳水加餐（非黄瓜）；复测 | S | 老年指南 2024；德心经验（修正） |
| R09 | 14 天 TBR 超标 | `TBR<3.9 ≥4%`（老年/高危 ≥1%）或 `TBR<3.0 ≥1%` | 报告首行标红"低血糖优先"；提交医生审查降糖药（去强化） | H | ATTD 2019；老年指南 |
| R10 | 低血糖无感知线索 | Level 2 事件时无患者手动标记/无症状记录 ≥2 次/14 天 | 提示医生评估 IAH；建议开启 CGM 低值告警 3.9→4.4 | S | Endocrine Society 2022 |
| R11 | 严重高血糖 | `G>16.7` 持续 ≥1 h，或 `G>13.9` 且患者报口渴/多尿/恶心 | 提示查血酮；有酮体或症状 → 就医；暂停运动与产品推荐 | H | CDS 不宜运动阈值；Colberg 2016 |
| R12 | SGLT2i 酮症警觉 | `meds ∋ SGLT2i` 且（极低碳水饮食标记 OR 长时间运动 OR 恶心/乏力）且 G 不高 | 提示查血酮（血糖正常也可能酮症） | H | 药物机制；产品简报含达格列净 |
| R13 | TAR L2 超标 | `TAR>13.9 ≥5%`（老年 ≥10%） | 报告标注；生成"哪些时段/餐次贡献最多"分析交医生 | S | ATTD 2019 |
| R14 | TAR L1 超标 | `TAR>10.0 ≥25%` | 饮食/运动/服药时机建议 | S | ATTD 2019 |
| R15 | TIR 未达标 | `TIR<70%`（老年/高危 <50%） | 达标差距换算成小时（每 5%≈1.2h）；建议复诊 | S | ATTD 2019；CDS 2024 |
| R16 | 血糖波动大 | `CV>36%`（H）或 `33%<CV≤36%`（S） | 提示波动源于低血糖或餐后，联动 R09/R19 | H/S | ATTD 2019；CDS 2021（中国 33%） |
| R17 | GMI 与 HbA1c 不一致 | `|GMI−HbA1c|≥0.5%` | 提示以实测 HbA1c 为准；标注可能贫血/血红蛋白变异 | S | Bergenstal 2018；Diabetes Care 2024 |
| R18 | CGM 分层（德心映射） | 按 §3.2 表计算 L0–L4（需 R01 通过、非老年） | 输出"服务分层"供方案规划智能体；对外措辞"提示区间，需医生确认" | S | §3；CDS 诊断切点 |
| R19 | 餐后高响应 | 单餐 `ΔP≥2.8 mmol/L OR P≥10.0 OR R2h≥1.7` ⚠**待核** | 记录该餐；同类餐 ≥2 次触发饮食建议（顺序、份量、搭配、餐后步行） | S | §4.2；Howard 2022 重复性 |
| R20 | 餐后极高响应 | `ΔP≥4.4 OR P≥13.9` | 联动 R13；推送健管师 | S | ATTD 分级 |
| R21 | 餐次数据混叠 | 与上一餐/加餐间隔 <2 h | 该餐不计入个人食物排序 | G | Howard 2022 |
| R22 | 黎明现象 | 03:00 最低值到 07:00 上升 ≥1.1 mmol/L 且无夜间加餐，14 天 ≥50% 天数 | 提示医生（基础胰岛素/晚餐调整） | S | 临床常规定义 |
| R23 | 运动前低值 | 运动打卡/加速度计触发前 `G<5.0` | 先补 15–30 g 碳水，复测 ≥5.0 再动 | H | Colberg 2016；ADA 患者指导 |
| R24 | 运动前高值 | `G>13.9` | 查酮体；阳性禁运动；阴性仅低–中强度 | H | Colberg 2016 |
| R25 | 运动中下降 | 运动期间 `slope≤−1.5` 或 G<4.4 | 提示停止并补碳水 | H | ADA 2026 监测建议 |
| R26 | 餐后步行提醒 | 餐开始后 15–30 min 且 `slope>1` | 推送"走 10–20 min" | S | Sci Rep 2025；Sports Med 2018 |
| R27 | 运动后延迟低血糖 | 当日 ≥45 min 运动且 `meds ∩ {胰岛素,磺脲}≠∅` | 当晚睡前目标 >5.6，夜间告警阈值上调至 4.4 | S | Colberg 2016【待核实】 |
| R28 | 老年目标切换 | `age≥65` | 全部阈值切换到老年三层表；TIR>50%、TBR<1%、TAR>13.9<10% | G | 老年指南 2024 |
| R29 | 缓解判定 | 停用降糖药 ≥90 天 且 (HbA1c<6.5% 或 GMI<6.5% 且 R01 通过) | 标记"缓解"，安排每年 HbA1c；否则禁止使用"缓解/逆转"字样 | H | ADA 2021；中国共识 2021 |
| R30 | 缓解适宜人群筛选 | ABCD：抗体阴性 AND (BMI≥25 或腰围男>90/女>85) AND 空腹 C 肽≥1.1 ng/ml AND 病程≤5 年 | 输出"可进入缓解路径"，转医生评估 | S | 中国共识 2021 |
| R31 | 妊娠模式 | `pregnant=true` | 目标范围切换 3.5–7.8；TIR>70%、TBR<4%；禁用德心分层与 MNT 推荐 | G/H | ATTD 2019 |
| R32 | 产品推荐合规闸 | 任何 MNT 产品推荐输出 | 不得与 R18 分层"诊断化"、R29"缓解"字样同句出现；附"固体饮料，不替代药物" | H | 简报合规提示；广告法 |

---

## 9. 待核实清单（上线前必须补）

1. 《中国2型糖尿病运动治疗指南（2024版）》76 条推荐中的运动前血糖阈值、"餐后 1 h"表述、CGM 运动应用条目（中华糖尿病杂志 2024;16(6):616–647）。
2. Colberg 2016 Table 3 逐字（<90 mg/dL 补 15–30 g；250–350 查酮体；>350 禁高强度）。
3. Riddell 2017 T1D 运动共识分层（<90、90–124、126–180、182–270、>270 mg/dL）。
4. Battelino 2023 临床试验共识中夜间窗口（疑为 00:00–05:59）与 TITR 表述。
5. 《持续葡萄糖监测临床应用专家共识 2024》《动态葡萄糖图谱报告临床应用专家共识 2023》全文中的读图步骤与是否更新目标值。
6. IDF 2024 1h-PG 立场（≥8.6 mmol/L 中间高血糖、≥11.6 糖尿病）——可作为 CGM "1 h 峰值"参考切点。
7. 中国 CGM 引导个性化饮食 RCT（2025）全文与终点。

## 10. 主要来源清单

- ATTD 2019 国际共识：https://pmc.ncbi.nlm.nih.gov/articles/PMC6973648/
- Battelino 2023 临床试验 CGM 共识（Lancet D&E）：https://pubmed.ncbi.nlm.nih.gov/36493795/
- TITR 综述：https://pmc.ncbi.nlm.nih.gov/articles/PMC11965008/ ；ATTD 2025 辩论：https://www.medscape.com/viewarticle/should-time-tight-range-be-primary-diabetes-goal-2025a100073q
- GMI：https://pubmed.ncbi.nlm.nih.gov/30224348/ ；https://diabetesjournals.org/care/article/47/6/906/154177/
- 健康人 CGM（Shah 2019）：https://scholarlycommons.henryford.com/endocrinology_articles/66/
- Glucotypes（Hall 2018）：https://journals.plos.org/plosbiology/article?id=10.1371/journal.pbio.2005143
- ADA 2026 Standards 摘要：https://www.guidelinecentral.com/guideline/14119/ ；第 6 章：https://diabetesjournals.org/care/article/49/Supplement_1/S132/163927/ ；第 7 章：https://pmc.ncbi.nlm.nih.gov/articles/PMC12690173
- 中国血糖监测指南 2021（英文版 2022）：https://pmc.ncbi.nlm.nih.gov/articles/PMC9786627/
- 中国糖尿病防治指南 2024：https://drugs.dxy.cn/pc/clinicalGuidelines/pC7RJoNHj1YANrh50uWaVA==?ky=AC ；解读：https://www.cmtopdr.com/post/detail/84aba646-718c-416e-bcad-7532fa003818
- 中国老年糖尿病诊疗指南 2024：https://pmc.ncbi.nlm.nih.gov/articles/PMC10985780/
- 中国 2 型糖尿病运动治疗指南 2024：https://www.chinagp.net/CN/10.12114/j.issn.1007-9572.2024.A0019
- 持续葡萄糖监测临床应用专家共识 2024：https://drugs.dxy.cn/pc/clinicalGuidelines/puq8pxE5XYXQNmvGRUVg_2A
- Endocrine Society 2022 低血糖指南：https://academic.oup.com/jcem/article-abstract/108/3/529/6880627
- CGM 低血糖事件定义：https://pmc.ncbi.nlm.nih.gov/articles/PMC6610605/
- 趋势箭头（Aleppo 2017）：https://academic.oup.com/jes/article/1/12/1445/4642923 ；Dexcom：https://www.dexcom.com/en-us/all-access/dexcom-cgm-explained/trend-arrow-and-treatment-decisions
- Colberg 2016 ADA 运动立场：https://diabetesjournals.org/care/article/39/11/2065/37249/
- 餐后运动综述：https://pubmed.ncbi.nlm.nih.gov/29396781/ ；https://www.nature.com/articles/s41598-025-07312-y ；https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10036272/
- Zeevi 2015：https://www.cell.com/fulltext/S0092-8674(15)01481-6 ；Berry 2020：https://www.nature.com/articles/s41591-020-0934-0 ；Howard 2022 CGM 效度：https://pmc.ncbi.nlm.nih.gov/articles/PMC9170468/ ；中国 T2DM PPG 预测：https://pmc.ncbi.nlm.nih.gov/articles/PMC12271334/
- Levels 方法：https://support.levels.com/article/548-understanding-glucose-spikes
- MAGE 算法：https://pmc.ncbi.nlm.nih.gov/articles/PMC5863323/
- ADA 2021 缓解共识：https://diabetesjournals.org/care/article/44/10/2438/138556/ ；中国缓解共识 2021：https://www.chinagp.net/CN/10.12114/j.issn.1007-9572.2021.01.105 ；解读：https://www.cmtopdr.com/post/detail/988cd768-dc47-4cbf-a944-803fb40854c2
- DiRECT 2 年：https://www.thelancet.com/journals/landia/article/PIIS2213-8587(19)30068-3/abstract ；5 年：https://www.thelancet.com/journals/landia/article/PIIS2213-8587(23)00385-6/fulltext
- Virta 2 年：https://www.frontiersin.org/journals/endocrinology/articles/10.3389/fendo.2019.00348/full ；5 年：https://www.sciencedirect.com/science/article/pii/S0168822724008088
