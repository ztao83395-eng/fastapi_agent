# Agent 评测报告

生成时间：2026-08-17 23:40

## RAG 问答质量

| 指标 | 平均分 (0-5) |
|---|---|
| 忠实度 | - |
| 上下文相关性 | - |
| 答案相关性 | - |

### 用例明细

- ❌ **最近有什么关于人工智能的新闻？** — 失败: status_code: 400 
 code: Arrearage 
 message: Access denied, please make sure your account is in good standing. For details, see: https://help.aliyun.com/zh/model-studio/error-code#overdue-payment

## 结论

- 指标 < 3 分的部分建议针对性优化：检索质量差 → 检查向量库/embedding；忠实度低 → 检查提示词与上下文截断。