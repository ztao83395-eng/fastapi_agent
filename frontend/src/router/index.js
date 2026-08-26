import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'home', component: () => import('@/views/HomeView.vue'), meta: { tab: true } },
  { path: '/news/:id', name: 'news-detail', component: () => import('@/views/NewsDetailView.vue') },
  { path: '/chat', name: 'chat', component: () => import('@/views/ChatView.vue'), meta: { tab: true } },
  { path: '/profile', name: 'profile', component: () => import('@/views/ProfileView.vue'), meta: { tab: true, requiresAuth: true } },
  { path: '/profile/edit', name: 'profile-edit', component: () => import('@/views/ProfileEditView.vue'), meta: { requiresAuth: true } },
  { path: '/profile/password', name: 'profile-password', component: () => import('@/views/PasswordEditView.vue'), meta: { requiresAuth: true } },
  { path: '/favorites', name: 'favorites', component: () => import('@/views/FavoritesView.vue'), meta: { requiresAuth: true } },
  { path: '/history', name: 'history', component: () => import('@/views/HistoryView.vue'), meta: { requiresAuth: true } },
  { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue') },
  { path: '/register', name: 'register', component: () => import('@/views/RegisterView.vue') },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 登录守卫：需登录页未登录 → 跳登录（带 redirect）；已登录访问登录/注册 → 回首页
router.beforeEach((to) => {
  const token = localStorage.getItem('news_agent_token')
  if (to.meta.requiresAuth && !token) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  if ((to.path === '/login' || to.path === '/register') && token) {
    return { path: '/' }
  }
  return true
})

export default router
