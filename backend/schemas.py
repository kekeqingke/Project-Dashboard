from pydantic import BaseModel, computed_field, field_validator, field_serializer
from datetime import datetime, date
from typing import List, Optional, Any
import re

# User schemas
class UserBase(BaseModel):
    username: str
    name: str
    role: str

class UserCreate(UserBase):
    password: Optional[str] = None  # 可选，如果不提供则自动生成

class User(UserBase):
    id: int
    initial_password: Optional[str] = None
    password_changed: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserCreateResponse(BaseModel):
    user: User
    initial_password: str

# Password change schemas
class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('密码长度至少8位')
        
        if not re.search(r'[A-Z]', v):
            raise ValueError('密码必须包含大写字母')
        
        if not re.search(r'[a-z]', v):
            raise ValueError('密码必须包含小写字母')
        
        if not re.search(r'\d', v):
            raise ValueError('密码必须包含数字')
        
        return v

class PasswordChangeResponse(BaseModel):
    message: str
    success: bool

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    user: User
    first_login: bool = False

# Room schemas
class RoomBase(BaseModel):
    building_unit: str
    room_number: str
    status: str = "整改中"
    delivery_status: str = "待交付"
    contract_status: str = "待签约"
    letter_status: str = "无"
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
    expected_delivery_date: Optional[date] = None
    
    # Aggregated fields for quality issues
    pending_issues_count: int = 0
    latest_issue_description: str = ""
    latest_issue_type: str = ""
    latest_issue_record_date: Optional[datetime] = None
    
    
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
    record_date: Optional[datetime] = None  # 录入时间，接收日期字符串格式如 "2025-09-11" 或 "2025/09/11"
    responsible_unit: Optional[str] = None  # 责任单位
    
    @field_validator('record_date', mode='before')
    @classmethod
    def parse_record_date(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            # 支持多种日期字符串格式
            if len(v) == 10:
                if v[4] == '-' and v[7] == '-':
                    # YYYY-MM-DD格式
                    try:
                        return datetime.strptime(v, '%Y-%m-%d')
                    except ValueError:
                        pass
                elif v[4] == '/' and v[7] == '/':
                    # YYYY/MM/DD格式
                    try:
                        return datetime.strptime(v, '%Y/%m/%d')
                    except ValueError:
                        pass
        # 如果已经是datetime对象或其他格式，保持原样
        return v

class QualityIssueCreate(QualityIssueBase):
    pass

class QualityIssueUpdate(BaseModel):
    description: Optional[str] = None
    issue_type: Optional[str] = None
    record_date: Optional[datetime] = None
    responsible_unit: Optional[str] = None
    
    @field_validator('record_date', mode='before')
    @classmethod
    def parse_record_date(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            # 支持多种日期字符串格式
            if len(v) == 10:
                if v[4] == '-' and v[7] == '-':
                    # YYYY-MM-DD格式
                    try:
                        return datetime.strptime(v, '%Y-%m-%d')
                    except ValueError:
                        pass
                elif v[4] == '/' and v[7] == '/':
                    # YYYY/MM/DD格式
                    try:
                        return datetime.strptime(v, '%Y/%m/%d')
                    except ValueError:
                        pass
        # 如果已经是datetime对象或其他格式，保持原样
        return v

class QualityIssue(QualityIssueBase):
    id: int
    user_id: int
    status: str
    issue_type: str
    accepted_by: Optional[int] = None
    accepted_at: Optional[datetime] = None
    record_date: Optional[datetime] = None  # 录入时间
    created_at: datetime
    
    # 用户相关字段
    user_name: Optional[str] = None
    user_role: Optional[str] = None
    acceptor_name: Optional[str] = None
    acceptor_role: Optional[str] = None
    
    is_verified: Optional[bool] = None
    
    def model_post_init(self, __context) -> None:
        """模型初始化后设置is_verified字段"""
        if hasattr(self, 'status'):
            self.is_verified = self.status == "已验收"
    
    class Config:
        from_attributes = True

# 操作日志相关schemas
class QualityIssueLogBase(BaseModel):
    issue_id: int
    action: str
    operator_id: int
    operator_name: Optional[str] = None
    operator_role: Optional[str] = None
    before_data: Optional[str] = None
    after_data: Optional[str] = None
    remarks: Optional[str] = None

class QualityIssueLogCreate(QualityIssueLogBase):
    pass

class QualityIssueLog(QualityIssueLogBase):
    id: int
    timestamp: datetime
    
    @field_serializer('timestamp')
    def serialize_timestamp(self, value: datetime) -> str:
        """确保timestamp序列化为UTC时间格式"""
        if value:
            # 如果datetime没有时区信息，假设它是UTC时间
            if value.tzinfo is None:
                return value.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
            else:
                return value.isoformat()
        return None
    
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

# 用户房间分配导入相关schemas
class UserRoomAssignmentImportItem(BaseModel):
    username: str  # 用户名
    name: str      # 姓名
    role: str      # 角色
    building_unit: str    # 楼栋单元
    room_numbers: List[str]  # 房间号列表

class UserRoomAssignmentImportResult(BaseModel):
    success: bool
    total: int
    success_count: int
    failed_count: int
    errors: List[str] = []