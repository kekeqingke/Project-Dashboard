# ZWY项目管理系统部署脚本说明

## 📂 核心文件

### 主要脚本
- **`update_deploy_v2.bat`** - 版本更新部署脚本（推荐使用）
- **`service_manager_v2.bat`** - 服务管理脚本（推荐使用）

### 工具脚本
- **`check_ports.bat`** - 端口冲突检查和解决
- **`show_admin_info.bat`** - 查看管理员账号信息
- **`emergency_rollback.bat`** - 紧急回滚脚本

### 文档
- **`DEPLOYMENT_GUIDE_v2.md`** - 详细部署指南

## 🚀 快速使用

### 标准部署流程
```cmd
# 1. 停止服务
service_manager_v2.bat stop

# 2. 备份数据（脚本中已集成）
# 3. 复制新代码并替换
# 4. 执行更新
cd D:\web_zwy
deployment\update_deploy_v2.bat

# 5. 启动服务
deployment\service_manager_v2.bat start
```

### 日常维护
```cmd
# 查看状态
service_manager_v2.bat status

# 启动/停止/重启
service_manager_v2.bat start|stop|restart

# 检查端口冲突
check_ports.bat

# 查看登录信息
show_admin_info.bat
```

## ⚠️ 注意事项

1. **数据库迁移**：更新脚本会提示是否需要迁移，请根据实际功能需求判断
2. **管理员权限**：所有脚本需要以管理员身份运行
3. **端口80冲突**：v2脚本会自动处理HTTP服务占用问题

---
*版本: v2.0 | 更新: 2025-09-15*