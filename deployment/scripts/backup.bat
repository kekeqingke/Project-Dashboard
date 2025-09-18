@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo 📦 执行自动备份...

set "PROJECT_ROOT=%~dp0..\.."
set "BACKEND_DIR=%PROJECT_ROOT%\backend"
set "BACKUP_DIR=%~dp0..\backup"

REM 创建备份目录
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

REM 生成时间戳
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "TIMESTAMP=%dt:~0,4%%dt:~4,2%%dt:~6,2%_%dt:~8,2%%dt:~10,2%"

REM 备份数据库
if exist "%BACKEND_DIR%\zwy_project.db" (
    copy "%BACKEND_DIR%\zwy_project.db" "%BACKUP_DIR%\zwy_project_%TIMESTAMP%.db" >nul
    echo ✅ 数据库已备份：zwy_project_%TIMESTAMP%.db
) else (
    echo ❌ 未找到数据库文件
    exit /b 1
)

REM 备份配置文件
if exist "%BACKEND_DIR%\.env" (
    copy "%BACKEND_DIR%\.env" "%BACKUP_DIR%\.env_%TIMESTAMP%" >nul
    copy "%BACKEND_DIR%\.env" "%BACKUP_DIR%\.env.backup" >nul
    echo ✅ 配置文件已备份
) else (
    echo ⚠️  未找到配置文件
)

echo ✅ 备份完成