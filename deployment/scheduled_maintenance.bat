@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ====================================================================
REM                    ZWY项目管理系统定时维护脚本
REM                   适用于凌晨3点自动维护任务
REM ====================================================================

set "PROJECT_DIR=%~dp0"
set "BACKEND_DIR=%PROJECT_DIR%backend"
set "NGINX_DIR=D:\nginx-1.28.0"
set "LOG_DIR=%PROJECT_DIR%maintenance_logs"
set "BACKUP_DIR=%PROJECT_DIR%backups"

REM 创建日志和备份目录
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

REM 设置日志文件名（包含时间戳）
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YYYY=%dt:~0,4%"
set "MM=%dt:~4,2%"
set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%"
set "MIN=%dt:~10,2%"
set "SS=%dt:~12,2%"
set "TIMESTAMP=%YYYY%-%MM%-%DD%_%HH%-%MIN%-%SS%"
set "LOG_FILE=%LOG_DIR%\maintenance_%TIMESTAMP%.log"

REM 开始维护日志
echo ====================================================================>> "%LOG_FILE%"
echo ZWY项目管理系统定时维护日志>> "%LOG_FILE%"
echo 维护时间: %YYYY%-%MM%-%DD% %HH%:%MIN%:%SS%>> "%LOG_FILE%"
echo ====================================================================>> "%LOG_FILE%"

echo 开始定时维护任务...
echo 开始定时维护任务...>> "%LOG_FILE%"

REM ====================================================================
REM 第1步：检查服务状态
REM ====================================================================
echo.
echo 1. 检查当前服务状态...
echo 1. 检查当前服务状态...>> "%LOG_FILE%"

REM 检查后端服务（端口8000）
netstat -ano | findstr :8000 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 后端服务运行中（端口8000）
    echo ✅ 后端服务运行中（端口8000）>> "%LOG_FILE%"
    set "BACKEND_RUNNING=1"
) else (
    echo ⚠️  后端服务未运行（端口8000）
    echo ⚠️  后端服务未运行（端口8000）>> "%LOG_FILE%"
    set "BACKEND_RUNNING=0"
)

REM 检查Nginx服务（端口80）
netstat -ano | findstr :80 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Nginx服务运行中（端口80）
    echo ✅ Nginx服务运行中（端口80）>> "%LOG_FILE%"
    set "NGINX_RUNNING=1"
) else (
    echo ⚠️  Nginx服务未运行（端口80）
    echo ⚠️  Nginx服务未运行（端口80）>> "%LOG_FILE%"
    set "NGINX_RUNNING=0"
)

REM ====================================================================
REM 第2步：优雅停止服务
REM ====================================================================
echo.
echo 2. 停止服务...
echo 2. 停止服务...>> "%LOG_FILE%"

REM 停止Nginx服务
if %NGINX_RUNNING% equ 1 (
    echo 正在停止Nginx服务...
    echo 正在停止Nginx服务...>> "%LOG_FILE%"
    cd /d "%NGINX_DIR%"
    nginx.exe -s quit
    timeout /t 3 /nobreak >nul
    echo ✅ Nginx服务已停止
    echo ✅ Nginx服务已停止>> "%LOG_FILE%"
)

REM 停止后端服务（通过进程ID）
if %BACKEND_RUNNING% equ 1 (
    echo 正在停止后端服务...
    echo 正在停止后端服务...>> "%LOG_FILE%"
    for /f "tokens=5" %%p in ('netstat -ano ^| findstr :8000') do (
        taskkill /pid %%p /f >nul 2>&1
        if !errorlevel! equ 0 (
            echo ✅ 后端服务已停止（PID: %%p）
            echo ✅ 后端服务已停止（PID: %%p）>> "%LOG_FILE%"
        )
    )
)

REM 等待服务完全停止
echo 等待服务完全停止...
timeout /t 5 /nobreak >nul

REM ====================================================================
REM 第3步：备份数据库和配置文件
REM ====================================================================
echo.
echo 3. 备份数据库和配置文件...
echo 3. 备份数据库和配置文件...>> "%LOG_FILE%"

set "BACKUP_SUBDIR=%BACKUP_DIR%\%YYYY%-%MM%-%DD%_%HH%-%MIN%"
if not exist "%BACKUP_SUBDIR%" mkdir "%BACKUP_SUBDIR%"

REM 备份数据库
if exist "%BACKEND_DIR%\zwy_project.db" (
    copy "%BACKEND_DIR%\zwy_project.db" "%BACKUP_SUBDIR%\zwy_project_%TIMESTAMP%.db" >nul
    echo ✅ 数据库备份完成: %BACKUP_SUBDIR%\zwy_project_%TIMESTAMP%.db
    echo ✅ 数据库备份完成: %BACKUP_SUBDIR%\zwy_project_%TIMESTAMP%.db>> "%LOG_FILE%"
) else (
    echo ❌ 数据库文件不存在: %BACKEND_DIR%\zwy_project.db
    echo ❌ 数据库文件不存在: %BACKEND_DIR%\zwy_project.db>> "%LOG_FILE%"
)

REM 备份配置文件
if exist "%BACKEND_DIR%\.env" (
    copy "%BACKEND_DIR%\.env" "%BACKUP_SUBDIR%\.env_%TIMESTAMP%" >nul
    echo ✅ 环境配置备份完成: %BACKUP_SUBDIR%\.env_%TIMESTAMP%
    echo ✅ 环境配置备份完成: %BACKUP_SUBDIR%\.env_%TIMESTAMP%>> "%LOG_FILE%"
) else (
    echo ⚠️  环境配置文件不存在: %BACKEND_DIR%\.env
    echo ⚠️  环境配置文件不存在: %BACKEND_DIR%\.env>> "%LOG_FILE%"
)

REM 备份Nginx配置
if exist "%NGINX_DIR%\conf\nginx.conf" (
    copy "%NGINX_DIR%\conf\nginx.conf" "%BACKUP_SUBDIR%\nginx_%TIMESTAMP%.conf" >nul
    echo ✅ Nginx配置备份完成: %BACKUP_SUBDIR%\nginx_%TIMESTAMP%.conf
    echo ✅ Nginx配置备份完成: %BACKUP_SUBDIR%\nginx_%TIMESTAMP%.conf>> "%LOG_FILE%"
)

REM ====================================================================
REM 第4步：清理过期备份（保留30天）
REM ====================================================================
echo.
echo 4. 清理过期备份文件（保留30天）...
echo 4. 清理过期备份文件（保留30天）...>> "%LOG_FILE%"

forfiles /p "%BACKUP_DIR%" /d -30 /c "cmd /c if @isdir==TRUE rmdir /s /q @path" 2>nul
if %errorlevel% equ 0 (
    echo ✅ 过期备份清理完成
    echo ✅ 过期备份清理完成>> "%LOG_FILE%"
) else (
    echo ℹ️  无过期备份需要清理
    echo ℹ️  无过期备份需要清理>> "%LOG_FILE%"
)

REM ====================================================================
REM 第5步：清理日志文件（保留7天）
REM ====================================================================
echo.
echo 5. 清理过期维护日志（保留7天）...
echo 5. 清理过期维护日志（保留7天）...>> "%LOG_FILE%"

forfiles /p "%LOG_DIR%" /d -7 /c "cmd /c del @path" 2>nul
if %errorlevel% equ 0 (
    echo ✅ 过期日志清理完成
    echo ✅ 过期日志清理完成>> "%LOG_FILE%"
) else (
    echo ℹ️  无过期日志需要清理
    echo ℹ️  无过期日志需要清理>> "%LOG_FILE%"
)

REM ====================================================================
REM 第6步：重新启动服务
REM ====================================================================
echo.
echo 6. 重新启动服务...
echo 6. 重新启动服务...>> "%LOG_FILE%"

REM 启动后端服务
echo 启动后端API服务...
echo 启动后端API服务...>> "%LOG_FILE%"
cd /d "%BACKEND_DIR%"
start "ZWY Backend Service" /min cmd /k "uvicorn main:app --host 0.0.0.0 --port 8000"
timeout /t 5 /nobreak >nul

REM 验证后端服务启动
netstat -ano | findstr :8000 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 后端服务启动成功（端口8000）
    echo ✅ 后端服务启动成功（端口8000）>> "%LOG_FILE%"
) else (
    echo ❌ 后端服务启动失败
    echo ❌ 后端服务启动失败>> "%LOG_FILE%"
)

REM 启动Nginx服务
echo 启动Nginx服务...
echo 启动Nginx服务...>> "%LOG_FILE%"
cd /d "%NGINX_DIR%"
start "ZWY Nginx Service" /min nginx.exe
timeout /t 3 /nobreak >nul

REM 验证Nginx服务启动
netstat -ano | findstr :80 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Nginx服务启动成功（端口80）
    echo ✅ Nginx服务启动成功（端口80）>> "%LOG_FILE%"
) else (
    echo ❌ Nginx服务启动失败
    echo ❌ Nginx服务启动失败>> "%LOG_FILE%"
)

REM ====================================================================
REM 第7步：服务健康检查
REM ====================================================================
echo.
echo 7. 服务健康检查...
echo 7. 服务健康检查...>> "%LOG_FILE%"

timeout /t 10 /nobreak >nul
echo 等待服务完全启动...

REM 检查系统是否可访问
curl -s -o nul -w "%%{http_code}" http://localhost/ | findstr "200" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 系统健康检查通过 - 网站可正常访问
    echo ✅ 系统健康检查通过 - 网站可正常访问>> "%LOG_FILE%"
) else (
    echo ❌ 系统健康检查失败 - 网站无法访问
    echo ❌ 系统健康检查失败 - 网站无法访问>> "%LOG_FILE%"
)

REM ====================================================================
REM 维护完成总结
REM ====================================================================
echo.
echo ====================================================================
echo                        🎉 定时维护完成！
echo ====================================================================
echo 维护时间：%YYYY%-%MM%-%DD% %HH%:%MIN%:%SS%
echo 备份位置：%BACKUP_SUBDIR%
echo 日志文件：%LOG_FILE%
echo.
echo 访问地址验证：
echo 🖥️  本机访问：http://localhost
echo 🌐 内网访问：http://10.13.33.52
echo ====================================================================

echo.>> "%LOG_FILE%"
echo ====================================================================>> "%LOG_FILE%"
echo 定时维护任务完成 - %YYYY%-%MM%-%DD% %HH%:%MIN%:%SS%>> "%LOG_FILE%"
echo 备份位置：%BACKUP_SUBDIR%>> "%LOG_FILE%"
echo ====================================================================>> "%LOG_FILE%"

echo.
echo 维护脚本执行完成，按任意键退出...
timeout /t 30 /nobreak >nul