<template>
  <div class="tab-layout">
    <router-view />
    <AppTabbar />
  </div>
</template>

<script setup>
import AppTabbar from '@/components/AppTabbar.vue'
</script>

<style scoped>
.tab-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
/* 给 tab 页底部留出 TabBar 高度 */
.tab-layout :deep(.page-content) {
  padding-bottom: 60px;
}
</style>
