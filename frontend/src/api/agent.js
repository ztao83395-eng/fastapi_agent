import request from './request'

// Agent 工具调用对话（需登录；后端 30s 超时，前端留余量）
export const agentChat = (question) =>
  request.post('/agent/chat', { question }, { timeout: 35000 })

// Agent 流式对话（SSE）：逐字回调渲染，像 ChatGPT 一样边生成边显示
// axios 不支持流式响应，这里用 fetch 手动解析；不走拦截器，需自己带 token
export async function streamAgentChat({ question, sessionId, onToken, onTool, onDone }) {
  const resp = await fetch('/api/agent/chat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${localStorage.getItem('news_agent_token') || ''}`,
    },
    body: JSON.stringify({ question, sessionId }),
  })
  // 非 SSE（如 429 额度用完 / 401 token 失效）时后端返回普通 JSON，手动处理
  const contentType = resp.headers.get('content-type') || ''
  if (!resp.ok || !contentType.includes('text/event-stream')) {
    const body = await resp.json().catch(() => null)
    if (resp.status === 401) {
      // 对齐 request.js 拦截器：清登录态并跳登录页
      localStorage.removeItem('news_agent_token')
      localStorage.removeItem('news_agent_user')
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname + window.location.search)}`
      }
    }
    const err = new Error(body?.message || `请求失败(${resp.status})`)
    err.code = resp.status
    throw err
  }
  // 流式读取：SSE 每行 "data: {json}"，事件之间以空行分隔
  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    let newlineIdx
    while ((newlineIdx = buffer.indexOf('\n')) >= 0) {
      const line = buffer.slice(0, newlineIdx).trim()
      buffer = buffer.slice(newlineIdx + 1)
      if (!line.startsWith('data:')) continue
      const payload = line.slice(5).trim()
      if (payload === '[DONE]') return
      let msg
      try { msg = JSON.parse(payload) } catch { continue }
      if (msg.type === 'token') onToken(msg.content)
      else if (msg.type === 'tool') onTool(msg.message)
      else if (msg.type === 'done') onDone(msg.usage, msg.sessionId)
      else if (msg.type === 'error') throw new Error(msg.message)
    }
  }
}

// —— AI 对话会话历史（登录）——
export const getChatSessions = (page = 1, pageSize = 20) =>
  request.get('/chat/sessions', { params: { page, pageSize } })

export const createChatSession = () =>
  request.post('/chat/sessions')

export const getSessionMessages = (sessionId) =>
  request.get(`/chat/sessions/${sessionId}/messages`)

export const deleteChatSession = (sessionId) =>
  request.delete(`/chat/sessions/${sessionId}`)

// 纯 RAG 检索问答（无需登录）
export const ragAsk = (question) =>
  request.post('/agent/rag', { question }, { timeout: 35000 })

// 今日 token 消耗与额度（需登录）
export const getAgentUsage = () => request.get('/agent/usage')
