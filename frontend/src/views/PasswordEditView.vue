<template>
  <div class="page">
    <van-nav-bar title="修改密码" left-arrow fixed placeholder @click-left="router.back()" />
    <van-form @submit="onSubmit">
      <van-cell-group inset class="pwd-group">
        <van-field
          v-model="form.oldPassword"
          type="password"
          label="旧密码"
          placeholder="请输入旧密码"
          :rules="[{ required: true, message: '请输入旧密码' }]"
        />
        <van-field
          v-model="form.newPassword"
          type="password"
          label="新密码"
          placeholder="请输入新密码（至少 6 位）"
          :rules="[{ required: true, pattern: /^\S{6,}$/, message: '新密码至少 6 位' }]"
        />
        <van-field
          v-model="form.confirm"
          type="password"
          label="确认新密码"
          placeholder="请再次输入新密码"
          :rules="[{ validator: checkConfirm, message: '两次输入的新密码不一致' }]"
        />
      </van-cell-group>
      <div class="save-btn">
        <van-button round block type="primary" native-type="submit" :loading="submitting">
          确认修改
        </van-button>
      </div>
    </van-form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const form = ref({ oldPassword: '', newPassword: '', confirm: '' })
const submitting = ref(false)

function checkConfirm(value) {
  return value === form.value.newPassword
}

async function onSubmit() {
  submitting.value = true
  try {
    await userStore.updatePassword({
      oldPassword: form.value.oldPassword,
      newPassword: form.value.newPassword,
    })
    showToast('修改成功')
    router.back()
  } catch (e) {
    // 拦截器已提示
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.pwd-group {
  margin-top: 12px;
}

.save-btn {
  padding: 24px 20px;
}
</style>
