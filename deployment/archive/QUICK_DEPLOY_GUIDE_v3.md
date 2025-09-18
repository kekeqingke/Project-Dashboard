# ZWY系统快速部署指南 v3.0

## 🚀 一键部署命令 (推荐)

基于2025-09-16实战经验，推荐使用以下优化流程：

### 服务器操作命令序列
```cmd
# 1. 智能停止服务 (v3.0新增)
cd D:\web_zwy\deployment
service_manager_v3.bat smart_stop

# 2. 自动备份
quick_backup.bat

# 3. 代码传输 (手动操作)
# 将 F:\pinrui\web_zwy\ 传输到服务器 D:\web_zwy_new\

# 4. 数据保留
copy "D:\web_zwy\backend\zwy_project.db" "D:\web_zwy_new\backend\zwy_project.db" /Y
copy "D:\web_zwy\backend\.env" "D:\web_zwy_new\backend\.env" /Y

# 5. 版本切换
D:
if exist "web_zwy_backup" rmdir /s /q "web_zwy_backup"
ren "web_zwy" "web_zwy_backup"
ren "web_zwy_new" "web_zwy"

# 6. 更新部署
cd D:\web_zwy
deployment\update_deploy_v3.bat

# 7. 启动服务
deployment\service_manager_v3.bat start

# 8. 验证状态
service_manager_v3.bat status
```

## 🎯 关键决策点

### 数据库迁移选择
- **前端功能更新**: 选择 `N`
- **仅界面优化**: 选择 `N`
- **后端结构变更**: 根据具体情况选择

### 用户操作提醒
**部署完成后必须提醒用户**:
> 🔄 系统已更新，首次访问请按 `Ctrl + F5` 刷新浏览器缓存

## ⚡ 紧急回滚 (如有问题)
```cmd
cd D:\web_zwy\deployment
emergency_rollback.bat
```

## 📞 技术支持清单

### 部署成功标志
- ✅ 两个服务都显示"运行中"
- ✅ 浏览器可访问 http://10.13.33.52
- ✅ 强制刷新后新功能正常

### 常见问题快速解决
1. **端口80停不掉** → 直接执行启动脚本，它会自动处理
2. **新功能不显示** → 提醒用户按 `Ctrl + F5`
3. **服务启动失败** → 检查Python环境和依赖

---

**基于实战验证** ✅ | **v3.0优化版** ✅ | **生产环境可用** ✅