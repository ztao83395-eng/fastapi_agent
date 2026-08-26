<template>
  <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
    <van-list
      v-model:loading="loading"
      :finished="finished"
      :finished-text="list.length ? '没有更多了' : ''"
      :immediate-check="immediate"
      @load="loadPage"
    >
      <template v-for="item in list" :key="item.id">
        <slot name="item" :item="item" :click="(i) => emit('item-click', i)">
          <NewsCard
            :item="item"
            :time-field="timeField"
            @click="emit('item-click', item)"
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
})
const emit = defineEmits(['item-click'])

const {
  list, loading, finished, refreshing, failed, loadPage, onRefresh, refresh,
} = usePagedList(props.fetchPage)

onMounted(() => {
  if (props.immediate) loadPage()
})

defineExpose({ refresh })
</script>
