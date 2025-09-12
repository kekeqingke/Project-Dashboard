"""
管理员密码重置工具
用于紧急情况下重置管理员密码
"""
import os
import sys
import getpass
import secrets
import string
from sqlalchemy.orm import sessionmaker
from database import engine
import models
import auth
from dotenv import load_dotenv

def generate_random_password(length=12):
    """生成随机密码"""
    characters = string.ascii_letters + string.digits
    # 避免容易混淆的字符
    characters = characters.replace('0', '').replace('O', '').replace('l', '').replace('1', '').replace('I', '')
    return ''.join(secrets.choice(characters) for _ in range(length))

def validate_password_strength(password):
    """验证密码强度"""
    if len(password) < 8:
        return False, "密码长度至少8位"
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    if not (has_upper and has_lower and has_digit):
        return False, "密码必须包含大写字母、小写字母和数字"
    
    return True, "密码强度符合要求"

def update_env_file(new_password):
    """更新.env文件中的管理员密码"""
    env_file = ".env"
    if not os.path.exists(env_file):
        print("⚠️  未找到.env文件")
        return
    
    # 读取现有内容
    with open(env_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 更新密码行
    updated = False
    for i, line in enumerate(lines):
        if line.startswith('ADMIN_PASSWORD='):
            lines[i] = f'ADMIN_PASSWORD={new_password}\n'
            updated = True
            break
    
    if updated:
        with open(env_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print("✅ 已更新.env文件")
    else:
        print("⚠️  未在.env文件中找到ADMIN_PASSWORD配置")

def main():
    print("="*50)
    print("🔐 管理员密码重置工具")
    print("="*50)
    
    # 加载环境变量
    load_dotenv()
    
    # 创建数据库会话
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 查找管理员用户
        admin_user = db.query(models.User).filter(models.User.role == "admin").first()
        if not admin_user:
            print("❌ 未找到管理员用户")
            return
        
        print(f"👤 找到管理员用户：{admin_user.username}")
        print("\n选择密码设置方式：")
        print("1. 自动生成随机密码")
        print("2. 手动输入新密码")
        
        choice = input("\n请选择 (1/2): ").strip()
        
        if choice == "1":
            # 自动生成密码
            new_password = generate_random_password()
            print(f"\n🔑 自动生成的新密码：{new_password}")
        elif choice == "2":
            # 手动输入密码
            while True:
                new_password = getpass.getpass("\n🔑 请输入新密码：")
                confirm_password = getpass.getpass("🔑 请确认新密码：")
                
                if new_password != confirm_password:
                    print("❌ 两次输入的密码不一致，请重试")
                    continue
                
                is_valid, message = validate_password_strength(new_password)
                if not is_valid:
                    print(f"❌ {message}")
                    continue
                
                break
        else:
            print("❌ 无效选择")
            return
        
        # 确认操作
        confirm = input(f"\n确认重置管理员 '{admin_user.username}' 的密码？(y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ 操作已取消")
            return
        
        # 更新数据库中的密码
        admin_user.password = auth.get_password_hash(new_password)
        db.commit()
        
        # 更新.env文件
        update_env_file(new_password)
        
        print("\n✅ 密码重置成功！")
        print(f"👤 用户名：{admin_user.username}")
        if choice == "1":
            print(f"🔑 新密码：{new_password}")
        print("\n⚠️  请妥善保管新密码，并建议首次登录后再次修改")
        
    except Exception as e:
        print(f"❌ 密码重置失败：{e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()