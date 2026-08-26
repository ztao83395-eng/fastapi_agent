import request from './request'

// Agent 工具调用对话（需登录；后端 30s 超时，前端留余量）
export const agentChat = (question) =>
  request.post('/agent/chat', { question }, { timeout: 35000 })

// 纯 RAG 检索问答（无需登录）
export const ragAsk = (question) =>
  request.post('/agent/rag', { question }, { timeout: 35000 })

// 今日 token 消耗与额度（需登录）
export const getAgentUsage = () => request.get('/agent/usage')
