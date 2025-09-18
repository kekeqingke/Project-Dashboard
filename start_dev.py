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
                    # 跳过系统进程 (PID 0-10)
                    if int(pid) <= 10:
                        continue
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

def reset_admin_password():
    """重置管理员密码"""
    backend_path = Path(BACKEND_DIR)
    reset_script = backend_path / "reset_admin_password.py"
    
    if not reset_script.exists():
        print("⚠️  管理员密码重置脚本不存在")
        return None
    
    try:
        print("🔐 重置管理员密码...")
        # 自动选择生成随机密码（选项1）
        result = subprocess.run([
            sys.executable, 'reset_admin_password.py'
        ], cwd=str(backend_path.absolute()), input='1\ny\n', 
          text=True, capture_output=True)
        
        if result.returncode == 0:
            print("✅ 管理员密码重置成功")
            
            # 从输出中提取新密码
            lines = result.stdout.split('\n')
            new_password = None
            for line in lines:
                if "🔑 自动生成的新密码：" in line:
                    new_password = line.split("：")[-1].strip()
                    break
            
            if new_password:
                print("\n" + "="*50)
                print("🔑 新的管理员登录信息")
                print("="*50)
                print(f"👤 用户名：admin")
                print(f"🔑 新密码：{new_password}")
                print("⚠️  请妥善保管新密码")
                print("="*50 + "\n")
                return new_password
            else:
                print("⚠️  无法获取新密码，请查看上方输出")
                return "重置成功但无法获取密码"
        else:
            print(f"✗ 管理员密码重置失败: {result.stderr}")
            return None
    except Exception as e:
        print(f"✗ 运行密码重置脚本时出错: {e}")
        return None

def check_security_config():
    """检查和初始化安全配置"""
    backend_path = Path(BACKEND_DIR)
    env_file = backend_path / ".env"
    init_db_file = backend_path / "init_db.py"
    
    print("🔐 检查安全配置...")
    
    if not init_db_file.exists():
        print(f"✗ 初始化脚本不存在: {init_db_file}")
        return False, None
    
    # 检查是否需要运行初始化
    needs_init = False
    if not env_file.exists():
        print("⚠️  未找到 .env 配置文件")
        needs_init = True
    
    # 检查数据库是否存在
    db_file = backend_path / "zwy_project.db"
    if not db_file.exists():
        print("⚠️  数据库文件不存在")
        needs_init = True
    
    admin_password = None
    
    if needs_init:
        try:
            print("🚀 正在运行数据库初始化...")
            result = subprocess.run([
                sys.executable, 'init_db.py'
            ], cwd=str(backend_path.absolute()), capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ 数据库初始化完成")
                # 显示输出中的重要信息
                if "临时密码" in result.stdout:
                    print("\n" + "="*50)
                    print("🔑 重要：管理员登录信息")
                    print("="*50)
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if "用户名：" in line or "临时密码：" in line or "⚠️" in line:
                            print(line)
                            if "临时密码：" in line:
                                admin_password = line.split("：")[-1].strip()
                    print("="*50 + "\n")
                return True, admin_password
            else:
                print(f"✗ 数据库初始化失败: {result.stderr}")
                return False, None
        except Exception as e:
            print(f"✗ 运行初始化脚本时出错: {e}")
            return False, None
    else:
        print("✓ 安全配置已存在")
        
        # 询问是否重置管理员密码
        print("\n🔄 是否需要重置管理员密码？")
        print("1. 是 - 生成新的随机密码")
        print("2. 否 - 使用现有密码")
        
        try:
            # 在自动化脚本中，默认选择重置密码以确保用户知道登录凭据
            choice = input("\n请选择 (1/2，默认选择1): ").strip()
            if choice == '' or choice == '1':
                admin_password = reset_admin_password()
                if admin_password:
                    return True, admin_password
            elif choice == '2':
                print("✓ 保持现有密码不变")
                # 尝试从.env文件读取密码
                try:
                    with open(env_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.startswith('ADMIN_PASSWORD='):
                                admin_password = line.split('=', 1)[1].strip()
                                print(f"📖 从.env文件读取到管理员密码：{admin_password}")
                                break
                except Exception as e:
                    print(f"⚠️  无法读取.env文件中的密码: {e}")
                return True, admin_password
            else:
                print("❌ 无效选择，保持现有密码")
                return True, None
        except KeyboardInterrupt:
            print("\n❌ 用户取消操作")
            return True, None
        except Exception as e:
            print(f"⚠️  输入处理出错: {e}")
            return True, None

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
    
    # 检查安全配置
    config_ok, admin_password = check_security_config()
    if not config_ok:
        print("✗ 安全配置检查失败")
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
        print("\n👤 管理员账号: admin")
        if admin_password:
            print(f"🔑 管理员密码: {admin_password}")
        else:
            print("🔑 密码信息: 查看上方初始化输出或 backend/.env 文件")
        print("\n⚠️  首次登录建议立即修改密码")
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