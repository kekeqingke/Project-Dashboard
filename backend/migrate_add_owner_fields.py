#!/usr/bin/env python3
"""
数据库迁移脚本：为customers表添加第二户主字段
添加字段：second_name, second_phone
"""

import sqlite3
import os

def migrate_add_owner_fields():
    db_path = "zwy_project.db"
    
    if not os.path.exists(db_path):
        print(f"数据库文件 {db_path} 不存在")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(customers)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # 添加 second_name 字段
        if 'second_name' not in columns:
            cursor.execute("ALTER TABLE customers ADD COLUMN second_name TEXT")
            print("✓ 已添加 second_name 字段")
        else:
            print("- second_name 字段已存在")
            
        # 添加 second_phone 字段
        if 'second_phone' not in columns:
            cursor.execute("ALTER TABLE customers ADD COLUMN second_phone TEXT")
            print("✓ 已添加 second_phone 字段")
        else:
            print("- second_phone 字段已存在")
        
        conn.commit()
        print("✓ 数据库迁移完成")
        return True
        
    except Exception as e:
        print(f"✗ 迁移失败: {e}")
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("开始数据库迁移...")
    success = migrate_add_owner_fields()
    if success:
        print("迁移成功！")
    else:
        print("迁移失败！")