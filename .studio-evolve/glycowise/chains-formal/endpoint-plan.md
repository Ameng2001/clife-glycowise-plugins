# formal 终点计算口径声明（2026-10-25，先于 B₁₂ 与重抽样的任何读数提交）

> criteria v5 规定「seeds = 3（三次留出集重抽）」「重抽 seed 预先固定不挑」，但没有写出具体 seed 值，也没有写 D₁₂ 不存在时 B₁₂ 怎么排除。以下按既有惯例机械确定，在读任何读数之前提交，提交时间即时间戳。若与导师理解不同，记为 v6 候选，不追溯改判。

## 1. B₁₂（判 round 11 提案回退）
- `holdout_sample.py --cases-dir cases --round 12 --seed 12 --holdout-size 100 --stratify family,tier --merge-min 8 --family-override sets/family-override.yaml --out sets/holdout-12.yaml`，池 = 当前 real 池 669 条（round 11 之后无新窗口）。
- 惯例：holdout-N 用 seed N、排除第 N 轮的 D⁻ 候选；没有第 12 轮，D₁₂ = ∅，不排除任何案例。
- 主口径：在 holdout-12 上比较 Apply(h₁₁, P) 与 h₁₁（同日、同一 --as-of）。round 11 提案都是看过 W54 定向句后产生的，定向句照常保留。
- 敏感性口径（描述性，不进判定，对应 v6 候选 ⑨）：剔除被判提案自己的 Dᵢ 后重算。

## 2. RQ-2 三次重抽
- 三份留出集：holdout-12（seed 12）、holdout-12b（seed 13）、holdout-12c（seed 14），同一池、同一参数，不排除案例。
- 每份上同日读三个状态：h_s（`chains-formal/ancestor-s`）、3d 链末态（= h₁₂ = 生产）、1d 链末态（`chains-formal/1d/state`）。
- T_tier3_gain(臂) = T_3(臂末态) − T_3(h_s)；三份取均值后做差（三维 − 一维）。A_holdout_diff 同理（全集口径；本体口径需逐案例的层归属，案例文件里没有，留「—」）。
- CI：bootstrap 1000 次，seed 0，按重抽分层——每次在每份留出集内有放回重抽案例，三个状态用同一组案例（配对），重算后取三份均值再做差。
- 判定按 criteria v5 RQ-2：两个差值的 CI 下界均 > −0.10 为通过；任一 ≤ −0.10、或三维臂自身 T_tier3_gain < 0、或三维臂 T_1 相对 h_s 下降 > 0.02（层样本 ≥ 8）为失败；任一 CI 半宽 > 0.10、或三份合并的 tier-3 案例 < 30、或任一链 APPLY_FAIL 占比 > 50% 为功效不足。
- APPLY_FAIL 占比两种读法都报：P-B 链上（补丁冲突，chain.json n_conflict）与 P-A 里该链提案打不上 hᵢ 的比例。

## 3. T1–T5
- `arm_compare.py --rounds 8,9,10,11`（round 11 回退改用 B₁₂ 后重算），`results_tables.py --formal`。T3 的 RQ-2 CI 由本声明第 2 节的计算补入。
