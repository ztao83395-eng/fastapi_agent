<template>
  <div class="chat-page">
    <van-nav-bar title="AI 问答" />

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
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { agentChat, ragAsk, getAgentUsage } from '@/api/agent'
import { useUserStore } from '@/stores/user'
import ChatBubble from '@/components/ChatBubble.vue'

const router = useRouter()
const userStore = useUserStore()

const messages = ref([])
const input = ref('')
const sending = ref(false)
const quotaExhausted = ref(false)
const usage = ref({ todayUsed: 0, dailyLimit: 0, remaining: 0 })
const msgListRef = ref(null)

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
  if (userStore.isLoggedIn) await refreshUsage()
})

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
  const pending = { role: 'assistant', content: '', question: text, loading: true }
  messages.value.push(pending)
  sending.value = true
  scrollToBottom()
  try {
    // 登录走 Agent 工具调用，游客走纯 RAG
    const data = userStore.isLoggedIn ? await agentChat(text) : await ragAsk(text)
    pending.loading = false
    pending.content = data.answer || '（暂无内容返回）'
    pending.usage = data.usage
    if (userStore.isLoggedIn) await refreshUsage()
  } catch (e) {
    pending.loading = false
    pending.error = true
    pending.content = e.msg || e.message || '请求失败，点击重试'
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
  height: 100vh;
  display: flex;
  flex-direction: column;
  padding-bottom: 50px; /* TabBar 高度，避免遮挡输入栏 */
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
</style>
