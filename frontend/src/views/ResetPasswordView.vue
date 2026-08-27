<template>
  <div class="page auth-page">
    <van-nav-bar title="重置密码" left-arrow @click-left="goBack" />
    <div class="auth-head">
      <div class="auth-logo">🔑</div>
      <div class="auth-title">重置密码</div>
      <div class="auth-sub">输入用户名与新密码即可重置，重置后请用新密码登录</div>
    </div>
    <van-form @submit="onSubmit" class="auth-form">
      <van-cell-group inset>
        <van-field
          v-model="form.username"
          name="username"
          label="用户名"
          placeholder="请输入用户名"
          maxlength="50"
          :rules="[{ required: true, message: '请输入用户名' }]"
        />
        <van-field
          v-model="form.newPassword"
          type="password"
          name="newPassword"
          label="新密码"
          placeholder="请输入新密码（至少 6 位）"
          :rules="[{ required: true, pattern: /^\S{6,}$/, message: '密码至少 6 位' }]"
        />
        <van-field
          v-model="form.confirm"
          type="password"
          name="confirm"
          label="确认密码"
          placeholder="请再次输入新密码"
          :rules="[{ validator: checkConfirm, message: '两次密码不一致' }]"
        />
      </van-cell-group>
      <div class="auth-btn">
        <van-button round block type="primary" native-type="submit" :loading="submitting">
          重置密码
        </van-button>
      </div>
    </van-form>
    <div class="auth-footer">
      想起密码了？
      <span class="link" @click="router.replace('/login')">去登录</span>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { resetPassword } from '@/api/user'

const router = useRouter()

const form = ref({ username: '', newPassword: '', confirm: '' })
const submitting = ref(false)

function checkConfirm(value) {
  return value === form.value.newPassword
}

async function onSubmit() {
  submitting.value = true
  try {
    await resetPassword({ username: form.value.username, newPassword: form.value.newPassword })
    showToast('重置成功，请登录')
    router.replace('/login')
  } catch (e) {
    // 拦截器已提示
  } finally {
    submitting.value = false
  }
}

// 左上角返回：用 vue-router 的 SPA 导航栈判断（不能看浏览器 history.length，
// 它包含无关历史页面）；直接打开/刷新本页时 state.back 为 null → 回首页
function goBack() {
  if (router.options.history.state.back) {
    router.back()
  } else {
    router.replace('/')
  }
}
</script>

<style scoped>
.auth-page {
  background: #fff;
  min-height: 100vh;
}

.auth-head {
  padding: 24px 24px 32px;
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
