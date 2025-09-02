#!/usr/bin/env python3

import os
import sys
from sqlalchemy import create_engine, text

# 获取环境变量，如果没有设置则使用默认值
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./zwy_project.db')

def main():
    try:
        engine = create_engine(DATABASE_URL)
        
        # 添加信件状态字段
        with engine.connect() as conn:
            # 检查是否已经存在 letter_status 字段
            result = conn.execute(text("PRAGMA table_info(rooms)")).fetchall()
            columns = [row[1] for row in result]
            
            if 'letter_status' not in columns:
                print("添加 letter_status 字段...")
                conn.execute(text("ALTER TABLE rooms ADD COLUMN letter_status VARCHAR DEFAULT '无'"))
                conn.commit()
                print("letter_status 字段添加成功")
            else:
                print("letter_status 字段已存在")
                
            # 检查是否已经存在 pre_leakage 字段
            if 'pre_leakage' not in columns:
                print("添加 pre_leakage 字段...")
                conn.execute(text("ALTER TABLE rooms ADD COLUMN pre_leakage VARCHAR DEFAULT '无'"))
                conn.commit()
                print("pre_leakage 字段添加成功")
            else:
                print("pre_leakage 字段已存在")
                
        print("数据库迁移完成！")
        
    except Exception as e:
        print(f"迁移失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()