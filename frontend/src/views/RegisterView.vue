<template>
  <div class="page auth-page">
    <div class="auth-head">
      <div class="auth-logo">📰</div>
      <div class="auth-title">创建账号</div>
      <div class="auth-sub">注册成功即自动登录</div>
    </div>
    <van-form @submit="onSubmit" class="auth-form">
      <van-cell-group inset>
        <van-field
          v-model="form.username"
          name="username"
          label="用户名"
          placeholder="请输入用户名"
          :rules="[
            { required: true, message: '请输入用户名' },
            { pattern: /^[a-zA-Z0-9_]{3,20}$/, message: '3-20位字母、数字或下划线' },
          ]"
        />
        <van-field
          v-model="form.password"
          type="password"
          name="password"
          label="密码"
          placeholder="请输入密码（至少 6 位）"
          :rules="[{ required: true, pattern: /^\S{6,}$/, message: '密码至少 6 位' }]"
        />
        <van-field
          v-model="form.confirm"
          type="password"
          name="confirm"
          label="确认密码"
          placeholder="请再次输入密码"
          :rules="[{ validator: checkConfirm, message: '两次密码不一致' }]"
        />
      </van-cell-group>
      <div class="auth-btn">
        <van-button round block type="primary" native-type="submit" :loading="submitting">
          注 册
        </van-button>
      </div>
    </van-form>
    <div class="auth-footer">
      已有账号？
      <span class="link" @click="router.push('/login')">去登录</span>
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

const form = ref({ username: '', password: '', confirm: '' })
const submitting = ref(false)

function checkConfirm(value) {
  return value === form.value.password
}

async function onSubmit() {
  submitting.value = true
  try {
    await userStore.register({ username: form.value.username, password: form.value.password })
    showToast('注册成功，已自动登录')
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
