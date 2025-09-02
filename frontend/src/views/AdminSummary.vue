<template>
  <div class="admin-summary">
    <div class="header">
      <h3>数据汇总</h3>
      <div class="filters">
        <div class="filter-row">
          <el-select v-model="selectedBuilding" placeholder="选择楼栋" clearable @change="onFilterChange" style="width: 120px">
            <el-option label="全部" value="" />
            <el-option label="3单元" value="3单元" />
            <el-option label="4单元" value="4单元" />
          </el-select>
          
          <el-select v-model="selectedStatus" placeholder="整改状态" clearable @change="onFilterChange" style="width: 120px">
            <el-option label="全部" value="" />
            <el-option label="整改中" value="整改中" />
            <el-option label="闭户" value="闭户" />
          </el-select>
          
          <el-select v-model="selectedDelivery" placeholder="交付状态" clearable @change="onFilterChange" style="width: 120px">
            <el-option label="全部" value="" />
            <el-option label="待交付" value="待交付" />
            <el-option label="已交付" value="已交付" />
          </el-select>
          
          <el-select v-model="selectedContract" placeholder="签约状态" clearable @change="onFilterChange" style="width: 120px">
            <el-option label="全部" value="" />
            <el-option label="待签约" value="待签约" />
            <el-option label="已签约" value="已签约" />
          </el-select>
          
          <el-select v-model="selectedIssueFilter" placeholder="问题筛选" clearable @change="onFilterChange" style="width: 120px">
            <el-option label="全部" value="" />
            <el-option label="有待验收" value="has_issues" />
            <el-option label="无问题" value="no_issues" />
          </el-select>
          
          <el-select v-model="selectedCommFilter" placeholder="沟通筛选" clearable @change="onFilterChange" style="width: 120px">
            <el-option label="全部" value="" />
            <el-option label="有待落实" value="has_comms" />
            <el-option label="无待落实" value="no_comms" />
          </el-select>
          
          <el-button type="primary" @click="refreshData" :loading="loading">
            刷新
          </el-button>
          <el-button type="success" @click="exportData">
            导出Excel
          </el-button>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-cards">
      <el-col :span="4" v-for="(stat, key) in statusStats" :key="key">
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
      </el-col>
    </el-row>

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
        <el-table-column prop="room_number" label="房间号" width="80" />
        
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
        <el-table-column prop="latest_issue_description" label="问题描述" width="150" show-overflow-tooltip />
        <el-table-column prop="latest_issue_type" label="问题类型" width="100" />
        <el-table-column label="录入时间" width="120">
          <template #default="scope">
            {{ scope.row.latest_issue_record_date ? formatDate(scope.row.latest_issue_record_date) : '' }}
          </template>
        </el-table-column>
        
        <!-- 待落实相关列 -->
        <el-table-column label="待落实" width="70" align="center">
          <template #default="scope">
            <span>{{ scope.row.pending_communications_count || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="latest_comm_content" label="沟通内容" width="150" show-overflow-tooltip />
        <el-table-column label="沟通时间" width="120">
          <template #default="scope">
            {{ scope.row.latest_comm_time ? formatDate(scope.row.latest_comm_time) : '' }}
          </template>
        </el-table-column>
        
        <!-- 收房意愿 -->
        <el-table-column label="收房意愿" width="100">
          <template #default="scope">
            <el-tag 
              v-if="scope.row.latest_feedback" 
              :type="scope.row.latest_feedback === '高' ? 'success' : 'danger'"
              size="small"
            >
              {{ scope.row.latest_feedback }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="100">
          <template #default="scope">
            <el-button type="primary" size="small" @click="viewRoom(scope.row)">
              查看
            </el-button>
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
import { adminAPI } from '../api'
import { ElMessage } from 'element-plus'
import { House, Tools, CircleCheck, SuccessFilled } from '@element-plus/icons-vue'

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
const selectedBuilding = ref('3单元')  // 默认选择3单元
const selectedStatus = ref('')
const selectedDelivery = ref('')
const selectedContract = ref('')
const selectedIssueFilter = ref('')
const selectedCommFilter = ref('')

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
    
    // 沟通筛选
    if (selectedCommFilter.value) {
      const hasComms = (room.pending_communications_count || 0) > 0
      if (selectedCommFilter.value === 'has_comms' && !hasComms) return false
      if (selectedCommFilter.value === 'no_comms' && hasComms) return false
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

const exportData = () => {
  // 简单的CSV导出
  const csvData = [
    ['楼栋', '房间号', '整改状态', '交付状态', '签约状态', '待验收', '问题描述', '问题类型', '录入时间', '待落实', '沟通内容', '沟通时间', '收房意愿']
  ]
  
  filteredRooms.value.forEach(room => {
    csvData.push([
      room.building_unit,
      room.room_number,
      room.status,
      room.delivery_status,
      room.contract_status,
      room.pending_issues_count || 0,
      room.latest_issue_description || '',
      room.latest_issue_type || '',
      room.latest_issue_record_date ? formatDate(room.latest_issue_record_date) : '',
      room.pending_communications_count || 0,
      room.latest_comm_content || '',
      room.latest_comm_time ? formatDate(room.latest_comm_time) : '',
      room.latest_feedback || ''
    ])
  })
  
  const csvContent = csvData.map(row => row.join(',')).join('\n')
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `ZWY项目汇总_${new Date().toLocaleDateString()}.csv`
  link.click()
  
  ElMessage.success('数据导出成功')
}

const viewRoom = (room) => {
  router.push(`/rooms/${room.id}`)
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
    '已签约': 'primary'
  }
  return typeMap[status] || 'info'
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('zh-CN')
}

onMounted(() => {
  fetchSummary()
})
</script>

<style scoped>
.admin-summary {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.filters {
  margin-bottom: 20px;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.stats-cards {
  margin-bottom: 20px;
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