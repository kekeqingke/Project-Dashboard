@echo off
chcp 65001 >nul
echo.
echo ====================================================================
echo                     ZWY项目管理系统紧急回滚脚本
echo ====================================================================
echo.

set "PROJECT_DIR=%~dp0.."
set "BACKEND_DIR=%PROJECT_DIR%\backend"
set "BACKUP_DIR=%~dp0backup"
set "MIGRATION_BACKUP_DIR=%BACKEND_DIR%\backup_migration"

echo ⚠️  紧急回滚操作将：
echo • 停止所有运行中的服务
echo • 恢复数据库到最近的备份
echo • 恢复配置文件
echo.

set /p "CONFIRM=确认执行紧急回滚操作? (输入 YES 确认): "
if /i not "%CONFIRM%"=="YES" (
    echo 回滚操作已取消
    pause
    exit /b 0
)

echo.
echo ====================================================================
echo                        执行紧急回滚
echo ====================================================================
echo.

echo 1. 停止所有服务...
REM 停止后端服务
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :8000 2^>nul') do (
    taskkill /pid %%p /f >nul 2>&1
    echo ✅ 停止后端服务 (PID: %%p)
)

REM 停止Nginx
set "NGINX_DIR=D:\nginx-1.28.0"
if exist "%NGINX_DIR%" (
    cd /d "%NGINX_DIR%"
    nginx.exe -s quit >nul 2>&1
    timeout /t 2 /nobreak >nul
    
    REM 强制停止Nginx进程
    for /f "tokens=5" %%p in ('netstat -ano ^| findstr :80 2^>nul') do (
        taskkill /pid %%p /f >nul 2>&1
        echo ✅ 停止Nginx服务 (PID: %%p)
    )
)

echo.
echo 2. 查找可用的备份文件...
cd /d "%BACKEND_DIR%"

REM 检查迁移备份
if exist "%MIGRATION_BACKUP_DIR%\zwy_project_before_migration_*.db" (
    echo 找到迁移备份文件：
    for %%f in ("%MIGRATION_BACKUP_DIR%\zwy_project_before_migration_*.db") do (
        echo   - %%~nxf
        set "MIGRATION_BACKUP=%%f"
    )
    echo.
    set /p "USE_MIGRATION_BACKUP=使用迁移前备份? (Y/N): "
    if /i "!USE_MIGRATION_BACKUP!"=="Y" (
        echo 正在恢复迁移前备份...
        copy "!MIGRATION_BACKUP!" "zwy_project.db" >nul
        if !errorlevel! equ 0 (
            echo ✅ 数据库已从迁移备份恢复
        ) else (
            echo ❌ 迁移备份恢复失败
        )
        goto :config_restore
    )
)

REM 检查常规备份
if exist "%BACKUP_DIR%\*.db" (
    echo 找到常规备份文件：
    for %%f in ("%BACKUP_DIR%\*.db") do (
        echo   - %%~nxf (修改时间: %%~tf)
    )
    echo.
    echo 选择要恢复的备份文件：
    set /p "BACKUP_FILE=输入备份文件名 (不含路径): "
    if exist "%BACKUP_DIR%\!BACKUP_FILE!" (
        echo 正在恢复备份: !BACKUP_FILE!
        copy "%BACKUP_DIR%\!BACKUP_FILE!" "zwy_project.db" >nul
        if !errorlevel! equ 0 (
            echo ✅ 数据库已从备份恢复
        ) else (
            echo ❌ 备份恢复失败
        )
    ) else (
        echo ❌ 指定的备份文件不存在
    )
) else (
    echo ❌ 未找到数据库备份文件
    echo 请检查以下目录中是否有备份：
    echo   - %BACKUP_DIR%
    echo   - %MIGRATION_BACKUP_DIR%
)

:config_restore
echo.
echo 3. 恢复配置文件...

REM 恢复.env文件
if exist "%BACKUP_DIR%\.env.backup" (
    copy "%BACKUP_DIR%\.env.backup" ".env" >nul
    echo ✅ 环境配置文件已恢复
) else (
    echo ⚠️  未找到环境配置备份
)

REM 恢复上传文件
if exist "%BACKUP_DIR%\uploads" (
    if exist "uploads" rmdir /s /q "uploads" >nul 2>&1
    xcopy "%BACKUP_DIR%\uploads" "uploads\" /E /I /Y >nul
    echo ✅ 上传文件已恢复
)

echo.
echo ====================================================================
echo                      🎯 回滚操作完成！
echo ====================================================================
echo.

echo 📋 回滚摘要：
echo • 服务已停止
echo • 数据库已恢复
echo • 配置文件已恢复
echo.

echo 🔄 下一步操作：
echo 1. 检查数据完整性：访问 http://localhost 确认系统状态
echo 2. 重新启动服务：运行 service_manager.bat start
echo 3. 如需重新部署：备份当前状态后运行相应部署脚本
echo.

echo ⚠️  重要提醒：
echo • 请验证数据完整性
echo • 记录回滚原因和时间
echo • 如有问题请联系技术支持
echo ====================================================================
echo.

pause