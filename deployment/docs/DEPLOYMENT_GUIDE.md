# ZWY项目管理系统完整部署指南

## 📋 系统要求

### 硬件要求
- **操作系统**: Windows Server 2016+
- **内存**: 4GB+
- **磁盘空间**: 10GB+ 可用空间
- **网络**: 稳定的内网连接

### 软件依赖
- **Python**: 3.11+
- **Node.js**: 16.0+ (用于前端构建)
- **Nginx**: 1.28.0+ (Web服务器)
- **管理员权限**: 必须以管理员身份运行

## 🎯 部署架构

```
[用户浏览器] → [Nginx:80] → [Python Backend:8000] → [SQLite数据库]
```

## 📂 标准目录结构

```
D:\web_zwy\                    # 项目根目录
├── backend\                   # 后端API
│   ├── main.py               # API入口文件
│   ├── zwy_project.db        # SQLite数据库
│   ├── .env                  # 环境配置
│   └── static\               # 前端静态文件
├── frontend\                 # 前端源码
│   ├── src\                  # Vue.js源码
│   └── dist\                 # 构建输出
└── deployment\               # 部署脚本
    ├── scripts\              # 核心脚本
    ├── docs\                 # 文档
    └── backup\               # 备份目录
```

## 🚀 详细部署流程

### 阶段1: 部署前准备

#### 1.1 环境检查
```cmd
# 检查磁盘空间
D:
dir

# 检查Python环境
python --version

# 检查Node.js环境
node --version

# 检查管理员权限
whoami /priv | findstr SeDebugPrivilege
```

#### 1.2 服务状态确认
```cmd
cd D:\web_zwy\deployment
scripts\service_manager.bat status
```

### 阶段2: 停止服务和备份

#### 2.1 智能停止服务
```cmd
scripts\service_manager.bat stop
```

#### 2.2 自动备份
备份会在更新脚本中自动执行，包括：
- 数据库文件 (zwy_project.db)
- 配置文件 (.env)
- 上传文件 (如存在)

### 阶段3: 代码更新

#### 3.1 创建临时目录
```cmd
D:
if not exist "web_zwy_new" mkdir web_zwy_new
```

#### 3.2 传输新版本代码
将开发环境的代码完整复制到 `D:\web_zwy_new\`

#### 3.3 保留关键数据
```cmd
# 复制数据库
copy "D:\web_zwy\backend\zwy_project.db" "D:\web_zwy_new\backend\zwy_project.db" /Y

# 复制配置文件
copy "D:\web_zwy\backend\.env" "D:\web_zwy_new\backend\.env" /Y

# 复制上传文件（如果存在）
if exist "D:\web_zwy\uploads" xcopy "D:\web_zwy\uploads" "D:\web_zwy_new\uploads\" /E /I /Y
```

#### 3.4 原子性版本切换
```cmd
D:
if exist "web_zwy_backup" rmdir /s /q "web_zwy_backup"
ren "web_zwy" "web_zwy_backup"
ren "web_zwy_new" "web_zwy"
```

### 阶段4: 系统更新

#### 4.1 执行更新脚本
```cmd
cd D:\web_zwy
deployment\scripts\update_deploy.bat
```

脚本会自动执行：
- ✅ 环境检查和备份
- ✅ 数据库迁移检查
- ✅ 前端项目构建
- ✅ 静态文件更新
- ✅ 后端依赖更新

### 阶段5: 启动和验证

#### 5.1 启动服务
```cmd
scripts\service_manager.bat start
```

#### 5.2 验证部署
```cmd
# 检查服务状态
scripts\service_manager.bat status

# 访问系统进行功能验证
# http://10.13.33.52
```

## 🧪 功能验证清单

### 基础功能验证
- [ ] 系统正常访问
- [ ] 用户登录功能
- [ ] 主要页面显示正常
- [ ] 数据查询正常

### 新功能验证
- [ ] 本次更新的功能正常
- [ ] 无明显错误和异常
- [ ] 性能无明显下降

## ⚠️ 故障排除

### 端口冲突问题
- **现象**: 端口80或8000被占用
- **解决**: 启动脚本会自动处理，无需手动干预

### 浏览器缓存问题
- **现象**: 新功能不显示或界面异常
- **解决**: 按 `Ctrl + F5` 强制刷新浏览器

### Python环境问题
- **现象**: 后端服务启动失败
- **解决**: 检查Python版本和依赖安装

### 前端构建问题
- **现象**: 静态资源异常
- **解决**: 检查Node.js环境，重新执行构建

## 🚨 应急回滚

### 自动回滚
```cmd
scripts\emergency_rollback.bat
```

### 手动回滚
```cmd
# 停止服务
scripts\service_manager.bat stop

# 恢复旧版本
D:
rmdir /s /q "web_zwy"
ren "web_zwy_backup" "web_zwy"

# 重启服务
cd D:\web_zwy\deployment
scripts\service_manager.bat start
```

## 📊 性能监控

### 系统资源监控
```cmd
# 查看进程状态
tasklist | findstr "python\|nginx"

# 查看端口状态
netstat -ano | findstr ":8000\|:80"
```

### 日志监控
- **后端日志**: uvicorn启动窗口
- **Nginx日志**: D:\nginx-1.28.0\logs\
- **部署日志**: deployment\backup\logs\

## 🔒 安全最佳实践

### 文件权限
- 限制数据库文件访问权限
- .env文件不可公开访问
- 定期清理过期备份

### 网络安全
- 仅开放必要端口（80, 8000）
- 限制管理员账号使用
- 定期更换管理员密码

## 📈 维护计划

### 日常维护
- **每日检查**: 服务状态和系统资源
- **每周备份**: 完整数据备份
- **每月清理**: 清理过期日志和备份

### 更新流程
1. **开发环境测试** - 确保功能稳定
2. **制定维护窗口** - 选择业务低峰期
3. **执行标准部署** - 按照指南操作
4. **功能验证** - 完整测试所有功能
5. **用户通知** - 通知系统恢复使用

---

**文档版本**: 精简优化版 | **适用环境**: Windows Server | **维护状态**: 活跃更新