<template>
  <el-container>
    <el-header>
      <div class="header">
        <h2>瑧湾悦项目品质管理系统</h2>
        <div class="user-info">
          <span>{{ authStore.user?.name }}（{{ getRoleName(authStore.user?.role) }}）</span>
          <el-button @click="logout" type="text">退出</el-button>
        </div>
      </div>
    </el-header>
    
    <el-container>
      <el-aside width="200px">
        <el-menu
          :default-active="activeMenu"
          class="el-menu-vertical"
          @select="handleMenuSelect"
        >
          <!-- 客户大使菜单 -->
          <el-menu-item v-if="authStore.isCustomerAmbassador" index="/dashboard/ambassador">
            <el-icon><User /></el-icon>
            <span>我的工作台</span>
          </el-menu-item>

          <!-- 工程师菜单 -->
          <el-menu-item v-if="authStore.isEngineer" index="/dashboard/engineer">
            <el-icon><User /></el-icon>
            <span>我的工作台</span>
          </el-menu-item>

          <!-- 管理员菜单 -->
          <el-menu-item v-if="authStore.isAdmin" index="/dashboard/admin/users">
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </el-menu-item>

          <el-menu-item v-if="authStore.isAdmin" index="/dashboard/rooms">
            <el-icon><House /></el-icon>
            <span>房间管理</span>
          </el-menu-item>

          <el-menu-item v-if="authStore.isAdmin" index="/dashboard/admin/summary">
            <el-icon><DataAnalysis /></el-icon>
            <span>数据汇总</span>
          </el-menu-item>
          
          <!-- 个人中心菜单 - 所有用户都可见 -->
          <el-divider style="margin: 10px 0;" />
          <el-sub-menu index="profile">
            <template #title>
              <el-icon><Avatar /></el-icon>
              <span>个人中心</span>
            </template>
            <el-menu-item index="/dashboard/profile/change-password">
              <el-icon><Lock /></el-icon>
              <span>修改密码</span>
            </el-menu-item>
          </el-sub-menu>
        </el-menu>
      </el-aside>
      
      <el-main>
        <router-view />
      </el-main>
    </el-container>
    
    <!-- 首次登录强制修改密码弹窗 -->
    <FirstLoginModal
      v-model="showFirstLoginModal"
      :current-password="authStore.loginPassword"
      @success="handleFirstLoginSuccess"
    />
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { House, User, DataAnalysis, Avatar, Lock } from '@element-plus/icons-vue'
import FirstLoginModal from '../components/FirstLoginModal.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const activeMenu = computed(() => route.path)
const showFirstLoginModal = ref(false)

onMounted(() => {
  authStore.initializeAuth()

  // 检查是否首次登录
  if (authStore.firstLogin) {
    showFirstLoginModal.value = true
  }

  // 只有在明确访问 /dashboard 路径时才进行角色跳转
  // 避免在子路由导航时误触发跳转
  if (route.path === '/dashboard' && !route.query.from) {
    // 根据用户角色跳转到不同的界面
    if (authStore.isCustomerAmbassador) {
      router.push('/dashboard/ambassador')
    } else if (authStore.isEngineer) {
      router.push('/dashboard/engineer')
    } else if (authStore.isAdmin) {
      router.push('/dashboard/admin/users')
    }
  }
})

const getRoleName = (role) => {
  const roleMap = {
    admin: '管理员',
    customer_ambassador: '客户大使',
    project_engineer: '项目工程师',
    maintenance_engineer: '维修工程师'
  }
  return roleMap[role] || role
}

const handleMenuSelect = (index) => {
  router.push(index)
}

const logout = () => {
  authStore.logout()
  router.push('/login')
}

const handleFirstLoginSuccess = () => {
  authStore.clearFirstLoginState()
  showFirstLoginModal.value = false
}
</script>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  background-color: #fff;
  box-shadow: 0 2px 4px rgba(0,0,0,.1);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.el-aside {
  background-color: #f5f5f5;
}

.el-menu-vertical {
  border-right: none;
}
</style>