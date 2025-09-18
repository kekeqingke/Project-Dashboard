@echo off
chcp 65001 >nul
echo.
echo ====================================================================
echo                    ZWY项目管理系统管理员账号查看
echo ====================================================================
echo.

set "BACKEND_DIR=%~dp0..\backend"
set "ENV_FILE=%BACKEND_DIR%\.env"

if not exist "%ENV_FILE%" (
    echo ❌ 未找到配置文件：%ENV_FILE%
    echo.
    echo 可能的解决方案：
    echo 1. 检查路径是否正确
    echo 2. 运行 deploy.bat 进行完整部署
    echo 3. 从备份恢复配置文件
    echo.
    pause
    exit /b 1
)

echo 📋 从配置文件读取管理员信息：
echo 📁 配置文件位置：%ENV_FILE%
echo.

REM 提取管理员用户名和密码
for /f "tokens=1,2 delims==" %%a in ('type "%ENV_FILE%" ^| findstr "ADMIN_USERNAME\|ADMIN_PASSWORD"') do (
    if "%%a"=="ADMIN_USERNAME" (
        set "ADMIN_USER=%%b"
        echo 👤 管理员用户名：%%b
    )
    if "%%a"=="ADMIN_PASSWORD" (
        set "ADMIN_PASS=%%b"
        echo 🔑 管理员密码：  %%b
    )
)

echo.
echo ====================================================================
echo                        🌐 系统访问信息
echo ====================================================================
echo.
echo 📍 访问地址：
echo   • 本机访问：http://localhost
echo   • 内网访问：http://10.13.33.52
echo   • API文档： http://10.13.33.52/docs
echo.
echo 🔐 登录方式：
echo   1. 打开浏览器访问上述任一地址
echo   2. 点击右上角"登录"按钮
echo   3. 输入上述用户名和密码
echo   4. 首次登录后建议立即修改密码
echo.
echo ⚠️  安全提醒：
echo   • 请妥善保管此登录信息
echo   • 建议首次登录后立即修改密码
echo   • 不要在不安全的环境中运行此脚本
echo   • 定期备份 .env 文件
echo.

REM 检查服务状态
echo 🔍 快速服务状态检查：
netstat -ano | findstr :8000 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 后端服务运行中 (端口8000)
) else (
    echo ❌ 后端服务未运行，请先启动服务
    echo    运行命令：service_manager.bat start
)

netstat -ano | findstr :80 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Web服务运行中 (端口80)
) else (
    echo ❌ Web服务未运行，请先启动Nginx
)

echo.
echo ====================================================================
echo.

pause