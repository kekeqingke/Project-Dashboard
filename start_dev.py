#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
开发环境启动脚本
自动清理端口并启动前后端服务
"""

import os
import sys
import time
import signal
import subprocess
import platform
from pathlib import Path

# 配置常量
BACKEND_PORT = 8000
FRONTEND_PORT = 5173
BACKEND_DIR = "backend"
FRONTEND_DIR = "frontend"

def is_windows():
    """检查是否为Windows系统"""
    return platform.system().lower() == "windows"

def kill_port(port):
    """杀死指定端口的进程"""
    try:
        if is_windows():
            # Windows系统
            result = subprocess.run(
                f'netstat -ano | findstr :{port}',
                shell=True, capture_output=True, text=True
            )
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                pids = set()
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 5 and f':{port}' in parts[1]:
                        pid = parts[-1]
                        if pid.isdigit():
                            pids.add(pid)
                
                for pid in pids:
                    try:
                        # 使用正确的taskkill语法，/T杀死进程树，/F强制终止
                        subprocess.run(f'taskkill /PID {pid} /T /F', shell=True, check=True)
                        print(f"✓ 已终止端口 {port} 上的进程树 (PID: {pid})")
                    except subprocess.CalledProcessError as e:
                        print(f"⚠ 无法终止进程 {pid}: {e}")
                        # 尝试强制杀死Python进程
                        try:
                            subprocess.run(f'taskkill /IM python.exe /F', shell=True, check=False)
                            print(f"✓ 强制终止了所有Python进程")
                        except:
                            pass
        else:
            # Linux/Mac系统
            result = subprocess.run(
                f'lsof -ti:{port}',
                shell=True, capture_output=True, text=True
            )
            if result.stdout:
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid.isdigit():
                        try:
                            subprocess.run(f'kill -9 {pid}', shell=True, check=True)
                            print(f"✓ 已终止端口 {port} 上的进程 (PID: {pid})")
                        except subprocess.CalledProcessError:
                            pass
    except Exception as e:
        print(f"⚠ 清理端口 {port} 时出错: {e}")

def check_python():
    """检查Python环境"""
    try:
        result = subprocess.run([sys.executable, '--version'], capture_output=True, text=True)
        print(f"✓ Python版本: {result.stdout.strip()}")
        return True
    except Exception as e:
        print(f"✗ Python检查失败: {e}")
        return False

def check_node():
    """检查Node.js环境"""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        print(f"✓ Node.js版本: {result.stdout.strip()}")
        return True
    except Exception as e:
        print(f"⚠ Node.js未安装或不在PATH中: {e}")
        return False

def install_backend_deps():
    """安装后端依赖"""
    backend_path = Path(BACKEND_DIR)
    if not backend_path.exists():
        print(f"✗ 后端目录 {BACKEND_DIR} 不存在")
        return False
    
    requirements_file = backend_path / "requirements.txt"
    if not requirements_file.exists():
        print(f"✗ requirements.txt 文件不存在: {requirements_file}")
        return False
    
    try:
        print("📦 检查后端依赖...")
        print(f"📂 工作目录: {backend_path.absolute()}")
        print(f"📄 requirements文件: {requirements_file.absolute()}")
        
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ], check=True, cwd=str(backend_path.absolute()))
        print("✓ 后端依赖安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 后端依赖安装失败: {e}")
        return False

def install_frontend_deps():
    """安装前端依赖"""
    frontend_path = Path(FRONTEND_DIR)
    if not frontend_path.exists():
        print(f"✗ 前端目录 {FRONTEND_DIR} 不存在")
        return False
    
    package_json = frontend_path / "package.json"
    if not package_json.exists():
        print(f"✗ package.json 文件不存在")
        return False
    
    node_modules = frontend_path / "node_modules"
    if node_modules.exists():
        print("✓ 前端依赖已存在，跳过安装")
        return True
    
    try:
        print("📦 安装前端依赖...")
        
        # 尝试不同的npm命令
        npm_commands = ['npm', 'npm.cmd']
        success = False
        
        for npm_cmd in npm_commands:
            try:
                subprocess.run([npm_cmd, 'install'], check=True, cwd=str(frontend_path.absolute()))
                success = True
                break
            except (FileNotFoundError, subprocess.CalledProcessError):
                continue
        
        if not success:
            raise FileNotFoundError("找不到npm命令或安装失败")
        
        print("✓ 前端依赖安装完成")
        return True
    except Exception as e:
        print(f"✗ 前端依赖安装失败: {e}")
        return False

def start_backend():
    """启动后端服务"""
    backend_path = Path(BACKEND_DIR)
    if not backend_path.exists():
        print(f"✗ 后端目录 {BACKEND_DIR} 不存在")
        return None
    
    try:
        print(f"🚀 启动后端服务 (端口: {BACKEND_PORT})...")
        process = subprocess.Popen([
            sys.executable, '-m', 'uvicorn', 
            'main:app', 
            '--host', '0.0.0.0',
            '--port', str(BACKEND_PORT),
            '--reload'
        ], cwd=backend_path)
        
        # 等待后端启动
        time.sleep(3)
        print("✓ 后端服务启动成功")
        return process
    except Exception as e:
        print(f"✗ 后端服务启动失败: {e}")
        return None

def start_frontend():
    """启动前端服务"""
    frontend_path = Path(FRONTEND_DIR)
    if not frontend_path.exists():
        print(f"✗ 前端目录 {FRONTEND_DIR} 不存在")
        return None
    
    try:
        print(f"🚀 启动前端服务 (端口: {FRONTEND_PORT})...")
        
        # 尝试不同的npm命令
        npm_commands = ['npm', 'npm.cmd']
        process = None
        
        for npm_cmd in npm_commands:
            try:
                process = subprocess.Popen([
                    npm_cmd, 'run', 'dev'
                ], cwd=str(frontend_path.absolute()))
                break
            except FileNotFoundError:
                continue
        
        if process is None:
            raise FileNotFoundError("找不到npm命令")
        
        # 等待前端启动
        time.sleep(3)
        print("✓ 前端服务启动成功")
        return process
    except Exception as e:
        print(f"✗ 前端服务启动失败: {e}")
        return None

def cleanup_processes(processes):
    """清理进程"""
    print("\n🔄 正在关闭服务...")
    for process in processes:
        if process and process.poll() is None:
            try:
                if is_windows():
                    process.terminate()
                    time.sleep(1)
                    if process.poll() is None:
                        process.kill()
                else:
                    process.send_signal(signal.SIGTERM)
                    time.sleep(1)
                    if process.poll() is None:
                        process.kill()
            except Exception as e:
                print(f"⚠ 进程清理时出错: {e}")

def main():
    """主函数"""
    print("=" * 60)
    print("🎯 ZWY项目开发环境启动脚本")
    print("=" * 60)
    
    # 检查环境
    if not check_python():
        sys.exit(1)
    
    node_available = check_node()
    
    # 清理端口
    print("\n🧹 清理占用的端口...")
    kill_port(BACKEND_PORT)
    kill_port(FRONTEND_PORT)
    
    # 安装依赖
    if not install_backend_deps():
        sys.exit(1)
    
    if node_available and not install_frontend_deps():
        print("⚠ 前端依赖安装失败，仅启动后端服务")
        node_available = False
    
    processes = []
    
    try:
        # 启动后端
        backend_process = start_backend()
        if backend_process:
            processes.append(backend_process)
        else:
            print("✗ 后端服务启动失败")
            sys.exit(1)
        
        # 启动前端
        if node_available:
            frontend_process = start_frontend()
            if frontend_process:
                processes.append(frontend_process)
            else:
                print("⚠ 前端服务启动失败，仅运行后端")
        
        # 显示访问信息
        print("\n" + "=" * 60)
        print("🎉 服务启动成功!")
        print(f"📡 后端API: http://localhost:{BACKEND_PORT}")
        if node_available and len(processes) > 1:
            print(f"🌐 前端界面: http://localhost:{FRONTEND_PORT}")
        print("📖 API文档: http://localhost:8000/docs")
        print("\n按 Ctrl+C 停止所有服务")
        print("=" * 60)
        
        # 等待用户中断
        while True:
            time.sleep(1)
            # 检查进程是否还在运行
            active_processes = [p for p in processes if p.poll() is None]
            if not active_processes:
                print("⚠ 所有服务已停止")
                break
    
    except KeyboardInterrupt:
        print("\n\n⏹ 接收到停止信号")
    
    finally:
        cleanup_processes(processes)
        print("✅ 所有服务已停止")

if __name__ == "__main__":
    main()