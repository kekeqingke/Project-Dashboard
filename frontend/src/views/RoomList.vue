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
        <el-button type="primary" @click="refreshData" :loading="loading">
          刷新数据
        </el-button>
        <el-button type="warning" @click="showImportDialog">
          导入户主信息
        </el-button>
      </div>
    </div>

    <div class="table-info">
      <span>显示 {{ paginatedRooms.length }} / {{ filteredRooms.length }} 条记录</span>
    </div>

    <el-table :data="paginatedRooms" style="width: 100%" v-loading="loading">
      <el-table-column prop="building_unit" label="楼栋" width="120" />
      <el-table-column prop="room_number" label="房间号" width="120">
        <template #default="scope">
          <span>{{ formatRoomNumber(scope.row.room_number) }}</span>
        </template>
      </el-table-column>
      
      <!-- 户主信息列 -->
      <el-table-column prop="owner_name" label="户主姓名" width="120">
        <template #default="scope">
          <span>{{ scope.row.owner_name || '未录入' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="owner_phone" label="手机号码" width="140">
        <template #default="scope">
          <span>{{ scope.row.owner_phone || '未录入' }}</span>
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

    <!-- Excel导入对话框 -->
    <el-dialog
      v-model="importDialogVisible"
      title="导入户主信息"
      width="600px"
      :close-on-click-modal="false"
    >
      <div class="import-content">
        <div class="import-instructions">
          <h4>导入说明：</h4>
          <ul>
            <li>Excel格式：楼栋 | 房间号 | 户主姓名1 | 手机号码1 | 户主姓名2 | 手机号码2</li>
            <li>楼栋和房间号为必填项</li>
            <li>至少需要填写一个户主的姓名或手机号</li>
            <li>第二户主信息为可选</li>
          </ul>
        </div>
        
        <el-upload
          ref="uploadRef"
          :auto-upload="false"
          :show-file-list="true"
          :limit="1"
          accept=".xlsx,.xls"
          @change="handleFileChange"
          @remove="handleFileRemove"
        >
          <el-button type="primary">选择Excel文件</el-button>
          <template #tip>
            <div class="el-upload__tip">
              只能上传 .xlsx 或 .xls 文件，且不超过 10MB
            </div>
          </template>
        </el-upload>
        
        <!-- 预览数据 -->
        <div v-if="previewData.length > 0" class="preview-section">
          <h4>数据预览（前5行）：</h4>
          <el-table :data="previewData.slice(0, 5)" border max-height="300">
            <el-table-column prop="building_unit" label="楼栋" width="80" />
            <el-table-column prop="room_number" label="房间号" width="80">
              <template #default="scope">
                <span>{{ formatRoomNumber(scope.row.room_number) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="owner_name1" label="户主姓名1" width="100" />
            <el-table-column prop="owner_phone1" label="手机号码1" width="120" />
            <el-table-column prop="owner_name2" label="户主姓名2" width="100" />
            <el-table-column prop="owner_phone2" label="手机号码2" width="120" />
          </el-table>
          <p style="margin-top: 10px;">共 {{ previewData.length }} 行数据</p>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="cancelImport">取消</el-button>
        <el-button 
          type="primary" 
          @click="executeImport" 
          :loading="importLoading"
          :disabled="previewData.length === 0"
        >
          确认导入
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { roomAPI, qualityIssueAPI, adminAPI } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api/index.js'
import * as XLSX from 'xlsx'

const router = useRouter()
const loading = ref(false)
const rooms = ref([])
const qualityIssues = ref([])
const selectedBuilding = ref('3单元')  // 默认选择3单元
const currentPage = ref(1)
const pageSize = ref(20)

// Excel导入相关
const importDialogVisible = ref(false)
const importLoading = ref(false)
const uploadRef = ref()
const previewData = ref([])
const selectedFile = ref(null)

const filteredRooms = computed(() => {
  return rooms.value.filter(room => {
    let matchBuilding = !selectedBuilding.value || room.building_unit === selectedBuilding.value
    return matchBuilding
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
    const [roomsRes, issuesRes] = await Promise.all([
      roomAPI.getRooms(),
      qualityIssueAPI.getQualityIssues()
    ])
    
    rooms.value = roomsRes.data
    qualityIssues.value = issuesRes.data
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
  return new Date(dateString).toLocaleString('zh-CN', {
    timeZone: 'Asia/Shanghai'
  })
}

const formatRoomNumber = (roomNumber) => {
  if (!roomNumber) return roomNumber
  
  // 如果房间号是4位数字且前两位是03-09，去掉前导0
  if (/^0[3-9]\d{2}$/.test(roomNumber)) {
    return roomNumber.substring(1)
  }
  
  // 其他情况保持原样（如1201等高楼层）
  return roomNumber
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

// Excel导入相关方法
const showImportDialog = () => {
  importDialogVisible.value = true
  previewData.value = []
  selectedFile.value = null
}

const handleFileChange = (file) => {
  selectedFile.value = file
  if (file.raw) {
    readExcelFile(file.raw)
  }
}

const handleFileRemove = () => {
  previewData.value = []
  selectedFile.value = null
}

const readExcelFile = (file) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const data = new Uint8Array(e.target.result)
      const workbook = XLSX.read(data, { type: 'array' })
      const sheetName = workbook.SheetNames[0]
      const worksheet = workbook.Sheets[sheetName]
      const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 })
      
      // 跳过标题行，转换数据格式
      const processedData = []
      for (let i = 1; i < jsonData.length; i++) {
        const row = jsonData[i]
        if (row.length > 0 && (row[0] || row[1])) { // 至少有楼栋或房间号
          // 格式化房间号：3-9楼是3位数需添加前导0，10楼及以上是4位数保持原样
          let roomNumber = String(row[1] || '')
          if (roomNumber && /^\d{3}$/.test(roomNumber)) {
            // 3位数房间号（3-9楼），例如301 -> 0301
            roomNumber = '0' + roomNumber
          }
          // 4位数房间号（10楼及以上，如1201）保持原样
          
          processedData.push({
            building_unit: String(row[0] || ''),
            room_number: roomNumber,
            owner_name1: String(row[2] || ''),
            owner_phone1: String(row[3] || ''),
            owner_name2: String(row[4] || ''),
            owner_phone2: String(row[5] || '')
          })
        }
      }
      
      previewData.value = processedData
      ElMessage.success(`成功读取 ${processedData.length} 条数据`)
    } catch (error) {
      console.error('Excel文件读取失败:', error)
      ElMessage.error('Excel文件读取失败，请检查文件格式')
    }
  }
  reader.readAsArrayBuffer(file)
}

const executeImport = async () => {
  console.log('开始执行导入，预览数据长度:', previewData.value.length)
  
  if (previewData.value.length === 0) {
    ElMessage.error('没有可导入的数据')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确认导入 ${previewData.value.length} 条户主信息吗？`,
      '确认导入',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    console.log('用户确认导入，开始发送请求')
    importLoading.value = true
    
    // 直接使用API调用而不是通过adminAPI
    console.log('发送请求到:', '/admin/import-room-owners', '数据:', previewData.value)
    const response = await api.post('/admin/import-room-owners', previewData.value)
    console.log('收到响应:', response)
    
    if (response.data.success) {
      ElMessage.success(
        `导入完成！总计：${response.data.total}，更新：${response.data.updated}，新建：${response.data.created}`
      )
      importDialogVisible.value = false
      // 刷新数据
      await fetchRooms()
    } else {
      // 显示错误信息
      const errors = response.data.errors.join('\n')
      ElMessageBox.alert(
        `导入完成，但存在错误：\n总计：${response.data.total}，更新：${response.data.updated}，新建：${response.data.created}\n\n错误详情：\n${errors}`,
        '导入结果',
        { type: 'warning' }
      )
      // 仍然刷新数据
      await fetchRooms()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('导入失败，完整错误对象:', error)
      console.error('错误响应数据:', error.response?.data)
      console.error('错误状态码:', error.response?.status)
      
      // 如果是422错误，显示详细的验证错误
      if (error.response?.status === 422 && error.response?.data?.detail) {
        console.error('验证错误详情:', error.response.data.detail)
      }
      
      let errorMessage = '导入失败'
      if (error.response?.status === 422 && error.response?.data?.detail) {
        // 处理验证错误
        const details = error.response.data.detail
        if (Array.isArray(details)) {
          errorMessage += '：数据验证失败，请检查Excel格式是否正确'
          console.error('详细验证错误:', details.map(d => `字段: ${d.loc?.join('.')}, 错误: ${d.msg}`).join('; '))
        } else {
          errorMessage += '：' + details
        }
      } else if (error.response?.data?.detail) {
        errorMessage += '：' + error.response.data.detail
      } else if (error.response?.status) {
        errorMessage += `：HTTP ${error.response.status}`
        if (error.response.status === 404) {
          errorMessage += ' - API端点未找到，请检查后端服务是否正常运行'
        } else if (error.response.status === 401) {
          errorMessage += ' - 未授权，请重新登录'
        } else if (error.response.status === 403) {
          errorMessage += ' - 权限不足，需要管理员权限'
        }
      } else if (error.message) {
        errorMessage += '：' + error.message
      }
      
      ElMessage.error(errorMessage)
    }
  } finally {
    importLoading.value = false
  }
}

const cancelImport = () => {
  importDialogVisible.value = false
  previewData.value = []
  selectedFile.value = null
  uploadRef.value?.clearFiles()
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