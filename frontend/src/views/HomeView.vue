<template>
  <div class="page-content home-page">
    <van-nav-bar title="小闻新闻" />
    <van-tabs v-model:active="activeTab" sticky offset-top="0" line-width="20">
      <van-tab v-for="cat in categories" :key="cat.id" :title="cat.name">
        <NewsList :fetch-page="makeFetchPage(cat.id)" @item-click="goDetail" />
      </van-tab>
    </van-tabs>
    <van-empty v-if="!loadingCategories && !categories.length" description="暂无分类" />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getCategories, getNewsList } from '@/api/news'
import NewsList from '@/components/NewsList.vue'

const router = useRouter()
const activeTab = ref(0)
const categories = ref([])
const loadingCategories = ref(true)

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
</script>

<style scoped>
.home-page {
  padding-bottom: 60px;
}
</style>
