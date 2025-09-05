from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import models, schemas, crud
from database import SessionLocal, engine, get_db
import auth
from typing import List
import os
import uuid
import shutil
import io
from pdf_generator import create_room_communication_pdf

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
    return {"access_token": access_token, "token_type": "bearer", "user": user}

@app.get("/users/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

# 用户管理接口
@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db), 
                current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")
    return crud.create_user(db=db, user=user)

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

@app.get("/rooms/{room_id}/export-pdf")
def export_room_pdf(room_id: int, db: Session = Depends(get_db),
                    current_user: models.User = Depends(auth.get_current_user)):
    # 检查房间访问权限
    room = crud.get_room_by_id(db=db, room_id=room_id, user_id=current_user.id if current_user.role != "admin" else None)
    if not room:
        raise HTTPException(status_code=404, detail="房间不存在或无权限访问")
    
    try:
        # 获取房间相关数据
        room_dict = {
            'building_unit': room.building_unit,
            'room_number': room.room_number,
            'expected_delivery_date': room.expected_delivery_date
        }
        
        # 获取客户信息
        customer_info = None
        try:
            customer = crud.get_customer_by_room_id(db, room_id)
            if customer:
                customer_info = {
                    'name': customer.name,
                    'gender': customer.gender,
                    'id_card': customer.id_card,
                    'phone': customer.phone,
                    'customer_level': customer.customer_level,
                    'work_unit': customer.work_unit
                }
        except:
            pass
        
        # 获取沟通记录
        communications = crud.get_communications_by_room_id(db, room_id)
        comm_list = []
        latest_customer_description = ""
        
        for comm in communications:
            comm_dict = {
                'content': comm.content,
                'communication_time': comm.communication_time,
                'feedback': comm.feedback,
                'customer_description': comm.customer_description,
                'created_at': comm.created_at
            }
            comm_list.append(comm_dict)
            
            # 获取最新的客户描摹
            if comm.customer_description and not latest_customer_description:
                latest_customer_description = comm.customer_description
        
        # 获取质量问题
        quality_issues = crud.get_quality_issues_by_room_id(db, room_id)
        issue_list = []
        for issue in quality_issues:
            issue_dict = {
                'description': issue.description,
                'status': issue.status,
                'created_at': issue.created_at,
                'user_name': issue.user.name if issue.user else ''
            }
            issue_list.append(issue_dict)
        
        # 获取分配的用户信息
        assigned_users = {'maintenance_engineer': '', 'customer_ambassador': ''}
        assignments = db.query(models.UserRoom).filter(models.UserRoom.room_id == room_id).all()
        for assignment in assignments:
            user = assignment.user
            if user.role == 'maintenance_engineer':
                assigned_users['maintenance_engineer'] = user.name
            elif user.role == 'customer_ambassador':
                assigned_users['customer_ambassador'] = user.name
        
        # 生成PDF
        pdf_bytes = create_room_communication_pdf(
            room_info=room_dict,
            customer_info=customer_info,
            communications=comm_list,
            quality_issues=issue_list,
            assigned_users=assigned_users,
            latest_customer_description=latest_customer_description
        )
        
        # 返回PDF文件
        filename = f"瑧湾悦二期-{room.building_unit}-{room.room_number}-沟通记录.pdf"
        
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF生成失败: {str(e)}")

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
    return crud.create_quality_issue(db=db, issue=issue, user_id=current_user.id)

@app.put("/quality-issues/{issue_id}/accept")
def accept_quality_issue(issue_id: int, db: Session = Depends(get_db),
                        current_user: models.User = Depends(auth.get_current_user)):
    return crud.accept_quality_issue(db=db, issue_id=issue_id, user_id=current_user.id)

@app.put("/quality-issues/{issue_id}", response_model=schemas.QualityIssue)
def update_quality_issue(issue_id: int, issue_update: dict, db: Session = Depends(get_db),
                        current_user: models.User = Depends(auth.get_current_user)):
    # 处理验收操作
    if issue_update.get("is_verified"):
        result = crud.accept_quality_issue(db=db, issue_id=issue_id, user_id=current_user.id)
        if not result:
            raise HTTPException(status_code=404, detail="质量问题未找到")
        return result
    
    # 处理其他字段的更新
    # 从dict转换为QualityIssueUpdate对象
    try:
        update_data = schemas.QualityIssueUpdate(**issue_update)
        result = crud.update_quality_issue(
            db=db, 
            issue_id=issue_id, 
            issue_update=update_data,
            user_id=current_user.id if current_user.role != "admin" else None
        )
        if not result:
            raise HTTPException(status_code=404, detail="质量问题未找到或无权限访问")
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"更新失败: {str(e)}")

# 客户沟通管理接口
@app.get("/communications/", response_model=List[schemas.Communication])
def read_communications(room_id: int = None, db: Session = Depends(get_db),
                       current_user: models.User = Depends(auth.get_current_user)):
    return crud.get_communications(db, room_id, current_user.id if current_user.role != "admin" else None)

@app.post("/communications/", response_model=schemas.Communication)
def create_communication(comm: schemas.CommunicationCreate, db: Session = Depends(get_db),
                        current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role not in ["customer_ambassador", "admin"]:
        raise HTTPException(status_code=403, detail="只有客户大使和管理员可以添加沟通记录")
    return crud.create_communication(db=db, communication=comm, user_id=current_user.id)

@app.put("/communications/{communication_id}", response_model=schemas.Communication)
def update_communication(communication_id: int, update_data: schemas.CommunicationUpdate, db: Session = Depends(get_db),
                         current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role not in ["customer_ambassador", "admin"]:
        raise HTTPException(status_code=403, detail="只有客户大使和管理员可以更新沟通记录")
    
    communication = crud.update_communication(db=db, communication_id=communication_id, is_implemented=update_data.is_implemented, user_id=current_user.id if current_user.role != "admin" else None)
    if not communication:
        raise HTTPException(status_code=404, detail="沟通记录未找到")
    
    return communication

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
    if letter_status not in ["无", "ZX", "SX"]:
        raise HTTPException(status_code=400, detail="无效的信件状态")
    
    room.letter_status = letter_status
    db.commit()
    db.refresh(room)
    
    return {"message": "信件状态更新成功", "letter_status": letter_status}

@app.put("/rooms/{room_id}/pre-leakage")
async def update_room_pre_leakage(
    room_id: int,
    pre_leakage: str = Query(...),
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
    if pre_leakage not in ["无", "有"]:
        raise HTTPException(status_code=400, detail="无效的前期渗漏状态")
    
    room.pre_leakage = pre_leakage
    db.commit()
    db.refresh(room)
    
    return {"message": "前期渗漏状态更新成功", "pre_leakage": pre_leakage}

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

# 客户信息相关接口
@app.get("/customers/room/{room_id}", response_model=schemas.Customer)
def get_customer_by_room(room_id: int, db: Session = Depends(get_db),
                        current_user: models.User = Depends(auth.get_current_user)):
    """根据房间ID获取客户信息"""
    # 只有管理员和客户大使可以查看客户信息
    if current_user.role not in ["admin", "customer_ambassador"]:
        raise HTTPException(status_code=403, detail="权限不足")
    
    customer = crud.get_customer_by_room_id(db, room_id)
    if not customer:
        raise HTTPException(status_code=404, detail="该房间暂无客户信息")
    
    return customer

@app.post("/customers/", response_model=schemas.Customer)
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db),
                   current_user: models.User = Depends(auth.get_current_user)):
    """创建客户信息"""
    # 只有管理员和客户大使可以创建客户信息
    if current_user.role not in ["admin", "customer_ambassador"]:
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 检查房间是否存在
    room = db.query(models.Room).filter(models.Room.id == customer.room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="房间不存在")
    
    # 检查该房间是否已有客户信息
    existing_customer = crud.get_customer_by_room_id(db, customer.room_id)
    if existing_customer:
        raise HTTPException(status_code=400, detail="该房间已有客户信息，请使用更新功能")
    
    # 检查身份证号是否已存在
    if crud.check_id_card_exists(db, customer.id_card):
        raise HTTPException(status_code=400, detail="该身份证号已存在")
    
    return crud.create_customer(db=db, customer=customer)

@app.put("/customers/{customer_id}", response_model=schemas.Customer)
def update_customer(customer_id: int, customer: schemas.CustomerUpdate, 
                   db: Session = Depends(get_db),
                   current_user: models.User = Depends(auth.get_current_user)):
    """更新客户信息"""
    # 只有管理员和客户大使可以更新客户信息
    if current_user.role not in ["admin", "customer_ambassador"]:
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 检查客户是否存在
    existing_customer = crud.get_customer(db, customer_id)
    if not existing_customer:
        raise HTTPException(status_code=404, detail="客户信息不存在")
    
    # 检查身份证号是否已被其他客户使用
    if customer.id_card and crud.check_id_card_exists(db, customer.id_card, customer_id):
        raise HTTPException(status_code=400, detail="该身份证号已被其他客户使用")
    
    updated_customer = crud.update_customer(db=db, customer_id=customer_id, customer=customer)
    if not updated_customer:
        raise HTTPException(status_code=404, detail="更新失败")
    
    return updated_customer

@app.delete("/customers/{customer_id}")
def delete_customer(customer_id: int, db: Session = Depends(get_db),
                   current_user: models.User = Depends(auth.get_current_user)):
    """删除客户信息"""
    # 只有管理员和客户大使可以删除客户信息
    if current_user.role not in ["admin", "customer_ambassador"]:
        raise HTTPException(status_code=403, detail="权限不足")
    
    success = crud.delete_customer(db=db, customer_id=customer_id)
    if not success:
        raise HTTPException(status_code=404, detail="客户信息不存在")
    
    return {"message": "客户信息删除成功"}

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

@app.delete("/admin/rooms/clear-all-content")
def clear_all_rooms_content(db: Session = Depends(get_db),
                           current_user: models.User = Depends(auth.get_current_user)):
    """清空所有房间的内容数据，保留用户分配和房号"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="只有管理员可以执行此操作")
    
    result = crud.clear_all_rooms_content(db=db)
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)