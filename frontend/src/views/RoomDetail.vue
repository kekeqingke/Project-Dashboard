<template>
  <div class="room-detail" v-loading="loading">
    <div class="header">
      <el-button @click="handleGoBack" type="text">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <h3 class="room-title" v-if="roomInfo">{{ roomInfo.building_unit }} {{ formatRoomNumber(roomInfo.room_number) }}号房</h3>
      <h3 class="room-title loading-title" v-else>加载中...</h3>
      <div class="header-actions">
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
          <el-table-column label="录入时间" width="120">
            <template #default="scope">
              {{ formatDateOnly(scope.row.record_date || scope.row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="状态" width="160">
            <template #default="scope">
              <div v-if="scope.row.status === '已验收'" class="status-with-time">
                <el-tag type="success">已验收</el-tag>
                <div class="acceptance-time" v-if="scope.row.accepted_at">
                  ({{ formatDateOnly(scope.row.accepted_at) }})
                </div>
              </div>
              <el-tag v-else type="warning">
                {{ scope.row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column v-if="isAdmin" label="操作" width="80">
            <template #default="scope">
              <el-button 
                type="danger" 
                size="small" 
                @click="handleDeleteIssue(scope.row)"
                :loading="scope.row.deleting"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
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

  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { roomAPI, qualityIssueAPI } from '../api/index.js'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Plus } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const activeTab = ref('issues')

const roomInfo = ref(null)
const qualityIssues = ref([])
const customerInfo = ref(null)

const showAddIssueDialog = ref(false)

const issueForm = ref({
  description: '',
  images: [],
  uploadedImages: []
})


const canAddIssue = computed(() => {
  const role = authStore.user?.role
  return ['project_engineer', 'maintenance_engineer', 'customer_ambassador'].includes(role)
})

const isAdmin = computed(() => {
  return authStore.user?.role === 'admin'
})

const fetchRoomData = async () => {
  const roomId = route.params.id
  if (!roomId) {
    ElMessage.error('房间ID无效')
    return
  }
  
  loading.value = true
  try {
    // 首先获取房间基本信息
    const roomResponse = await roomAPI.getRooms()
    roomInfo.value = roomResponse.data.find(r => r.id == roomId)
    
    if (!roomInfo.value) {
      throw new Error('房间不存在')
    }
    
    // 然后获取质量问题数据
    const issuesRes = await qualityIssueAPI.getQualityIssues(roomId)
    qualityIssues.value = issuesRes.data
  } catch (error) {
    ElMessage.error('获取房间数据失败: ' + (error.message || '未知错误'))
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

const handleDeleteIssue = async (issue) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除这条质量问题吗？\n问题描述：${issue.description}`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    // 设置删除中状态
    issue.deleting = true
    
    await qualityIssueAPI.deleteQualityIssue(issue.id)
    ElMessage.success('质量问题删除成功')
    fetchRoomData() // 重新获取数据
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除质量问题失败')
    }
  } finally {
    issue.deleting = false
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
  return new Date(dateString).toLocaleString('zh-CN', {
    timeZone: 'Asia/Shanghai'
  })
}

// 格式化日期 - 只显示年月日
const formatDateOnly = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN')
}

// 格式化房号，去掉前导零
const formatRoomNumber = (roomNumber) => {
  if (!roomNumber) return roomNumber
  // 将房号转为字符串，然后去掉前导零
  return parseInt(roomNumber).toString()
}

// 处理返回逻辑，根据来源页面进行不同的返回处理
const handleGoBack = () => {
  const fromPage = route.query.from
  const returnPage = route.query.returnPage
  const returnPageSize = route.query.returnPageSize
  const returnBuilding = route.query.returnBuilding
  const returnRoomSearch = route.query.returnRoomSearch
  const returnRole = route.query.returnRole
  const returnPerson = route.query.returnPerson

  if (fromPage === 'admin-summary') {
    // 来自数据汇总页面，返回到带有页码的汇总页面
    const query = {}
    if (returnPage) query.returnPage = returnPage
    if (returnPageSize) query.returnPageSize = returnPageSize

    router.push({
      path: '/dashboard/admin/summary',
      query: query
    })
  } else if (fromPage === 'room-list') {
    // 来自房间管理页面，返回到房间管理页面并恢复页码和筛选条件
    const query = {}
    if (returnPage) query.returnPage = returnPage
    if (returnPageSize) query.returnPageSize = returnPageSize
    if (returnBuilding) query.returnBuilding = returnBuilding
    if (returnRoomSearch) query.returnRoomSearch = returnRoomSearch
    if (returnRole) query.returnRole = returnRole
    if (returnPerson) query.returnPerson = returnPerson

    router.push({
      path: '/dashboard/rooms',
      query: query
    })
  } else {
    // 其他情况使用浏览器后退
    router.go(-1)
  }
}



onMounted(() => {
  fetchRoomData()
})

// 监听路由变化，处理同一组件内路由参数变化的情况
watch(() => route.params.id, (newId, oldId) => {
  if (newId && newId !== oldId) {
    // 重置数据
    roomInfo.value = null
    qualityIssues.value = []
    customerInfo.value = null
    // 重新获取数据
    fetchRoomData()
  }
}, { immediate: false })
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

.header-actions {
  display: flex;
  align-items: center;
}

.status-with-time {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.acceptance-time {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
  text-align: center;
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

.loading-title {
  color: #909399;
  font-style: italic;
}
</style>