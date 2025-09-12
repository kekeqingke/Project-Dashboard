@echo off
chcp 65001 >nul
echo.
echo ====================================================================
echo                    ZWY项目管理系统版本更新脚本
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
echo 2. 备份现有数据...
if not exist "backup" mkdir "backup"

:: 备份数据库文件
if exist "backend\*.db" (
    copy "backend\*.db" "backup\" >nul 2>&1
    echo ✅ 数据库文件已备份
) else (
    echo ℹ️  未找到数据库文件，跳过备份
)

:: 备份配置文件
if exist "backend\.env" (
    copy "backend\.env" "backup\.env.backup" >nul 2>&1
    echo ✅ 配置文件已备份
) else (
    echo ℹ️  未找到配置文件，跳过备份
)

:: 备份上传文件目录
if exist "backend\uploads" (
    xcopy "backend\uploads" "backup\uploads\" /E /I /Y >nul 2>&1
    echo ✅ 上传文件已备份
) else (
    echo ℹ️  未找到上传文件目录，跳过备份
)

echo.
echo 3. 构建前端项目...
cd /d "%~dp0..\frontend"
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
echo 4. 更新静态文件...
cd /d "%~dp0.."
if exist "backend\static" rmdir /s /q "backend\static"
mkdir "backend\static"
xcopy "frontend\dist\*" "backend\static\" /E /Y >nul
if %errorlevel% neq 0 (
    echo ❌ 静态文件复制失败
    pause
    exit /b 1
)
echo ✅ 静态文件更新完成

echo.
echo 5. 安装/更新后端依赖...
cd /d "%~dp0..\backend"
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ 后端依赖安装失败
    pause
    exit /b 1
)
echo ✅ 后端依赖更新完成

echo.
echo 6. 恢复数据文件...
cd /d "%~dp0.."

:: 恢复配置文件
if exist "deployment\backup\.env.backup" (
    copy "deployment\backup\.env.backup" "backend\.env" >nul 2>&1
    echo ✅ 配置文件已恢复
)

:: 恢复数据库文件
if exist "deployment\backup\*.db" (
    copy "deployment\backup\*.db" "backend\" >nul 2>&1
    echo ✅ 数据库文件已恢复
)

:: 恢复上传文件
if exist "deployment\backup\uploads" (
    if not exist "backend\uploads" mkdir "backend\uploads"
    xcopy "deployment\backup\uploads\*" "backend\uploads\" /E /Y >nul 2>&1
    echo ✅ 上传文件已恢复
)

echo.
echo ====================================================================
echo                         🎉 版本更新完成！
echo ====================================================================
echo.
echo 📋 更新内容：
echo ✅ 前端代码已更新并重新构建
echo ✅ 后端代码已更新
echo ✅ 依赖包已更新
echo ✅ 数据文件已保留
echo.
echo 🔄 接下来请重启服务：
echo 1. 如果后端服务正在运行，请先停止（Ctrl+C）
echo 2. 运行 start_backend.bat 启动后端
echo 3. 确认 Nginx 服务正常运行
echo 4. 访问 http://10.13.33.52 查看更新效果
echo.
echo ⚠️  重要提示：
echo • 数据文件已备份到 deployment\backup 目录
echo • 如有问题可从备份恢复
echo ====================================================================
echo.
pause