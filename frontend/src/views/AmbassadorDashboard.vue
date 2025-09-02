<template>
  <div class="ambassador-dashboard">
    <div class="dashboard-header">
      <h3>客户大使工作台</h3>
      <p class="role-description">管理分配给您的房间的质量问题和客户沟通记录</p>
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
                <div class="status-controls">
                  <div class="control-group">
                    <label>交付状态：</label>
                    <el-select 
                      v-model="currentRoom.delivery_status" 
                      size="small"
                      @change="updateDeliveryStatus"
                      style="width: 100px"
                    >
                      <el-option label="待交付" value="待交付" />
                      <el-option label="已交付" value="已交付" />
                    </el-select>
                  </div>
                  <div class="control-group">
                    <label>签约状态：</label>
                    <el-select 
                      v-model="currentRoom.contract_status" 
                      size="small"
                      @change="updateContractStatus"
                      style="width: 100px"
                    >
                      <el-option label="待签约" value="待签约" />
                      <el-option label="已签约" value="已签约" />
                    </el-select>
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
                <span>客户沟通管理</span>
              </div>
              <el-button type="primary" @click="openCommunicationDialog">
                <el-icon><Plus /></el-icon>
                添加沟通记录
              </el-button>
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
                  <div class="comm-actions">
                    <el-button 
                      v-if="!comm.is_implemented" 
                      type="success" 
                      size="small"
                      @click="markImplemented(comm)"
                    >
                      标记落实
                    </el-button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 快速添加沟通记录对话框 -->
    <el-dialog
      v-model="communicationDialogVisible"
      title="添加沟通记录"
      width="700px"
    >
      <el-form :model="communicationForm" label-width="100px">
        <el-form-item label="房间">
          <span>{{ currentRoom?.building_unit }} {{ currentRoom?.room_number }}号房</span>
        </el-form-item>
        <el-form-item label="沟通内容" required>
          <el-input
            v-model="communicationForm.content"
            type="textarea"
            rows="4"
            placeholder="请输入沟通内容"
          />
        </el-form-item>
        <el-form-item label="沟通时间" required>
          <el-date-picker
            v-model="communicationForm.communication_time"
            type="date"
            placeholder="请选择沟通时间"
            format="YYYY/MM/DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="收房意愿" required>
          <el-select 
            v-model="communicationForm.feedback" 
            placeholder="请选择收房意愿"
            style="width: 100%"
          >
            <el-option label="高" value="高" />
            <el-option label="低" value="低" />
          </el-select>
        </el-form-item>
        <el-form-item label="客户描摹">
          <el-input
            v-model="communicationForm.customer_description"
            type="textarea"
            rows="3"
            placeholder="请输入客户描摹（选填）"
          />
        </el-form-item>
        <el-form-item label="沟通截图">
          <el-upload
            ref="uploadRef"
            action=""
            :http-request="handleImageUpload"
            :before-upload="beforeImageUpload"
            :on-success="handleUploadSuccess"
            :on-error="handleUploadError"
            :show-file-list="false"
            accept="image/*"
            :loading="uploadLoading"
          >
            <el-button type="primary" :loading="uploadLoading">
              <el-icon><Upload /></el-icon>
              上传图片
            </el-button>
            <template #tip>
              <div class="el-upload__tip">
                只能上传jpg/png文件，且不超过2MB
              </div>
            </template>
          </el-upload>
          
          <!-- 图片预览 -->
          <div v-if="communicationForm.image" class="image-preview-container">
            <div class="image-wrapper">
              <el-image
                :src="`http://localhost:8000/uploads/${communicationForm.image}`"
                style="width: 120px; height: 90px"
                fit="cover"
                :preview-src-list="[`http://localhost:8000/uploads/${communicationForm.image}`]"
                class="preview-image"
              />
            </div>
            <div class="image-actions">
              <el-button
                type="danger"
                size="small"
                :icon="Delete"
                @click="removeImage"
              >
                删除图片
              </el-button>
            </div>
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="communicationDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveCommunication">保存</el-button>
      </template>
    </el-dialog>

    <!-- 添加质量问题对话框 -->
    <el-dialog
      v-model="qualityIssueDialogVisible"
      title="记录质量问题"
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
      </el-form>
      
      <template #footer>
        <el-button @click="qualityIssueDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveQualityIssue">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading, ChatLineSquare, Warning, Select, Plus, Refresh, Upload, Delete } from '@element-plus/icons-vue'
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
const communicationDialogVisible = ref(false)
const qualityIssueDialogVisible = ref(false)

// 图片上传相关
const uploadLoading = ref(false)

// 表单数据
const communicationForm = ref({
  content: '',
  feedback: '',
  customer_description: '',
  image: ''
})

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

// 打开沟通记录对话框
const openCommunicationDialog = () => {
  // 设置默认沟通时间为今天日期
  const today = new Date().toISOString().split('T')[0]
  communicationForm.value = {
    content: '',
    communication_time: today,
    feedback: '',
    customer_description: '',
    image: ''
  }
  communicationDialogVisible.value = true
}

// 保存沟通记录
const saveCommunication = async () => {
  if (!communicationForm.value.content.trim()) {
    ElMessage.error('请输入沟通内容')
    return
  }
  
  if (!communicationForm.value.communication_time) {
    ElMessage.error('请选择沟通时间')
    return
  }
  
  if (!communicationForm.value.feedback) {
    ElMessage.error('请选择收房意愿')
    return
  }
  
  try {
    // 格式化日期为ISO格式
    const communicationTime = communicationForm.value.communication_time ? 
      new Date(communicationForm.value.communication_time + 'T00:00:00').toISOString() : null
    
    await api.post('/communications/', {
      room_id: selectedRoomId.value,
      content: communicationForm.value.content,
      communication_time: communicationTime,
      feedback: communicationForm.value.feedback,
      customer_description: communicationForm.value.customer_description,
      image: communicationForm.value.image || null
    })
    
    ElMessage.success('沟通记录保存成功')
    communicationDialogVisible.value = false
    
    // 刷新当前房间数据和汇总信息
    await fetchRoomDetails(selectedRoomId.value)
    await fetchAssignedRooms()
    // 更新当前房间的统计信息
    const updatedRoom = assignedRooms.value.find(r => r.id === selectedRoomId.value)
    if (updatedRoom) {
      currentRoom.value = updatedRoom
    }
  } catch (error) {
    console.error('保存沟通记录失败:', error)
    ElMessage.error('保存沟通记录失败')
  }
}

// 图片上传相关方法
const beforeImageUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isImage) {
    ElMessage.error('只能上传图片文件!')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2MB!')
    return false
  }
  return true
}

const handleImageUpload = async (options) => {
  const { file } = options
  const formData = new FormData()
  formData.append('file', file)
  
  try {
    uploadLoading.value = true
    const response = await api.post('/upload-image/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    communicationForm.value.image = response.data.filename
    ElMessage.success('图片上传成功')
  } catch (error) {
    console.error('图片上传失败:', error)
    ElMessage.error('图片上传失败')
  } finally {
    uploadLoading.value = false
  }
}

const handleUploadSuccess = () => {
  // 成功回调已在handleImageUpload中处理
}

const handleUploadError = () => {
  ElMessage.error('图片上传失败')
  uploadLoading.value = false
}

const removeImage = () => {
  communicationForm.value.image = ''
  ElMessage.success('图片已删除')
}

// 打开质量问题对话框
const openQualityIssueDialog = () => {
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
    ElMessage.error('请选择录入时间')
    return
  }
  
  try {
    // 格式化日期为 YYYY-MM-DD HH:MM:SS 格式
    const recordDate = qualityIssueForm.value.record_date ? 
      new Date(qualityIssueForm.value.record_date + 'T00:00:00').toISOString() : null
    
    await api.post('/quality-issues/', {
      room_id: selectedRoomId.value,
      description: qualityIssueForm.value.description,
      issue_type: qualityIssueForm.value.issue_type,
      record_date: recordDate,
      // 这里需要处理图片上传，暂时先不上传图片
    })
    
    ElMessage.success('质量问题记录成功')
    qualityIssueDialogVisible.value = false
    
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
    ElMessage.error('保存质量问题失败')
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

// 标记沟通记录为已落实
const markImplemented = async (comm) => {
  try {
    await ElMessageBox.confirm(
      '确认标记此沟通记录为已落实吗？',
      '落实状态确认',
      {
        confirmButtonText: '确认落实',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await api.put(`/communications/${comm.id}`, {
      is_implemented: true
    })
    
    ElMessage.success('沟通记录标记落实成功')
    
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
      console.error('标记落实失败:', error)
      ElMessage.error('标记落实失败')
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

// 更新交付状态
const updateDeliveryStatus = async (newStatus) => {
  try {
    await api.put(`/rooms/${selectedRoomId.value}/delivery-status`, null, {
      params: { delivery_status: newStatus }
    })
    ElMessage.success('交付状态更新成功')
    // 更新本地状态
    if (currentRoom.value) {
      currentRoom.value.delivery_status = newStatus
    }
    // 更新房间列表中的状态
    const roomIndex = assignedRooms.value.findIndex(r => r.id === selectedRoomId.value)
    if (roomIndex !== -1) {
      assignedRooms.value[roomIndex].delivery_status = newStatus
    }
  } catch (error) {
    console.error('更新交付状态失败:', error)
    ElMessage.error('更新交付状态失败')
    // 恢复原状态
    if (currentRoom.value) {
      const originalRoom = assignedRooms.value.find(r => r.id === selectedRoomId.value)
      if (originalRoom) {
        currentRoom.value.delivery_status = originalRoom.delivery_status
      }
    }
  }
}

// 更新签约状态
const updateContractStatus = async (newStatus) => {
  try {
    await api.put(`/rooms/${selectedRoomId.value}/contract-status`, null, {
      params: { contract_status: newStatus }
    })
    ElMessage.success('签约状态更新成功')
    // 更新本地状态
    if (currentRoom.value) {
      currentRoom.value.contract_status = newStatus
    }
    // 更新房间列表中的状态
    const roomIndex = assignedRooms.value.findIndex(r => r.id === selectedRoomId.value)
    if (roomIndex !== -1) {
      assignedRooms.value[roomIndex].contract_status = newStatus
    }
  } catch (error) {
    console.error('更新签约状态失败:', error)
    ElMessage.error('更新签约状态失败')
    // 恢复原状态
    if (currentRoom.value) {
      const originalRoom = assignedRooms.value.find(r => r.id === selectedRoomId.value)
      if (originalRoom) {
        currentRoom.value.contract_status = originalRoom.contract_status
      }
    }
  }
}

onMounted(() => {
  console.log('客户大使界面加载，当前用户:', authStore.user)
  console.log('用户角色:', authStore.user?.role)
  console.log('是否为客户大使:', authStore.isCustomerAmbassador)
  console.log('认证token存在:', !!authStore.token)
  fetchAssignedRooms()
})
</script>

<style scoped>
.ambassador-dashboard {
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

.status-controls {
  display: flex;
  gap: 16px;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}

.control-group label {
  color: #606266;
  white-space: nowrap;
  font-weight: 500;
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

/* 图片预览样式 */
.image-preview-container {
  margin-top: 12px;
  padding: 12px;
  background-color: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.image-wrapper {
  display: flex;
  justify-content: center;
  margin-bottom: 8px;
}

.preview-image {
  border-radius: 6px;
  border: 1px solid #dcdfe6;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.preview-image:hover {
  border-color: #409eff;
  box-shadow: 0 4px 8px rgba(64, 158, 255, 0.2);
}

.image-actions {
  display: flex;
  justify-content: center;
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
  
  .status-controls {
    flex-direction: column;
    gap: 8px;
  }
  
  .control-group {
    justify-content: space-between;
  }
}
</style>