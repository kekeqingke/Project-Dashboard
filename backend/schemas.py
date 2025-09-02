from pydantic import BaseModel, computed_field
from datetime import datetime
from typing import List, Optional, Any

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

class RoomCreate(RoomBase):
    pass

class Room(RoomBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    assigned_users: Optional[List[Any]] = []
    
    class Config:
        from_attributes = True

# Room summary schema with aggregated fields for admin dashboard
class RoomSummary(RoomBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    letter_status: str = "无"
    pre_leakage: str = "无"
    
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
    
    is_verified: Optional[bool] = None
    
    def model_post_init(self, __context) -> None:
        """模型初始化后设置is_verified字段"""
        if hasattr(self, 'status'):
            self.is_verified = self.status == "已验收"
    
    class Config:
        from_attributes = True

# Communication schemas
class CommunicationBase(BaseModel):
    room_id: int
    content: str
    communication_time: Optional[datetime] = None
    feedback: Optional[str] = None
    customer_description: Optional[str] = None  # 客户描摹
    image: Optional[str] = None  # 沟通记录图片文件名

class CommunicationCreate(CommunicationBase):
    pass

class CommunicationUpdate(BaseModel):
    is_implemented: bool

class Communication(CommunicationBase):
    id: int
    user_id: int
    communication_time: Optional[datetime] = None
    customer_description: Optional[str] = None  # 客户描摹
    image: Optional[str] = None  # 沟通记录图片文件名
    is_implemented: bool = False  # 是否已落实
    created_at: datetime
    
    class Config:
        from_attributes = True