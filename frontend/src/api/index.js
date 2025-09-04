import axios from 'axios'

// 创建axios实例
const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 60000
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => Promise.reject(error)
)

// 响应拦截器
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// API方法
export const authAPI = {
  login: (username, password) => {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)
    return api.post('/token', formData)
  },
  getCurrentUser: () => api.get('/users/me')
}

export const userAPI = {
  getUsers: () => api.get('/users/'),
  createUser: (userData) => api.post('/users/', userData),
  resetPassword: (userId) => api.put(`/users/${userId}/reset-password`),
  deleteUser: (userId) => api.delete(`/users/${userId}`),
  assignRoom: (userId, roomId) => api.post('/room-assignments/', { user_id: userId, room_id: roomId }),
  getRoomAssignments: () => api.get('/room-assignments/'),
  deleteRoomAssignment: (assignmentId) => api.delete(`/room-assignments/${assignmentId}`)
}

export const roomAPI = {
  getRooms: () => api.get('/rooms/'),
  createRoom: (roomData) => api.post('/rooms/', roomData)
}

export const qualityIssueAPI = {
  getQualityIssues: (roomId) => api.get('/quality-issues/', { params: { room_id: roomId } }),
  createQualityIssue: (issueData) => api.post('/quality-issues/', issueData),
  acceptQualityIssue: (issueId) => api.put(`/quality-issues/${issueId}/accept`)
}

export const communicationAPI = {
  getCommunications: (roomId) => api.get('/communications/', { params: { room_id: roomId } }),
  createCommunication: (commData) => api.post('/communications/', commData)
}

export const adminAPI = {
  getSummary: (buildingUnit) => api.get('/admin/summary', { params: { building_unit: buildingUnit } })
}

export const customerAPI = {
  getCustomerByRoom: (roomId) => api.get(`/customers/room/${roomId}`),
  createCustomer: (customerData) => api.post('/customers/', customerData),
  updateCustomer: (customerId, customerData) => api.put(`/customers/${customerId}`, customerData),
  deleteCustomer: (customerId) => api.delete(`/customers/${customerId}`)
}

export default api