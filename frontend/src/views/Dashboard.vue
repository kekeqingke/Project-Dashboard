<template>
  <el-container>
    <el-header>
      <div class="header">
        <h2>ZWY项目管理系统</h2>
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
          <el-menu-item v-if="authStore.isCustomerAmbassador" index="/ambassador">
            <el-icon><User /></el-icon>
            <span>我的工作台</span>
          </el-menu-item>
          
          <!-- 工程师菜单 -->
          <el-menu-item v-if="authStore.isEngineer" index="/engineer">
            <el-icon><User /></el-icon>
            <span>我的工作台</span>
          </el-menu-item>
          
          <!-- 管理员菜单 -->
          <el-menu-item v-if="authStore.isAdmin" index="/admin/users">
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </el-menu-item>
          
          <el-menu-item v-if="authStore.isAdmin" index="/rooms">
            <el-icon><House /></el-icon>
            <span>房间管理</span>
          </el-menu-item>
          
          <el-menu-item v-if="authStore.isAdmin" index="/admin/summary">
            <el-icon><DataAnalysis /></el-icon>
            <span>数据汇总</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { House, User, DataAnalysis } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const activeMenu = computed(() => route.path)

onMounted(() => {
  authStore.initializeAuth()
  if (route.path === '/dashboard') {
    // 根据用户角色跳转到不同的界面
    if (authStore.isCustomerAmbassador) {
      router.push('/ambassador')
    } else if (authStore.isEngineer) {
      router.push('/engineer')
    } else if (authStore.isAdmin) {
      router.push('/admin/users')
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