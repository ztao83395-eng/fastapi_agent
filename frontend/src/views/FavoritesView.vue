<template>
  <div class="page fav-page">
    <van-nav-bar title="我的收藏" left-arrow fixed placeholder @click-left="router.back()">
      <template #right>
        <span v-if="!listEmpty" class="clear-btn" @click="onClear">清空</span>
      </template>
    </van-nav-bar>

    <NewsList ref="listRef" :fetch-page="fetchPage" @item-click="goDetail">
      <template #item="{ item, click }">
        <van-swipe-cell>
          <NewsCard :item="item" :time-field="'favoriteTime'" @click="click" />
          <template #right>
            <van-button square type="danger" text="删除" class="swipe-del" @click="onDelete(item)" />
          </template>
        </van-swipe-cell>
      </template>
    </NewsList>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { showConfirmDialog, showToast } from 'vant'
import { getFavoriteList, clearFavorites, removeFavorite } from '@/api/favorite'
import NewsList from '@/components/NewsList.vue'
import NewsCard from '@/components/NewsCard.vue'

const router = useRouter()
const listRef = ref(null)
const listEmpty = ref(true)

const fetchPage = async (page) => {
  const data = await getFavoriteList(page, 10)
  listEmpty.value = data.list.length === 0
  return data
}

function goDetail(item) {
  router.push(`/news/${item.id}`)
}

async function onDelete(item) {
  try {
    await removeFavorite(item.id)
    showToast('已删除')
    listRef.value?.refresh()
  } catch (e) {
    // 拦截器已提示
  }
}

async function onClear() {
  try {
    await showConfirmDialog({ title: '清空收藏', message: '确定清空全部收藏吗？' })
  } catch (e) {
    return // 取消
  }
  try {
    await clearFavorites()
    showToast('已清空')
    listRef.value?.refresh()
  } catch (e) {
    // 拦截器已提示
  }
}
</script>

<style scoped>
.clear-btn {
  font-size: 13px;
  color: #646566;
}

.swipe-del {
  height: 100%;
}
</style>
