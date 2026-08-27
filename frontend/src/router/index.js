import { createRouter, createWebHistory } from 'vue-router'
import { getUserInfo } from '@/api/user'

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
  { path: '/forgot-password', name: 'forgot-password', component: () => import('@/views/ResetPasswordView.vue') },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 登录守卫：需登录页未登录 → 跳登录（带 redirect）
// 访问登录/注册页时若本地有 token → 调接口验证有效性：有效才回首页，无效自动清除并放行
router.beforeEach(async (to) => {
  const token = localStorage.getItem('news_agent_token')
  if (to.meta.requiresAuth && !token) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  if ((to.path === '/login' || to.path === '/register' || to.path === '/forgot-password') && token) {
    try {
      await getUserInfo() // 401 时响应拦截器会自动清除本地 token（当前在 /login 页，不会触发跳转）
      return { path: '/' }
    } catch {
      // token 已失效或网络异常：清掉残留登录态，放行登录/注册页
      localStorage.removeItem('news_agent_token')
      localStorage.removeItem('news_agent_user')
    }
  }
  return true
})

export default router
