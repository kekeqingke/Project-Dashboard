#!/usr/bin/env python3
"""
测试房间排序和统计功能
"""

from database import SessionLocal
from models import Room
from sqlalchemy import cast, Integer

def test_room_sorting():
    db = SessionLocal()
    try:
        # 测试排序后的房间列表
        print("=== 房间排序测试 ===")
        rooms = db.query(Room).order_by(Room.building_unit, cast(Room.room_number, Integer)).all()
        
        # 统计总数
        total_rooms = len(rooms)
        unit3_rooms = [r for r in rooms if r.building_unit == '3单元']
        unit4_rooms = [r for r in rooms if r.building_unit == '4单元']
        
        print(f"总房间数: {total_rooms}")
        print(f"3单元房间数: {len(unit3_rooms)}")
        print(f"4单元房间数: {len(unit4_rooms)}")
        
        # 显示3单元前10间和后10间房间号
        print(f"\n3单元房间号范围:")
        if unit3_rooms:
            print(f"前10间: {[r.room_number for r in unit3_rooms[:10]]}")
            print(f"后10间: {[r.room_number for r in unit3_rooms[-10:]]}")
        
        # 显示4单元前10间和后10间房间号  
        print(f"\n4单元房间号范围:")
        if unit4_rooms:
            print(f"前10间: {[r.room_number for r in unit4_rooms[:10]]}")
            print(f"后10间: {[r.room_number for r in unit4_rooms[-10:]]}")
            
        # 检查是否有重复的房间号
        print(f"\n=== 重复房间号检查 ===")
        all_room_keys = [(r.building_unit, r.room_number) for r in rooms]
        unique_room_keys = set(all_room_keys)
        
        if len(all_room_keys) != len(unique_room_keys):
            print("发现重复房间号!")
            duplicates = []
            seen = set()
            for key in all_room_keys:
                if key in seen:
                    duplicates.append(key)
                seen.add(key)
            print(f"重复的房间: {duplicates}")
        else:
            print("没有发现重复房间号")
            
    except Exception as e:
        print(f"测试出错: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_room_sorting()