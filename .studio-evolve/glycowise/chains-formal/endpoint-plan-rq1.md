# RQ-1 / RQ-3 补做三次留出集重抽 —— seed 表与计算口径（先于任何补抽读数提交）

> 依据：导师裁定 `proposal/advisor-ruling-2026-10-25b.md` §3（论文仓库）；criteria v5 RQ-1 protocol「三次留出集重抽的结果合并计 n 但 CI 按重抽分层」。协议偏离 D-6 见 `protocol-deviations.md`。裁决不重跑：各轮各臂接受集照旧，只重算回退读数。

## 1. 每轮的三份 B_{i+1}

`holdout_sample.py --cases-dir cases --round <R+1> --seed <s> --holdout-size 100 --stratify family,tier --merge-min 8 --family-override sets/family-override.yaml --exclude-file <E> --out sets/holdout-<R+1>-s<s>.yaml`

| 判定的轮次 R | B | seed | 池（重建为当轮抽样时的池） | 排除 E | 判定前剔除 |
|---|---|---|---|---|---|
| 8 | B₉ | 9, 10, 11 | 现池减 real-W53、real-W54 → 495 | r9 D⁻ 候选（15） | targeted-W52 |
| 9 | B₁₀ | 10, 11, 12 | 现池减 real-W54 → 570 | r10 D⁻ 候选（37） | targeted-W53 |
| 10 | B₁₁ | 11, 12, 13 | 现池 669 | r11 D⁻ 候选（27） | targeted-W54 |
| 11 | B₁₂ | 12, 13, 14 | 现池 669 | 无（D₁₂ = ∅） | 无 |

- 规则沿用 RQ-2：每轮第一份 seed = 原留出集的 seed，后两份顺延。第一份必须与原 `holdout-<R+1>.yaml` 逐条相同，用来证明池重建正确；不相同即停止并报告，不改 seed。
- round 11 的三份就是 RQ-2 已用的 holdout-12 / 12b / 12c。
- 排除集 E 写成临时文件（D⁻ 候选 ∪ 后续窗口案例），文件随结果提交。

## 2. 计算

- 每份 B 上同日（--as-of 2026-10-25）读 hᵢ 与每份被判提案的 h′（沙箱与原裁决相同：round 8 为 h_s + 补丁，round 9–11 为当轮 3d 链起点 + 补丁）。三份全部重新计算，包括与原留出集相同的第一份。
- 回退判定照 criteria：A_holdout 下降 > 0，或样本 ≥ 8 的 tier 层 T_k 下降 > 0.02 → regress = 1；单条口径 regress_any 并排。
- 合并：regress_rate(臂) = 该臂接受集 × 三份留出集上 regress 的均值（n = 3 × n_accept）。
- CI：配对 bootstrap 1000 次，seed 0，按重抽分层——每次在每份留出集内、按轮次对提案有放回重抽（各臂用同一组抽样），三份合并后算各臂比例再做差。
- 同时报告不含定向补充案例（剔除 targeted-W50…W54 全部）的版本。

## 3. 之后

作废 r-2026-10-25-0001 / 0004（以及 0002 / 0003、辅助量 0012～0018）并按三次重抽重录，seeds = 3；rollup 重算。正文按新数字改写，单份留出集的旧读数移附录并注明来源。
