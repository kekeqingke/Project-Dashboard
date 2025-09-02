#!/usr/bin/env python3
"""
开发环境启动脚本
"""
import subprocess
import sys
import os
import time
from pathlib import Path

def run_command(cmd, cwd=None):
    """执行命令"""
    try:
        if isinstance(cmd, str):
            process = subprocess.Popen(cmd, shell=True, cwd=cwd)
        else:
            # 在Windows下，需要使用shell=True来执行npm命令
            if os.name == 'nt' and cmd[0] == 'npm':
                cmd_str = ' '.join(cmd)
                process = subprocess.Popen(cmd_str, shell=True, cwd=cwd)
            else:
                process = subprocess.Popen(cmd, cwd=cwd)
        return process
    except Exception as e:
        print(f"执行命令失败: {cmd}, 错误: {e}")
        return None

def main():
    print("=== ZWY项目开发环境启动 ===")
    
    # 检查Python依赖
    print("\n1. 检查后端依赖...")
    backend_dir = Path("backend")
    if not (backend_dir / "zwy_project.db").exists():
        print("初始化数据库...")
        init_process = run_command([sys.executable, "init_db.py"], cwd=backend_dir)
        if init_process:
            init_process.wait()
    
    # 启动后端
    print("\n2. 启动后端服务 (FastAPI)...")
    backend_process = run_command([sys.executable, "-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"], cwd=backend_dir)
    
    # 等待后端启动
    print("等待后端服务启动...")
    time.sleep(3)
    
    # 检查npm
    print("\n3. 检查前端依赖...")
    frontend_dir = Path("frontend")
    if not (frontend_dir / "node_modules").exists():
        print("安装前端依赖...")
        npm_install = run_command(["npm", "install"], cwd=frontend_dir)
        if npm_install:
            npm_install.wait()
    
    # 启动前端
    print("\n4. 启动前端服务 (Vue.js)...")
    frontend_process = run_command(["npm", "run", "dev"], cwd=frontend_dir)
    
    print("\n=== 启动完成 ===")
    print("后端服务: http://localhost:8000")
    print("API文档: http://localhost:8000/docs")
    print("前端服务: http://localhost:5173")
    print("\n默认账号:")
    print("管理员: admin / admin123")
    print("\n按 Ctrl+C 停止所有服务")
    
    try:
        # 等待用户中断
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在停止服务...")
        if backend_process:
            backend_process.terminate()
        if frontend_process:
            frontend_process.terminate()
        print("服务已停止")

if __name__ == "__main__":
    main()