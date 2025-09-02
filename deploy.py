#!/usr/bin/env python3
"""
生产环境部署脚本
"""
import subprocess
import sys
import os
import shutil
from pathlib import Path

def run_command(cmd, cwd=None):
    """执行命令"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"命令执行失败: {cmd}")
            print(f"错误信息: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"执行命令失败: {cmd}, 错误: {e}")
        return False

def build_frontend():
    """构建前端"""
    print("构建前端应用...")
    frontend_dir = Path("frontend")
    
    if not run_command("npm install", cwd=frontend_dir):
        return False
        
    if not run_command("npm run build", cwd=frontend_dir):
        return False
        
    # 移动构建文件到后端静态目录
    dist_dir = frontend_dir / "dist"
    static_dir = Path("backend") / "static"
    
    if static_dir.exists():
        shutil.rmtree(static_dir)
    
    shutil.copytree(dist_dir, static_dir)
    print("✅ 前端构建完成")
    return True

def setup_production_backend():
    """设置生产环境后端"""
    print("设置生产环境后端...")
    backend_dir = Path("backend")
    
    # 创建生产环境配置
    prod_config = """
# 生产环境配置
SECRET_KEY = "your-super-secret-key-change-this-in-production"
DATABASE_URL = "sqlite:///./zwy_project_prod.db"
UPLOAD_DIR = "./uploads"
"""
    
    with open(backend_dir / "config_prod.py", "w", encoding="utf-8") as f:
        f.write(prod_config)
        
    print("✅ 生产环境后端设置完成")
    return True

def create_docker_compose_prod():
    """创建生产环境Docker配置"""
    print("创建生产环境Docker配置...")
    
    docker_compose_prod = """version: '3.8'

services:
  web:
    build: .
    ports:
      - "80:8000"
    volumes:
      - ./data:/app/data
      - ./uploads:/app/uploads
    environment:
      - PYTHONPATH=/app
      - ENV=production
    restart: unless-stopped

volumes:
  data:
  uploads:
"""

    with open("docker-compose.prod.yml", "w") as f:
        f.write(docker_compose_prod)
    
    # 创建生产环境Dockerfile
    dockerfile_prod = """FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# 复制并安装Python依赖
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY backend/ ./
COPY frontend/dist/ ./static/

# 创建必要目录
RUN mkdir -p uploads data

# 初始化数据库
RUN python init_db.py

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

    with open("Dockerfile.prod", "w") as f:
        f.write(dockerfile_prod)
        
    print("✅ Docker生产环境配置创建完成")
    return True

def main():
    print("=== ZWY项目生产环境部署 ===")
    
    # 检查Node.js
    if not shutil.which("npm"):
        print("❌ 未找到npm，请先安装Node.js")
        return
        
    # 检查Docker
    if not shutil.which("docker"):
        print("❌ 未找到docker，请先安装Docker")
        return
    
    try:
        # 构建前端
        if not build_frontend():
            return
            
        # 设置生产环境后端
        if not setup_production_backend():
            return
            
        # 创建Docker配置
        if not create_docker_compose_prod():
            return
            
        print("\n=== 部署完成 ===")
        print("生产环境部署文件已准备就绪:")
        print("1. docker-compose.prod.yml - 生产环境Docker编排")
        print("2. Dockerfile.prod - 生产环境Docker镜像")
        print("3. backend/static/ - 前端构建文件")
        print("\n启动生产环境:")
        print("docker-compose -f docker-compose.prod.yml up -d --build")
        print("\n系统将在 http://localhost 访问")
        
    except Exception as e:
        print(f"❌ 部署过程中出现错误: {e}")

if __name__ == "__main__":
    main()