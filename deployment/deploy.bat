@echo off
chcp 65001 >nul
echo.
echo ====================================================================
echo                    ZWY项目管理系统一键部署脚本
echo ====================================================================
echo.

echo 1. 检查项目目录...
if not exist "frontend" (
    echo ❌ 错误：未找到frontend目录
    pause
    exit /b 1
)

if not exist "backend" (
    echo ❌ 错误：未找到backend目录
    pause
    exit /b 1
)

echo ✅ 项目目录检查通过

echo.
echo 2. 构建前端项目...
cd /d "%~dp0frontend"
call npm install
if %errorlevel% neq 0 (
    echo ❌ 前端依赖安装失败
    pause
    exit /b 1
)

call npm run build
if %errorlevel% neq 0 (
    echo ❌ 前端构建失败
    pause
    exit /b 1
)
echo ✅ 前端构建完成

echo.
echo 3. 复制静态文件到后端...
cd /d "%~dp0"
if exist "backend\static" rmdir /s /q "backend\static"
mkdir "backend\static"
xcopy "frontend\dist\*" "backend\static\" /E /Y >nul
if %errorlevel% neq 0 (
    echo ❌ 静态文件复制失败
    pause
    exit /b 1
)
echo ✅ 静态文件复制完成

echo.
echo 4. 安装后端依赖...
cd /d "%~dp0backend"
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ 后端依赖安装失败
    pause
    exit /b 1
)
echo ✅ 后端依赖安装完成

echo.
echo 5. 初始化数据库和安全配置...
python init_db.py
if %errorlevel% neq 0 (
    echo ❌ 数据库初始化失败
    pause
    exit /b 1
)
echo ✅ 数据库初始化完成

echo.
echo 6. 配置Windows防火墙（需要管理员权限）...
netsh advfirewall firewall add rule name="ZWY-HTTP-Port-80" dir=in action=allow protocol=TCP localport=80 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 防火墙规则配置成功
) else (
    echo ⚠️  防火墙规则配置失败（可能需要管理员权限）
    echo    如果内网访问有问题，请手动执行：
    echo    netsh advfirewall firewall add rule name="ZWY-HTTP-Port-80" dir=in action=allow protocol=TCP localport=80
)

echo.
echo ====================================================================
echo                         🎉 一键部署完成！
echo ====================================================================
echo.
echo 接下来需要手动启动两个服务：
echo.
echo 【步骤1】启动后端API服务
echo ┌────────────────────────────────────────────────────────┐
echo │ 1. 打开新的命令行窗口（管理员身份）                      │
echo │ 2. 复制并执行以下命令：                                │
echo │    cd /d "%~dp0backend"                                │
echo │    uvicorn main:app --host 0.0.0.0 --port 8000        │
echo │ 3. 看到"Uvicorn running"消息后继续下一步               │
echo └────────────────────────────────────────────────────────┘
echo.
echo 【步骤2】启动Nginx服务
echo ┌────────────────────────────────────────────────────────┐
echo │ 1. 再打开一个新的命令行窗口（管理员身份）               │
echo │ 2. 复制并执行以下命令：                                │
echo │    cd /d "D:\nginx-1.28.0"                            │
echo │    nginx.exe                                          │
echo │ 3. 没有错误提示即为启动成功                             │
echo └────────────────────────────────────────────────────────┘
echo.
echo ====================================================================
echo 📋 部署完成后访问地址：
echo ====================================================================
echo 🖥️  本机访问：   http://localhost
echo 🌐 内网访问：   http://10.13.33.52
echo 📚 API文档：    http://10.13.33.52/docs
echo 👤 管理后台：   http://10.13.33.52/admin
echo.
echo 🔐 管理员账号信息：
echo 📧 用户名：admin
echo 🔑 密码：请查看上方数据库初始化输出的密码信息
echo.
echo ⚠️  重要提示：
echo • 请保持两个命令行窗口开启，不要关闭
echo • 首次登录后请立即修改管理员密码
echo • 如需停止服务，在对应窗口按 Ctrl+C
echo ====================================================================
echo.
pause