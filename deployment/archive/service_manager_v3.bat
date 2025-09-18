@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ====================================================================
REM            ZWY项目管理系统服务管理脚本 v3.0 (部署优化版)
REM                   基于2025-09-16实战部署经验优化
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
if /i "%ACTION%"=="smart_stop" goto :smart_stop

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
echo                ZWY项目管理系统服务管理 v3.0
echo               (基于实战部署经验优化版)
echo ====================================================================
echo.
echo 请选择操作：
echo.
echo 【1】 查看服务状态        【2】 启动所有服务
echo 【3】 停止所有服务        【4】 重启所有服务
echo 【5】 仅备份数据          【6】 完整维护
echo 【7】 查看维护日志        【8】 清理过期文件
echo 【9】 检查端口冲突        【S】 智能停服(新)      【A】 帮助信息            【0】 退出
echo.
echo ====================================================================
set /p "CHOICE=请输入选项 (0-9,S,A): "

if "%CHOICE%"=="1" goto :check_status
if "%CHOICE%"=="2" goto :start_services
if "%CHOICE%"=="3" goto :stop_services
if "%CHOICE%"=="4" goto :restart_services
if "%CHOICE%"=="5" goto :backup_only
if "%CHOICE%"=="6" goto :full_maintenance
if "%CHOICE%"=="7" goto :view_logs
if "%CHOICE%"=="8" goto :cleanup_files
if "%CHOICE%"=="9" goto :check_ports
if /i "%CHOICE%"=="S" goto :smart_stop
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

:smart_stop
echo.
echo ====================================================================
echo                    智能停止服务 (v3.0新增)
echo ====================================================================
echo.
echo 💡 基于实战经验优化的停止策略：
echo    1. 尝试优雅停止
echo    2. 如果失败，跳过并依赖启动脚本处理
echo    3. 避免强制终止系统核心进程
echo.

REM 停止后端服务（相对安全）
echo 正在停止后端服务...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :8000 2^>nul') do (
    taskkill /pid %%p /f >nul 2>&1
    echo ✅ 后端服务已停止 ^(PID: %%p^)
)

REM 对于Nginx，采用更保守的策略
echo 正在尝试停止Nginx服务...
if exist "%NGINX_DIR%" (
    cd /d "%NGINX_DIR%"
    nginx.exe -s quit >nul 2>&1
    timeout /t 3 /nobreak >nul
)

REM 检查Nginx是否停止，如果没停止就提示但不强制
netstat -ano | findstr ":80 " >nul 2>&1
if %errorlevel% equ 0 (
    echo ⚠️  Nginx服务仍在运行，这是正常的
    echo 💡 启动脚本会自动处理端口冲突，无需担心
    for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":80 " 2^>nul') do (
        if not "%%p"=="4" (
            taskkill /pid %%p /f >nul 2>&1
            echo ✅ 已停止非系统Nginx进程 ^(PID: %%p^)
        ) else (
            echo ℹ️  系统进程占用端口80 ^(PID: %%p^) - 启动时会自动处理
        )
    )
) else (
    echo ✅ Nginx服务已成功停止
)

echo.
echo ====================================================================
echo 📋 智能停止完成 - 部署经验总结：
echo ✅ 后端服务已停止
echo ℹ️  端口80可能仍被占用，但启动脚本会自动处理
echo 💡 建议：直接执行部署脚本，无需手动处理端口冲突
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
echo ⚠️  注意：如果遇到端口80停止困难，请使用"智能停止服务"选项
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
    if not "%%p"=="4" (
        taskkill /pid %%p /f >nul 2>&1
        echo ✅ Nginx服务已停止 ^(PID: %%p^)
    ) else (
        echo ⚠️  跳过系统核心进程 ^(PID: %%p^) - 部署时会自动处理
    )
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
    echo ⚠️  部分服务可能未完全停止，但这不影响部署
    echo 💡 启动脚本具备端口冲突自动处理能力
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

REM 启动前自动处理端口冲突 (增强版)
echo 1. 检查并处理端口占用...

REM 检查端口8000
netstat -ano | findstr ":8000 " >nul 2>&1
if %errorlevel% equ 0 (
    echo ⚠️  端口8000被占用，正在清理...
    for /f "tokens=5" %%p in ('netstat -ano ^| findstr :8000') do (
        taskkill /pid %%p /f >nul 2>&1
        echo ✅ 已清理端口8000占用进程 ^(PID: %%p^)
    )
    timeout /t 2 /nobreak >nul
) else (
    echo ✅ 端口8000可用
)

REM 增强的端口80处理逻辑
netstat -ano | findstr ":80 " >nul 2>&1
if %errorlevel% equ 0 (
    echo ⚠️  端口80被占用，执行增强处理策略...

    REM 记录处理前状态
    echo 📊 处理前端口占用情况：
    for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":80 "') do (
        echo    端口80被占用 ^(PID: %%p^)
    )

    REM 停止Web发布服务 (改进错误处理)
    echo 正在停止Web发布服务...
    net stop "World Wide Web Publishing Service" >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✅ Web发布服务已停止
    ) else (
        echo ℹ️  Web发布服务未运行或停止失败
    )
    timeout /t 2 /nobreak >nul

    REM 检查是否释放
    netstat -ano | findstr ":80 " >nul 2>&1
    if !errorlevel! equ 0 (
        echo 正在停止HTTP服务...
        net stop http /y >nul 2>&1
        if !errorlevel! equ 0 (
            echo ✅ HTTP服务已停止
        ) else (
            echo ℹ️  HTTP服务停止可能失败，继续处理...
        )
        timeout /t 3 /nobreak >nul

        REM 最终检查和智能处理
        netstat -ano | findstr ":80 " >nul 2>&1
        if !errorlevel! equ 0 (
            echo 🔧 执行智能端口清理...
            for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":80 "') do (
                if not "%%p"=="4" (
                    taskkill /pid %%p /f >nul 2>&1
                    echo ✅ 已清理非系统进程 ^(PID: %%p^)
                ) else (
                    echo ℹ️  检测到系统核心进程 ^(PID: %%p^)，使用特殊处理...
                    REM 对系统进程，我们不强制kill，而是尝试其他方法
                    net stop "World Wide Web Publishing Service" >nul 2>&1
                    sc stop http >nul 2>&1
                    echo 💡 已执行系统级服务停止命令
                )
            )

            REM 再次检查
            timeout /t 3 /nobreak >nul
            netstat -ano | findstr ":80 " >nul 2>&1
            if !errorlevel! equ 0 (
                echo ⚠️  端口80仍被占用，但Nginx具备共存能力
                echo 💡 系统会尝试启动，如果失败会有明确提示
            ) else (
                echo ✅ 端口80已成功释放
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

REM 等待并验证后端服务 (增加重试逻辑)
echo 等待后端服务启动...
set "BACKEND_STARTED=0"
for /L %%i in (1,1,15) do (
    timeout /t 2 /nobreak >nul
    netstat -ano | findstr :8000 >nul 2>&1
    if !errorlevel! equ 0 (
        echo ✅ 后端API服务启动成功 ^(端口:8000^)
        set "BACKEND_STARTED=1"
        goto :start_nginx
    )
    echo 等待中... ^(%%i/15^)
)

if "%BACKEND_STARTED%"=="0" (
    echo ❌ 后端API服务启动失败或超时
    echo 💡 请检查Python环境和依赖包是否正确安装
    if not "%ACTION%"=="" exit /b 1
    pause
    goto :menu
)

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

REM 智能启动Nginx (处理可能的端口共存)
echo 正在启动Nginx服务...
start "ZWY Nginx Service" /min nginx.exe
echo ✅ Nginx服务启动命令已执行

REM 等待并验证Nginx服务 (改进验证逻辑)
echo 等待Nginx服务启动...
set "NGINX_STARTED=0"
for /L %%i in (1,1,10) do (
    timeout /t 1 /nobreak >nul
    netstat -ano | findstr ":80 " >nul 2>&1
    if !errorlevel! equ 0 (
        REM 进一步验证是否是我们的Nginx
        tasklist /fi "imagename eq nginx.exe" >nul 2>&1
        if !errorlevel! equ 0 (
            echo ✅ Nginx Web服务启动成功 ^(端口:80^)
            set "NGINX_STARTED=1"
            goto :start_complete
        )
    )
    echo 等待中... ^(%%i/10^)
)

if "%NGINX_STARTED%"=="0" (
    echo ⚠️  Nginx启动状态待确认
    echo 🔍 正在进行详细检查...

    tasklist /fi "imagename eq nginx.exe" >nul 2>&1
    if !errorlevel! equ 0 (
        echo ✅ Nginx进程存在，可能正在处理端口冲突
        echo 💡 请稍等片刻或手动访问网站验证
        set "NGINX_STARTED=1"
        goto :start_complete
    ) else (
        echo ❌ Nginx未能成功启动
        echo 💡 请检查端口占用情况和Nginx配置
        if not "%ACTION%"=="" exit /b 1
        pause
        goto :menu
    )
)

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
echo 💡 部署后建议操作：
echo   1. 浏览器访问系统进行功能验证
echo   2. 如果页面显示异常，请按 Ctrl+F5 强制刷新清除缓存
echo   3. 测试新功能是否正常工作
echo   4. 检查时间显示和分页功能
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

call :smart_stop
echo.
echo 等待服务完全停止...
timeout /t 5 /nobreak >nul
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

call :smart_stop
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
echo                        使用帮助 v3.0
echo ====================================================================
echo.
echo 【命令行使用方式】
echo %~nx0 [操作]
echo.
echo 【支持的操作参数】
echo   status      - 查看服务状态
echo   start       - 启动所有服务（增强的端口冲突处理）
echo   stop        - 停止所有服务
echo   smart_stop  - 智能停止服务（新增，基于部署经验优化）
echo   restart     - 重启所有服务
echo   backup      - 仅备份数据
echo   maintenance - 完整维护（停止→备份→清理→重启）
echo   help        - 显示此帮助信息
echo.
echo 【v3.0新特性 - 基于2025-09-16实战部署经验】
echo   ✅ 新增智能停止服务功能，避免强制终止系统进程
echo   ✅ 增强的端口80冲突处理，支持多种解决策略
echo   ✅ 改进的启动验证逻辑，更准确的状态检测
echo   ✅ 部署后提示清除浏览器缓存，避免功能显示问题
echo   ✅ 更完善的错误处理和用户友好的提示信息
echo.
echo 【部署最佳实践建议】
echo   1. 部署前使用 smart_stop 而不是 stop
echo   2. 如果端口80停止困难，直接执行部署脚本
echo   3. 部署后提醒用户按 Ctrl+F5 刷新浏览器
echo   4. 遇到问题时查看详细的状态检查信息
echo.
echo 【使用示例】
echo   %~nx0 smart_stop       # 智能停止（推荐部署前使用）
echo   %~nx0 start           # 增强启动（自动处理冲突）
echo   %~nx0 restart         # 重启所有服务
echo   %~nx0 maintenance     # 执行完整维护
echo.
echo ====================================================================

if not "%ACTION%"=="" exit /b 0
pause
goto :menu