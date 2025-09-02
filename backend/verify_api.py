"""
验证API数据结构
"""

import requests
from database import SessionLocal
import models

def get_admin_token():
    """获取管理员token"""
    try:
        response = requests.post(
            "http://localhost:8000/token",
            data={"username": "admin", "password": "123456"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            print(f"登录失败: {response.text}")
            return None
    except Exception as e:
        print(f"登录异常: {str(e)}")
        return None

def verify_summary_api():
    """验证汇总API数据结构"""
    print("=== 验证管理员汇总API ===")
    
    token = get_admin_token()
    if not token:
        print("无法获取管理员token")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get("http://localhost:8000/admin/summary", headers=headers)
        
        if response.status_code != 200:
            print(f"API调用失败: {response.status_code} - {response.text}")
            return False
        
        data = response.json()
        
        print(f"总房间数: {data.get('total_rooms', 0)}")
        print(f"状态汇总: {data.get('status_summary', {})}")
        print(f"交付汇总: {data.get('delivery_summary', {})}")
        print(f"签约汇总: {data.get('contract_summary', {})}")
        
        rooms = data.get('rooms', [])
        print(f"房间详细数据数量: {len(rooms)}")
        
        if len(rooms) > 0:
            print("\n=== 验证房间数据结构 ===")
            room = rooms[0]
            
            # 检查新增字段是否存在
            required_fields = [
                'building_unit', 'room_number', 'status', 
                'delivery_status', 'contract_status',
                'pending_issues_count', 'latest_issue_description', 
                'latest_issue_type', 'latest_issue_record_date',
                'pending_communications_count', 'latest_comm_content',
                'latest_comm_time', 'latest_feedback'
            ]
            
            print("检查必需字段:")
            all_fields_present = True
            for field in required_fields:
                if hasattr(room, field) or field in room:
                    print(f"  ✓ {field}: {getattr(room, field, room.get(field, '未定义'))}")
                else:
                    print(f"  ✗ 缺失字段: {field}")
                    all_fields_present = False
            
            if all_fields_present:
                print("\n✅ 所有必需字段都存在")
            else:
                print("\n❌ 存在缺失字段")
            
            # 显示第一个房间的完整数据
            print(f"\n=== 第一个房间详细数据 ===")
            for key, value in room.items():
                print(f"  {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"验证过程中出现异常: {str(e)}")
        return False

def verify_database_data():
    """直接验证数据库数据"""
    print("\n=== 验证数据库数据 ===")
    
    db = SessionLocal()
    try:
        rooms = db.query(models.Room).all()
        print(f"数据库中房间总数: {len(rooms)}")
        
        for room in rooms:
            print(f"\n房间: {room.building_unit} {room.room_number}")
            print(f"  状态: {room.status}")
            print(f"  交付状态: {room.delivery_status}")
            print(f"  签约状态: {room.contract_status}")
            
            # 检查质量问题
            pending_issues = db.query(models.QualityIssue).filter(
                models.QualityIssue.room_id == room.id,
                models.QualityIssue.status == "待验收"
            ).all()
            print(f"  待验收问题数: {len(pending_issues)}")
            
            if pending_issues:
                latest_issue = pending_issues[0]
                print(f"  最新问题描述: {latest_issue.description}")
                print(f"  最新问题类型: {latest_issue.issue_type}")
                print(f"  最新问题录入时间: {latest_issue.record_date}")
            
            # 检查沟通记录
            pending_comms = db.query(models.Communication).filter(
                models.Communication.room_id == room.id,
                models.Communication.is_implemented == False
            ).all()
            print(f"  待落实沟通数: {len(pending_comms)}")
            
            if pending_comms:
                latest_comm = pending_comms[0]
                print(f"  最新沟通内容: {latest_comm.content}")
                print(f"  最新沟通时间: {latest_comm.communication_time}")
            
            # 检查收房意愿
            latest_feedback_comm = db.query(models.Communication).filter(
                models.Communication.room_id == room.id,
                models.Communication.feedback.isnot(None)
            ).first()
            
            if latest_feedback_comm:
                print(f"  收房意愿: {latest_feedback_comm.feedback}")
        
    finally:
        db.close()

if __name__ == "__main__":
    print("开始API和数据验证...")
    
    # 验证数据库数据
    verify_database_data()
    
    # 验证API返回
    success = verify_summary_api()
    
    if success:
        print("\n✅ API验证完成")
    else:
        print("\n❌ API验证失败")