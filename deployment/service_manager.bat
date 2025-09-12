@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ====================================================================
REM                    ZWY项目管理系统服务管理脚本
REM                        支持多种维护操作
REM ====================================================================

set "PROJECT_DIR=%~dp0"
set "BACKEND_DIR=%PROJECT_DIR%backend"
set "NGINX_DIR=D:\nginx-1.28.0"
set "LOG_DIR=%PROJECT_DIR%maintenance_logs"
set "BACKUP_DIR=%PROJECT_DIR%backups"

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
echo                    ZWY项目管理系统服务管理
echo ====================================================================
echo.
echo 请选择操作：
echo.
echo 【1】 查看服务状态        【2】 启动所有服务
echo 【3】 停止所有服务        【4】 重启所有服务  
echo 【5】 仅备份数据          【6】 完整维护（停止→备份→重启）
echo 【7】 查看维护日志        【8】 清理过期文件
echo 【9】 帮助信息            【0】 退出
echo.
echo ====================================================================
set /p "CHOICE=请输入选项 (0-9): "

if "%CHOICE%"=="1" goto :check_status
if "%CHOICE%"=="2" goto :start_services
if "%CHOICE%"=="3" goto :stop_services
if "%CHOICE%"=="4" goto :restart_services
if "%CHOICE%"=="5" goto :backup_only
if "%CHOICE%"=="6" goto :full_maintenance
if "%CHOICE%"=="7" goto :view_logs
if "%CHOICE%"=="8" goto :cleanup_files
if "%CHOICE%"=="9" goto :show_help
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
        set "BACKEND_PID=%%p"
        goto :check_nginx
    )
) else (
    echo ❌ 后端API服务：未运行 ^(端口:8000^)
    set "BACKEND_PID="
)

:check_nginx
REM 检查Nginx服务
netstat -ano | findstr :80 >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=5" %%p in ('netstat -ano ^| findstr :80') do (
        echo ✅ Nginx Web服务：运行中 ^(端口:80, PID:%%p^)
        set "NGINX_PID=%%p"
        goto :check_website
    )
) else (
    echo ❌ Nginx Web服务：未运行 ^(端口:80^)
    set "NGINX_PID="
)

:check_website
REM 检查网站可访问性
echo.
echo 正在检查网站可访问性...
ping -n 1 127.0.0.1 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 网络连通性：正常
    REM 尝试访问网站
    curl -s -o nul -w "%%{http_code}" http://localhost/ 2>nul | findstr "200" >nul 2>&1
    if !errorlevel! equ 0 (
        echo ✅ 网站访问：正常 ^(http://localhost^)
        echo ✅ 内网访问：http://10.13.33.52
    ) else (
        echo ❌ 网站访问：异常
    )
) else (
    echo ❌ 网络连通性：异常
)

echo.
echo ====================================================================
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
cd /d "%NGINX_DIR%"
nginx.exe -s quit >nul 2>&1
timeout /t 3 /nobreak >nul

REM 检查Nginx是否停止
netstat -ano | findstr :80 >nul 2>&1
if %errorlevel% equ 0 (
    echo ⚠️  Nginx未能正常停止，尝试强制结束...
    for /f "tokens=5" %%p in ('netstat -ano ^| findstr :80') do (
        taskkill /pid %%p /f >nul 2>&1
    )
    echo ✅ Nginx服务已强制停止
) else (
    echo ✅ Nginx服务已正常停止
)

REM 停止后端服务
echo 正在停止后端服务...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :8000') do (
    taskkill /pid %%p /f >nul 2>&1
    echo ✅ 后端服务已停止 ^(PID: %%p^)
)

REM 验证服务停止
timeout /t 2 /nobreak >nul
netstat -ano | findstr ":8000\|:80" >nul 2>&1
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

REM 启动后端服务
echo 正在启动后端API服务...
cd /d "%BACKEND_DIR%"
start "ZWY Backend Service" /min cmd /k "uvicorn main:app --host 0.0.0.0 --port 8000"
echo ✅ 后端服务启动命令已执行

REM 等待后端服务启动
echo 等待后端服务启动...
timeout /t 8 /nobreak >nul

REM 验证后端服务
netstat -ano | findstr :8000 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 后端API服务启动成功 ^(端口:8000^)
) else (
    echo ❌ 后端API服务启动失败
    echo 请检查控制台输出或手动启动
    if not "%ACTION%"=="" exit /b 1
    pause
    goto :menu
)

REM 启动Nginx服务
echo.
echo 正在启动Nginx服务...
cd /d "%NGINX_DIR%"
start "ZWY Nginx Service" /min nginx.exe
echo ✅ Nginx服务启动命令已执行

REM 等待Nginx启动
timeout /t 5 /nobreak >nul

REM 验证Nginx服务
netstat -ano | findstr :80 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Nginx Web服务启动成功 ^(端口:80^)
) else (
    echo ❌ Nginx Web服务启动失败
    echo 请检查配置文件或手动启动
    if not "%ACTION%"=="" exit /b 1
    pause
    goto :menu
)

echo.
echo ====================================================================
echo                      🎉 服务启动完成！
echo ====================================================================
echo 📱 访问地址：
echo   本机访问: http://localhost
echo   内网访问: http://10.13.33.52
echo   API文档: http://localhost/docs
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

REM 备份数据库
if exist "%BACKEND_DIR%\zwy_project.db" (
    echo 正在备份数据库...
    copy "%BACKEND_DIR%\zwy_project.db" "%BACKUP_SUBDIR%\zwy_project_%TIMESTAMP%.db" >nul
    echo ✅ 数据库备份完成
) else (
    echo ❌ 数据库文件不存在
)

REM 备份配置文件
if exist "%BACKEND_DIR%\.env" (
    echo 正在备份环境配置...
    copy "%BACKEND_DIR%\.env" "%BACKUP_SUBDIR%\.env_%TIMESTAMP%" >nul
    echo ✅ 环境配置备份完成
) else (
    echo ⚠️  环境配置文件不存在
)

REM 备份Nginx配置
if exist "%NGINX_DIR%\conf\nginx.conf" (
    echo 正在备份Nginx配置...
    copy "%NGINX_DIR%\conf\nginx.conf" "%BACKUP_SUBDIR%\nginx_%TIMESTAMP%.conf" >nul
    echo ✅ Nginx配置备份完成
) else (
    echo ⚠️  Nginx配置文件不存在
)

echo.
echo ====================================================================
echo                      🎉 备份操作完成！
echo ====================================================================
echo 备份位置: %BACKUP_SUBDIR%
echo 备份时间: %TIMESTAMP%
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

echo 📋 维护流程：
echo 1. 停止所有服务
echo 2. 备份数据和配置  
echo 3. 清理过期文件
echo 4. 重新启动服务
echo 5. 系统健康检查
echo.

set /p "CONFIRM=确认执行完整维护? (Y/N): "
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

echo 正在执行系统健康检查...
timeout /t 10 /nobreak >nul
call :check_status

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
echo.
dir /b /od "%LOG_DIR%\maintenance_*.log" 2>nul | tail -n 5
echo.

set /p "VIEW_LOG=是否查看最新日志文件? (Y/N): "
if /i "%VIEW_LOG%"=="Y" (
    for /f %%f in ('dir /b /od "%LOG_DIR%\maintenance_*.log" 2^>nul ^| tail -n 1') do (
        echo.
        echo 正在查看: %%f
        echo ====================================================================
        type "%LOG_DIR%\%%f"
        echo ====================================================================
    )
)

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
echo   status      - 查看服务状态
echo   start       - 启动所有服务
echo   stop        - 停止所有服务  
echo   restart     - 重启所有服务
echo   backup      - 仅备份数据
echo   maintenance - 完整维护（停止→备份→清理→重启）
echo   help        - 显示此帮助信息
echo.
echo 【使用示例】
echo   %~nx0 status           # 查看服务状态
echo   %~nx0 restart          # 重启所有服务
echo   %~nx0 backup           # 仅执行备份
echo   %~nx0 maintenance      # 执行完整维护
echo.
echo 【交互模式】
echo   双击运行脚本或不带参数运行，进入交互式菜单
echo.
echo ====================================================================

if not "%ACTION%"=="" exit /b 0
pause
goto :menu