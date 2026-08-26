<template>
  <div class="page detail-page">
    <van-nav-bar
      title="新闻详情"
      left-arrow
      fixed
      placeholder
      @click-left="router.back()"
    >
      <template #right>
        <van-icon
          :name="isFavorite ? 'star' : 'star-o'"
          :color="isFavorite ? '#ffc300' : '#646566'"
          size="20"
          @click="toggleFavorite"
        />
      </template>
    </van-nav-bar>

    <van-loading v-if="loading" class="detail-loading" size="24" vertical>加载中…</van-loading>

    <template v-else-if="detail">
      <div class="detail-head">
        <h1 class="detail-title">{{ detail.title }}</h1>
        <div class="detail-meta">
          <span>{{ detail.author || '小编' }}</span>
          <span>·</span>
          <span>{{ formatDateTime(detail.publishTime) }}</span>
          <span>·</span>
          <span>{{ formatViews(detail.views) }} 阅读</span>
        </div>
        <van-image v-if="detail.image" :src="detail.image" fit="cover" radius="8" lazy-load>
          <template #loading>
            <van-loading size="24" color="#c8c9cc" />
          </template>
          <template #error>
            <div class="detail-img-error">
              <van-icon name="photo-o" size="32" color="#c8c9cc" />
            </div>
          </template>
        </van-image>
      </div>
      <div class="detail-content">{{ detail.content }}</div>

      <div v-if="detail.relatedNews?.length" class="related">
        <div class="related-title">相关推荐</div>
        <div
          v-for="item in detail.relatedNews"
          :key="item.id"
          class="related-item"
          @click="router.push(`/news/${item.id}`)"
        >
          <span class="related-text van-ellipsis">{{ item.title }}</span>
          <van-icon name="arrow" color="#c8c9cc" />
        </div>
      </div>
      <div class="safe-bottom" />
    </template>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast } from 'vant'
import { getNewsDetail } from '@/api/news'
import { checkFavorite, addFavorite, removeFavorite } from '@/api/favorite'
import { addHistory } from '@/api/history'
import { useUserStore } from '@/stores/user'
import { formatDateTime, formatViews } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const newsId = Number(route.params.id)
const detail = ref(null)
const loading = ref(true)
const isFavorite = ref(false)

onMounted(async () => {
  try {
    detail.value = await getNewsDetail(newsId)
  } catch (e) {
    if (e.code !== 404) showToast('新闻加载失败')
  } finally {
    loading.value = false
  }
  // 登录后：静默上报浏览历史 + 查询收藏状态
  if (userStore.isLoggedIn) {
    addHistory(newsId).catch(() => {})
    checkFavorite(newsId)
      .then((data) => { isFavorite.value = data.isFavorite })
      .catch(() => {})
  }
})

async function toggleFavorite() {
  if (!userStore.isLoggedIn) {
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }
  try {
    if (isFavorite.value) {
      await removeFavorite(newsId)
      isFavorite.value = false
      showToast('已取消收藏')
    } else {
      await addFavorite(newsId)
      isFavorite.value = true
      showToast('收藏成功')
    }
  } catch (e) {
    // 拦截器已提示
  }
}
</script>

<style scoped>
.detail-page {
  background: #fff;
}

.detail-loading {
  padding: 60px 0;
}

.detail-img-error {
  height: 180px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f2f3f5;
  border-radius: 8px;
}

.detail-head {
  padding: 16px;
}

.detail-title {
  font-size: 20px;
  font-weight: 600;
  line-height: 1.4;
  color: #1c1c1e;
}

.detail-meta {
  display: flex;
  gap: 6px;
  align-items: center;
  font-size: 12px;
  color: #969799;
  margin: 10px 0 14px;
}

.detail-content {
  padding: 0 16px 24px;
  font-size: 15px;
  line-height: 1.8;
  color: #323233;
  white-space: pre-line;
  word-break: break-word;
}

.related {
  margin: 0 16px 20px;
  border-top: 8px solid #f7f8fa;
  padding-top: 12px;
}

.related-title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 8px;
}

.related-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px solid #f2f3f5;
  cursor: pointer;
}

.related-text {
  font-size: 14px;
  color: #323233;
}
</style>
