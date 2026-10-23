# .studio-evolve/glycowise — 自生长运行时工作区

- `config.yaml`：闸门参数（β=0.05、window 20、单骨干）。`trajectory_source` 与 `sources` 为 TODO(FDE)：引擎审计日志与真实数据源尚未接入，所以 `cases/real/` 为空，外关卡无法开。
- `cases/sim/`：28 条黄金问题（`cq/golden.yaml` 经 `runner_onto_engine.py golden-to-cases` 转出，family=golden，origin=sim，只进内关卡）。
- `growth-ledger.md`：成长台账。生产裁决只用 `gate_mode=3d`；论文对照臂（1d / none / random / 消融）的裁决写到论文仓 `runs/`，不写进这里。
- `verdicts/`：3d 裁决的 verdict.json。
