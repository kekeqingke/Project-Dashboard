<template>
  <div class="room-list">
    <div class="header">
      <h3>房间管理</h3>
      <div class="filters">
        <el-select v-model="selectedBuilding" placeholder="选择楼栋" clearable @change="onFilterChange" style="width: 150px">
          <el-option label="全部" value="" />
          <el-option label="3单元" value="3单元" />
          <el-option label="4单元" value="4单元" />
        </el-select>
        <el-select v-model="selectedStatus" placeholder="选择状态" clearable @change="onFilterChange" style="width: 150px">
          <el-option label="全部" value="" />
          <el-option label="整改中" value="整改中" />
          <el-option label="闭户" value="闭户" />
          <el-option label="已交付" value="已交付" />
          <el-option label="已签约" value="已签约" />
        </el-select>
        <el-button type="primary" @click="refreshData" :loading="loading">
          刷新数据
        </el-button>
      </div>
    </div>

    <div class="table-info">
      <span>显示 {{ paginatedRooms.length }} / {{ filteredRooms.length }} 条记录</span>
    </div>

    <el-table :data="paginatedRooms" style="width: 100%" v-loading="loading">
      <el-table-column prop="building_unit" label="楼栋" width="120" />
      <el-table-column prop="room_number" label="房间号" width="120" />
      <el-table-column prop="status" label="状态" width="120">
        <template #default="scope">
          <el-tag :type="getStatusType(scope.row.status)">
            {{ scope.row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="质量问题" width="120">
        <template #default="scope">
          <span>{{ getRoomIssueCount(scope.row.id) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="沟通记录" width="120">
        <template #default="scope">
          <span>{{ getRoomCommCount(scope.row.id) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="客户大使" width="120">
        <template #default="scope">
          <div class="user-cell">
            <span v-if="getUserByRole(scope.row.assigned_users, 'customer_ambassador')">
              {{ getUserByRole(scope.row.assigned_users, 'customer_ambassador').name }}
            </span>
            <span v-else class="no-user">未分配</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="项目工程师" width="120">
        <template #default="scope">
          <div class="user-cell">
            <span v-if="getUserByRole(scope.row.assigned_users, 'project_engineer')">
              {{ getUserByRole(scope.row.assigned_users, 'project_engineer').name }}
            </span>
            <span v-else class="no-user">未分配</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="维修工程师" width="120">
        <template #default="scope">
          <div class="user-cell">
            <span v-if="getUserByRole(scope.row.assigned_users, 'maintenance_engineer')">
              {{ getUserByRole(scope.row.assigned_users, 'maintenance_engineer').name }}
            </span>
            <span v-else class="no-user">未分配</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="updated_at" label="最后更新时间" width="180">
        <template #default="scope">
          {{ formatDate(scope.row.updated_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120">
        <template #default="scope">
          <el-button type="primary" size="small" @click="viewRoom(scope.row)">
            查看详情
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="filteredRooms.length"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { roomAPI, qualityIssueAPI, communicationAPI } from '../api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const loading = ref(false)
const rooms = ref([])
const qualityIssues = ref([])
const communications = ref([])
const selectedBuilding = ref('3单元')  // 默认选择3单元
const selectedStatus = ref('')
const currentPage = ref(1)
const pageSize = ref(20)

const filteredRooms = computed(() => {
  return rooms.value.filter(room => {
    let matchBuilding = !selectedBuilding.value || room.building_unit === selectedBuilding.value
    let matchStatus = !selectedStatus.value || room.status === selectedStatus.value
    return matchBuilding && matchStatus
  })
})

const paginatedRooms = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredRooms.value.slice(start, end)
})

const fetchRooms = async () => {
  loading.value = true
  try {
    const [roomsRes, issuesRes, commsRes] = await Promise.all([
      roomAPI.getRooms(),
      qualityIssueAPI.getQualityIssues(),
      communicationAPI.getCommunications()
    ])
    
    rooms.value = roomsRes.data
    qualityIssues.value = issuesRes.data
    communications.value = commsRes.data
  } catch (error) {
    ElMessage.error('获取房间数据失败')
  } finally {
    loading.value = false
  }
}

const onFilterChange = () => {
  // 筛选条件改变时重置到第一页
  currentPage.value = 1
}

const refreshData = () => {
  fetchRooms()
}

const handleSizeChange = (newSize) => {
  pageSize.value = newSize
  currentPage.value = 1  // 重置到第一页
}

const handleCurrentChange = (newPage) => {
  currentPage.value = newPage
}

const getRoomIssueCount = (roomId) => {
  return qualityIssues.value.filter(issue => issue.room_id === roomId).length
}

const getRoomCommCount = (roomId) => {
  return communications.value.filter(comm => comm.room_id === roomId).length
}

const getStatusType = (status) => {
  const typeMap = {
    '整改中': 'warning',
    '闭户': 'info',
    '已交付': 'success',
    '已签约': 'primary'
  }
  return typeMap[status] || 'info'
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

const getRoleTagType = (role) => {
  const typeMap = {
    'customer_ambassador': 'primary',
    'project_engineer': 'success',
    'maintenance_engineer': 'warning'
  }
  return typeMap[role] || 'info'
}

const getRoleDisplayName = (role) => {
  const nameMap = {
    'customer_ambassador': '客户大使',
    'project_engineer': '项目工程师', 
    'maintenance_engineer': '维修工程师'
  }
  return nameMap[role] || role
}

const getSortedRoleUsers = (users) => {
  if (!users || users.length === 0) return []
  
  const roleOrder = {
    'customer_ambassador': 1,
    'project_engineer': 2,
    'maintenance_engineer': 3
  }
  
  return [...users].sort((a, b) => {
    const orderA = roleOrder[a.role] || 999
    const orderB = roleOrder[b.role] || 999
    return orderA - orderB
  })
}

const getUserByRole = (users, role) => {
  if (!users || users.length === 0) return null
  return users.find(user => user.role === role) || null
}

const viewRoom = (room) => {
  router.push(`/rooms/${room.id}`)
}

onMounted(() => {
  fetchRooms()
})
</script>

<style scoped>
.room-list {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.filters {
  display: flex;
  gap: 10px;
  align-items: center;
}

.table-info {
  margin: 15px 0;
  color: #666;
  font-size: 14px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.user-cell {
  text-align: center;
  padding: 8px 4px;
  font-size: 13px;
}

.user-cell span {
  color: #303133;
  font-weight: 500;
}

.no-user {
  color: #C0C4CC;
  font-size: 12px;
  font-style: italic;
}
</style>