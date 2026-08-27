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
        <span
          v-if="showFav"
          class="fav-star"
          :class="{ active: faved }"
          @click.stop="toggleFav"
        >{{ faved ? '⭐' : '☆' }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { showToast } from 'vant'
import { formatRelativeTime, formatViews } from '@/utils/format'
import { addFavorite, removeFavorite } from '@/api/favorite'
import { useUserStore } from '@/stores/user'

const props = defineProps({
  item: { type: Object, required: true },
  // 历史列表显示浏览时间 viewTime；默认显示发布时间
  timeField: { type: String, default: '' },
  // 收藏/历史列表传 false（它们有自己的删除交互），其余列表默认显示
  showFav: { type: Boolean, default: true },
  // 收藏状态由父组件受控传入（列表页加载后批量查询后端填充），
  // 卡片本身不再内部查询，点击后通过 fav-change 事件回传给父组件统一维护
  faved: { type: Boolean, default: false },
})
const emit = defineEmits(['click', 'fav-change'])

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

async function toggleFav() {
  if (!userStore.isLoggedIn) {
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }
  try {
    if (props.faved) {
      await removeFavorite(props.item.id)
      emit('fav-change', false)
      showToast('已取消收藏')
    } else {
      // add 接口幂等（重复收藏返回原记录），本地状态与真实状态偶有偏差也能自愈
      await addFavorite(props.item.id)
      emit('fav-change', true)
      showToast('收藏成功')
    }
  } catch (e) {
    // 拦截器已提示
  }
}
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

.fav-star {
  margin-left: auto;
  padding: 0 2px;
  font-size: 15px;
  line-height: 1;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
}

.fav-star.active {
  /* 保持视觉一致，颜色由 emoji 自带 */
}
</style>
