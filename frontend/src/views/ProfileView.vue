<template>
  <div class="page-content profile-page">
    <div class="profile-head">
      <van-image round width="64" height="64" :src="userStore.avatar || DEFAULT_AVATAR">
        <template #error>
          <van-image round width="64" height="64" :src="DEFAULT_AVATAR" />
        </template>
      </van-image>
      <div class="profile-info">
        <div class="profile-name">{{ userStore.userInfo?.nickname || userStore.userInfo?.username }}</div>
        <div class="profile-bio">{{ userStore.userInfo?.bio || '这个人很懒，什么都没留下' }}</div>
      </div>
    </div>

    <van-cell-group inset class="profile-group">
      <van-cell title="我的收藏" icon="star-o" is-link to="/favorites" />
      <van-cell title="浏览历史" icon="clock-o" is-link to="/history" />
    </van-cell-group>

    <van-cell-group inset class="profile-group">
      <van-cell title="编辑资料" icon="edit" is-link to="/profile/edit" />
      <van-cell title="修改密码" icon="shield-o" is-link to="/profile/password" />
    </van-cell-group>

    <div class="logout-btn">
      <van-button round block plain type="danger" @click="onLogout">退出登录</van-button>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showConfirmDialog } from 'vant'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const DEFAULT_AVATAR = 'https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg'

onMounted(() => {
  // 刷新一次用户信息（编辑资料后回来自动更新）
  userStore.fetchUserInfo().catch(() => {})
})

async function onLogout() {
  try {
    await showConfirmDialog({ title: '提示', message: '确定退出登录吗？' })
  } catch (e) {
    return // 取消
  }
  userStore.logout()
  router.replace('/login')
}
</script>

<style scoped>
.profile-page {
  background: #f7f8fa;
}

.profile-head {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 28px 20px;
  background: linear-gradient(135deg, #1989fa, #53a8ff);
  margin-bottom: 12px;
}

.profile-info {
  flex: 1;
  min-width: 0;
}

.profile-name {
  font-size: 20px;
  font-weight: 600;
  color: #fff;
}

.profile-bio {
  margin-top: 6px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.85);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.profile-group {
  margin-bottom: 12px;
}

.logout-btn {
  padding: 16px 20px;
}
</style>
