<template>
  <div class="page auth-page">
    <div class="auth-head">
      <div class="auth-logo">📰</div>
      <div class="auth-title">欢迎回来</div>
      <div class="auth-sub">登录小闻新闻，享受 AI 智能问答</div>
    </div>
    <van-form @submit="onSubmit" class="auth-form">
      <van-cell-group inset>
        <van-field
          v-model="form.username"
          name="username"
          label="用户名"
          placeholder="请输入用户名"
          :rules="[{ required: true, message: '请输入用户名' }]"
        />
        <van-field
          v-model="form.password"
          type="password"
          name="password"
          label="密码"
          placeholder="请输入密码"
          :rules="[{ required: true, message: '请输入密码' }]"
        />
      </van-cell-group>
      <div class="auth-btn">
        <van-button round block type="primary" native-type="submit" :loading="submitting">
          登 录
        </van-button>
      </div>
    </van-form>
    <div class="auth-footer">
      还没有账号？
      <span class="link" @click="router.push('/register')">立即注册</span>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast } from 'vant'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const form = ref({ username: '', password: '' })
const submitting = ref(false)

async function onSubmit() {
  submitting.value = true
  try {
    await userStore.login(form.value)
    showToast('登录成功')
    router.replace(route.query.redirect || '/')
  } catch (e) {
    // 拦截器已提示
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.auth-page {
  background: #fff;
  min-height: 100vh;
}

.auth-head {
  padding: 48px 24px 32px;
  text-align: center;
}

.auth-logo {
  font-size: 52px;
}

.auth-title {
  font-size: 24px;
  font-weight: 600;
  margin-top: 12px;
}

.auth-sub {
  font-size: 13px;
  color: #969799;
  margin-top: 8px;
}

.auth-form {
  padding: 8px 0;
}

.auth-btn {
  padding: 24px 20px;
}

.auth-footer {
  text-align: center;
  font-size: 13px;
  color: #969799;
}

.link {
  color: #1989fa;
  cursor: pointer;
}
</style>
