@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ====================================================================
REM            ZWY项目管理系统服务管理脚本 (精简优化版)
REM                   整合v3.0实战经验，简化维护
REM ====================================================================

set "PROJECT_DIR=%~dp0..\.."
set "BACKEND_DIR=%PROJECT_DIR%\backend"
set "NGINX_DIR=D:\nginx-1.28.0"
set "LOG_DIR=%~dp0..\backup\logs"
set "BACKUP_DIR=%~dp0..\backup"

REM 创建必要目录
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

REM 参数处理
set "ACTION=%1"
if "%ACTION%"=="" goto :show_menu

REM 根据参数执行相应操作
if /i "%ACTION%"=="status" goto :check_status
if /i "%ACTION%"=="stop" goto :smart_stop
if /i "%ACTION%"=="start" goto :start_services
if /i "%ACTION%"=="restart" goto :restart_services
if /i "%ACTION%"=="help" goto :show_help

echo ❌ 无效参数: %ACTION%
goto :show_help

:show_menu
cls
echo.
echo ====================================================================
echo                ZWY项目管理系统服务管理 (精简版)
echo ====================================================================
echo.
echo 请选择操作：
echo.
echo 【1】 查看服务状态        【2】 启动所有服务
echo 【3】 停止所有服务        【4】 重启所有服务
echo 【H】 帮助信息            【0】 退出
echo.
echo ====================================================================
set /p "CHOICE=请输入选项 (0-4,H): "

if "%CHOICE%"=="1" goto :check_status
if "%CHOICE%"=="2" goto :start_services
if "%CHOICE%"=="3" goto :smart_stop
if "%CHOICE%"=="4" goto :restart_services
if /i "%CHOICE%"=="H" goto :show_help
if "%CHOICE%"=="0" exit /b 0

echo 无效选择，请重新输入...
timeout /t 2 /nobreak >nul
goto :show_menu

:check_status
echo.
echo ====================================================================
echo                        服务状态检查
echo ====================================================================
echo.

REM 检查后端服务
netstat -ano | findstr :8000 >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=5" %%p in ('netstat -ano ^| findstr :8000') do (
        echo ✅ 后端API服务：运行中 ^(端口:8000, PID:%%p^)
        goto :check_nginx
    )
) else (
    echo ❌ 后端API服务：未运行 ^(端口:8000^)
)

:check_nginx
REM 检查Nginx服务
netstat -ano | findstr :80 >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":80 "') do (
        echo ✅ Nginx Web服务：运行中 ^(端口:80, PID:%%p^)
        goto :show_access_info
    )
) else (
    echo ❌ Nginx Web服务：未运行 ^(端口:80^)
)

:show_access_info
echo.
echo 🌐 系统访问地址：
echo   • 本机访问：http://localhost
echo   • 内网访问：http://10.13.33.52
echo   • API文档： http://10.13.33.52/docs

echo.
if not "%ACTION%"=="" exit /b 0
pause
goto :show_menu

:smart_stop
echo.
echo ====================================================================
echo                    智能停止服务
echo ====================================================================
echo.
echo 💡 基于实战经验的智能停止策略
echo.

REM 停止后端服务
echo 正在停止后端服务...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :8000 2^>nul') do (
    taskkill /pid %%p /f >nul 2>&1
    echo ✅ 后端服务已停止 ^(PID: %%p^)
)

REM 智能处理Nginx
echo 正在处理Nginx服务...
if exist "%NGINX_DIR%" (
    cd /d "%NGINX_DIR%"
    nginx.exe -s quit >nul 2>&1
    timeout /t 3 /nobreak >nul
)

netstat -ano | findstr ":80 " >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":80 " 2^>nul') do (
        if not "%%p"=="4" (
            taskkill /pid %%p /f >nul 2>&1
            echo ✅ Nginx服务已停止 ^(PID: %%p^)
        ) else (
            echo ℹ️  系统进程占用端口80，启动时会自动处理
        )
    )
) else (
    echo ✅ Nginx服务已停止
)

echo.
echo ✅ 服务停止完成

if not "%ACTION%"=="" exit /b 0
pause
goto :show_menu

:start_services
echo.
echo ====================================================================
echo                        启动所有服务
echo ====================================================================
echo.

REM 端口检查和处理
call :handle_port_conflicts

echo.
echo 2. 启动后端API服务...
cd /d "%BACKEND_DIR%"

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python环境不可用
    if not "%ACTION%"=="" exit /b 1
    pause
    goto :show_menu
)

if not exist "main.py" (
    echo ❌ 未找到main.py文件
    if not "%ACTION%"=="" exit /b 1
    pause
    goto :show_menu
)

start "ZWY Backend Service" /min cmd /k "uvicorn main:app --host 0.0.0.0 --port 8000"
echo ✅ 后端服务启动命令已执行

REM 等待后端服务启动
echo 等待后端服务启动...
for /L %%i in (1,1,15) do (
    timeout /t 2 /nobreak >nul
    netstat -ano | findstr :8000 >nul 2>&1
    if !errorlevel! equ 0 (
        echo ✅ 后端API服务启动成功
        goto :start_nginx
    )
)

echo ❌ 后端API服务启动失败
if not "%ACTION%"=="" exit /b 1
pause
goto :show_menu

:start_nginx
echo.
echo 3. 启动Nginx Web服务...
if not exist "%NGINX_DIR%" (
    echo ❌ Nginx目录不存在: %NGINX_DIR%
    if not "%ACTION%"=="" exit /b 1
    pause
    goto :show_menu
)

cd /d "%NGINX_DIR%"
start "ZWY Nginx Service" /min nginx.exe
echo ✅ Nginx服务启动命令已执行

REM 等待Nginx服务启动
echo 等待Nginx服务启动...
for /L %%i in (1,1,10) do (
    timeout /t 1 /nobreak >nul
    netstat -ano | findstr ":80 " >nul 2>&1
    if !errorlevel! equ 0 (
        tasklist /fi "imagename eq nginx.exe" >nul 2>&1
        if !errorlevel! equ 0 (
            echo ✅ Nginx Web服务启动成功
            goto :start_complete
        )
    )
)

echo ⚠️  Nginx启动状态需要确认
tasklist /fi "imagename eq nginx.exe" >nul 2>&1
if !errorlevel! equ 0 (
    echo ✅ Nginx进程已启动
    goto :start_complete
) else (
    echo ❌ Nginx启动失败
    if not "%ACTION%"=="" exit /b 1
    pause
    goto :show_menu
)

:start_complete
echo.
echo ====================================================================
echo                      🎉 服务启动完成！
echo ====================================================================
echo 🌐 系统访问地址：http://10.13.33.52
echo.
echo 💡 部署后提醒：
echo   • 首次访问新功能时按 Ctrl+F5 刷新浏览器
echo ====================================================================

if not "%ACTION%"=="" exit /b 0
pause
goto :show_menu

:restart_services
echo.
echo ====================================================================
echo                        重启所有服务
echo ====================================================================
echo.

call :smart_stop
echo.
echo 等待服务完全停止...
timeout /t 5 /nobreak >nul
echo.
call :start_services

if not "%ACTION%"=="" exit /b 0
pause
goto :show_menu

:handle_port_conflicts
echo 1. 检查并处理端口占用...

REM 检查端口8000
netstat -ano | findstr ":8000 " >nul 2>&1
if %errorlevel% equ 0 (
    echo ⚠️  端口8000被占用，正在清理...
    for /f "tokens=5" %%p in ('netstat -ano ^| findstr :8000') do (
        taskkill /pid %%p /f >nul 2>&1
        echo ✅ 已清理端口8000占用
    )
    timeout /t 2 /nobreak >nul
) else (
    echo ✅ 端口8000可用
)

REM 智能处理端口80
netstat -ano | findstr ":80 " >nul 2>&1
if %errorlevel% equ 0 (
    echo ⚠️  端口80被占用，执行智能处理...

    net stop "World Wide Web Publishing Service" >nul 2>&1
    net stop http /y >nul 2>&1
    timeout /t 3 /nobreak >nul

    netstat -ano | findstr ":80 " >nul 2>&1
    if !errorlevel! equ 0 (
        for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":80 "') do (
            if not "%%p"=="4" (
                taskkill /pid %%p /f >nul 2>&1
                echo ✅ 已清理端口80占用
            )
        )
    )
) else (
    echo ✅ 端口80可用
)
goto :eof

:show_help
echo.
echo ====================================================================
echo                        使用帮助
echo ====================================================================
echo.
echo 【命令行使用方式】
echo %~nx0 [操作]
echo.
echo 【支持的操作参数】
echo   status    - 查看服务状态
echo   start     - 启动所有服务
echo   stop      - 智能停止服务
echo   restart   - 重启所有服务
echo   help      - 显示此帮助信息
echo.
echo 【使用示例】
echo   %~nx0 start     # 启动服务
echo   %~nx0 restart   # 重启服务
echo   %~nx0 status    # 查看状态
echo.
echo ====================================================================

if not "%ACTION%"=="" exit /b 0
pause
goto :show_menu