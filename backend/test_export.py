#!/usr/bin/env python3

"""
测试导出功能的脚本
"""

import sys
import os

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_db
import crud
from sqlalchemy.orm import Session

def test_get_room_summary():
    """测试get_room_summary函数"""
    print("测试get_room_summary函数...")
    
    db = next(get_db())
    try:
        result = crud.get_room_summary(db, None)
        print(f"总房间数: {result['total_rooms']}")
        print(f"状态汇总: {result['status_summary']}")
        print(f"交付状态汇总: {result['delivery_summary']}")
        print(f"签约状态汇总: {result['contract_summary']}")
        
        if result['rooms']:
            first_room = result['rooms'][0]
            print(f"第一个房间的字段: {list(first_room.keys())}")
            print(f"第一个房间数据: {first_room}")
        else:
            print("没有找到房间数据")
            
    except Exception as e:
        print(f"测试get_room_summary时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def test_export_logic():
    """测试导出逻辑"""
    print("\n测试导出逻辑...")
    
    db = next(get_db())
    try:
        # 获取汇总数据
        summary_data = crud.get_room_summary(db, None)
        rooms = summary_data["rooms"]
        
        print(f"获取到的房间数量: {len(rooms)}")
        
        # 测试筛选逻辑
        filtered_rooms = []
        for room in rooms:
            # 测试获取字段
            try:
                building_unit = room.get("building_unit")
                room_number = room.get("room_number")
                status = room.get("status")
                print(f"房间: {building_unit}-{room_number}, 状态: {status}")
                filtered_rooms.append(room)
            except Exception as e:
                print(f"处理房间时出错: {e}")
                
        print(f"筛选后的房间数量: {len(filtered_rooms)}")
        
    except Exception as e:
        print(f"测试导出逻辑时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_get_room_summary()
    test_export_logic()