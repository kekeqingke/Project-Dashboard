from pydantic import BaseModel, computed_field, field_validator
from datetime import datetime, date
from typing import List, Optional, Any
import re

# User schemas
class UserBase(BaseModel):
    username: str
    name: str
    role: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    initial_password: Optional[str] = None
    password_changed: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

# Room schemas
class RoomBase(BaseModel):
    building_unit: str
    room_number: str
    status: str = "整改中"
    delivery_status: str = "待交付"
    contract_status: str = "待签约"
    letter_status: str = "无"
    pre_leakage: str = "无"
    expected_delivery_date: Optional[date] = None

class RoomCreate(RoomBase):
    pass

class Room(RoomBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    assigned_users: Optional[List[Any]] = []
    
    # 户主信息字段
    owner_name: Optional[str] = None
    owner_phone: Optional[str] = None
    second_owner_name: Optional[str] = None
    second_owner_phone: Optional[str] = None
    
    class Config:
        from_attributes = True

# Room summary schema with aggregated fields for admin dashboard
class RoomSummary(RoomBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    letter_status: str = "无"
    pre_leakage: str = "无"
    expected_delivery_date: Optional[date] = None
    
    # Aggregated fields for quality issues
    pending_issues_count: int = 0
    latest_issue_description: str = ""
    latest_issue_type: str = ""
    latest_issue_record_date: Optional[datetime] = None
    
    # Aggregated fields for communications
    pending_communications_count: int = 0
    latest_comm_content: str = ""
    latest_comm_time: Optional[datetime] = None
    
    # Latest feedback
    latest_feedback: str = ""
    
    # Customer/Owner information
    owner_name: Optional[str] = None  # 户主姓名（格式化后的）
    owner_phone: Optional[str] = None  # 户主手机号（格式化后的）
    
    class Config:
        from_attributes = True

# Room assignment schemas
class RoomAssignmentCreate(BaseModel):
    user_id: int
    room_id: int

# Quality Issue schemas
class QualityIssueBase(BaseModel):
    room_id: int
    description: str
    issue_type: Optional[str] = "质量瑕疵"
    images: Optional[str] = None
    record_date: Optional[datetime] = None  # 录入时间

class QualityIssueCreate(QualityIssueBase):
    pass

class QualityIssueUpdate(BaseModel):
    description: Optional[str] = None
    issue_type: Optional[str] = None
    record_date: Optional[datetime] = None

class QualityIssue(QualityIssueBase):
    id: int
    user_id: int
    status: str
    issue_type: str
    accepted_by: Optional[int] = None
    accepted_at: Optional[datetime] = None
    revoked_by: Optional[int] = None
    revoked_at: Optional[datetime] = None
    reverified_by: Optional[int] = None
    reverified_at: Optional[datetime] = None
    record_date: Optional[datetime] = None  # 录入时间
    created_at: datetime
    
    # 用户相关字段
    user_name: Optional[str] = None
    user_role: Optional[str] = None
    acceptor_name: Optional[str] = None
    acceptor_role: Optional[str] = None
    revoker_name: Optional[str] = None
    revoker_role: Optional[str] = None
    reverifier_name: Optional[str] = None
    reverifier_role: Optional[str] = None
    
    is_verified: Optional[bool] = None
    
    def model_post_init(self, __context) -> None:
        """模型初始化后设置is_verified字段"""
        if hasattr(self, 'status'):
            self.is_verified = self.status in ["已验收", "已复验"]
    
    class Config:
        from_attributes = True



# Excel导入相关schemas
class OwnerImportItem(BaseModel):
    building_unit: str  # 楼栋
    room_number: str    # 房间号
    owner_name1: Optional[str] = None    # 户主姓名1
    owner_phone1: Optional[str] = None   # 手机号码1
    owner_name2: Optional[str] = None    # 户主姓名2（可选）
    owner_phone2: Optional[str] = None   # 手机号码2（可选）

class OwnerImportResult(BaseModel):
    success: bool
    total: int
    updated: int
    created: int
    errors: List[str] = []