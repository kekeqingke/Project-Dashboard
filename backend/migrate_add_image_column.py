"""
数据库迁移脚本：为communications表添加image字段
"""
import sqlite3
import os

def migrate_database():
    # 数据库文件路径
    db_path = "zwy_project.db"
    
    if not os.path.exists(db_path):
        print("数据库文件不存在，无需迁移")
        return
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查image字段是否已存在
        cursor.execute("PRAGMA table_info(communications);")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'image' in columns:
            print("image字段已存在，无需添加")
            return
        
        # 添加image字段
        print("正在为communications表添加image字段...")
        cursor.execute("ALTER TABLE communications ADD COLUMN image VARCHAR(255);")
        
        conn.commit()
        print("数据库迁移完成：已添加image字段")
        
    except Exception as e:
        print(f"数据库迁移失败: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()