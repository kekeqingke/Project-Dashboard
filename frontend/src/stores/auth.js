import { defineStore } from 'pinia'
import axios from 'axios'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: localStorage.getItem('token') || null
  }),
  
  getters: {
    isAuthenticated: (state) => !!state.token && !!state.user,
    isAdmin: (state) => state.user?.role === 'admin',
    isCustomerAmbassador: (state) => state.user?.role === 'customer_ambassador',
    isEngineer: (state) => ['project_engineer', 'maintenance_engineer'].includes(state.user?.role)
  },
  
  actions: {
    async login(username, password) {
      try {
        const formData = new FormData()
        formData.append('username', username)
        formData.append('password', password)
        
        const response = await axios.post('http://localhost:8000/token', formData)
        const { access_token, user } = response.data
        
        this.token = access_token
        this.user = user
        
        localStorage.setItem('token', access_token)
        axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
        
        return { success: true }
      } catch (error) {
        return { 
          success: false, 
          message: error.response?.data?.detail || '登录失败' 
        }
      }
    },
    
    logout() {
      this.user = null
      this.token = null
      localStorage.removeItem('token')
      delete axios.defaults.headers.common['Authorization']
    },
    
    async getCurrentUser() {
      if (!this.token) return
      
      try {
        const response = await axios.get('http://localhost:8000/users/me')
        this.user = response.data
      } catch (error) {
        this.logout()
      }
    },
    
    initializeAuth() {
      if (this.token) {
        axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`
        this.getCurrentUser()
      }
    }
  }
})