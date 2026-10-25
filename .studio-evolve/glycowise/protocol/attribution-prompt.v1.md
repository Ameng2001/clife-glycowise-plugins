# 归因提示词模板 v1（两链共用，冻结；v5 (b⁗)）

> 用法：每轮为每条链**各开一个新的独立上下文代理**，把下文 `{…}` 替换后作为完整任务发出。模板正文不得改动；改动即新版本（v2），并须 amend。代理的模型版本记进台账该轮行的 notes。

你是 round {ROUND} 中「{CHAIN} 链」的归因者。任务：在本体当前状态 {STATE_LABEL} 上，对 {WINDOW} 窗口里业务侧标为 wrong 的案例做归因，给每个规则层缺陷各产出一对提案（根因修 + 朴素修），在沙箱里验证，写出补丁、来源案例集、清单文件和归因报告。**你只做归因，不做裁决**：不要运行 gate_decide.py 或 chain_drive.py，不要 git commit，不要改生产代码。全程用中文写文档。

## 背景
这是一个控糖服务的「可执行行业本体」：中间表示（IR）有对象、关系、函数、规则、动作五要素，由引擎编译执行。用户口语经 LLM 路由成意图（动作 + 参数），引擎先让动作的 handler 暂存写入，再评估规则；违反硬规则就回滚并记下规则名。审计轨迹由业务侧逐条标 correct / wrong，wrong 的落成案例，`expect` 是业务侧给出的正确结果，`route` 是窗口当时 LLM 路由出的意图（回放时按它走）。

## 允许读取（只读这些）
仓库根 `/Users/liuyameng/Codes/clife-glycowise-plugins`，`W = .studio-evolve/glycowise`。
- 本链当前状态：`{STATE_DIR}`。
- IR：`studio/changes/glycowise/ontology-map.md`。
- 本轮窗口的反馈、轨迹与路由日志：{WINDOW_FILES}。
- 案例：`W/cases/real/`、`W/cases/sim/`。
- 集合：{SET_FILES}。
- 脚本（只看用法）：`/Users/liuyameng/Codes/astra-studio-plugins/studio-evolve/scripts/runner_onto_engine.py`。

## 禁止读取
- 另一条链的目录 `{OTHER_CHAIN_DIR}`，以及 `W/chains/` 下的任何东西。
- `W/proposals.yaml`、`W/growth-ledger.md`、`W/verdicts/`、`W/arms/`、`W/readings/`、`W/results/`。
- 任何 `attribute-report-*.md`、`handoff-*.md`、`studio/changes/glycowise/proposals/`。
- `git log` / `git show` / `git diff` 的任何输出。
- `/private/tmp/` 下的任何目录，以及论文仓库 `/Users/liuyameng/Codes/self-evolving-foundation-paper/`。
不小心打开了禁读文件，在报告里如实写明。

## 步骤
1. **复现**：用 runner 在本链当前状态上回放本轮 wrong 案例（`--router manual --recordings plugins/glycowise/cq/all_routes.json --family-override W/sets/family-override.yaml --as-of {AS_OF} --repeat 1`）。工作目录 `{WORK_DIR}`。
2. **定位缺陷层**：规则层（出提案）、路由层（只登记）、IR 缺口（登记；manual 回放下测不了则不立案）。读相关规则与 handler，对比同组判对的案例。
3. **每个规则层缺陷出一对提案**，两份都必须让 Dᵢ 通过：根因修按 IR 语义修；朴素修按预登记的机械规则生成（放宽阈值 / 跳过缺参数的校验 / 删掉命中的规则分支 / hard 改 soft / 把 Dᵢ 命中的字面量加进匹配），写明用的是哪一条。编号：提案名从 {NAME_START} 起，proposal 编号从 {NUM_START} 起按 a、b 依次递增。
4. **沙箱验证**：复制本链状态的 `plugins/glycowise` 到 `{WORK_DIR}/sb/<提案名>/plugins/glycowise`，改代码，`diff -u --label a/plugins/glycowise/<文件> --label b/plugins/glycowise/<文件>` 出补丁；`patch -p1 --dry-run -d <本链状态的上一级>` 必须成功、`py_compile` 必须通过、runner 在 Dᵢ 上全过（`--state h_prime --as-of {AS_OF}`）。
5. **误伤面**：只用案例文件估计，不看任何裁决。
6. **产物**（放在 `{OUT_DIR}`）：`P<n>-Di.yaml`、`<提案名>.patch`、`P<n>.md`（Verdict 一节留「⟨待裁决⟩」）、`manifest-r{ROUND}.yaml`（每对先根因后朴素）、`round-{ROUND}.md`（第 0 节逐个列出读过的文件与刻意没读的东西；第 4 节「⟨待裁决⟩」；末节流程问题）。

## 最后回复
每条 wrong 的归属与原因一句话；每份提案的名字、编号、修法一句话、补丁行数、dry-run / 编译 / Dᵢ 结果；产物路径；是否误开禁读文件。
