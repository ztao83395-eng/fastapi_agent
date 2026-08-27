<template>
  <!-- tab 页（新闻/AI 问答/我的）套 TabLayout 显示底部 TabBar；其他页纯路由视图 -->
  <TabLayout v-if="route.meta.tab" />
  <router-view v-else />
</template>

<script setup>
import { useRoute } from 'vue-router'
import TabLayout from '@/layouts/TabLayout.vue'

const route = useRoute()
</script>
