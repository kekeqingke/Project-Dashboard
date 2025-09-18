# ZWY项目管理系统部署文档

## 🚀 快速开始

### 一键部署
```cmd
# 在项目根目录执行
deployment\deploy.bat
```

### 服务管理
```cmd
# 查看状态
deployment\scripts\service_manager.bat status

# 启动服务
deployment\scripts\service_manager.bat start

# 停止服务
deployment\scripts\service_manager.bat stop

# 重启服务
deployment\scripts\service_manager.bat restart
```

## 📁 目录结构

```
deployment/
├── scripts/                    # 核心脚本
│   ├── service_manager.bat    # 服务管理
│   ├── update_deploy.bat      # 部署更新
│   ├── backup.bat             # 数据备份
│   ├── emergency_rollback.bat # 紧急回滚
│   └── utils/                 # 工具脚本
│       ├── check_ports.bat    # 端口检查
│       └── show_admin_info.bat # 管理员信息
├── docs/                      # 文档目录
├── deploy.bat                 # 统一入口脚本
└── backup/                    # 备份数据
```

## 🎯 部署流程

### 标准部署步骤
1. **停止服务**: `scripts\service_manager.bat stop`
2. **备份数据**: 自动执行（在更新脚本中）
3. **传输代码**: 将新版本代码传输到服务器
4. **保留数据**: 复制数据库和配置文件
5. **版本切换**: 原子性替换版本
6. **执行更新**: `scripts\update_deploy.bat`
7. **启动服务**: `scripts\service_manager.bat start`
8. **功能验证**: 访问系统并测试功能

### 重要提醒
- **浏览器缓存**: 部署后按 `Ctrl + F5` 刷新浏览器
- **数据库迁移**: 前端更新通常选择 `N`
- **端口冲突**: 脚本会自动处理端口80冲突问题

## ⚠️ 常见问题

### 问题1: 端口80无法停止
**解决**: 直接执行启动脚本，它会自动处理冲突

### 问题2: 新功能不显示
**解决**: 按 `Ctrl + F5` 强制刷新浏览器缓存

### 问题3: 服务启动失败
**解决**: 检查Python环境和依赖安装

## 🔧 紧急回滚

如遇严重问题，立即执行：
```cmd
scripts\emergency_rollback.bat
```

## 📞 技术支持

- **系统访问**: http://10.13.33.52
- **API文档**: http://10.13.33.52/docs
- **备份位置**: deployment\backup\

---

**版本**: 精简优化版 | **维护**: 定期更新 | **状态**: 生产可用