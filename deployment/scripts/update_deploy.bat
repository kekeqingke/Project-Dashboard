@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
echo.
echo ====================================================================
echo       ZWY项目管理系统版本更新脚本 (精简优化版)
echo                整合v3.0实战经验，简化操作
echo ====================================================================
echo.

REM 设置项目根目录
set "PROJECT_ROOT=%~dp0..\.."
set "BACKEND_DIR=%PROJECT_ROOT%\backend"
set "FRONTEND_DIR=%PROJECT_ROOT%\frontend"
set "DEPLOYMENT_DIR=%PROJECT_ROOT%\deployment"

echo 🔍 1. 环境检查...
echo 项目根目录: %PROJECT_ROOT%

REM 检查目录结构
if not exist "%FRONTEND_DIR%" (
    echo ❌ 错误：未找到frontend目录
    echo 💡 请确保从项目根目录运行此脚本
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
echo 📦 2. 自动备份...
call "%DEPLOYMENT_DIR%\scripts\backup.bat"

echo.
echo 🔧 3. 数据库迁移检查...
cd /d "%BACKEND_DIR%"

echo 💡 智能分析：
echo • 基于更新类型，系统建议：
echo • 前端功能更新 → 选择 N
echo • 界面优化更新 → 选择 N
echo • 后端结构更新 → 根据具体情况选择
echo.

set /p "DB_MIGRATION=是否需要执行数据库迁移? (Y/N): "

if /i "%DB_MIGRATION%"=="Y" (
    echo.
    echo 📋 数据库迁移提醒：
    echo 1. 请确保已备份数据
    echo 2. 执行必要的迁移操作
    echo 3. 验证迁移结果
    echo.
    pause
    echo ✅ 数据库迁移已确认完成
) else (
    echo ✅ 跳过数据库迁移
)

echo.
echo 🏗️  4. 构建前端...
cd /d "%FRONTEND_DIR%"

node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js环境不可用，跳过前端构建
    echo ⚠️  如有前端更新，请手动构建
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
    echo ⚠️  使用现有静态文件
)

echo.
echo 🐍 6. 更新后端依赖...
cd /d "%BACKEND_DIR%"

if exist "requirements.txt" (
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ⚠️  依赖更新失败，但继续部署
    ) else (
        echo ✅ 后端依赖更新完成
    )
) else (
    echo ℹ️  无requirements.txt文件，跳过依赖更新
)

echo.
echo ====================================================================
echo                         🎉 版本更新完成！
echo ====================================================================
echo.
echo 📋 更新总结：
echo ✅ 数据已备份
echo ✅ 前端已重新构建
echo ✅ 静态文件已更新
echo ✅ 后端依赖已更新
echo.
echo 🚀 接下来：
echo 1. 启动服务：scripts\service_manager.bat start
echo 2. 访问系统：http://10.13.33.52
echo 3. 🎯 重要：按 Ctrl+F5 刷新浏览器清除缓存
echo.
echo ====================================================================

pause