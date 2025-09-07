#!/usr/bin/env python3
"""
数据库迁移脚本：添加质量问题撤销和复验字段
用法：python migrate_add_revoke_fields.py
"""

import sqlite3
from datetime import datetime
import os

# 数据库文件路径
DB_PATH = "zwy_project.db"

def add_revoke_fields():
    """添加撤销和复验相关字段到quality_issues表"""
    
    if not os.path.exists(DB_PATH):
        print(f"错误：数据库文件 {DB_PATH} 不存在")
        return False
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='quality_issues'")
        if not cursor.fetchone():
            print("错误：quality_issues表不存在")
            return False
        
        # 检查字段是否已经存在
        cursor.execute("PRAGMA table_info(quality_issues)")
        columns = [column[1] for column in cursor.fetchall()]
        
        new_fields = {
            'revoked_by': 'INTEGER',
            'revoked_at': 'DATETIME',
            'reverified_by': 'INTEGER',
            'reverified_at': 'DATETIME'
        }
        
        # 添加缺失的字段
        for field_name, field_type in new_fields.items():
            if field_name not in columns:
                print(f"添加字段: {field_name}")
                cursor.execute(f"ALTER TABLE quality_issues ADD COLUMN {field_name} {field_type}")
            else:
                print(f"字段 {field_name} 已存在，跳过")
        
        # 更新状态字段的注释（SQLite不支持直接修改列注释，这里仅为文档目的）
        print("状态字段现在支持：待验收, 已验收, 需复验")
        
        conn.commit()
        conn.close()
        
        print("✅ 数据库迁移完成！")
        print("新增字段：")
        for field_name in new_fields:
            print(f"  - {field_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ 迁移失败：{e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def verify_migration():
    """验证迁移是否成功"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(quality_issues)")
        columns = cursor.fetchall()
        
        print("\n当前 quality_issues 表结构：")
        for column in columns:
            print(f"  {column[1]} {column[2]} {'NOT NULL' if column[3] else 'NULL'}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"验证失败：{e}")
        return False

if __name__ == "__main__":
    print("🚀 开始数据库迁移...")
    print("=" * 50)
    
    if add_revoke_fields():
        print("\n🔍 验证迁移结果...")
        verify_migration()
        print("\n✨ 迁移完成！现在可以使用撤销验收和复验功能了。")
    else:
        print("\n💥 迁移失败，请检查错误信息。")