#!/usr/bin/env python3
"""
数据库迁移脚本：添加预计交付时间字段到rooms表
"""

from sqlalchemy import create_engine, text
from database import SQLALCHEMY_DATABASE_URL
import os

def main():
    """添加expected_delivery_date字段到rooms表"""
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    try:
        with engine.connect() as connection:
            # 检查字段是否已存在
            result = connection.execute(text("""
                SELECT COUNT(*) as count 
                FROM pragma_table_info('rooms') 
                WHERE name = 'expected_delivery_date'
            """))
            
            count = result.fetchone()[0]
            
            if count == 0:
                # 添加字段
                connection.execute(text("""
                    ALTER TABLE rooms 
                    ADD COLUMN expected_delivery_date DATE DEFAULT NULL
                """))
                connection.commit()
                print("✅ 成功添加expected_delivery_date字段到rooms表")
            else:
                print("ℹ️  expected_delivery_date字段已存在，跳过迁移")
                
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        raise e
    
    print("🎉 数据库迁移完成")

if __name__ == "__main__":
    main()