<template>
  <van-pull-refresh v-model="refreshing" @refresh="wrappedRefresh">
    <van-list
      v-model:loading="loading"
      :finished="finished"
      :finished-text="list.length ? '没有更多了' : ''"
      :immediate-check="immediate"
      @load="wrappedLoadPage"
    >
      <template v-for="item in list" :key="item.id">
        <slot name="item" :item="item" :click="(i) => emit('item-click', i)">
          <NewsCard
            :item="item"
            :time-field="timeField"
            :faved="favedMap[item.id] || false"
            @click="emit('item-click', item)"
            @fav-change="(f) => emit('fav-change', { id: item.id, faved: f })"
          />
        </slot>
      </template>
      <van-empty v-if="!loading && failed && !list.length" description="加载失败">
        <van-button size="small" type="primary" round @click="onRefresh">点击重试</van-button>
      </van-empty>
      <van-empty v-else-if="!loading && !failed && !list.length" description="暂无数据" />
    </van-list>
  </van-pull-refresh>
</template>

<script setup>
import { onMounted } from 'vue'
import NewsCard from '@/components/NewsCard.vue'
import { usePagedList } from '@/composables/usePagedList'

const props = defineProps({
  // (page) => Promise<{ list, hasMore }>
  fetchPage: { type: Function, required: true },
  immediate: { type: Boolean, default: true },
  timeField: { type: String, default: '' },
  // 收藏状态表 { [newsId]: bool }，由父组件批量查询后传入，透传给每张卡片
  favedMap: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['item-click', 'page-loaded', 'fav-change'])

const {
  list, loading, finished, refreshing, failed, loadPage, onRefresh, refresh,
} = usePagedList(props.fetchPage)

// 包装分页加载：每页（含下拉刷新）加载完成后把当前全部新闻上报给父组件，
// 父组件据此批量查询收藏状态，点亮/熄灭 ⭐
async function wrappedLoadPage() {
  await loadPage()
  emit('page-loaded', list.value)
}

async function wrappedRefresh() {
  await onRefresh()
  emit('page-loaded', list.value)
}

onMounted(() => {
  // 必须走包装函数：裸调 loadPage 会同步置 loading=true，
  // 抢在 van-list 的 immediate-check 之前，导致首次 @load 被跳过、page-loaded 永远不 emit
  if (props.immediate) wrappedLoadPage()
})

defineExpose({ refresh })
</script>
