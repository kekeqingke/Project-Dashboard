from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import models, schemas, auth
from typing import List, Optional
import json
import random
import string

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def generate_initial_password():
    """生成6位数字初始密码"""
    return ''.join(random.choices(string.digits, k=6))

def create_user(db: Session, user: schemas.UserCreate):
    # 生成初始密码（如果没有提供）
    initial_password = user.password if hasattr(user, 'password') else generate_initial_password()
    hashed_password = auth.get_password_hash(initial_password)
    
    db_user = models.User(
        username=user.username,
        password=hashed_password,
        name=user.name,
        role=user.role,
        initial_password=initial_password,
        password_changed=False
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def reset_user_password(db: Session, user_id: int):
    """重置用户密码为新的初始密码"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return None
    
    # 生成新的初始密码
    new_initial_password = generate_initial_password()
    hashed_password = auth.get_password_hash(new_initial_password)
    
    user.password = hashed_password
    user.initial_password = new_initial_password
    user.password_changed = False
    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, user_id: int):
    """删除用户及其相关数据"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return False
    
    # 删除用户的房间分配
    db.query(models.UserRoom).filter(models.UserRoom.user_id == user_id).delete()
    
    # 删除用户的质量问题记录
    db.query(models.QualityIssue).filter(models.QualityIssue.user_id == user_id).delete()
    
    # 沟通记录已删除，无需处理
    
    # 删除用户
    db.delete(user)
    db.commit()
    return True

# Room operations
def get_rooms(db: Session):
    rooms = db.query(models.Room).all()
    # 为每个房间添加用户分配信息
    for room in rooms:
        assignments = db.query(models.UserRoom).filter(models.UserRoom.room_id == room.id).all()
        room.assigned_users = []
        for assignment in assignments:
            user = db.query(models.User).filter(models.User.id == assignment.user_id).first()
            if user:
                room.assigned_users.append({
                    'id': user.id,
                    'name': user.name,
                    'role': user.role
                })
    return rooms

def get_user_rooms(db: Session, user_id: int):
    return db.query(models.Room).join(models.UserRoom, models.Room.id == models.UserRoom.room_id).filter(models.UserRoom.user_id == user_id).all()

def get_room_by_id(db: Session, room_id: int, user_id: Optional[int] = None):
    """获取单个房间信息，如果指定了user_id则检查权限"""
    query = db.query(models.Room).filter(models.Room.id == room_id)
    
    if user_id is not None:
        # 非管理员用户只能查看分配给自己的房间
        query = query.join(models.UserRoom, models.Room.id == models.UserRoom.room_id).filter(models.UserRoom.user_id == user_id)
    
    room = query.first()
    if not room:
        return None
    return room

def create_room(db: Session, room: schemas.RoomCreate):
    db_room = models.Room(**room.dict())
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room

def delete_room(db: Session, room_id: int):
    """删除房间及其相关数据"""
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not room:
        return False
    
    # 删除房间的用户分配
    db.query(models.UserRoom).filter(models.UserRoom.room_id == room_id).delete()
    
    # 删除房间的质量问题记录
    db.query(models.QualityIssue).filter(models.QualityIssue.room_id == room_id).delete()
    
    # 沟通记录已删除，无需处理
    
    # 删除房间
    db.delete(room)
    db.commit()
    return True

def assign_room_to_user(db: Session, user_id: int, room_id: int):
    # 检查是否已分配
    existing = db.query(models.UserRoom).filter(
        models.UserRoom.user_id == user_id,
        models.UserRoom.room_id == room_id
    ).first()
    if existing:
        return existing
    
    assignment = models.UserRoom(user_id=user_id, room_id=room_id)
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment

def get_room_assignments(db: Session):
    return db.query(models.UserRoom).all()

def get_user_room_assignments(db: Session, user_id: int):
    """获取指定用户的房间分配，包含房间信息"""
    assignments = db.query(models.UserRoom).filter(models.UserRoom.user_id == user_id).all()
    result = []
    for assignment in assignments:
        result.append({
            "id": assignment.id,
            "user_id": assignment.user_id,
            "room_id": assignment.room_id,
            "created_at": assignment.created_at
        })
    return result

def delete_room_assignment(db: Session, assignment_id: int):
    assignment = db.query(models.UserRoom).filter(models.UserRoom.id == assignment_id).first()
    if assignment:
        db.delete(assignment)
        db.commit()
        return True
    return False

# Quality Issue operations
def get_quality_issues(db: Session, room_id: Optional[int] = None, user_id: Optional[int] = None):
    # 先构建基础查询，包含user的JOIN
    from sqlalchemy.orm import joinedload
    query = db.query(models.QualityIssue).options(
        joinedload(models.QualityIssue.user)
    )
    
    if room_id:
        query = query.filter(models.QualityIssue.room_id == room_id)
    if user_id:
        # 只显示用户有权限的房间的质量问题
        query = query.join(models.UserRoom, models.QualityIssue.room_id == models.UserRoom.room_id).filter(models.UserRoom.user_id == user_id)
    
    issues = query.all()
    # 为每个质量问题添加用户信息和计算is_verified字段
    for issue in issues:
        issue.user_name = issue.user.name if issue.user else "未知用户"
        issue.user_role = issue.user.role if issue.user else ""
        # 设置is_verified字段（保证前端工作台兼容性）
        issue.is_verified = issue.status == "已验收"
        # 添加验收人信息
        if issue.accepted_by:
            acceptor = db.query(models.User).filter(models.User.id == issue.accepted_by).first()
            if acceptor:
                issue.acceptor_name = acceptor.name
                issue.acceptor_role = acceptor.role
    return issues

def create_quality_issue(db: Session, issue: schemas.QualityIssueCreate, user_id: int):
    db_issue = models.QualityIssue(**issue.dict(), user_id=user_id)
    db.add(db_issue)
    db.commit()
    db.refresh(db_issue)
    
    # 更新房间状态为"整改中"
    update_room_status(db, issue.room_id)
    return db_issue

def accept_quality_issue(db: Session, issue_id: int, user_id: int):
    from datetime import datetime
    issue = db.query(models.QualityIssue).filter(models.QualityIssue.id == issue_id).first()
    if issue:
        issue.status = "已验收"
        issue.accepted_by = user_id
        issue.accepted_at = datetime.now()
        db.commit()
        
        # 检查房间是否可以设置为"闭户"
        update_room_status(db, issue.room_id)
        return issue
    return None

def update_quality_issue(db: Session, issue_id: int, issue_update: schemas.QualityIssueUpdate, user_id: Optional[int] = None):
    """更新质量问题"""
    query = db.query(models.QualityIssue).filter(models.QualityIssue.id == issue_id)
    
    # 如果提供了user_id，检查用户是否有权限访问该质量问题
    if user_id:
        query = query.join(models.UserRoom, models.QualityIssue.room_id == models.UserRoom.room_id).filter(models.UserRoom.user_id == user_id)
    
    issue = query.first()
    if issue:
        for key, value in issue_update.dict(exclude_unset=True).items():
            if value is not None:
                setattr(issue, key, value)
        db.commit()
        db.refresh(issue)
        
        # 更新房间状态
        update_room_status(db, issue.room_id)
        
        # 设置is_verified字段（保证前端兼容性）
        issue.is_verified = issue.status == "已验收"
        
        return issue
    return None



# Room status management
def update_room_status(db: Session, room_id: int):
    """
    自动更新房间整改状态：
    - 如果有待验收的质量问题，状态为"整改中"
    - 如果所有质量问题都已验收，状态为"闭户"
    """
    # 检查是否有未验收的质量问题
    pending_issues = db.query(models.QualityIssue).filter(
        models.QualityIssue.room_id == room_id,
        models.QualityIssue.status == "待验收"
    ).count()
    
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if room:
        if pending_issues > 0:
            room.status = "整改中"
        else:
            # 所有质量问题都已验收，自动设置为"闭户"
            room.status = "闭户"
        db.commit()

def update_room_ambassador_status(db: Session, room_id: int, status_data: dict):
    """
    客户大使更新房间状态（仅限特定字段）
    允许更新：delivery_status, contract_status, letter_status, expected_delivery_date
    不允许更新：status（整改状态由系统自动管理）
    """
    from datetime import datetime
    
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not room:
        return None
    
    # 只允许客户大使更新特定字段
    allowed_fields = ['delivery_status', 'contract_status', 'letter_status', 'expected_delivery_date']
    
    for field, value in status_data.items():
        if field in allowed_fields:
            if field == 'expected_delivery_date' and value:
                # 处理日期字符串转换
                try:
                    if isinstance(value, str):
                        parsed_date = datetime.strptime(value, '%Y-%m-%d').date()
                        setattr(room, field, parsed_date)
                    else:
                        setattr(room, field, value)
                except ValueError:
                    # 日期格式错误，跳过这个字段
                    continue
            elif value is not None:
                setattr(room, field, value)
    
    db.commit()
    db.refresh(room)
    return room

# Admin summary
def get_room_summary(db: Session, building_unit: Optional[str] = None):
    query = db.query(models.Room)
    if building_unit:
        query = query.filter(models.Room.building_unit == building_unit)
    
    rooms = query.all()
    
    # 统计各状态房间数量
    status_count = {}
    delivery_count = {}
    contract_count = {}
    
    # 构建带聚合数据的房间列表
    rooms_with_summary = []
    
    for room in rooms:
        # 统计房间主状态
        status_count[room.status] = status_count.get(room.status, 0) + 1
        # 统计交付状态
        delivery_count[room.delivery_status] = delivery_count.get(room.delivery_status, 0) + 1
        # 统计签约状态  
        contract_count[room.contract_status] = contract_count.get(room.contract_status, 0) + 1
        
        # 获取质量问题统计和详情
        pending_issues = db.query(models.QualityIssue).filter(
            models.QualityIssue.room_id == room.id,
            models.QualityIssue.status == "待验收"
        ).order_by(desc(func.coalesce(models.QualityIssue.record_date, models.QualityIssue.created_at))).all()
        
        # 获取最新的待验收问题详情
        latest_pending_issue = pending_issues[0] if pending_issues else None
        
        # 沟通记录相关功能已删除
        
        # 构建带聚合数据的房间对象
        room_summary = {
            # 基本房间信息
            'id': room.id,
            'building_unit': room.building_unit,
            'room_number': room.room_number,
            'status': room.status,
            'delivery_status': room.delivery_status,
            'contract_status': room.contract_status,
            'letter_status': room.letter_status,  # 添加信件状态
            'expected_delivery_date': room.expected_delivery_date,  # 添加预计交付时间
            'created_at': room.created_at,
            'updated_at': room.updated_at,
            
            # 聚合的质量问题信息
            'pending_issues_count': len(pending_issues),
            'latest_issue_description': latest_pending_issue.description if latest_pending_issue else "",
            'latest_issue_type': latest_pending_issue.issue_type if latest_pending_issue else "",
            'latest_issue_record_date': latest_pending_issue.record_date if latest_pending_issue else None,
            
            # 沟通记录功能已删除，保留字段结构
            'pending_communications_count': 0,
            'latest_comm_content': "",
            'latest_comm_time': None,
            'latest_feedback': ""
        }
        
        rooms_with_summary.append(room_summary)
    
    return {
        "total_rooms": len(rooms),
        "status_summary": status_count,
        "delivery_summary": delivery_count,
        "contract_summary": contract_count,
        "rooms": rooms_with_summary
    }

def clear_room_content(db: Session, room_id: int):
    """清空房间内容数据，保留用户分配和房号
    
    清空以下数据：
    - 质量问题记录(quality_issues)
    - 沟通记录(communications)
    - 重置房间状态为初始值
    
    保留以下数据：
    - 房间基本信息(building_unit, room_number)
    - 用户-房间分配关系(user_rooms)
    """
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not room:
        return False
    
    # 删除房间的质量问题记录
    deleted_issues = db.query(models.QualityIssue).filter(models.QualityIssue.room_id == room_id).delete()
    
    # 沟通记录已删除，无需处理
    deleted_communications = 0
    
    # 重置房间状态为初始值
    room.status = "整改中"
    room.delivery_status = "待交付"
    room.contract_status = "待签约"
    room.letter_status = "无"
    
    db.commit()
    
    return {
        "room_id": room_id,
        "deleted_issues": deleted_issues,
        "deleted_communications": deleted_communications,
        "message": f"房间 {room.building_unit}-{room.room_number} 内容已清空，保留用户分配"
    }

def clear_all_rooms_content(db: Session):
    """清空所有房间内容数据，保留用户分配和房号
    
    批量执行clear_room_content操作
    """
    rooms = db.query(models.Room).all()
    if not rooms:
        return {"message": "没有找到房间数据"}
    
    total_deleted_issues = 0
    total_deleted_communications = 0
    cleared_rooms = []
    
    for room in rooms:
        # 删除质量问题记录
        deleted_issues = db.query(models.QualityIssue).filter(models.QualityIssue.room_id == room.id).delete()
        total_deleted_issues += deleted_issues
        
        # 沟通记录已删除，无需处理
        deleted_communications = 0
        total_deleted_communications += deleted_communications
        
        # 重置房间状态
        room.status = "整改中"
        room.delivery_status = "待交付"
        room.contract_status = "待签约"
        room.letter_status = "无"
        
        cleared_rooms.append(f"{room.building_unit}-{room.room_number}")
    
    db.commit()
    
    return {
        "total_rooms": len(rooms),
        "cleared_rooms": cleared_rooms,
        "total_deleted_issues": total_deleted_issues,
        "total_deleted_communications": total_deleted_communications,
        "message": f"已清空 {len(rooms)} 个房间的内容数据，保留用户分配和房号信息"
    }

# Customer CRUD operations
def get_customer_by_room_id(db: Session, room_id: int):
    """根据房间ID获取客户信息"""
    return db.query(models.Customer).filter(models.Customer.room_id == room_id).first()

def create_customer(db: Session, customer: schemas.CustomerCreate):
    """创建客户信息"""
    db_customer = models.Customer(**customer.dict())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

def update_customer(db: Session, customer_id: int, customer: schemas.CustomerUpdate):
    """更新客户信息"""
    db_customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if db_customer:
        for key, value in customer.dict(exclude_unset=True).items():
            setattr(db_customer, key, value)
        db.commit()
        db.refresh(db_customer)
    return db_customer

def delete_customer(db: Session, customer_id: int):
    """删除客户信息"""
    db_customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if db_customer:
        db.delete(db_customer)
        db.commit()
        return True
    return False

def get_customer(db: Session, customer_id: int):
    """根据ID获取客户信息"""
    return db.query(models.Customer).filter(models.Customer.id == customer_id).first()

def check_id_card_exists(db: Session, id_card: str, exclude_customer_id: int = None):
    """检查身份证号是否已存在"""
    query = db.query(models.Customer).filter(models.Customer.id_card == id_card)
    if exclude_customer_id:
        query = query.filter(models.Customer.id != exclude_customer_id)
    return query.first() is not None