@echo off
chcp 65001 >nul
title ZWY项目 - Nginx服务
echo.
echo ====================================================================
echo                      ZWY项目管理系统 - Nginx服务
echo ====================================================================
echo.
echo 正在启动Nginx服务...

REM 检查Nginx目录是否存在
if not exist "D:\nginx-1.28.0\nginx.exe" (
    echo.
    echo ❌ 错误：未找到Nginx执行文件
    echo 📁 预期位置：D:\nginx-1.28.0\nginx.exe
    echo.
    echo 💡 解决方案：
    echo 1. 确保Nginx已正确安装到 D:\nginx-1.28.0\ 目录
    echo 2. 或修改此脚本中的Nginx路径
    echo.
    pause
    exit /b 1
)

cd /d "D:\nginx-1.28.0"
echo 当前目录：%CD%
echo 启动命令：nginx.exe
echo.

REM 先尝试停止可能正在运行的nginx
nginx.exe -s quit >nul 2>&1

echo 启动Nginx...
nginx.exe
if %errorlevel% equ 0 (
    echo ✅ Nginx启动成功
    echo.
    echo 🌐 服务地址：
    echo    • 本机访问：http://localhost
    echo    • 内网访问：http://10.13.33.52
    echo.
    echo ⚠️  请保持此窗口开启
    echo 💡 如需停止服务，请按任意键
    echo.
    pause >nul
    echo.
    echo 正在停止Nginx服务...
    nginx.exe -s quit
    echo ✅ Nginx服务已停止
) else (
    echo ❌ Nginx启动失败
    echo.
    echo 💡 可能的原因：
    echo 1. 端口80被占用
    echo 2. 配置文件有错误
    echo 3. 权限不足
    echo.
    echo 🔍 检查步骤：
    echo 1. 检查端口占用：netstat -ano ^| findstr :80
    echo 2. 测试配置文件：nginx.exe -t
    echo 3. 以管理员身份运行此脚本
    echo.
)

pause