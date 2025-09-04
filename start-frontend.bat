@echo off
echo 正在启动前端服务...
echo.

REM 检查5173端口是否被占用
echo 检查端口5173状态...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173') do (
    set PID=%%a
    if defined PID (
        echo 发现端口5173被进程 !PID! 占用，正在终止...
        taskkill //F //PID !PID! >nul 2>&1
        if !errorlevel! equ 0 (
            echo 成功终止进程 !PID!
        ) else (
            echo 无法终止进程 !PID!，可能权限不足
        )
    )
)

REM 等待端口释放
timeout /t 2 /nobreak >nul

echo.
echo 启动前端开发服务器...
cd /d "%~dp0frontend"
npm run dev

pause