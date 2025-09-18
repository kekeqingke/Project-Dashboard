@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
echo.
echo ====================================================================
echo                     ZWY项目管理系统快速备份脚本
echo ====================================================================
echo.

set "PROJECT_DIR=%~dp0.."
set "BACKEND_DIR=%PROJECT_DIR%\backend"
set "BACKUP_DIR=%~dp0backup"

REM 创建备份目录
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

REM 生成时间戳
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "TIMESTAMP=%dt:~0,4%-%dt:~4,2%-%dt:~6,2%_%dt:~8,2%-%dt:~10,2%-%dt:~12,2%"

echo 📅 备份时间：%TIMESTAMP%
echo 📁 备份目录：%BACKUP_DIR%
echo.

cd /d "%BACKEND_DIR%"

echo 1. 备份主数据库文件...
if exist "zwy_project.db" (
    for /f %%A in ('dir "zwy_project.db" ^| findstr /c:" bytes"') do set size=%%A
    copy "zwy_project.db" "%BACKUP_DIR%\zwy_project_%TIMESTAMP%.db" >nul
    echo ✅ 主数据库备份完成：zwy_project_%TIMESTAMP%.db
    echo ℹ️  数据库大小：!size! 字节，包含生产数据
) else (
    echo ❌ 主数据库文件不存在 (zwy_project.db)
)

REM 检查其他数据库文件并报告
if exist "app.db" (
    for /f %%A in ('dir "app.db" ^| findstr /c:" bytes"') do (
        if %%A EQU 0 (
            echo ℹ️  发现空数据库文件 app.db，已跳过备份
        )
    )
)
if exist "test.db" (
    for /f %%A in ('dir "test.db" ^| findstr /c:" bytes"') do (
        if %%A EQU 0 (
            echo ℹ️  发现空数据库文件 test.db，已跳过备份
        )
    )
)

echo.
echo 2. 备份环境配置...
if exist ".env" (
    copy ".env" "%BACKUP_DIR%\.env_%TIMESTAMP%" >nul
    copy ".env" "%BACKUP_DIR%\.env.backup" >nul
    echo ✅ 环境配置备份完成
) else (
    echo ⚠️  环境配置文件不存在
)

echo.
echo 3. 备份上传文件...
if exist "uploads" (
    if exist "%BACKUP_DIR%\uploads" rmdir /s /q "%BACKUP_DIR%\uploads" >nul 2>&1
    xcopy "uploads" "%BACKUP_DIR%\uploads\" /E /I /Y >nul
    echo ✅ 上传文件备份完成
) else (
    echo ℹ️  上传文件目录不存在
)

echo.
echo ====================================================================
echo                      ✅ 快速备份完成！
echo ====================================================================
echo.

echo 📦 备份内容：
if exist "%BACKUP_DIR%\zwy_project_%TIMESTAMP%.db" (
    echo • 数据库：zwy_project_%TIMESTAMP%.db
)
if exist "%BACKUP_DIR%\.env_%TIMESTAMP%" (
    echo • 环境配置：.env_%TIMESTAMP%
)
if exist "%BACKUP_DIR%\uploads" (
    echo • 上传文件：uploads 目录
)

echo.
echo 💡 使用说明：
echo • 紧急回滚：运行 emergency_rollback.bat
echo • 手动恢复：从 %BACKUP_DIR% 目录复制文件
echo • 清理备份：定期清理过期备份文件
echo ====================================================================
echo.

if "%1"=="" pause