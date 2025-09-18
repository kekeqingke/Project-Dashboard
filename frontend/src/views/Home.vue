<template>
  <div class="home-container">
    <div class="welcome-section">
      <h1>🏠 瑧湾悦项目品质管理系统</h1>
      <div class="status-card">
        <h2>✅ 系统已启动成功！</h2>
        <p>前后端服务均已正常运行</p>
      </div>
    </div>

    <div class="info-section">
      <div class="system-info">
        <h3>🎯 系统功能</h3>
        <div class="feature-cards">
          <div class="feature-card admin">
            <h4>👑 管理员功能</h4>
            <p>用户管理、系统配置、数据统计</p>
            <p class="permission">完整系统管理权限</p>
          </div>
          
          <div class="feature-card ambassador">
            <h4>💬 客户大使功能</h4>
            <p>客户沟通记录、验收反馈</p>
            <p class="permission">客户沟通 + 质量验收</p>
          </div>
          
          <div class="feature-card engineer">
            <h4>🔧 项目工程师功能</h4>
            <p>质量问题跟踪、工程进度管理</p>
            <p class="permission">质量问题管理</p>
          </div>
          
          <div class="feature-card maintenance">
            <h4>🛠️ 维修工程师功能</h4>
            <p>质量整改、维修记录管理</p>
            <p class="permission">质量问题管理</p>
          </div>
        </div>
      </div>

      <div class="action-section">
        <button class="login-button" @click="goToLogin">
          🚀 开始使用系统
        </button>
      </div>

      <div class="api-section">
        <h3>🔗 系统链接</h3>
        <div class="links">
          <a href="/api/docs" target="_blank" class="api-link">
            📚 后端API文档
          </a>
          <span class="current-link">
            🌐 前端地址: localhost:5173
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
console.log('✅ Home component loaded')

const goToLogin = () => {
  console.log('Login button clicked')
  window.location.href = '/login'
}
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.welcome-section {
  text-align: center;
  color: white;
  margin-bottom: 40px;
}

h1 {
  font-size: 3em;
  margin-bottom: 20px;
  text-shadow: 0 4px 8px rgba(0,0,0,0.3);
}

.status-card {
  background: rgba(255,255,255,0.1);
  backdrop-filter: blur(10px);
  border-radius: 15px;
  padding: 30px;
  margin: 0 auto;
  max-width: 500px;
  border: 1px solid rgba(255,255,255,0.2);
}

.status-card h2 {
  font-size: 2em;
  margin-bottom: 10px;
}

.info-section {
  max-width: 1200px;
  margin: 0 auto;
}

.system-info h3 {
  text-align: center;
  color: white;
  font-size: 2em;
  margin-bottom: 30px;
  text-shadow: 0 2px 4px rgba(0,0,0,0.3);
}

.feature-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 25px;
  margin-bottom: 40px;
}

.feature-card {
  background: white;
  border-radius: 15px;
  padding: 25px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.2);
  transition: transform 0.3s ease;
  border-left: 6px solid;
}

.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 15px 40px rgba(0,0,0,0.3);
}

.feature-card.admin { border-left-color: #e74c3c; }
.feature-card.ambassador { border-left-color: #3498db; }
.feature-card.engineer { border-left-color: #2ecc71; }
.feature-card.maintenance { border-left-color: #f39c12; }

.feature-card h4 {
  color: #333;
  font-size: 1.4em;
  margin-bottom: 15px;
}

.feature-card p {
  margin: 8px 0;
  color: #666;
}

.permission {
  color: #888 !important;
  font-style: italic;
  font-size: 0.9em;
  margin-top: 15px !important;
}

.action-section {
  text-align: center;
  margin: 50px 0;
}

.login-button {
  background: linear-gradient(135deg, #ff6b6b, #ee5a52);
  color: white;
  border: none;
  padding: 20px 40px;
  font-size: 1.2em;
  font-weight: bold;
  border-radius: 50px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 8px 25px rgba(255,107,107,0.3);
}

.login-button:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 35px rgba(255,107,107,0.4);
}

.api-section {
  background: rgba(255,255,255,0.1);
  backdrop-filter: blur(10px);
  border-radius: 15px;
  padding: 30px;
  text-align: center;
}

.api-section h3 {
  color: white;
  margin-bottom: 20px;
  font-size: 1.5em;
}

.links {
  display: flex;
  justify-content: center;
  gap: 30px;
  flex-wrap: wrap;
}

.api-link {
  background: rgba(255,255,255,0.2);
  color: white;
  text-decoration: none;
  padding: 15px 25px;
  border-radius: 10px;
  transition: all 0.3s ease;
}

.api-link:hover {
  background: rgba(255,255,255,0.3);
  transform: translateY(-2px);
}

.current-link {
  color: white;
  padding: 15px 25px;
  background: rgba(255,255,255,0.15);
  border-radius: 10px;
}

@media (max-width: 768px) {
  h1 { font-size: 2em; }
  .feature-cards { grid-template-columns: 1fr; }
  .links { flex-direction: column; }
}
</style>