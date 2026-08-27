<template>
  <div class="chat-page">
    <van-nav-bar title="AI 问答">
      <template #right>
        <van-icon
          v-if="userStore.isLoggedIn"
          name="orders-o"
          size="20"
          color="#323233"
          class="history-btn"
          @click="openHistory"
        />
      </template>
    </van-nav-bar>

    <!-- 会话历史抽屉 -->
    <van-popup v-model:show="showHistory" position="left" :style="{ width: '72%', height: '100%' }">
      <div class="history-panel">
        <div class="history-head">
          <span class="history-title">对话历史</span>
          <van-button size="small" type="primary" round plain @click="onNewSession">＋ 新建对话</van-button>
        </div>
        <div v-if="sessions.length === 0" class="history-empty">暂无对话记录</div>
        <div v-else class="history-list">
          <div
            v-for="s in sessions"
            :key="s.id"
            class="history-item"
            :class="{ active: s.id === currentSessionId }"
            @click="switchSession(s.id)"
          >
            <div class="history-item-main">
              <div class="history-item-title van-ellipsis">{{ s.title }}</div>
              <div class="history-item-meta">{{ formatRelativeTime(s.updatedAt) }} · {{ s.messageCount }} 条</div>
            </div>
            <van-icon name="delete-o" color="#969799" @click.stop="onDeleteSession(s)" />
          </div>
        </div>
      </div>
    </van-popup>

    <!-- 游客模式引导 -->
    <van-notice-bar v-if="!userStore.isLoggedIn" left-icon="info-o" :scrollable="false" wrapable color="#1989fa" background="#e8f3ff">
      <div class="notice-content">
        <span>当前为游客模式，仅知识库检索。登录后可使用完整 AI 能力（搜索、收藏等）</span>
        <span class="login-link" @click="goLogin">去登录</span>
      </div>
    </van-notice-bar>

    <!-- 额度条（登录态） -->
    <div v-else class="quota-bar">
      <van-progress :percentage="usagePercent" :show-pivot="false" :stroke-width="6" color="#1989fa" track-color="#e8e9eb" />
      <span class="quota-text">
        今日已用 {{ usage.todayUsed }} / {{ usage.dailyLimit }} tokens（剩余 {{ usage.remaining }}）
      </span>
    </div>

    <!-- 额度用尽 -->
    <div v-if="quotaExhausted" class="quota-exhausted">
      <van-icon name="warning-o" /> 今日 AI 额度已用完，请明天再来
    </div>

    <!-- 快捷问题 -->
    <div v-if="messages.length === 0" class="quick-area">
      <div class="quick-tip">你可以问我：</div>
      <div class="quick-chips">
        <van-tag v-for="q in quickQuestions" :key="q" class="quick-chip" round plain type="primary" @click="quickSend(q)">
          {{ q }}
        </van-tag>
      </div>
    </div>

    <div ref="msgListRef" class="msg-list">
      <ChatBubble v-for="(m, index) in messages" :key="index" :message="m" @retry="retry" />
    </div>

    <div class="input-bar safe-bottom">
      <van-field
        v-model="input"
        class="input-field"
        :placeholder="quotaExhausted ? '今日额度已用完' : '输入你的问题…'"
        :readonly="quotaExhausted"
        maxlength="500"
        @keyup.enter="send"
      />
      <van-button
        round
        type="primary"
        size="small"
        class="send-btn"
        :loading="sending"
        :disabled="quotaExhausted"
        @click="send"
      >
        发送
      </van-button>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { showConfirmDialog, showToast } from 'vant'
import {
  streamAgentChat, ragAsk, getAgentUsage,
  getChatSessions, getSessionMessages, deleteChatSession,
} from '@/api/agent'
import { useUserStore } from '@/stores/user'
import ChatBubble from '@/components/ChatBubble.vue'
import { formatRelativeTime } from '@/utils/format'

const router = useRouter()
const userStore = useUserStore()

const messages = ref([])
const input = ref('')
const sending = ref(false)
const quotaExhausted = ref(false)
const usage = ref({ todayUsed: 0, dailyLimit: 0, remaining: 0 })
const msgListRef = ref(null)
// —— 会话历史 ——
const showHistory = ref(false)
const sessions = ref([])
const currentSessionId = ref(null)

const usagePercent = computed(() => {
  if (!usage.value.dailyLimit) return 0
  return Math.min(100, Math.round((usage.value.todayUsed / usage.value.dailyLimit) * 100))
})

const quickQuestions = computed(() =>
  userStore.isLoggedIn
    ? ['今天有什么热点新闻？', '我的收藏有哪些？', '帮我收藏一条新闻', '清空我的收藏']
    : ['今天有什么热点新闻？', '最近有什么重要新闻？', '这个网站能做什么？']
)

onMounted(async () => {
  if (userStore.isLoggedIn) {
    await refreshUsage()
    await loadLatestSession() // 自动回显最近一次会话
  }
})

// 进入页面自动回显最近一个会话（相当于 ChatHistory 的"恢复上次对话"）
async function loadLatestSession() {
  try {
    const data = await getChatSessions(1, 1)
    const latest = data.list[0]
    if (!latest) return
    currentSessionId.value = latest.id
    const msgData = await getSessionMessages(latest.id)
    messages.value = msgData.list.map((m) => ({ role: m.role, content: m.content }))
    scrollToBottom()
  } catch (e) {
    // 拦截器已提示
  }
}

// 刷新抽屉里的会话列表
async function refreshSessions() {
  try {
    const data = await getChatSessions(1, 50)
    sessions.value = data.list
  } catch (e) {
    // 拦截器已提示
  }
}

function openHistory() {
  refreshSessions()
  showHistory.value = true
}

// 新建对话：清空对话区，发首问时后端自动建会话（done 事件回传 sessionId）
async function onNewSession() {
  messages.value = []
  currentSessionId.value = null
  showHistory.value = false
}

// 切换会话：加载该会话的全部消息
async function switchSession(id) {
  try {
    const msgData = await getSessionMessages(id)
    messages.value = msgData.list.map((m) => ({ role: m.role, content: m.content }))
    currentSessionId.value = id
    showHistory.value = false
    scrollToBottom()
  } catch (e) {
    // 拦截器已提示
  }
}

// 删除会话
async function onDeleteSession(s) {
  try {
    await showConfirmDialog({ title: '删除会话', message: `确定删除「${s.title}」吗？` })
  } catch (e) {
    return // 取消
  }
  try {
    await deleteChatSession(s.id)
    sessions.value = sessions.value.filter((x) => x.id !== s.id)
    if (currentSessionId.value === s.id) {
      currentSessionId.value = null
      messages.value = []
    }
    showToast('已删除')
  } catch (e) {
    // 拦截器已提示
  }
}

function goLogin() {
  router.push({ path: '/login', query: { redirect: '/chat' } })
}

async function refreshUsage() {
  try {
    usage.value = await getAgentUsage()
    quotaExhausted.value = usage.value.remaining <= 0
  } catch (e) {
    // 拦截器已提示
  }
}

function scrollToBottom() {
  nextTick(() => {
    const el = msgListRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

async function send() {
  const text = input.value.trim()
  if (!text || sending.value || quotaExhausted.value) return
  messages.value.push({ role: 'user', content: text })
  input.value = ''
  // 用 reactive 包装：流式回调里逐字段修改（content/toolMsg/loading）都必须走响应式追踪，
  // 普通对象 push 进 ref 数组后修改不触发渲染，气泡会永远卡在"思考中…"
  const pending = reactive({ role: 'assistant', content: '', question: text, loading: true, toolMsg: '' })
  messages.value.push(pending)
  sending.value = true
  scrollToBottom()
  try {
    if (userStore.isLoggedIn) {
      // 登录：Agent 流式对话，token 逐个到达，边生成边渲染
      await streamAgentChat({
        question: text,
        sessionId: currentSessionId.value,
        onToken: (t) => {
          pending.content += t
          scrollToBottom()
        },
        onTool: (m) => {
          pending.toolMsg = m
          scrollToBottom()
        },
        onDone: (usageData, sid) => {
          pending.usage = usageData
          // 新会话时后端自动建会话并回传 sessionId，绑定为当前会话
          if (sid && currentSessionId.value !== sid) currentSessionId.value = sid
        },
      })
      pending.loading = false
      if (!pending.content) pending.content = '（暂无内容返回）'
      await refreshUsage()
      refreshSessions() // 会话列表标题/条数变化，静默刷新
    } else {
      // 游客：纯 RAG，一次性返回
      const data = await ragAsk(text)
      pending.loading = false
      pending.content = data.answer || '（暂无内容返回）'
      pending.usage = data.usage
    }
  } catch (e) {
    pending.loading = false
    pending.error = true
    pending.content = pending.content || e.msg || e.message || '请求失败，点击重试'
    if (e.code === 429) quotaExhausted.value = true
  } finally {
    sending.value = false
    scrollToBottom()
  }
}

// 点击错误气泡重试：移除错误气泡及其问题，重新发送
function retry(msg) {
  if (sending.value || quotaExhausted.value) return
  const idx = messages.value.indexOf(msg)
  if (idx <= 0) return
  const question = messages.value[idx - 1].content
  messages.value.splice(idx - 1)
  input.value = question
  send()
}

function quickSend(q) {
  input.value = q
  send()
}
</script>

<style scoped>
.chat-page {
  /* 100vh 减去底部 TabBar 高度（50px），否则 TabBar 会被推出屏幕 */
  height: calc(100vh - 50px);
  display: flex;
  flex-direction: column;
  background: #f0f2f5;
}

.notice-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.login-link {
  flex-shrink: 0;
  font-weight: 600;
  color: #1989fa;
  cursor: pointer;
}

.quota-bar {
  padding: 10px 12px;
  background: #fff;
}

.quota-text {
  display: block;
  margin-top: 6px;
  font-size: 11px;
  color: #969799;
}

.quota-exhausted {
  padding: 8px 12px;
  font-size: 12px;
  color: #d9534f;
  background: #fff4f4;
}

.quick-area {
  padding: 24px 16px 8px;
}

.quick-tip {
  font-size: 13px;
  color: #969799;
  margin-bottom: 12px;
}

.quick-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.quick-chip {
  padding: 6px 12px;
  font-size: 13px;
}

.msg-list {
  flex: 1;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

.input-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #fff;
  border-top: 1px solid #ebedf0;
}

.input-field {
  flex: 1;
  background: #f2f3f5;
  border-radius: 18px;
  padding: 0 12px;
}

.send-btn {
  flex-shrink: 0;
  min-width: 64px;
}

/* —— 会话历史抽屉 —— */
.history-btn {
  padding: 4px;
}

.history-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f7f8fa;
}

.history-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  background: #fff;
  border-bottom: 1px solid #ebedf0;
}

.history-title {
  font-size: 16px;
  font-weight: 600;
  color: #1c1c1e;
}

.history-empty {
  padding: 60px 0;
  text-align: center;
  font-size: 13px;
  color: #969799;
}

.history-list {
  flex: 1;
  overflow-y: auto;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: #fff;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}

.history-item + .history-item {
  border-top: 1px solid #f2f3f5;
}

.history-item.active {
  background: #e8f3ff;
}

.history-item-main {
  flex: 1;
  min-width: 0;
}

.history-item-title {
  font-size: 14px;
  color: #323233;
}

.history-item-meta {
  margin-top: 3px;
  font-size: 11px;
  color: #b0b1b3;
}
</style>
