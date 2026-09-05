# Ontology Map: glycowise

- ontology_id: glycowise
- bounded_context: 控糖服务（CGM 数据摄入 → 指标 → 临床规则 → 方案签发 → 履约与缓解判定）
- target_dir: plugins/glycowise
- source_artifacts:
    - studio/changes/glycowise/behavior-matrix.md
    - studio/changes/glycowise/domain-canvas.md
    - studio/changes/glycowise/processes/{enrollment,daily-monitoring,review-and-plan,remission-assessment}.md
    - studio/changes/glycowise/journeys/*.md、studio/changes/glycowise/personas/*.md（§7 CQ 来源）
    - studio/changes/glycowise/decisions/confirmed-facts.md（**事实基准，优先级高于其余全部**）
    - research/sources/02-CGM临床指标与规则库.md §8（R01–R32 规则候选表）
    - research/sources/04-合规风险.md §6（22 条合规风险清单）
- iteration: 1
- date: 2026-09-05
- 建模分工：`ontology-architect`（Object/Link/Function/Action/Mapping）、`rule-engineer`（Rule 抽取、分类、挂出处）

> 本次无 event-storm.md。Hotspot 一路的输入由 processes 的 Decision Point 与 behavior-matrix §3 事件映射表替代。

## 读这份 IR 之前要知道的五件事

1. **规则治理是这个本体的核心价值。** 每条 Rule 都带 `source` + `citations`：临床规则追到指南条目，合规规则追到法条条款号。没有一条留空——`ontology-validate` 会审计这一项。研究文档自己标注"待核实"的几条，`source` 写成 `TODO(FDE): 补依据`，这是显式缺口不是遗漏。
2. **两套低血糖口径物理分开。** 实时告警触发 = 连续 2 个读数 + 预测性告警；回顾性事件统计 = 持续 ≥15 分钟的 Danne 口径。它们在 IR 里是 **R03a/R04a 与 R03b/R04b 四条独立 Rule**，不是一条带参数的规则。把统计定义拿去做告警触发条件，是本系统最容易致命的实现错误（confirmed-facts C-01、A3-6、R-4）。编译后 FDE 若为省事让它们共用一个判定函数，等于原样重犯已被临床评审纠正过的错。
3. **数据充分性门槛只关结论层。** R01（14 天 + ≥70%）不是全局前置门，它只关闭达标/分层/缓解这一类结论输出，安全通道在佩戴第 1 天就生效（confirmed-facts C-11）。把它做成全局闸会静音佩戴早期的夜间低血糖。
4. **人群维度是规则入参，不是分支硬编码。** age≥65 切老年三分层目标、无感知低血糖高危人群阈值上调 4.4 且不可静音、pregnant 切 3.5–7.8，都建成独立的参数切换规则（R28/R46/R31），由下游规则读取 `target_profile`。
5. **一期无实时告警（confirmed-facts B-13）。** 实时链路的 Rule 与 Action **全部照建**并标 `phase=P2`，二期直接启用。一期不投递不等于不建模——一期的回顾性事件统计正好是二期实时告警 ROI 的基线数据（R-4）。

---

## 1. Objects（对象）— compiles to `ObjectType`

| name | primary_key | properties | lifecycle | source |
|---|---|---|---|---|
| GlucoseReading | reading_id | value_raw:number:required:密级=confidential, unit_raw:enum=mmol/L\|mg/dL:required, value_mmol:number:mmol/L, device_time:string, time_utc:string, tz_provenance:enum=device_reported\|vendor_reported\|patient_profile_inferred\|upload_day_assumed:required, source_channel:enum=vendor_api\|sdk_ble_direct\|ble_gls_1808\|ocr_upload\|manual_entry\|staff_entry, source_confidence:number, quality_flag:enum=clean\|warmup\|noise\|out_of_range\|superseded\|suspect_duplicate\|reattached, is_backfill:boolean, data_age:string, sensor_serial:string, dedup_key:string | ingested,quality_tagged,superseded,retracted,corrected (initial=ingested) | behavior-matrix §4/§6；domain-canvas D1；daily-monitoring §2.1 |
| IngestBatch | batch_id | channel:string, record_count:number, status:enum=pending\|committed\|rejected\|rolled_back | pending,committed,rejected,rolled_back (initial=pending) | behavior-matrix §6 |
| VendorSummarySnapshot | snapshot_id | vendor:string:required, algo_version:string:required, denominator_def:string:required, metric_provenance:string | recorded (initial=recorded) | behavior-matrix §6；daily-monitoring D1b |
| ChannelRegistry | channel_id | vendor:string:required, model:string, capability_level:enum=cloud_api\|report_only\|pilot\|none:required, storage_region:string:required, sampling_interval:number:分钟:required, warmup_minutes:number, max_window_days:number, rate_limit:number, is_incremental_cursor:boolean, supports_realtime_alert:boolean, observed_latency_p95:number, dpa_no:string | draft,active,deprecated (initial=draft) | domain-canvas D1；processes/README |
| DeviceModel | model_id | vendor:string:required, sampling_interval:number:分钟, warmup_minutes:number, expiry_days:number, calibration_free:boolean, native_unit:string, mard_pct:number, sdk_protocol_version:string | active,deprecated (initial=active) | behavior-matrix §6；domain-canvas D8a |
| CarrierRegistry | patient_id | carrier_type:enum=none\|patient_phone\|gateway_box:required, last_sync_at:string, coverage_window:string, supports_local_forced_alert:boolean, sync_plan_ref:ref(SyncPlan) | registered,active,degraded (initial=registered) | confirmed-facts B-13、R-2；processes/README。一期取值域只有 none\|patient_phone；gateway_box 为二期占位 |
| GatewayDevice | sn | model:string, firmware_version:string, bound_patient_id:ref(PatientProfile), bound_at:string, last_heartbeat_at:string, online:boolean, unbound_at:string, returned_at:string, asset_status:enum=未配发\|在用\|已回收\|遗失 | 未配发,已绑定,在线,离线,已解绑,已归还 (initial=未配发) | behavior-matrix §6。**生效阶段=P2**（confirmed-facts B-13：一期不做采集盒） |
| SensorSession | session_id | sensor_serial:string:required, vendor:string, sensor_model:string, placement_time:string:required, warmup_minutes:number, expected_sampling_interval:number:分钟, expiry_days:number, end_reason:enum=replaced\|fallen_off\|expired\|failed_at_placement | opened,warmup,active,expired,fallen_off,replaced,closed (initial=opened) | behavior-matrix §6；domain-canvas D8a |
| PatientTimeBaseline | patient_id | patient_phone_tz:string, patient_phone_clock_offset:number, device_clock_offset:number, tz_baseline:string | collected,corrected (initial=collected) | behavior-matrix §6；domain-canvas §3.3 |
| SyncPlan | patient_id | trigger_type:enum=到店自动\|主动打开\|子女协助\|同住家属:required, expected_interval:number:小时, assist_person:string | established,revised (initial=established) | enrollment.md D11e |
| ConsentRecord | consent_id | patient_id:required, scope_items:list:required, version:string:required, signed_at:string:required, ip_device:string:密级=confidential, hash:string, legacy_import:boolean | granted,scope_changed,revoked (initial=granted) | domain-canvas D7；behavior-matrix §6 |
| ConsentRevocation | revocation_id | patient_id:required, scope:list:required, revoked_at:string:required, executed_at:string, executor:string | raised,executed (initial=raised) | domain-canvas D7 |
| ContactConsent | contact_id | patient_id:required, contact_person:string:required, confirmed_at:string, method:string | pending,confirmed (initial=pending) | behavior-matrix §5.1 |
| VendorGrant | grant_id | vendor:string:required, patient_id:required, granted_at:string, scope:list, expires_at:string, status:enum=active\|revoked\|expired | active,revoked,expired (initial=active) | behavior-matrix §6 |
| PatientProfile | patient_id | age:number:required, pregnant:boolean, meds:list:密级=confidential, health_tier:enum=良好\|中等\|差, target_profile:enum=adult\|elderly\|pregnancy, is_iah_high_risk:boolean, eGFR:number, renal_unknown:boolean, tier_label:string, disclosure_approved:boolean, remission_status:enum=none\|candidate\|in_remission\|relapsed, away_mode:boolean | draft,baseline_complete,active,exited (initial=draft) | behavior-matrix §6；domain-canvas D15 |
| MedClassHint | hint_id | patient_id:required, hint_source:enum=self_report\|drug_box_photo:required, hypo_risk_med:boolean, sglt2i:boolean | collected,confirmed,discarded (initial=collected) | behavior-matrix §6/§7.1 G1b |
| LabResult | lab_result_id | patient_id:required, value:number:密级=confidential, method:string:required, lab_id:string, is_ngsp_certified:boolean, specimen_type:string, measured_at:string:required | recorded (initial=recorded) | behavior-matrix §6 |
| BodyMeasurement | measurement_id | patient_id:required, measured_at:string:required, device_id:string:required, protocol_version:string:required, fasting:boolean, weight:number:kg, waist:number:cm, body_fat_pct:number | recorded (initial=recorded) | behavior-matrix §6/§7.1 G10 |
| PatientIdentityLink | patient_id | wecom_external_userid:string, feishu_record_id:string, vendor_account_id:string | active,revoked (initial=active) | behavior-matrix §6 |
| AlertThreshold | threshold_id | patient_id:required, field:string:required, current_value:number:required, default_value:number, safe_direction:enum=收紧\|放宽:required | active (initial=active) | behavior-matrix §6；daily-monitoring §2.3b |
| ThresholdChangeLog | log_id | patient_id:required, changed_by:string:required, trigger_rule:string, before:number, after:number, effective_window:string | recorded (initial=recorded) | 同上 |
| AlertEvent | alert_id | patient_id:required, level:enum=低\|中\|高\|危急:required, value:number, trend:number, evidence:string, confidence:number, rule_id:string:required, is_backfill:boolean | raised,acknowledged,value_recovered,escalated,escalated_emergency,resolved,retracted (initial=raised) | domain-canvas D4；daily-monitoring §2.2/2.4。实时推送分支 **phase=P2** |
| AlertAck | ack_id | alert_id:required, responder:string:required, responded_at:string:required, action_taken:string, retest_value:number | recorded (initial=recorded) | daily-monitoring D20 |
| AlertEscalation | escalation_id | alert_id:required, level:number:required, escalated_at:string, target:string | raised,closed (initial=raised) | daily-monitoring §2.4。**phase=P2** |
| AlertSuppressedLog | log_id | alert_id:required, reason:string:required, suppressed_at:string | recorded (initial=recorded) | behavior-matrix §6 A117b。**phase=P2** |
| HypoEpisode | episode_id | patient_id:required, start_time:string:required, end_time:string:required, min_value:number, level:enum=L1\|L2:required, night_flag:boolean | detected (initial=detected) | domain-canvas D2；daily-monitoring D11。一期核心安全产出：次日医师减药审查证据 |
| HypoState | patient_id | prolonged_risk:boolean, recurrence_window_until:string, closure_blocked_reason:string | none,prolonged_risk,recurrence_window,closed (initial=none) | behavior-matrix §6；daily-monitoring D12b/D21 |
| CgmSummary | summary_id | patient_id:required, window_start:string:required, window_end:string:required, wear_ratio:number, active_pct:number, sufficiency_ok:boolean, tz_uncertain:boolean, brand_changed:boolean, metric_provenance:enum=self_computed\|vendor_reported, nocturnal_coverage_pct:number, nocturnal_coverage_insufficient:boolean, confounded_window:boolean | computed,stale,recomputed,invalidated (initial=computed) | domain-canvas D3；confirmed-facts「一期特有医源性伤害路径」 |
| ContextEvent | event_id | patient_id:required, event_type:enum=meal\|exercise\|sleep\|supplement_checkin\|away:required, occurred_at:string:required, meal_time_confidence:number, recorded_by:string | recorded (initial=recorded) | domain-canvas D9。`event_type` 禁用 MNT |
| SymptomTreatmentRecord | record_id | patient_id:required, alert_id:string, symptom_tag:string, treatment_action:string, recorded_by:string:required, recorded_at:string:required | recorded (initial=recorded) | behavior-matrix §6/§7.1 G7。R10 唯一输入 |
| KetoneReading | ketone_id | patient_id:required, value_or_qualitative:string:required, measured_at:string:required, method:enum=血酮仪\|尿酮试纸 | recorded (initial=recorded) | behavior-matrix §7.1 G9 |
| ClinicalContextEvent | event_id | patient_id:required, type:enum=急性病\|感染发热\|激素使用\|住院\|用药调整:required, start_at:string:required, end_at:string | recorded,closed (initial=recorded) | behavior-matrix §7.1 G6；review-and-plan D2b |
| MealResponse | response_id | patient_id:required, meal_event_id:required, baseline:number, delta_p:number, time_to_peak:number:分钟, iAUC_2h:number, r2h:number, return_to_baseline:boolean, pairing_quality:number, cross_brand:boolean | computed (initial=computed) | domain-canvas D10 |
| DutyRoster | roster_id | date:string:required, slot:string:required, responder:string | scheduled,gap_detected (initial=scheduled) | behavior-matrix §6；confirmed-facts D-02。**phase=P2** |
| EmergencyContact | contact_id | patient_id:required, name:string:required, phone:string:required:密级=confidential, relation:string, can_reach_onsite:boolean | registered (initial=registered) | behavior-matrix §6 |
| PlanDraft | draft_id | patient_id:required, content:string:required, template_version:string, med_interaction_routed:boolean, direction:enum=强化\|维持\|去强化 | drafted,gated,pending_signoff,rejected (initial=drafted) | domain-canvas D5 |
| PlanSigned | plan_id | patient_id:required, content_snapshot:string:required, signer_id:string:required, signed_at:string:required, evidence_snapshot:string:required, review_evidence_ref:string, evidence_stale:boolean | signed,superseded,revoked (initial=signed) | domain-canvas D5 |
| TaperPlan | taper_id | patient_id:required, original_document_hash:string:required, schedule:string:required, relapse_redline:string | signed,active,completed,aborted (initial=signed) | remission-assessment D3 |
| ComplianceCheckLog | log_id | model_version:string, prompt_version:string, hit_rules:list, blocked_reason:string, target_content_ref:string | recorded (initial=recorded) | domain-canvas D6a |
| GateToken | token_id | issued_at:string:required, scope:string:required, expiry:string:required | issued,consumed,expired (initial=issued) | domain-canvas D6a |
| BannedTermLibrary | term_id | term:string:required, category:string:required, version:string:required | active,deprecated (initial=active) | domain-canvas D6a/D6b |
| ComplianceIncident | incident_id | actor:string:required, hit_text_fragment:string, recorded_at:string:required | recorded,escalated (initial=recorded) | behavior-matrix §6 |
| Credential | credential_id | holder:string:required, credential_type:string:required, registration_no:string:required, expiry_date:string:required, status:enum=valid\|expiring\|revoked\|frozen | valid,expiring,revoked,frozen (initial=valid) | domain-canvas D18 |
| ServicePackage | package_id | patient_id:required, tier:enum=A\|B\|C:required, start_date:string, end_date:string, wear_days_fulfilled:number | pending,active,completed,exited (initial=pending) | domain-canvas D11a |
| ServiceExitRecord | exit_id | patient_id:required, exit_at:string:required, exit_stage:string, exit_path:enum=P1\|P2\|P3\|P4\|P5\|P6, refund_amount:number, fulfilled_days:number, last_churn_signal:string | recorded (initial=recorded) | behavior-matrix §6 |
| ChurnSignal | signal_id | patient_id:required, code:string:required, severity:enum=黄\|橙\|红, applicable:boolean | raised,processed (initial=raised) | domain-canvas D11a |
| KpiSettlement | settlement_id | package_id:required, safety_gate_passed:boolean:required, tir_delta:number, settlement_result:string | computed (initial=computed) | review-and-plan D17。"减药"禁入任何字段 |
| RemissionClock | patient_id | day0:string, status:enum=running\|reset\|stopped:required, confirmed_by:string | started,running,reset,stopped (initial=started) | remission-assessment D3/D5 |
| RemissionAssessment | assessment_id | patient_id:required, status:enum=in_remission\|not_in_remission:required, evidence_pack_ref:string:required, method_used:enum=HbA1c\|GMI\|FPG:required | assessed (initial=assessed) | remission-assessment D8 |
| EnrollmentDecision | decision_id | patient_id:required, flags:list, decided_by:string:required, decided_at:string:required, coverage_disclosed_at:string, channel_verified_at_store:boolean | decided,pending_channel,enrolled (initial=decided) | enrollment.md D4/D11b/D11c |
| ReviewEvidence | evidence_id | plan_id:required, opened_at:string, agp_expand_count:number, dwell_time:number:秒, diff:string, review_suspicious:boolean | collected (initial=collected) | review-and-plan D13 |
| DeliveryReceipt | receipt_id | target:string:required, channel:string:required, delivered_at:string, status:enum=requested\|delivered\|rejected, gate_token_ref:string | requested,delivered,rejected (initial=requested) | behavior-matrix §6 |
| StoreReadinessCheck | check_id | store_id:string:required, checked_at:string, signed_by:string | pending,passed (initial=pending) | behavior-matrix §7.1 G4 |
| ReferralRecord | referral_id | patient_id:required, question:string:required, referred_to:string:required, referred_at:string:required, replied_at:string | recorded,replied (initial=recorded) | behavior-matrix §7.2 |
| OnsiteTriageRecord | record_id | patient_id:required, glucose_value:number:required, tier:string, disposition:string | recorded (initial=recorded) | behavior-matrix §7.2；enrollment D2 |
| PsychNote | note_id | patient_id:required, content:string:密级=confidential | recorded (initial=recorded) | behavior-matrix §6 |
| MetricRegistry | metric_id | name:string:required, numerator_def:string:required, denominator_def:string:required, exclusions:string, version:string:required, owner:string:required | active,deprecated (initial=active) | behavior-matrix §6；confirmed-facts R-3 |
| AuditLog | log_id | actor:string:required, action:string:required, target:string, timestamp:string:required | recorded (initial=recorded) | domain-canvas D13。只进不出，≥3 年 |
| DataSubjectRequest | request_id | patient_id:required, type:enum=查阅\|复制\|更正\|删除\|可携\|自动化决策解释:required, received_at:string:required, resolved_at:string | received,resolved (initial=received) | domain-canvas D7 |
| StoreEntity | store_id | name:string:required, license_no:string, medical_scope:list, readiness_ref:string | active,suspended (initial=active) | domain-canvas D18；enrollment D8 |
| ProductSku | sku_id | name:string:required, category:enum=服务\|食品\|器械引用:required, label_verified:boolean, commission_config:string | draft,listed,rejected,delisted (initial=draft) | domain-canvas D11a/X4；behavior-matrix §6 |
| OutboundContent | content_id | target_audience:string:required, body:string:required, content_type:enum=方案\|日报\|周报\|告警\|宣传素材\|群内答复:required, gate_token_ref:string, disclaimer_attached:boolean | drafted,gated,blocked,delivered (initial=drafted) | domain-canvas D6a/D16 |

共 **62** 个 Object。

> **判 Object 的口径**：TIR/TAR/TBR/GMI/CV/MAGE/AGP/active%/nocturnal_coverage_pct 全部是派生量，进 §3 Function，**不建 Object**。`CgmSummary` 是这些派生量的物化快照（有窗口、有版本、被引用、需失效通知），所以它是 Object。
>
> **一期/二期边界**：`GatewayDevice / AlertEscalation / AlertSuppressedLog / DutyRoster` 标 phase=P2，一期不实现但照建，二期直接启用（confirmed-facts B-13、R-2）。`CarrierRegistry` 一期即建——云侧拉取也是一条 carrier，健康度监控一期就要跑（R-2）。

---

## 2. Links（关系）— compiles to `LinkType`

| name | from | to | cardinality | edge_semantics | properties |
|---|---|---|---|---|---|
| belongs_to_session | GlucoseReading | SensorSession | 1:N | derivation | 按 device_time 晚绑定解析，可重算 |
| uses_device_model | SensorSession | DeviceModel | 1:N | derivation | — |
| via_channel | GlucoseReading | ChannelRegistry | 1:N | derivation | — |
| has_carrier | PatientProfile | CarrierRegistry | 1:1 | derivation | — |
| has_sync_plan | PatientProfile | SyncPlan | 1:1 | derivation | — |
| bound_gateway | CarrierRegistry | GatewayDevice | 1:1 | derivation | phase=P2 |
| computed_from | CgmSummary | GlucoseReading | 1:N | derivation | window |
| statistically_derived_from | HypoEpisode | GlucoseReading | 1:N | derivation | Danne ≥15min 口径，**仅供统计** |
| triggered_by_reading | AlertEvent | GlucoseReading | 1:N | root_cause | 触发读数即告警成立的根因，溯源可终止；连续 2 读数口径 |
| gates_alert_closure | HypoState | AlertEvent | 1:N | root_cause | closure_blocked_reason 是"能否闭环"的终止判据 |
| escalates_via | AlertEvent | AlertEscalation | 1:N | derivation | phase=P2 |
| acknowledged_by | AlertEvent | AlertAck | 1:1 | derivation | — |
| suppressed_as | AlertEvent | AlertSuppressedLog | 1:1 | derivation | phase=P2 |
| gated_by_duty_roster | AlertEscalation | DutyRoster | 1:N | root_cause | 值班链尾留空即安全事故直接根因，不是待查假设 |
| unblocks_closure | SymptomTreatmentRecord | AlertEvent | 1:N | derivation | 判据之一，仍需结合 HypoState |
| confirms_ketosis | KetoneReading | AlertEvent | 1:N | root_cause | 酮体阳性是终止酮症判断链的客观证据 |
| based_on_summary | PlanDraft | CgmSummary | 1:N | hypothesis | 草稿依据指标，须经人工复核才成立，不可终止推理 |
| supersedes | PlanSigned | PlanDraft | 1:1 | derivation | — |
| gated_by_token | OutboundContent | GateToken | 1:N | root_cause | 无 token 硬拒投递 |
| requires_credential | PlanSigned | Credential | 1:N | root_cause | 资质失效即签不出，直接根因 |
| gates_delivery | ComplianceCheckLog | DeliveryReceipt | 1:N | root_cause | gate.blocked 直接阻断投递 |
| marks_confounded | ClinicalContextEvent | CgmSummary | 1:N | root_cause | 命中即终止该窗口的分层/续约/缓解资格 |
| feeds_rule_gate | MedClassHint | PatientProfile | 1:N | hypothesis | 未经医师确认只能作规则开闸的假设性输入，永不作诊疗根因 |
| starts_clock | TaperPlan | RemissionClock | 1:1 | derivation | day0 |
| gated_by_meds | RemissionClock | PatientProfile | 1:N | root_cause | 任一降糖药在用即清零，唯一判据 |
| assessed_with_lab | RemissionAssessment | LabResult | N:N | derivation | 同一方法学配对 |
| assessed_with_gmi | RemissionAssessment | CgmSummary | 1:N | hypothesis | GMI 是否可用还要核验四条前提，不能直接当根因 |
| triggers_settlement | ServicePackage | KpiSettlement | 1:1 | derivation | — |
| gated_by_safety_gate | KpiSettlement | CgmSummary | 1:N | root_cause | TBR 安全门一票否决 |
| grounded_by_exit | ChurnSignal | ServiceExitRecord | 1:N | root_cause | 退出记录是流失信号真假阳性的 ground truth |
| requires_consent_enroll | EnrollmentDecision | ConsentRecord | 1:1 | root_cause | 无单独同意即挂起，终止入组推理 |
| requires_consent_session | SensorSession | ConsentRecord | 1:N | root_cause | 授权前置于建 session，个人信息处理硬性前提 |
| cascades_from_revocation | ConsentRevocation | ConsentRecord | 1:1 | derivation | — |
| discloses_coverage | CarrierRegistry | PatientProfile | 1:1 | derivation | 覆盖状态供出口话术拦截读取 |
| paired_with_meal | MealResponse | ContextEvent | 1:1 | derivation | [t-60, t+180] 配对窗 |
| held_by | Credential | StoreEntity | 1:N | derivation | — |
| gated_by_readiness | ServicePackage | StoreReadinessCheck | 1:N | root_cause | 未完成清查的门店不予开通 |
| listed_as | ProductSku | StoreEntity | 1:N | derivation | — |
| delivered_as | OutboundContent | DeliveryReceipt | 1:1 | derivation | — |
| audited_by | AuditLog | PatientProfile | 1:N | derivation | 只进不出 |

共 **40** 条 Link。

> **edge_semantics 的判法**：本体里 `root_cause` 全部落在「命中即可终止推理」的硬闸上——授权、资质、值班链尾、去重后的触发读数、酮体阳性、TBR 安全门。`hypothesis` 只留给三处「还要再查一层才成立」的边：AI 草稿依据指标（要医师复核）、GMI 用于缓解判定（要核验四条前提）、患者自报用药线索（要医师确认）。其余是结构派生。

---

## 3. Functions（函数 / 派生量）— compiles to `FunctionDef`

| name | reads | returns | intent |
|---|---|---|---|
| TIR | GlucoseReading, PatientProfile | number:百分比 | 目标区间内读数占比。区间随 target_profile 切换：adult 3.9–10.0、elderly 3.9–10.0（目标值不同）、pregnancy 3.5–7.8。分子只计 source_channel ∈ {vendor_api, sdk_ble_direct, ble_gls_1808} 且 quality_flag=clean 的读数 |
| TAR_L1 | GlucoseReading | number:百分比 | >10.0 mmol/L 时间占比，分子口径同 TIR |
| TAR_L2 | GlucoseReading | number:百分比 | >13.9 mmol/L 时间占比，分子口径同 TIR |
| TBR_L1 | GlucoseReading, PatientProfile | number:百分比 | 3.0–3.8 mmol/L 时间占比（妊娠切 <3.5），分子口径同 TIR |
| TBR_L2 | GlucoseReading | number:百分比 | <3.0 mmol/L 时间占比 |
| MeanGlucose | GlucoseReading | number:mmol/L | 窗口内 clean 读数算术均值 |
| GMI | GlucoseReading, DeviceModel, ChannelRegistry, SensorSession | number:百分比 | GMI(%) = 3.31 + 0.02392 × mean(mg/dL)（Bergenstal 2018 官方公式，对外只用这一条，不用 uGMI）。四条前提全满足才计算：① 窗口读数 100% 来自单一厂商连续监测通道 ② 全窗口同 vendor 同 sensor_model ③ active% ≥70 且 days ≥14 ④ device_model.mard_pct 已在 channel_registry 登记。任一不满足返回 null，**不得用近似值填空** |
| CV | GlucoseReading | number:百分比 | SD ÷ MeanGlucose × 100 |
| SD | GlucoseReading | number:mmol/L | 窗口内 clean 读数标准差 |
| MAGE | GlucoseReading | number:mmol/L | 平均血糖漂移幅度，取振幅 >1×SD 的有效波动均值 |
| AGP分位曲线 | GlucoseReading, SensorSession | object | 14 天复合曲线：中位数 + 25–75% + 5–95% 分位带 + 逐日曲线，须披露 session 构成 |
| active_pct | GlucoseReading, ChannelRegistry | number:百分比 | **口径固定（confirmed-facts R-3）**：去重后 distinct 读数数 ÷ (窗口天数 × 1440 ÷ expected_sampling_interval)。采样间隔 5 分钟时分母即天数 × 288；公式引用 channel_registry 字段而不是硬编码 288。同一时刻多路只算一次 |
| wear_ratio | GlucoseReading, SensorSession | number:百分比 | 会话覆盖时长 ÷ 窗口总时长。**与 active_pct 不同义，两者不得互相引用**（metric_registry 治理项） |
| sufficiency_ok | GlucoseReading, ChannelRegistry | boolean | days ≥14 AND active_pct ≥70。只供结论层判定使用 |
| nocturnal_coverage_pct | GlucoseReading | number:百分比 | 00:00–06:00 窗口内按 active_pct 同口径计算。<70 置 nocturnal_coverage_insufficient，报告首屏显示。TODO(FDE)：夜间窗口边界（00:00–06:00 vs 23:00–07:00）上线前需临床拍板 |
| tz_uncertain | GlucoseReading | boolean | 窗口内 tz_provenance 非 device/vendor 来源占比超阈值时置位；命中则按本地时间切分的统计不出正式结论 |
| brand_changed | SensorSession | boolean | 窗口横跨传感器品牌/型号代际变更；命中禁止输出跨期比较结论 |
| hypo_episode_stats | GlucoseReading | object | 持续 ≥15 分钟的低血糖事件计数、时长、分级（Danne 2017 口径）。**仅用于回顾统计，永不用于实时触发**——与 R03a/R04a 的连续 2 读数口径物理分开 |
| meal_response_calc | GlucoseReading, ContextEvent | object | 配对窗 [t−60, t+180]，基线取 [t−60, t−15] 均值；输出 delta_p / time_to_peak / iAUC_2h / r2h / return_to_baseline。基线缺口 <20% 才出结论 |
| glucose_slope | GlucoseReading | number:mmol/L每分钟 | 近 15 分钟线性拟合斜率，供 R05/R06/R25/R26 使用 |
| sync_gap_risk | CarrierRegistry, SyncPlan | enum:低\|中\|高 | 距上次同步超过 sync_plan 预期间隔 ×1.5 时评估距传感器缓存深度还剩多远。TODO(FDE)：缓存深度参数待向硅基问定（confirmed-facts D-12），问定前按 24h 保守假设 |
| gmi_hba1c_consistency | GlucoseReading, LabResult | object | \|GMI − HbA1c\| 及一致性布尔值；≥0.5% 提示以实测 HbA1c 为准 |
| dedup_hit_rate | GlucoseReading | number:百分比 | 去重命中率与疑似重复率，供数据质量看板与去重失效自检 |
| hypo_risk_med | PatientProfile | boolean | meds ∩ {胰岛素, 磺脲, 格列奈} ≠ ∅ |
| target_profile_of | PatientProfile | enum:adult\|elderly\|pregnancy | 按 age≥65 / pregnant 解析人群维度，供全部阈值规则读取。**这是入参解析函数，不是分支硬编码** |
| service_tier_map | CgmSummary, PatientProfile | string | 德心 L0–L4 服务分层映射（内部标签）。前提：sufficiency_ok=true、非老年、非妊娠、非 confounded_window |
| churn_signal_coverage | ChurnSignal, PatientProfile | number:百分比 | 至少 1 个流失信号可计算的患者比例，按 health_tier/年龄分层；老年组 <50% 即预警"信号体系对该人群失效" |
| away_days | ContextEvent, CarrierRegistry | number:天 | away_mode 期间天数。**照常计入 R01 分母**，不得移出 |

共 **28** 个 Function。

---

## 4. Rules（规则 / 不变式）— compiles to `RuleDef` ★FDE 核心

本段共 **92 条**规则，按优先级带分布：元规则 1、低血糖 17、高血糖 6、波动与餐后 9、运动安全 6、人群与结论层 13、出口签发闸 14、器械/数据/机构合规 20、流程与显示口径 6。其中 **62 条 function-backed**、30 条 declarative。
表格前九列是 schema 规范列，编译器按此顺序取；末尾两列 `priority` / `phase` 是本项目扩展列，承载「规则优先级」与「生效阶段」两项本体语义（见 §4.1、§4.2）。

### 4.1 规则优先级带（priority band）与抢占语义

优先级不是注释，是 IR 的一等字段。`priority` 为整数，**数值小者先评估、先抢占**。带划分依据 AGP 读图顺序「先低血糖 → 再高血糖 → 再波动」（confirmed-facts A3-2；中国血糖监测临床应用指南 2021 读图顺序）。

| 带 | priority | 内容 | 抢占语义 |
|---|---|---|---|
| B0 元规则 | 99 | 低血糖优先抢占 | 编排其余各带的评估顺序与抑制关系 |
| B1 低血糖 | 100–199 | 实时触发、预测性、伪差过滤、夜间事件、睡前低值、TBR 超标、IAH、HAAF 复发窗 | **命中即抢占**：同评估周期内 B2/B3/B4 的建议类输出全部让位，只保留低血糖处置话术 |
| B2 高血糖 | 200–249 | 严重高血糖、SGLT2i 酮症、TAR 超标、TIR 未达标、黎明现象 | 抢占 B3/B4 |
| B3 波动与餐后 | 300–349 | CV 超标、GMI 一致性、PPGR、混叠排除、混杂窗口、去重自检 | 抢占 B4 |
| B4 运动安全 | 400–449 | 运动前低值/高值、运动中下降、餐后步行、运动后延迟低血糖 | 由运动事件触发，本质是 B1/B2 在运动语境下的变体 |
| B5 人群与结论层 | 500–569 | R01 数据门槛、老年/妊娠切换、服务分层、缓解判定与筛查、疑似 1 型红旗、夜间覆盖不足禁强化、器械交易合规 | **只关结论层**，不拦截 B1–B4 任何安全告警 |
| B6 出口签发闸 | 600–649 | 禁用词、产品功效、用药建议、分型直推、资质、反橡皮图章 | 作用于已成形的输出文本，最后一道闸 |
| B7 器械/数据/机构合规 | 650–748 | 22 条合规风险清单的落点 | 多为动作前置闸 |
| B8 流程操作性 | 750–769 | 告警兜底配置、覆盖告知留痕、同步策略、落库验证 | 防止服务在没人看得住的情况下悄悄开始 |

**三条硬语义**（由 `低血糖优先抢占` 这条 function-backed 元规则强制执行，不是文档约定）：

1. B1 命中时，B2–B5 产生的任何「加强降糖 / 限食 / 增加运动量」方向的建议一律抑制并留痕；
2. R01（B5）**不得**作为 B1–B4 的前置门——它只关闭结论层，安全通道照跑（confirmed-facts C-11）；
3. B6 出口闸门**不作用于紧急告警**，告警走预审冻结模板（confirmed-facts C-10）。

### 4.2 phase 取值

`P1` = 一期即生效；`P2` = 二期生效（实时告警链路，confirmed-facts B-13）；`P1+P2` = 两期都生效；`系统级` = 与患者分期无关的平台级前置条件。

### 4.3 Rules 全表

| name | severity | backing | evaluation | on_actions | intent | source | citations | check | priority | phase |
|---|---|---|---|---|---|---|---|---|---|---|
| 低血糖优先抢占 | hard | function | post_write | 生成方案草稿,生成AGP与指标报告,输出服务分层标签,生成结营报告 | 低血糖组命中时抑制同周期内一切加强降糖方向的输出，固定 AGP 读图顺序：低 → 高 → 波动 | 中国血糖监测临床应用指南 2021 读图顺序；ATTD 2019 AGP 规范 | confirmed-facts A3-2 | TODO(FDE): 查本次评估周期内 priority 落在 100–199 的规则命中集合，非空则抑制 priority ≥200 的**建议类**输出并写抑制留痕。**不作用于告警投递本身**——否则会出现低血糖优先规则把 B1 自己的告警当成待抑制输出的自反 bug | 99 | P1+P2 |
| R03a_Level2低血糖_实时告警 | hard | function | post_write | 触发低血糖处置,推送告警 | 连续 2 个读数确认 G<3.0 即触发，患者/健管师/群立即收到 15-15 处置指引，老年或独居加电话 | 国际低血糖研究组 IHSG；ADA Standards 2026 第 6 章 6.15 | daily-monitoring D8；confirmed-facts A3-6、C-01 | TODO(FDE): 查最近读数序列，校验是否出现连续 2 个读数（间隔 ≥5min）满足 G<3.0。**禁止复用 ≥15min 口径**，与 R03b 必须是两个独立函数签名 | 100 | P2 |
| R04a_Level1低血糖_实时告警 | hard | function | post_write | 触发低血糖处置,推送告警 | 连续 2 个读数确认 3.0≤G<3.9 即触发 | 同 R03a；15-15 法则 | daily-monitoring D9；confirmed-facts A3-6 | TODO(FDE): 查最近读数序列，校验连续 2 个读数（间隔 ≥5min）满足 3.0≤G<3.9 | 105 | P2 |
| R03b_Level2低血糖_回顾事件统计 | hard | function | post_write | 统计低血糖事件,生成AGP与指标报告,生成结营报告 | 持续 ≥15 分钟的 G<3.0 计一次事件，用于 TBR 统计与次日医师减药审查；一期是核心安全产出，二期是实时告警 ROI 基线 | Danne 2017 CGM 事件定义 | confirmed-facts A3-6、R-4；research/sources/02 §5.2 | TODO(FDE): 查连续读数窗口，校验是否存在持续 ≥15min 的 G<3.0 区间（起止均按时长判定）。**禁止复用 R03a 的 2 读数口径** | 110 | P1+P2 |
| R04b_Level1低血糖_回顾事件统计 | hard | function | post_write | 统计低血糖事件,生成AGP与指标报告,生成结营报告 | 持续 ≥15 分钟的 3.0≤G<3.9 计一次事件 | Danne 2017 CGM 事件定义 | confirmed-facts A3-6、R-4 | TODO(FDE): 查连续读数窗口，校验是否存在持续 ≥15min 的 3.0≤G<3.9 区间 | 115 | P1+P2 |
| R02_传感器压迫伪差识别 | soft | function | post_write | 去重与通道仲裁,统计低血糖事件 | 单点 <3.0 但前后 10min 内回升 ≥1.5，或 15min 内跳变 >5.0，判伪差不计入事件。**伪差判定不得抑制 hard 级告警发出** | Danne 2017 CGM 事件定义 | research/sources/02 §8 R02；domain-canvas §3.6 | TODO(FDE): 查该读数前后 10min 窗口，校验是否满足回升 ≥1.5 mmol/L 或 15min 内跳变 >5.0 mmol/L | 120 | P1+P2 |
| R05_即将低血糖预测告警 | hard | function | post_write | 触发低血糖处置,推送告警 | 预测性告警，提前 10–30 分钟提示补 10–15g 碳水并暂停运动。负时延正是二期的价值来源 | Aleppo 2017 趋势箭头共识 | research/sources/02 §5.4、§8 R05；confirmed-facts C-01 | TODO(FDE): 查近 15min 斜率，校验 G<5.0 且 slope≤−1，或 G + slope×20 < 3.9 | 125 | P2 |
| R06_快速下降箭头提示 | soft | declarative | post_write | 推送告警 | 双下箭且血糖已偏低时提示 15 分钟后复看，不建议大量补碳水以免反跳 | Aleppo 2017 趋势箭头共识 | research/sources/02 §5.4 | slope <= -2 AND G < 7.0 | 130 | P2 |
| R07_夜间低血糖事件 | hard | function | post_write | 统计低血糖事件,生成去强化证据工单 | 00:00–06:00 窗口内持续性低血糖；3 天内 ≥2 次升级医师复核晚间用药与晚餐 | Endocrine Society 2022 低血糖指南；中国老年糖尿病诊疗指南 2024 | daily-monitoring D11；research/sources/02 §8 R07 | TODO(FDE): 查 00:00–06:00 窗口连续读数，校验是否存在持续 ≥15min 的 G<3.9 区间；并查过去 3 天该窗口事件次数 | 135 | P1+P2 |
| R08_睡前低值预警 | soft | function | post_write | 推送告警,生成方案草稿 | 睡前窗口均值低于分层下限且用药含胰岛素或磺脲时，建议 10–15g 含碳水加餐并复测。**加餐种类不得是黄瓜**（门店旧口径已纠正） | 中国老年糖尿病诊疗指南 2024；门店经验（已修正加餐种类） | research/sources/02 §5.5、§8 R08；daily-monitoring D12 | TODO(FDE): 查 health_tier 与 meds，校验 21:00–23:00 窗口均值 < 分层下限（老年良好 5.0 / 中等 5.6 / 差 8.3；非老年 5.0）且 meds ∩ {胰岛素, 磺脲} ≠ ∅ | 140 | P1+P2 |
| R09_TBR超标触发去强化审查 | hard | function | post_write | 生成AGP与指标报告,生成去强化证据工单,生成结营报告 | 报告首行标红「低血糖优先」，并必出低血糖事件明细表置于第一页，提交医师降糖药去强化审查 | ATTD 2019；中国老年糖尿病诊疗指南 2024 | research/sources/02 §5.6、§8 R09；review-and-plan D3 | TODO(FDE): 查 14 天窗口 TBR_L1 与 TBR_L2 占比，校验 TBR<3.9 ≥4%（老年/高危 ≥1%）或 TBR<3.0 ≥1%，或 14 天内 L2 事件 ≥1 次。**事件计数只取 hypo_episode_stats（回顾口径），不接实时告警日志**，否则会虚高医师去强化审查证据表里的事件条数 | 145 | P1+P2 |
| R10_低血糖无感知线索 | soft | function | post_write | 生成去强化证据工单,配置患者告警与静音策略 | Level 2 事件发生但无患者症状标记 ≥2 次/14 天，提示医师评估无感知低血糖 | Endocrine Society 2022 低血糖指南 | research/sources/02 §8 R10；behavior-matrix §7.1 G7 | TODO(FDE): 查 14 天内 L2 事件记录，校验其中 ≥2 次无伴随的 SymptomTreatmentRecord | 148 | P1+P2 |
| R46_IAH高危阈值上调且禁止静音 | hard | declarative | pre | 配置患者告警与静音策略 | 无感知低血糖高危人群阈值上调至 4.4 且保留告警，不可一律夜间静音。人群维度是入参不是分支硬编码 | Endocrine Society 2022 低血糖指南 | confirmed-facts A3-7、C-05 | is_iah_high_risk is not True or (alert_threshold >= 4.4 and night_mute_allowed is False) | 149 | P1+P2 |
| R34_HAAF_24小时复发窗 | hard | function | post_write | 更新低血糖状态机,收紧告警阈值 | 24 小时内已发生 Level 2 事件即进入 HAAF 高危窗口：阈值上调 4.4、夜间强制人工巡检、当日禁运动建议、医师复核任务 | Endocrine Society 2022（HAAF 机制） | daily-monitoring D12b | TODO(FDE): 查过去 24h 内 L2 事件，**只计 hypo_episode_stats 产出的回顾事件（R03b/R04b 口径），不得接 R03a/R04a 的实时触发计数**，否则伪差重复触发会把 HAAF 窗口频繁误开；校验是否 ≥1 次，命中则置 recurrence_window 并联动 R46 阈值 | 150 | P1+P2 |
| R44_高危用药禁止闭环 | hard | function | pre | 响应并回执告警 | 磺脲或长效/预混胰岛素使用者的低血糖不得按一次复测回升就闭环 | TODO(FDE): 补依据（机制方向由 Endocrine Society 2022 与中国糖尿病防治指南 2024 用药章节支持，但"可持续 24–72 小时"这个具体时长在两份基准文档里均无逐字出处） | daily-monitoring D21；behavior-matrix §6 hypo_state | TODO(FDE): 查 HypoState.closure_blocked_reason 与 meds ∩ {磺脲, 长效胰岛素, 预混胰岛素}，任一命中则拒绝写入 alert.resolved | 155 | P1+P2 |
| R57_15-15三轮无效强制升级就医 | hard | function | post_write | 响应并回执告警,推送告警 | 15-15 法则重复 3 轮仍未回升，或症状持续 30–45 分钟，立即升级至就医/120 并通知紧急联系人。**这是处置链条最危险的一环，此前 87 条里没有一条兜住** | 国际低血糖研究组 IHSG；15-15 法则；ADA Standards 2026 第 6 章 | research/sources/02 §5.1；daily-monitoring D21；临床复核补充 | TODO(FDE): 查该告警的 15-15 循环轮次与症状标记持续时长，校验轮次 ≥3 且复测仍 <3.9，或症状持续 ≥30 分钟 | 152 | P1+P2 |
| R58_Level3严重低血糖强制转诊 | hard | function | post_write | 记录症状与处置,推送告警,转介医师 | Level 3（需他人协助的严重低血糖）**定义上不依赖血糖数值**，命中即强制触发就医与医师复核工单，不看当前 G 值 | 国际低血糖研究组 IHSG Level 3 定义；ADA Standards 2026 第 6 章 | research/sources/02 §5.1；临床复核补充 | TODO(FDE): 查 SymptomTreatmentRecord 是否含需他人协助/意识改变/抽搐类标记，命中即触发，**不得附加任何血糖阈值前置条件** | 153 | P1+P2 |
| R59_老年非典型症状疑似低血糖 | soft | function | post_write | 记录症状与处置,生成去强化证据工单 | 老年低血糖常表现为跌倒、意识模糊、叫不醒、胡言乱语，而不是出汗心悸。这类记录若同期 CGM 处于临界低值区间，提示疑似低血糖诱因并推医师复核 | 中国老年糖尿病诊疗指南 2024；Endocrine Society 2022 | daily-monitoring D28；research/sources/02 §5.5；临床复核补充 | TODO(FDE): 查 age≥65 患者近期跌倒/意识行为改变类症状标记，并查同期 CGM 是否处于临界低值区间（<4.4），命中则出疑似提示 | 154 | P1+P2 |
| R11_严重高血糖 | hard | function | post_write | 触发低血糖处置,推送告警,生成方案草稿 | G>16.7 持续 ≥1h，或 G>13.9 伴口渴多尿恶心，提示查血酮，阳性或有症状转就医，暂停运动与产品推荐 | 中国糖尿病防治指南 2024（不宜运动阈值）；Colberg 2016 ADA 运动立场 | research/sources/02 §8 R11；daily-monitoring D13 | TODO(FDE): 查最近读数窗口，校验 G>16.7 持续 ≥1h，或 G>13.9 且存在同期症状标记 | 200 | P1+P2 |
| R12_SGLT2i酮症警觉 | hard | function | post_write | 推送告警,记录酮体 | SGLT2i 使用者在极低碳水、长时间运动或恶心乏力情形下，血糖不高也可能酮症（euDKA） | TODO(FDE): 补依据（药物机制层面成立，但需补 SGLT2i euDKA 的权威指南条目） | research/sources/02 §6.4、§8 R12；behavior-matrix §7.1 G1b | TODO(FDE): 查 meds 或 MedClassHint.sglt2i 是否为真，并查是否存在极低碳水标记/长时间运动标记/恶心乏力症状标记，且当前 G 不高 | 205 | P1+P2 |
| R13_TAR_L2超标 | soft | function | post_write | 生成AGP与指标报告,生成方案草稿 | TAR>13.9 占比超标，生成"哪些时段/餐次贡献最多"的归因分析交医师 | ATTD 2019 | research/sources/02 §8 R13 | TODO(FDE): 查 14 天窗口 TAR_L2 占比，校验 ≥5%（老年 ≥10%） | 210 | P1+P2 |
| R14_TAR_L1超标 | soft | declarative | post_write | 生成方案草稿 | TAR>10.0 占比 ≥25%，给饮食/运动/服药时机建议 | ATTD 2019 | research/sources/02 §8 R14 | TAR_L1 < 25 | 215 | P1+P2 |
| R15_TIR未达标 | soft | declarative | post_write | 生成AGP与指标报告,生成方案草稿 | TIR 未达标，把差距换算成小时（每 5% ≈ 1.2h/天）并建议复诊 | ATTD 2019；中国糖尿病防治指南 2024 | research/sources/02 §8 R15 | (target_profile == 'adult' and TIR >= 70) or (target_profile in ('elderly','high_risk') and TIR >= 50) or (target_profile == 'pregnancy' and TIR >= 70) | 220 | P1+P2 |
| R22_黎明现象 | soft | function | post_write | 生成方案草稿,转介医师 | 03:00 最低值到 07:00 上升明显且无夜间加餐，提示医师调整基础胰岛素或晚餐 | TODO(FDE): 补依据（研究文档标注为"临床常规定义"，需补权威出处） | research/sources/02 §8 R22 | TODO(FDE): 查 03:00 最低值与 07:00 读数，校验上升 ≥1.1 mmol/L 且无夜间加餐标记，14 天内 ≥50% 天数满足 | 225 | P1+P2 |
| R16a_波动超标_硬 | hard | declarative | post_write | 生成AGP与指标报告,生成方案草稿 | CV>36% 判波动过大，需联动低血糖与餐后归因 | ATTD 2019 | research/sources/02 §8 R16 | CV <= 36 | 300 | P1+P2 |
| R16b_波动偏高_软_中国口径 | soft | declarative | post_write | 生成AGP与指标报告,生成方案草稿 | 33% < CV ≤ 36% 提示波动偏高，中国人群本土证据阈值 | 中国血糖监测临床应用指南 2021（CV>33% 与低血糖风险升高相关） | research/sources/02 §2.1、§8 R16 | CV <= 33 or CV > 36 | 305 | P1+P2 |
| R17_GMI与HbA1c不一致 | soft | function | post_write | 生成AGP与指标报告,判定缓解结果 | 偏差 ≥0.5% 时提示以实测 HbA1c 为准，标注可能贫血或血红蛋白变异 | Bergenstal 2018；Diabetes Care 2024 GMI 差异评论 | research/sources/02 §1.1、§8 R17；review-and-plan D7 | TODO(FDE): 先校验 GMI 四条计算前提（单一厂商连续通道、同 vendor 同 sensor_model、active%≥70 且 days≥14、剔除 warmup 与末期衰减段）与实测 HbA1c 距今 ≤3 个月；前提不满足则 GMI 置 null 且本规则跳过；满足则校验 abs(GMI − HbA1c) ≥ 0.5 | 310 | P1+P2 |
| R19_餐后高响应 | soft | function | post_write | 计算餐后响应,生成方案草稿 | 单餐响应超标，同类餐重复 ≥2 次才触发饮食顺序/份量/搭配/餐后步行建议 | Howard 2022 CGM 效度与重复性研究 | research/sources/02 §4.2、§8 R19 | TODO(FDE): 查该患者同类餐历史，校验 delta_p ≥2.8 或 peak ≥10.0 或 return_to_baseline 为 false（**不要用 r2h ≥1.7**——1.7 是 ΔP 分级表的分界值，源文档从未给过 r2h 的数值切点），且同类餐已出现 ≥2 次 | 315 | P1+P2 |
| R20_餐后极高响应 | soft | function | post_write | 计算餐后响应,推送告警 | 餐后响应达到 TAR L2 级别，联动 R13 并推送健管师 | ATTD 2019 分级 | research/sources/02 §8 R20 | TODO(FDE): 查该餐 MealResponse，校验 delta_p ≥4.4 或 peak ≥13.9 | 320 | P1+P2 |
| R21_餐次数据混叠排除 | hard | function | pre | 计算餐后响应 | 与上一餐或加餐间隔 <2h，曲线重叠不可信，该餐不计入个人食物排序 | Howard 2022 CGM 效度与重复性研究 | research/sources/02 §8 R21；review-and-plan D6 | TODO(FDE): 查该餐与前一餐/加餐记录，校验时间间隔是否 <2h | 325 | P1+P2 |
| R47_跨品牌配对排除 | hard | declarative | pre | 计算餐后响应,生成AGP与指标报告 | 跨品牌/跨型号代际的读数不得用于个体化餐后结论与跨期比较（跨品牌误分类率约 19%） | Howard 2022；ATTD 2019 报告标准化 | review-and-plan D6；behavior-matrix §6 metric_registry | cross_brand is not True and brand_changed is not True | 328 | P1+P2 |
| R36_active率超100自检 | hard | declarative | post_write | 去重与通道仲裁,计算窗口指标 | active% > 100% 是去重失效唯一且极灵敏的自检信号，一期即上线红色告警 | 通用（工程自检口径） | confirmed-facts R-3 | active_pct <= 100 | 335 | P1+P2 |
| R48_去重键必须用传感器序号 | hard | function | pre | 去重与通道仲裁,摄入读数 | 去重键一期就用传感器侧序号，不用厂商记录 ID，也不单独用可空的 device_time。这是四条一期强制预留里唯一不可逆的一条 | 通用（confirmed-facts R-1 工程决策，依据 A1-6 硅基确认读数默认带传感器侧序号） | confirmed-facts A1-6、R-1 | TODO(FDE): 校验 dedup_key 是否以 sensor_serial + 序号构成；无序号时才允许退到 ±90 秒容差兜底并置 weak_dedup 标记 | 340 | P1+P2 |
| R23_运动前低值 | hard | function | post_write | 推送告警,记录餐食与运动事件 | 运动前 G<5.0 须先补 15–30g 碳水，复测 ≥5.0 才可运动 | Colberg 2016 ADA 运动立场；ADA 患者运动指导 | research/sources/02 §8 R23；daily-monitoring D16 | TODO(FDE): 查运动打卡或加速度计事件前的最近读数，校验 G<5.0 | 400 | P2 |
| R24a_运动前高值查酮体 | hard | function | post_write | 推送告警,记录酮体 | 13.9 < G ≤ 16.7：先查酮体，阳性禁运动，阴性仅低–中强度 | Colberg 2016 ADA 运动立场 | research/sources/02 §8 R24 | TODO(FDE): 查运动打卡前最近读数，校验 13.9 < G <= 16.7，并查是否已有 KetoneReading | 405 | P2 |
| R24b_运动前极高值一律不宜运动 | hard | function | post_write | 推送告警 | G>16.7 无论酮体阴阳性一律不宜运动。R11 要求持续 ≥1h，而运动前是即时判断，不能等一小时 | 中国糖尿病防治指南 2024（不宜运动阈值）；中国 2 型糖尿病运动治疗指南 2024 | research/sources/02 §6.1、§8 R11/R24；临床复核补充 | TODO(FDE): 查运动打卡前最近读数，校验 G > 16.7；命中即拒绝运动建议，不进入酮体分支 | 406 | P2 |
| R25_运动中下降 | hard | function | post_write | 推送告警 | 运动期间快速下降或已进入警戒值，提示停止运动并补碳水 | ADA Standards 2026 运动期监测建议；Colberg 2016 | research/sources/02 §8 R25 | TODO(FDE): 查运动会话期间斜率，校验 slope ≤ −1.5 或 G < 4.4 | 410 | P2 |
| R26_餐后步行提醒 | soft | function | post_write | 推送告警 | 餐后 15–30 分钟且血糖上行时提示走 10–20 分钟 | Sci Rep 2025 餐后运动研究；Sports Med 2018 餐后运动综述 | research/sources/02 §6.3、§8 R26 | TODO(FDE): 查餐开始时间，校验当前处于餐后 15–30min 窗口且 slope > 1 | 415 | P1+P2 |
| R27_运动后延迟低血糖 | soft | function | post_write | 收紧告警阈值,生成方案草稿 | 胰岛素或磺脲使用者当日运动 ≥45 分钟，当晚睡前目标上调 >5.6，夜间告警阈值上调至 4.4 | TODO(FDE): 补依据（research/sources/02 §9 待核实清单第 2 条，Colberg 2016 原文阈值待逐字核对） | research/sources/02 §8 R27 | TODO(FDE): 查当日运动记录，校验时长 ≥45min 且 meds ∩ {胰岛素, 磺脲} ≠ ∅ | 420 | P1+P2 |
| R01_数据充分性门槛_仅管结论层 | hard | declarative | pre | 生成AGP与指标报告,输出服务分层标签,判定缓解结果,生成结营报告,兑现结果承诺 | 14 天 + ≥70% 有效数据不满足则只出趋势描述，禁出达标/分层/缓解结论。**明确不覆盖 R03a/R04a/R05/R11/R23–R25 等安全告警路径**——它不是全局前置门 | ATTD 2019；中国血糖监测临床应用指南 2021 | research/sources/02 §8 R01；confirmed-facts A3-1、C-11；review-and-plan D1 | days >= 14 and active_pct >= 70 | 500 | P1+P2 |
| R28_老年目标切换 | hard | declarative | pre | 入组判定,计算窗口指标,生成AGP与指标报告 | age≥65 切老年三分层目标：TIR>50%、TBR<1%、TAR>13.9 <10%。人群维度是规则入参 | 中国老年糖尿病诊疗指南 2024 | confirmed-facts A3-5；research/sources/02 §8 R28 | age < 65 or target_profile == 'elderly' | 505 | P1+P2 |
| R31_妊娠模式切换 | hard | declarative | pre | 入组判定,计算窗口指标,输出服务分层标签 | pregnant 切目标区间 3.5–7.8、TIR>70%、TBR<4%，并禁用德心分层与营养产品推荐 | ATTD 2019 妊娠目标表 | research/sources/02 §1.1、§8 R31 | pregnant is not True or (target_profile == 'pregnancy' and service_tier_enabled is False) | 510 | P1+P2 |
| R42_急性混杂窗口禁止出结论 | hard | function | post_write | 输出服务分层标签,生成方案草稿,判定缓解结果,生成结营报告 | 急性病、感染发热、糖皮质激素等升糖药、住院、用药调整期内的数据不做分层、不出个性化饮食结论、不作缓解或续约依据，只出趋势描述 | research/sources/02 §3.2 分层前提「不在急性病/用药调整期」 | review-and-plan D2b；behavior-matrix §7.1 G6 | TODO(FDE): 查窗口内 ClinicalContextEvent，校验是否存在急性病/感染发热/激素/住院/用药调整标记，命中则置 confounded_window | 508 | P1+P2 |
| R49_缺参数时按最保守执行 | hard | declarative | pre | 计算窗口指标,生成方案草稿,推送告警 | 人群参数缺失时不得回落一般成人阈值，须按最保守（老年/高危）执行并置 population_params_stale | 通用（domain-canvas 架构护栏「D2 不得在缺参数时回落一般成人阈值」） | domain-canvas §3.6；behavior-matrix §7.1 G1 | age is None or health_tier is not None or target_profile == 'elderly' | 512 | P1+P2 |
| R18_CGM服务分层_内部标签 | soft | function | post_write | 输出服务分层标签 | 德心 L0–L4 映射，只作服务分层内部标签，对外措辞"提示区间，需医生确认"，**不得表述为诊断** | research/sources/02 §3 德心映射表；中国糖尿病防治指南 2024 诊断切点 | confirmed-facts A3-3；research/sources/02 §3.2、§8 R18 | TODO(FDE): 查 FG_cgm（14 天中位数）、PP2h_cgm（14 天 75 分位）、GMI、TAR 等指标，前提校验 R01 已过、target_profile 非 elderly 非 pregnancy、非 confounded_window，按 §3.2 表判 L0–L4，冲突取更严一级 | 515 | P1+P2 |
| R29_缓解判定 | hard | function | post_write | 判定缓解结果 | 停用全部降糖药 ≥90 天且 HbA1c<6.5%（GMI<6.5% 可替代）才标记缓解，否则禁用"缓解/逆转"字样 | ADA 2021 缓解共识；缓解 2 型糖尿病中国专家共识 2021 | confirmed-facts A3-4；research/sources/02 §7.1、§8 R29；remission-assessment D6/D8 | TODO(FDE): 查 RemissionClock 是否 ≥90 天且期间无任何降糖药（含二甲双胍）记录，并查 HbA1c 或 GMI 是否 <6.5%；GMI 替代须先满足 R17 的四条前提 | 520 | P1+P2 |
| R30_缓解适宜人群筛选_ABCD | soft | function | post_write | 入组判定,判定缓解结果 | 抗体阴性 AND (BMI≥25 或腰围男>90/女>85) AND 空腹 C 肽≥1.1 且餐后 2h C 肽≥2.5 AND 病程≤5 年，四条全满足才可进缓解路径 | 缓解 2 型糖尿病中国专家共识 2021（ABCD 标准） | research/sources/02 §7.1、§8 R30；enrollment D5 | TODO(FDE): 查抗体检验、BMI 或腰围、空腹 C 肽 ≥1.1 与餐后 2h C 肽 ≥2.5、病程 ≤5 年，校验四条同时满足。⚠ confirmed-facts A3 只收录了空腹 C 肽一项，餐后 2h C 肽 ≥2.5 来自 research/sources/02 §7.1 与 processes/enrollment D5——**这是基准文件的漏收，须回补 confirmed-facts，不得静默采用** | 525 | P1+P2 |
| R33_停药观察期反弹预警 | hard | function | post_write | 判定缓解结果,转介医师 | 停药后血糖恶化或安全事件早期预警，立即推医师并触发病因排查 | TODO(FDE): 补依据（remission-assessment D4 自标"阈值待临床确认，建议固化为 R33"，未经临床签字不得上线） | remission-assessment D4 | TODO(FDE): 查是否命中任一：连续 7 天平均葡萄糖 ≥8.6（不得标称 GMI）、14 天滚动 GMI ≥7.0%、TAR>10.0 连续 7 天 ≥50%、G>16.7 持续 ≥1h、症状或酮体阳性、停药后任一 L1 及以上低血糖事件、体重非计划下降 + 血糖恶化 + 酮体阳性 | 530 | P1+P2 |
| R37_疑似1型LADA红旗 | hard | function | post_write | 入组判定,生成方案草稿,评估可否停药并签发减停计划 | 命中即冻结一切减停药与缓解话术、禁推 C 包，先开抗体与 C 肽，结果回报前不解冻 | 缓解 2 型糖尿病中国专家共识 2021 ABCD-A 项 | enrollment D1；research/sources/02 §7.1 | TODO(FDE): 查起病年龄<40、BMI<24 消瘦、近期非计划体重快速下降、既往酮症或 DKA、口服药迅速失效、一级亲属 1 型病史等标记，任一命中即冻结（具体诊断标准另需补权威出处） | 535 | P1+P2 |
| R35_夜间覆盖不足禁强化 | hard | declarative | post_write | 生成方案草稿,生成AGP与指标报告 | 夜间有效覆盖 <70% 时置 nocturnal_coverage_insufficient 并在报告首屏显示，**禁止生成任何强化降糖方向的草稿**。夜间缺口会让 TBR 被系统性低估，医师在一个低估了低血糖的数据集上加药，是老年严重低血糖的经典成因 | 通用（confirmed-facts「一期特有医源性伤害路径」三条对策之一，临床评审新发现） | confirmed-facts §C 末尾对策 ①②；机会评估 | nocturnal_coverage_pct >= 70 or plan_direction != '强化' | 540 | P1+P2 |
| R50_夜间低覆盖高危用药进临床队列 | hard | declarative | post_write | 生成去强化证据工单 | 用胰岛素或磺脲，且连续 ≥2 晚夜间有效率 <50% 的患者，进临床队列低血糖分支，**不是挽留队列** | 通用（confirmed-facts「一期特有医源性伤害路径」对策 ③） | confirmed-facts §C 末尾对策 ③ | not (hypo_risk_med and consecutive_low_night_nights >= 2) or queue == 'clinical_hypo' | 542 | P1+P2 |
| R41_器械交易主体与收货合规 | hard | function | pre | 记录到店随机指血分诊,建立传感器会话 | 销售主体须持证、票据抬头与收货人均为患者本人、门店无器械库存记录、无按销量返佣 | 医疗器械经营监督管理办法；医疗器械监督管理条例第 40–42 条 | enrollment D8；confirmed-facts B-1；research/sources/04 §6 风险 1 | TODO(FDE): 查销售主体资质、票据抬头与收货人、门店库存记录与返佣配置 | 545 | P1+P2 |
| R32_产品推荐合规闸 | hard | declarative | post_write | 生成产品推荐,审核输出内容 | 产品推荐不得与服务分层结论、"缓解/逆转"字样同句出现，且必须附"固体饮料，不替代药物"尾注 | 广告法第 17 条；食品安全法第 73 条；总局 2021 年第 46 号公告 | research/sources/02 §8 R32；confirmed-facts A2-4、B-2 | not (has_product_recommendation and (same_sentence_has_tier_label or same_sentence_has_remission_word)) and disclaimer_attached is True | 600 | P1+P2 |
| D8_禁用词拦截 | hard | declarative | post_write | 审核输出内容,群内答复患者,发布宣传素材 | 逆转/治愈/停药/疗程/修复胰腺/降血糖/MNT 医学营养治疗等词一律拦截重写，2 次不过转人工 | 食品安全法第 71、73 条；广告法第 17、28、55 条；反不正当竞争法第 9 条；总局 2021 年第 46 号公告第 4 条 | review-and-plan D8；research/sources/04 §6 风险 13 | banned_term_hits == 0 | 605 | P1+P2 |
| C9_AI方案禁止直接推送 | hard | function | pre | 推送方案至患者 | AI 只出草稿，医师或注册营养师签发后才能推送。这是产品能合法存在的前提 | 互联网诊疗监管细则第 13、21 条；医师法；医疗机构管理条例实施细则第 88 条 | research/sources/04 §6 风险 9；confirmed-facts A2-3、B-3 | TODO(FDE): 查该 PlanDraft 是否已存在有效 PlanSigned（签发人资质有效、签发时间戳与依据快照齐备），未签发一律拒绝推送 | 610 | P1+P2 |
| D9_产品功效声称拦截 | hard | declarative | post_write | 审核输出内容,生成产品推荐,发布宣传素材 | 出现营养食品推荐时，与分层或缓解同句即硬拦截，否则强制尾注 | 食品安全法第 71、73 条；广告法第 17、28 条 | review-and-plan D9；research/sources/04 §6 风险 13 | not (has_product_recommendation and (same_sentence_has_tier_label or same_sentence_has_remission_word)) | 615 | P1+P2 |
| D10_用药建议拦截 | hard | function | post_write | 审核输出内容,群内答复患者,生成方案草稿 | 药名 + 剂量/加减停/换药动词一律硬拦截并转医师任务，健管师与 AI 均不得答 | 互联网诊疗监管细则第 21 条；医师法（处方权） | review-and-plan D10；daily-monitoring D26；research/sources/04 §6 风险 10 | TODO(FDE): 对生成文本做实体识别，校验是否出现药名 + 剂量或加减停或换药的建议性表述 | 618 | P1+P2 |
| D11_未确认分型分级措辞拦截 | hard | function | post_write | 审核输出内容,输出服务分层标签 | 出现"你是 X 型/X 级糖尿病"式确定性措辞须降级或移除；CGM 不能用于诊断 | 医疗机构管理条例实施细则第 88 条；ADA/CDS 均无 CGM 诊断条目 | confirmed-facts A3-3；review-and-plan D11；research/sources/04 §6 风险 11 | TODO(FDE): 检测文本是否出现"诊断/确诊/X 型糖尿病/X 级"等确定性措辞，命中则降级为"提示区间"表述 | 620 | P1+P2 |
| R51_分层结论默认不可披露患者 | hard | declarative | pre | 推送方案至患者,输出服务分层标签,群内答复患者 | tier_label 必与 disclosure_approved 同表且默认 false，未经医师披露授权不得直推患者。理由链：直推等于以非诊断手段作出诊断化表述 | 互联网诊疗监管细则第 21 条；医疗机构管理条例实施细则第 88 条（直推构成无证诊断时适用） | confirmed-facts A2-3、B-3；behavior-matrix §6/§8；domain-canvas §3.5 ③ | not includes_tier_label or disclosure_approved is True | 622 | P1+P2 |
| D11a_签发人资质失效自动冻结 | hard | function | pre | 签发方案,评估可否停药并签发减停计划,判定缓解结果 | 执业证/多点执业备案/注册证/康复师资质任一过期即自动冻结签发权限，任务转有资质人员 | TODO(FDE): 补依据（执业资格核验，需补《医师法》与营养师注册管理的具体条款号） | review-and-plan D11a；domain-canvas D18 | TODO(FDE): 查签发人 Credential 记录，校验类型与内容归属匹配且 status == valid 且未过期 | 625 | P1+P2 |
| D12_签发人归属分流 | hard | function | pre | 签发方案 | 用药或分型 → 医师；营养 → 注册营养师且不含用药；运动 → 康复师起草 + 医师筛查运动禁忌后双签发；教育 → 健管师 | 医师法；临床营养师与康复治疗师执业范围规定 | review-and-plan D12；behavior-matrix §8.1 | TODO(FDE): 按 PlanDraft 内容分类与签发人 Credential 类型做匹配校验；运动类须存在医师禁忌筛查记录 | 628 | P1+P2 |
| R45_紧急告警豁免关键词闸 | hard | declarative | pre | 推送告警 | 低血糖处置话术天然含"胰岛素/磺脲/停"字样，词库误命中会吃掉致命告警。**只豁免关键词与实体识别类闸门（D8/D9/D10/D11），不豁免 C22 免责尾注与 R54 夜间承诺红线**——这两条改由 R56 在模板预审阶段兜住 | 通用（domain-canvas 临床评审推翻了"所有对外输出经统一闸门"的初稿设计） | confirmed-facts C-10；domain-canvas §3.6 | content_type != '告警' or keyword_gates_applied is False | 630 | P1+P2 |
| R56_告警模板预审冻结 | hard | function | pre | 推送告警 | 告警话术不走运行时闸门，改为模板预先审定并冻结；模板准入时必须一次性满足免责尾注与夜间承诺红线，之后运行时只允许套用已冻结模板，不允许现场生成 | 通用（confirmed-facts C-10 的配套机制：豁免运行时闸门的前提是模板已过预审） | confirmed-facts C-10、B-11；domain-canvas §3.6 | TODO(FDE): 查该告警使用的模板是否在已冻结模板库内，且该模板的预审记录同时通过 C22_免责声明强制展示 与 R54_服务话术不得含夜间安全承诺 | 631 | P1+P2 |
| R52_回填读数不得触发实时告警 | hard | declarative | pre | 推送告警,触发低血糖处置 | 回填 14 天历史会把三周前的低血糖当实时危急值推进群里。is_backfill 读数只进统计通道 | 通用（domain-canvas 架构护栏「D4 ⇏ is_backfill 读数」） | domain-canvas §3.6；behavior-matrix E53 | is_backfill is not True | 632 | P1+P2 |
| R53_低置信通道不得独立触发危急告警 | hard | declarative | pre | 推送告警,触发低血糖处置 | OCR 与手工录入不得独立触发危急告警，须先指血复测或健管师加急复核确认。未复核的单位误读会制造大量假低血糖 | 通用（daily-monitoring D7a 防假危急外呼链） | daily-monitoring D7a；domain-canvas §3.6 | source_channel in ('vendor_api','sdk_ble_direct','ble_gls_1808') and source_confidence >= 0.95 | 634 | P1+P2 |
| D13_签发反橡皮图章检测 | soft | function | post_write | 签发方案 | 停留 <20 秒标 review_suspicious，连续 10 份零修改触发质控复核。系统不提供"批量全部通过"按钮 | 通用（内部质控 SOP，反橡皮图章） | review-and-plan D13；confirmed-facts C-07 | TODO(FDE): 查该签发人近期 ReviewEvidence，校验 dwell_time 与修改率是否落入可疑阈值 | 638 | P1+P2 |
| C1_器械经营资质闸 | hard | function | pre | 上架产品SKU,创建服务包SKU | 门店与平台均无三类经营许可，CGM 交易只能由持证厂商或经销商完成，门店纯引流不碰货不收款 | 医疗器械监督管理条例第 40–42、84 条；医疗器械网络销售监督管理办法 | research/sources/04 §6 风险 1；confirmed-facts A2-1、B-1 | TODO(FDE): 查交易主体是否持《医疗器械经营许可证》及网络销售备案 | 650 | P1+P2 |
| C2_网络销售备案与证照公示 | hard | function | pre | 上架产品SKU | 器械类 SKU 须单独频道并展示经营许可证与注册证，无证不上架 | 医疗器械网络销售监督管理办法第 8、11 条 | research/sources/04 §6 风险 2 | TODO(FDE): 查该 SKU 对应的经营许可证与注册证是否已在页面公示 | 655 | P1+P2 |
| C3_敏感个人信息单独同意 | hard | function | pre | 摄入读数,建立传感器会话,标记入组成功 | 血糖与用药属敏感个人信息，须单独同意 + 逐项勾选 + 电子签名 + 时间戳落库，未取得则服务挂起、零数据摄入 | 个人信息保护法第 28、29、30 条 | confirmed-facts A2-2；enrollment D9；research/sources/04 §6 风险 3 | TODO(FDE): 查该患者 ConsentRecord 的 scope_items 是否覆盖本次处理目的，且七项独立勾选未被合并 | 660 | P1+P2 |
| C4_数据用于产品推荐须单独同意 | hard | function | pre | 生成产品推荐 | 营销用途须单独勾选，推荐可关闭，自动化决策提供人工复核入口 | GB/T 39725 第 7 章；个人信息保护法第 24 条（自动化决策） | research/sources/04 §6 风险 4 | TODO(FDE): 查营销用途单独同意是否存在且未撤回，并校验该推荐是否提供关闭与人工复核入口 | 665 | P1+P2 |
| C5_厂商云对接协议与PIPIA | hard | function | pre | 建立厂商云通道对接 | 云对接前须签数据接收协议、完成 PIPIA，处理记录保存 3 年 | 个人信息保护法第 21、23、55 条；网络数据安全管理条例第 12 条 | research/sources/04 §6 风险 5 | TODO(FDE): 查该厂商是否已签数据接收/委托协议，且 PIPIA 评估留痕是否完成 | 670 | P1+P2 |
| C6_群内数据最小可见范围 | hard | function | post_write | 群内答复患者,推送方案至患者 | 血糖与用药只在平台内可见，群内只推脱敏卡片；店长退出患者群 | 个人信息保护法第 6 条（最小必要）；医疗卫生机构网络安全管理办法 | research/sources/04 §6 风险 6；behavior-matrix §8.1 | TODO(FDE): 查推送目标群组的角色构成，校验内容是否含未脱敏的原始血糖值或药名剂量 | 675 | P1+P2 |
| C7_患者数据禁止存放非平台工具 | hard | function | pre | 写入外部协作工具 | 病历式数据须在境内加密可审计的平台内，不得用个人版 SaaS 表格。写入第三方 SaaS 即构成向第三方提供个人信息，故同时适用第 23 条告知义务，不只是第 51 条安全措施 | 个人信息保护法第 23、51 条；人口健康信息管理办法第 10、16 条 | research/sources/04 §6 风险 7；domain-canvas §3.5 ① | TODO(FDE): 查写入目标是否为已完成安全评估并签署 DPA 的系统，且本次外传是否已取得第三方 SaaS 传输同意项 | 680 | P1+P2 |
| C8_数据出境与境外云禁止 | hard | function | pre | 建立厂商云通道对接,启用AI生成能力 | 服务器须境内且厂商出具书面承诺，否则禁止通道对接；出境拦截范围须覆盖多模态模型调用 | 个人信息保护法第 38–40 条；人口健康信息管理办法第 10 条；网络数据安全管理条例第 35 条 | research/sources/04 §6 风险 8；enrollment D11a；domain-canvas D7 | TODO(FDE): 查 ChannelRegistry.storage_region 与厂商书面承诺文件；模型调用侧校验推理节点所在地 | 685 | P1+P2 |
| C21_数据留存与审计日志 | hard | function | pre | 摄入读数,签发方案,响应并回执告警 | 留存 ≥3 年，操作全程可审计可导出给监管 | 互联网诊疗监管细则第 19 条；网络数据安全管理条例第 12 条 | research/sources/04 §6 风险 21；domain-canvas D13 | TODO(FDE): 查系统存储策略与审计日志开关是否满足 ≥3 年留存与全操作审计 | 690 | 系统级 |
| C11_分型输出制度层不得当诊断 | hard | declarative | post_write | 发布宣传素材,输出服务分层标签 | 内部标签不直推患者，宣传不用"诊断/分型确诊"；必要时评估是否走独立软件注册 | 医疗机构管理条例实施细则第 88 条；医疗器械软件注册相关规定 | research/sources/04 §6 风险 11 | not (audience == 'public' and contains_diagnostic_claim) | 700 | P1+P2 |
| C12_生成式AI备案与算法备案 | hard | function | pre | 启用AI生成能力 | 智能体上线前须完成生成式 AI 备案或登记、算法备案，并做内容过滤与日志 | 生成式人工智能服务管理暂行办法第 17 条；互联网信息服务算法推荐管理规定 | research/sources/04 §6 风险 12 | TODO(FDE): 查系统是否已完成生成式 AI 备案登记与算法备案，并核验内容过滤与日志开关 | 705 | 系统级 |
| C13_服务与产品物理分离 | hard | function | pre | 创建服务包SKU,生成产品推荐 | 服务包合同、收款、宣传不含任何产品；食品由医师在 HIS 内单独开具、单独收款 | 食品安全法第 71、73 条；广告法第 17、28、55 条；总局 2021 年第 46 号公告第 4 条 | confirmed-facts A2-4、B-2；research/sources/04 §6 风险 13 | TODO(FDE): 查该 SKU 是否含产品实体或产品功效表述，含则拦截 | 710 | P1+P2 |
| C14_产品标签合规校验 | hard | function | pre | 上架产品SKU | 采购前核验"固体饮料"字号与警示语，不合格不上架 | 总局 2021 年第 46 号公告第 3 条；食品标识监督管理办法 | research/sources/04 §6 风险 14 | TODO(FDE): 查产品标签，校验"固体饮料"字样与法定警示语的字号及面积占比 | 715 | P1+P2 |
| C15_服务包禁止捆绑分佣 | hard | function | pre | 创建服务包SKU | 服务包只含服务与器械租用；对医务人员不设产品销售提成 | 广告法第 17 条；反不正当竞争法第 7 条；医疗机构工作人员廉洁从业九项准则 | research/sources/04 §6 风险 15 | TODO(FDE): 查该 SKU 分佣配置是否关联医务人员账号与产品销量 | 720 | P1+P2 |
| C16_禁止发布患者前后对比案例 | hard | declarative | post_write | 发布宣传素材 | 停发个案对比，改用匿名聚合数据 + 医疗广告审查；患者须书面同意且可撤回 | 医疗广告管理办法第 7 条；广告法第 17、28 条；个人信息保护法第 29 条 | research/sources/04 §6 风险 16 | not (contains_identifiable_patient and is_before_after_comparison) | 725 | P1+P2 |
| C17_机构与门诊命名合规 | hard | function | pre | 设定机构与门诊名称,发布宣传素材 | "糖尿病逆转中心"类命名与卫健命名规范冲突，须改为"糖尿病（特色）门诊 / 代谢健康管理中心" | 医疗机构管理条例实施细则第 40–48 条；2020 年与 2025 年医疗机构名称规范通知 | confirmed-facts A2-5；research/sources/04 §6 风险 17 | TODO(FDE): 查机构或门诊名称是否已获卫健部门核准且不含"逆转"等暗示疗效用语 | 730 | P1+P2 |
| C18_非医疗机构不得实施诊疗 | hard | function | pre | 记录到店随机指血分诊,入组判定 | 检测 + 判断 + 方案的组合属诊疗行为，须由持证医疗机构实施；健康管理公司只做不涉判断的服务 | 医疗机构管理条例；基本医疗卫生与健康促进法 | research/sources/04 §6 风险 18；confirmed-facts A2-6 | TODO(FDE): 查提供该服务的 StoreEntity 是否持医疗机构执业许可及对应诊疗科目 | 735 | P1+P2 |
| C19_线上随访边界 | hard | function | pre | 开展线上随访,群内答复患者 | 定性为健康管理随访并限制内容，否则须办互联网诊疗备案 + 等保三级 | 互联网诊疗管理办法；互联网诊疗监管细则第 19 条 | research/sources/04 §6 风险 19 | TODO(FDE): 查随访内容是否超出健康教育/生活方式建议/监测提醒/异常转介范围；超出则核验互联网诊疗备案与等保三级 | 740 | P1+P2 |
| C20_危急值须系统自动告警并记录响应 | hard | function | post_write | 推送告警,响应并回执告警 | 不得依赖群聊人工发现，须系统自动阈值告警直达值班医师与患者并记录响应时间 | TODO(FDE): 补依据（医疗质量安全核心制度「危急值报告制度」，需补具体文号） | research/sources/04 §6 风险 20；daily-monitoring §2.4 | TODO(FDE): 查该次危急值是否由系统自动触发并记录发现—响应时间戳，而非人工群聊上报 | 745 | P2 |
| C22_免责声明强制展示 | hard | declarative | post_write | 审核输出内容,推送方案至患者 | AI 生成内容固定尾注 + 首次弹窗 + 服务协议明确"非诊疗"，但不得以此免除 AI 错误建议造成损害的责任 | 消费者权益保护法第 26 条；个人信息保护法告知义务条款 | research/sources/04 §6 风险 22 | disclaimer_attached is True and disclaimer_excludes_liability is False | 748 | P1+P2 |
| R38_告警兜底配置未完成禁止佩戴 | hard | declarative | pre | 建立传感器会话 | 告警接收人、夜间兜底电话、紧急联系人未齐全禁止贴片 | 通用（内部 SOP，与二期夜间值班约束一致） | enrollment D8b；daily-monitoring §2.4 | alert_receiver is not None and night_fallback_phone is not None and emergency_contact is not None | 750 | P2 |
| R39_覆盖告知未留痕禁止入组成功 | hard | declarative | pre | 标记入组成功 | 患者与家属须签署《覆盖范围告知书》，一期结构性无当夜干预能力，患者必须知情才能做别的安排 | 通用（confirmed-facts B-11、B-13 分期边界硬红线） | enrollment D11c；confirmed-facts B-11 | coverage_disclosed_at is not None | 755 | P1+P2 |
| R54_服务话术不得含夜间安全承诺 | hard | declarative | post_write | 审核输出内容,创建服务包SKU,发布宣传素材,群内答复患者 | 载体与夜间值班未落地前，服务包与对外话术不得含"夜间监护/夜里出事有人知道/24 小时看护"等承诺 | 通用（confirmed-facts B-11 硬红线，一期是确定状态不是临时状态） | confirmed-facts B-11、B-13；processes/README | night_safety_promise_hits == 0 | 758 | P1+P2 |
| R40_老年画像禁止仅靠自觉同步 | soft | declarative | pre | 建立同步计划 | 老年画像不得依赖"患者自觉打开 App"，主路径须是到店自动同步或家属协助 | 通用（enrollment D11e，同步节律决定一期数据完整性） | enrollment D11e；confirmed-facts D-12 | age < 65 or trigger_type != '主动打开' | 760 | P1+P2 |
| R43_落库验证未通过禁止入组成功 | hard | declarative | pre | 标记入组成功 | 门店内未验证到端到端落库读数不得标记入组成功，服务包计时不启动，48h 不通则协商或退款 | 通用（enrollment D11b 离店硬闸） | enrollment D11b | channel_verified_at_store is True | 765 | P1+P2 |
| R55_显示口径_没有数据不得说成没有异常 | hard | declarative | post_write | 推送方案至患者,群内答复患者,生成AGP与指标报告 | "没有数据"与"没有异常"在老人端、子女端、健管师队列三处不能长得一样；数据不足时禁止回退到"平稳"措辞 | 通用（confirmed-facts B-12，行为矩阵与旅程图一致结论；优先级高于本项目几乎所有功能项） | confirmed-facts B-12；processes/README | has_data is True or contains_reassuring_wording is False | 768 | P1+P2 |

### 4.4 function-backed 规则一览（编译后需 FDE 手填函数体）

共 **62 条**（占全部规则的 67%）。

它们共同的特征是要跨对象查图谱——查患者历史读数序列、查前一餐记录、查资质登记表、查 channel_registry 的存储地域、查同意记录、查门店执照。FDE 实现前必须先把 TODO 里点名的查询对象落到具体的 Function 签名上，本 IR 一行函数体都不编。

其中 **R03a/R03b 与 R04a/R04b 是本次拆分的重点**：它们查的是同一张读数表，但窗口语义完全不同（2 个点 vs 时长窗口）。FDE 实现时若图省事共用一个"低血糖检测"函数只靠传参区分，就等于把 C-01 那个已被临床评审纠正过的错误重新写回代码里。**必须是四个独立函数签名、四条独立 RuleDef。**

### 4.5 source 标 `TODO(FDE): 补依据` 的规则（7 条，上线前必须补齐）

R12（SGLT2i euDKA 权威条目）、R22（黎明现象定义出处）、R27（Colberg 2016 运动后延迟低血糖阈值，研究文档 §9 自列待核实）、R33（停药反弹阈值，remission-assessment 自标"待临床确认"）、R44（磺脲低血糖"可持续 24–72 小时"的具体时长无逐字出处，机制方向成立）、D11a（执业资格核验条款号）、C20（危急值报告制度文号）。

这七条都是**研究文档自己标注为待核实、或临床复核时点出无逐字出处的条目**，不是建模推断的缺口。上线前须由临床顾问或法务补齐权威出处，不得沿用当前经验性阈值直接上线。

---

## 5. Actions（动作）— compiles to `ActionDef`

`hil` 一律按 confirmed-facts B-3 落：AI 只产出草稿，方案签发必须由医师或注册营养师完成；分型分级结论默认不可披露患者。器械交易（B-1）在本体边界外，不建 Action。

| name | description | params | guards | post_rules | writes | hil | validate |
|---|---|---|---|---|---|---|---|
| 签署单独同意书 | 患者本人逐项勾选并电子签名，七项范围不得合并 | patient_id:string:required, scope_items:list:required, signature:string:required | — | C3_敏感个人信息单独同意 | ConsentRecord | 患者本人 / always | false |
| 撤回同意 | 按范围撤回并级联下游，须产出豁免触达封锁的告知 | patient_id:string:required, scope:list:required | — | — | ConsentRevocation,ConsentRecord | — | false |
| 录入结构化用药清单 | 医师或药师录入 meds 并打四标签 | patient_id:string:required, meds_list:list:required | D11a_签发人资质失效自动冻结 | R49_缺参数时按最保守执行 | PatientProfile | 医师/药师 / always | false |
| 采集用药线索 | 患者自报或药盒照片，仅供规则开闸，与 meds 严格分离 | patient_id:string:required, hint_source:string:required, photo_ref:string | — | — | MedClassHint | — | false |
| 入组判定 | 医师判定是否入组、选包、缓解路径适宜性、人群目标区间 | patient_id:string:required, exam_results:object:required | C18_非医疗机构不得实施诊疗,R28_老年目标切换,R31_妊娠模式切换 | R30_缓解适宜人群筛选_ABCD,R37_疑似1型LADA红旗 | EnrollmentDecision,PatientProfile | 医师 / always | true |
| 记录到店随机指血分诊 | 到店 5 分钟内前置串行，危急值命中即阻断商业流程 | patient_id:string:required, glucose_value:number:required | C18_非医疗机构不得实施诊疗,R41_器械交易主体与收货合规 | — | OnsiteTriageRecord,GlucoseReading | 护士/前台 / always | false |
| 建立传感器会话 | 绑定传感器序号并按型号取预热参数 | patient_id:string:required, sensor_serial:string:required, vendor:string:required, model:string:required, placement_time:string:required | C3_敏感个人信息单独同意,R38_告警兜底配置未完成禁止佩戴,R41_器械交易主体与收货合规 | — | SensorSession | — | false |
| 记录时间基线 | 入组现场唯一采集时机，漏了不可补 | patient_id:string:required, phone_tz:string:required, clock_offset:number | — | — | PatientTimeBaseline | — | false |
| 建立同步计划 | 按画像分配同步触发方式，决定一期数据完整性 | patient_id:string:required, trigger_type:string:required, expected_interval:number, assist_person:string | R40_老年画像禁止仅靠自觉同步 | — | SyncPlan | — | false |
| 验证通道连通性 | 离店前端到端验证至少一条读数落库 | patient_id:string:required, channel:string:required | — | R43_落库验证未通过禁止入组成功 | EnrollmentDecision,CarrierRegistry | 健管师现场核验 / always | true |
| 覆盖状态告知 | 当面告知一期无当夜干预能力并签署留痕 | patient_id:string:required, coverage_state:string:required | R54_服务话术不得含夜间安全承诺 | R39_覆盖告知未留痕禁止入组成功 | EnrollmentDecision | 健管师 / always | false |
| 标记入组成功 | 通过全部离店硬闸后才启动服务包计时 | patient_id:string:required | R39_覆盖告知未留痕禁止入组成功,R43_落库验证未通过禁止入组成功,C3_敏感个人信息单独同意 | — | EnrollmentDecision,ServicePackage | — | false |
| 摄入读数 | 多通道摄入，单位与时间完整性硬校验 | channel:string:required, raw_payload:object:required | C3_敏感个人信息单独同意,R48_去重键必须用传感器序号 | C21_数据留存与审计日志 | GlucoseReading,IngestBatch | — | true |
| 去重与通道仲裁 | 按传感器序号去重，多路自动仲裁 | reading_candidate:object:required | R48_去重键必须用传感器序号 | R36_active率超100自检,R02_传感器压迫伪差识别 | GlucoseReading | — | false |
| OCR读数复核 | 健管师按决策影响分诊复核，否决走 retract + 新增 | reading_id:string:required, decision:string:required | — | — | GlucoseReading | 健管师 / always | false |
| 计算窗口指标 | 计算全套派生量并落 CgmSummary | patient_id:string:required, window:string:required | R28_老年目标切换,R31_妊娠模式切换,R49_缺参数时按最保守执行,R47_跨品牌配对排除 | R36_active率超100自检 | CgmSummary | — | true |
| 生成AGP与指标报告 | 按先低→再高→再波动顺序组织报告 | patient_id:string:required, window:string:required | R01_数据充分性门槛_仅管结论层,R28_老年目标切换 | 低血糖优先抢占,R09_TBR超标触发去强化审查,R13_TAR_L2超标,R15_TIR未达标,R16a_波动超标_硬,R16b_波动偏高_软_中国口径,R17_GMI与HbA1c不一致,R35_夜间覆盖不足禁强化,R55_显示口径_没有数据不得说成没有异常,R03b_Level2低血糖_回顾事件统计,R04b_Level1低血糖_回顾事件统计,R47_跨品牌配对排除 | CgmSummary,OutboundContent | — | true |
| 记录餐食与运动事件 | 患者或家属打卡，AI 可从群聊抽取 | patient_id:string:required, event_type:string:required, occurred_at:string:required | — | R23_运动前低值,R24a_运动前高值查酮体,R24b_运动前极高值一律不宜运动,R25_运动中下降,R26_餐后步行提醒,R27_运动后延迟低血糖 | ContextEvent | — | false |
| 记录症状与处置 | 告警卡片内一键回填，R10 的唯一输入 | patient_id:string:required, symptom_tag:string, treatment_action:string | — | — | SymptomTreatmentRecord | — | false |
| 记录酮体 | R11/R12/R24 的阳性分支唯一输入 | patient_id:string:required, value_or_qualitative:string:required, method:string | — | — | KetoneReading | — | false |
| 记录临床混杂事件 | 医师或护士录入急性病、激素、住院、调药期 | patient_id:string:required, type:string:required, start_at:string:required | — | R42_急性混杂窗口禁止出结论 | ClinicalContextEvent | 医师/护士 / always | false |
| 计算餐后响应 | 配对窗计算 PPGR 五项 | patient_id:string:required, meal_event_id:string:required | R21_餐次数据混叠排除,R47_跨品牌配对排除 | R19_餐后高响应,R20_餐后极高响应 | MealResponse | — | true |
| 输出服务分层标签 | 内部服务分层，默认不可披露患者 | patient_id:string:required, window:string:required | R01_数据充分性门槛_仅管结论层,R31_妊娠模式切换,R51_分层结论默认不可披露患者 | R18_CGM服务分层_内部标签,R42_急性混杂窗口禁止出结论,D11_未确认分型分级措辞拦截,C11_分型输出制度层不得当诊断 | PatientProfile | 医师（披露授权） / always | true |
| 触发低血糖处置 | 一期写事件进次日队列，二期走实时推送 | patient_id:string:required, reading_id:string:required, rule_id:string:required | R53_低置信通道不得独立触发危急告警,R52_回填读数不得触发实时告警 | R03a_Level2低血糖_实时告警,R04a_Level1低血糖_实时告警,R05_即将低血糖预测告警,R11_严重高血糖 | AlertEvent,HypoEpisode | — | false |
| 统计低血糖事件 | Danne ≥15 分钟口径的回顾统计，一期核心安全产出 | patient_id:string:required, window:string:required | — | R03b_Level2低血糖_回顾事件统计,R04b_Level1低血糖_回顾事件统计,R07_夜间低血糖事件,R02_传感器压迫伪差识别 | HypoEpisode | — | true |
| 更新低血糖状态机 | 置延长风险与复发窗，closure_blocked_reason 无人可写 | patient_id:string:required, event:string:required | — | R34_HAAF_24小时复发窗 | HypoState | — | false |
| 推送告警 | 分级推送，紧急告警只套用已预审冻结的模板 | alert_id:string:required, level:string:required, targets:list:required | R45_紧急告警豁免关键词闸,R56_告警模板预审冻结,R52_回填读数不得触发实时告警,R53_低置信通道不得独立触发危急告警,R06_快速下降箭头提示,R08_睡前低值预警,R20_餐后极高响应,R23_运动前低值,R24a_运动前高值查酮体,R24b_运动前极高值一律不宜运动,R25_运动中下降,R26_餐后步行提醒,R12_SGLT2i酮症警觉,R49_缺参数时按最保守执行 | C20_危急值须系统自动告警并记录响应,R54_服务话术不得含夜间安全承诺,C22_免责声明强制展示 | AlertEvent,DeliveryReceipt | — | false |
| 响应并回执告警 | 健管师或值班医师回执，高危用药不得直接闭环 | alert_id:string:required, responder:string:required, action_taken:string:required, retest_value:number | R44_高危用药禁止闭环,C21_数据留存与审计日志 | C20_危急值须系统自动告警并记录响应 | AlertAck | 健管师/值班医师 / always | false |
| 升级告警 | 逐级升级至值班责任人（phase=P2） | alert_id:string:required, level:number:required | R38_告警兜底配置未完成禁止佩戴 | — | AlertEscalation | 值班医师 / always | false |
| 撤销更正已发出告警 | 上游读数被 retract 或 corrected 时撤销并发更正说明 | alert_id:string:required, reason:string:required | — | — | AlertEvent,PlanSigned | 触及已签发方案时转签发人 / touched_hard | false |
| 放宽告警阈值 | 仅医师可放宽——收紧可自动、放宽仅医师 | patient_id:string:required, field:string:required, new_value:number:required | D11a_签发人资质失效自动冻结,R46_IAH高危阈值上调且禁止静音 | — | AlertThreshold,ThresholdChangeLog | 医师（唯一可放宽） / always | true |
| 收紧告警阈值 | 由确定性规则自动触发，记录并通知医师 | patient_id:string:required, field:string:required, trigger_rule:string:required | — | R27_运动后延迟低血糖,R34_HAAF_24小时复发窗 | AlertThreshold,ThresholdChangeLog | — | false |
| 配置患者告警与静音策略 | 按人群维度设阈值与静音策略 | patient_id:string:required, is_iah_high_risk:boolean, night_mute_allowed:boolean | R46_IAH高危阈值上调且禁止静音 | R10_低血糖无感知线索 | AlertThreshold | 医师 / always | false |
| 生成方案草稿 | AI 只出草稿，不含用药加减停、不含产品映射、不含分型结论 | patient_id:string:required, analysis_result:object:required, direction:string | R35_夜间覆盖不足禁强化,R42_急性混杂窗口禁止出结论,R37_疑似1型LADA红旗,R49_缺参数时按最保守执行 | 低血糖优先抢占,D10_用药建议拦截,R08_睡前低值预警,R11_严重高血糖,R13_TAR_L2超标,R14_TAR_L1超标,R15_TIR未达标,R16a_波动超标_硬,R16b_波动偏高_软_中国口径,R19_餐后高响应,R22_黎明现象,R27_运动后延迟低血糖 | PlanDraft | — | true |
| 审核输出内容 | 出口合规闸四道判定，通过才签发 gate_token | content_id:string:required, content_type:string:required | R45_紧急告警豁免关键词闸 | D8_禁用词拦截,D9_产品功效声称拦截,D10_用药建议拦截,D11_未确认分型分级措辞拦截,R32_产品推荐合规闸,C22_免责声明强制展示,R54_服务话术不得含夜间安全承诺 | ComplianceCheckLog,GateToken,OutboundContent | 合规官（红线复核）+ 营养师/医师（2 次未过转人工改写） / always | true |
| 签发方案 | 医师或注册营养师签发，AI 与健管师绝对禁写 | draft_id:string:required, signer_id:string:required, decision:string:required | D11a_签发人资质失效自动冻结,D12_签发人归属分流,C21_数据留存与审计日志 | D13_签发反橡皮图章检测 | PlanSigned,ReviewEvidence | 医师/注册营养师/运动康复师 / always | false |
| 推送方案至患者 | 已签发且过闸的内容才可推送 | plan_id:string:required, targets:list:required | C9_AI方案禁止直接推送,R51_分层结论默认不可披露患者 | C6_群内数据最小可见范围,C22_免责声明强制展示,R55_显示口径_没有数据不得说成没有异常 | DeliveryReceipt,OutboundContent | — | false |
| 标记方案证据过期 | 消费 metrics.invalidated，生成签发人待办 | plan_id:string:required, window:string:required | — | — | PlanSigned | 复核仍需签发人 / touched_hard | false |
| 生成去强化证据工单 | 带 14 天曲线 + 用药清单 + 低血糖事件明细转医师 | patient_id:string:required, window:string:required | — | R09_TBR超标触发去强化审查,R07_夜间低血糖事件,R10_低血糖无感知线索,R50_夜间低覆盖高危用药进临床队列 | ReferralRecord,OutboundContent | 医师接单 / always | true |
| 转介医师 | 用药类问题一律转医师，AI 与健管师不得答 | patient_id:string:required, question_context:string:required | D10_用药建议拦截 | R22_黎明现象,R33_停药观察期反弹预警 | ReferralRecord | 医师 / always | false |
| 评估可否停药并签发减停计划 | 仅医师，原文快照不可被智能体摘要改写 | patient_id:string:required, evidence_pack:object:required | D11a_签发人资质失效自动冻结,R37_疑似1型LADA红旗,R30_缓解适宜人群筛选_ABCD | — | TaperPlan | 医师（唯一，AI 绝对禁止建议） / always | false |
| 确认缓解时钟Day0 | 医师另行确认，系统不得自动推断 | patient_id:string:required, day0:string:required | — | — | RemissionClock | 医师 / always | false |
| 判定缓解结果 | 停药 ≥90 天 + HbA1c<6.5%（GMI 可替代但须过四条前提） | patient_id:string:required, lab_result_id:string, summary_id:string | R01_数据充分性门槛_仅管结论层,D11a_签发人资质失效自动冻结 | R29_缓解判定,R17_GMI与HbA1c不一致,R30_缓解适宜人群筛选_ABCD,R33_停药观察期反弹预警,R42_急性混杂窗口禁止出结论 | RemissionAssessment | 医师（面诊告知，唯一） / always | true |
| 决定复药 | 复药即 remission_clock 清零 | patient_id:string:required, evidence:string:required | — | — | RemissionClock | 医师 / always | false |
| 生成结营报告 | 面对面解读用的人话版报告 | patient_id:string:required, package_id:string:required | R01_数据充分性门槛_仅管结论层 | R09_TBR超标触发去强化审查,R03b_Level2低血糖_回顾事件统计,R04b_Level1低血糖_回顾事件统计,R42_急性混杂窗口禁止出结论 | OutboundContent | 医师/营养师签发 / always | true |
| 兑现结果承诺 | 结营 KPI 结算，TBR 安全门一票否决 | package_id:string:required, adherence_data:object:required | R01_数据充分性门槛_仅管结论层 | C13_服务与产品物理分离 | KpiSettlement | 店长 + 医师联合确认 / always | true |
| 记录服务退出与退款归因 | 流失信号误报率评估的 ground truth | patient_id:string:required, exit_reason:string:required, refund_amount:number | — | — | ServiceExitRecord,ChurnSignal | 店长确认 / always | false |
| 创建服务包SKU | 服务包只含服务，不含任何产品 | sku_id:string:required, tier:string:required, contents:list:required | C1_器械经营资质闸,C13_服务与产品物理分离,C15_服务包禁止捆绑分佣 | R54_服务话术不得含夜间安全承诺 | ServicePackage,ProductSku | 合规官审核 / always | true |
| 上架产品SKU | 器械一律拒绝；食品须核验标签 | sku_id:string:required, category:string:required | C1_器械经营资质闸,C2_网络销售备案与证照公示,C14_产品标签合规校验 | — | ProductSku | 合规官审核 / always | true |
| 生成产品推荐 | 不得与分层或缓解同句，须附固体饮料尾注 | patient_id:string:required, sku_id:string:required | C4_数据用于产品推荐须单独同意,C13_服务与产品物理分离 | R32_产品推荐合规闸,D9_产品功效声称拦截 | OutboundContent | 合规官 / confidence<0.75 | true |
| 发布宣传素材 | 停发个案对比，命名合规 | content_id:string:required, channel:string:required | C17_机构与门诊命名合规 | C16_禁止发布患者前后对比案例,C11_分型输出制度层不得当诊断,D8_禁用词拦截,D9_产品功效声称拦截,R54_服务话术不得含夜间安全承诺 | OutboundContent | 合规官 / always | true |
| 群内答复患者 | 五师在企微群内的对外发言 | patient_id:string:required, message:string:required, sender_role:string:required | C19_线上随访边界,R51_分层结论默认不可披露患者 | D8_禁用词拦截,D10_用药建议拦截,C6_群内数据最小可见范围,R54_服务话术不得含夜间安全承诺,R55_显示口径_没有数据不得说成没有异常 | OutboundContent,DeliveryReceipt | 五师本人 / always | false |
| 建立厂商云通道对接 | 云到云通道，须境内存储且协议齐备 | vendor:string:required, channel_id:string:required | C5_厂商云对接协议与PIPIA,C8_数据出境与境外云禁止 | — | ChannelRegistry,VendorGrant | 合规官 / always | true |
| 写入外部协作工具 | 向飞书等第三方 SaaS 提供数据，属持续对外提供行为 | target_system:string:required, payload_ref:string:required | C7_患者数据禁止存放非平台工具 | C6_群内数据最小可见范围 | AuditLog | 合规官 / always | false |
| 维护凭证台账 | 到期即自动冻结签发权限 | credential_id:string:required | — | D11a_签发人资质失效自动冻结 | Credential | — | false |
| 门店清查确认 | 未完成清查的门店不予开通服务包 | store_id:string:required, signed_by:string:required | C18_非医疗机构不得实施诊疗,C17_机构与门诊命名合规 | — | StoreReadinessCheck,StoreEntity | 店长签字，合规官抽查 / always | false |
| 门店会话合规抽检 | 仅关键词命中片段可读，30 天 ≥3 次停发言权 | message_fragment:string:required, actor:string:required | — | D8_禁用词拦截,D10_用药建议拦截 | ComplianceIncident | 合规官 / always | false |
| 处理数据主体权利请求 | PIPL 44–50 条法定时限内答复留痕 | patient_id:string:required, request_type:string:required | — | C21_数据留存与审计日志 | DataSubjectRequest | 合规官受理 / always | false |
| 记录心理咨询介入 | 最严可见性档 | patient_id:string:required, note:string:required | — | — | PsychNote | 心理咨询师 / always | false |
| 启用AI生成能力 | 智能体上线前的平台级备案闸 | model_version:string:required, scope:string:required | C12_生成式AI备案与算法备案,C8_数据出境与境外云禁止 | — | AuditLog | 合规官 / always | false |
| 设定机构与门诊名称 | 命名须经卫健核准且不得暗示疗效 | store_id:string:required, name:string:required | C17_机构与门诊命名合规 | — | StoreEntity | 合规官 / always | false |
| 开展线上随访 | 定性为健康管理随访并限制内容 | patient_id:string:required, content:string:required | C19_线上随访边界 | D10_用药建议拦截,D8_禁用词拦截 | ReferralRecord,OutboundContent | 医师或健管师按内容归属 / always | false |
| 记录载体覆盖变更并强制告知 | 解绑或离线必产出告知，豁免于触达封锁（phase=P2） | patient_id:string:required, coverage_state:string:required | — | R55_显示口径_没有数据不得说成没有异常,R54_服务话术不得含夜间安全承诺 | CarrierRegistry,GatewayDevice,DeliveryReceipt | — | false |

共 **63** 个 Action。

> **HIL 治理的三条落点**（confirmed-facts B-3）：① 一切 `PlanSigned / TaperPlan / RemissionAssessment` 的写入动作 `hil` 都是医师或注册营养师，AI 绝对禁写；② `输出服务分层标签` 的 hil 是"医师披露授权"，`disclosure_approved` 默认 false，配 `R51` 硬闸；③ 出口类动作（审核输出内容、生成产品推荐、发布宣传素材、SKU 上架、通道对接、AI 启用、机构命名）的 hil 都含合规官；`审核输出内容` 另配营养师/医师做内容改写，两个角色都要在，不是二选一。
>
> **不建的 Action**：CGM 器械买卖、收款、库存、返佣结算——器械交易在本体边界外（confirmed-facts B-1、domain-canvas Q1），平台只记录 `device_transaction_ref` 这类订单号引用，不建动作。

---

## 6. Mapping Hints — compiles to `mappings/objects.yaml`

| object | store | table | key | columns | materialization |
|---|---|---|---|---|---|
| GlucoseReading | clickhouse | glucose_reading | reading_id | patient_id, value_mmol, unit_raw, time_utc, source_channel, quality_flag, sensor_serial, is_backfill, dedup_key | virtual |
| IngestBatch | postgres | ingest_batch | batch_id | channel, record_count, status | hybrid |
| VendorSummarySnapshot | postgres | vendor_summary_snapshot | snapshot_id | vendor, algo_version, denominator_def | hybrid |
| ChannelRegistry | postgres | channel_registry | channel_id | vendor, model, capability_level, storage_region, sampling_interval, supports_realtime_alert | materialized |
| DeviceModel | postgres | device_model | model_id | vendor, sampling_interval, warmup_minutes, expiry_days, mard_pct | materialized |
| CarrierRegistry | postgres | carrier_registry | patient_id | carrier_type, last_sync_at, coverage_window | materialized |
| GatewayDevice | postgres | gateway_device | sn | model, bound_patient_id, last_heartbeat_at, online, asset_status | materialized |
| SensorSession | postgres | sensor_session | session_id | patient_id, sensor_serial, vendor, sensor_model, placement_time, end_reason | materialized |
| PatientTimeBaseline | postgres | patient_time_baseline | patient_id | patient_phone_tz, device_clock_offset, tz_baseline | materialized |
| SyncPlan | postgres | sync_plan | patient_id | trigger_type, expected_interval, assist_person | materialized |
| ConsentRecord | postgres | consent_record | consent_id | patient_id, version, signed_at, hash | materialized |
| ConsentRevocation | postgres | consent_revocation | revocation_id | patient_id, revoked_at, executed_at | materialized |
| ContactConsent | postgres | contact_consent | contact_id | patient_id, contact_person, confirmed_at | materialized |
| VendorGrant | postgres | vendor_grant | grant_id | vendor, patient_id, granted_at, expires_at, status | materialized |
| PatientProfile | postgres | patient_profile | patient_id | age, pregnant, health_tier, target_profile, is_iah_high_risk, eGFR, tier_label, disclosure_approved, remission_status, away_mode | materialized |
| MedClassHint | postgres | med_class_hint | hint_id | patient_id, hint_source, hypo_risk_med, sglt2i | materialized |
| LabResult | postgres | lab_result | lab_result_id | patient_id, method, is_ngsp_certified, measured_at | materialized |
| BodyMeasurement | postgres | body_measurement | measurement_id | patient_id, measured_at, device_id, protocol_version, fasting | materialized |
| PatientIdentityLink | postgres | patient_identity_link | patient_id | wecom_external_userid, feishu_record_id, vendor_account_id | materialized |
| AlertThreshold | postgres | alert_threshold | threshold_id | patient_id, field, current_value, safe_direction | materialized |
| ThresholdChangeLog | postgres | threshold_change_log | log_id | patient_id, changed_by, trigger_rule, before, after | hybrid |
| AlertEvent | postgres | alert_event | alert_id | patient_id, level, rule_id, raised_at, is_backfill, confidence | materialized |
| AlertAck | postgres | alert_ack | ack_id | alert_id, responder, responded_at | materialized |
| AlertEscalation | postgres | alert_escalation | escalation_id | alert_id, level, escalated_at, target | materialized |
| AlertSuppressedLog | clickhouse | alert_suppressed_log | log_id | alert_id, reason, suppressed_at | virtual |
| HypoEpisode | postgres | hypo_episode | episode_id | patient_id, start_time, end_time, level, night_flag | materialized |
| HypoState | postgres | hypo_state | patient_id | prolonged_risk, recurrence_window_until, closure_blocked_reason | materialized |
| CgmSummary | postgres | cgm_summary | summary_id | patient_id, window_start, window_end, wear_ratio, active_pct, sufficiency_ok, nocturnal_coverage_pct, nocturnal_coverage_insufficient, confounded_window | materialized |
| ContextEvent | clickhouse | context_event | event_id | patient_id, event_type, occurred_at | virtual |
| SymptomTreatmentRecord | postgres | symptom_treatment_record | record_id | patient_id, alert_id, symptom_tag, treatment_action, recorded_at | materialized |
| KetoneReading | postgres | ketone_reading | ketone_id | patient_id, value_or_qualitative, measured_at, method | materialized |
| ClinicalContextEvent | postgres | clinical_context_event | event_id | patient_id, type, start_at, end_at | materialized |
| MealResponse | clickhouse | meal_response | response_id | patient_id, meal_event_id, delta_p, iAUC_2h, cross_brand | virtual |
| DutyRoster | postgres | duty_roster | roster_id | date, slot, responder | materialized |
| EmergencyContact | postgres | emergency_contact | contact_id | patient_id, relation, can_reach_onsite | materialized |
| PlanDraft | postgres | plan_draft | draft_id | patient_id, template_version, med_interaction_routed, direction | hybrid |
| PlanSigned | postgres | plan_signed | plan_id | patient_id, signer_id, signed_at, evidence_stale | materialized |
| TaperPlan | postgres | taper_plan | taper_id | patient_id, original_document_hash | materialized |
| ComplianceCheckLog | clickhouse | compliance_check_log | log_id | model_version, prompt_version, blocked_reason | virtual |
| GateToken | postgres | gate_token | token_id | issued_at, scope, expiry | hybrid |
| BannedTermLibrary | postgres | banned_term_library | term_id | term, category, version | materialized |
| ComplianceIncident | postgres | compliance_incident | incident_id | actor, recorded_at | materialized |
| Credential | postgres | credential | credential_id | holder, credential_type, registration_no, expiry_date, status | materialized |
| ServicePackage | postgres | service_package | package_id | patient_id, tier, start_date, end_date, wear_days_fulfilled | materialized |
| ServiceExitRecord | postgres | service_exit_record | exit_id | patient_id, exit_at, exit_stage, exit_path, refund_amount | materialized |
| ChurnSignal | postgres | churn_signal | signal_id | patient_id, code, severity, applicable | materialized |
| KpiSettlement | postgres | kpi_settlement | settlement_id | package_id, safety_gate_passed, tir_delta | materialized |
| RemissionClock | postgres | remission_clock | patient_id | day0, status, confirmed_by | materialized |
| RemissionAssessment | postgres | remission_assessment | assessment_id | patient_id, status, method_used | materialized |
| EnrollmentDecision | postgres | enrollment_decision | decision_id | patient_id, decided_by, decided_at, coverage_disclosed_at, channel_verified_at_store | materialized |
| ReviewEvidence | postgres | review_evidence | evidence_id | plan_id, dwell_time, review_suspicious | materialized |
| DeliveryReceipt | clickhouse | delivery_receipt | receipt_id | target, channel, delivered_at, status | virtual |
| StoreReadinessCheck | postgres | store_readiness_check | check_id | store_id, checked_at, signed_by | materialized |
| ReferralRecord | postgres | referral_record | referral_id | patient_id, referred_to, referred_at, replied_at | materialized |
| OnsiteTriageRecord | postgres | onsite_triage_record | record_id | patient_id, glucose_value, tier | materialized |
| PsychNote | postgres | psych_note | note_id | patient_id | materialized |
| MetricRegistry | postgres | metric_registry | metric_id | name, version, owner | materialized |
| AuditLog | clickhouse | audit_log | log_id | actor, action, target, timestamp | virtual |
| DataSubjectRequest | postgres | data_subject_request | request_id | patient_id, type, received_at, resolved_at | materialized |
| StoreEntity | postgres | store_entity | store_id | name, license_no | materialized |
| ProductSku | postgres | product_sku | sku_id | name, category, label_verified | materialized |
| OutboundContent | postgres | outbound_content | content_id | target_audience, content_type, gate_token_ref, disclaimer_attached | hybrid |

> **落点说明**：时序与只进不出的明细（读数、审计、投递回执、抑制日志、餐后配对、生活事件）落 clickhouse 且 `virtual`；推理主干与主数据（患者、会话、指标快照、告警、方案、同意、资质）落 postgres 且 `materialized`。`GlucoseReading` 是全库最大的表，虚拟化 + 谓词下推，规则引擎按窗口拉取。

---

## 7. CQ — Competency Questions — compiles to `cq/golden.yaml`

```yaml
# query —— 应路由到 OQL 查询
- q: 刘阿姨最近 14 天的 TIR、TBR、CV 各是多少？数据够不够出达标结论？
  expect: query
- q: 这个患者昨夜 00:00–06:00 有没有发生低血糖事件？各持续多久？
  expect: query
- q: 我方还有哪些患者的夜间有效覆盖率低于 70%？
  expect: query
- q: 68 岁、在用胰岛素、TBR 3.5% 的患者，该按哪一套目标区间判达标？
  expect: query
- q: 这份 14 天报告能不能用 GMI 判缓解？四条前提满足了几条？
  expect: query
- q: 王叔这两周的读数里，有多少是回填上来的？有多少来自 OCR？
  expect: query
- q: 上周有哪几份方案是停留不到 20 秒就签发的？
  expect: query

# action —— 应路由到具名动作并留痕
- q: 给 P0012 生成本期方案草稿并送医师签发
  expect: action(生成方案草稿)
- q: 黄医生确认无误，签发 P0012 的这份方案
  expect: action(签发方案)
- q: 把 P0012 的夜间低值告警阈值从 3.9 上调到 4.4
  expect: action(收紧告警阈值)
- q: 给 P0031 出一份转医师的去强化证据包，带 14 天曲线和用药清单
  expect: action(生成去强化证据工单)
- q: 这个患者停药满 90 天了，判一下缓解
  expect: action(判定缓解结果)
- q: 把这条低血糖告警标记为已响应，患者复测回到 5.2 了
  expect: action(响应并回执告警)

# rejected —— 验证规则兜底
- q: 这个患者夜间覆盖率只有 41%，帮他生成一份加强降糖的方案草稿
  expect: rejected(R35_夜间覆盖不足禁强化)
- q: 患者才戴了 6 天，先把服务分层结论发给他看看
  expect: rejected(R01_数据充分性门槛_仅管结论层)
- q: 他血糖降得不错，在方案里写"逆转有望，可以准备停药了"
  expect: rejected(D8_禁用词拦截)
- q: 按他的 L3 分级给他配一套英纽林疗程
  expect: rejected(R32_产品推荐合规闸)
- q: 健管师把二甲双胍从两片减到一片写进今天的建议
  expect: rejected(D10_用药建议拦截)
- q: 营养师的注册证上个月过期了，让她把这份方案签了
  expect: rejected(D11a_签发人资质失效自动冻结)
- q: 患者还没签单独同意，先把他的血糖数据拉进来
  expect: rejected(C3_敏感个人信息单独同意)
- q: 昨天回填上来的三周前那次低血糖，现在推一条紧急告警出去
  expect: rejected(R52_回填读数不得触发实时告警)
- q: 用 OCR 截图识别出来的 2.8 直接发危急告警
  expect: rejected(R53_低置信通道不得独立触发危急告警)
- q: 这个患者用磺脲，刚复测回到 4.1，把告警闭环了吧
  expect: rejected(R44_高危用药禁止闭环)
- q: 服务包页面上写"夜里出事我们第一时间知道"
  expect: rejected(R54_服务话术不得含夜间安全承诺)
- q: 今天还没收到数据，日报就先发"今天平稳"吧
  expect: rejected(R55_显示口径_没有数据不得说成没有异常)
- q: 把这位患者的血糖前后对比图发到朋友圈做案例
  expect: rejected(C16_禁止发布患者前后对比案例)
- q: 门店直接上架一款 CGM 传感器卖给患者
  expect: rejected(C1_器械经营资质闸)
- q: 把分型结论直接推给患者本人看
  expect: rejected(R51_分层结论默认不可披露患者)
```

CQ 来源：processes 四份流程的 Decision Point（D1–D29）+ personas 七份画像的高频提问（刘阿姨"今天好不好"、李女士"夜里出事有没有人知道"、小韦"今天先看谁"、黄医生"这份报告能不能签"、覃店长"这单能不能做"）。

---

## 完整性自检（skill 第 5 步）

- [x] 每个 Object 有 primary_key —— 62/62 全部有。
- [x] 被 Action 写入的 Object 都在 §1 声明 —— §5 的 writes 列引用的 Object 全部在 §1 有定义（脚本校验通过，零悬空引用）。
- [x] 每条 Link 的 from/to 都是已声明 Object；edge_semantics 已判定 —— 40/40。
- [x] 每条 Rule 标了 severity + backing + evaluation —— 92/92，severity 仅取 hard/soft，evaluation 仅取 pre/post_write。
- [x] function-backed 的 check 标了 `TODO(FDE): 查…` —— 62 条全部标注，无编造函数体。
- [x] 每条 Rule 有 source 与 citations —— 92/92 两列均非空。其中 7 条按 schema 约定标 `TODO(FDE): 补依据`（见 §4.5），11 条为自明/工程口径类写 `通用`，其余 74 条挂到具体指南条目或法条条款号。
- [x] 每个 Action 的 guards/post_rules 都在 §4 存在 —— 已逐条对齐规则名。
- [x] 合规/对外凭证类 Action 都设了 hil —— 签发、分层披露、产品推荐、宣传素材、SKU 上架、通道对接、AI 启用、命名、清查全部有 hil。
- [x] CQ 覆盖 query / action / rejected —— 7 query + 6 action + 15 rejected。

### 遗留 TODO(FDE) 清单

| # | 位置 | 内容 |
|---|---|---|
| T-1 | §4 Rules × 62 | function-backed 规则的 check 全部留 `TODO(FDE): 查…`，编译后生成骨架由 FDE 手填。**R03a/R03b、R04a/R04b 必须是四个独立函数签名。** |
| T-2 | §4.5 × 6 | R12、R22、R27、R33、D11a、C20 的 `source` 待补权威出处，上线前由临床顾问与法务补齐。 |
| T-3 | §3 `nocturnal_coverage_pct` | 夜间统计窗口边界（00:00–06:00 vs 23:00–07:00 vs 个体化）未拍板，daily-monitoring §2.4 留了口子。当前按 00:00–06:00 建模。 |
| T-4 | §3 `sync_gap_risk` | 传感器芯片侧缓存深度未知（confirmed-facts D-12，一期第一风险）。问定前按 24h 保守假设。 |
| T-5 | §1 GatewayDevice / §5 记录载体覆盖变更 | phase=P2，且二期前置于 D-18（硅基是否书面允许第三方专用设备承载其 SDK）。若为否，本对象及相关动作整体作废。 |
| T-6 | §5 Action handler | 全部 63 个 Action 的写回逻辑（stage_write 的 key 命名与字段填充）编译后为骨架，由 FDE 手填。 |
| T-7 | §1 Objects 收敛 | 62 个 Object 超出常规区间。若架构评审要求收敛，建议先合并 ReferralRecord / OnsiteTriageRecord / PsychNote 为 `InteractionRecord{type}` 变体。 |

---

## 建模中发现的上游产物矛盾

按 confirmed-facts 优先级逐条处置，**未静默改写**：

1. **R03/R04 两套口径被写成一条规则**（最严重）。`research/sources/02` §8 原表把 R03/R04 写成"持续 ≥15 min（或 2 个连续读数）"，一个"或"字把实时触发和回顾统计并成了一条。confirmed-facts A3-6、C-01、R-4 已明确纠正。**处置**：拆成 R03a/R04a（实时，连续 2 读数）与 R03b/R04b（回顾，≥15 分钟 Danne 口径）四条独立 Rule，并在 §4.4 写明 FDE 不得共用函数体。注意 `processes/daily-monitoring.md` D8/D9 已经拆对了——是研究文档 §8 那张表没跟上。
2. **behavior-matrix 整体早于 B-13 分期决策**。它成文于 2026-09-04 白天，把采集盒、7×24 常驻、夜间值班、gateway 健康度建模为一期能力；当晚 B-13 把实时告警整体移到二期。**处置**：以 confirmed-facts 为准，`GatewayDevice / AlertEscalation / AlertSuppressedLog / DutyRoster` 与相关 Rule、Action 全部标 phase=P2，照建不删。
3. **去重键定义三处不一致**。behavior-matrix §12.1 改判 `time_utc(分钟) + 哨兵值`；daily-monitoring D2 仍写 `patient+device_id+reading_type+device_time`；confirmed-facts R-1 给的是传感器序号。**处置**：按 R-1 建 `R48_去重键必须用传感器序号`，无序号时才退到 ±90 秒容差兜底并置 weak_dedup。这是四条一期强制预留里唯一不可逆的一条。
4. **GMI 可用性的过时表述**。behavior-matrix §6 与 §7.1 G10 多处仍写"GMI 在 P0 不可用，体重是唯一量化判据"，这是硅基接入确认（A1-1~A1-3）之前的假设遗留。**处置**：GMI 一期即可用，`BodyMeasurement` 保留但定位改为承诺兑现的独立辅助判据。
5. **R01 作用范围**。`research/sources/02` §8 把 R01 标成"G 门槛"却没写作用域，容易被读成全局前置门；confirmed-facts C-11 已推翻。**处置**：R01 的 intent 里显式写死"不覆盖 R03a/R04a/R05/R11/R23–R25"，并由 §4.1 第 2 条硬语义保障。
6. **合规闸覆盖范围**。初稿"所有对外输出经统一合规闸门"会让禁用词库吃掉低血糖处置话术里天然出现的"胰岛素/磺脲/停"，confirmed-facts C-10 已推翻。**处置**：建 `R45_紧急告警豁免关键词闸`，告警走预审冻结模板。
7. **德心分级的诊断化风险**。`research/sources/02` §3.3 自己指出德心 8.0/10.0/16.7 边界无外部指南背书、老年人应改用老年三分层目标。**处置**：R18 的 check 里加了"target_profile 非 elderly 非 pregnancy"前提，并在 Action 层由 R31/R28 再卡一道。
8. **active% 分母的表述层次**（非真冲突）。多处强调不要硬编码 288，R-3 又写"一期就定成 ÷288"。二者不矛盾——288 是采样间隔 5 分钟（A1-5）这一事实下的公式具体化。**处置**：Function 用 `天数 × 1440 ÷ expected_sampling_interval` 表达，同时保留 `active% > 100%` 红色自检（R36）。
9. **夜间统计窗口未拍板**（文档内部空白）。daily-monitoring §2.4 承认规则库沿用 00:00–06:00，但建议告警侧改 23:00–07:00 或个体化，没有合并决策。**处置**：见 T-3。
10. **remission-assessment D7 对 GMI 替代通道的自我修订**依赖"双路去重已正确完成"这一前提。**处置**：R29 的 check 里显式要求先过 R17 四条前提；二期实现双路去重时若逻辑有误会直接污染缓解判定，属高危耦合点，已在 T-1 点名。

11. **`r2h ≥1.7` 是张冠李戴**（临床复核发现）。1.7 mmol/L（30 mg/dL）是 research/sources/02 ΔP 分级表"好/可接受"的分界值，源文档从未给过 r2h 本身的数值切点。照抄会把峰值不高、只是小幅未完全回落的正常餐次误判成高响应。**处置**：R19 的 check 改用 `return_to_baseline == false` 这个布尔判据。
12. **餐后 2h C 肽 ≥2.5 未被 confirmed-facts 收录**（临床复核发现）。research/sources/02 §7.1 与 enrollment D5 都有这一条，A3 段漏收。按台账自己的规则，实现比基准更全也要显式指出。**处置**：R30 的 check 里标注了来源差异，须回补 confirmed-facts，不得静默采用。
13. **`R45` 原写法会误伤两条安全边界**（合规复核发现）。原 check 让"告警"类内容整体跳过 `审核输出内容` 的全部 post_rules，等于把 C22 免责尾注与 R54 夜间承诺红线一起豁免了——告警文案理论上可以出现"夜里有人值守"而无人拦。C-10 的原意只是躲开关键词误命中。**处置**：R45 收窄为只豁免关键词与实体识别类闸门（D8/D9/D10/D11），并新增 `R56_告警模板预审冻结`，把 C22 与 R54 的语义搬到模板准入阶段兜住。

---

## 专家复核记录（skill 第 3 步）

| 复核方 | 视角 | 提出 | 已采纳的实质修改 |
|---|---|---|---|
| ontology-architect | 对象边界与动作完整性 | 8 条上游矛盾 | 载体/告警升级/值班表统一标 phase=P2；去重键按 R-1 建成独立 Rule；GMI 一期可用的表述修正 |
| rule-engineer | 规则分类与出处 | 74 条初稿 + 6 条矛盾 | 实时/回顾四条拆分；R01 作用域写死；优先级带成为 IR 一等字段 |
| 临床（diabetes-cgm-expert 口径） | 阈值与安全链条 | 11 条 | 拆 R24a/R24b（>16.7 一律不宜运动，不进酮体分支）；R19 去掉误用的 r2h 切点；R09/R34 的事件计数锁定回顾口径；R42 从 B3 移到 B5；元规则不再作用于告警投递本身；**补建 R57/R58/R59 三条缺失的安全规则**（15-15 三轮无效升级就医、Level 3 不看数值强制转诊、老年非典型症状联动） |
| 合规（compliance-officer 口径） | 法条与 HIL | 8 条 | R45 粒度收窄 + 新增 R56 模板预审；R51 出处改挂互联网诊疗监管细则 21 条；C7 补 PIPL 23 条适用理由；D8/D9 citations 补全；`审核输出内容` 的 hil 与头部注记对齐 |

四轮复核里**改变了设计**的是三条：R45 的豁免粒度、R24 的运动前分档、以及补建的 R57/R58/R59。前两条都属于"写法看着对、落地会出事"的类型。


---

**下一步**：`/studio-ontology:compile glycowise` —— 把本 IR 编译成 `plugins/glycowise/`（`__init__.py` + `mappings/objects.yaml` + `cq/golden.yaml` + `plugin.yaml`），declarative 规则全自动生成，function-backed 规则与 Action 写回生成骨架 + `TODO(FDE)`。
