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
              <h4>{{ room.building_unit }} {{ room.room_number }}号房</h4>
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
        <el-card class="room-info-card">
          <template #header>
            <div class="room-info-header">
              <h4>{{ currentRoom.building_unit }} {{ currentRoom.room_number }}号房 - 详细信息</h4>
              <el-tag :type="getStatusType(currentRoom.status)">{{ currentRoom.status }}</el-tag>
            </div>
          </template>
          
          <div class="room-info-grid">
            <div class="info-item">
              <label>交付状态：</label>
              <el-tag :type="currentRoom.delivery_status === '已交付' ? 'success' : 'warning'" size="small">
                {{ currentRoom.delivery_status }}
              </el-tag>
            </div>
            <div class="info-item">
              <label>签约状态：</label>
              <el-tag :type="currentRoom.contract_status === '已签约' ? 'success' : 'warning'" size="small">
                {{ currentRoom.contract_status }}
              </el-tag>
            </div>
            <div class="info-item">
              <label>预计交付时间：</label>
              <span>{{ currentRoom.expected_delivery_date ? formatDate(currentRoom.expected_delivery_date) : '未设置' }}</span>
            </div>
            <div class="info-item">
              <label>最后更新：</label>
              <span>{{ formatDate(currentRoom.updated_at) }}</span>
            </div>
          </div>

          <div class="stats-row">
            <div class="stat-item">
              <el-statistic title="质量问题总数" :value="currentRoom.quality_issue_count || 0" />
            </div>
            <div class="stat-item">
              <el-statistic title="待验收" :value="currentRoom.pending_verification_count || 0" />
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
                    <span>{{ getUserDisplayName(issue) }}</span>
                  </div>
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
                  <el-button 
                    v-if="issue.status === '待验收'" 
                    type="success" 
                    size="small"
                    @click="acceptIssue(issue)"
                  >
                    验收
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading, Tools, Plus, Upload, Close } from '@element-plus/icons-vue'
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
    // 按照录入时间和创建时间降序排序，新问题在前
    qualityIssues.value = issuesResponse.data.sort((a, b) => {
      const dateA = new Date(a.record_date || a.created_at)
      const dateB = new Date(b.record_date || b.created_at)
      return dateB - dateA
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
  return status === '已验收' ? 'success' : 'warning'
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
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
    const recordDate = qualityIssueForm.value.record_date ? 
      new Date(qualityIssueForm.value.record_date + 'T00:00:00').toISOString() : null
    
    const data = {
      room_id: selectedRoomId.value,
      description: qualityIssueForm.value.description,
      issue_type: qualityIssueForm.value.issue_type,
      record_date: recordDate,
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

// 验收质量问题
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
    if (error !== 'cancel') {
      console.error('验收质量问题失败:', error)
      ElMessage.error('验收质量问题失败')
    }
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
  height: calc(100vh - 150px);
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

.stat-item {
  text-align: center;
}

.room-details {
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow-y: auto;
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
  max-height: 500px;
  overflow-y: auto;
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
</style>