from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
import models, schemas, crud
from database import SessionLocal, engine, get_db
import auth
from typing import List, Optional
import os
import uuid
import shutil
import io
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from datetime import datetime
from urllib.parse import quote

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="ZWY项目信息跟踪管理系统", version="1.0.0")

# 创建上传文件夹
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 挂载静态文件目录
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"],  # Vue开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/")
async def root():
    return {"message": "ZWY项目信息跟踪管理系统 API", "status": "运行中"}

@app.post("/token", response_model=schemas.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.username})
    # 检查是否首次登录
    first_login = not user.password_changed
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "user": user,
        "first_login": first_login
    }

@app.get("/users/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

@app.post("/users/change-password", response_model=schemas.PasswordChangeResponse)
async def change_password(
    password_data: schemas.PasswordChangeRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # 验证当前密码
    if not auth.verify_password(password_data.current_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前密码错误"
        )
    
    # 检查新密码不能与当前密码相同
    if auth.verify_password(password_data.new_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码不能与当前密码相同"
        )
    
    # 更新密码
    current_user.password = auth.get_password_hash(password_data.new_password)
    current_user.password_changed = True
    db.commit()
    
    return schemas.PasswordChangeResponse(
        message="密码修改成功",
        success=True
    )

# 用户管理接口
@app.post("/users/", response_model=schemas.UserCreateResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db), 
                current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 生成初始密码
    initial_password = user.password if user.password else crud.generate_initial_password()
    
    # 创建用户
    created_user = crud.create_user(db=db, user=user)
    
    return schemas.UserCreateResponse(
        user=created_user,
        initial_password=initial_password
    )

@app.get("/users/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
               current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")
    return crud.get_users(db, skip=skip, limit=limit)

@app.put("/users/{user_id}/reset-password", response_model=schemas.User)
def reset_user_password(user_id: int, db: Session = Depends(get_db),
                       current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")
    
    user = crud.reset_user_password(db=db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user

@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db),
                current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 防止删除管理员账户
    user = crud.get_user(db=db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if user.role == "admin":
        raise HTTPException(status_code=400, detail="无法删除管理员账户")
    
    success = crud.delete_user(db=db, user_id=user_id)
    if not success:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return {"message": "用户删除成功"}

# 房间管理接口
@app.get("/rooms/", response_model=List[schemas.Room])
def read_rooms(db: Session = Depends(get_db), 
               current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role == "admin":
        return crud.get_rooms(db)
    else:
        return crud.get_user_rooms(db, current_user.id)

@app.get("/rooms/{room_id}", response_model=schemas.Room)
def get_room(room_id: int, db: Session = Depends(get_db),
             current_user: models.User = Depends(auth.get_current_user)):
    room = crud.get_room_by_id(db=db, room_id=room_id, user_id=current_user.id if current_user.role != "admin" else None)
    if not room:
        raise HTTPException(status_code=404, detail="房间不存在或无权限访问")
    return room

@app.post("/rooms/", response_model=schemas.Room)
def create_room(room: schemas.RoomCreate, db: Session = Depends(get_db),
                current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")
    return crud.create_room(db=db, room=room)

@app.delete("/rooms/{room_id}")
def delete_room(room_id: int, db: Session = Depends(get_db),
                current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")
    
    success = crud.delete_room(db=db, room_id=room_id)
    if not success:
        raise HTTPException(status_code=404, detail="房间不存在")
    
    return {"message": "房间删除成功"}


# 房间分配接口
@app.get("/room-assignments/")
def get_room_assignments(db: Session = Depends(get_db),
                        current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role == "admin":
        # 管理员可以查看所有房间分配
        return crud.get_room_assignments(db=db)
    else:
        # 其他角色只能查看分配给自己的房间
        return crud.get_user_room_assignments(db=db, user_id=current_user.id)

@app.post("/room-assignments/")
def assign_room(assignment: schemas.RoomAssignmentCreate, db: Session = Depends(get_db),
                current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")
    return crud.assign_room_to_user(db=db, user_id=assignment.user_id, room_id=assignment.room_id)

@app.delete("/room-assignments/{assignment_id}")
def delete_room_assignment(assignment_id: int, db: Session = Depends(get_db),
                          current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")
    success = crud.delete_room_assignment(db=db, assignment_id=assignment_id)
    if not success:
        raise HTTPException(status_code=404, detail="分配关系不存在")
    return {"message": "删除成功"}

# 质量问题管理接口
@app.get("/quality-issues/", response_model=List[schemas.QualityIssue])
def read_quality_issues(room_id: int = None, db: Session = Depends(get_db),
                       current_user: models.User = Depends(auth.get_current_user)):
    return crud.get_quality_issues(db, room_id, current_user.id if current_user.role != "admin" else None)

@app.post("/quality-issues/", response_model=schemas.QualityIssue)
def create_quality_issue(issue: schemas.QualityIssueCreate, db: Session = Depends(get_db),
                        current_user: models.User = Depends(auth.get_current_user)):
    """创建质量问题 - 限制客户大使和维修工程师"""
    allowed_roles = ["customer_ambassador", "maintenance_engineer", "project_engineer"]
    if current_user.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="权限不足，无法创建质量问题")
    return crud.create_quality_issue(db=db, issue=issue, user_id=current_user.id)

@app.put("/quality-issues/{issue_id}/accept")
def accept_quality_issue(issue_id: int, db: Session = Depends(get_db),
                        current_user: models.User = Depends(auth.get_current_user)):
    """验收质量问题 - 限制项目工程师"""
    if current_user.role != "project_engineer":
        raise HTTPException(status_code=403, detail="只有项目工程师可以验收质量问题")
    
    result = crud.accept_quality_issue(db=db, issue_id=issue_id, user_id=current_user.id)
    if not result:
        raise HTTPException(status_code=400, detail="验收失败，请检查问题状态")
    return {"message": "验收成功", "issue": result}

@app.delete("/quality-issues/{issue_id}/accept")  
def revoke_accept_quality_issue(issue_id: int, db: Session = Depends(get_db),
                               current_user: models.User = Depends(auth.get_current_user)):
    """撤销验收 - 24小时内且只能撤销自己的验收"""
    result = crud.revoke_accept_quality_issue(db=db, issue_id=issue_id, user_id=current_user.id)
    if not result:
        raise HTTPException(status_code=400, detail="撤销失败，可能已超过24小时限制或非本人验收")
    return {"message": "撤销成功", "issue": result}

@app.get("/quality-issues/{issue_id}", response_model=schemas.QualityIssue)
def get_quality_issue(issue_id: int, db: Session = Depends(get_db),
                     current_user: models.User = Depends(auth.get_current_user)):
    """获取单个质量问题详情"""
    issue = crud.get_quality_issue_by_id(db=db, issue_id=issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="质量问题不存在")
    return issue

@app.get("/quality-issues/{issue_id}/logs", response_model=List[schemas.QualityIssueLog])
def get_quality_issue_logs(issue_id: int, db: Session = Depends(get_db),
                          current_user: models.User = Depends(auth.get_current_user)):
    """获取质量问题操作日志"""
    return crud.get_quality_issue_logs(db=db, issue_id=issue_id)

@app.put("/quality-issues/{issue_id}/responsible-unit")
def update_responsible_unit(issue_id: int, responsible_unit: dict, db: Session = Depends(get_db),
                           current_user: models.User = Depends(auth.get_current_user)):
    """项目工程师更新质量问题的责任单位"""
    if current_user.role != "project_engineer":
        raise HTTPException(status_code=403, detail="只有项目工程师可以分配责任单位")

    unit_name = responsible_unit.get("responsible_unit", "").strip()
    if not unit_name:
        raise HTTPException(status_code=400, detail="责任单位不能为空")

    result = crud.update_responsible_unit(db=db, issue_id=issue_id,
                                        responsible_unit=unit_name, user_id=current_user.id)
    if not result:
        raise HTTPException(status_code=404, detail="质量问题不存在或无权限操作")

    return {"message": "责任单位更新成功", "responsible_unit": unit_name}

@app.put("/quality-issues/{issue_id}", response_model=schemas.QualityIssue)
def update_quality_issue(issue_id: int, issue_update: schemas.QualityIssueUpdate,
                        db: Session = Depends(get_db),
                        current_user: models.User = Depends(auth.get_current_user)):
    """更新质量问题 - 只允许创建人修改待验收状态的问题"""
    result = crud.update_quality_issue(db=db, issue_id=issue_id, 
                                      issue_update=issue_update, user_id=current_user.id)
    if not result:
        raise HTTPException(status_code=403, detail="无权限修改此问题或问题已验收")
    return result

@app.delete("/quality-issues/{issue_id}")
def delete_quality_issue(issue_id: int, db: Session = Depends(get_db),
                        current_user: models.User = Depends(auth.get_current_user)):
    """删除质量问题 - 仅管理员可操作"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足，仅管理员可删除质量问题")
    
    success = crud.delete_quality_issue(db=db, issue_id=issue_id)
    if not success:
        raise HTTPException(status_code=404, detail="质量问题不存在")
    return {"message": "质量问题删除成功"}

# 质量问题Excel导出接口
@app.get("/export-quality-issues")
def export_quality_issues(
    room_ids: str = Query(..., description="房间ID列表，用逗号分隔"),
    status_filter: str = Query("all", description="状态筛选: all/pending/completed"),
    issue_type: str = Query("", description="问题类型筛选: 质量瑕疵/材料备货"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """导出指定房间的质量问题Excel文件"""
    try:
        # 解析房间ID列表
        room_id_list = [int(id.strip()) for id in room_ids.split(',') if id.strip()]
        if not room_id_list:
            raise HTTPException(status_code=400, detail="请选择要导出的房间")
        
        # 获取质量问题数据
        issues_data = crud.get_quality_issues_for_export(db, room_id_list, current_user.id if current_user.role != "admin" else None)
        
        # 根据状态筛选
        if status_filter == "pending":
            issues_data = [issue for issue in issues_data if issue["status"] == "待验收"]
        elif status_filter == "completed":
            issues_data = [issue for issue in issues_data if issue["status"] == "已验收"]

        # 根据问题类型筛选
        if issue_type and issue_type.strip():
            issues_data = [issue for issue in issues_data if issue["issue_type"] == issue_type.strip()]

        if not issues_data:
            raise HTTPException(status_code=404, detail="未找到符合条件的质量问题数据")
        
        # 创建Excel工作簿
        wb = Workbook()
        ws = wb.active
        ws.title = "质量问题清单"
        
        # 设置标题行
        headers = [
            "楼栋", "房号", "问题描述", "问题类型", "记录人", "录入时间", 
            "问题状态", "责任单位"
        ]
        
        # 写入标题行
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
            cell.fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
        
        # 写入数据行
        for row_idx, issue in enumerate(issues_data, 2):
            ws.cell(row=row_idx, column=1, value=issue.get("building_unit", ""))
            ws.cell(row=row_idx, column=2, value=format_room_number(issue.get("room_number", "")))
            ws.cell(row=row_idx, column=3, value=issue.get("description", ""))
            ws.cell(row=row_idx, column=4, value=issue.get("issue_type", ""))
            ws.cell(row=row_idx, column=5, value=issue.get("user_display", ""))
            
            # 录入时间格式化
            record_date = issue.get("record_date")
            if record_date:
                if isinstance(record_date, str):
                    ws.cell(row=row_idx, column=6, value=record_date[:10])  # 取日期部分
                else:
                    ws.cell(row=row_idx, column=6, value=record_date.strftime("%Y-%m-%d"))
            else:
                ws.cell(row=row_idx, column=6, value="")
            
            ws.cell(row=row_idx, column=7, value=issue.get("status", ""))
            ws.cell(row=row_idx, column=8, value=issue.get("responsible_unit", ""))  # 责任单位
        
        # 自动调整列宽
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 30)  # 最大宽度30
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # 保存到内存
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        # 生成文件名
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        status_text = {"all": "全部", "pending": "待验收", "completed": "已验收"}.get(status_filter, "全部")
        filename = f"质量问题清单_{status_text}_{current_time}.xlsx"
        encoded_filename = quote(filename, safe='')
        
        # 返回文件流
        return StreamingResponse(
            io.BytesIO(output.getvalue()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename*=UTF-8\'\'{encoded_filename}',
                "Cache-Control": "no-cache",
                "Pragma": "no-cache"
            }
        )
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Export quality issues error: {str(e)}")
        print(f"Error details: {error_details}")
        raise HTTPException(status_code=500, detail=f"导出质量问题Excel文件失败: {str(e)}")

# 房间状态更新接口
@app.put("/rooms/{room_id}/delivery-status")
async def update_room_delivery_status(
    room_id: int,
    delivery_status: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # 只有管理员和客户大使可以更新房间状态
    if current_user.role not in ["admin", "customer_ambassador"]:
        raise HTTPException(status_code=403, detail="权限不足")
    
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="房间不存在")
    
    # 验证状态值
    if delivery_status not in ["待交付", "已交付"]:
        raise HTTPException(status_code=400, detail="无效的交付状态")
    
    room.delivery_status = delivery_status
    db.commit()
    db.refresh(room)
    
    return {"message": "交付状态更新成功", "delivery_status": delivery_status}

@app.put("/rooms/{room_id}/contract-status")
async def update_room_contract_status(
    room_id: int,
    contract_status: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # 只有管理员和客户大使可以更新房间状态
    if current_user.role not in ["admin", "customer_ambassador"]:
        raise HTTPException(status_code=403, detail="权限不足")
    
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="房间不存在")
    
    # 验证状态值
    if contract_status not in ["待签约", "已签约"]:
        raise HTTPException(status_code=400, detail="无效的签约状态")
    
    room.contract_status = contract_status
    db.commit()
    db.refresh(room)
    
    return {"message": "签约状态更新成功", "contract_status": contract_status}

@app.put("/rooms/{room_id}/letter-status")
async def update_room_letter_status(
    room_id: int,
    letter_status: str = Query(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # 只有管理员和客户大使可以更新房间状态
    if current_user.role not in ["admin", "customer_ambassador"]:
        raise HTTPException(status_code=403, detail="权限不足")
    
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="房间不存在")
    
    # 验证状态值
    if letter_status not in ["无", "ZX", "SX", "ZX+SX"]:
        raise HTTPException(status_code=400, detail="无效的信件状态")
    
    room.letter_status = letter_status
    db.commit()
    db.refresh(room)
    
    return {"message": "信件状态更新成功", "letter_status": letter_status}

# 前期渗漏字段已删除，相关接口也已删除

@app.put("/rooms/{room_id}/expected-delivery-date")
async def update_room_expected_delivery_date(
    room_id: int,
    expected_delivery_date: str = Query(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # 只有管理员和客户大使可以更新房间状态
    if current_user.role not in ["admin", "customer_ambassador"]:
        raise HTTPException(status_code=403, detail="权限不足")
    
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="房间不存在")
    
    # 解析日期字符串
    from datetime import datetime
    try:
        if expected_delivery_date:
            parsed_date = datetime.strptime(expected_delivery_date, '%Y-%m-%d').date()
            room.expected_delivery_date = parsed_date
        else:
            room.expected_delivery_date = None
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式不正确，应为YYYY-MM-DD")
    
    db.commit()
    db.refresh(room)
    
    return {"message": "预计交付时间更新成功", "expected_delivery_date": expected_delivery_date}

# 客户大使专用状态更新接口
@app.put("/rooms/{room_id}/ambassador-status")
async def update_room_ambassador_status(
    room_id: int,
    status_data: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """客户大使更新房间状态（仅允许特定字段）"""
    # 只有管理员和客户大使可以更新
    if current_user.role not in ["admin", "customer_ambassador"]:
        raise HTTPException(status_code=403, detail="权限不足")
    
    room = crud.update_room_ambassador_status(db=db, room_id=room_id, status_data=status_data)
    if not room:
        raise HTTPException(status_code=404, detail="房间不存在")
    
    return {
        "message": "房间状态更新成功",
        "room_id": room_id,
        "updated_fields": {k: v for k, v in status_data.items() if k in ['delivery_status', 'contract_status', 'letter_status', 'expected_delivery_date']}
    }

# 文件上传接口
@app.post("/upload-image/")
async def upload_image(file: UploadFile = File(...), 
                      current_user: models.User = Depends(auth.get_current_user)):
    # 检查文件类型
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="只能上传图片文件")
    
    # 生成唯一文件名
    file_extension = file.filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # 保存文件
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"filename": unique_filename, "url": f"/uploads/{unique_filename}"}

# 管理员汇总接口
@app.get("/admin/summary")
def get_summary(building_unit: str = None, db: Session = Depends(get_db),
                current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")
    return crud.get_room_summary(db, building_unit)


# 清空房间内容接口
@app.delete("/admin/rooms/{room_id}/clear-content")
def clear_room_content(room_id: int, db: Session = Depends(get_db),
                      current_user: models.User = Depends(auth.get_current_user)):
    """清空指定房间的内容数据，保留用户分配和房号"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="只有管理员可以执行此操作")
    
    result = crud.clear_room_content(db=db, room_id=room_id)
    if not result:
        raise HTTPException(status_code=404, detail="房间不存在")
    
    return result

# 重置房间接口
@app.post("/admin/rooms/{room_id}/reset")
def reset_room(room_id: int, db: Session = Depends(get_db),
               current_user: models.User = Depends(auth.get_current_user)):
    """重置房间到初始状态，删除所有质量问题记录，重置状态字段"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="只有管理员可以执行此操作")
    
    result = crud.clear_room_content(db=db, room_id=room_id)
    if not result:
        raise HTTPException(status_code=404, detail="房间不存在")
    
    return {
        "message": f"房间重置成功",
        "room_id": room_id,
        "details": result
    }

@app.delete("/admin/rooms/clear-all-content")
def clear_all_rooms_content(db: Session = Depends(get_db),
                           current_user: models.User = Depends(auth.get_current_user)):
    """清空所有房间的内容数据，保留用户分配和房号"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="只有管理员可以执行此操作")
    
    result = crud.clear_all_rooms_content(db=db)
    return result

# Excel导入户主信息接口
@app.post("/admin/import-room-owners", response_model=schemas.OwnerImportResult)
def import_room_owners(owner_data: List[schemas.OwnerImportItem], 
                      db: Session = Depends(get_db),
                      current_user: models.User = Depends(auth.get_current_user)):
    """批量导入房间户主信息"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足，只有管理员可以导入数据")
    
    # 转换为dict格式
    owner_dict_data = []
    for item in owner_data:
        owner_dict_data.append({
            'building_unit': item.building_unit,
            'room_number': item.room_number,
            'owner_name1': item.owner_name1,
            'owner_phone1': item.owner_phone1,
            'owner_name2': item.owner_name2,
            'owner_phone2': item.owner_phone2,
        })
    
    result = crud.import_room_owners(db=db, owner_data=owner_dict_data)
    return result

# Excel导入用户房间分配接口
@app.post("/admin/import-user-room-assignments", response_model=schemas.UserRoomAssignmentImportResult)
def import_user_room_assignments(assignment_data: List[schemas.UserRoomAssignmentImportItem], 
                                db: Session = Depends(get_db),
                                current_user: models.User = Depends(auth.get_current_user)):
    """批量导入用户房间分配"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足，只有管理员可以导入数据")
    
    # 转换为dict格式
    assignment_dict_data = []
    for item in assignment_data:
        assignment_dict_data.append({
            'username': item.username,
            'name': item.name,
            'role': item.role,
            'building_unit': item.building_unit,
            'room_numbers': item.room_numbers,
        })
    
    result = crud.import_user_room_assignments(db=db, assignment_data=assignment_dict_data)
    return result

# 房间号格式化函数
def format_room_number(room_number):
    """格式化房间号：3-9楼去掉前导0，10楼以上保持4位数"""
    if not room_number:
        return room_number

    # 如果房间号是4位数字且前两位是03-09，去掉前导0
    import re
    if re.match(r'^0[3-9]\d{2}$', str(room_number)):
        return str(room_number)[1:]

    # 其他情况保持原样（如1201等高楼层）
    return str(room_number)

# Excel导出接口
@app.get("/admin/export")
def export_to_excel(
    building_unit: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    delivery_status: Optional[str] = Query(None),
    contract_status: Optional[str] = Query(None),
    issue_filter: Optional[str] = Query(None),
    letter_filter: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """导出Excel文件，支持筛选条件"""
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="权限不足")
        
        # 获取汇总数据
        summary_data = crud.get_room_summary(db, None)
        rooms = summary_data["rooms"]
        
        # 应用筛选条件
        filtered_rooms = []
        for room in rooms:
            # 楼栋筛选
            if building_unit and room.get("building_unit") != building_unit:
                continue
            
            # 整改状态筛选
            if status and room.get("status") != status:
                continue
            
            # 交付状态筛选
            if delivery_status and room.get("delivery_status") != delivery_status:
                continue
            
            # 签约状态筛选
            if contract_status and room.get("contract_status") != contract_status:
                continue
            
            # 问题筛选
            if issue_filter:
                has_issues = (room.get("pending_issues_count") or 0) > 0
                if issue_filter == "has_issues" and not has_issues:
                    continue
                if issue_filter == "no_issues" and has_issues:
                    continue
            
            # 信件状态筛选
            if letter_filter:
                letter_status = room.get("letter_status") or "无"
                if letter_status != letter_filter:
                    continue
            
            filtered_rooms.append(room)
        
        # 创建Excel工作簿
        wb = Workbook()
        ws = wb.active
        ws.title = "房间信息汇总"
        
        # 设置标题行
        headers = [
            "楼栋", "房间号", "户主姓名", "手机号码", "整改状态", 
            "交付状态", "签约状态", "待验收", "预计交付时间", "信件状态"
        ]
        
        # 写入标题行
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
            cell.fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
        
        # 写入数据行
        for row_idx, room in enumerate(filtered_rooms, 2):
            ws.cell(row=row_idx, column=1, value=room.get("building_unit", ""))
            ws.cell(row=row_idx, column=2, value=format_room_number(room.get("room_number", "")))
            ws.cell(row=row_idx, column=3, value=room.get("owner_name", "") or "未录入")
            ws.cell(row=row_idx, column=4, value=room.get("owner_phone", "") or "未录入")
            ws.cell(row=row_idx, column=5, value=room.get("status", ""))
            ws.cell(row=row_idx, column=6, value=room.get("delivery_status", ""))
            ws.cell(row=row_idx, column=7, value=room.get("contract_status", ""))
            ws.cell(row=row_idx, column=8, value=room.get("pending_issues_count", 0))
            
            # 处理日期格式
            expected_delivery = room.get("expected_delivery_date")
            if expected_delivery:
                if isinstance(expected_delivery, str):
                    try:
                        date_obj = datetime.fromisoformat(expected_delivery.replace('Z', '+00:00'))
                        ws.cell(row=row_idx, column=9, value=date_obj.strftime("%Y-%m-%d"))
                    except:
                        ws.cell(row=row_idx, column=9, value=expected_delivery)
                else:
                    ws.cell(row=row_idx, column=9, value=str(expected_delivery))
            else:
                ws.cell(row=row_idx, column=9, value="")
            
            ws.cell(row=row_idx, column=10, value=room.get("letter_status", "") or "无")
        
        # 自动调整列宽
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 20)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # 保存到内存
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        # 生成文件名
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ZWY项目汇总_{current_time}.xlsx"
        encoded_filename = quote(filename, safe='')
        
        # 返回文件流
        return StreamingResponse(
            io.BytesIO(output.getvalue()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename*=UTF-8\'\'{encoded_filename}',
                "Cache-Control": "no-cache",
                "Pragma": "no-cache"
            }
        )
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Export error: {str(e)}")
        print(f"Error details: {error_details}")
        raise HTTPException(status_code=500, detail=f"导出Excel文件失败: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)