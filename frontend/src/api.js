import axios from 'axios'

// 创建axios实例
const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器 - 自动添加认证token
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 处理统一错误
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Token过期，清除登录信息
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// 房间相关API
export const roomAPI = {
  // 获取房间列表
  getRooms() {
    return api.get('/rooms/')
  },
  
  // 创建房间
  createRoom(roomData) {
    return api.post('/rooms/', roomData)
  },
  
  // 获取房间详情
  getRoomDetail(id) {
    return api.get(`/rooms/${id}`)
  }
}

// 质量问题相关API
export const qualityIssueAPI = {
  // 获取质量问题列表
  getQualityIssues(roomId) {
    const params = roomId ? { room_id: roomId } : {}
    return api.get('/quality-issues/', { params })
  },
  
  // 创建质量问题
  createQualityIssue(issueData) {
    return api.post('/quality-issues/', issueData)
  },
  
  // 接受质量问题
  acceptQualityIssue(issueId) {
    return api.put(`/quality-issues/${issueId}/accept`)
  }
}

// 客户沟通相关API
export const communicationAPI = {
  // 获取沟通记录列表
  getCommunications(roomId) {
    const params = roomId ? { room_id: roomId } : {}
    return api.get('/communications/', { params })
  },
  
  // 创建沟通记录
  createCommunication(commData) {
    return api.post('/communications/', commData)
  }
}

// 用户相关API
export const userAPI = {
  // 获取用户列表
  getUsers() {
    return api.get('/users/')
  },
  
  // 创建用户
  createUser(userData) {
    return api.post('/users/', userData)
  },
  
  // 获取当前用户信息
  getCurrentUser() {
    return api.get('/users/me')
  },
  
  // 分配房间给用户
  assignRoom(userId, roomId) {
    return api.post('/room-assignments/', {
      user_id: userId,
      room_id: roomId
    })
  },
  
  // 获取房间分配关系
  getRoomAssignments() {
    return api.get('/room-assignments/')
  },
  
  // 删除房间分配
  deleteRoomAssignment(assignmentId) {
    return api.delete(`/room-assignments/${assignmentId}`)
  }
}

// 管理员相关API
export const adminAPI = {
  // 获取数据汇总
  getSummary(buildingUnit) {
    const params = buildingUnit ? { building_unit: buildingUnit } : {}
    return api.get('/admin/summary', { params })
  }
}

// 文件上传API
export const fileAPI = {
  // 上传图片
  uploadImage(file) {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/upload-image/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  }
}

export default api