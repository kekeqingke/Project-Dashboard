@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ====================================================================
REM            ZWY项目管理系统统一部署入口 (精简优化版)
REM                       一键部署，简化操作
REM ====================================================================

cls
echo.
echo ====================================================================
echo                ZWY项目管理系统部署管理中心
echo ====================================================================
echo.
echo 请选择操作：
echo.
echo 【部署相关】
echo 【1】 完整版本更新部署    【2】 仅启动服务
echo 【3】 仅停止服务          【4】 重启服务
echo.
echo 【维护相关】
echo 【5】 查看服务状态        【6】 数据备份
echo 【7】 紧急回滚            【8】 端口检查
echo.
echo 【信息查看】
echo 【9】 管理员信息          【H】 查看帮助
echo 【0】 退出
echo.
echo ====================================================================
set /p "CHOICE=请选择操作 (0-9,H): "

if "%CHOICE%"=="1" goto :full_deploy
if "%CHOICE%"=="2" goto :start_only
if "%CHOICE%"=="3" goto :stop_only
if "%CHOICE%"=="4" goto :restart_only
if "%CHOICE%"=="5" goto :status_only
if "%CHOICE%"=="6" goto :backup_only
if "%CHOICE%"=="7" goto :rollback_only
if "%CHOICE%"=="8" goto :check_ports_only
if "%CHOICE%"=="9" goto :admin_info_only
if /i "%CHOICE%"=="H" goto :help_info
if "%CHOICE%"=="0" exit /b 0

echo 无效选择，请重新输入...
timeout /t 2 /nobreak >nul
goto :menu

:full_deploy
echo.
echo ====================================================================
echo                      完整版本更新部署
echo ====================================================================
echo.
echo 💡 部署流程预览：
echo 1. 智能停止服务
echo 2. 执行系统更新
echo 3. 启动服务验证
echo.

set /p "CONFIRM=确认开始完整部署? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo 部署已取消
    pause
    goto :menu
)

echo.
echo 📋 部署步骤 1/3：停止服务...
call scripts\service_manager.bat stop

echo.
echo 📋 部署步骤 2/3：执行系统更新...
call scripts\update_deploy.bat

echo.
echo 📋 部署步骤 3/3：启动服务...
call scripts\service_manager.bat start

echo.
echo ====================================================================
echo                      🎉 完整部署流程完成！
echo ====================================================================
echo.
echo 📋 部署总结：
echo ✅ 服务已停止并重新启动
echo ✅ 系统已更新到最新版本
echo.
echo 🎯 重要提醒：
echo • 首次访问请按 Ctrl+F5 刷新浏览器清除缓存
echo • 系统地址：http://10.13.33.52
echo • 如有问题请使用紧急回滚功能
echo ====================================================================

pause
goto :menu

:start_only
call scripts\service_manager.bat start
pause
goto :menu

:stop_only
call scripts\service_manager.bat stop
pause
goto :menu

:restart_only
call scripts\service_manager.bat restart
pause
goto :menu

:status_only
call scripts\service_manager.bat status
pause
goto :menu

:backup_only
call scripts\backup.bat
echo.
echo 💾 备份完成，文件保存在 backup\ 目录
pause
goto :menu

:rollback_only
echo.
echo ====================================================================
echo                        紧急回滚操作
echo ====================================================================
echo.
echo ⚠️  警告：此操作将恢复到上一个版本
echo • 当前数据可能会丢失
echo • 请确认已尝试其他解决方案
echo.
set /p "ROLLBACK_CONFIRM=确认执行紧急回滚? (Y/N): "
if /i "%ROLLBACK_CONFIRM%"=="Y" (
    call scripts\emergency_rollback.bat
) else (
    echo 回滚已取消
)
pause
goto :menu

:check_ports_only
call scripts\utils\check_ports.bat
pause
goto :menu

:admin_info_only
call scripts\utils\show_admin_info.bat
pause
goto :menu

:help_info
echo.
echo ====================================================================
echo                          部署帮助信息
echo ====================================================================
echo.
echo 📋 功能说明：
echo.
echo 【1】完整版本更新部署
echo     • 适用于：版本更新、功能升级
echo     • 包含：停服→更新→启动的完整流程
echo     • 注意：请在执行前手动完成代码、数据库、.env和uploads更新
echo.
echo 【2-4】服务管理
echo     • 启动/停止/重启系统服务
echo     • 适用于：日常维护、故障处理
echo.
echo 【5】查看服务状态
echo     • 检查后端API服务和Nginx Web服务状态
echo     • 显示系统访问地址
echo.
echo 【6】数据备份
echo     • 备份数据库和配置文件
echo     • 建议：定期执行或重要操作前执行
echo.
echo 【7】紧急回滚
echo     • 快速恢复到上一个版本
echo     • 适用于：部署失败或严重问题
echo.
echo 🎯 最佳实践：
echo • 部署前手动完成：代码复制、数据库更新、.env配置、uploads文件
echo • 部署后清除浏览器缓存 (Ctrl+F5)
echo • 遇到问题优先查看服务状态
echo • 重要更新建议在业务低峰期执行
echo.
echo 📞 技术支持：
echo • 系统地址：http://10.13.33.52
echo • API文档：http://10.13.33.52/docs
echo • 备份位置：deployment\backup\
echo ====================================================================
echo.
pause
goto :menu

:menu
cls
echo.
echo ====================================================================
echo                ZWY项目管理系统部署管理中心
echo ====================================================================
echo.
echo 请选择操作：
echo.
echo 【部署相关】
echo 【1】 完整版本更新部署    【2】 仅启动服务
echo 【3】 仅停止服务          【4】 重启服务
echo.
echo 【维护相关】
echo 【5】 查看服务状态        【6】 数据备份
echo 【7】 紧急回滚            【8】 端口检查
echo.
echo 【信息查看】
echo 【9】 管理员信息          【H】 查看帮助
echo 【0】 退出
echo.
echo ====================================================================
set /p "CHOICE=请选择操作 (0-9,H): "

if "%CHOICE%"=="1" goto :full_deploy
if "%CHOICE%"=="2" goto :start_only
if "%CHOICE%"=="3" goto :stop_only
if "%CHOICE%"=="4" goto :restart_only
if "%CHOICE%"=="5" goto :status_only
if "%CHOICE%"=="6" goto :backup_only
if "%CHOICE%"=="7" goto :rollback_only
if "%CHOICE%"=="8" goto :check_ports_only
if "%CHOICE%"=="9" goto :admin_info_only
if /i "%CHOICE%"=="H" goto :help_info
if "%CHOICE%"=="0" exit /b 0

echo 无效选择，请重新输入...
timeout /t 2 /nobreak >nul
goto :menu