<template>
  <el-dialog
    v-model="visible"
    title="🔐 安全提醒 - 首次登录需修改密码"
    width="500px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :show-close="false"
    center
  >
    <div class="first-login-content">
      <div class="warning-icon">
        <el-icon size="48" color="#f56c6c"><Warning /></el-icon>
      </div>
      
      <div class="message">
        <h3>为了您的账户安全</h3>
        <p>检测到您是首次登录或使用初始密码，请立即修改密码以确保账户安全。</p>
      </div>
      
      <el-form 
        ref="formRef" 
        :model="form" 
        :rules="rules" 
        label-width="100px"
        @submit.prevent="handleSubmit"
      >
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

        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input 
            v-model="form.confirmPassword" 
            type="password" 
            placeholder="请再次输入新密码"
            show-password
            maxlength="50"
          />
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

    <template #footer>
      <div class="dialog-footer">
        <el-button 
          type="primary" 
          @click="handleSubmit"
          :loading="loading"
          size="large"
          style="width: 100%"
        >
          {{ loading ? '修改中...' : '立即修改密码' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Warning } from '@element-plus/icons-vue'
import api from '../api/index.js'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  currentPassword: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['update:modelValue', 'success'])

const visible = ref(props.modelValue)
const formRef = ref()
const loading = ref(false)

// 表单数据
const form = reactive({
  newPassword: '',
  confirmPassword: ''
})

// 密码强度相关
const strengthPercentage = ref(0)
const strengthText = ref('')
const strengthClass = ref('')

// 表单验证规则
const rules = {
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
      current_password: props.currentPassword,
      new_password: form.newPassword
    })
    
    ElMessage.success('密码修改成功！')
    
    // 关闭弹窗
    visible.value = false
    emit('update:modelValue', false)
    emit('success')
    
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

// 监听 props 变化
watch(() => props.modelValue, (newVal) => {
  visible.value = newVal
})

watch(visible, (newVal) => {
  emit('update:modelValue', newVal)
})
</script>

<script>
import { watch } from 'vue'
</script>

<style scoped>
.first-login-content {
  text-align: center;
  padding: 20px 0;
}

.warning-icon {
  margin-bottom: 20px;
}

.message {
  margin-bottom: 30px;
}

.message h3 {
  color: #333;
  margin-bottom: 10px;
  font-size: 18px;
}

.message p {
  color: #666;
  line-height: 1.6;
  margin: 0;
}

.password-strength {
  margin-top: 8px;
  text-align: left;
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
  margin-top: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #f56c6c;
  text-align: left;
}

.password-rules h4 {
  margin: 0 0 10px 0;
  color: #333;
  font-size: 14px;
  font-weight: 600;
}

.password-rules ul {
  margin: 0;
  padding-left: 18px;
}

.password-rules li {
  margin-bottom: 4px;
  color: #666;
  font-size: 13px;
}

.dialog-footer {
  padding: 0 20px 20px 20px;
}

:deep(.el-dialog__header) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 8px 8px 0 0;
  padding: 20px 24px;
}

:deep(.el-dialog__title) {
  font-weight: 600;
  font-size: 16px;
}
</style>