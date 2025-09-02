"""
数据库初始化脚本
创建数据库表并插入示例数据
"""
from database import engine
import models
from sqlalchemy.orm import sessionmaker
import auth

# 创建数据库表
models.Base.metadata.create_all(bind=engine)

# 创建数据库会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    # 检查是否已有数据
    existing_users = db.query(models.User).count()
    if existing_users > 0:
        print("数据库已有数据，跳过初始化")
        exit()

    # 创建管理员用户
    admin_user = models.User(
        username="admin",
        password=auth.get_password_hash("admin123"),
        name="系统管理员",
        role="admin"
    )
    db.add(admin_user)

    # 不创建测试用户，只保留管理员账号

    # 创建房间数据
    # 3单元和4单元：3-46层，每层01-04号房，排除14层和30层（避难层）
    excluded_floors = [14, 30]  # 避难层
    for building_unit in ["3单元", "4单元"]:
        for floor in range(3, 47):  # 3到46楼
            if floor in excluded_floors:
                continue  # 跳过避难层
            for room_num in ["01", "02", "03", "04"]:
                room = models.Room(
                    building_unit=building_unit,
                    room_number=f"{floor:02d}{room_num}",
                    status="整改中"
                )
                db.add(room)

    db.commit()
    
    # 获取创建的用户和房间ID
    users_by_role = {}
    all_users = db.query(models.User).filter(models.User.role != "admin").all()
    for user in all_users:
        if user.role not in users_by_role:
            users_by_role[user.role] = []
        users_by_role[user.role].append(user)
    
    all_rooms = db.query(models.Room).all()
    
    # 为每个房间分配3种角色的用户（客户大使、项目工程师、维修工程师）
    import random
    for room in all_rooms:
        # 每个房间分配一个客户大使
        if 'customer_ambassador' in users_by_role and users_by_role['customer_ambassador']:
            customer_amb = random.choice(users_by_role['customer_ambassador'])
            assignment = models.UserRoom(user_id=customer_amb.id, room_id=room.id)
            db.add(assignment)
        
        # 每个房间分配一个项目工程师
        if 'project_engineer' in users_by_role and users_by_role['project_engineer']:
            proj_eng = random.choice(users_by_role['project_engineer'])
            assignment = models.UserRoom(user_id=proj_eng.id, room_id=room.id)
            db.add(assignment)
        
        # 每个房间分配一个维修工程师
        if 'maintenance_engineer' in users_by_role and users_by_role['maintenance_engineer']:
            maint_eng = random.choice(users_by_role['maintenance_engineer'])
            assignment = models.UserRoom(user_id=maint_eng.id, room_id=room.id)
            db.add(assignment)
    
    # 添加一些示例质量问题
    if all_rooms and all_users:
        sample_issues = [
            {
                "room_id": all_rooms[0].id,
                "user_id": all_users[0].id,  # 第一个非管理员用户
                "description": "墙面有裂缝，需要修补",
                "status": "待验收"
            },
            {
                "room_id": all_rooms[1].id,
                "user_id": all_users[1].id if len(all_users) > 1 else all_users[0].id,
                "description": "水龙头漏水，需要更换",
                "status": "待验收"
            },
            {
                "room_id": all_rooms[2].id,
                "user_id": all_users[0].id,
                "description": "地板有划痕",
                "status": "已验收"
            }
        ]
        
        for issue_data in sample_issues:
            issue = models.QualityIssue(**issue_data)
            db.add(issue)
        
        # 添加一些示例客户沟通记录
        customer_ambassadors = [u for u in all_users if u.role == 'customer_ambassador']
        if customer_ambassadors:
            sample_communications = [
                {
                    "room_id": all_rooms[0].id,
                    "user_id": customer_ambassadors[0].id,
                    "content": "已与客户沟通房间问题",
                    "feedback": "高"
                },
                {
                    "room_id": all_rooms[1].id,
                    "user_id": customer_ambassadors[0].id,
                    "content": "客户验房发现问题",
                    "feedback": "低"
                }
            ]
            
            for comm_data in sample_communications:
                comm = models.Communication(**comm_data)
                db.add(comm)
    
    db.commit()
    print("数据库初始化完成！")
    print("\n默认账号:")
    print("管理员: admin / admin123")

except Exception as e:
    print(f"数据库初始化失败: {e}")
    db.rollback()
finally:
    db.close()