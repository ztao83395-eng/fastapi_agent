<template>
  <div class="chat-msg" :class="message.role">
    <div v-if="message.role === 'assistant'" class="msg-avatar assistant">🤖</div>
    <div class="msg-main">
      <div v-if="message.loading" class="msg-bubble loading-bubble">
        <van-loading size="14" color="#1989fa" />
        <span>思考中…</span>
      </div>
      <div v-else-if="message.error" class="msg-bubble error-bubble" @click="emit('retry', message)">
        <div>{{ message.content }}</div>
        <div class="retry-tip">⚠ 点击此条重试</div>
      </div>
      <div v-else class="msg-bubble" :class="{ 'markdown-body': message.role === 'assistant' }">
        <div v-if="message.role === 'user'" v-text="message.content"></div>
        <div v-else v-html="rendered"></div>
      </div>
      <div v-if="message.usage?.totalTokens" class="msg-usage">
        本次消耗 {{ message.usage.totalTokens }} tokens
      </div>
    </div>
    <div v-if="message.role === 'user'" class="msg-avatar user">😊</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { renderMarkdown } from '@/utils/markdown'

const props = defineProps({
  message: { type: Object, required: true }, // { role, content, loading, error, usage }
})
const emit = defineEmits(['retry'])

const rendered = computed(() => renderMarkdown(props.message.content || ''))
</script>

<style scoped>
.chat-msg {
  display: flex;
  gap: 8px;
  padding: 10px 12px;
}

.chat-msg.user {
  flex-direction: row-reverse;
}

.msg-avatar {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.msg-avatar.assistant {
  background: #1989fa;
}

.msg-avatar.user {
  background: #07c160;
}

.msg-main {
  max-width: 78%;
  display: flex;
  flex-direction: column;
}

.chat-msg.user .msg-main {
  align-items: flex-end;
}

.msg-bubble {
  padding: 9px 12px;
  border-radius: 10px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
}

.chat-msg.assistant .msg-bubble {
  background: #fff;
  border-top-left-radius: 2px;
  color: #323233;
}

.chat-msg.user .msg-bubble {
  background: #1989fa;
  color: #fff;
  border-top-right-radius: 2px;
}

.loading-bubble {
  background: #fff !important;
  color: #969799 !important;
  display: flex;
  align-items: center;
  gap: 6px;
}

.error-bubble {
  background: #fff7f7 !important;
  border: 1px solid #f7d4d4;
  color: #d9534f !important;
}

.retry-tip {
  font-size: 11px;
  margin-top: 4px;
  opacity: 0.8;
}

.msg-usage {
  font-size: 10px;
  color: #b0b1b3;
  margin-top: 3px;
}
</style>
