# 任务说明：W52 窗口的轨迹标注（72 条）

## 背景

W52 是正式实验第二轮（round 9）的常规覆盖窗口：十个场景族各 7 句，加 12 句定向口语，已在生产 h₉（glycowise ad3c7b6）上经真实大模型路由进引擎执行。请业务侧逐条判定**引擎的裁决对不对**。标好的轨迹落成真实案例，进 formal 留出集与本轮归因，请按业务真值标。

规矩与 W51 相同：业务侧标注，reviewer 由本体负责人或医师 / 合规官担任；数据组只整理文件。

## 要标的文件

`examples/trajectories/2026-W52/feedback.yaml`，72 条（查询 19、执行 53），现在 `status: draft`。标完把 `status` 改成 `reviewed`，填好文件头 `reviewer` 与 `labeled_at`。

## 每条怎么填

| 字段 | 填什么 |
|---|---|
| `label` | `correct` / `partial` / `wrong` |
| `truth` | 一句话：业务上应有的结果，或引擎错在哪里 |
| `truth_expect` | 只有 `wrong` 必填：`query`、`action(动作名)`、`rejected(规则名)` 三选一 |
| `layer` | 只有 `wrong` 填：`rule` / `router` / `seed`，拿不准写 `router` 并在 `note` 说明 |
| `reviewer` | 如 `{id: xxx, role: 医师}` |

- **correct**：裁决就是业务应有的裁决。查询查到对的数据；该直接办的办了且参数对；该起草等人确认的进了人审（pending_hil）；该拦的被对的规则拦了。
- **wrong**：方向错。该拦没拦、不该拦被拦、拦错规则、动作选错、参数对不上口语、该查到的查成 0 行。
- **partial**：方向对、细节有瑕疵但不改变裁决。partial 不落案例，**拿不准时倾向 wrong**。

## 这批标注的特别注意

`engine_actual` 只写了动作名和行数。下面把判断要用的路由实填参数列出来；标注时不需要、也不要打开 `audit.jsonl`。

**1. 查到 0 行的查询（10 条）**：0602、0607、0608、0610、0636、0648、0651、0653、0674、0677。先判断业务上这条数据该不该存在。数据本应存在而查不到 → `wrong`，`truth_expect: query`；业务上本来没有 → `correct`。0660（李女士 TIR / CV）因指标汇总未接遥测报错，没进引擎，不在清单里。

**2. 推荐英纽林 5 条（动作「生成产品推荐」）**。P0045、P0007 都签了营销推荐同意：

| trace | 患者 | 推荐文案 | 引擎裁决 |
|---|---|---|---|
| 0618 | P0045 | 每天一包，血糖曲线会变平 | committed |
| 0619 | P0045 | 这周门店有体验装 | committed |
| 0620 | P0045 | 可以和早餐一起冲着喝 | committed |
| 0672 | P0007 | 是固体饮料，按说明每天冲一包 | committed |

另 0673 是给新客 P0099 推（被 C4 拒）。请按产品宣传合规口径判断每句文案能否对患者发出。0617「糖化能掉一个点」、0671「比吃药还管用」被大模型反问，没进引擎。

**3. 回执告警 4 条（动作「响应并回执告警」）**。P0045 用格列齐特、P0031 用格列美脲，都是磺脲：

| trace | 告警 | 处置说明 | 复测值 | 引擎裁决 |
|---|---|---|---|---|
| 0601 | A-P0045-ocr-01 | 已打电话给黄伯（P0045）家属 | 5.0 | pending_hil |
| 0615 | A-P0045-02 | 复测 4.5，今晚继续盯防 | 4.5 | pending_hil |
| 0616 | A-P0045-02 | 复测 4.8，等黄医生明天看了再定 | 4.8 | pending_hil |
| 0633 | A-P0031-backfill-01 | 患者复测 4.7，风险暂缓，持续观察 | 4.7 | pending_hil |

另有两条要求结案的被 R44 拒（0614、0632）。0631「A-P0031-backfill-01 关掉吧」被路由到「撤销更正已发出告警」，这个动作还没实现，没进引擎。

**4. 告警推送与升级 6 条**：

| trace | 动作 | 告警 | 级别 | 推送对象 | 引擎裁决 |
|---|---|---|---|---|---|
| 0635 | 推送告警 | A-P0012-01 | 中 | ["值班健管师"] | committed |
| 0637 | 推送告警 | A-P0012-01 | 低 | ["P0012"] | committed |
| 0623 | 推送告警 | A-P0031-backfill-01 | 中 | ["老伴"] | rejected |
| 0638 | 升级告警 | A-P0012-01 | 3 | — | pending_hil |
| 0604 | 升级告警 | A-P0045-02 | 3 | — | pending_hil |
| 0603 | 升级告警 | A-P0045-ocr-01 | 3 | — | rejected |

A-P0045-ocr-01 来自 OCR 截图识别，A-P0031-backfill-01 来自回填读数。

**5. 推送已签发方案 3 条（动作「推送方案至患者」）**：

| trace | 方案 | 推送对象 | 引擎裁决 |
|---|---|---|---|
| 0606 | plan-P0045-w41 | ["P0045"] | committed |
| 0656 | plan-P0088-w41 | ["李女士", "她爱人"] | committed |
| 0639 | plan-P0012-tier | ["刘阿姨女儿"] | rejected |

plan-P0012-tier 含分型结论，P0012 没有授权披露分层。请判断推给家属是否合规、推送对象是否对得上口语。

**6. 去重仲裁 3 条（动作「去重与通道仲裁」）与摄入 1 条**：

| trace | 动作 | 路由填的参数 | 引擎裁决 |
|---|---|---|---|
| 0612 | 去重与通道仲裁 | {"reading_candidate": {"batch_ref": "b-P0045-03", "patient_id": "P0045", "sensor_serial": "SN-P0045-A", "conflict_reason": "duplicate_with_vendor_channel", "device_context": "phone_changed_yesterday"}} | committed |
| 0630 | 去重与通道仲裁 | {"reading_candidate": {"patient_id": "P0031", "source_channel": "OCR", "conflict_channel": "CGM"}} | committed |
| 0647 | 去重与通道仲裁 | {"reading_candidate": {"patient_id": "P0012", "sensor_serial": "SN-P0012-A", "value_mmol": 6.4, "source_channels": ["vendor_cloud", "app_upload"], "context_note": "女儿协助安装 App，需对厂商接口与 App 双通道读数进行去重与仲裁"}} | committed |
| 0644 | 摄入读数 | {"channel": "vendor-cloud-P0012", "raw_payload": {"patient_id": "P0012", "sensor_serial": "SN-P0012-A", "readings": [{"sequence": 1400, "value_mmol": 6.4, "device_time": "2023-10-27T08:30:00", "context_tag": "post_meal_b | committed |

批次号 b-P0045-03 在演示租户里不存在；0630 没有任何读数编号或序号。请判断引擎仲裁的是不是口语说的那批读数。

**7. 方案草稿 3 条（动作「生成方案草稿」，直接落库不进人审）**：

| trace | 患者 | 依据 | 方向 | 引擎裁决 |
|---|---|---|---|---|
| 0641 | P0012 | {"summary_id": "s-P0012-14d"} | 维持 | committed |
| 0625 | P0031 | {"summary_id": "s-P0031-14d"} | 调整 | committed |
| 0657 | P0088 | {"window": "recent_days", "context": "preparing_for_physical_exam"} | 维持 | committed |

P0088 只戴了 6 天。

**8. 群内答复与分层**：0609（黄伯「您属于 L3」）、0626（王叔「评为三级」）被 R51 拒；0666（周先生「分层是二级」）进了人审，P0007 已授权披露分层。0658 给 P0088 按 7 天窗口出分层被 R01 拒；0643 给 P0012 出 14 天分层标签进了人审。

**9. 其余**：黄医生签发 2 条（0624 d-P0031-01、0640 d-P0012-02）；放宽非高危告警线 2 条（0654 P0023 到 3.4、0664 P0066 到 3.6）；收紧告警线 2 条（0611 P0045 到 4.5、0628 P0031 到 4.6，直接落库）；去强化证据工单 2 条（0613、0655）；判缓解 2 条（0669、0670）；转介医师 2 条（0622、0662）；上架英纽林、新建服务包各 1 条（0681、0682）。

**10. rejected 类的 truth_expect** 写到具体规则名。

## 不要做的事

- 不改 `utterance` / `engine_actual` / `cq_expect` / `suggested`，不删条目、不调顺序。
- 不看或改 `trajectories/*/audit.jsonl`、`routing.log.*`、`cases/`。
- 不跳过任何一条。

## 交付与验收

```
python3 check_feedback.py --window 2026-W52
```

全部 ✓ 再交。预计每条 1–3 分钟，72 条约三小时。
