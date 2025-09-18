<template>
  <div class="admin-summary">
    <div class="header">
      <h3>数据汇总</h3>

      <!-- 导出功能区域 -->
      <div class="export-sections-container">
        <!-- 房间信息导出区域 -->
        <div class="export-section room-export">
          <div class="section-title">
            <el-icon><House /></el-icon>
            <span>房间信息导出</span>
          </div>
          <div class="filter-content">
            <div class="filter-row">
              <el-select v-model="selectedBuilding" placeholder="选择楼栋" clearable @change="onFilterChange" size="small">
                <el-option label="全部" value="" />
                <el-option label="3单元" value="3单元" />
                <el-option label="4单元" value="4单元" />
              </el-select>

              <el-select v-model="selectedStatus" placeholder="整改状态" clearable @change="onFilterChange" size="small">
                <el-option label="全部" value="" />
                <el-option label="整改中" value="整改中" />
                <el-option label="闭户" value="闭户" />
              </el-select>

              <el-select v-model="selectedDelivery" placeholder="交付状态" clearable @change="onFilterChange" size="small">
                <el-option label="全部" value="" />
                <el-option label="待交付" value="待交付" />
                <el-option label="已交付" value="已交付" />
              </el-select>
            </div>
            <div class="filter-row">
              <el-select v-model="selectedContract" placeholder="签约状态" clearable @change="onFilterChange" size="small">
                <el-option label="全部" value="" />
                <el-option label="待签约" value="待签约" />
                <el-option label="已签约" value="已签约" />
              </el-select>

              <el-select v-model="selectedIssueFilter" placeholder="问题筛选" clearable @change="onFilterChange" size="small">
                <el-option label="全部" value="" />
                <el-option label="有待验收" value="has_issues" />
                <el-option label="无问题" value="no_issues" />
              </el-select>

              <el-select v-model="selectedLetterFilter" placeholder="信件状态" clearable @change="onFilterChange" size="small">
                <el-option label="全部" value="" />
                <el-option label="无" value="无" />
                <el-option label="ZX" value="ZX" />
                <el-option label="SX" value="SX" />
                <el-option label="ZX+SX" value="ZX+SX" />
              </el-select>
            </div>
          </div>
        </div>

        <!-- 质量问题导出区域 -->
        <div class="export-section quality-export">
          <div class="section-title">
            <el-icon><Tools /></el-icon>
            <span>质量问题导出</span>
          </div>
          <div class="filter-content">
            <div class="filter-row">
              <el-select v-model="qualityExportBuilding" placeholder="选择楼栋" clearable size="small">
                <el-option label="全部" value="" />
                <el-option label="3单元" value="3单元" />
                <el-option label="4单元" value="4单元" />
              </el-select>

              <el-select v-model="qualityExportStatus" placeholder="问题状态" clearable size="small">
                <el-option label="全部" value="all" />
                <el-option label="待验收" value="pending" />
                <el-option label="已验收" value="completed" />
              </el-select>

              <el-select v-model="qualityExportType" placeholder="问题类型" clearable size="small">
                <el-option label="全部" value="" />
                <el-option label="质量瑕疵" value="质量瑕疵" />
                <el-option label="材料备货" value="材料备货" />
              </el-select>
            </div>
            <div class="filter-row">
              <!-- 空的第二行，保持与房间信息导出对齐 -->
            </div>
          </div>
        </div>
      </div>

      <!-- 统一的导出按钮区域 -->
      <div class="export-buttons-container">
        <div class="export-button-section">
          <el-button type="success" @click="exportData" :loading="loading" size="default">
            <el-icon><House /></el-icon>
            导出房间信息Excel
          </el-button>
        </div>
        <div class="export-button-section">
          <el-button type="success" @click="exportQualityIssues" :loading="qualityExportLoading" size="default">
            <el-icon><Tools /></el-icon>
            导出质量问题Excel
          </el-button>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards-container">
      <div class="stats-cards">
        <div v-for="(stat, key) in statusStats" :key="key" class="stat-card-wrapper">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-number">{{ stat.count }}</div>
              <div class="stat-label">{{ stat.label }}</div>
            </div>
            <div class="stat-icon" :class="stat.iconClass">
              <el-icon>
                <component :is="stat.icon" />
              </el-icon>
            </div>
          </el-card>
        </div>
      </div>
    </div>

    <!-- 房间详细列表 -->
    <el-card class="room-details">
      <template #header>
        <div class="card-header">
          <span>房间详细信息</span>
          <span class="total-count">显示 {{ paginatedRooms.length }} / 共 {{ filteredRooms.length }} 条记录（总计{{ summaryData.total_rooms }}间）</span>
        </div>
      </template>
      
      <el-table :data="paginatedRooms" v-loading="loading" max-height="500">
        <el-table-column prop="building_unit" label="楼栋" width="80" />
        <el-table-column prop="room_number" label="房间号" width="80">
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

        <!-- 工程师信息列 -->
        <el-table-column label="客户大使" width="120">
          <template #default="scope">
            <span>{{ getUserByRole(scope.row.assigned_users, 'customer_ambassador')?.name || '未分配' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="项目工程师" width="120">
          <template #default="scope">
            <span>{{ getUserByRole(scope.row.assigned_users, 'project_engineer')?.name || '未分配' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="维修工程师" width="120">
          <template #default="scope">
            <span>{{ getUserByRole(scope.row.assigned_users, 'maintenance_engineer')?.name || '未分配' }}</span>
          </template>
        </el-table-column>

        <!-- 三类状态列 -->
        <el-table-column prop="status" label="整改状态" width="90">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)" size="small">
              {{ scope.row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="delivery_status" label="交付状态" width="90">
          <template #default="scope">
            <el-tag :type="scope.row.delivery_status === '已交付' ? 'success' : 'info'" size="small">
              {{ scope.row.delivery_status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="contract_status" label="签约状态" width="90">
          <template #default="scope">
            <el-tag :type="scope.row.contract_status === '已签约' ? 'success' : 'info'" size="small">
              {{ scope.row.contract_status }}
            </el-tag>
          </template>
        </el-table-column>
        
        <!-- 待验收相关列 -->
        <el-table-column label="待验收" width="70" align="center">
          <template #default="scope">
            <span>{{ scope.row.pending_issues_count || 0 }}</span>
          </template>
        </el-table-column>
        
        
        <!-- 客户大使录入字段 -->
        <el-table-column prop="expected_delivery_date" label="预计交付时间" width="120">
          <template #default="scope">
            {{ scope.row.expected_delivery_date ? formatDate(scope.row.expected_delivery_date) : '' }}
          </template>
        </el-table-column>
        <el-table-column prop="letter_status" label="信件状态" width="90">
          <template #default="scope">
            <el-tag 
              v-if="scope.row.letter_status && scope.row.letter_status !== '无'" 
              :type="getLetterStatusType(scope.row.letter_status)" 
              size="small"
              :style="getLetterStatusStyle(scope.row.letter_status)"
            >
              {{ scope.row.letter_status }}
            </el-tag>
            <span v-else>{{ scope.row.letter_status || '无' }}</span>
          </template>
        </el-table-column>
        
        
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <div style="display: flex; gap: 8px;">
              <el-button type="primary" size="small" @click="viewRoom(scope.row)" style="white-space: nowrap; flex: 1;">
                查看详情
              </el-button>
              <el-button type="warning" size="small" @click="resetRoom(scope.row)" style="white-space: nowrap; flex: 1;">
                重置信息
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[20, 50, 100, 200]"
          :total="filteredRooms.length"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import * as API from '../api/index.js'
const { adminAPI } = API
import { ElMessage, ElMessageBox } from 'element-plus'
import { House, Tools, CircleCheck, SuccessFilled, Download } from '@element-plus/icons-vue'

const router = useRouter()
const loading = ref(false)
const summaryData = ref({
  total_rooms: 0,
  status_summary: {},
  delivery_summary: {},
  contract_summary: {},
  rooms: []
})

// 筛选条件
const selectedBuilding = ref('')  // 默认显示全部楼栋
const selectedStatus = ref('')
const selectedDelivery = ref('')
const selectedContract = ref('')
const selectedIssueFilter = ref('')
const selectedLetterFilter = ref('')

// 质量问题导出相关
const qualityExportBuilding = ref('')
const qualityExportStatus = ref('all')
const qualityExportType = ref('')
const qualityExportLoading = ref(false)

// 分页相关
const currentPage = ref(1)
const pageSize = ref(20)

// 动态统计当前筛选结果
const statusStats = computed(() => {
  const filtered = filteredRooms.value
  
  return {
    total: {
      count: filtered.length,
      label: '当前显示',
      icon: House,
      iconClass: 'total'
    },
    pending: {
      count: filtered.filter(room => room.status === '整改中').length,
      label: '整改中',
      icon: Tools,
      iconClass: 'pending'
    },
    closed: {
      count: filtered.filter(room => room.status === '闭户').length,
      label: '闭户',
      icon: CircleCheck,
      iconClass: 'closed'
    },
    delivered: {
      count: filtered.filter(room => room.delivery_status === '已交付').length,
      label: '已交付',
      icon: SuccessFilled,
      iconClass: 'delivered'
    },
    signed: {
      count: filtered.filter(room => room.contract_status === '已签约').length,
      label: '已签约',
      icon: CircleCheck,
      iconClass: 'signed'
    }
  }
})

// 多维度筛选逻辑
const filteredRooms = computed(() => {
  return summaryData.value.rooms.filter(room => {
    // 楼栋筛选
    if (selectedBuilding.value && room.building_unit !== selectedBuilding.value) {
      return false
    }
    
    // 整改状态筛选
    if (selectedStatus.value && room.status !== selectedStatus.value) {
      return false
    }
    
    // 交付状态筛选
    if (selectedDelivery.value && room.delivery_status !== selectedDelivery.value) {
      return false
    }
    
    // 签约状态筛选
    if (selectedContract.value && room.contract_status !== selectedContract.value) {
      return false
    }
    
    // 问题筛选
    if (selectedIssueFilter.value) {
      const hasIssues = (room.pending_issues_count || 0) > 0
      if (selectedIssueFilter.value === 'has_issues' && !hasIssues) return false
      if (selectedIssueFilter.value === 'no_issues' && hasIssues) return false
    }
    
    
    // 信件状态筛选
    if (selectedLetterFilter.value) {
      const letterStatus = room.letter_status || '无'
      if (letterStatus !== selectedLetterFilter.value) return false
    }
    
    
    return true
  })
})

// 分页数据
const paginatedRooms = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredRooms.value.slice(start, end)
})

const fetchSummary = async () => {
  loading.value = true
  try {
    // 获取所有数据，在前端做筛选
    const response = await adminAPI.getSummary(null)
    summaryData.value = response.data
  } catch (error) {
    ElMessage.error('获取氇总数据失败')
  } finally {
    loading.value = false
  }
}

const onFilterChange = () => {
  // 筛选条件改变时重置到第一页
  currentPage.value = 1
}

const refreshData = () => {
  fetchSummary()
}

const handleSizeChange = (newSize) => {
  pageSize.value = newSize
  currentPage.value = 1
}

const handleCurrentChange = (newPage) => {
  currentPage.value = newPage
}

const exportData = async () => {
  try {
    loading.value = true

    // 调试信息
    console.log('🏠 房间信息导出 - 开始执行')

    // 构建查询参数对象
    const params = {}
    if (selectedBuilding.value) params.building_unit = selectedBuilding.value
    if (selectedStatus.value) params.status = selectedStatus.value
    if (selectedDelivery.value) params.delivery_status = selectedDelivery.value
    if (selectedContract.value) params.contract_status = selectedContract.value
    if (selectedIssueFilter.value) params.issue_filter = selectedIssueFilter.value
    if (selectedLetterFilter.value) params.letter_filter = selectedLetterFilter.value

    console.log('🏠 房间信息导出 - 参数:', params)
    console.log('🏠 房间信息导出 - 调用API: /admin/export')

    // 调用后端导出接口
    const response = await adminAPI.exportExcel(params)
    
    // 处理文件下载
    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    
    // 从响应头获取文件名，如果没有则使用默认名称
    const contentDisposition = response.headers['content-disposition']
    let filename = `ZWY项目汇总_${new Date().toLocaleDateString().replace(/\//g, '')}.xlsx`
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename=['"]?([^'";]*)['"]?/)
      if (filenameMatch) {
        filename = filenameMatch[1]
      }
    }
    
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('Excel文件导出成功')
  } catch (error) {
    console.error('导出Excel失败:', error)
    ElMessage.error('导出Excel失败：' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

// 导出质量问题
const exportQualityIssues = async () => {
  try {
    qualityExportLoading.value = true

    // 调试信息
    console.log('🔧 质量问题导出 - 开始执行')

    // 首先获取符合条件的所有房间ID
    const params = {}
    if (qualityExportBuilding.value) {
      params.building_unit = qualityExportBuilding.value
    }

    // 获取汇总数据
    const summaryResponse = await adminAPI.getSummary(qualityExportBuilding.value)
    const allRooms = summaryResponse.data.rooms || []

    if (allRooms.length === 0) {
      ElMessage.warning('未找到符合条件的房间数据')
      return
    }

    // 获取所有房间ID
    const roomIds = allRooms.map(room => room.id).join(',')

    // 构建导出参数
    const exportParams = new URLSearchParams({
      room_ids: roomIds,
      status_filter: qualityExportStatus.value
    })

    // 如果选择了问题类型，需要在后端进行筛选（这里需要修改后端API支持）
    if (qualityExportType.value) {
      exportParams.append('issue_type', qualityExportType.value)
    }

    // 调用导出API
    const response = await fetch(`/api/export-quality-issues?${exportParams}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })

    if (!response.ok) {
      throw new Error('导出失败')
    }

    // 处理文件下载
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url

    // 生成文件名
    const buildingText = qualityExportBuilding.value || '全部'
    const statusText = qualityExportStatus.value === 'all' ? '全部' :
                      qualityExportStatus.value === 'pending' ? '待验收' : '已验收'
    const typeText = qualityExportType.value || '全部'
    const dateStr = new Date().toLocaleDateString().replace(/\//g, '')
    const filename = `质量问题清单_${buildingText}_${statusText}_${typeText}_${dateStr}.xlsx`

    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success('质量问题Excel导出成功')
  } catch (error) {
    console.error('导出质量问题Excel失败:', error)
    ElMessage.error('导出质量问题Excel失败：' + (error.message || '未知错误'))
  } finally {
    qualityExportLoading.value = false
  }
}


const viewRoom = (room) => {
  // 保存当前页码到查询参数，方便返回时恢复
  router.push({
    path: `/dashboard/rooms/${room.id}`,
    query: {
      from: 'admin-summary',
      returnPage: currentPage.value,
      returnPageSize: pageSize.value
    }
  })
}

const resetRoom = async (room) => {
  try {
    await ElMessageBox.confirm(
      `确定要重置房间 ${room.building_unit}-${room.room_number} 吗？此操作将清除所有质量问题和状态信息，但保留户主信息。`,
      '重置房间确认',
      {
        confirmButtonText: '确定重置',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--warning',
        dangerouslyUseHTMLString: false
      }
    )
    
    loading.value = true
    await adminAPI.resetRoom(room.id)
    ElMessage.success(`房间 ${room.building_unit}-${room.room_number} 重置成功`)
    await fetchSummary()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('重置房间失败：' + (error.response?.data?.detail || error.message))
    }
  } finally {
    loading.value = false
  }
}

const getRoleName = (role) => {
  const roleMap = {
    customer_ambassador: '客户大使',
    project_engineer: '项目工程师',
    maintenance_engineer: '维修工程师'
  }
  return roleMap[role] || role
}

const getUserByRole = (assignedUsers, targetRole) => {
  if (!assignedUsers || assignedUsers.length === 0) return null
  return assignedUsers.find(user => user.role === targetRole) || null
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

const getLetterStatusType = (status) => {
  // 为了确保样式正确应用，这里返回基础类型
  return 'info'
}

const getLetterStatusStyle = (status) => {
  // 移除所有信件状态的背景色样式，保持简洁风格
  return ''
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('zh-CN')
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


onMounted(() => {
  // 检查是否有返回页码参数，如果有则恢复
  const returnPage = router.currentRoute.value.query.returnPage
  const returnPageSize = router.currentRoute.value.query.returnPageSize

  if (returnPage && !isNaN(parseInt(returnPage))) {
    currentPage.value = parseInt(returnPage)
  }

  if (returnPageSize && !isNaN(parseInt(returnPageSize))) {
    pageSize.value = parseInt(returnPageSize)
  }

  fetchSummary()
})
</script>

<style scoped>
.admin-summary {
  padding: 20px;
}

.header {
  margin-bottom: 20px;
}

.header h3 {
  margin-bottom: 20px;
  text-align: center;
  color: #303133;
}

/* 导出区域容器 */
.export-sections-container {
  display: flex;
  gap: 20px;
  justify-content: center;
  margin-bottom: 20px;
}

/* 导出区域样式 */
.export-section {
  flex: 1;
  max-width: 48%;
  min-height: 200px;
  padding: 20px;
  border-radius: 12px;
  border: 2px solid #e4e7ed;
  transition: all 0.3s ease;
}

.export-section:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

.export-section.room-export {
  background: linear-gradient(135deg, #f0f8ff 0%, #e6f3ff 100%);
  border-left: 4px solid #409eff;
  border-color: #409eff;
}

.export-section.quality-export {
  background: linear-gradient(135deg, #f0f9f0 0%, #e6f7e6 100%);
  border-left: 4px solid #67c23a;
  border-color: #67c23a;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  font-size: 18px;
  font-weight: 700;
  color: #303133;
  padding-bottom: 8px;
  border-bottom: 1px solid #e4e7ed;
}

.filter-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 80px; /* 确保两个区域高度一致 */
}

/* 统一的导出按钮区域 */
.export-buttons-container {
  display: flex;
  gap: 20px;
  justify-content: center;
  margin: 20px 0;
}

.export-button-section {
  flex: 1;
  max-width: 48%;
  display: flex;
  justify-content: center;
}

.filters {
  margin-bottom: 20px;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: center;
}

.filter-row .el-select {
  width: 110px;
}

/* 统计卡片容器 */
.stats-cards-container {
  margin: 30px 0;
  display: flex;
  justify-content: center;
}

.stats-cards {
  display: flex;
  gap: 20px;
  justify-content: center;
  align-items: center;
  flex-wrap: wrap;
  max-width: 1000px; /* 限制最大宽度 */
}

.stat-card-wrapper {
  flex: 1;
  min-width: 160px;
  max-width: 200px;
}

.stat-card {
  position: relative;
  overflow: hidden;
}

.stat-content {
  padding: 20px;
}

.stat-number {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.stat-icon {
  position: absolute;
  right: 20px;
  top: 20px;
  font-size: 40px;
  opacity: 0.3;
}

.stat-icon.total { color: #409EFF; }
.stat-icon.pending { color: #E6A23C; }
.stat-icon.closed { color: #909399; }
.stat-icon.delivered { color: #67C23A; }
.stat-icon.signed { color: #67C23A; }

.room-details {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.total-count {
  color: #909399;
  font-size: 14px;
}

.issue-count {
  font-size: 12px;
  white-space: nowrap;
}

.user-tag {
  margin: 2px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  padding: 15px 0;
  border-top: 1px solid #ebeef5;
}

</style>