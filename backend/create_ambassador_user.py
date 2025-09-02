"""
为客户大使创建用户和分配房间的脚本
"""
from database import engine
import models
from sqlalchemy.orm import sessionmaker
import auth

# 创建数据库会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    # 检查客户大使用户是否已存在
    existing_user = db.query(models.User).filter(models.User.username == "13786141906").first()
    if existing_user:
        print("客户大使用户已存在，删除现有分配...")
        # 删除现有的房间分配
        db.query(models.UserRoom).filter(models.UserRoom.user_id == existing_user.id).delete()
        db.commit()
        user = existing_user
    else:
        # 创建客户大使用户
        user = models.User(
            username="13786141906",
            password=auth.get_password_hash("123456"),
            name="客户大使",
            role="customer_ambassador"
        )
        db.add(user)
        db.commit()
        print("客户大使用户创建成功")

    # 查找或创建3单元1701-1704房间
    room_numbers = ["1701", "1702", "1703", "1704"]
    room_ids = []
    
    for room_number in room_numbers:
        # 先查找房间是否存在
        existing_room = db.query(models.Room).filter(
            models.Room.building_unit == "3单元",
            models.Room.room_number == room_number
        ).first()
        
        if existing_room:
            print(f"房间3单元{room_number}已存在，ID: {existing_room.id}")
            room_ids.append(existing_room.id)
        else:
            # 创建房间
            room = models.Room(
                building_unit="3单元",
                room_number=room_number,
                status="整改中"
            )
            db.add(room)
            db.commit()
            db.refresh(room)
            print(f"房间3单元{room_number}创建成功，ID: {room.id}")
            room_ids.append(room.id)
    
    # 为客户大使分配这些房间
    for room_id in room_ids:
        # 检查是否已分配
        existing_assignment = db.query(models.UserRoom).filter(
            models.UserRoom.user_id == user.id,
            models.UserRoom.room_id == room_id
        ).first()
        
        if not existing_assignment:
            assignment = models.UserRoom(user_id=user.id, room_id=room_id)
            db.add(assignment)
    
    db.commit()
    print(f"\n客户大使房间分配完成:")
    print(f"用户: {user.name} ({user.username})")
    print(f"分配房间: 3单元1701, 3单元1702, 3单元1703, 3单元1704")
    print(f"房间ID: {room_ids}")

except Exception as e:
    print(f"操作失败: {e}")
    db.rollback()
finally:
    db.close()