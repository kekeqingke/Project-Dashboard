@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
echo.
echo ====================================================================
echo                     端口占用检查和解决工具
echo ====================================================================
echo.

set "REQUIRED_PORTS=8000 80"
set "PORT_CONFLICT=false"

echo 🔍 检查系统必需端口状态...
echo.

for %%p in (%REQUIRED_PORTS%) do (
    echo 检查端口 %%p...
    
    REM 检查端口是否被占用
    for /f "tokens=2,5" %%a in ('netstat -ano ^| findstr ":%%p "') do (
        set "LOCAL_ADDR=%%a"
        set "PID=%%b"
        
        REM 只关心监听状态的端口
        echo !LOCAL_ADDR! | findstr ":%%p" >nul
        if !errorlevel! equ 0 (
            echo ❌ 端口 %%p 被占用
            echo    本地地址: !LOCAL_ADDR!
            echo    进程 PID: !PID!
            
            REM 获取进程名
            for /f "tokens=1" %%n in ('tasklist /fi "pid eq !PID!" /fo csv /nh 2^>nul ^| findstr /v "INFO:"') do (
                set "PROCESS_NAME=%%n"
                set "PROCESS_NAME=!PROCESS_NAME:"=!"
                echo    进程名称: !PROCESS_NAME!
            )
            
            set "PORT_CONFLICT=true"
            echo.
            
            REM 提供解决方案
            if "%%p"=="8000" (
                echo 💡 解决方案：
                echo    1. 如果是旧的后端服务，运行: taskkill /pid !PID! /f
                echo    2. 如果是其他应用，请手动关闭或更换端口
                echo    3. 确认是否为ZWY后端服务：检查进程是否为 python.exe 或 uvicorn
                set /p "KILL_8000=是否结束占用端口8000的进程 !PID!? (Y/N): "
                if /i "!KILL_8000!"=="Y" (
                    taskkill /pid !PID! /f >nul 2>&1
                    if !errorlevel! equ 0 (
                        echo ✅ 进程 !PID! 已结束
                        timeout /t 2 /nobreak >nul
                    ) else (
                        echo ❌ 结束进程失败，可能需要管理员权限
                    )
                )
            )
            
            if "%%p"=="80" (
                echo 💡 解决方案：
                echo    1. 如果是旧的Nginx服务，运行: taskkill /pid !PID! /f  
                echo    2. 如果是IIS或Apache，请先停止相应服务
                echo    3. 如果是其他Web服务器，请手动关闭
                set /p "KILL_80=是否结束占用端口80的进程 !PID!? (Y/N): "
                if /i "!KILL_80!"=="Y" (
                    taskkill /pid !PID! /f >nul 2>&1
                    if !errorlevel! equ 0 (
                        echo ✅ 进程 !PID! 已结束
                        timeout /t 2 /nobreak >nul
                    ) else (
                        echo ❌ 结束进程失败，可能需要管理员权限
                    )
                )
            )
            
            echo ────────────────────────────────────────────────────
        )
    )
)

REM 重新检查端口状态
echo.
echo 🔄 重新检查端口状态...
set "FINAL_CHECK=true"

for %%p in (%REQUIRED_PORTS%) do (
    netstat -ano | findstr ":%%p " >nul 2>&1
    if !errorlevel! equ 0 (
        echo ❌ 端口 %%p 仍被占用
        set "FINAL_CHECK=false"
    ) else (
        echo ✅ 端口 %%p 可用
    )
)

echo.
echo ====================================================================
if "%FINAL_CHECK%"=="true" (
    echo                   ✅ 端口检查通过
    echo ====================================================================
    echo.
    echo 🎉 所有必需端口均可用，可以启动服务！
    echo.
    set /p "START_SERVICES=是否立即启动服务? (Y/N): "
    if /i "!START_SERVICES!"=="Y" (
        echo 启动服务中...
        call "%~dp0service_manager.bat" start
    )
) else (
    echo                   ❌ 仍有端口冲突
    echo ====================================================================
    echo.
    echo ⚠️  部分端口仍被占用，请手动解决冲突后再启动服务
    echo.
    echo 🛠️  手动解决步骤：
    echo 1. 使用任务管理器结束占用端口的进程
    echo 2. 或重启计算机清除所有进程
    echo 3. 重新运行此脚本确认端口可用
    echo 4. 运行 service_manager.bat start 启动服务
)

echo.
echo 💡 提示：
echo • 端口 8000: ZWY后端API服务
echo • 端口 80:   Nginx Web服务器
echo • 如果问题持续，请检查是否有服务设置为开机自启
echo ====================================================================
echo.

pause