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

    <div v-else-if="rooms.length === 0" class="empty-state">
      <el-empty description="您当前没有被分配任何房间" />
    </div>

    <div v-else class="dashboard-content">
      <!-- 房间卡片列表 -->
      <div class="rooms-grid">
        <div v-for="room in rooms" :key="room.id" class="room-card">
          <el-card 
            :class="{ 'active-room': selectedRoomId === room.id }"
            @click="selectRoom(room.id)"
          >
            <div class="room-header">
              <h4>{{ room.building_unit }} {{ formatRoomNumber(room.room_number) }}号房</h4>
              <el-tag :type="getStatusType(room.status)">{{ room.status }}</el-tag>
            </div>
            
            <div class="room-stats">
              <div class="stat-item">
                <el-statistic title="质量问题" :value="room.quality_issue_count || 0" />
              </div>
              <div class="stat-item">
                <el-statistic title="待验收" :value="room.pending_verification_count || 0" />
              </div>
            </div>
          </el-card>
        </div>
      </div>

      <!-- 房间详情面板 -->
      <div v-if="selectedRoomId && currentRoom" class="room-details">
        <!-- 合并后的房间信息与状态管理卡片 -->
        <el-card class="unified-room-card">
          <template #header>
            <div class="room-header">
              <div class="room-title">
                <el-icon><House /></el-icon>
                <h4>{{ currentRoom.building_unit }} {{ formatRoomNumber(currentRoom.room_number) }}号房 - 信息与状态管理</h4>
              </div>
              <div class="header-tags">
                <el-text type="info" size="small" style="margin-right: 12px;">只读模式 - 仅客户大使可编辑</el-text>
                <el-tag :type="getStatusType(currentRoom.status)" size="large">{{ currentRoom.status }}</el-tag>
              </div>
            </div>
          </template>
          
          <!-- 状态管理区域 -->
          <div class="status-management-section">
            <div class="section-title">
              <el-icon><Setting /></el-icon>
              <span>状态管理</span>
            </div>
            <div class="status-controls readonly">
              <div class="status-item">
                <label>交付状态</label>
                <el-tag :type="currentRoom.delivery_status === '已交付' ? 'success' : 'warning'" size="small">
                  {{ currentRoom.delivery_status || '待交付' }}
                </el-tag>
              </div>
              
              <div class="status-item">
                <label>签约状态</label>
                <el-tag :type="currentRoom.contract_status === '已签约' ? 'success' : 'warning'" size="small">
                  {{ currentRoom.contract_status || '待签约' }}
                </el-tag>
              </div>
              
              <div class="status-item">
                <label>信件状态</label>
                <el-tag :type="currentRoom.letter_status === '无' ? 'info' : 'warning'" size="small">
                  {{ currentRoom.letter_status || '无' }}
                </el-tag>
              </div>
              
              <div class="status-item">
                <label>预计交付时间</label>
                <span class="status-text">
                  {{ currentRoom.expected_delivery_date ? formatDateOnly(currentRoom.expected_delivery_date) : '未设置' }}
                </span>
              </div>
            </div>
          </div>

          <!-- 质量问题统计区域 -->
          <div class="statistics-section">
            <div class="section-title">
              <el-icon><DataAnalysis /></el-icon>
              <span>质量问题统计</span>
            </div>
            <div class="stats-grid">
              <div class="stat-card">
                <el-statistic title="总计" :value="roomStats.total" />
                <el-icon class="stat-icon total"><Document /></el-icon>
              </div>
              <div class="stat-card">
                <el-statistic title="待验收" :value="roomStats.pending" />
                <el-icon class="stat-icon pending"><Clock /></el-icon>
              </div>
              <div class="stat-card">
                <el-statistic title="已验收" :value="roomStats.completed" />
                <el-icon class="stat-icon completed"><CircleCheck /></el-icon>
              </div>
              <div class="stat-card completion-rate">
                <el-statistic title="验收完成率" :value="roomStats.completionRate" suffix="%" />
                <el-progress 
                  :percentage="roomStats.completionRate" 
                  :stroke-width="8"
                  :show-text="false"
                  color="#67c23a"
                  class="progress-bar"
                />
                <el-icon class="stat-icon completed"><CircleCheck /></el-icon>
              </div>
            </div>
            
            <!-- 问题类型分布 -->
            <div class="type-distribution">
              <div class="type-item">
                <span class="type-label">🔧 质量瑕疵:</span>
                <span class="type-stats">{{ roomStats.qualityDefects.total }} (待验收:{{ roomStats.qualityDefects.pending }} | 已验收:{{ roomStats.qualityDefects.completed }})</span>
              </div>
              <div class="type-item">
                <span class="type-label">📦 材料备货:</span>
                <span class="type-stats">{{ roomStats.materialPrep.total }} (待验收:{{ roomStats.materialPrep.pending }} | 已验收:{{ roomStats.materialPrep.completed }})</span>
              </div>
            </div>
          </div>

          <!-- 责任分工区域 -->
          <div class="assignment-section">
            <div class="section-title">
              <el-icon><User /></el-icon>
              <span>责任分工</span>
            </div>
            <div class="assignment-grid">
              <div class="assignment-item">
                <span class="role-label">🤝 客户大使:</span>
                <span class="person-name">{{ getUserByRole(currentRoom.assigned_users, 'customer_ambassador')?.name || '未分配' }}</span>
              </div>
              <div class="assignment-item">
                <span class="role-label">🔧 项目工程师:</span>
                <span class="person-name">{{ getUserByRole(currentRoom.assigned_users, 'project_engineer')?.name || '未分配' }}</span>
              </div>
              <div class="assignment-item">
                <span class="role-label">🛠️ 维修工程师:</span>
                <span class="person-name">{{ getUserByRole(currentRoom.assigned_users, 'maintenance_engineer')?.name || '未分配' }}</span>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 质量问题管理模块 -->
        <el-card class="module-card">
          <template #header>
            <div class="module-header">
              <div class="module-title">
                <el-icon><Tools /></el-icon>
                <span>质量问题管理</span>
              </div>
              <el-button type="primary" @click="openQualityIssueDialog">
                <el-icon><Plus /></el-icon>
                添加质量问题
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
                <div class="issue-header">
                  <span class="issue-date">录入时间：{{ formatDateOnly(issue.record_date || issue.created_at) }}</span>
                  <el-tag :type="getIssueStatusType(issue.status)">{{ issue.status }}</el-tag>
                </div>
                <div class="issue-content">
                  <div class="issue-section">
                    <strong>问题描述:</strong>
                    <p>{{ issue.description }}</p>
                  </div>
                  <div class="issue-section">
                    <strong>问题类型:</strong>
                    <span>{{ issue.issue_type }}</span>
                  </div>
                  <div class="issue-section">
                    <strong>记录人:</strong>
                    <span>{{ getUserDisplayName(issue) }} | 录入：{{ formatDateOnly(issue.record_date || issue.created_at) }}</span>
                  </div>
                  <!-- 验收信息 -->
                  <div v-if="issue.status === '已验收'" class="issue-section">
                    <strong>验收信息:</strong>
                    <span>{{ getAcceptanceInfo(issue) }}</span>
                  </div>
                  <!-- 注意：已简化验收流程，只支持待验收和已验收两种状态 -->
                  <div v-if="issue.images" class="issue-images">
                    <strong>相关图片:</strong>
                    <div class="images-container">
                      <el-image
                        v-for="(image, index) in JSON.parse(issue.images || '[]')"
                        :key="index"
                        :src="`/api/uploads/${image}`"
                        style="width: 80px; height: 60px; margin-right: 8px;"
                        fit="cover"
                        :preview-src-list="JSON.parse(issue.images || '[]').map(img => `/api/uploads/${img}`)"
                        class="preview-image"
                      />
                    </div>
                  </div>
                </div>
                <div class="issue-actions">
                  <!-- 验收按钮 - 只有项目工程师可见 -->
                  <el-button 
                    v-if="issue.status === '待验收' && authStore.user?.role === 'project_engineer'" 
                    type="success" 
                    size="small"
                    @click="acceptIssue(issue)"
                  >
                    <el-icon><Check /></el-icon>
                    验收
                  </el-button>
                  <!-- 查看日志按钮 -->
                  <el-button 
                    type="info" 
                    size="small"
                    @click="viewIssueLogs(issue.id)"
                    :title="`Debug: issue.id = ${issue.id}, type = ${typeof issue.id}`"
                  >
                    <el-icon><Document /></el-icon>
                    查看日志
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 快速添加质量问题对话框 -->
    <el-dialog
      v-model="qualityIssueDialogVisible"
      title="添加质量问题"
      width="700px"
    >
      <el-form :model="qualityIssueForm" label-width="100px">
        <el-form-item label="房间">
          <span>{{ currentRoom?.building_unit }} {{ formatRoomNumber(currentRoom?.room_number) }}号房</span>
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
          <el-select v-model="qualityIssueForm.issue_type" placeholder="请选择问题类型" style="width: 100%">
            <el-option label="质量瑕疵" value="质量瑕疵" />
            <el-option label="材料备货" value="材料备货" />
          </el-select>
        </el-form-item>
        <el-form-item label="录入时间" required>
          <el-date-picker
            v-model="qualityIssueForm.record_date"
            type="date"
            placeholder="请选择录入时间"
            format="YYYY/MM/DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="相关图片">
          <el-upload
            ref="uploadRef"
            action=""
            :http-request="uploadImage"
            :show-file-list="false"
            accept="image/*"
            :before-upload="beforeImageUpload"
            multiple
          >
            <el-button type="primary">
              <el-icon><Upload /></el-icon>
              点击上传图片
            </el-button>
            <template #tip>
              <div class="el-upload__tip">
                只能上传jpg/png文件，且不超过5MB，最多2张图片
              </div>
            </template>
          </el-upload>
          
          <!-- 图片预览 -->
          <div v-if="qualityIssueForm.uploadedImages.length > 0" class="uploaded-images">
            <div v-for="(image, index) in qualityIssueForm.uploadedImages" :key="index" class="image-item">
              <el-image
                :src="`/api/uploads/${image}`"
                style="width: 100px; height: 75px"
                fit="cover"
                class="preview-img"
              />
              <el-button
                type="danger"
                size="small"
                circle
                class="remove-btn"
                @click="removeImage(index)"
              >
                <el-icon><Close /></el-icon>
              </el-button>
            </div>
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="qualityIssueDialogVisible = false">取消</el-button>
        <el-button @click="resetQualityIssueForm">重置</el-button>
        <el-button type="primary" @click="saveQualityIssue">保存</el-button>
      </template>
    </el-dialog>

    <!-- 操作日志查看对话框 -->
    <el-dialog
      v-model="logsDialogVisible"
      width="800px"
      :close-on-click-modal="false"
    >
      <template #header>
        <div class="logs-dialog-header">
          <span class="logs-title">操作日志</span>
          <span v-if="currentIssueInfo" class="logs-record-time">
            问题录入: {{ formatDateOnly(currentIssueInfo.record_date || currentIssueInfo.created_at) }}
          </span>
        </div>
      </template>
      <div v-if="logsLoading" class="logs-loading">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>加载日志中...</span>
      </div>
      
      <div v-else-if="issueLogs.length === 0" class="logs-empty">
        <el-empty description="暂无操作日志" />
      </div>
      
      <div v-else class="logs-container">
        <div class="logs-timeline">
          <div 
            v-for="(log, index) in issueLogs" 
            :key="log.id"
            class="log-item"
            :class="getLogItemClass(log.action)"
          >
            <div class="log-dot">
              <el-icon :class="getLogIconClass(log.action)">
                <component :is="getLogIcon(log.action)" />
              </el-icon>
            </div>
            
            <div class="log-content">
              <div class="log-header">
                <div class="log-action">{{ getLogActionText(log.action) }}</div>
                <div class="log-time">操作时间: {{ formatDateTime(log.timestamp) }}</div>
              </div>
              
              <div class="log-operator">
                <el-icon><User /></el-icon>
                <span>{{ log.operator_name }}</span>
                <el-tag size="small" type="info">{{ log.operator_role }}</el-tag>
              </div>
              
              <div class="log-description">
                <el-icon><component :is="getLogDescriptionIcon(log.action)" /></el-icon>
                <span>{{ getLogDescription(log.action) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="logsDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading, Tools, Plus, Upload, Close, Setting, Document, User, Edit, Check, RefreshLeft, House, DataAnalysis, Clock, CircleCheck } from '@element-plus/icons-vue'
import api from '../api'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()

// 响应式数据
const loading = ref(true)
const rooms = ref([])
const selectedRoomId = ref(null)
const currentRoom = ref(null)
const qualityIssues = ref([])

// 对话框控制
const qualityIssueDialogVisible = ref(false)

// 日志查看控制
const logsDialogVisible = ref(false)
const logsLoading = ref(false)
const issueLogs = ref([])
const currentIssueId = ref(null)
const currentIssueInfo = ref(null)

// 表单引用
const uploadRef = ref(null)

// 表单数据
const qualityIssueForm = ref({
  description: '',
  issue_type: '质量瑕疵',
  record_date: '',
  uploadedImages: []
})

// 获取工作台标题
const getWorkplaceTitle = () => {
  const role = authStore.user?.role
  const titleMap = {
    'project_engineer': '项目工程师工作台',
    'maintenance_engineer': '维修工程师工作台'
  }
  return titleMap[role] || '工程师工作台'
}

// 组件挂载时获取数据
onMounted(async () => {
  await fetchRooms()
  if (rooms.value.length > 0) {
    selectRoom(rooms.value[0].id)
  }
  loading.value = false
})

// 获取房间列表
const fetchRooms = async () => {
  try {
    const response = await api.get('/room-assignments/')
    const assignments = response.data
    
    const roomsData = await Promise.all(
      assignments.map(async (assignment) => {
        const roomResponse = await api.get(`/rooms/${assignment.room_id}`)
        const room = roomResponse.data
        
        const issuesResponse = await api.get(`/quality-issues/?room_id=${room.id}`)
        const issues = issuesResponse.data
        const pendingVerification = issues.filter(issue => issue.status === '待验收')
        return {
          ...room,
          quality_issue_count: issues.length,
          pending_verification_count: pendingVerification.length
        }
      })
    )
    
    rooms.value = roomsData
  } catch (error) {
    console.error('获取房间列表失败:', error)
    ElMessage.error('获取房间列表失败')
  }
}

// 格式化房号，去掉前导零
const formatRoomNumber = (roomNumber) => {
  if (!roomNumber) return roomNumber
  // 将房号转为字符串，然后去掉前导零
  return parseInt(roomNumber).toString()
}

// 选择房间
const selectRoom = async (roomId) => {
  selectedRoomId.value = roomId
  await fetchRoomDetails(roomId)
}

// 获取房间详情
const fetchRoomDetails = async (roomId) => {
  try {
    // 获取房间基本信息
    const roomResponse = await api.get(`/rooms/${roomId}`)
    currentRoom.value = roomResponse.data
    
    // 获取质量问题
    const issuesResponse = await api.get(`/quality-issues/?room_id=${roomId}`)
    console.log('Quality issues response:', issuesResponse.data)
    console.log('First issue structure:', issuesResponse.data[0])
    
    // 按照录入时间和创建时间降序排序，新问题在前
    qualityIssues.value = issuesResponse.data.sort((a, b) => {
      const dateA = new Date(a.record_date || a.created_at)
      const dateB = new Date(b.record_date || b.created_at)
      return dateB - dateA
    })
    
    // 调试每个质量问题的 ID
    qualityIssues.value.forEach((issue, index) => {
      console.log(`Issue ${index}:`, {
        id: issue.id,
        id_type: typeof issue.id,
        id_string: String(issue.id),
        description: issue.description?.substring(0, 50) + '...'
      })
    })
    
    // 更新统计数据
    const pendingVerification = qualityIssues.value.filter(issue => issue.status === '待验收')
    
    currentRoom.value = {
      ...currentRoom.value,
      quality_issue_count: qualityIssues.value.length,
      pending_verification_count: pendingVerification.length
    }
    
  } catch (error) {
    console.error('获取房间详情失败:', error)
    ElMessage.error('获取房间详情失败')
  }
}

// 状态类型映射
const getStatusType = (status) => {
  const typeMap = {
    '整改中': 'warning',
    '闭户': 'info',
    '已交付': 'success',
    '验收完成': 'success'
  }
  return typeMap[status] || 'info'
}

const getIssueStatusType = (status) => {
  const typeMap = {
    '待验收': 'warning',
    '已验收': 'success'
  }
  return typeMap[status] || 'warning'
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    timeZone: 'Asia/Shanghai'
  })
}

// 格式化日期 - 只显示年月日
const formatDateOnly = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN')
}

// 获取用户显示名称
const getUserDisplayName = (record) => {
  if (record.user_name) {
    const roleText = getRoleText(record.user_role)
    return `${record.user_name}(${roleText})`
  }
  return '未知用户'
}

const getRoleText = (role) => {
  const roleMap = {
    'customer_ambassador': '客户大使',
    'project_engineer': '项目工程师',
    'maintenance_engineer': '维修工程师'
  }
  return roleMap[role] || role
}

// 获取指定角色的用户
const getUserByRole = (users, role) => {
  if (!users || users.length === 0) return null
  return users.find(user => user.role === role) || null
}

// 计算房间统计数据
const roomStats = computed(() => {
  const issues = qualityIssues.value
  
  return {
    total: issues.length,
    pending: issues.filter(i => i.status === '待验收').length,
    completed: issues.filter(i => i.status === '已验收').length,
    completionRate: issues.length > 0 ? 
      Math.round((issues.filter(i => i.status === '已验收').length / issues.length) * 100) : 0,
    
    // 按类型分组统计
    qualityDefects: {
      total: issues.filter(i => i.issue_type === '质量瑕疵').length,
      pending: issues.filter(i => i.issue_type === '质量瑕疵' && i.status === '待验收').length,
      completed: issues.filter(i => i.issue_type === '质量瑕疵' && i.status === '已验收').length
    },
    materialPrep: {
      total: issues.filter(i => i.issue_type === '材料备货').length,
      pending: issues.filter(i => i.issue_type === '材料备货' && i.status === '待验收').length,
      completed: issues.filter(i => i.issue_type === '材料备货' && i.status === '已验收').length
    }
  }
})

// 打开质量问题对话框
const openQualityIssueDialog = () => {
  const today = new Date().toISOString().split('T')[0]
  qualityIssueForm.value = {
    description: '',
    issue_type: '质量瑕疵',
    record_date: today,
    uploadedImages: []
  }
  qualityIssueDialogVisible.value = true
}

// 重置质量问题表单
const resetQualityIssueForm = () => {
  const today = new Date().toISOString().split('T')[0]
  qualityIssueForm.value = {
    description: '',
    issue_type: '质量瑕疵',
    record_date: today,
    uploadedImages: []
  }
  ElMessage.success('表单已重置')
}

// 保存质量问题
const saveQualityIssue = async () => {
  if (!qualityIssueForm.value.description.trim()) {
    ElMessage.error('请输入问题描述')
    return
  }
  
  if (!qualityIssueForm.value.record_date) {
    ElMessage.error('请选择录入时间')
    return
  }
  
  try {
    const data = {
      room_id: selectedRoomId.value,
      description: qualityIssueForm.value.description,
      issue_type: qualityIssueForm.value.issue_type,
      record_date: qualityIssueForm.value.record_date,
      images: JSON.stringify(qualityIssueForm.value.uploadedImages)
    }
    
    await api.post('/quality-issues/', data)
    ElMessage.success('质量问题保存成功')
    
    qualityIssueDialogVisible.value = false
    
    // 刷新数据
    await fetchRoomDetails(selectedRoomId.value)
    await fetchRooms()
    
  } catch (error) {
    console.error('保存质量问题失败:', error)
    ElMessage.error('保存质量问题失败')
  }
}

// 获取验收信息
const getAcceptanceInfo = (issue) => {
  if (issue.accepted_by && issue.acceptor_name) {
    return `${issue.acceptor_name}(${getRoleText(issue.acceptor_role)}) | 验收：${formatDateOnly(issue.accepted_at)}`
  }
  return '验收信息缺失'
}

// 注意：撤销和复验功能已移除，系统简化为待验收和已验收两种状态

// 验收质量问题 - 只有项目工程师有权限
const acceptIssue = async (issue) => {
  try {
    await ElMessageBox.confirm(
      '确认验收此质量问题吗？验收后将标记为已验收状态。',
      '验收确认',
      {
        confirmButtonText: '确认验收',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await api.put(`/quality-issues/${issue.id}/accept`)
    ElMessage.success('质量问题验收成功')
    
    // 刷新数据
    await fetchRoomDetails(selectedRoomId.value)
    await fetchRooms()
    
  } catch (error) {
    if (error === 'cancel') {
      return
    }
    console.error('验收失败:', error)
    ElMessage.error('验收失败，请重试')
  }
}

// 图片上传相关
const beforeImageUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  const isLt5M = file.size / 1024 / 1024 < 5
  const hasSpace = qualityIssueForm.value.uploadedImages.length < 2

  if (!isImage) {
    ElMessage.error('只能上传图片文件!')
    return false
  }
  if (!isLt5M) {
    ElMessage.error('上传图片大小不能超过 5MB!')
    return false
  }
  if (!hasSpace) {
    ElMessage.error('最多只能上传2张图片!')
    return false
  }
  return true
}

const uploadImage = async (options) => {
  const formData = new FormData()
  formData.append('file', options.file)
  
  try {
    const response = await api.post('/upload-image/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    qualityIssueForm.value.uploadedImages.push(response.data.filename)
    ElMessage.success('图片上传成功')
  } catch (error) {
    console.error('图片上传失败:', error)
    ElMessage.error('图片上传失败')
  }
}

const removeImage = (index) => {
  qualityIssueForm.value.uploadedImages.splice(index, 1)
  ElMessage.success('图片已删除')
}

// 日志查看相关方法
const viewIssueLogs = async (issueId) => {
  console.log('=== viewIssueLogs Debug Start ===')
  console.log('Raw issueId:', issueId)
  console.log('Type of issueId:', typeof issueId)
  console.log('String representation:', String(issueId))
  console.log('JSON stringified:', JSON.stringify(issueId))
  
  currentIssueId.value = issueId
  logsDialogVisible.value = true
  logsLoading.value = true
  
  try {
    // 确保 issueId 是纯数字
    const cleanIssueId = parseInt(String(issueId).split(':')[0])
    console.log('Cleaned issueId:', cleanIssueId)
    
    const logsUrl = `/quality-issues/${cleanIssueId}/logs`
    console.log('Final requesting URL:', logsUrl)
    console.log('=== viewIssueLogs Debug End ===')
    
    const [issueResponse, logsResponse] = await Promise.all([
      api.get(`/quality-issues/${cleanIssueId}`),
      api.get(logsUrl)
    ])
    
    currentIssueInfo.value = issueResponse.data
    issueLogs.value = logsResponse.data.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
  } catch (error) {
    console.error('获取操作日志失败:', error)
    ElMessage.error('获取操作日志失败')
  } finally {
    logsLoading.value = false
  }
}

// 日志相关格式化方法
const getLogActionText = (action) => {
  const actionMap = {
    'CREATE': '创建问题',
    'UPDATE': '修改问题',
    'ACCEPT': '验收通过',
    'REVOKE_ACCEPT': '撤销验收',
    'REVERIFY': '复验通过'
  }
  return actionMap[action] || action
}

// 获取操作描述
const getLogDescription = (action) => {
  const descriptionMap = {
    'CREATE': '创建了新的质量问题',
    'UPDATE': '更新了问题描述和相关图片',
    'ACCEPT': '质量问题验收通过，问题状态更新为"已验收"',
    'REVOKE_ACCEPT': '撤销了验收状态',
    'REVERIFY': '复验确认问题已解决'
  }
  return descriptionMap[action] || '执行了操作'
}

// 获取操作描述图标
const getLogDescriptionIcon = (action) => {
  const iconMap = {
    'CREATE': Edit,
    'UPDATE': Edit,
    'ACCEPT': Check,
    'REVOKE_ACCEPT': RefreshLeft,
    'REVERIFY': Check
  }
  return iconMap[action] || Document
}

const getLogIcon = (action) => {
  const iconMap = {
    'CREATE': Plus,
    'UPDATE': Edit,
    'ACCEPT': Check,
    'REVOKE_ACCEPT': RefreshLeft,
    'REVERIFY': Check
  }
  return iconMap[action] || Document
}

const getLogIconClass = (action) => {
  const classMap = {
    'CREATE': 'log-icon-create',
    'UPDATE': 'log-icon-update',
    'ACCEPT': 'log-icon-accept',
    'REVOKE_ACCEPT': 'log-icon-revoke',
    'REVERIFY': 'log-icon-reverify'
  }
  return classMap[action] || 'log-icon-default'
}

const getLogItemClass = (action) => {
  const classMap = {
    'CREATE': 'log-item-create',
    'UPDATE': 'log-item-update',
    'ACCEPT': 'log-item-accept',
    'REVOKE_ACCEPT': 'log-item-revoke',
    'REVERIFY': 'log-item-reverify'
  }
  return classMap[action] || 'log-item-default'
}

const formatLogData = (data) => {
  if (!data) return ''
  try {
    const parsed = JSON.parse(data)
    return JSON.stringify(parsed, null, 2)
  } catch {
    return data
  }
}

const formatDateTime = (datetime) => {
  if (!datetime) return ''
  const date = new Date(datetime)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    timeZone: 'Asia/Shanghai'
  })
}

// 统一的北京时间格式化函数，包含时区标注
const formatDateTimeWithTimezone = (datetime) => {
  if (!datetime) return ''
  const date = new Date(datetime)
  const formatted = date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    timeZone: 'Asia/Shanghai'
  })
  return `${formatted} (北京时间)`
}
</script>

<style scoped>
.engineer-dashboard {
  padding: 20px;
  background-color: #f5f5f5;
  min-height: 100vh;
}

.dashboard-header {
  text-align: center;
  margin-bottom: 30px;
}

.dashboard-header h3 {
  font-size: 28px;
  color: #303133;
  margin-bottom: 8px;
}

.role-description {
  color: #606266;
  font-size: 16px;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  color: #909399;
}

.loading .el-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 400px;
}

.dashboard-content {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 20px;
  min-height: calc(100vh - 150px);
}

.rooms-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
  height: fit-content;
  max-height: 100%;
}

.room-card .el-card {
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.room-card .el-card:hover {
  border-color: #67c23a;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(103, 194, 58, 0.15);
}

.room-card .el-card.active-room {
  border-color: #67c23a;
  background-color: #f0f9ff;
}

.room-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.room-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.room-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.room-stats.three-stats {
  grid-template-columns: 1fr 1fr 1fr;
  gap: 8px;
}

.stat-item {
  text-align: center;
}

.room-details {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.room-info-card {
  flex-shrink: 0;
}

.room-info-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.room-info-header h4 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}

.room-info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-item label {
  font-weight: 600;
  color: #606266;
  min-width: 100px;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}

.stats-row.three-stats {
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
}

.module-card {
  flex: 1;
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
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.module-content {
  /* 移除固定高度，让内容自然流动 */
}

.empty-content {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
}

.issues-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.issue-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  background-color: #fafafa;
  transition: all 0.3s ease;
}

.issue-item:hover {
  border-color: #c6e2ff;
  background-color: #ecf5ff;
}

.issue-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.issue-date {
  font-size: 13px;
  color: #909399;
}

.issue-content {
  margin-bottom: 12px;
}

.issue-section {
  margin-bottom: 8px;
}

.issue-section strong {
  color: #606266;
  font-weight: 600;
  margin-right: 8px;
}

.issue-section p {
  margin: 4px 0;
  color: #303133;
  line-height: 1.5;
}

.issue-images {
  margin-top: 12px;
}

.images-container {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.preview-image {
  border-radius: 4px;
  border: 1px solid #dcdfe6;
  cursor: pointer;
  transition: all 0.3s ease;
}

.preview-image:hover {
  border-color: #67c23a;
  transform: scale(1.05);
}

.issue-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.verification-history {
  margin-left: 10px;
  font-size: 14px;
  line-height: 1.6;
}

.verification-history div {
  color: #606266;
  margin-bottom: 2px;
}

.uploaded-images {
  display: flex;
  gap: 12px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.image-item {
  position: relative;
}

.preview-img {
  border-radius: 6px;
  border: 1px solid #e4e7ed;
}

.remove-btn {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 24px;
  height: 24px;
  padding: 0;
}

/* 合并后的统一房间卡片样式 */
.unified-room-card {
  margin-bottom: 20px;
}

.room-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.room-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.room-title h4 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.header-tags {
  display: flex;
  align-items: center;
}

/* 分区样式 */
.status-management-section,
.statistics-section,
.assignment-section {
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid #f0f2f5;
}

.assignment-section {
  border-bottom: none;
  margin-bottom: 0;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
}

/* 状态管理区域 */
.status-controls {
  display: flex;
  align-items: flex-end;
  gap: 20px;
  flex-wrap: wrap;
}

.status-controls.readonly {
  background-color: #f9f9f9;
  padding: 16px;
  border-radius: 8px;
}

.status-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 140px;
}

.status-item label {
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  white-space: nowrap;
}

.status-item .el-select {
  width: 140px;
}

.status-item .el-date-picker {
  width: 150px;
  min-width: 150px;
}

.status-text {
  font-size: 14px;
  color: #303133;
  padding: 4px 8px;
  background-color: #f0f0f0;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
}

/* 统计区域 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.stat-card {
  position: relative;
  padding: 16px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  text-align: center;
  transition: all 0.3s ease;
}

.stat-card:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.15);
}

.stat-card .stat-icon {
  position: absolute;
  top: 12px;
  right: 12px;
  font-size: 20px;
  opacity: 0.6;
}

.stat-icon.total { color: #409eff; }
.stat-icon.pending { color: #e6a23c; }
.stat-icon.completed { color: #67c23a; }

.completion-rate {
  background: #ffffff;
  border: 2px solid #67c23a;
  color: #303133;
}

.completion-rate .stat-icon {
  color: #67c23a;
}

.progress-bar {
  margin-top: 8px;
}

/* 问题类型分布 */
.type-distribution {
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: #fafbfc;
  padding: 12px;
  border-radius: 6px;
}

.type-item {
  display: flex;
  align-items: center;
  padding: 6px 12px;
  background: white;
  border-radius: 4px;
  border: 1px solid #e2e8f0;
  margin-bottom: 4px;
}

.type-label {
  font-weight: 600;
  color: #303133;
  margin-right: 16px;
  min-width: 80px;
}

.type-stats {
  color: #606266;
  font-size: 14px;
  flex: 1;
}

/* 责任分工区域 */
.assignment-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.assignment-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f8fafc;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
}

.role-label {
  font-weight: 600;
  color: #303133;
}

.person-name {
  color: #606266;
  font-weight: 500;
}

/* 日志查看对话框样式 */
.logs-dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.logs-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.logs-record-time {
  font-size: 14px;
  color: #67c23a;
  font-weight: 500;
  background-color: #f0f9ff;
  padding: 4px 12px;
  border-radius: 4px;
  border: 1px solid #d4edda;
}

.logs-loading, .logs-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #909399;
}

.logs-loading .el-icon {
  font-size: 32px;
  margin-bottom: 12px;
}

.logs-container {
  max-height: 500px;
  overflow-y: auto;
}

.logs-timeline {
  position: relative;
  padding-left: 30px;
}

.logs-timeline::before {
  content: '';
  position: absolute;
  left: 15px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: linear-gradient(to bottom, #e4e7ed, #c0c4cc);
}

.log-item {
  position: relative;
  margin-bottom: 24px;
  padding-bottom: 16px;
}

.log-item:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
}

.log-dot {
  position: absolute;
  left: -22px;
  top: 2px;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  border: 2px solid #e4e7ed;
  z-index: 1;
}

.log-item-create .log-dot {
  border-color: #67c23a;
}

.log-item-update .log-dot {
  border-color: #e6a23c;
}

.log-item-accept .log-dot {
  border-color: #409eff;
}

.log-item-revoke .log-dot {
  border-color: #f56c6c;
}

.log-icon-create {
  color: #67c23a;
}

.log-icon-update {
  color: #e6a23c;
}

.log-icon-accept {
  color: #409eff;
}

.log-icon-revoke {
  color: #f56c6c;
}

.log-icon-default {
  color: #909399;
}

.log-content {
  background: #fafbfc;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  margin-left: 8px;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.log-action {
  font-weight: 600;
  color: #303133;
  font-size: 14px;
}

.log-time {
  font-size: 12px;
  color: #909399;
}

.log-operator {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
  font-size: 13px;
  color: #606266;
}

.log-description {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 8px 0;
  font-size: 14px;
  color: #303133;
  padding: 8px 12px;
  background-color: #f8fafc;
  border-radius: 6px;
  border-left: 3px solid #409eff;
}

.log-data {
  margin-top: 12px;
  border-top: 1px solid #ebeef5;
  padding-top: 12px;
}

.data-before, .data-after {
  margin-bottom: 8px;
}

.data-before strong, .data-after strong {
  color: #606266;
  font-size: 12px;
  display: block;
  margin-bottom: 4px;
}

.log-data pre {
  background: #f5f7fa;
  padding: 8px;
  border-radius: 4px;
  font-size: 11px;
  color: #606266;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 150px;
  overflow-y: auto;
  margin: 0;
}
</style>