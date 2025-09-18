<template>
  <div class="user-management">
    <div class="header">
      <h3>用户管理</h3>
      <div class="header-buttons">
        <el-button type="warning" @click="showImportDialog">
          导入用户房间分配
        </el-button>
        <el-button type="primary" @click="showCreateDialog = true">
          创建用户
        </el-button>
      </div>
    </div>

    <!-- 角色筛选器 -->
    <div class="filter-section">
      <el-select
        v-model="roleFilter"
        placeholder="筛选角色"
        clearable
        style="width: 200px"
        @clear="roleFilter = ''"
      >
        <el-option label="全部角色" value="" />
        <el-option label="客户大使" value="customer_ambassador" />
        <el-option label="项目工程师" value="project_engineer" />
        <el-option label="维修工程师" value="maintenance_engineer" />
      </el-select>
    </div>

    <el-table :data="sortedAndFilteredUsers" v-loading="loading">
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
      <el-table-column label="操作" width="400">
        <template #default="scope">
          <div class="action-buttons">
            <el-button 
              type="info" 
              size="small"
              @click="showUserRooms(scope.row)"
            >
              查看房间
            </el-button>
            <el-button 
              type="primary" 
              size="small"
              @click="showAssignDialog(scope.row)"
            >
              分配房间
            </el-button>
            <el-button 
              type="warning" 
              size="small"
              @click="resetPassword(scope.row)"
            >
              重置密码
            </el-button>
            <el-button 
              type="danger" 
              size="small"
              @click="deleteUser(scope.row)"
              class="delete-button"
            >
              删除用户
            </el-button>
          </div>
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
        <el-table-column label="房间号" width="100">
          <template #default="scope">
            {{ formatRoomNumber(scope.row.room_number) }}
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
        <el-table-column label="房间号" width="120">
          <template #default="scope">
            {{ formatRoomNumber(scope.row.room_number) }}
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

    <!-- Excel导入对话框 -->
    <el-dialog
      v-model="importDialogVisible"
      title="导入用户房间分配"
      width="700px"
      :close-on-click-modal="false"
    >
      <div class="import-content">
        <div class="import-instructions">
          <h4>导入说明：</h4>
          <ul>
            <li>Excel格式：用户名 | 姓名 | 角色 | 楼栋单元 | 房间号列表</li>
            <li>角色可选值：客户大使、项目工程师、维修工程师</li>
            <li>楼栋单元格式：3单元、4单元</li>
            <li>房间号列表用逗号分隔，3-9楼用3位数（如：301,302），10楼及以上用4位数（如：1201,1202）</li>
            <li>系统会自动为3位数房间号补充前导0进行匹配</li>
          </ul>
        </div>
        
        <el-upload
          ref="importUploadRef"
          :auto-upload="false"
          :show-file-list="true"
          :limit="1"
          accept=".xlsx,.xls"
          @change="handleImportFileChange"
          @remove="handleImportFileRemove"
        >
          <el-button type="primary">选择Excel文件</el-button>
          <template #tip>
            <div class="el-upload__tip">
              只能上传 .xlsx 或 .xls 文件，且不超过 10MB
            </div>
          </template>
        </el-upload>
        
        <!-- 预览数据 -->
        <div v-if="importPreviewData.length > 0" class="preview-section">
          <h4>数据预览（前5行）：</h4>
          <el-table :data="importPreviewData.slice(0, 5)" border max-height="300">
            <el-table-column prop="username" label="用户名" width="100" />
            <el-table-column prop="name" label="姓名" width="100" />
            <el-table-column prop="role" label="角色" width="120" />
            <el-table-column prop="building_unit" label="楼栋单元" width="100" />
            <el-table-column prop="room_numbers" label="房间号列表" min-width="200">
              <template #default="scope">
                <span>{{ scope.row.room_numbers.join(', ') }}</span>
              </template>
            </el-table-column>
          </el-table>
          <p style="margin-top: 10px;">共 {{ importPreviewData.length }} 行数据，总计 {{ getTotalRoomCount() }} 个房间分配</p>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="cancelImport">取消</el-button>
        <el-button 
          type="primary" 
          @click="executeImport" 
          :loading="importLoading"
          :disabled="importPreviewData.length === 0"
        >
          确认导入
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { userAPI, roomAPI } from '../api/index.js'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as XLSX from 'xlsx'

const loading = ref(false)
const users = ref([])
const rooms = ref([])
const assignments = ref([])

const showCreateDialog = ref(false)
const showAssignRoomDialog = ref(false)
const showUserRoomsDialog = ref(false)

// Excel导入相关
const importDialogVisible = ref(false)
const importLoading = ref(false)
const importUploadRef = ref()
const importPreviewData = ref([])
const selectedImportFile = ref(null)

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

const roleFilter = ref('')

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

const sortedAndFilteredUsers = computed(() => {
  let filtered = users.value

  // 角色筛选
  if (roleFilter.value) {
    filtered = filtered.filter(user => user.role === roleFilter.value)
  }

  // 按角色排序
  const roleOrder = {
    'customer_ambassador': 1,
    'project_engineer': 2,
    'maintenance_engineer': 3
  }

  return filtered.sort((a, b) => {
    const orderA = roleOrder[a.role] || 999
    const orderB = roleOrder[b.role] || 999
    return orderA - orderB
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
    ElMessage.success(`已移除房间 ${room.building_unit}-${formatRoomNumber(room.room_number)}`)
    fetchData() // 刷新数据
  } catch (error) {
    ElMessage.error('移除房间分配失败')
  }
}

const getRoomAssignedUsers = (roomId) => {
  // 获取该房间已分配的用户
  const roomAssignments = assignments.value.filter(assignment => assignment.room_id === roomId)
  
  if (roomAssignments.length === 0) {
    return '暂无分配'
  }
  
  // 获取已分配的角色
  const assignedRoles = new Set()
  roomAssignments.forEach(assignment => {
    const user = users.value.find(u => u.id === assignment.user_id)
    if (user) {
      assignedRoles.add(user.role)
    }
  })
  
  // 转换为中文角色名
  const roleNames = []
  if (assignedRoles.has('customer_ambassador')) roleNames.push('客户大使')
  if (assignedRoles.has('project_engineer')) roleNames.push('项目工程师')
  if (assignedRoles.has('maintenance_engineer')) roleNames.push('维修工程师')
  
  return roleNames.length > 0 ? roleNames.join('、') : '暂无分配'
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
  return new Date(dateString).toLocaleString('zh-CN', {
    timeZone: 'Asia/Shanghai'
  })
}

const formatRoomNumber = (roomNumber) => {
  if (!roomNumber) return ''
  
  const roomStr = roomNumber.toString()
  
  // 如果是4位数且以0开头（3-9楼），去掉前导0
  if (roomStr.length === 4 && roomStr.startsWith('0')) {
    return roomStr.substring(1)
  }
  
  // 其他情况（10楼以上的4位数）保持原样
  return roomStr
}

// Excel导入相关方法
const showImportDialog = () => {
  importDialogVisible.value = true
  importPreviewData.value = []
  selectedImportFile.value = null
}

const handleImportFileChange = (file) => {
  selectedImportFile.value = file
  if (file.raw) {
    readImportExcelFile(file.raw)
  }
}

const handleImportFileRemove = () => {
  importPreviewData.value = []
  selectedImportFile.value = null
}

const readImportExcelFile = (file) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const data = new Uint8Array(e.target.result)
      const workbook = XLSX.read(data, { type: 'array' })
      const sheetName = workbook.SheetNames[0]
      const worksheet = workbook.Sheets[sheetName]
      const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 })
      
      // 跳过前15行（说明和表头），从第16行开始读取数据
      const processedData = []
      for (let i = 15; i < jsonData.length; i++) {
        const row = jsonData[i]
        if (row.length >= 5 && row[0] && row[1] && row[2] && row[3] && row[4]) {
          // 解析房间号列表，自动补充前导0
          const roomNumbersStr = String(row[4] || '')
          const roomNumbers = roomNumbersStr.split(',').map(num => {
            const trimmed = num.trim()
            // 如果是3位数字，补充前导0；4位数保持原样
            if (/^\d{3}$/.test(trimmed)) {
              return '0' + trimmed
            }
            return trimmed
          }).filter(num => num) // 过滤空值
          
          // 角色转换
          const roleMap = {
            '客户大使': 'customer_ambassador',
            '项目工程师': 'project_engineer', 
            '维修工程师': 'maintenance_engineer'
          }
          const role = roleMap[String(row[2] || '').trim()] || String(row[2] || '').trim()
          
          processedData.push({
            username: String(row[0] || '').trim(),
            name: String(row[1] || '').trim(),
            role: role,
            building_unit: String(row[3] || '').trim(),
            room_numbers: roomNumbers
          })
        }
      }
      
      importPreviewData.value = processedData
      ElMessage.success(`成功读取 ${processedData.length} 条数据`)
    } catch (error) {
      console.error('Excel文件读取失败:', error)
      ElMessage.error('Excel文件读取失败，请检查文件格式')
    }
  }
  reader.readAsArrayBuffer(file)
}

const getTotalRoomCount = () => {
  return importPreviewData.value.reduce((total, item) => total + item.room_numbers.length, 0)
}

const executeImport = async () => {
  if (importPreviewData.value.length === 0) {
    ElMessage.error('没有可导入的数据')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确认导入 ${importPreviewData.value.length} 条用户房间分配数据，总计 ${getTotalRoomCount()} 个房间分配吗？`,
      '确认导入',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    importLoading.value = true
    
    console.log('准备导入数据:', importPreviewData.value)
    const response = await userAPI.importUserRoomAssignments(importPreviewData.value)
    console.log('收到响应:', response)
    
    if (response.data.success) {
      ElMessage.success(
        `导入完成！总计：${response.data.total}，成功：${response.data.success_count}，失败：${response.data.failed_count}`
      )
      importDialogVisible.value = false
      // 刷新数据
      await fetchData()
    } else {
      // 显示错误信息
      const errors = response.data.errors.join('\n')
      ElMessageBox.alert(
        `导入完成，但存在错误：\n总计：${response.data.total}，成功：${response.data.success_count}，失败：${response.data.failed_count}\n\n错误详情：\n${errors}`,
        '导入结果',
        { type: 'warning' }
      )
      // 仍然刷新数据
      await fetchData()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('导入失败：' + (error.message || '未知错误'))
    }
  } finally {
    importLoading.value = false
  }
}

const cancelImport = () => {
  importDialogVisible.value = false
  importPreviewData.value = []
  selectedImportFile.value = null
  importUploadRef.value?.clearFiles()
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

.header-buttons {
  display: flex;
  gap: 10px;
}

.filter-section {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
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

.action-buttons {
  display: flex;
  flex-wrap: nowrap;
  gap: 5px;
  align-items: center;
  white-space: nowrap;
}

.delete-button {
  margin-left: 20px !important;
}

/* Excel导入相关样式 */
.import-content {
  margin: 20px 0;
}

.import-instructions {
  background-color: #f5f7fa;
  padding: 15px;
  border-radius: 6px;
  margin-bottom: 20px;
}

.import-instructions h4 {
  margin: 0 0 10px 0;
  color: #303133;
}

.import-instructions ul {
  margin: 0;
  padding-left: 20px;
  color: #606266;
}

.import-instructions li {
  margin-bottom: 5px;
}

.preview-section {
  margin-top: 20px;
  padding: 15px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  background-color: #fafafa;
}

.preview-section h4 {
  margin: 0 0 15px 0;
  color: #303133;
}
</style>