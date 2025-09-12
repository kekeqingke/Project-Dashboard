"""
应用房间表的唯一性约束
此脚本用于在现有数据库上添加唯一性约束
"""

import sqlite3
from database import engine
from sqlalchemy import text

def apply_unique_constraint():
    """为rooms表添加唯一性约束"""
    
    print("开始为rooms表添加唯一性约束...")
    
    try:
        # 使用SQLAlchemy执行SQL命令
        with engine.connect() as connection:
            # 检查是否已存在唯一性约束
            result = connection.execute(text("""
                SELECT sql FROM sqlite_master 
                WHERE type='table' AND name='rooms'
            """))
            
            table_sql = result.fetchone()[0]
            
            if '_building_room_uc' in table_sql:
                print("✅ 唯一性约束已存在，无需重复添加")
                return True
            
            print("📋 当前rooms表结构中没有唯一性约束，需要重建表...")
            
            # 重建表结构以添加唯一性约束
            # 1. 创建新表结构（带唯一性约束）
            connection.execute(text("""
                CREATE TABLE rooms_new (
                    id INTEGER NOT NULL PRIMARY KEY,
                    building_unit VARCHAR,
                    room_number VARCHAR,
                    status VARCHAR DEFAULT '整改中',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    delivery_status VARCHAR DEFAULT '待交付',
                    contract_status VARCHAR DEFAULT '待签约',
                    letter_status VARCHAR DEFAULT '无',
                    pre_leakage VARCHAR DEFAULT '无',
                    expected_delivery_date DATE,
                    owner_name VARCHAR,
                    owner_phone VARCHAR,
                    second_owner_name VARCHAR,
                    second_owner_phone VARCHAR,
                    CONSTRAINT _building_room_uc UNIQUE (building_unit, room_number)
                )
            """))
            
            # 2. 复制数据到新表（只保留每个楼栋+房号组合的第一条记录）
            connection.execute(text("""
                INSERT INTO rooms_new 
                SELECT * FROM rooms 
                WHERE id IN (
                    SELECT MIN(id) 
                    FROM rooms 
                    GROUP BY building_unit, room_number
                )
                ORDER BY id
            """))
            
            # 3. 删除旧表
            connection.execute(text("DROP TABLE rooms"))
            
            # 4. 重命名新表
            connection.execute(text("ALTER TABLE rooms_new RENAME TO rooms"))
            
            # 5. 重建索引
            connection.execute(text("CREATE INDEX ix_rooms_id ON rooms (id)"))
            
            connection.commit()
            
            print("✅ 唯一性约束添加成功！")
            
            # 验证结果
            result = connection.execute(text("SELECT COUNT(*) FROM rooms"))
            room_count = result.fetchone()[0]
            print(f"📊 当前房间记录总数: {room_count}")
            
            # 检查是否还有重复记录
            result = connection.execute(text("""
                SELECT building_unit, room_number, COUNT(*) 
                FROM rooms 
                GROUP BY building_unit, room_number 
                HAVING COUNT(*) > 1
            """))
            
            duplicates = result.fetchall()
            if duplicates:
                print(f"⚠️  仍存在 {len(duplicates)} 个重复记录")
                for dup in duplicates[:5]:  # 只显示前5个
                    print(f"  - {dup[0]} {dup[1]}: {dup[2]}条")
            else:
                print("✅ 无重复记录，唯一性约束生效")
                
            return True
            
    except Exception as e:
        print(f"❌ 添加唯一性约束失败: {e}")
        return False

if __name__ == "__main__":
    success = apply_unique_constraint()
    if success:
        print("\n🎉 数据库约束更新完成！")
        print("📋 现在所有房间导入和初始化操作都会自动保证数据唯一性")
    else:
        print("\n💥 操作失败，请检查错误信息")