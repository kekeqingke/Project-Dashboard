#!/usr/bin/env python3
"""
清理测试数据，准备上线部署
保留管理员账号和房间基础信息，清理所有虚构的人员分配、质量问题和沟通记录
"""
from sqlalchemy.orm import sessionmaker
from database import engine
import models

# 创建数据库会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def clean_test_data():
    try:
        print("开始清理测试数据...")
        
        # 1. 清理沟通记录
        print("1. 删除所有沟通记录...")
        communications = db.query(models.Communication).all()
        for comm in communications:
            db.delete(comm)
        comm_count = len(communications)
        print(f"   删除了 {comm_count} 条沟通记录")
        
        # 2. 清理质量问题记录
        print("2. 删除所有质量问题记录...")
        quality_issues = db.query(models.QualityIssue).all()
        for issue in quality_issues:
            db.delete(issue)
        issue_count = len(quality_issues)
        print(f"   删除了 {issue_count} 条质量问题记录")
        
        # 3. 清理用户-房间分配关系
        print("3. 删除所有用户-房间分配关系...")
        user_rooms = db.query(models.UserRoom).all()
        for ur in user_rooms:
            db.delete(ur)
        ur_count = len(user_rooms)
        print(f"   删除了 {ur_count} 条分配关系")
        
        # 4. 删除测试用户（保留管理员）
        print("4. 删除所有测试用户（保留管理员）...")
        test_users = db.query(models.User).filter(models.User.username != "admin").all()
        for user in test_users:
            print(f"   删除用户: {user.username} ({user.name})")
            db.delete(user)
        user_count = len(test_users)
        print(f"   删除了 {user_count} 个测试用户")
        
        # 5. 重置房间状态
        print("5. 重置所有房间状态为初始状态...")
        rooms = db.query(models.Room).all()
        for room in rooms:
            room.status = "整改中"  # 重置为初始状态
            room.delivery_status = "待交付"  # 重置交付状态
            room.contract_status = "待签约"  # 重置合同状态
        print(f"   重置了 {len(rooms)} 个房间的状态")
        
        # 提交更改
        db.commit()
        print("\n数据清理完成！")
        
        # 显示清理后的统计信息
        print("\n=== 清理后的数据统计 ===")
        remaining_users = db.query(models.User).count()
        remaining_rooms = db.query(models.Room).count()
        remaining_user_rooms = db.query(models.UserRoom).count()
        remaining_issues = db.query(models.QualityIssue).count()
        remaining_comms = db.query(models.Communication).count()
        
        print(f"剩余用户数量: {remaining_users}")
        print(f"房间数量: {remaining_rooms}")
        print(f"用户-房间分配数量: {remaining_user_rooms}")
        print(f"质量问题数量: {remaining_issues}")
        print(f"沟通记录数量: {remaining_comms}")
        
        if remaining_users == 1:
            admin_user = db.query(models.User).first()
            print(f"\n保留的管理员账号: {admin_user.username} ({admin_user.name})")
        
        print(f"\n所有房间已重置为初始状态：")
        print("- 状态: 整改中")
        print("- 交付状态: 待交付") 
        print("- 合同状态: 待签约")
        print("- 无人员分配")
        print("- 无质量问题记录")
        print("- 无沟通记录")
        
        return True
        
    except Exception as e:
        print(f"清理数据时发生错误: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    # 确认清理操作
    print("=" * 50)
    print("数据清理脚本")
    print("=" * 50)
    print("此脚本将清理以下测试数据：")
    print("- 所有测试用户账号（保留管理员admin）")
    print("- 所有用户-房间分配关系") 
    print("- 所有质量问题记录")
    print("- 所有沟通记录")
    print("- 重置所有房间状态为初始状态")
    print()
    
    confirm = input("确认执行清理操作吗？(输入 'YES' 确认): ")
    if confirm == "YES":
        success = clean_test_data()
        if success:
            print("\n数据清理成功！系统已准备好部署上线。")
        else:
            print("\n数据清理失败，请检查错误信息。")
    else:
        print("取消清理操作。")