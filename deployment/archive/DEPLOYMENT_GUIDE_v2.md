# ZWY项目管理系统生产环境部署指南 v2.0

## 📋 概述

本指南基于实际生产环境部署经验制定，提供了完整的、经过验证的部署流程和优化脚本。

### 版本信息
- **指南版本**: v2.0
- **适用系统**: Windows Server
- **更新日期**: 2025-09-15
- **基于经验**: 4功能整合部署实战

## 🎯 功能特性

### 部署流程特点：
- **通用性强** - 适用于任何版本更新部署
- **安全可靠** - 包含完整的备份和回滚机制
- **自动化程度高** - 智能处理常见部署问题
- **错误处理完善** - 详细的问题诊断和解决方案

## 🔧 系统要求

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

## 📂 目录结构

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
    ├── update_deploy_v2.bat  # 主部署脚本
    ├── service_manager_v2.bat # 服务管理脚本
    ├── check_ports.bat       # 端口检查脚本
    ├── quick_backup.bat      # 快速备份脚本
    └── backup\               # 备份目录
```

## 🚀 标准部署流程

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
service_manager_v2.bat status
```

#### 1.3 停止现有服务
```cmd
service_manager_v2.bat stop
```

### 阶段2: 数据备份

#### 2.1 自动备份（推荐）
```cmd
cd D:\web_zwy\deployment
quick_backup.bat
```

#### 2.2 手动备份（备选）
```cmd
# 创建备份目录
if not exist "D:\web_zwy\deployment\backup" mkdir "D:\web_zwy\deployment\backup"

# 备份数据库
copy "D:\web_zwy\backend\zwy_project.db" "D:\web_zwy\deployment\backup\zwy_project_%date:~0,4%%date:~5,2%%date:~8,2%.db"

# 备份配置
copy "D:\web_zwy\backend\.env" "D:\web_zwy\deployment\backup\.env.backup"
```

### 阶段3: 代码部署

#### 3.1 创建临时目录
```cmd
D:
if not exist "web_zwy_new" mkdir web_zwy_new
```

#### 3.2 复制新代码
将开发环境的 `F:\pinrui\web_zwy` 完整复制到 `D:\web_zwy_new\`

#### 3.3 保留关键数据
```cmd
# 复制数据库到新版本
copy "D:\web_zwy\deployment\backup\zwy_project*.db" "D:\web_zwy_new\backend\zwy_project.db" /Y

# 复制配置文件到新版本
copy "D:\web_zwy\deployment\backup\.env.backup" "D:\web_zwy_new\backend\.env" /Y

# 复制上传文件（如果存在）
if exist "D:\web_zwy\backend\uploads" xcopy "D:\web_zwy\backend\uploads" "D:\web_zwy_new\backend\uploads\" /E /I /Y
```

#### 3.4 原子性替换
```cmd
# 安全的版本切换
D:
if exist "web_zwy_backup" rmdir /s /q "web_zwy_backup"
ren "web_zwy" "web_zwy_backup"
ren "web_zwy_new" "web_zwy"
echo ✅ 版本切换完成
```

### 阶段4: 系统更新

#### 4.1 执行更新脚本
```cmd
# ⚠️ 重要：必须从项目根目录运行
D:
cd D:\web_zwy
deployment\update_deploy_v2.bat
```

**脚本自动执行：**
- ✅ 环境检查和路径验证
- ✅ 数据完整性验证
- ✅ 数据库迁移检查和提示
- ✅ 前端项目构建
- ✅ 静态文件更新
- ✅ 后端依赖更新
- ✅ 错误处理和回滚机制

### 阶段5: 服务启动

#### 5.1 启动服务（自动化）
```cmd
cd D:\web_zwy\deployment
service_manager_v2.bat start
```

**v2.0增强特性：**
- ✅ 自动端口冲突检测和处理
- ✅ 自动停止HTTP服务释放端口80
- ✅ 智能启动验证和超时处理
- ✅ 详细的错误报告和状态显示

#### 5.2 验证部署结果
```cmd
# 检查服务状态
service_manager_v2.bat status

# 获取登录信息
show_admin_info.bat
```

## 🧪 功能验证清单

### 验证步骤
1. **基础系统验证**
   - [ ] 浏览器访问系统地址正常
   - [ ] 用户登录功能正常
   - [ ] 主界面正常显示

2. **核心功能验证**
   - [ ] 主要业务模块页面正常
   - [ ] 数据查询和显示功能正常
   - [ ] 表单提交和保存功能正常
   - [ ] 权限控制功能正常

3. **新功能验证**
   - [ ] 本次更新的新功能可正常访问
   - [ ] 新功能的操作流程正常
   - [ ] 新功能的数据处理正确
   - [ ] 新功能与现有功能无冲突

4. **数据完整性验证**
   - [ ] 现有数据显示正确
   - [ ] 数据库迁移后无数据丢失
   - [ ] 导出功能正常（如适用）
   - [ ] 文件上传下载正常（如适用）

5. **兼容性验证**
   - [ ] 原有功能保持正常
   - [ ] 用户权限体系正常
   - [ ] 系统性能无明显下降

## ⚠️ 常见问题和解决方案

### 问题1: "未找到frontend目录"
**原因**: 脚本路径问题
**解决**: 从项目根目录运行脚本
```cmd
cd D:\web_zwy
deployment\update_deploy_v2.bat
```

### 问题2: 500错误 - "no such column: [字段名]"
**原因**: 数据库迁移未完成，缺少新字段
**解决**: 根据具体错误信息手动添加字段
```cmd
cd D:\web_zwy\backend
# 示例：添加缺失字段
python -c "import sqlite3; conn=sqlite3.connect('zwy_project.db'); cursor=conn.cursor(); cursor.execute('ALTER TABLE [表名] ADD COLUMN [字段名] [字段类型]'); conn.commit(); conn.close(); print('字段添加成功')"

# 或者检查表结构
python -c "import sqlite3; conn=sqlite3.connect('zwy_project.db'); cursor=conn.cursor(); cursor.execute('PRAGMA table_info([表名])'); print([row[1] for row in cursor.fetchall()]); conn.close()"
```

### 问题3: 端口80被占用
**原因**: Windows HTTP服务占用
**解决**: v2.0脚本自动处理，或手动执行
```cmd
net stop "World Wide Web Publishing Service"
net stop http /y
```

### 问题4: 前端构建失败
**原因**: Node.js环境问题
**解决**: 检查Node.js安装或跳过构建
```cmd
node --version
npm --version
```

### 问题5: 后端服务启动失败
**原因**: Python环境或依赖问题
**解决**:
```cmd
cd D:\web_zwy\backend
python --version
pip install -r requirements.txt
python main.py  # 查看具体错误
```

## 🚨 应急回滚方案

### 自动回滚（推荐）
```cmd
cd D:\web_zwy\deployment
emergency_rollback.bat
```

### 手动回滚
```cmd
# 停止服务
service_manager_v2.bat stop

# 恢复旧版本
D:
if exist "web_zwy_backup" (
    rmdir /s /q "web_zwy"
    ren "web_zwy_backup" "web_zwy"
)

# 重启服务
cd D:\web_zwy\deployment
service_manager_v2.bat start
```

### 数据恢复
```cmd
# 从备份恢复数据库
copy "D:\web_zwy\deployment\backup\zwy_project_*.db" "D:\web_zwy\backend\zwy_project.db" /Y

# 从备份恢复配置
copy "D:\web_zwy\deployment\backup\.env.backup" "D:\web_zwy\backend\.env" /Y
```

## 📊 性能监控

### 系统资源监控
```cmd
# 查看进程状态
tasklist | findstr python
tasklist | findstr nginx

# 查看端口状态
netstat -ano | findstr ":8000\|:80"

# 查看磁盘使用
dir D:\web_zwy /s
```

### 日志监控
- **后端日志**: 观察uvicorn启动窗口
- **Nginx日志**: `D:\nginx-1.28.0\logs\`
- **部署日志**: `D:\web_zwy\deployment\maintenance_logs\`

## 🔒 安全最佳实践

### 文件权限
- **数据库文件**: 限制访问权限
- **配置文件**: .env文件不可公开访问
- **备份文件**: 定期清理过期备份

### 网络安全
- **防火墙规则**: 仅开放必要端口（80, 8000）
- **访问控制**: 限制管理员账号使用
- **密码策略**: 定期更换管理员密码

### 数据保护
- **定期备份**: 每次部署前必须备份
- **版本控制**: 保留多个版本的备份
- **恢复测试**: 定期测试备份恢复流程

## 📈 维护计划

### 日常维护
- **每日检查**: 服务状态和系统资源
- **每周备份**: 完整数据备份
- **每月清理**: 清理过期日志和备份

### 定期维护
```cmd
# 完整维护（推荐每月执行）
service_manager_v2.bat maintenance
```

### 更新流程
1. **开发环境测试** - 确保新功能稳定
2. **制定维护窗口** - 选择业务低峰期
3. **执行标准部署** - 按照本指南操作
4. **功能验证** - 完整测试所有功能
5. **用户通知** - 通知系统恢复使用

## 📞 技术支持

### 联系方式
- **紧急问题**: 立即执行回滚方案
- **技术咨询**: 提供详细的错误日志和系统状态
- **功能反馈**: 记录具体的问题描述和重现步骤

### 问题报告模板
```
问题描述: [具体现象]
发生时间: [时间]
操作步骤: [导致问题的操作]
错误信息: [具体错误消息]
系统状态: [服务状态、端口状态等]
已尝试解决: [已经尝试的解决方法]
```

---

## 📝 版本历史

### v2.0 (2025-09-15)
- ✅ 基于实际部署经验优化
- ✅ 增加自动端口冲突处理
- ✅ 完善数据库迁移机制
- ✅ 增强错误处理和回滚机制
- ✅ 优化启动验证和超时处理

### v1.0 (2025-09-12)
- ✅ 初始版本
- ✅ 基础部署流程
- ✅ 基本的备份和恢复机制

---

**注意**: 本指南基于实际生产环境部署经验编写，建议在执行前仔细阅读每个步骤，确保理解操作内容和潜在风险。