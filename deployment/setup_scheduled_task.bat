@echo off
chcp 65001 >nul

REM ====================================================================
REM                Windows任务计划程序配置脚本
REM              用于设置ZWY项目定时维护任务（凌晨3点）
REM ====================================================================

echo.
echo ====================================================================
echo                Windows定时维护任务配置向导
echo ====================================================================
echo.

echo 本脚本将创建Windows任务计划，实现以下功能：
echo ✅ 每天凌晨3:00自动执行维护
echo ✅ 自动停止服务 → 备份数据 → 重启服务
echo ✅ 清理过期文件和日志
echo ✅ 生成维护报告日志
echo.

REM 检查管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误：需要管理员权限才能创建任务计划
    echo.
    echo 请右键点击此脚本，选择"以管理员身份运行"
    echo.
    pause
    exit /b 1
)

echo ✅ 管理员权限检查通过
echo.

set "SCRIPT_PATH=%~dp0scheduled_maintenance.bat"
set "TASK_NAME=ZWY项目定时维护"

REM 检查维护脚本是否存在
if not exist "%SCRIPT_PATH%" (
    echo ❌ 错误：未找到维护脚本文件
    echo 请确保 scheduled_maintenance.bat 文件存在于：
    echo %SCRIPT_PATH%
    echo.
    pause
    exit /b 1
)

echo ✅ 维护脚本文件检查通过
echo 脚本位置：%SCRIPT_PATH%
echo.

REM 删除现有任务（如果存在）
echo 检查并删除现有任务计划...
schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if %errorlevel% equ 0 (
    echo 发现现有任务，正在删除...
    schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1
    echo ✅ 现有任务已删除
) else (
    echo ℹ️  未发现现有任务
)
echo.

REM 创建新的定时任务
echo 正在创建定时维护任务...
echo 任务名称：%TASK_NAME%
echo 执行时间：每天凌晨 03:00
echo 执行脚本：%SCRIPT_PATH%
echo.

schtasks /create ^
    /tn "%TASK_NAME%" ^
    /tr "\"%SCRIPT_PATH%\"" ^
    /sc daily ^
    /st 03:00 ^
    /ru "SYSTEM" ^
    /rl highest ^
    /f

if %errorlevel% equ 0 (
    echo ✅ 定时任务创建成功！
    echo.
    echo ====================================================================
    echo                        🎉 配置完成！
    echo ====================================================================
    echo.
    echo 📅 任务计划详情：
    echo ┌────────────────────────────────────────────────────┐
    echo │ 任务名称：ZWY项目定时维护                           │
    echo │ 执行时间：每天凌晨 03:00                           │
    echo │ 执行账户：SYSTEM（系统账户）                        │
    echo │ 权限级别：最高权限                                 │
    echo │ 脚本位置：%SCRIPT_PATH%
    echo └────────────────────────────────────────────────────┘
    echo.
    echo 🔧 维护内容：
    echo • 自动停止 Nginx 和后端服务
    echo • 备份数据库和配置文件
    echo • 清理过期备份（保留30天）
    echo • 清理过期日志（保留7天）
    echo • 重新启动所有服务
    echo • 执行健康检查
    echo • 生成详细维护日志
    echo.
    echo 📂 相关目录：
    echo • 备份目录：%~dp0backups\
    echo • 日志目录：%~dp0maintenance_logs\
    echo.
    echo ⚠️  重要提醒：
    echo 1. 系统会在每天凌晨3点自动执行维护
    echo 2. 维护期间服务会短暂中断（约1-2分钟）
    echo 3. 可以随时手动运行 scheduled_maintenance.bat 进行维护
    echo 4. 查看维护日志了解执行情况
    echo.
) else (
    echo ❌ 定时任务创建失败！
    echo.
    echo 可能的原因：
    echo 1. 脚本路径包含特殊字符
    echo 2. 权限不足
    echo 3. 任务计划程序服务未启动
    echo.
    echo 请检查以上问题后重新运行此脚本
    echo.
    pause
    exit /b 1
)

echo ====================================================================
echo                         管理命令参考
echo ====================================================================
echo.
echo 💡 常用任务管理命令：
echo.
echo 【查看任务状态】
echo schtasks /query /tn "ZWY项目定时维护"
echo.
echo 【立即执行任务】
echo schtasks /run /tn "ZWY项目定时维护"
echo.
echo 【停用任务】
echo schtasks /change /tn "ZWY项目定时维护" /disable
echo.
echo 【启用任务】
echo schtasks /change /tn "ZWY项目定时维护" /enable
echo.
echo 【删除任务】
echo schtasks /delete /tn "ZWY项目定时维护" /f
echo.
echo 【修改执行时间为凌晨2点】
echo schtasks /change /tn "ZWY项目定时维护" /st 02:00
echo.

echo ====================================================================
echo.
echo 🎯 下一步操作建议：
echo 1. 手动执行一次维护脚本测试：双击 scheduled_maintenance.bat
echo 2. 查看生成的日志文件确认功能正常
echo 3. 在Windows任务计划程序中确认任务已创建
echo 4. 可以修改执行时间适应你的维护时间窗口
echo.

pause