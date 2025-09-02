<template>
  <div class="user-management">
    <div class="header">
      <h3>用户管理</h3>
      <el-button type="primary" @click="showCreateDialog = true">
        创建用户
      </el-button>
    </div>

    <el-table :data="users" v-loading="loading">
      <el-table-column prop="username" label="用户名" width="120" />
      <el-table-column prop="name" label="姓名" width="120" />
      <el-table-column prop="role" label="角色" width="120">
        <template #default="scope">
          {{ getRoleName(scope.row.role) }}
        </template>
      </el-table-column>
      <el-table-column label="初始密码" width="120">
        <template #default="scope">
          <span v-if="!scope.row.password_changed" class="password-display">
            {{ scope.row.initial_password }}
          </span>
          <span v-else class="password-changed">
            已修改
          </span>
        </template>
      </el-table-column>
      <el-table-column label="分配房间" width="100">
        <template #default="scope">
          {{ getUserRoomCount(scope.row.id) }}
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="150">
        <template #default="scope">
          {{ formatDate(scope.row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="300">
        <template #default="scope">
          <el-button 
            type="info" 
            size="small"
            @click="showUserRooms(scope.row)"
            style="margin-right: 5px"
          >
            房间
          </el-button>
          <el-button 
            type="primary" 
            size="small"
            @click="showAssignDialog(scope.row)"
            style="margin-right: 5px"
          >
            分配
          </el-button>
          <el-button 
            type="warning" 
            size="small"
            @click="resetPassword(scope.row)"
            style="margin-right: 5px"
          >
            重置
          </el-button>
          <el-button 
            type="danger" 
            size="small"
            @click="deleteUser(scope.row)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 创建用户对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建用户" width="500px">
      <el-form :model="userForm" :rules="userRules" ref="userFormRef" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="userForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="姓名" prop="name">
          <el-input v-model="userForm.name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="userForm.password" type="password" placeholder="请输入密码" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="userForm.role" placeholder="请选择角色">
            <el-option label="客户大使" value="customer_ambassador" />
            <el-option label="项目工程师" value="project_engineer" />
            <el-option label="维修工程师" value="maintenance_engineer" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createUser">确认</el-button>
      </template>
    </el-dialog>

    <!-- 分配房间对话框 -->
    <el-dialog v-model="showAssignRoomDialog" title="分配房间" width="700px">
      <div class="assign-header">
        <h4>为 {{ selectedUser?.name }} 分配房间</h4>
      </div>
      
      <div class="room-filters">
        <el-select v-model="roomFilter.building" placeholder="选择楼栋" clearable>
          <el-option label="3单元" value="3单元" />
          <el-option label="4单元" value="4单元" />
        </el-select>
      </div>

      <el-table 
        :data="filteredRooms" 
        @selection-change="handleRoomSelection"
        max-height="400"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="building_unit" label="楼栋" width="100" />
        <el-table-column prop="room_number" label="房间号" width="100" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ scope.row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="已分配用户" min-width="200">
          <template #default="scope">
            {{ getRoomAssignedUsers(scope.row.id) }}
          </template>
        </el-table-column>
      </el-table>
      
      <template #footer>
        <el-button @click="showAssignRoomDialog = false">取消</el-button>
        <el-button type="primary" @click="assignRooms">确认分配</el-button>
      </template>
    </el-dialog>

    <!-- 查看用户房间对话框 -->
    <el-dialog v-model="showUserRoomsDialog" title="用户分配房间详情" width="800px">
      <div class="user-rooms-header">
        <h4>{{ selectedUser?.name }} 的分配房间</h4>
        <p>总计：{{ userAssignedRooms.length }} 个房间</p>
      </div>
      
      <el-table :data="userAssignedRooms" style="width: 100%">
        <el-table-column prop="building_unit" label="楼栋" width="120" />
        <el-table-column prop="room_number" label="房间号" width="120" />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ scope.row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="分配时间" width="180">
          <template #default="scope">
            {{ formatDate(scope.row.assignment_created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="scope">
            <el-button 
              type="danger" 
              size="small"
              @click="removeRoomAssignment(scope.row)"
            >
              移除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <template #footer>
        <el-button @click="showUserRoomsDialog = false">关闭</el-button>
        <el-button type="primary" @click="showAssignDialog(selectedUser)">继续分配</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { userAPI, roomAPI } from '../api/index.js'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const users = ref([])
const rooms = ref([])
const assignments = ref([])

const showCreateDialog = ref(false)
const showAssignRoomDialog = ref(false)
const showUserRoomsDialog = ref(false)

const selectedUser = ref(null)
const selectedRooms = ref([])

const userForm = ref({
  username: '',
  name: '',
  password: '',
  role: ''
})

const roomFilter = ref({
  building: ''
})

const userRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }]
}

const filteredRooms = computed(() => {
  return rooms.value.filter(room => {
    if (roomFilter.value.building && room.building_unit !== roomFilter.value.building) {
      return false
    }
    return true
  })
})

const userAssignedRooms = computed(() => {
  if (!selectedUser.value) return []
  
  const userAssignments = assignments.value.filter(assignment => 
    assignment.user_id === selectedUser.value.id
  )
  
  return userAssignments.map(assignment => {
    const room = rooms.value.find(room => room.id === assignment.room_id)
    return {
      ...room,
      assignment_id: assignment.id,
      assignment_created_at: assignment.created_at
    }
  }).filter(room => room.id) // 过滤掉找不到的房间
})

const fetchData = async () => {
  loading.value = true
  try {
    const [usersRes, roomsRes, assignmentsRes] = await Promise.all([
      userAPI.getUsers(),
      roomAPI.getRooms(),
      userAPI.getRoomAssignments()
    ])
    users.value = usersRes.data.filter(u => u.role !== 'admin')
    rooms.value = roomsRes.data
    assignments.value = assignmentsRes.data
  } catch (error) {
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
  }
}

const createUser = async () => {
  try {
    await userAPI.createUser(userForm.value)
    ElMessage.success('用户创建成功')
    showCreateDialog.value = false
    userForm.value = { username: '', name: '', password: '', role: '' }
    fetchData()
  } catch (error) {
    ElMessage.error('创建用户失败')
  }
}

const resetPassword = async (user) => {
  try {
    const result = await ElMessageBox.confirm(
      `确定要重置用户 ${user.name} 的密码吗？`,
      '重置密码确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    if (result === 'confirm') {
      ElMessage.info('正在重置密码，请稍候...')
      const response = await userAPI.resetPassword(user.id)
      ElMessage.success(`密码已重置为：${response.data.initial_password}`)
      fetchData()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Reset password error:', error)
      const errorMsg = error.response?.data?.detail || error.message || '重置密码失败'
      ElMessage.error(errorMsg)
    }
  }
}

const deleteUser = async (user) => {
  try {
    const result = await ElMessageBox.confirm(
      `确定要删除用户 ${user.name} 吗？删除后将无法恢复！`,
      '删除用户确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'error',
        buttonSize: 'default'
      }
    )
    
    if (result === 'confirm') {
      ElMessage.info('正在删除用户，请稍候...')
      await userAPI.deleteUser(user.id)
      ElMessage.success('用户删除成功')
      fetchData()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete user error:', error)
      const errorMsg = error.response?.data?.detail || error.message || '删除用户失败'
      ElMessage.error(errorMsg)
    }
  }
}

const showAssignDialog = (user) => {
  selectedUser.value = user
  showAssignRoomDialog.value = true
  selectedRooms.value = []
}

const showUserRooms = (user) => {
  selectedUser.value = user
  showUserRoomsDialog.value = true
}

const handleRoomSelection = (selection) => {
  selectedRooms.value = selection
}

const assignRooms = async () => {
  if (selectedRooms.value.length === 0) {
    ElMessage.warning('请选择要分配的房间')
    return
  }
  
  try {
    for (const room of selectedRooms.value) {
      await userAPI.assignRoom(selectedUser.value.id, room.id)
    }
    ElMessage.success(`成功分配 ${selectedRooms.value.length} 个房间`)
    showAssignRoomDialog.value = false
    fetchData() // 刷新数据以更新房间计数
  } catch (error) {
    ElMessage.error('分配房间失败')
  }
}

const getUserRoomCount = (userId) => {
  return assignments.value.filter(assignment => assignment.user_id === userId).length
}

const removeRoomAssignment = async (room) => {
  try {
    await userAPI.deleteRoomAssignment(room.assignment_id)
    ElMessage.success(`已移除房间 ${room.building_unit}-${room.room_number}`)
    fetchData() // 刷新数据
  } catch (error) {
    ElMessage.error('移除房间分配失败')
  }
}

const getRoomAssignedUsers = (roomId) => {
  // 这里需要实际的分配数据，暂时返回空
  return '暂无分配'
}

const getRoleName = (role) => {
  const roleMap = {
    customer_ambassador: '客户大使',
    project_engineer: '项目工程师',
    maintenance_engineer: '维修工程师'
  }
  return roleMap[role] || role
}

const getStatusType = (status) => {
  const typeMap = {
    '整改中': 'warning',
    '闭户': 'info',
    '已交付': 'success',
    '已签约': 'success'
  }
  return typeMap[status] || 'info'
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

onMounted(() => {
  console.log('userAPI methods:', Object.keys(userAPI))
  fetchData()
})
</script>

<style scoped>
.user-management {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.assign-header {
  margin-bottom: 15px;
}

.room-filters {
  margin-bottom: 15px;
}

.password-display {
  font-family: 'Courier New', monospace;
  background-color: #f5f5f5;
  padding: 2px 6px;
  border-radius: 3px;
  font-weight: bold;
  color: #409eff;
}

.password-changed {
  color: #67c23a;
  font-style: italic;
}
</style>