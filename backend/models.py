from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    name = Column(String)
    role = Column(String)  # admin, customer_ambassador, project_engineer, maintenance_engineer
    initial_password = Column(String, nullable=True)  # 存储初始密码（明文，仅用于管理员查看）
    password_changed = Column(Boolean, default=False)  # 标记密码是否已修改
    created_at = Column(DateTime, server_default=func.now())
    
    # 关系
    room_assignments = relationship("UserRoom", back_populates="user")
    quality_issues = relationship("QualityIssue", back_populates="user", foreign_keys="QualityIssue.user_id")
    communications = relationship("Communication", back_populates="user")

class Room(Base):
    __tablename__ = "rooms"
    
    id = Column(Integer, primary_key=True, index=True)
    building_unit = Column(String)  # 3单元, 4单元
    room_number = Column(String)  # 101, 201, 303等
    status = Column(String, default="整改中")  # 整改中, 验收完成, 闭户
    delivery_status = Column(String, default="待交付")  # 待交付, 已交付
    contract_status = Column(String, default="待签约")  # 待签约, 已签约
    letter_status = Column(String, default="无")  # 无, ZX, SX
    pre_leakage = Column(String, default="无")  # 无, 有
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关系
    user_assignments = relationship("UserRoom", back_populates="room")
    quality_issues = relationship("QualityIssue", back_populates="room")
    communications = relationship("Communication", back_populates="room")

class UserRoom(Base):
    __tablename__ = "user_rooms"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    room_id = Column(Integer, ForeignKey("rooms.id"))
    created_at = Column(DateTime, server_default=func.now())
    
    # 关系
    user = relationship("User", back_populates="room_assignments")
    room = relationship("Room", back_populates="user_assignments")

class QualityIssue(Base):
    __tablename__ = "quality_issues"
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    description = Column(Text)
    issue_type = Column(String, default="质量瑕疵")  # 质量瑕疵, 材料备货
    images = Column(Text)  # JSON字符串存储图片路径
    status = Column(String, default="待验收")  # 待验收, 已验收
    accepted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    accepted_at = Column(DateTime, nullable=True)
    record_date = Column(DateTime, nullable=True)  # 录入时间（用户指定的日期）
    created_at = Column(DateTime, server_default=func.now())
    
    # 关系
    room = relationship("Room", back_populates="quality_issues")
    user = relationship("User", back_populates="quality_issues", foreign_keys=[user_id])
    acceptor = relationship("User", foreign_keys=[accepted_by])

class Communication(Base):
    __tablename__ = "communications"
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text)
    communication_time = Column(DateTime, nullable=True)
    feedback = Column(Text)
    customer_description = Column(Text, nullable=True)  # 客户描摹
    image = Column(String(255), nullable=True)  # 沟通记录图片文件名
    is_implemented = Column(Boolean, default=False)  # 是否已落实
    created_at = Column(DateTime, server_default=func.now())
    
    # 关系
    room = relationship("Room", back_populates="communications")
    user = relationship("User", back_populates="communications")