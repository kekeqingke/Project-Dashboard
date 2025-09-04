<template>
  <div class="engineer-dashboard">
    <div class="dashboard-header">
      <h3>{{ getWorkplaceTitle() }}</h3>
      <p class="role-description">管理分配给您的房间的质量问题</p>
    </div>

    <div v-if="loading" class="loading">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>加载中...</span>
    </div>

    <div v-else-if="assignedRooms.length === 0" class="no-rooms">
      <el-empty description="暂无分配的房间">
        <p>请联系管理员为您分配房间</p>
      </el-empty>
    </div>

    <div v-else>
      <!-- 房间选择器 -->
      <div class="room-selector">
        <el-select 
          v-model="selectedRoomId" 
          placeholder="请选择要管理的房间"
          size="large"
          style="width: 300px"
          @change="handleRoomChange"
        >
          <el-option
            v-for="room in assignedRooms"
            :key="room.id"
            :label="`${room.building_unit} ${room.room_number}号房`"
            :value="room.id"
          >
            <span>{{ room.building_unit }} {{ room.room_number }}号房</span>
            <el-tag 
              :type="getStatusType(room.status)" 
              size="small" 
              style="margin-left: 8px"
            >
              {{ getStatusText(room.status) }}
            </el-tag>
          </el-option>
        </el-select>
      </div>

      <!-- 当前房间信息 -->
      <div v-if="currentRoom" class="current-room-info">
        <el-card>
          <template #header>
            <div class="room-header">
              <div class="room-info">
                <h4>{{ currentRoom.building_unit }} {{ currentRoom.room_number }}号房</h4>
                <div class="status-tags">
                  <el-tag :type="getStatusType(currentRoom.status)">
                    {{ getStatusText(currentRoom.status) }}
                  </el-tag>
                </div>
              </div>
              <div class="room-controls">
                <div class="status-display">
                  <div class="status-item">
                    <label>交付状态：</label>
                    <el-tag :type="currentRoom.delivery_status === '已交付' ? 'success' : 'warning'" size="small">
                      {{ currentRoom.delivery_status || '待交付' }}
                    </el-tag>
                  </div>
                  <div class="status-item">
                    <label>预计交付时间：</label>
                    <span class="status-value">{{ formatExpectedDeliveryDate(currentRoom.expected_delivery_date) }}</span>
                  </div>
                  <div class="status-item">
                    <label>签约状态：</label>
                    <el-tag :type="currentRoom.contract_status === '已签约' ? 'success' : 'warning'" size="small">
                      {{ currentRoom.contract_status || '待签约' }}
                    </el-tag>
                  </div>
                  <div class="status-item">
                    <label>信件状态：</label>
                    <el-tag :type="currentRoom.letter_status === 'ZX' ? 'danger' : currentRoom.letter_status === 'SX' ? 'warning' : 'info'" size="small">
                      {{ currentRoom.letter_status || '无' }}
                    </el-tag>
                  </div>
                  <div class="status-item">
                    <label>前期渗漏：</label>
                    <el-tag :type="currentRoom.pre_leakage === '有' ? 'primary' : 'success'" size="small">
                      {{ currentRoom.pre_leakage || '无' }}
                    </el-tag>
                  </div>
                </div>
                <el-button 
                  type="primary" 
                  :icon="Refresh" 
                  size="small"
                  @click="refreshRoomData"
                  :loading="refreshing"
                >
                  刷新数据
                </el-button>
              </div>
            </div>
          </template>
          
          <div class="room-stats">
            <div class="stat-item">
              <el-statistic title="质量问题" :value="currentRoom.quality_issue_count || 0" />
            </div>
            <div class="stat-item">
              <el-statistic title="待验收" :value="currentRoom.pending_verification_count || 0" />
            </div>
            <div class="stat-item">
              <el-statistic title="沟通记录" :value="currentRoom.communication_count || 0" />
            </div>
            <div class="stat-item">
              <el-statistic title="待落实" :value="currentRoom.pending_implementation_count || 0" />
            </div>
          </div>
        </el-card>
      </div>

      <!-- 功能模块 -->
      <div v-if="currentRoom" class="function-modules">
        <!-- 质量问题管理模块 -->
        <el-card class="module-card">
          <template #header>
            <div class="module-header">
              <div class="module-title">
                <el-icon><Warning /></el-icon>
                <span>质量问题管理</span>
              </div>
              <el-button type="primary" @click="openQualityIssueDialog">
                <el-icon><Plus /></el-icon>
                记录新问题
              </el-button>
            </div>
          </template>
          
          <div class="module-content">
            <div v-if="qualityIssues.length === 0" class="empty-content">
              <el-empty description="暂无质量问题" />
            </div>
            <div v-else class="issues-list">
              <div 
                v-for="issue in qualityIssues" 
                :key="issue.id"
                class="issue-item"
              >
                <div class="issue-content">
                  <div class="issue-header">
                    <span class="issue-date">{{ formatDate(issue.record_date || issue.created_at) }}</span>
                    <el-tag 
                      :type="issue.is_verified ? 'success' : 'warning'"
                      size="small"
                    >
                      {{ issue.is_verified ? '已验收' : '待验收' }}
                    </el-tag>
                  </div>
                  <p class="issue-description">{{ issue.description }}</p>
                  <div class="issue-actions">
                    <el-button 
                      type="primary" 
                      size="small"
                      @click="editQualityIssue(issue)"
                    >
                      编辑
                    </el-button>
                    <el-button 
                      v-if="!issue.is_verified" 
                      type="success" 
                      size="small"
                      @click="verifyIssue(issue)"
                    >
                      标记验收
                    </el-button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 客户沟通管理模块 -->
        <el-card class="module-card">
          <template #header>
            <div class="module-header">
              <div class="module-title">
                <el-icon><ChatLineSquare /></el-icon>
                <span>客户沟通记录</span>
              </div>
            </div>
          </template>
          
          <div class="module-content">
            <div v-if="communications.length === 0" class="empty-content">
              <el-empty description="暂无沟通记录" />
            </div>
            <div v-else class="communications-list">
              <div 
                v-for="comm in communications" 
                :key="comm.id"
                class="communication-item"
              >
                <div class="comm-header">
                  <span class="comm-date">
                    {{ comm.communication_time ? formatDate(comm.communication_time) : formatDate(comm.created_at) }}
                  </span>
                  <el-tag 
                    :type="comm.is_implemented ? 'success' : 'warning'"
                    size="small"
                  >
                    {{ comm.is_implemented ? '已落实' : '待落实' }}
                  </el-tag>
                </div>
                <div class="comm-content">
                  <div class="comm-section">
                    <strong>沟通内容:</strong>
                    <p>{{ comm.content }}</p>
                  </div>
                  <div v-if="comm.feedback" class="comm-section">
                    <strong>收房意愿:</strong>
                    <el-tag :type="comm.feedback === '高' ? 'success' : 'danger'">
                      {{ comm.feedback }}
                    </el-tag>
                  </div>
                  <div v-if="comm.customer_description" class="comm-section">
                    <strong>客户描摹:</strong>
                    <p>{{ comm.customer_description }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </div>
    </div>


    <!-- 添加质量问题对话框 -->
    <el-dialog
      v-model="qualityIssueDialogVisible"
      :title="editingQualityIssue ? '编辑质量问题' : '记录质量问题'"
      width="600px"
    >
      <el-form :model="qualityIssueForm" label-width="100px">
        <el-form-item label="房间">
          <span>{{ currentRoom?.building_unit }} {{ currentRoom?.room_number }}号房</span>
        </el-form-item>
        <el-form-item label="问题描述" required>
          <el-input
            v-model="qualityIssueForm.description"
            type="textarea"
            rows="4"
            placeholder="请详细描述质量问题"
          />
        </el-form-item>
        <el-form-item label="问题类型" required>
          <el-select 
            v-model="qualityIssueForm.issue_type" 
            placeholder="请选择问题类型"
            style="width: 100%"
          >
            <el-option label="质量瑕疵" value="质量瑕疵" />
            <el-option label="材料备货" value="材料备货" />
          </el-select>
        </el-form-item>
        <el-form-item label="完成时间" required>
          <el-date-picker
            v-model="qualityIssueForm.record_date"
            type="date"
            placeholder="请选择完成时间"
            format="YYYY/MM/DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="qualityIssueDialogVisible = false">取消</el-button>
        <el-button @click="resetQualityIssueForm">重置</el-button>
        <el-button type="primary" @click="saveQualityIssue">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading, ChatLineSquare, Warning, Select, Plus, Refresh } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import api from '../api/index.js'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(true)
const refreshing = ref(false)
const assignedRooms = ref([])
const selectedRoomId = ref(null)
const currentRoom = ref(null)
const qualityIssues = ref([])
const communications = ref([])

// 对话框控制
const qualityIssueDialogVisible = ref(false)
const editingQualityIssue = ref(null)

// 表单数据
const qualityIssueForm = ref({
  description: '',
  issue_type: '',
  record_date: '',
  images: []
})

// 获取分配给当前用户的房间
const fetchAssignedRooms = async () => {
  try {
    loading.value = true
    console.log('正在获取房间分配信息...')
    const assignmentsResponse = await api.get('/room-assignments/')
    const assignments = assignmentsResponse.data
    console.log('房间分配信息:', assignments)
    
    const roomPromises = assignments.map(async (assignment) => {
      const roomResponse = await api.get(`/rooms/${assignment.room_id}`)
      const room = roomResponse.data
      
      const communicationsResponse = await api.get(`/communications/?room_id=${room.id}`)
      const communications = communicationsResponse.data
      
      const issuesResponse = await api.get(`/quality-issues/?room_id=${room.id}`)
      const issues = issuesResponse.data
      const pendingVerification = issues.filter(issue => !issue.is_verified)
      const pendingImplementation = communications.filter(comm => !comm.is_implemented)
      
      return {
        ...room,
        communication_count: communications.length,
        quality_issue_count: issues.length,
        pending_verification_count: pendingVerification.length,
        pending_implementation_count: pendingImplementation.length
      }
    })
    
    assignedRooms.value = await Promise.all(roomPromises)
    
    // 默认选择第一个房间
    if (assignedRooms.value.length > 0 && !selectedRoomId.value) {
      selectedRoomId.value = assignedRooms.value[0].id
    }
  } catch (error) {
    console.error('获取房间信息失败:', error)
    ElMessage.error('获取房间信息失败')
  } finally {
    loading.value = false
  }
}

// 处理房间切换
const handleRoomChange = (roomId) => {
  const room = assignedRooms.value.find(r => r.id === roomId)
  if (room) {
    currentRoom.value = room
    fetchRoomDetails(roomId)
  }
}

// 获取房间详细信息
const fetchRoomDetails = async (roomId) => {
  try {
    // 获取质量问题
    const issuesResponse = await api.get(`/quality-issues/?room_id=${roomId}`)
    qualityIssues.value = issuesResponse.data
    
    // 获取沟通记录
    const communicationsResponse = await api.get(`/communications/?room_id=${roomId}`)
    communications.value = communicationsResponse.data
  } catch (error) {
    console.error('获取房间详情失败:', error)
    ElMessage.error('获取房间详情失败')
  }
}

// 监听房间选择变化
watch(selectedRoomId, (newRoomId) => {
  if (newRoomId) {
    handleRoomChange(newRoomId)
  }
})

// 格式化日期
const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

// 格式化日期时间（详细格式）
const formatDateTime = (dateString) => {
  if (!dateString) return ''
  return new Date(dateString).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 获取状态显示文本
const getStatusText = (status) => {
  const statusMap = {
    '整改中': '整改中',
    '验收完成': '验收完成',
    '闭户': '闭户',
    'under_renovation': '整改中',
    'closed': '闭户',
    'delivered': '已交付',
    'contracted': '已签约'
  }
  return statusMap[status] || status
}

// 获取状态标签类型
const getStatusType = (status) => {
  const typeMap = {
    '整改中': 'warning',
    '验收完成': 'success',
    '闭户': 'info',
    'under_renovation': 'warning',
    'closed': 'info',
    'delivered': 'success',
    'contracted': 'primary'
  }
  return typeMap[status] || 'info'
}

// 获取工作台标题
const getWorkplaceTitle = () => {
  const userRole = authStore.user?.role
  if (userRole === 'maintenance_engineer') {
    return '维修工程师工作台'
  } else if (userRole === 'project_engineer') {
    return '项目工程师工作台'
  }
  return '工程师工作台'
}

// 格式化预计交付时间
const formatExpectedDeliveryDate = (dateString) => {
  if (!dateString) return '未设置'
  const date = new Date(dateString)
  return `${String(date.getMonth() + 1).padStart(2, '0')}/${String(date.getDate()).padStart(2, '0')}`
}


// 打开质量问题对话框
const openQualityIssueDialog = () => {
  editingQualityIssue.value = null
  // 设置默认录入时间为今天
  const today = new Date().toISOString().split('T')[0]
  qualityIssueForm.value = {
    description: '',
    issue_type: '',
    record_date: today,
    images: []
  }
  qualityIssueDialogVisible.value = true
}

// 编辑质量问题
const editQualityIssue = (issue) => {
  editingQualityIssue.value = issue
  qualityIssueForm.value = {
    description: issue.description || '',
    issue_type: issue.issue_type || '',
    record_date: issue.record_date ? new Date(issue.record_date).toISOString().split('T')[0] : '',
    images: []
  }
  qualityIssueDialogVisible.value = true
}

// 保存质量问题
const saveQualityIssue = async () => {
  if (!qualityIssueForm.value.description.trim()) {
    ElMessage.error('请输入问题描述')
    return
  }
  
  if (!qualityIssueForm.value.issue_type) {
    ElMessage.error('请选择问题类型')
    return
  }
  
  if (!qualityIssueForm.value.record_date) {
    ElMessage.error('请选择完成时间')
    return
  }
  
  try {
    // 格式化日期为 YYYY-MM-DD HH:MM:SS 格式
    const recordDate = qualityIssueForm.value.record_date ? 
      new Date(qualityIssueForm.value.record_date + 'T00:00:00').toISOString() : null
    
    const data = {
      room_id: selectedRoomId.value,
      description: qualityIssueForm.value.description,
      issue_type: qualityIssueForm.value.issue_type,
      record_date: recordDate,
    }
    
    if (editingQualityIssue.value) {
      // 编辑模式
      await api.put(`/quality-issues/${editingQualityIssue.value.id}`, data)
      ElMessage.success('质量问题更新成功')
    } else {
      // 新增模式
      await api.post('/quality-issues/', data)
      ElMessage.success('质量问题记录成功')
    }
    
    qualityIssueDialogVisible.value = false
    editingQualityIssue.value = null
    
    // 刷新当前房间数据和汇总信息
    await fetchRoomDetails(selectedRoomId.value)
    await fetchAssignedRooms()
    // 更新当前房间的统计信息
    const updatedRoom = assignedRooms.value.find(r => r.id === selectedRoomId.value)
    if (updatedRoom) {
      currentRoom.value = updatedRoom
    }
  } catch (error) {
    console.error('保存质量问题失败:', error)
    const action = editingQualityIssue.value ? '更新' : '保存'
    ElMessage.error(`${action}质量问题失败`)
  }
}

// 重置质量问题表单
const resetQualityIssueForm = () => {
  const today = new Date().toISOString().split('T')[0]
  qualityIssueForm.value = {
    description: '',
    issue_type: '',
    record_date: today,
    images: []
  }
}

// 验收质量问题
const verifyIssue = async (issue) => {
  try {
    await ElMessageBox.confirm(
      '确认验收此质量问题吗？',
      '质量验收确认',
      {
        confirmButtonText: '确认验收',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await api.put(`/quality-issues/${issue.id}`, {
      is_verified: true
    })
    
    ElMessage.success('质量问题验收成功')
    
    // 刷新当前房间数据和汇总信息
    await fetchRoomDetails(selectedRoomId.value)
    await fetchAssignedRooms()
    // 更新当前房间的统计信息
    const updatedRoom = assignedRooms.value.find(r => r.id === selectedRoomId.value)
    if (updatedRoom) {
      currentRoom.value = updatedRoom
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('验收质量问题失败:', error)
      ElMessage.error('验收质量问题失败')
    }
  }
}


// 刷新房间数据
const refreshRoomData = async () => {
  if (!selectedRoomId.value) return
  
  try {
    refreshing.value = true
    // 先刷新房间详情
    await fetchRoomDetails(selectedRoomId.value)
    // 再刷新所有房间的汇总信息
    await fetchAssignedRooms()
    // 更新当前房间的统计信息
    const updatedRoom = assignedRooms.value.find(r => r.id === selectedRoomId.value)
    if (updatedRoom) {
      currentRoom.value = updatedRoom
    }
    ElMessage.success('汇总信息已更新')
  } catch (error) {
    console.error('刷新数据失败:', error)
    ElMessage.error('刷新数据失败')
  } finally {
    refreshing.value = false
  }
}


onMounted(() => {
  console.log('项目工程师界面加载，当前用户:', authStore.user)
  console.log('用户角色:', authStore.user?.role)
  console.log('是否为工程师:', authStore.isEngineer)
  console.log('认证token存在:', !!authStore.token)
  fetchAssignedRooms()
})
</script>

<style scoped>
.engineer-dashboard {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.dashboard-header {
  margin-bottom: 32px;
  text-align: center;
}

.dashboard-header h3 {
  margin: 0 0 8px 0;
  font-size: 28px;
  color: #303133;
  font-weight: 600;
}

.role-description {
  margin: 0;
  color: #909399;
  font-size: 16px;
}

.loading {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  padding: 40px;
  color: #909399;
}

.no-rooms {
  padding: 40px;
  text-align: center;
}

.room-selector {
  margin-bottom: 24px;
  text-align: center;
}

.current-room-info {
  margin-bottom: 24px;
}

.room-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.room-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.room-info h4 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}

.status-tags {
  display: flex;
  gap: 8px;
}

.room-controls {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 12px;
}

.status-display {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}

.status-item label {
  color: #606266;
  white-space: nowrap;
  font-weight: 500;
}

.status-value {
  background-color: #f4f4f5;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  color: #606266;
  font-size: 12px;
  padding: 4px 8px;
  min-width: 40px;
  text-align: center;
  display: inline-block;
}

.room-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.stat-item {
  text-align: center;
}

.function-modules {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.module-card {
  height: fit-content;
}

.module-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.module-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 16px;
}

.module-content {
  max-height: 400px;
  overflow-y: auto;
}

.empty-content {
  text-align: center;
  padding: 20px;
}

.issues-list,
.communications-list {
  space: 16px 0;
}

.issue-item,
.communication-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
  background-color: #fafafa;
}

.issue-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.comm-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.issue-date {
  font-size: 12px;
  color: #909399;
}

.comm-date {
  font-size: 14px;
  color: #409EFF;
  font-weight: 600;
}

.comm-time {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.comm-author {
  font-size: 12px;
  color: #606266;
}

.issue-description {
  margin: 8px 0;
  color: #606266;
  line-height: 1.5;
}

.issue-actions {
  margin-top: 12px;
}

.comm-content {
  margin-top: 8px;
}

.comm-section {
  margin-bottom: 12px;
}

.comm-section strong {
  color: #303133;
  font-size: 14px;
}

.comm-section p {
  margin: 4px 0 0 0;
  color: #606266;
  line-height: 1.5;
}

.comm-actions {
  margin-top: 12px;
  padding-top: 8px;
  border-top: 1px solid #f0f0f0;
}

@media (max-width: 768px) {
  .function-modules {
    grid-template-columns: 1fr;
  }
  
  .room-stats {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
  
  .room-header {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .room-controls {
    align-items: stretch;
  }
  
  .status-display {
    flex-direction: column;
    gap: 8px;
  }
  
  .status-item {
    justify-content: space-between;
  }
}
</style>