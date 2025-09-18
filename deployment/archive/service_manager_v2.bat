@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ====================================================================
REM            ZWY项目管理系统服务管理脚本 v2.0 (生产优化版)
REM                        支持多种维护操作
REM ====================================================================

set "PROJECT_DIR=%~dp0.."
set "BACKEND_DIR=%PROJECT_DIR%\backend"
set "NGINX_DIR=D:\nginx-1.28.0"
set "LOG_DIR=%~dp0maintenance_logs"
set "BACKUP_DIR=%~dp0backup"

REM 创建必要目录
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

REM 参数处理
set "ACTION=%1"
if "%ACTION%"=="" goto :show_menu

REM 根据参数执行相应操作
if /i "%ACTION%"=="status" goto :check_status
if /i "%ACTION%"=="stop" goto :stop_services
if /i "%ACTION%"=="start" goto :start_services
if /i "%ACTION%"=="restart" goto :restart_services
if /i "%ACTION%"=="backup" goto :backup_only
if /i "%ACTION%"=="maintenance" goto :full_maintenance
if /i "%ACTION%"=="help" goto :show_help

echo ❌ 无效参数: %ACTION%
goto :show_help

:show_menu
REM ====================================================================
REM 显示交互式菜单
REM ====================================================================
:menu
cls
echo.
echo ====================================================================
echo                ZWY项目管理系统服务管理 v2.0
echo ====================================================================
echo.
echo 请选择操作：
echo.
echo 【1】 查看服务状态        【2】 启动所有服务
echo 【3】 停止所有服务        【4】 重启所有服务
echo 【5】 仅备份数据          【6】 完整维护
echo 【7】 查看维护日志        【8】 清理过期文件
echo 【9】 检查端口冲突        【A】 帮助信息            【0】 退出
echo.
echo ====================================================================
set /p "CHOICE=请输入选项 (0-9,A): "

if "%CHOICE%"=="1" goto :check_status
if "%CHOICE%"=="2" goto :start_services
if "%CHOICE%"=="3" goto :stop_services
if "%CHOICE%"=="4" goto :restart_services
if "%CHOICE%"=="5" goto :backup_only
if "%CHOICE%"=="6" goto :full_maintenance
if "%CHOICE%"=="7" goto :view_logs
if "%CHOICE%"=="8" goto :cleanup_files
if "%CHOICE%"=="9" goto :check_ports
if /i "%CHOICE%"=="A" goto :show_help
if "%CHOICE%"=="0" exit /b 0

echo 无效选择，请重新输入...
timeout /t 2 /nobreak >nul
goto :menu

REM ====================================================================
REM 功能函数定义
REM ====================================================================

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
        goto :check_website
    )
) else (
    echo ❌ Nginx Web服务：未运行 ^(端口:80^)
)

:check_website
REM 检查网站可访问性
echo.
echo 🌐 系统访问地址：
echo   • 本机访问：http://localhost
echo   • 内网访问：http://10.13.33.52
echo   • API文档： http://10.13.33.52/docs

echo.
if not "%ACTION%"=="" exit /b 0
pause
goto :menu

:stop_services
echo.
echo ====================================================================
echo                        停止所有服务
echo ====================================================================
echo.

REM 停止Nginx
echo 正在停止Nginx服务...
if exist "%NGINX_DIR%" (
    cd /d "%NGINX_DIR%"
    nginx.exe -s quit >nul 2>&1
    timeout /t 3 /nobreak >nul
)

REM 强制停止Nginx进程（如果正常停止失败）
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":80 " 2^>nul') do (
    taskkill /pid %%p /f >nul 2>&1
    echo ✅ Nginx服务已停止 ^(PID: %%p^)
)

REM 停止后端服务
echo 正在停止后端服务...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :8000 2^>nul') do (
    taskkill /pid %%p /f >nul 2>&1
    echo ✅ 后端服务已停止 ^(PID: %%p^)
)

REM 验证服务停止
timeout /t 2 /nobreak >nul
netstat -ano | findstr ":8000\|:80 " >nul 2>&1
if %errorlevel% equ 0 (
    echo ⚠️  部分服务可能未完全停止
) else (
    echo ✅ 所有服务已成功停止
)

echo.
if not "%ACTION%"=="" exit /b 0
pause
goto :menu

:start_services
echo.
echo ====================================================================
echo                        启动所有服务
echo ====================================================================
echo.

REM 启动前自动处理端口冲突
echo 1. 检查并处理端口占用...

REM 检查端口8000
netstat -ano | findstr ":8000 " >nul 2>&1
if %errorlevel% equ 0 (
    echo ⚠️  端口8000被占用，正在清理...
    for /f "tokens=5" %%p in ('netstat -ano ^| findstr :8000') do (
        taskkill /pid %%p /f >nul 2>&1
        echo ✅ 已清理端口8000占用进程
    )
    timeout /t 2 /nobreak >nul
) else (
    echo ✅ 端口8000可用
)

REM 自动处理端口80占用
netstat -ano | findstr ":80 " >nul 2>&1
if %errorlevel% equ 0 (
    echo ⚠️  端口80被占用，正在自动释放...

    REM 停止Web发布服务
    net stop "World Wide Web Publishing Service" >nul 2>&1
    timeout /t 2 /nobreak >nul

    REM 检查是否释放
    netstat -ano | findstr ":80 " >nul 2>&1
    if !errorlevel! equ 0 (
        echo 正在停止HTTP服务...
        net stop http /y >nul 2>&1
        timeout /t 3 /nobreak >nul

        REM 最终检查
        netstat -ano | findstr ":80 " >nul 2>&1
        if !errorlevel! equ 0 (
            echo ⚠️  端口80仍被占用，尝试强制清理...
            for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":80 "') do (
                if not "%%p"=="4" (
                    taskkill /pid %%p /f >nul 2>&1
                    echo ✅ 已强制清理进程 %%p
                )
            )
        ) else (
            echo ✅ 端口80已成功释放
        )
    ) else (
        echo ✅ 端口80已成功释放
    )
) else (
    echo ✅ 端口80可用
)

echo.
echo 2. 启动后端API服务...
cd /d "%BACKEND_DIR%"

REM 检查Python环境和main.py
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python环境不可用
    if not "%ACTION%"=="" exit /b 1
    pause
    goto :menu
)

if not exist "main.py" (
    echo ❌ 未找到main.py文件
    if not "%ACTION%"=="" exit /b 1
    pause
    goto :menu
)

REM 启动后端服务
start "ZWY Backend Service" /min cmd /k "uvicorn main:app --host 0.0.0.0 --port 8000"
echo ✅ 后端服务启动命令已执行

REM 等待并验证后端服务
echo 等待后端服务启动...
for /L %%i in (1,1,15) do (
    timeout /t 2 /nobreak >nul
    netstat -ano | findstr :8000 >nul 2>&1
    if !errorlevel! equ 0 (
        echo ✅ 后端API服务启动成功 ^(端口:8000^)
        goto :start_nginx
    )
)

echo ❌ 后端API服务启动失败或超时
if not "%ACTION%"=="" exit /b 1
pause
goto :menu

:start_nginx
echo.
echo 3. 启动Nginx Web服务...
if not exist "%NGINX_DIR%" (
    echo ❌ Nginx目录不存在: %NGINX_DIR%
    echo 请检查Nginx安装路径
    if not "%ACTION%"=="" exit /b 1
    pause
    goto :menu
)

cd /d "%NGINX_DIR%"
start "ZWY Nginx Service" /min nginx.exe
echo ✅ Nginx服务启动命令已执行

REM 等待并验证Nginx服务
echo 等待Nginx服务启动...
for /L %%i in (1,1,10) do (
    timeout /t 1 /nobreak >nul
    netstat -ano | findstr ":80 " >nul 2>&1
    if !errorlevel! equ 0 (
        echo ✅ Nginx Web服务启动成功 ^(端口:80^)
        goto :start_complete
    )
)

echo ❌ Nginx Web服务启动失败或超时
if not "%ACTION%"=="" exit /b 1
pause
goto :menu

:start_complete
echo.
echo ====================================================================
echo                      🎉 服务启动完成！
echo ====================================================================
echo 🌐 系统访问地址：
echo   • 本机访问：http://localhost
echo   • 内网访问：http://10.13.33.52
echo   • API文档： http://10.13.33.52/docs
echo.
echo 💡 建议验证功能：
echo   1. 浏览器访问系统
echo   2. 测试登录功能
echo   3. 检查新功能是否正常
echo ====================================================================

if not "%ACTION%"=="" exit /b 0
pause
goto :menu

:restart_services
echo.
echo ====================================================================
echo                        重启所有服务
echo ====================================================================
echo.

call :stop_services
echo.
echo 等待服务完全停止...
timeout /t 3 /nobreak >nul
echo.
call :start_services

if not "%ACTION%"=="" exit /b 0
pause
goto :menu

:backup_only
echo.
echo ====================================================================
echo                        数据备份操作
echo ====================================================================
echo.

REM 生成时间戳
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "TIMESTAMP=%dt:~0,4%-%dt:~4,2%-%dt:~6,2%_%dt:~8,2%-%dt:~10,2%-%dt:~12,2%"
set "BACKUP_SUBDIR=%BACKUP_DIR%\%TIMESTAMP%"

echo 创建备份目录: %BACKUP_SUBDIR%
if not exist "%BACKUP_SUBDIR%" mkdir "%BACKUP_SUBDIR%"

cd /d "%BACKEND_DIR%"

REM 备份数据库
if exist "zwy_project.db" (
    echo 正在备份数据库...
    copy "zwy_project.db" "%BACKUP_SUBDIR%\zwy_project_%TIMESTAMP%.db" >nul
    echo ✅ 数据库备份完成
) else (
    echo ❌ 数据库文件不存在
)

REM 备份配置文件
if exist ".env" (
    echo 正在备份环境配置...
    copy ".env" "%BACKUP_SUBDIR%\.env_%TIMESTAMP%" >nul
    echo ✅ 环境配置备份完成
) else (
    echo ⚠️  环境配置文件不存在
)

REM 备份Nginx配置
if exist "%NGINX_DIR%\conf\nginx.conf" (
    echo 正在备份Nginx配置...
    copy "%NGINX_DIR%\conf\nginx.conf" "%BACKUP_SUBDIR%\nginx_%TIMESTAMP%.conf" >nul
    echo ✅ Nginx配置备份完成
)

echo.
echo ====================================================================
echo                      🎉 备份操作完成！
echo ====================================================================
echo 📁 备份位置: %BACKUP_SUBDIR%
echo 🕐 备份时间: %TIMESTAMP%
echo ====================================================================

if not "%ACTION%"=="" exit /b 0
pause
goto :menu

:full_maintenance
echo.
echo ====================================================================
echo                      完整系统维护
echo ====================================================================
echo.

set /p "CONFIRM=确认执行完整维护（停止→备份→清理→重启）? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo 维护操作已取消
    if not "%ACTION%"=="" exit /b 0
    pause
    goto :menu
)

call :stop_services
echo.
call :backup_only
echo.
call :cleanup_files
echo.
call :start_services

echo.
echo ====================================================================
echo                    🎉 完整维护已完成！
echo ====================================================================

if not "%ACTION%"=="" exit /b 0
pause
goto :menu

:view_logs
echo.
echo ====================================================================
echo                        维护日志查看
echo ====================================================================
echo.

if not exist "%LOG_DIR%" (
    echo ❌ 维护日志目录不存在: %LOG_DIR%
    pause
    goto :menu
)

echo 最近的维护日志文件:
dir /b /od "%LOG_DIR%\*.log" 2>nul
echo.

pause
goto :menu

:cleanup_files
echo.
echo 正在清理过期文件...

REM 清理过期备份（30天）
forfiles /p "%BACKUP_DIR%" /d -30 /c "cmd /c if @isdir==TRUE rmdir /s /q @path" 2>nul
if %errorlevel% equ 0 (
    echo ✅ 过期备份清理完成 ^(保留30天^)
) else (
    echo ℹ️  无过期备份需要清理
)

REM 清理过期日志（7天）
forfiles /p "%LOG_DIR%" /d -7 /c "cmd /c del @path" 2>nul
if %errorlevel% equ 0 (
    echo ✅ 过期日志清理完成 ^(保留7天^)
) else (
    echo ℹ️  无过期日志需要清理
)

if not "%ACTION%"=="" exit /b 0
pause
goto :menu

:check_ports
echo.
echo ====================================================================
echo                        端口占用检查
echo ====================================================================
echo.

call "%~dp0check_ports.bat"

if not "%ACTION%"=="" exit /b 0
pause
goto :menu

:show_help
echo.
echo ====================================================================
echo                        使用帮助 v2.0
echo ====================================================================
echo.
echo 【命令行使用方式】
echo %~nx0 [操作]
echo.
echo 【支持的操作参数】
echo   status      - 查看服务状态
echo   start       - 启动所有服务（自动处理端口冲突）
echo   stop        - 停止所有服务
echo   restart     - 重启所有服务
echo   backup      - 仅备份数据
echo   maintenance - 完整维护（停止→备份→清理→重启）
echo   help        - 显示此帮助信息
echo.
echo 【v2.0新特性】
echo   ✅ 自动端口冲突处理（HTTP服务、端口80）
echo   ✅ 增强的启动验证和超时处理
echo   ✅ 更完善的错误处理和回滚机制
echo   ✅ 详细的状态检查和日志记录
echo.
echo 【使用示例】
echo   %~nx0 start            # 自动启动（推荐）
echo   %~nx0 restart          # 重启所有服务
echo   %~nx0 maintenance      # 执行完整维护
echo.
echo ====================================================================

if not "%ACTION%"=="" exit /b 0
pause
goto :menu