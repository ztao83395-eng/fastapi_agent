import axios from 'axios'
import { showToast } from 'vant'
import { camelizeKeys } from '@/utils/normalizers'

const TOKEN_KEY = 'news_agent_token'
const USER_KEY = 'news_agent_user'

const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 15000,
})

// 请求拦截器：自动附加 Bearer token
service.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// 响应拦截器：解包 data、业务码/401 统一处理、字段规范化
service.interceptors.response.use(
  (response) => {
    const res = response.data
    if (res && typeof res === 'object' && 'code' in res) {
      if (res.code !== 200) {
        const err = new Error(res.message || '请求失败')
        err.code = res.code
        err.msg = res.message
        showToast(err.msg)
        return Promise.reject(err)
      }
      // 直接返回业务 data；特殊请求（如 markdown 原文）可用 skipNormalize 关闭
      const data = response.config.skipNormalize ? res.data : camelizeKeys(res.data)
      return data
    }
    return response.data
  },
  (error) => {
    const status = error.response?.status
    if (status === 401) {
      // token 无效/过期：清除本地登录态并跳登录页
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
      const { pathname, search } = window.location
      if (!pathname.startsWith('/login')) {
        window.location.href = `/login?redirect=${encodeURIComponent(pathname + search)}`
      }
    } else {
      showToast(error.response?.data?.detail || '网络异常，请稍后重试')
    }
    const err = new Error(error.message || '请求失败')
    err.code = status
    return Promise.reject(err)
  }
)

export default service
