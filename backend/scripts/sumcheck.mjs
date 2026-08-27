// 临时验证：问 AI 总结新闻，确认给出内容总结而非只有标题（用后删除）
import { spawn } from 'node:child_process'
import { mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

const PORT = 9337
const profile = mkdtempSync(join(tmpdir(), 'sumcheck-'))
const chrome = spawn('C:/Program Files/Google/Chrome/Application/chrome.exe',
  ['--headless=new', `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`,
   '--no-first-run', '--no-default-browser-check', 'about:blank'],
  { stdio: 'ignore' })
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

try {
  for (let i = 0; i < 50; i++) {
    try { if ((await fetch(`http://127.0.0.1:${PORT}/json/version`)).ok) break } catch {}
    await sleep(200)
  }
  const pages = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()
  const page = pages.find((p) => p.type === 'page') || pages[0]
  const ws = new WebSocket(page.webSocketDebuggerUrl)
  let seq = 0; const pending = new Map()
  ws.onmessage = (ev) => { const m = JSON.parse(ev.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id) } }
  await new Promise((res) => (ws.onopen = res))
  const send = (method, params = {}) => new Promise((res) => { const id = ++seq; pending.set(id, res); ws.send(JSON.stringify({ id, method, params })) })
  const ev = async (expr) => {
    const r = await send('Runtime.evaluate', { expression: expr, returnByValue: true })
    if (r.result?.exceptionDetails) throw new Error('eval: ' + JSON.stringify(r.result.exceptionDetails))
    return r.result?.result?.value
  }
  const waitFor = async (expr, timeoutMs = 60000) => {
    const start = Date.now()
    for (;;) {
      const v = await ev(expr)
      if (v) return v
      if (Date.now() - start > timeoutMs) throw new Error('waitFor timeout: ' + expr)
      await sleep(500)
    }
  }

  await send('Page.enable')
  await send('Page.navigate', { url: 'http://localhost:5173/login' })
  await waitFor(`document.querySelectorAll('.van-field__control').length >= 2`)
  await ev(`(() => { const els = document.querySelectorAll('.van-field__control'); els[0].value = 'test_probe_1'; els[0].dispatchEvent(new Event('input', { bubbles: true })); els[1].value = 'pass123456'; els[1].dispatchEvent(new Event('input', { bubbles: true })) })()`)
  await sleep(200)
  await ev(`document.querySelector('.van-button').click()`)
  await waitFor(`location.pathname === '/'`)
  await send('Page.navigate', { url: 'http://localhost:5173/chat' })
  await waitFor(`!!document.querySelector('.input-field input, .input-field textarea')`)
  // 复现用户问题
  await ev(`(() => { const el = document.querySelector('.input-field input, .input-field textarea'); el.value = '帮我总结一下2024年国家账本公布的内容'; el.dispatchEvent(new Event('input', { bubbles: true })) })()`)
  await sleep(200)
  await ev(`document.querySelector('.send-btn').click()`)
  // 等回答完成（loading 消失）
  await waitFor(`[...document.querySelectorAll('.chat-msg')].length > 2 && !document.querySelector('.loading-bubble')`, 60000)
  await sleep(500)
  const answer = await ev(`JSON.stringify([...document.querySelectorAll('.chat-msg.assistant .markdown-body, .chat-msg.assistant .msg-bubble')].map(b => b.innerText).filter(t => t.length > 20))`)
  console.log('AI 回答:', answer)
  ws.close()
} catch (e) {
  console.error('FAIL:', e.message)
  process.exitCode = 1
} finally {
  chrome.kill()
}
