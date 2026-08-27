<template>
  <div class="page-content home-page">
    <van-nav-bar title="小闻新闻" />
    <van-tabs v-model:active="activeTab" sticky offset-top="0" line-width="20">
      <van-tab v-for="cat in categories" :key="cat.id" :title="cat.name">
        <NewsList
          :fetch-page="makeFetchPage(cat.id)"
          :faved-map="favedMap"
          @item-click="goDetail"
          @page-loaded="onPageLoaded"
          @fav-change="onFavChange"
        />
      </van-tab>
    </van-tabs>
    <van-empty v-if="!loadingCategories && !categories.length" description="暂无分类" />
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { getCategories, getNewsList } from '@/api/news'
import { batchCheckFavorite } from '@/api/favorite'
import NewsList from '@/components/NewsList.vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const activeTab = ref(0)
const categories = ref([])
const loadingCategories = ref(true)
// 收藏状态表 { [newsId]: bool }：新闻列表加载后批量查询后端填充，
// 卡片点击收藏/取消时回写——保证重新进入页面 ⭐ 与真实收藏状态一致
const favedMap = ref({})
// 已批量查询过收藏状态的新闻 id 集合（翻页时不重复查询旧 id）
const checkedIds = ref(new Set())

onMounted(async () => {
  try {
    categories.value = (await getCategories()).sort((a, b) => (a.sortOrder ?? 0) - (b.sortOrder ?? 0))
  } catch (e) {
    // 拦截器已提示错误
  } finally {
    loadingCategories.value = false
  }
})

// 每个分类一个分页请求函数
function makeFetchPage(categoryId) {
  return async (page) => {
    const data = await getNewsList({ categoryId, page, pageSize: 10 })
    return data // { list, total, hasMore }
  }
}

function goDetail(item) {
  router.push(`/news/${item.id}`)
}

// 每页新闻加载后：登录态下批量查询该页的收藏状态（未查询过的 id），点亮/熄灭 ⭐
async function onPageLoaded(list) {
  if (!userStore.isLoggedIn || !list.length) return
  const ids = list.map((n) => n.id).filter((id) => !checkedIds.value.has(id))
  if (!ids.length) return
  ids.forEach((id) => checkedIds.value.add(id))
  try {
    const data = await batchCheckFavorite(ids)
    const favoriteSet = new Set(data.favoriteIds)
    for (const id of ids) favedMap.value[id] = favoriteSet.has(id)
  } catch (e) {
    // 拦截器已提示；失败时撤销标记，下次翻页/刷新可重试
    ids.forEach((id) => checkedIds.value.delete(id))
  }
}

// 卡片上点击收藏/取消后回写状态表，保证与后端真实状态一致
function onFavChange({ id, faved }) {
  favedMap.value[id] = faved
}

// 登出时清空收藏状态，避免残留上个账号的数据
watch(
  () => userStore.isLoggedIn,
  (logged) => {
    if (!logged) {
      favedMap.value = {}
      checkedIds.value = new Set()
    }
  }
)
</script>

<style scoped>
/* 底部空隙由 TabLayout 统一提供，避免重复 padding */
</style>
