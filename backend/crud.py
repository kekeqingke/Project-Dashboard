from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import models, schemas, auth
from typing import List, Optional
import json
import random
import string
from datetime import datetime

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def generate_initial_password():
    """生成8位随机初始密码"""
    # 包含字母和数字，但避免容易混淆的字符
    characters = string.ascii_letters + string.digits
    characters = characters.replace('0', '').replace('O', '').replace('l', '').replace('1', '').replace('I', '')
    return ''.join(random.choices(characters, k=8))

def create_user(db: Session, user: schemas.UserCreate):
    # 生成初始密码（如果没有提供）
    initial_password = user.password if user.password else generate_initial_password()
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
    from sqlalchemy import cast, Integer
    rooms = db.query(models.Room).order_by(models.Room.building_unit, cast(models.Room.room_number, Integer)).all()
    # 为每个房间添加用户分配信息和格式化户主信息
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
        
        # 格式化户主信息用于前端显示（保留原始逻辑但修复空值问题）
        names = []
        phones = []
        
        if room.owner_name:
            names.append(room.owner_name)
        if room.owner_phone:
            phones.append(room.owner_phone)
        if room.second_owner_name:
            names.append(room.second_owner_name)
        if room.second_owner_phone:
            phones.append(room.second_owner_phone)
        
        # 为前端显示设置合并后的户主信息
        room.owner_name = "/".join(names) if len(names) > 1 else names[0] if names else None
        room.owner_phone = "/".join(phones) if len(phones) > 1 else phones[0] if phones else None
    
    return rooms

def get_user_rooms(db: Session, user_id: int):
    from sqlalchemy import cast, Integer
    return db.query(models.Room).join(models.UserRoom, models.Room.id == models.UserRoom.room_id).filter(models.UserRoom.user_id == user_id).order_by(models.Room.building_unit, cast(models.Room.room_number, Integer)).all()

def get_room_by_id(db: Session, room_id: int, user_id: Optional[int] = None):
    """获取单个房间信息，如果指定了user_id则检查权限"""
    query = db.query(models.Room).filter(models.Room.id == room_id)
    
    if user_id is not None:
        # 非管理员用户只能查看分配给自己的房间
        query = query.join(models.UserRoom, models.Room.id == models.UserRoom.room_id).filter(models.UserRoom.user_id == user_id)
    
    room = query.first()
    if not room:
        return None
    
    # 添加用户分配信息，与get_rooms函数保持一致
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
    
    # 格式化户主信息用于前端显示（保留原始逻辑但修复空值问题）
    names = []
    phones = []
    
    if room.owner_name:
        names.append(room.owner_name)
    if room.owner_phone:
        phones.append(room.owner_phone)
    if room.second_owner_name:
        names.append(room.second_owner_name)
    if room.second_owner_phone:
        phones.append(room.second_owner_phone)
    
    # 为前端显示设置合并后的户主信息
    room.owner_name = "/".join(names) if len(names) > 1 else names[0] if names else None
    room.owner_phone = "/".join(phones) if len(phones) > 1 else phones[0] if phones else None
    
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
        issue.is_verified = issue.status in ["已验收", "已复验"]
        
        # 添加验收人信息
        if issue.accepted_by:
            acceptor = db.query(models.User).filter(models.User.id == issue.accepted_by).first()
            if acceptor:
                issue.acceptor_name = acceptor.name
                issue.acceptor_role = acceptor.role
        
    return issues

def get_quality_issue_by_id(db: Session, issue_id: int):
    """获取单个质量问题详情"""
    issue = db.query(models.QualityIssue).filter(models.QualityIssue.id == issue_id).first()
    if not issue:
        return None
    
    # 添加用户信息
    if issue.user_id:
        user = db.query(models.User).filter(models.User.id == issue.user_id).first()
        if user:
            issue.user_name = user.name
            issue.user_role = user.role
    
    # 添加验收人信息
    if issue.accepted_by:
        acceptor = db.query(models.User).filter(models.User.id == issue.accepted_by).first()
        if acceptor:
            issue.acceptor_name = acceptor.name
            issue.acceptor_role = acceptor.role
    
    # 注意：当前模型已简化，不再支持撤销和复验功能
    # 如果需要这些功能，需要在模型中添加相应字段
    
    return issue

def create_quality_issue(db: Session, issue: schemas.QualityIssueCreate, user_id: int):
    """创建质量问题并记录日志"""
    db_issue = models.QualityIssue(**issue.dict(), user_id=user_id)
    db.add(db_issue)
    db.commit()
    db.refresh(db_issue)
    
    # 获取用户信息
    user = db.query(models.User).filter(models.User.id == user_id).first()
    
    # 创建操作日志
    log = models.QualityIssueLog(
        issue_id=db_issue.id,
        action="CREATE",
        operator_id=user_id,
        operator_name=user.name if user else "未知用户",
        operator_role=user.role if user else "unknown",
        timestamp=datetime.utcnow(),  # 明确设置为UTC时间
        after_data=json.dumps({
            "status": db_issue.status,
            "description": db_issue.description,
            "issue_type": db_issue.issue_type,
            "record_date": db_issue.record_date.isoformat() if db_issue.record_date else None
        }),
        remarks="创建质量问题"
    )
    
    db.add(log)
    db.commit()
    
    # 更新房间状态为"整改中"
    update_room_status(db, issue.room_id)
    return db_issue

def accept_quality_issue(db: Session, issue_id: int, user_id: int):
    """简化的验收功能 - 只支持项目工程师验收"""
    issue = db.query(models.QualityIssue).filter(models.QualityIssue.id == issue_id).first()
    if not issue:
        return None
    
    if issue.status != "待验收":
        return None
        
    # 获取操作用户信息
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or user.role != "project_engineer":
        return None  # 只允许项目工程师验收
    
    # 记录变更前数据
    before_data = json.dumps({
        "status": issue.status,
        "accepted_by": issue.accepted_by,
        "accepted_at": issue.accepted_at.isoformat() if issue.accepted_at else None
    })
    
    # 执行验收
    issue.status = "已验收"
    issue.accepted_by = user_id
    issue.accepted_at = datetime.now()
    
    # 记录变更后数据
    after_data = json.dumps({
        "status": issue.status,
        "accepted_by": issue.accepted_by,
        "accepted_at": issue.accepted_at.isoformat()
    })
    
    # 创建操作日志
    log = models.QualityIssueLog(
        issue_id=issue_id,
        action="ACCEPT",
        operator_id=user_id,
        operator_name=user.name,
        operator_role=user.role,
        timestamp=datetime.utcnow(),  # 明确设置为UTC时间
        before_data=before_data,
        after_data=after_data,
        remarks="质量问题验收通过"
    )
    
    db.add(log)
    db.commit()
    
    # 检查房间是否可以设置为"闭户"
    update_room_status(db, issue.room_id)
    return issue

def revoke_accept_quality_issue(db: Session, issue_id: int, user_id: int):
    """撤销验收功能 - 限制24小时内且只能撤销自己的验收"""
    issue = db.query(models.QualityIssue).filter(models.QualityIssue.id == issue_id).first()
    if not issue:
        return None
        
    if issue.status != "已验收" or issue.accepted_by != user_id:
        return None  # 只能撤销自己的验收
        
    # 检查是否在24小时内
    if issue.accepted_at:
        time_diff = datetime.now() - issue.accepted_at
        if time_diff.total_seconds() > 86400:  # 24小时 = 86400秒
            return None
    
    # 获取操作用户信息
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return None
    
    # 记录变更前数据
    before_data = json.dumps({
        "status": issue.status,
        "accepted_by": issue.accepted_by,
        "accepted_at": issue.accepted_at.isoformat() if issue.accepted_at else None
    })
    
    # 执行撤销
    issue.status = "待验收"
    issue.accepted_by = None
    issue.accepted_at = None
    
    # 记录变更后数据
    after_data = json.dumps({
        "status": issue.status,
        "accepted_by": None,
        "accepted_at": None
    })
    
    # 创建操作日志
    log = models.QualityIssueLog(
        issue_id=issue_id,
        action="REVOKE_ACCEPT",
        operator_id=user_id,
        operator_name=user.name,
        operator_role=user.role,
        timestamp=datetime.utcnow(),  # 明确设置为UTC时间
        before_data=before_data,
        after_data=after_data,
        remarks="验收人撤销验收(24小时内)"
    )
    
    db.add(log)
    db.commit()
    
    # 更新房间状态
    update_room_status(db, issue.room_id)
    return issue

def get_quality_issue_logs(db: Session, issue_id: int):
    """获取质量问题的所有操作日志"""
    return db.query(models.QualityIssueLog).filter(
        models.QualityIssueLog.issue_id == issue_id
    ).order_by(models.QualityIssueLog.timestamp.asc()).all()

def update_quality_issue(db: Session, issue_id: int, issue_update: schemas.QualityIssueUpdate, user_id: int):
    """更新质量问题 - 只允许创建人修改且仅限待验收状态"""
    issue = db.query(models.QualityIssue).filter(models.QualityIssue.id == issue_id).first()
    
    if not issue:
        return None
        
    # 只允许创建人修改
    if issue.user_id != user_id:
        return None
        
    # 只允许修改待验收状态的问题
    if issue.status != "待验收":
        return None
    
    # 获取操作用户信息
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return None
    
    # 记录变更前数据
    before_data = json.dumps({
        "description": issue.description,
        "issue_type": issue.issue_type,
        "record_date": issue.record_date.isoformat() if issue.record_date else None,
        "images": issue.images
    })
    
    # 执行更新
    update_dict = issue_update.dict(exclude_unset=True)
    for key, value in update_dict.items():
        if value is not None:
            setattr(issue, key, value)
    
    # 记录变更后数据
    after_data = json.dumps({
        "description": issue.description,
        "issue_type": issue.issue_type,
        "record_date": issue.record_date.isoformat() if issue.record_date else None,
        "images": issue.images
    })
    
    # 创建操作日志
    log = models.QualityIssueLog(
        issue_id=issue_id,
        action="UPDATE",
        operator_id=user_id,
        operator_name=user.name,
        operator_role=user.role,
        timestamp=datetime.utcnow(),  # 明确设置为UTC时间
        before_data=before_data,
        after_data=after_data,
        remarks="修改质量问题信息"
    )
    
    db.add(log)
    db.commit()
    db.refresh(issue)
    
    # 更新房间状态
    update_room_status(db, issue.room_id)
    
    # 设置is_verified字段（保证前端兼容性）
    issue.is_verified = issue.status == "已验收"
    
    return issue

def delete_quality_issue(db: Session, issue_id: int):
    """删除质量问题 - 仅供管理员使用"""
    issue = db.query(models.QualityIssue).filter(models.QualityIssue.id == issue_id).first()
    
    if not issue:
        return False
    
    # 删除相关的日志记录
    db.query(models.QualityIssueLog).filter(models.QualityIssueLog.issue_id == issue_id).delete()
    
    # 删除质量问题
    room_id = issue.room_id  # 保存room_id用于后续更新房间状态
    db.delete(issue)
    db.commit()
    
    # 删除后更新房间状态
    update_room_status(db, room_id)
    
    return True

def update_responsible_unit(db: Session, issue_id: int, responsible_unit: str, user_id: int):
    """项目工程师更新质量问题的责任单位"""
    issue = db.query(models.QualityIssue).filter(models.QualityIssue.id == issue_id).first()

    if not issue:
        return None

    # 获取操作用户信息
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or user.role != "project_engineer":
        return None  # 只允许项目工程师更新责任单位

    # 记录变更前数据
    before_data = json.dumps({
        "responsible_unit": issue.responsible_unit
    })

    # 更新责任单位
    issue.responsible_unit = responsible_unit

    # 记录变更后数据
    after_data = json.dumps({
        "responsible_unit": issue.responsible_unit
    })

    # 创建操作日志
    log = models.QualityIssueLog(
        issue_id=issue_id,
        action="UPDATE_RESPONSIBLE_UNIT",
        operator_id=user_id,
        operator_name=user.name,
        operator_role=user.role,
        timestamp=datetime.utcnow(),
        before_data=before_data,
        after_data=after_data,
        remarks="项目工程师更新责任单位"
    )

    db.add(log)
    db.commit()
    db.refresh(issue)

    return issue


# Room status management
def update_room_status(db: Session, room_id: int):
    """
    自动更新房间整改状态：
    - 如果有待验收或需复验的质量问题，状态为"整改中"
    - 如果所有质量问题都已验收，状态为"闭户"
    """
    # 检查是否有未完成的质量问题（待验收或需复验）
    pending_issues = db.query(models.QualityIssue).filter(
        models.QualityIssue.room_id == room_id,
        models.QualityIssue.status.in_(["待验收", "需复验"])
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
    
    # 添加排序逻辑：先按楼栋单元，再按房间号（数值排序）
    from sqlalchemy import cast, Integer
    rooms = query.order_by(models.Room.building_unit, cast(models.Room.room_number, Integer)).all()
    
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
        all_issues = db.query(models.QualityIssue).filter(
            models.QualityIssue.room_id == room.id
        ).all()
        
        pending_issues = [issue for issue in all_issues if issue.status == "待验收"]
        reverification_issues = [issue for issue in all_issues if issue.status == "需复验"]
        accepted_issues = [issue for issue in all_issues if issue.status in ["已验收", "已复验"]]
        
        # 获取最新的待处理问题详情（待验收或需复验）
        pending_and_reverify = pending_issues + reverification_issues
        latest_pending_issue = None
        if pending_and_reverify:
            latest_pending_issue = max(pending_and_reverify, 
                                     key=lambda x: x.record_date or x.created_at)
        
        # 沟通记录相关功能已删除
        
        # 获取户主信息（从rooms表获取）
        names = []
        phones = []
        
        if room.owner_name:
            names.append(room.owner_name)
        if room.owner_phone:
            phones.append(room.owner_phone)
        if room.second_owner_name:
            names.append(room.second_owner_name)
        if room.second_owner_phone:
            phones.append(room.second_owner_phone)
        
        # 只有在有多个时才用"/"分隔
        owner_name = "/".join(names) if len(names) > 1 else names[0] if names else ""
        owner_phone = "/".join(phones) if len(phones) > 1 else phones[0] if phones else ""
        
        # 获取房间的用户分配信息
        assignments = db.query(models.UserRoom).filter(models.UserRoom.room_id == room.id).all()
        assigned_users = []
        for assignment in assignments:
            user = db.query(models.User).filter(models.User.id == assignment.user_id).first()
            if user:
                assigned_users.append({
                    'id': user.id,
                    'name': user.name,
                    'role': user.role
                })

        # 构建带聚合数据的房间对象
        room_summary = {
            # 基本房间信息
            'id': room.id or 0,
            'building_unit': room.building_unit or "",
            'room_number': room.room_number or "",
            'status': room.status or "整改中",
            'delivery_status': room.delivery_status or "待交付",
            'contract_status': room.contract_status or "待签约",
            'letter_status': room.letter_status or "无",  # 添加信件状态
            'expected_delivery_date': room.expected_delivery_date,  # 添加预计交付时间
            'created_at': room.created_at,
            'updated_at': room.updated_at,

            # 户主信息
            'owner_name': owner_name or "",
            'owner_phone': owner_phone or "",

            # 用户分配信息
            'assigned_users': assigned_users,

            # 聚合的质量问题信息
            'pending_issues_count': len(pending_issues),
            'reverification_issues_count': len(reverification_issues),
            'accepted_issues_count': len(accepted_issues),
            'latest_issue_description': latest_pending_issue.description if latest_pending_issue else "",
            'latest_issue_type': latest_pending_issue.issue_type if latest_pending_issue else "",
            'latest_issue_record_date': latest_pending_issue.record_date if latest_pending_issue else None,

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
    
    # 沟通记录功能已移除
    deleted_communications = 0
    
    # 重置房间状态为初始值
    room.status = "整改中"
    room.delivery_status = "待交付"
    room.contract_status = "待签约"
    room.letter_status = "无"
    room.expected_delivery_date = None
    
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
        
        # 沟通记录功能已移除
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


def import_room_owners(db: Session, owner_data: List[dict]) -> dict:
    """批量导入房间户主信息（直接更新rooms表）"""
    total = len(owner_data)
    updated = 0
    errors = []
    
    for i, row in enumerate(owner_data, 1):
        try:
            # 验证必填字段
            if not row.get('building_unit') or not row.get('room_number'):
                errors.append(f"第{i}行：楼栋和房间号不能为空")
                continue
            
            # 查找对应的房间
            room = db.query(models.Room).filter(
                models.Room.building_unit == row['building_unit'],
                models.Room.room_number == row['room_number']
            ).first()
            
            if not room:
                errors.append(f"第{i}行：未找到对应房间 {row['building_unit']} {row['room_number']}")
                continue
            
            # 准备户主数据
            owner_name1 = row.get('owner_name1', '').strip() if row.get('owner_name1') else None
            owner_phone1 = row.get('owner_phone1', '').strip() if row.get('owner_phone1') else None
            owner_name2 = row.get('owner_name2', '').strip() if row.get('owner_name2') else None
            owner_phone2 = row.get('owner_phone2', '').strip() if row.get('owner_phone2') else None
            
            # 允许清空户主信息（用于重置），但如果填写了信息则需要完整
            # 注释掉强制验证，支持清空户主信息的需求
            
            # 直接更新rooms表的户主字段（支持清空）
            room.owner_name = owner_name1
            room.owner_phone = owner_phone1
            room.second_owner_name = owner_name2
            room.second_owner_phone = owner_phone2
            
            db.commit()
            updated += 1
                
        except Exception as e:
            errors.append(f"第{i}行：处理失败 - {str(e)}")
            db.rollback()
    
    return {
        'success': len(errors) == 0,
        'total': total,
        'updated': updated,
        'created': 0,  # 不再创建新记录，只更新现有房间
        'errors': errors
    }

def get_quality_issues_for_export(db: Session, room_ids: List[int], user_id: Optional[int] = None):
    """获取指定房间的质量问题数据用于Excel导出"""
    from sqlalchemy.orm import joinedload
    
    # 构建基础查询
    query = db.query(models.QualityIssue).options(
        joinedload(models.QualityIssue.user),
        joinedload(models.QualityIssue.room)
    ).filter(models.QualityIssue.room_id.in_(room_ids))
    
    # 如果指定了user_id，需要验证权限（只能导出分配给自己的房间）
    if user_id is not None:
        query = query.join(models.UserRoom, models.QualityIssue.room_id == models.UserRoom.room_id).filter(models.UserRoom.user_id == user_id)
    
    issues = query.all()
    
    # 构建导出数据
    export_data = []
    for issue in issues:
        # 获取用户显示信息
        user_display = ""
        if issue.user:
            role_map = {
                'customer_ambassador': '客户大使',
                'project_engineer': '项目工程师',
                'maintenance_engineer': '维修工程师'
            }
            role_text = role_map.get(issue.user.role, issue.user.role)
            user_display = f"{issue.user.name}({role_text})"
        
        export_data.append({
            "building_unit": issue.room.building_unit if issue.room else "",
            "room_number": issue.room.room_number if issue.room else "",
            "description": issue.description or "",
            "issue_type": issue.issue_type or "",
            "user_display": user_display,
            "record_date": issue.record_date or issue.created_at,
            "status": issue.status or "",
            "responsible_unit": issue.responsible_unit or "",
            "images": issue.images or "[]"
        })
    
    # 按房间号和录入时间排序
    export_data.sort(key=lambda x: (x["building_unit"], int(x["room_number"]) if x["room_number"].isdigit() else 999, x["record_date"] or datetime.min))
    
    return export_data

def import_user_room_assignments(db: Session, assignment_data: List[dict]) -> dict:
    """批量导入用户房间分配"""
    total = len(assignment_data)
    success_count = 0
    failed_count = 0
    errors = []
    
    # 角色映射
    role_map = {
        '客户大使': 'customer_ambassador',
        '项目工程师': 'project_engineer', 
        '维修工程师': 'maintenance_engineer',
        'customer_ambassador': 'customer_ambassador',
        'project_engineer': 'project_engineer',
        'maintenance_engineer': 'maintenance_engineer'
    }
    
    for i, item in enumerate(assignment_data, 1):
        try:
            # 验证必填字段
            if not all([item.get('username'), item.get('name'), item.get('role'), 
                       item.get('building_unit'), item.get('room_numbers')]):
                errors.append(f"第{i}行：用户名、姓名、角色、楼栋单元和房间号列表不能为空")
                failed_count += 1
                continue
            
            # 转换角色
            role = role_map.get(item['role'])
            if not role:
                errors.append(f"第{i}行：无效角色 '{item['role']}'，请使用：客户大使、项目工程师、维修工程师")
                failed_count += 1
                continue
            
            # 查找或创建用户
            user = db.query(models.User).filter(
                models.User.username == item['username']
            ).first()
            
            if not user:
                # 创建新用户
                try:
                    initial_password = generate_initial_password()
                    user = models.User(
                        username=item['username'],
                        name=item['name'],
                        role=role,
                        password=auth.get_password_hash(initial_password),
                        initial_password=initial_password,
                        password_changed=False
                    )
                    db.add(user)
                    db.flush()  # 获取用户ID但不提交事务
                except Exception as e:
                    errors.append(f"第{i}行：创建用户失败 - {str(e)}")
                    failed_count += 1
                    db.rollback()
                    continue
            else:
                # 验证现有用户信息
                if user.name != item['name']:
                    errors.append(f"第{i}行：用户名 '{item['username']}' 已存在但姓名不匹配（现有：{user.name}，导入：{item['name']}）")
                    failed_count += 1
                    continue
                
                if user.role != role:
                    errors.append(f"第{i}行：用户名 '{item['username']}' 已存在但角色不匹配（现有：{user.role}，导入：{role}）")
                    failed_count += 1
                    continue
            
            # 处理房间分配
            room_assignment_count = 0
            for room_number in item['room_numbers']:
                if not room_number or not room_number.strip():
                    continue
                
                # 查找房间
                room = db.query(models.Room).filter(
                    models.Room.building_unit == item['building_unit'],
                    models.Room.room_number == room_number.strip()
                ).first()
                
                if not room:
                    errors.append(f"第{i}行：未找到房间 {item['building_unit']}-{room_number}")
                    continue
                
                # 检查是否已分配
                existing_assignment = db.query(models.UserRoom).filter(
                    models.UserRoom.user_id == user.id,
                    models.UserRoom.room_id == room.id
                ).first()
                
                if existing_assignment:
                    # 已分配，跳过
                    continue
                
                # 创建新分配
                assignment = models.UserRoom(
                    user_id=user.id,
                    room_id=room.id
                )
                db.add(assignment)
                room_assignment_count += 1
            
            if room_assignment_count > 0:
                db.commit()
                success_count += 1
            else:
                # 用户存在但没有新的房间分配
                if user.id:  # 如果用户已存在
                    success_count += 1
                else:
                    db.rollback()
                    errors.append(f"第{i}行：用户创建成功但没有有效的房间分配")
                    failed_count += 1
                
        except Exception as e:
            errors.append(f"第{i}行：处理失败 - {str(e)}")
            failed_count += 1
            db.rollback()
    
    return {
        'success': failed_count == 0,
        'total': total,
        'success_count': success_count,
        'failed_count': failed_count,
        'errors': errors
    }