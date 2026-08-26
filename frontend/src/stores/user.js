import { defineStore } from 'pinia'
import {
  login as apiLogin,
  register as apiRegister,
  getUserInfo,
  updateUser,
  updatePassword,
} from '@/api/user'

const TOKEN_KEY = 'news_agent_token'
const USER_KEY = 'news_agent_user'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem(TOKEN_KEY) || '',
    userInfo: JSON.parse(localStorage.getItem(USER_KEY) || 'null'),
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
    nickname: (state) => state.userInfo?.nickname || state.userInfo?.username || '未登录',
    avatar: (state) => state.userInfo?.avatar || '',
  },
  actions: {
    _setAuth(data) {
      this.token = data.token
      this.userInfo = data.userInfo
      localStorage.setItem(TOKEN_KEY, data.token)
      localStorage.setItem(USER_KEY, JSON.stringify(data.userInfo))
    },
    async login(payload) {
      const data = await apiLogin(payload)
      this._setAuth(data)
      return data
    },
    async register(payload) {
      const data = await apiRegister(payload)
      this._setAuth(data)
      return data
    },
    async fetchUserInfo() {
      const info = await getUserInfo()
      this.userInfo = info
      localStorage.setItem(USER_KEY, JSON.stringify(info))
      return info
    },
    async updateProfile(payload) {
      const info = await updateUser(payload)
      this.userInfo = { ...this.userInfo, ...info }
      localStorage.setItem(USER_KEY, JSON.stringify(this.userInfo))
      return info
    },
    async updatePassword(payload) {
      return updatePassword(payload)
    },
    logout() {
      this.token = ''
      this.userInfo = null
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
    },
  },
})
