# formal 轮次运行手册（criteria v5，2026-10-25 冻结）

> 适用：check-pool 判定的 formal 起点 s 起，每一轮（s 至 s+3）。v5 全文见 paper `proposal/criteria.yaml` 头注 v5 段。之前的轮次一律探索性。

## 0. 本轮开始前
- 定本轮固定日期 `AS_OF=<本轮开始日>`，记进台账；本轮**所有** runner / chain_drive 调用带 `--as-of $AS_OF`。gate_decide 出现 `AS_OF_MISMATCH` 的裁决须同日重算后再记账。
- 分层规则已锁定（v5 (a′)）：`sets/family-override.yaml`、`holdout_sample.py`、`_common.py` 的哈希与 v5 头注一致才可运行；改其中任何一项都要 amend。

## 1. 落案例与 check-pool（先于任何归因）
1. 数据组落案例：`make_real_cases.py --window <窗口> --out ../cases/real`。
2. `holdout_sample.py --cases-dir cases --round <r> --holdout-size 100 --stratify family,tier --merge-min 8 --family-override sets/family-override.yaml --check-pool > checkpool/r<r>.txt`。
3. **立即提交** `checkpool/r<r>.txt`（提交时间即时间戳）。这次提交必须早于本轮任何归因文件。
4. 判定：
   - 尚未开 formal 且 check-pool 通过 → 本轮记为 **s**，在台账和 `checkpool/s.txt` 记下；
   - 尚未开 formal 且不通过 → 本轮探索性；若本轮是 round 10 → 不开 formal，三个 RQ 记「未进入 formal」；
   - 已开 formal → 照常继续（出现薄层记 HOLDOUT_THIN，不回退）。

## 2. 抽留出集
`holdout_sample.py … --holdout-size 100 --seed <r> --exclude-file <本轮 D⁻ 候选> --ledger growth-ledger.md --out sets/holdout-<r>.yaml`。

## 3. 两链归因（v5 (b⁗)）
- 顺序（formal 内序号）：s、s+2 先 1d 后 3d；s+1、s+3 先 3d 后 1d。
- 每条链**各开一个新的独立上下文代理**，任务文本 = `protocol/attribution-prompt.v1.md` 填占位符（模板正文不改；先核哈希 `b600b281…2116fb0e`）。
  - 占位符：ROUND、CHAIN、STATE_LABEL / STATE_DIR（本链当前状态，s 轮两链都是 h_s）、WINDOW / WINDOW_FILES、SET_FILES（本轮 D⁻ 候选、real-W*、holdout-<r>、family-override）、OTHER_CHAIN_DIR、AS_OF、WORK_DIR / OUT_DIR（`chains-formal/<chain>/attribution/round-<r>/`）、NAME_START / NUM_START（两链共用计数器：先归因的链用完后，后一条链接着编号）。
- 记下代理的模型版本。主会话不归因。
- s 轮开始时：从 h_s（当前生产）复制两链起点到 `chains-formal/ancestor-s/`；演练链 `chains-r7/1d` 丢弃（不删，只不再使用）。

## 4. 链上裁决（P-B，只走根因修）
每条链：`chain_drive.py run --manifest chains-formal/<chain>/manifest-r<r>.yaml --work-dir .studio-evolve/glycowise/chains-formal --gate-mode <chain> --as-of $AS_OF --family-override sets/family-override.yaml --repeat 3 …`（清单只含根因修与路由 error 入口提案）。

## 5. P-A 八臂（两链并集，v5 (i)）
- Pᵢ = 两链本轮全部提案（根因 + `pa-extra-r<r>.yaml` 里的朴素修）；逐字节相同的补丁只判一次。
- 每份提案对 hᵢ（= 3d 主链状态，即当前生产）建沙箱：补丁打不上记 **APPLY_FAIL**（不进分母，进 T5）。
- 基线与候选**在同一次运行里**、同一 `--as-of` 算 Dᵢ 与 B 读数；`gate_decide` 八个 mode，3d 行 `--ledger --window <窗口>`；台账 notes 记来源链、模型版本、AS_OF。

## 6. 合入与下一轮
- 3d 链的接受集经人确认后合入生产 → h_{r+1}；1d 链的接受集只在 1d 链内前进。
- 用 `sets/holdout-<r+1>.yaml` 判本轮合入提案的回退（B_{i+1} 口径），读数对 `P<num>-h{i,p}-B<r+1>.json`。

## 7. 每轮必报（RQ-2 v5 (b‴)）
- ① P-A 反事实：本轮缺陷集在两种闸门下各自的接受集（P-A 的 3d / 1d 两臂）。
- ② P-B 两链状态差（每轮末，在 `real-all-<窗口>` 与 B 上）。
- ③ 归因分歧数：两链规则层缺陷集的对称差大小，写进 `chains-formal/compare-r<r>.md`。
