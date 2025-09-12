"""
数据库初始化脚本
创建数据库表并插入示例数据
"""
from database import engine
import models
from sqlalchemy.orm import sessionmaker
import auth
import os
import secrets
import string
from dotenv import load_dotenv

def generate_random_password(length=10):
    """生成随机密码"""
    # 包含大小写字母和数字
    characters = string.ascii_letters + string.digits
    # 避免容易混淆的字符
    characters = characters.replace('0', '').replace('O', '').replace('l', '').replace('1', '').replace('I', '')
    return ''.join(secrets.choice(characters) for _ in range(length))

def generate_jwt_secret(length=64):
    """生成JWT密钥"""
    return secrets.token_urlsafe(length)

def create_env_file():
    """创建.env文件"""
    env_file = ".env"
    if os.path.exists(env_file):
        print("⚠️  .env文件已存在，跳过创建")
        return
    
    # 生成安全配置
    jwt_secret = generate_jwt_secret()
    admin_password = generate_random_password()
    
    env_content = f"""# ZWY项目管理系统 - 自动生成的安全配置
# 请妥善保管此文件，不要提交到Git仓库

# 数据库配置
DATABASE_URL=sqlite:///./zwy_project.db

# JWT 安全配置
JWT_SECRET_KEY={jwt_secret}
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=43200

# 管理员账号配置
ADMIN_USERNAME=admin
ADMIN_PASSWORD={admin_password}

# 应用配置  
DEBUG=False
UPLOAD_DIR=uploads

# 内网部署配置
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
"""
    
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("✅ 已创建 .env 配置文件")
    return admin_password

def load_config():
    """加载环境变量"""
    load_dotenv()
    return {
        'admin_username': os.getenv('ADMIN_USERNAME', 'admin'),
        'admin_password': os.getenv('ADMIN_PASSWORD', 'admin123'),
        'jwt_secret': os.getenv('JWT_SECRET_KEY', 'default-secret-key')
    }

# 创建数据库表
models.Base.metadata.create_all(bind=engine)

# 创建或加载环境配置
generated_password = create_env_file()
config = load_config()

# 使用生成的密码（如果刚创建了.env文件）
if generated_password:
    admin_password = generated_password
else:
    admin_password = config['admin_password']

# 创建数据库会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    # 检查是否已有管理员用户
    existing_admin = db.query(models.User).filter(models.User.role == "admin").first()
    
    if existing_admin:
        print("📋 管理员账号已存在")
        # 检查是否使用默认密码
        if auth.verify_password("admin123", existing_admin.password):
            print("⚠️  检测到管理员仍在使用默认密码 'admin123'")
            print("🔐 强烈建议立即登录系统修改密码！")
        print(f"👤 管理员用户名：{existing_admin.username}")
    else:
        # 创建管理员用户
        admin_user = models.User(
            username=config['admin_username'],
            password=auth.get_password_hash(admin_password),
            name="系统管理员",
            role="admin"
        )
        db.add(admin_user)
        
        print("👤 已创建管理员账号")
    
    # 创建或重置房间数据（支持覆盖已有数据）
    existing_rooms = db.query(models.Room).count()
    if existing_rooms > 0:
        print("⚠️  检测到已有房间数据，将清理并重新创建房间数据")
        print("🗑️  删除旧房间数据...")
        # 删除所有房间记录（级联删除相关的质量问题和分配记录）
        db.query(models.Room).delete()
        db.commit()
    
    print("🏠 开始创建房间数据...")

    # 不创建测试用户，只保留管理员账号

    # 创建房间数据
    # 3单元和4单元：3-46层，每层01-04号房，排除14层和30层（避难层）
    # 4单元额外排除：4503、4504、4601、4602、4603、4604
    excluded_floors = [14, 30]  # 避难层
    excluded_4_unit_rooms = ["4503", "4504", "4601", "4602", "4603", "4604"]  # 4单元排除的房间
    
    rooms_to_create = []
    for building_unit in ["3单元", "4单元"]:
        for floor in range(3, 47):  # 3到46楼
            if floor in excluded_floors:
                continue  # 跳过避难层
            for room_num in ["01", "02", "03", "04"]:
                room_number = f"{floor:02d}{room_num}"
                # 如果是4单元，检查是否在排除列表中
                if building_unit == "4单元" and room_number in excluded_4_unit_rooms:
                    continue  # 跳过4单元的特定房间
                
                room = models.Room(
                    building_unit=building_unit,
                    room_number=room_number,
                    status="整改中"
                )
                rooms_to_create.append(room)
    
    # 批量插入房间数据
    db.add_all(rooms_to_create)
    print(f"💾 创建了 {len(rooms_to_create)} 个房间记录")
    
    # 提交房间数据
    try:
        db.commit()
        print("✅ 房间数据创建成功")
    except Exception as e:
        print(f"❌ 房间数据创建失败: {e}")
        db.rollback()
        raise
    
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
        
        # 沟通记录功能已移除，不再初始化示例数据
    
    db.commit()
    
    # 显示初始化完成信息
    print("\n" + "="*60)
    print("🎉 数据库初始化完成！")
    print("="*60)
    
    if generated_password:
        print("\n🔐 管理员账号信息：")
        print(f"👤 用户名：{config['admin_username']}")
        print(f"🔑 临时密码：{admin_password}")
        print("\n⚠️  安全提示：")
        print("• 请立即登录系统修改此临时密码！")
        print("• 建议新密码：8位以上，包含大小写字母和数字")
        print("• 此密码已保存在 .env 文件中，请妥善保管")
    else:
        print(f"\n👤 管理员用户名：{config['admin_username']}")
        print("🔑 密码已从 .env 文件加载")
    
    print("\n🌐 系统访问地址：")
    print("• 本机访问：http://localhost")
    print("• 内网访问：http://10.13.33.52")
    print("• API文档：http://10.13.33.52/docs")
    print("="*60)

except Exception as e:
    print(f"数据库初始化失败: {e}")
    db.rollback()
finally:
    db.close()