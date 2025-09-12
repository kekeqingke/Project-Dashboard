@echo off
chcp 65001 >nul
title ZWY项目 - 后端API服务
echo.
echo ====================================================================
echo                    ZWY项目管理系统 - 后端API服务
echo ====================================================================
echo.
echo 正在启动后端服务...
cd /d "%~dp0backend"
echo 当前目录：%CD%
echo 启动命令：uvicorn main:app --host 0.0.0.0 --port 8000
echo.
echo ⚠️  服务启动后请不要关闭此窗口
echo 💡 如需停止服务，请按 Ctrl+C
echo.
uvicorn main:app --host 0.0.0.0 --port 8000
echo.
echo 后端服务已停止
pause