#!/usr/bin/env python3
"""
数据库迁移脚本：为用户表添加初始密码相关字段
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from database import engine
from models import Base

def migrate_user_table():
    """为用户表添加新字段"""
    with engine.begin() as conn:
        try:
            # 检查字段是否已存在
            result = conn.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in result.fetchall()]
            
            # 添加 initial_password 字段
            if 'initial_password' not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN initial_password TEXT"))
                print("已添加 initial_password 字段")
            else:
                print("initial_password 字段已存在")
                
            # 添加 password_changed 字段
            if 'password_changed' not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN password_changed BOOLEAN DEFAULT 0"))
                print("已添加 password_changed 字段")
            else:
                print("password_changed 字段已存在")
                
            print("数据库迁移完成！")
            
        except Exception as e:
            print(f"迁移失败: {e}")
            raise

if __name__ == "__main__":
    print("开始数据库迁移...")
    migrate_user_table()