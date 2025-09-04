<template>
  <div class="room-detail" v-loading="loading">
    <div class="header">
      <el-button @click="$router.go(-1)" type="text">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <h3 class="room-title">{{ roomInfo?.building_unit }} {{ roomInfo?.room_number }}号房</h3>
      <div class="status">
        <el-tag :type="getStatusType(roomInfo?.status)">{{ roomInfo?.status }}</el-tag>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="room-tabs">
      <el-tab-pane label="质量问题" name="issues">
        <div class="tab-header">
          <h4>质量问题 ({{ qualityIssues.length }})</h4>
          <el-button 
            v-if="canAddIssue" 
            type="primary" 
            @click="showAddIssueDialog = true"
          >
            添加质量问题
          </el-button>
        </div>
        
        <el-table :data="qualityIssues">
          <el-table-column label="填写人" width="120">
            <template #default="scope">
              {{ getUserDisplayName(scope.row) }}
            </template>
          </el-table-column>
          <el-table-column prop="description" label="问题描述" />
          <el-table-column prop="issue_type" label="问题类型" width="100" />
          <el-table-column label="录入时间" width="180">
            <template #default="scope">
              {{ formatDate(scope.row.record_date || scope.row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="scope">
              <el-tag :type="scope.row.status === '已验收' ? 'success' : 'warning'">
                {{ scope.row.status }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="客户沟通" name="communications">
        <div class="tab-header">
          <h4>客户沟通记录 ({{ communications.length }})</h4>
          <el-button 
            v-if="authStore.isCustomerAmbassador" 
            type="primary"
            @click="showAddCommDialog = true"
          >
            添加沟通记录
          </el-button>
        </div>
        
        <el-table :data="communications">
          <el-table-column prop="content" label="沟通内容" />
          <el-table-column label="核心诉求" width="100">
            <template #default="scope">
              <el-tag 
                v-if="scope.row.feedback" 
                :type="scope.row.feedback === '高' ? 'success' : 'danger'"
                size="small"
              >
                {{ scope.row.feedback }}
              </el-tag>
              <span v-else class="no-feedback">-</span>
            </template>
          </el-table-column>
          <el-table-column prop="customer_description" label="客户描摹" show-overflow-tooltip>
            <template #default="scope">
              <span v-if="scope.row.customer_description">{{ scope.row.customer_description }}</span>
              <span v-else class="no-description">-</span>
            </template>
          </el-table-column>
          <el-table-column label="沟通图片" width="100">
            <template #default="scope">
              <span v-if="scope.row.image">
                <el-image
                  :src="`http://localhost:8000/uploads/${scope.row.image}`"
                  style="width: 60px; height: 60px"
                  fit="cover"
                  :preview-src-list="[`http://localhost:8000/uploads/${scope.row.image}`]"
                  class="comm-image"
                />
              </span>
              <span v-else class="no-image">无图片</span>
            </template>
          </el-table-column>
          <el-table-column label="沟通时间" width="120">
            <template #default="scope">
              {{ scope.row.communication_time ? formatDate(scope.row.communication_time) : '-' }}
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="客户信息" name="customer">
        <div class="customer-info-container" v-if="customerInfo">
          <div class="customer-info-grid">
            <div class="info-item">
              <label>姓名：</label>
              <span>{{ customerInfo.name }}</span>
            </div>
            <div class="info-item">
              <label>性别：</label>
              <span>{{ customerInfo.gender }}</span>
            </div>
            <div class="info-item">
              <label>客户分级：</label>
              <el-tag :type="getCustomerLevelType(customerInfo.customer_level)" size="small">
                {{ customerInfo.customer_level }}
              </el-tag>
            </div>
            <div class="info-item">
              <label>身份证号：</label>
              <span>{{ customerInfo.id_card }}</span>
            </div>
            <div class="info-item">
              <label>手机号：</label>
              <span>{{ customerInfo.phone }}</span>
            </div>
            <div class="info-item">
              <label>工作单位：</label>
              <span>{{ customerInfo.work_unit || '-' }}</span>
            </div>
          </div>
        </div>
        <div v-else class="no-customer-info">
          <el-empty description="暂无客户信息" />
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 添加质量问题对话框 -->
    <el-dialog v-model="showAddIssueDialog" title="添加质量问题" width="600px">
      <el-form :model="issueForm" label-width="100px">
        <el-form-item label="问题描述" required>
          <el-input 
            v-model="issueForm.description" 
            type="textarea" 
            rows="4"
            placeholder="请详细描述质量问题..."
          />
        </el-form-item>
        <el-form-item label="问题图片">
          <el-upload
            v-model:file-list="issueForm.images"
            action="/api/upload-image/"
            :headers="{ Authorization: `Bearer ${authStore.token}` }"
            :on-success="handleUploadSuccess"
            :on-error="handleUploadError"
            accept="image/*"
            list-type="picture-card"
            multiple
          >
            <el-icon><Plus /></el-icon>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddIssueDialog = false">取消</el-button>
        <el-button type="primary" @click="submitIssue">提交</el-button>
      </template>
    </el-dialog>

    <!-- 添加客户沟通对话框 -->
    <el-dialog v-model="showAddCommDialog" title="添加沟通记录" width="600px">
      <el-form :model="commForm" label-width="100px">
        <el-form-item label="沟通内容" required>
          <el-input 
            v-model="commForm.content" 
            type="textarea" 
            rows="4"
            placeholder="请输入沟通内容..."
          />
        </el-form-item>
        <el-form-item label="客户反馈">
          <el-input 
            v-model="commForm.feedback" 
            type="textarea" 
            rows="3"
            placeholder="请输入客户反馈..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddCommDialog = false">取消</el-button>
        <el-button type="primary" @click="submitComm">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { roomAPI, qualityIssueAPI, communicationAPI, customerAPI } from '../api/index.js'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Plus } from '@element-plus/icons-vue'

const route = useRoute()
const authStore = useAuthStore()
const loading = ref(false)
const activeTab = ref('issues')

const roomInfo = ref(null)
const qualityIssues = ref([])
const communications = ref([])
const customerInfo = ref(null)

const showAddIssueDialog = ref(false)
const showAddCommDialog = ref(false)

const issueForm = ref({
  description: '',
  images: [],
  uploadedImages: []
})

const commForm = ref({
  content: '',
  feedback: ''
})

const canAddIssue = computed(() => {
  const role = authStore.user?.role
  return ['project_engineer', 'maintenance_engineer', 'customer_ambassador'].includes(role)
})

const fetchRoomData = async () => {
  loading.value = true
  try {
    const roomId = route.params.id
    const promises = [
      roomAPI.getRooms(),
      qualityIssueAPI.getQualityIssues(roomId),
      communicationAPI.getCommunications(roomId)
    ]
    
    // 只有管理员和客户大使可以看到客户信息标签
    if (authStore.user?.role === 'admin' || authStore.user?.role === 'customer_ambassador') {
      promises.push(customerAPI.getCustomerByRoom(roomId))
    }
    
    const responses = await Promise.all(promises)
    const [roomsRes, issuesRes, commsRes, customerRes] = responses
    
    roomInfo.value = roomsRes.data.find(r => r.id == roomId)
    qualityIssues.value = issuesRes.data
    communications.value = commsRes.data
    
    if (customerRes) {
      customerInfo.value = customerRes.data
    }
  } catch (error) {
    if (error.response?.status === 404 && error.config?.url?.includes('/customers/room/')) {
      // 客户信息不存在，这是正常情况
      customerInfo.value = null
    } else {
      ElMessage.error('获取房间数据失败')
    }
  } finally {
    loading.value = false
  }
}

const handleUploadSuccess = (response, file) => {
  issueForm.value.uploadedImages.push(response.url)
  ElMessage.success('图片上传成功')
}

const handleUploadError = () => {
  ElMessage.error('图片上传失败')
}

const submitIssue = async () => {
  if (!issueForm.value.description.trim()) {
    ElMessage.warning('请输入问题描述')
    return
  }
  
  try {
    await qualityIssueAPI.createQualityIssue({
      room_id: parseInt(route.params.id),
      description: issueForm.value.description,
      images: JSON.stringify(issueForm.value.uploadedImages)
    })
    
    ElMessage.success('质量问题添加成功')
    showAddIssueDialog.value = false
    issueForm.value = { description: '', images: [], uploadedImages: [] }
    fetchRoomData()
  } catch (error) {
    ElMessage.error('添加质量问题失败')
  }
}

const submitComm = async () => {
  if (!commForm.value.content.trim()) {
    ElMessage.warning('请输入沟通内容')
    return
  }
  
  try {
    await communicationAPI.createCommunication({
      room_id: parseInt(route.params.id),
      content: commForm.value.content,
      feedback: commForm.value.feedback
    })
    
    ElMessage.success('沟通记录添加成功')
    showAddCommDialog.value = false
    commForm.value = { content: '', feedback: '' }
    fetchRoomData()
  } catch (error) {
    ElMessage.error('添加沟通记录失败')
  }
}


const getUserDisplayName = (record) => {
  // 从后端返回的用户信息中获取用户名和角色
  if (record.user_name) {
    const roleText = getRoleText(record.user_role)
    return `${record.user_name}(${roleText})`
  }
  return '未知用户'
}

const getRoleText = (role) => {
  const roleMap = {
    'admin': '管理员',
    'customer_ambassador': '客户大使',
    'project_engineer': '项目工程师',
    'maintenance_engineer': '维修工程师'
  }
  return roleMap[role] || role
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

const getIssueImages = (imagesJson) => {
  if (!imagesJson) return []
  try {
    const images = JSON.parse(imagesJson)
    return images.map(img => img.startsWith('http') ? img : `/api${img}`)
  } catch {
    return []
  }
}

const previewImage = (src) => {
  window.open(src, '_blank')
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

const getCustomerLevelType = (level) => {
  const levelMap = {
    'A': 'success',
    'B': 'warning', 
    'C': 'danger'
  }
  return levelMap[level] || 'info'
}

onMounted(() => {
  fetchRoomData()
})
</script>

<style scoped>
.room-detail {
  padding: 20px;
}

.header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #ebeef5;
}

.room-title {
  flex: 1;
  white-space: nowrap;
  overflow: visible;
  text-overflow: unset;
  min-width: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.tab-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.room-tabs {
  margin-top: 20px;
}

.image-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.preview-img {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 4px;
  cursor: pointer;
  transition: transform 0.2s;
}

.preview-img:hover {
  transform: scale(1.1);
}

/* 沟通图片样式 */
.comm-image {
  border-radius: 6px;
  border: 1px solid #e4e7ed;
  cursor: pointer;
}

.comm-image:hover {
  border-color: #409eff;
}

.no-image {
  color: #909399;
  font-size: 12px;
}

.no-feedback,
.no-description {
  color: #c0c4cc;
  font-size: 12px;
}

.customer-info-container {
  padding: 20px;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #ebeef5;
}

.customer-info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
}

.info-item label {
  font-weight: 600;
  color: #606266;
  min-width: 80px;
  flex-shrink: 0;
}

.info-item span {
  color: #303133;
  word-break: break-word;
}

.no-customer-info {
  padding: 40px 0;
}
</style>