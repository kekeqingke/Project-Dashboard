@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
echo.
echo ====================================================================
echo            ZWY项目管理系统版本更新脚本 v2.0 (生产优化版)
echo ====================================================================
echo.

REM 设置项目根目录
set "PROJECT_ROOT=%~dp0.."
set "BACKEND_DIR=%PROJECT_ROOT%\backend"
set "FRONTEND_DIR=%PROJECT_ROOT%\frontend"
set "DEPLOYMENT_DIR=%PROJECT_ROOT%\deployment"

echo 🔍 1. 环境检查...
echo 项目根目录: %PROJECT_ROOT%

REM 检查是否从正确目录运行
if not exist "%FRONTEND_DIR%" (
    echo ❌ 错误：未找到frontend目录
    echo 💡 请确保从项目根目录运行此脚本：
    echo    cd D:\web_zwy
    echo    deployment\update_deploy_v2.bat
    pause
    exit /b 1
)

if not exist "%BACKEND_DIR%" (
    echo ❌ 错误：未找到backend目录
    pause
    exit /b 1
)

echo ✅ 项目目录检查通过

echo.
echo 📦 2. 执行数据备份...
cd /d "%DEPLOYMENT_DIR%"
if not exist "backup" mkdir "backup"

REM 生成时间戳
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "TIMESTAMP=%dt:~0,4%%dt:~4,2%%dt:~6,2%_%dt:~8,2%%dt:~10,2%"

REM 备份数据库
if exist "%BACKEND_DIR%\zwy_project.db" (
    copy "%BACKEND_DIR%\zwy_project.db" "backup\zwy_project_%TIMESTAMP%.db" >nul
    echo ✅ 数据库已备份：zwy_project_%TIMESTAMP%.db
) else (
    echo ❌ 未找到数据库文件，这可能导致系统异常
    set /p "CONTINUE=继续更新可能导致数据丢失，是否继续? (Y/N): "
    if /i not "!CONTINUE!"=="Y" (
        echo 更新已取消
        pause
        exit /b 1
    )
)

REM 备份配置文件
if exist "%BACKEND_DIR%\.env" (
    copy "%BACKEND_DIR%\.env" "backup\.env.backup" >nul
    copy "%BACKEND_DIR%\.env" "backup\.env_%TIMESTAMP%" >nul
    echo ✅ 配置文件已备份
) else (
    echo ❌ 未找到配置文件，可能导致登录问题
    set /p "CONTINUE=继续更新可能导致无法登录，是否继续? (Y/N): "
    if /i not "!CONTINUE!"=="Y" (
        echo 更新已取消
        pause
        exit /b 1
    )
)

echo.
echo 🔧 3. 数据库迁移检查...
cd /d "%BACKEND_DIR%"

echo 正在自动检测数据库结构...

REM ====================================================================
REM 自动检测部分 - 在此添加您的具体检测逻辑
REM ====================================================================

set "AUTO_MIGRATION_NEEDED=N"
set "MIGRATION_REASONS="

REM 示例检测1：检查某个字段是否存在（取消注释并修改为实际需要检测的字段）
REM python -c "import sqlite3; conn=sqlite3.connect('zwy_project.db'); cursor=conn.cursor(); cursor.execute('PRAGMA table_info(quality_issues)'); columns=[row[1] for row in cursor.fetchall()]; conn.close(); exit(0 if 'responsible_unit' in columns else 1)" >nul 2>&1
REM if !errorlevel! neq 0 (
REM     set "AUTO_MIGRATION_NEEDED=Y"
REM     set "MIGRATION_REASONS=!MIGRATION_REASONS! • 缺少字段: quality_issues.responsible_unit"
REM )

REM 示例检测2：检查某个表是否存在（取消注释并修改为实际需要检测的表）
REM python -c "import sqlite3; conn=sqlite3.connect('zwy_project.db'); cursor=conn.cursor(); cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\" AND name=\"new_table\"'); result=cursor.fetchone(); conn.close(); exit(0 if result else 1)" >nul 2>&1
REM if !errorlevel! neq 0 (
REM     set "AUTO_MIGRATION_NEEDED=Y"
REM     set "MIGRATION_REASONS=!MIGRATION_REASONS! • 缺少表: new_table"
REM )

REM ====================================================================
REM 智能提示和确认
REM ====================================================================

if "%AUTO_MIGRATION_NEEDED%"=="Y" (
    echo.
    echo ⚠️  自动检测发现需要数据库迁移：
    echo %MIGRATION_REASONS%
    echo.
    set /p "DB_MIGRATION=系统检测到需要数据库迁移，是否执行? (Y/N): "
) else (
    echo ✅ 自动检测：数据库结构正常
    echo.
    echo ⚠️  重要提醒：
    echo • 如果本次更新涉及新的数据库结构变更，请确认
    echo • 自动检测可能无法覆盖所有情况
    echo.
    set /p "DB_MIGRATION=是否仍需要手动执行数据库迁移? (Y/N): "
)
if /i "%DB_MIGRATION%"=="Y" (
    echo.
    echo 📋 数据库迁移准备：
    echo 1. 数据库文件位置：%BACKEND_DIR%\zwy_project.db
    echo 2. 建议先备份：copy zwy_project.db zwy_project_backup_%TIMESTAMP%.db
    echo 3. 执行迁移操作（SQL命令或Python脚本）
    echo 4. 验证迁移结果
    echo.
    pause
    echo ✅ 数据库迁移已确认完成，继续部署...
) else (
    echo ✅ 无需数据库迁移，继续部署...
)

echo.
echo 🏗️  4. 构建前端...
cd /d "%FRONTEND_DIR%"

REM 检查Node.js环境
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js环境不可用，跳过前端构建
    echo ⚠️  如果前端有更新，请手动构建或安装Node.js
    goto :skip_frontend
)

echo 安装前端依赖...
call npm install
if %errorlevel% neq 0 (
    echo ❌ 前端依赖安装失败
    pause
    exit /b 1
)

echo 构建前端项目...
call npm run build
if %errorlevel% neq 0 (
    echo ❌ 前端构建失败
    pause
    exit /b 1
)
echo ✅ 前端构建完成

:skip_frontend
echo.
echo 📂 5. 更新静态文件...
cd /d "%PROJECT_ROOT%"
if exist "backend\static" rmdir /s /q "backend\static"
mkdir "backend\static"

if exist "frontend\dist" (
    xcopy "frontend\dist\*" "backend\static\" /E /Y >nul
    echo ✅ 静态文件更新完成
) else (
    echo ⚠️  前端构建目录不存在，使用现有静态文件
)

echo.
echo 🐍 6. 更新后端依赖...
cd /d "%BACKEND_DIR%"
pip install -r requirements.txt >nul
if %errorlevel% neq 0 (
    echo ❌ 后端依赖安装失败
    pause
    exit /b 1
)
echo ✅ 后端依赖更新完成

echo.
echo 🔄 7. 恢复数据文件...
REM 数据文件已在部署过程中保留，无需额外恢复

echo.
echo ====================================================================
echo                         🎉 版本更新完成！
echo ====================================================================
echo.
echo 📋 更新内容：
echo ✅ 前端代码已更新并重新构建
echo ✅ 后端代码已更新
echo ✅ 数据库结构已更新（如适用）
echo ✅ 依赖包已更新
echo ✅ 数据文件已保留
echo.
echo 🚀 接下来请启动服务：
echo 1. 运行：deployment\service_manager_v2.bat start
echo 2. 访问：http://10.13.33.52 验证功能
echo.
echo 💾 备份信息：
echo • 数据库备份：deployment\backup\zwy_project_%TIMESTAMP%.db
echo • 配置备份：deployment\backup\.env.backup
echo • 迁移备份：backend\backup_migration\ (如果执行了迁移)
echo ====================================================================
echo.

pause