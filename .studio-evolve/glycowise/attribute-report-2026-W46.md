# 归因报告 — glycowise · 窗口 2026-W46（round 5）

输入：`trajectories/2026-W46/audit.jsonl`（69 条：execute 52 / ask 17）+ `feedback.yaml`（status reviewed，reviewer Ameng2001 / 本体负责人，2026-10-23；标签采纳自 `feedback.expert-draft.yaml` 69 条建议：correct 39 / wrong 24 / partial 6）。口语 80 句全部是仿真库变体（original 9 / paraphrase 29 / irrelevant_field 42），优先补 real 池最薄的五个 family。
产出：`cases/real/` 新增 63 条 → 累计 **203 条**（≥ 200，v1 判据前置 (1) 的数量条件首次满足；每层 ≥ 16 仍不满足，见 amend-v2 §1）；`sets/real-all.yaml`（203）、`sets/real-W46.yaml`（63）、`sets/P9-Di.yaml`（5）、`sets/holdout-5.yaml`（40 / 20 层，四窗口，排除 Dᵢ）。提案 P9a / P9b（`studio/changes/glycowise/proposals/P9.md`）。
生产 h_i：clife-glycowise-plugins `feat/glycowise-fde-fill` fcd4191（P2–P8 已合入）。路由 manual（案例自带窗口当时的意图），repeat 3。

## 1. 反馈 → 案例

| 标签 | 条数 | 落案例 | 说明 |
|---|---|---|---|
| correct | 39 | 39 | expect = 引擎实际裁决 |
| wrong | 24 | 24 | expect = truth_expect；layer router 14 / rule 5 / seed 5 |
| partial | 6 | 0 | 无关从句进了患者可见正文 / ReferralRecord.question（0304/0307/0322/0346/0378/0379），只计成本 |

## 2. h_i 基线与 D⁻

h_i 在 203 条 × 3 run：**474/609**（A .778；S_consist = S_stable = 1.0；W_family .90）。W46 的 63 条里 22 条 ×3 稳定失败。

| layer | 条数 | 归因 |
|---|---|---|
| **rule** | 5 | `去重与通道仲裁` 对无序号读数硬拒 R48（art1 ×2、ocr9 ×3）——IR 要求落 weak_dedup 回退。**P9**。其中 0364 的键是字面量 'weak_dedup'，实为路由层 |
| router | 14 | 新型：参数漏填（dedup_key / time_utc）×6；旧型：多挂一跳 ×3（0335/0349 + 0374 部分）、年份 2023 ×1（0348）、枚举「中级」vs「中」×2（0312/0313）、payload 平铺 ×2（0316/0317，IngestBatch record_count=0 仍 committed）、无关从句当过滤值 ×1（0303 lab_id=市一医院）|
| seed | 5 | 40 个 LinkType 声明、seed 0 条边（0336/0340/0374 合法多跳 0 行）；Credential holder 装名字（0381）；tier_label 陈旧（0319）|

路由层累计四窗口 49 条，不归本体（平台 backlog）。seed 层 5 条是演示租户的问题，不归本体也不归路由，留出集里两臂同败。

## 3. 提案与裁决

见 `proposals/P9.md`。两次裁决：
- 第 1 次（commit / 规则名判据）：P9a 与 P9b 八臂几乎同判 ACCEPT，Dᵢ / B_5 / B-sim / real-all 逐行相同——判据读不到落库状态。
- 第 2 次（runner 加 `expect_state`，15 条 dedup 案例补落库真值）：Dᵢ 上 P9a 12/15、P9b **0/15**，判据分开了；但 3d 仍接受 P9b——g_in 的 strict 项被 ΔC −0.8 单独满足（steps 把违规数计入成本，放行永远比拒绝便宜），外关卡 B_5 又有两条同根 x9 案例给 +0.05。八臂只有 1d-strict 拒（ΔA < δ）。`arm_compare` r1–5（attempt 2 的 verdict）：9 条提案 × 8 臂，regress 全 0，1d-strict accept 8/9，random 5/9。
- 第 3 次（criteria amend：strict 只认 T / S / W，ΔC 只做约束；v3 未冻结）：3d 族四臂 **REJECT** P9b（无严格改善），1d 仍 ACCEPT，1d-strict REJECT——**第一个分歧集**（1d 接受 ∧ 3d 拒绝 = P9b）；但 B_5 上 regress = 0，因为 B_5 没有 dup1 案例、留出集对这类写错盲。arms r1–5（attempt 3）：3d accept 8/9、1d 9/9、regress 全 0。

## 4. 方法问题

1. **判据粒度（已修）**：pass 只看 commit / rejected 规则名，看不到「写了什么」。runner 已加 `expect_state`，15 条 dedup 案例补了落库真值；h_i 读数不变，P9b 在 Dᵢ 上从 12/15 跌到 0/15。
1b. **strict 项被成本满足（已 amend，v3 待签字）**：gate-rules §1 的 strict 含 ΔC<0，而 steps 成本把违规规则数算进去，「拒绝改放行」总是更便宜——零增长的朴素修法靠成本过了内关卡。修法预登记进 amend-v2 §5：strict 只认 T / S / W；成本改用不随裁决方向变化的口径。v3 判定式下 3d 拒了 P9b、1d 没拒，分歧集第一次非空；但 regress 判定要看见它，B 里的写类案例也得带 expect_state——否则 regress_rate_diff 仍为 0。
2. **real 池过 200 但分层仍薄（并层口径复核仍未达）**：203 条 / 20 层，最薄层 2 条；按 v3 并层口径（family×tier，<8 并入同 family 其余 tier）复核，8 个 family×rest 层仍不足 8（产品与机构合规 4 / 低血糖安全 5 / 出口签发闸 3 / 参考与配置 7 / 因果链溯源 7 / 指标口径 7 / 缓解路径 2 / 高血糖与波动 4）；make_real_cases 把去重类案例归到「指标口径」family（按口语推断），分层口径本身也要修。
3. 三胞胎案例（同一 sim 案例的 original / paraphrase / irrelevant_field 各落一条 real 案例）不是独立样本，63 条里 23 组。
5. **写类案例落库断言全覆盖**：其余 54 条 correct 写类动作案例（16 个动作）补 `expect_state`，期望只从 IR §4 writes 列 + 路由参数 + 参考数据固定事实推出（时间戳键用 `key_prefix`）；h_i real-all 474 → **471/609**，唯一新失败 数据与同意合规-r02（摄入读数）：路由把单条读数平铺进 `raw_payload`，handler 只读 `raw_payload.readings[]`，一条都没入库、批次计数 0，而 reviewed 标签按 C3 放行判 correct——**commit 判据下的「正确」掩盖了空写入**；IR §4 只写 `raw_payload:object`，golden 路由一律 `readings[]` 形状、该条真实窗口路由平铺——归路由层，登记为发现不在本轮修。B_5 现含带断言的写类案例，下一对提案的 regress_rate_diff 才可能非零。
4. irrelevant_field 变体在路由层的泄漏（patient-facing 正文 ×2、Session 记忆串句 ×3、当过滤值 ×1）：S 维度只在规则层测了扰动一致性，路由层没测。
