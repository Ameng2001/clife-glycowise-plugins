# round 7 演练 · 协议偏离记录

## D-1（2026-10-24）：3d 链归因未隔一天，改用独立上下文

- **条文**：criteria v4 (b)（冻结，2026-10-24T16:25）——两链归因「间隔 ≥ 1 天、不回看」；v5 草案 (b″) 规定演练照 v4 (b) 做。
- **实际**：1d 链归因于 2026-10-24 17:09 提交（glycowise 8799a75）；3d 链归因于同日由**新开的独立上下文代理**执行，未间隔一天。
- **决定人**：用户（2026-10-24），理由：AI 归因者在同一会话隔一天不会遗忘前一条链的补丁与推理，间隔不起隔离作用；独立上下文才真正隔离。
- **隔离措施**：代理只拿到 h₇（`chains-r7/ancestor-h7`）、W50 / W50b 的 feedback 与路由日志、`cases/`、IR、若干 `sets/`；明文禁读 `chains-r7/1d/`、`chains/`、`proposals.yaml`、`growth-ledger.md`、`verdicts/`、`arms/`、`readings/`、`results/`、全部归因报告与交接、`studio/changes/glycowise/proposals/`、git 历史、`/private/tmp/`、论文仓库；要求在归因报告第 0 节逐项列出读过的文件。只给了提案编号起点（P22 / 28），未告知 1d 链提案内容与数量。
- **残余泄漏**：编号起点 P22 / 28 间接表明另一条链本轮出了 4 份提案；`chains-r7/reading-h7-real-all-W50.json` 等 h₇ 读数文件在允许目录的上一级、未列入禁读。
- **影响**：round 7 本来就是探索性演练，不进任何 formal 判定。
- **后续**：把「AI 归因用独立上下文代替间隔一天」作为 v5 第五点 (b⁗) 报导师（paper `proposal/amend-v5.draft.md` §2.1c）。
