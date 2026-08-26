<template>
  <div class="news-card" @click="$emit('click', item)">
    <div class="cover">
      <van-image v-if="item.image" :src="item.image" fit="cover" radius="6" lazy-load>
        <template #loading>
          <van-loading size="20" color="#c8c9cc" />
        </template>
        <template #error>
          <div class="cover-error">
            <van-icon name="photo-o" size="22" color="#c8c9cc" />
          </div>
        </template>
      </van-image>
      <div v-else class="cover-placeholder">
        <van-icon name="newspaper-o" size="26" color="#c8c9cc" />
      </div>
    </div>
    <div class="info">
      <div class="title van-ellipsis--l2">{{ item.title }}</div>
      <div class="desc van-ellipsis">{{ item.description || '' }}</div>
      <div class="meta">
        <span class="author">{{ item.author || '小编' }}</span>
        <span class="dot">·</span>
        <span>{{ formatViews(item.views) }} 阅读</span>
        <span class="dot">·</span>
        <span>{{ formatRelativeTime(timeField ? item[timeField] : item.publishTime || item.publishedTime) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { formatRelativeTime, formatViews } from '@/utils/format'

defineProps({
  item: { type: Object, required: true },
  // 历史列表显示浏览时间 viewTime；默认显示发布时间
  timeField: { type: String, default: '' },
})
defineEmits(['click'])
</script>

<style scoped>
.news-card {
  display: flex;
  gap: 10px;
  padding: 12px;
  background: #fff;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}

.news-card + .news-card {
  border-top: 1px solid #f0f0f0;
}

.cover {
  flex-shrink: 0;
  width: 112px;
  height: 84px;
  border-radius: 6px;
  overflow: hidden;
  background: #f2f3f5;
}

.cover-placeholder,
.cover-error {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f2f3f5;
}

.info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.title {
  font-size: 15px;
  font-weight: 500;
  color: #1c1c1e;
  line-height: 1.4;
}

.desc {
  margin-top: 4px;
  font-size: 12px;
  color: #969799;
}

.meta {
  margin-top: auto;
  padding-top: 6px;
  font-size: 11px;
  color: #b0b1b3;
  display: flex;
  align-items: center;
}

.dot {
  margin: 0 4px;
}
</style>
