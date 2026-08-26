<template>
  <div class="page">
    <van-nav-bar title="编辑资料" left-arrow fixed placeholder @click-left="router.back()" />
    <van-form @submit="onSubmit">
      <van-cell-group inset class="edit-group">
        <van-field
          v-model="form.nickname"
          label="昵称"
          placeholder="请输入昵称"
          maxlength="50"
        />
        <van-field
          v-model="form.avatar"
          label="头像 URL"
          placeholder="请输入头像图片地址"
          maxlength="255"
        />
        <van-field
          is-link
          readonly
          name="gender"
          label="性别"
          :model-value="genderText"
          placeholder="请选择性别"
          @click="showGenderPicker = true"
        />
        <van-field
          v-model="form.phone"
          label="手机号"
          type="tel"
          placeholder="请输入手机号"
          maxlength="20"
        />
        <van-field
          v-model="form.bio"
          label="简介"
          type="textarea"
          rows="3"
          autosize
          placeholder="介绍一下自己吧"
          maxlength="500"
          show-word-limit
        />
      </van-cell-group>
      <div class="save-btn">
        <van-button round block type="primary" native-type="submit" :loading="submitting">
          保存
        </van-button>
      </div>
    </van-form>

    <van-popup v-model:show="showGenderPicker" position="bottom" round>
      <van-picker
        :columns="genderColumns"
        @confirm="onGenderConfirm"
        @cancel="showGenderPicker = false"
      />
    </van-popup>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const genderColumns = [
  { text: '保密', value: 'unknown' },
  { text: '男', value: 'male' },
  { text: '女', value: 'female' },
]

const form = ref({ nickname: '', avatar: '', gender: 'unknown', bio: '', phone: '' })
const showGenderPicker = ref(false)
const submitting = ref(false)

const genderText = computed(
  () => genderColumns.find((g) => g.value === form.value.gender)?.text || '保密'
)

onMounted(async () => {
  try {
    const info = await userStore.fetchUserInfo()
    form.value = {
      nickname: info.nickname || '',
      avatar: info.avatar || '',
      gender: info.gender || 'unknown',
      bio: info.bio || '',
      phone: info.phone || '',
    }
  } catch (e) {
    // 拦截器已提示
  }
})

function onGenderConfirm({ selectedOptions }) {
  form.value.gender = selectedOptions[0].value
  showGenderPicker.value = false
}

async function onSubmit() {
  submitting.value = true
  try {
    await userStore.updateProfile(form.value)
    showToast('保存成功')
    router.back()
  } catch (e) {
    // 拦截器已提示
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.edit-group {
  margin-top: 12px;
}

.save-btn {
  padding: 24px 20px;
}
</style>
