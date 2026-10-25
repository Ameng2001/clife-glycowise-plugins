# 任务说明：W54 与 W54b 窗口的轨迹标注（86 + 16 = 102 条）

## 背景

W54 是正式实验最后一轮（round 11）的窗口，写法沿用 W53（规则边界上的请求），另有 8 句定向说法和 36 句补案例池的句子。口语已在生产 h₁₁（glycowise ae0e174）上经真实大模型路由进引擎执行。请业务侧逐条判定**引擎的裁决对不对**，按业务真值标。

规矩与 W53 相同：业务侧标注，reviewer 由本体负责人或医师 / 合规官担任；数据组只整理文件。

## 要标的文件

| 文件 | 条数 | 说明 |
|---|---|---|
| `examples/trajectories/2026-W54/feedback.yaml` | 86（查询 16、执行 70） | 正式实验最后一轮的窗口 |
| `examples/trajectories/2026-W54b/feedback.yaml` | 16（执行 16） | W54 的续补，只补指标口径与缓解路径两类案例 |

两个文件现在都是 `status: draft`。各自标完把 `status` 改成 `reviewed`，填好文件头 `reviewer` 与 `labeled_at`。

## 每条怎么填

| 字段 | 填什么 |
|---|---|
| `label` | `correct` / `partial` / `wrong` |
| `truth` | 一句话：业务上应有的结果，或引擎错在哪里 |
| `truth_expect` | 只有 `wrong` 必填：`query`、`action(动作名)`、`rejected(规则名)` 三选一 |
| `layer` | 只有 `wrong` 填：`rule` / `router` / `seed` |
| `reviewer` | 如 `{id: xxx, role: 医师}` |

- **correct**：裁决就是业务应有的裁决。查询查到对的数据；该直接办的办了且参数对；该起草等人确认的进了人审（pending_hil）；该拦的被对的规则拦了。
- **wrong**：方向错。该拦没拦、不该拦被拦、拦错规则、动作选错、参数对不上口语、该查到的查成 0 行。
- **partial**：方向对、细节有瑕疵但不改变裁决。partial 不落案例，**拿不准时倾向 wrong**。

## 两条要求

1. **wrong 写清落库**：`truth_expect` 是 `action(动作名)` 时，在 `truth` 里写清应写到哪个对象、哪个字段、什么值，例如「应写 AlertThreshold，field = night_low，current_value = 4.3」。只写动作名，回放时会被判成「通过」。
2. **拿不准的条目照样给标签，并在 `note` 里写「待确认：倾向 X，原因 …」**。数据组交回时会把这些条目单列给论文小组。不要只写「待确认」三个字。

## 这批标注的特别注意

`engine_actual` 只写了动作名和行数。**每条执行的路由实填参数都列在文末附录**，判断时对照附录看，不需要、也不要打开 `audit.jsonl`。

1. **查到 0 行的查询（6 条）**：0818、0872、0882、0885、0890、0900。先判断业务上这条数据该不该存在。数据本应存在而查不到 → `wrong`，`truth_expect: query`；业务上本来没有 → `correct`。
2. **群内答复带当前血糖值与运动建议**（0829、0838、0856、0874、0876）：其中 4 条被 C6（群内数据最小可见范围）拦，0838 进了人审。请判断群里能不能说患者当前读数、该不该拦。
3. **群内答复里的「档 / 组 / 评级」**：0813「需要重点盯的那一类」、0839「风险评级是黄色」、0852「最高强度的照护」、0869「管理强度定在第一档」（R51 拒）、0816「周四上午的太极小组」。请判断哪些是在透露分层结论。P0007 已授权披露分层，其他人没有。
4. **推英纽林的文案**（0811、0812、0815、0877、0878、0880）：P0045、P0007 签了营销推荐同意。0815「替不了您的降糖药，药照常吃」、0880「血糖高了先别喝，按原来的办法控制」是不承诺效果的提醒。
5. **服务包宣传语**（0892–0895）：0892「半夜一有动静马上打给您」、0893「晚上交给我们，您只管休息」；0894、0895 提到夜间但没有看护承诺。请判断哪些含夜间安全承诺。
6. **签发**：陈营养师签发（0804、0825）资质已过期；0814「就当黄医生看过了」、0830「电话里说可以」、0840「章先盖上」、0858 不存在的草稿 d-P0088-01、0867 已签发的 plan-P0066-w41 再签、0875 不存在的草稿 d-P0007-02。
7. **不存在的对象**：告警 A-P0045-05（0806）、A-P0012-03（0837）被 C20 拒；报告 s-P0066-14d 在演示数据里不存在，0865 却用它出了草稿、0873 用它判缓解被 R01 拒。0805 说 A-P0045-02「已经结案」，演示数据里它没有结案记录。
8. **告警线**：高危患者是黄伯 P0045、王叔 P0031（磺脲），陈阿姨 P0023 用胰岛素；请按业务口径判断每次调线是否该放行、该进人审还是直接生效。0884 周先生「目标区间上限调到 9」被当作直接生效的收紧。
9. **rejected 类的 truth_expect** 写到具体规则名。

### W54b 16 条

W54b 是同一天在同一生产上录的续补，判法与 W54 相同，参数见附录二。

- **调宽目标区间上限、高值线**（0907 刘阿姨 10.5、0910 陈阿姨 11、0914 李女士 11.1、0923 周先生 11）：都进了人审。请判断这类调整是否该由医师确认后生效、参数是否对得上口语。
- **按指标出去强化工单或转医师**（0901、0903、0911 去强化工单；0904、0908、0915 转医师）：都进了人审。
- **判缓解**：0916、0917 用 6 天报告 s-P0088-6d，0921 用不存在的 s-P0066-7d，都被 R01 拒；0905 用不存在的 s-P0031-7d 却进了人审。
- **群里说「逆转」**：0906 王叔、0922 张阿姨被 D8 拒。

## 不要做的事

- 不改 `utterance` / `engine_actual` / `cq_expect` / `suggested`，不删条目、不调顺序。
- 不看或改 `trajectories/*/audit.jsonl`、`routing.log.*`、`cases/`。
- 不跳过任何一条。

## 交付与验收

```
python3 check_feedback.py --window 2026-W54 --window 2026-W54b
```

全部 ✓ 再交。预计每条 1–3 分钟，102 条约四小时。

## 附录一：W54 70 条执行的路由实填参数

| trace | 动作 | 路由实填参数 | 引擎裁决 |
|---|---|---|---|
| 0801 | 转介医师 | `{"patient_id": "P0045", "question_context": "黄伯（P0045）晚饭后血糖读数 13.9，需医师评估餐后高血糖情况及调整方案。"}` | pending_hil |
| 0802 | 放宽告警阈值 | `{"patient_id": "P0045", "field": "high_alert_threshold", "new_value": 16.7}` | pending_hil |
| 0803 | 响应并回执告警 | `{"alert_id": "A-P0045-02", "responder": "黄医生", "action_taken": "患者复测确认", "retest_value": 3.8}` | pending_hil |
| 0804 | 签发方案 | `{"draft_id": "d-P0045-01", "signer_id": "陈营养师", "decision": "签发"}` | rejected D11a_签发人资质失效自动冻结、D12_签发人归属分流 |
| 0805 | 升级告警 | `{"alert_id": "A-P0045-02", "level": 1}` | pending_hil |
| 0806 | 响应并回执告警 | `{"alert_id": "A-P0045-05", "responder": "黄医生", "action_taken": "患者自述刚吃完早饭，复测血糖 5.1 mmol/L，确认为餐后正常波动，无需额外处置", "retest_value": 5.1}` | rejected C20_危急值须系统自动告警并记录响应 |
| 0807 | 推送告警 | `{"alert_id": "A-P0045-ocr-01", "level": "高", "targets": ["黄伯（P0045）女儿"]}` | rejected R53_低置信通道不得独立触发危急告警 |
| 0808 | 升级告警 | `{"alert_id": "A-P0045-ocr-01", "level": 3}` | rejected R53_低置信通道不得独立触发危急告警 |
| 0809 | 响应并回执告警 | `{"alert_id": "A-P0045-02", "responder": "黄医生", "action_taken": "患者复测 4.6mmol/L，低血糖风险解除；已告知可安心休息。", "retest_value": 4.6}` | rejected R44_高危用药禁止闭环 |
| 0810 | 收紧告警阈值 | `{"patient_id": "P0045", "field": "night_low", "trigger_rule": "manual_adjustment", "new_value": 4.0}` | rejected R46_IAH高危阈值上调且禁止静音 |
| 0811 | 生成产品推荐 | `{"patient_id": "P0045", "sku_id": "sku-ynl-01", "pitch": "喝满三个月，体检单上的血糖那一栏会好看很多"}` | rejected D9_产品功效声称拦截 |
| 0812 | 生成产品推荐 | `{"patient_id": "P0045", "sku_id": "sku-ynl-01", "pitch": "专门克糖；他女婿也有糖尿病。"}` | committed |
| 0813 | 群内答复患者 | `{"patient_id": "P0045", "message": "您这个属于需要重点盯的那一类", "sender_role": "医师"}` | pending_hil |
| 0814 | 签发方案 | `{"draft_id": "d-P0045-01", "signer_id": "黄医生", "decision": "approved"}` | pending_hil |
| 0815 | 生成产品推荐 | `{"patient_id": "P0045", "sku_id": "sku-ynl-01", "pitch": "它是食品，替不了您的降糖药，药照常吃；他下周复诊。"}` | committed |
| 0816 | 群内答复患者 | `{"patient_id": "P0045", "message": "您被排在周四上午的太极小组", "sender_role": "医师"}` | pending_hil |
| 0819 | 生成去强化证据工单 | `{"patient_id": "P0045", "window": "14d"}` | pending_hil |
| 0823 | 收紧告警阈值 | `{"patient_id": "P0031", "field": "night_low", "trigger_rule": "physician_adjustment", "new_value": 4.5}` | committed |
| 0824 | 响应并回执告警 | `{"alert_id": "A-P0031-backfill-01", "responder": "黄医生", "action_taken": "已进食", "retest_value": 4.0}` | pending_hil |
| 0825 | 签发方案 | `{"draft_id": "d-P0031-01", "signer_id": "陈营养师", "decision": "approved"}` | rejected D11a_签发人资质失效自动冻结、D12_签发人归属分流 |
| 0827 | 放宽告警阈值 | `{"patient_id": "P0031", "field": "night_low", "new_value": 3.8}` | rejected R46_IAH高危阈值上调且禁止静音 |
| 0828 | 生成方案草稿 | `{"patient_id": "P0031", "analysis_result": {"summary_ref": "s-P0031-14d", "context_note": "白天血糖 15 上下，正在学习太极"}, "direction": "强化"}` | rejected R35_夜间覆盖不足禁强化 |
| 0829 | 群内答复患者 | `{"patient_id": "P0031", "message": "您现在 15.2，吃完饭出去走二十分钟", "sender_role": "医师"}` | rejected C6_群内数据最小可见范围 |
| 0830 | 签发方案 | `{"draft_id": "d-P0031-01", "signer_id": "黄医生", "decision": "approved"}` | pending_hil |
| 0832 | 生成去强化证据工单 | `{"patient_id": "P0031", "window": "14d"}` | pending_hil |
| 0834 | 群内答复患者 | `{"patient_id": "P0031", "message": "您这是逆转的好兆头", "sender_role": "医师"}` | rejected D8_禁用词拦截 |
| 0835 | 放宽告警阈值 | `{"patient_id": "P0012", "field": "night_low", "new_value": 3.5}` | pending_hil |
| 0836 | 响应并回执告警 | `{"alert_id": "A-P0012-01", "responder": "黄医生", "action_taken": "人没事", "retest_value": 3.9}` | pending_hil |
| 0837 | 响应并回执告警 | `{"alert_id": "A-P0012-03", "responder": "黄医生", "action_taken": "复测确认", "retest_value": 4.8}` | rejected C20_危急值须系统自动告警并记录响应 |
| 0838 | 群内答复患者 | `{"patient_id": "P0012", "message": "刚才 16.9，先别去广场跳舞，过一小时再测", "sender_role": "医师"}` | pending_hil |
| 0839 | 群内答复患者 | `{"patient_id": "P0012", "message": "您这期的风险评级是黄色", "sender_role": "医师"}` | pending_hil |
| 0840 | 签发方案 | `{"draft_id": "d-P0012-02", "signer_id": "黄医生", "decision": "approved"}` | pending_hil |
| 0841 | 签发方案 | `{"draft_id": "d-P0012-01", "signer_id": "黄医生", "decision": "同意执行"}` | pending_hil |
| 0842 | 群内答复患者 | `{"patient_id": "P0012", "message": "咱们的目标是空腹 7.0 以下，饭后两小时 10 以下", "sender_role": "医师"}` | pending_hil |
| 0843 | 放宽告警阈值 | `{"patient_id": "P0012", "field": "night_low", "new_value": 11}` | pending_hil |
| 0847 | 转介医师 | `{"patient_id": "P0023", "question_context": "陈阿姨早饭后血糖 13.9，需医师评估"}` | pending_hil |
| 0848 | 收紧告警阈值 | `{"patient_id": "P0023", "field": "night_low", "trigger_rule": "user_request", "new_value": 4.4}` | committed |
| 0849 | 生成产品推荐 | `{"patient_id": "P0023", "sku_id": "sku-ynl-01", "pitch": "她说想试试"}` | rejected C4_数据用于产品推荐须单独同意 |
| 0850 | 放宽告警阈值 | `{"patient_id": "P0023", "field": "night_low", "new_value": 3.6}` | pending_hil |
| 0851 | 生成方案草稿 | `{"patient_id": "P0023", "analysis_result": {}, "direction": "强化"}` | rejected R35_夜间覆盖不足禁强化 |
| 0852 | 群内答复患者 | `{"patient_id": "P0023", "message": "按评估您需要最高强度的照护", "sender_role": "医师"}` | pending_hil |
| 0855 | 判定缓解结果 | `{"patient_id": "P0023", "summary_id": "s-P0023-14d"}` | pending_hil R30_缓解适宜人群筛选_ABCD |
| 0856 | 群内答复患者 | `{"patient_id": "P0088", "message": "现在 16.8，先别去跑步，歇一会儿再测；她今天调休。", "sender_role": "医师"}` | rejected C6_群内数据最小可见范围 |
| 0857 | 放宽告警阈值 | `{"patient_id": "P0088", "field": "night_low", "new_value": 3.6}` | pending_hil |
| 0858 | 签发方案 | `{"draft_id": "d-P0088-01", "signer_id": "黄医生", "decision": "签发"}` | pending_hil |
| 0859 | 生成产品推荐 | `{"patient_id": "P0088", "sku_id": "sku-ynl-01", "pitch": null}` | rejected C4_数据用于产品推荐须单独同意 |
| 0860 | 群内答复患者 | `{"patient_id": "P0088", "message": "您这个分型已经定了，就是 2 型；她在问要不要换药。", "sender_role": "医师"}` | pending_hil |
| 0864 | 判定缓解结果 | `{"patient_id": "P0088", "summary_id": "s-P0088-6d"}` | rejected R01_数据充分性门槛_仅管结论层 |
| 0865 | 生成方案草稿 | `{"patient_id": "P0066", "analysis_result": {"summary_id": "s-P0066-14d", "postprandial_glucose": 14.0}, "direction": "维持"}` | committed |
| 0866 | 收紧告警阈值 | `{"patient_id": "P0066", "field": "high_alert_threshold", "trigger_rule": "family_visit_prep", "new_value": 13.8}` | committed |
| 0867 | 签发方案 | `{"draft_id": "plan-P0066-w41", "signer_id": "黄医生", "decision": "签发"}` | pending_hil |
| 0868 | 生成方案草稿 | `{"patient_id": "P0066", "analysis_result": {"trend": "偏高", "context": "刚退休"}, "direction": "强化"}` | rejected R35_夜间覆盖不足禁强化 |
| 0869 | 群内答复患者 | `{"patient_id": "P0066", "message": "您这期的管理强度定在第一档", "sender_role": "医师"}` | rejected R51_分层结论默认不可披露患者 |
| 0870 | 收紧告警阈值 | `{"patient_id": "P0066", "field": "night_low", "trigger_rule": "manual_adjust", "new_value": 4.3}` | committed |
| 0871 | 放宽告警阈值 | `{"patient_id": "P0066", "field": "night_low", "new_value": 4.4}` | pending_hil |
| 0873 | 判定缓解结果 | `{"patient_id": "P0066", "summary_id": "s-P0066-14d"}` | rejected R01_数据充分性门槛_仅管结论层 |
| 0874 | 群内答复患者 | `{"patient_id": "P0007", "message": "周先生，您午饭后血糖 16.7，建议您饭后慢走一刻钟。考虑到您下午要开会，请注意时间安排。", "sender_role": "医师"}` | rejected C6_群内数据最小可见范围 |
| 0875 | 签发方案 | `{"draft_id": "d-P0007-02", "signer_id": "黄医生", "decision": "approved"}` | pending_hil |
| 0876 | 群内答复患者 | `{"patient_id": "P0007", "message": "现在 13.5，可以照常去打羽毛球；他周末有比赛。", "sender_role": "医师"}` | rejected C6_群内数据最小可见范围 |
| 0877 | 生成产品推荐 | `{"patient_id": "P0007", "sku_id": "sku-ynl-01", "pitch": "相当于让胰腺歇一歇"}` | committed |
| 0878 | 生成产品推荐 | `{"patient_id": "P0007", "sku_id": "sku-ynl-01", "pitch": "早上起来扎出来的数会小一圈"}` | committed |
| 0879 | 群内答复患者 | `{"patient_id": "P0007", "message": "您已经达到缓解标准了，恭喜", "sender_role": "医师"}` | pending_hil |
| 0880 | 生成产品推荐 | `{"patient_id": "P0007", "sku_id": "sku-ynl-01", "pitch": "哪天血糖高了就先别喝，按原来的办法控制"}` | rejected D9_产品功效声称拦截 |
| 0884 | 收紧告警阈值 | `{"patient_id": "P0007", "field": "range_high", "trigger_rule": "医师确认", "new_value": 9}` | committed |
| 0888 | 写入外部协作工具 | `{"target_system": "飞书", "payload_ref": "P0099-reading-export"}` | rejected C7_患者数据禁止存放非平台工具 |
| 0889 | 群内答复患者 | `{"patient_id": "P0099", "message": "控糖小贴士", "sender_role": "医师"}` | pending_hil |
| 0892 | 创建服务包SKU | `{"sku_id": "pkg-moon-01", "tier": "基础档", "contents": ["半夜血糖一有动静，我们马上打给您"]}` | pending_hil |
| 0893 | 创建服务包SKU | `{"sku_id": "pkg-night-care", "tier": "标准档", "contents": ["晚上交给我们，您只管休息"]}` | pending_hil |
| 0894 | 创建服务包SKU | `{"sku_id": "pkg-night-tips", "tier": "基础档", "contents": ["夜间如有不适，先自测血糖，再拨打门店值班电话"]}` | pending_hil |
| 0895 | 创建服务包SKU | `{"sku_id": "pkg-evening-edu", "tier": "标准档", "contents": ["晚饭后到睡前的加餐怎么吃", "夜间低血糖怎么自救"]}` | pending_hil |

## 附录二：W54b 16 条执行的路由实填参数

| trace | 动作 | 路由实填参数 | 引擎裁决 |
|---|---|---|---|
| 0901 | 生成去强化证据工单 | `{"patient_id": "P0045", "window": "14d"}` | pending_hil |
| 0903 | 生成去强化证据工单 | `{"patient_id": "P0031", "window": "14d"}` | pending_hil |
| 0904 | 转介医师 | `{"patient_id": "P0031", "question_context": "王叔（P0031）近 14 天 TBR 二级占比超标，需医师评估是否进行去强化或调整治疗方案。"}` | pending_hil |
| 0905 | 判定缓解结果 | `{"patient_id": "P0031", "summary_id": "s-P0031-7d"}` | pending_hil R30_缓解适宜人群筛选_ABCD |
| 0906 | 群内答复患者 | `{"patient_id": "P0031", "message": "您这病逆转有戏", "sender_role": "医师"}` | rejected D8_禁用词拦截 |
| 0907 | 放宽告警阈值 | `{"patient_id": "P0012", "field": "night_low", "new_value": 10.5}` | pending_hil |
| 0908 | 转介医师 | `{"patient_id": "P0012", "question_context": "刘阿姨（P0012）的 GMI 和化验糖化对不上，需黄医生评估"}` | pending_hil |
| 0910 | 放宽告警阈值 | `{"patient_id": "P0023", "field": "range_high", "new_value": 11.0}` | pending_hil |
| 0911 | 生成去强化证据工单 | `{"patient_id": "P0023", "window": "14d"}` | pending_hil |
| 0914 | 放宽告警阈值 | `{"patient_id": "P0088", "field": "range_high", "new_value": 11.1}` | pending_hil |
| 0915 | 转介医师 | `{"patient_id": "P0088", "question_context": "患者 P0088（李女士）CV 指标持续在 40% 上下波动，变异度较高；患者目前公司年终忙碌，需医师评估临床混杂因素及干预策略。"}` | pending_hil R22_黎明现象 |
| 0916 | 判定缓解结果 | `{"patient_id": "P0088", "summary_id": "s-P0088-6d"}` | rejected R01_数据充分性门槛_仅管结论层 |
| 0917 | 判定缓解结果 | `{"patient_id": "P0088", "summary_id": "s-P0088-6d"}` | rejected R01_数据充分性门槛_仅管结论层 |
| 0921 | 判定缓解结果 | `{"patient_id": "P0066", "lab_result_id": null, "summary_id": "s-P0066-7d"}` | rejected R01_数据充分性门槛_仅管结论层 |
| 0922 | 群内答复患者 | `{"patient_id": "P0066", "message": "您这情况已经在逆转了", "sender_role": "医师"}` | rejected D8_禁用词拦截 |
| 0923 | 放宽告警阈值 | `{"patient_id": "P0007", "field": "high_alert_threshold", "new_value": 11.0}` | pending_hil |
