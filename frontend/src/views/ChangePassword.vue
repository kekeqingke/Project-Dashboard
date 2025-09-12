<template>
  <div class="change-password-container">
    <div class="change-password-card">
      <h2 class="title">🔐 修改密码</h2>
      
      <el-form 
        ref="formRef" 
        :model="form" 
        :rules="rules" 
        label-width="120px"
        @submit.prevent="handleSubmit"
      >
        <el-form-item label="当前密码" prop="currentPassword">
          <el-input 
            v-model="form.currentPassword" 
            type="password" 
            placeholder="请输入当前密码"
            show-password
            maxlength="50"
          />
        </el-form-item>

        <el-form-item label="新密码" prop="newPassword">
          <el-input 
            v-model="form.newPassword" 
            type="password" 
            placeholder="请输入新密码"
            show-password
            maxlength="50"
            @input="checkPasswordStrength"
          />
          
          <!-- 密码强度指示器 -->
          <div v-if="form.newPassword" class="password-strength">
            <div class="strength-bar">
              <div 
                class="strength-fill" 
                :class="strengthClass"
                :style="{ width: strengthPercentage + '%' }"
              ></div>
            </div>
            <span class="strength-text" :class="strengthClass">
              {{ strengthText }}
            </span>
          </div>
        </el-form-item>

        <el-form-item label="确认新密码" prop="confirmPassword">
          <el-input 
            v-model="form.confirmPassword" 
            type="password" 
            placeholder="请再次输入新密码"
            show-password
            maxlength="50"
          />
        </el-form-item>

        <el-form-item>
          <el-button 
            type="primary" 
            @click="handleSubmit"
            :loading="loading"
            size="large"
            style="width: 100%"
          >
            {{ loading ? '修改中...' : '修改密码' }}
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 密码规则说明 -->
      <div class="password-rules">
        <h4>密码要求：</h4>
        <ul>
          <li>至少8位字符</li>
          <li>包含大写字母 (A-Z)</li>
          <li>包含小写字母 (a-z)</li>
          <li>包含数字 (0-9)</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import api from '../api/index.js'

const router = useRouter()
const formRef = ref()
const loading = ref(false)

// 表单数据
const form = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// 密码强度相关
const strengthPercentage = ref(0)
const strengthText = ref('')
const strengthClass = ref('')

// 表单验证规则
const rules = {
  currentPassword: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '密码长度至少8位', trigger: 'blur' },
    {
      pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$/,
      message: '密码必须包含大写字母、小写字母和数字',
      trigger: 'blur'
    }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== form.newPassword) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 检查密码强度
const checkPasswordStrength = () => {
  const password = form.newPassword
  let score = 0
  
  // 长度检查
  if (password.length >= 8) score += 25
  if (password.length >= 12) score += 10
  
  // 包含小写字母
  if (/[a-z]/.test(password)) score += 20
  
  // 包含大写字母
  if (/[A-Z]/.test(password)) score += 20
  
  // 包含数字
  if (/\d/.test(password)) score += 15
  
  // 包含特殊字符
  if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) score += 10
  
  strengthPercentage.value = Math.min(score, 100)
  
  if (score < 40) {
    strengthText.value = '弱'
    strengthClass.value = 'weak'
  } else if (score < 70) {
    strengthText.value = '中等'
    strengthClass.value = 'medium'
  } else {
    strengthText.value = '强'
    strengthClass.value = 'strong'
  }
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    loading.value = true
    
    await api.post('/users/change-password', {
      current_password: form.currentPassword,
      new_password: form.newPassword
    })
    
    ElMessage.success('密码修改成功！')
    
    // 显示成功提示并跳转
    setTimeout(() => {
      router.push('/')
    }, 1500)
    
  } catch (error) {
    console.error('修改密码失败:', error)
    
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('密码修改失败，请重试')
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.change-password-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.change-password-card {
  background: white;
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 500px;
}

.title {
  text-align: center;
  margin-bottom: 30px;
  color: #333;
  font-size: 24px;
  font-weight: 600;
}

.password-strength {
  margin-top: 8px;
}

.strength-bar {
  width: 100%;
  height: 6px;
  background-color: #e0e0e0;
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 5px;
}

.strength-fill {
  height: 100%;
  border-radius: 3px;
  transition: all 0.3s ease;
}

.strength-fill.weak {
  background-color: #ff4757;
}

.strength-fill.medium {
  background-color: #ffa502;
}

.strength-fill.strong {
  background-color: #26de81;
}

.strength-text {
  font-size: 12px;
  font-weight: 500;
}

.strength-text.weak {
  color: #ff4757;
}

.strength-text.medium {
  color: #ffa502;
}

.strength-text.strong {
  color: #26de81;
}

.password-rules {
  margin-top: 30px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #667eea;
}

.password-rules h4 {
  margin: 0 0 12px 0;
  color: #333;
  font-size: 14px;
  font-weight: 600;
}

.password-rules ul {
  margin: 0;
  padding-left: 20px;
}

.password-rules li {
  margin-bottom: 6px;
  color: #666;
  font-size: 13px;
}

.el-form-item {
  margin-bottom: 25px;
}

.el-button--large {
  height: 48px;
  font-size: 16px;
  font-weight: 500;
}
</style>