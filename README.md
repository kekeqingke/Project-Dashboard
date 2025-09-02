# ZWY项目信息跟踪管理系统

## 项目概述

ZWY项目信息跟踪管理系统是一个多角色Web应用程序，用于管理房间质量问题、整改进展、客户沟通和房间状态。系统支持3单元和4单元两栋楼，每层4户房间的管理，共338个房间的全生命周期管理。

## ✨ 功能特性

### 🎯 已实现核心功能
- 🔐 **用户认证系统** - JWT身份认证，多角色权限管理
- 🏠 **房间管理** - 支持楼栋筛选、分页显示、状态管理
- 🔧 **质量问题管理** - 问题录入、验收流程、类型分类
- 💬 **客户沟通管理** - 沟通记录、收房意愿、落实状态
- 📊 **数据汇总统计** - 多维度筛选、实时统计、分页展示
- 📤 **数据导出功能** - Excel导出、筛选结果导出
- 🚀 **生产环境部署** - Docker容器化、一键部署

### 🎨 界面优化亮点
- **智能筛选** - 6维度筛选（楼栋、状态、问题、沟通等）
- **分页显示** - 避免长列表，支持自定义每页数量
- **实时统计** - 统计卡片响应筛选条件变化
- **默认优化** - 页面加载时默认显示关键数据
- **响应式设计** - 移动端适配，跨设备访问

## 🏗️ 技术架构

### 后端技术栈
- **FastAPI** - 现代高性能Python Web框架
- **SQLAlchemy** - 强大的ORM数据库操作
- **SQLite** - 轻量级嵌入式数据库
- **JWT** - 安全的身份认证机制
- **Uvicorn** - ASGI服务器
- **Python 3.11+**

### 前端技术栈
- **Vue 3** - 渐进式前端框架
- **Element Plus** - 企业级UI组件库
- **Pinia** - 新一代状态管理
- **Vue Router** - 前端路由管理
- **Axios** - HTTP请求库
- **Vite** - 极速构建工具

### 部署和运维
- **Docker & Docker Compose** - 容器化部署
- **Nginx** - 反向代理和静态文件服务
- **SSL/TLS** - HTTPS安全传输
- **Systemd** - 系统服务管理

## 👥 角色权限体系

| 角色 | 权限描述 | 主要功能 |
|------|----------|----------|
| **管理员** | 完整系统管理权限 | 用户管理、房间分配、数据汇总、系统配置 |
| **客户大使** | 客户服务权限 | 客户沟通编辑、质量问题验收、收房意愿记录 |
| **项目工程师** | 工程管理权限 | 质量问题管理、工程进度跟踪、验收审核 |
| **维修工程师** | 维修服务权限 | 质量问题整改、维修记录管理、状态更新 |

## 🚀 快速开始

### 环境要求
- Python 3.11+
- Node.js 16+
- Docker & Docker Compose（可选）

### 方式一：一键启动脚本（推荐）
```bash
# 克隆项目
git clone <repository-url>
cd web_zwy

# 使用Python启动脚本
python start_dev.py
```

### 方式二：手动启动
```bash
# 1. 后端启动
cd backend
pip install -r requirements.txt
python init_db.py          # 初始化数据库
uvicorn main:app --reload  # 启动后端API

# 2. 前端启动（新终端）
cd frontend
npm install
npm run dev                # 启动前端开发服务器
```

### 方式三：Docker容器部署
```bash
# 开发环境
docker-compose up --build

# 生产环境
docker-compose -f docker-compose.prod.yml up -d --build
```

## 🌐 系统访问

### 开发环境
- **前端界面**: http://localhost:5173
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **管理后台**: http://localhost:5173/admin

### 生产环境
- **系统主页**: http://your-server-ip
- **管理后台**: http://your-server-ip/admin
- **API文档**: http://your-server-ip/docs

## 🔑 系统账号

> **⚠️ 注意**: 生产环境已清理测试数据，仅保留管理员账号

| 角色 | 用户名 | 密码 | 状态 |
|------|--------|------|------|
| **管理员** | admin | admin123 | ✅ 生产可用 |

> **首次部署后，请管理员创建正式用户账号**

## 📁 项目结构

```
web_zwy/
├── backend/                    # 🔧 后端FastAPI应用
│   ├── main.py                # 主应用入口和路由
│   ├── models.py              # SQLAlchemy数据模型
│   ├── schemas.py             # Pydantic API模式
│   ├── crud.py                # 数据库CRUD操作
│   ├── auth.py                # JWT认证逻辑
│   ├── database.py            # 数据库连接配置
│   ├── init_db.py             # 数据库初始化脚本
│   ├── clean_test_data.py     # 测试数据清理脚本
│   ├── requirements.txt       # Python依赖包
│   ├── static/               # 前端构建文件目录
│   └── Dockerfile            # Docker镜像构建
├── frontend/                   # 🎨 前端Vue应用
│   ├── src/
│   │   ├── views/            # 页面组件
│   │   │   ├── Home.vue      # 系统首页
│   │   │   ├── Login.vue     # 登录页面
│   │   │   ├── AdminSummary.vue  # 管理员数据汇总
│   │   │   ├── RoomList.vue  # 房间管理列表
│   │   │   └── RoomDetail.vue # 房间详情页面
│   │   ├── stores/           # Pinia状态管理
│   │   ├── api/              # API接口封装
│   │   ├── router/           # Vue路由配置
│   │   └── main.js           # 应用入口文件
│   ├── dist/                 # 构建输出目录
│   ├── package.json          # Node.js依赖配置
│   └── Dockerfile            # Docker镜像构建
├── docker-compose.yml         # 🐳 开发环境容器编排
├── docker-compose.prod.yml    # 🚀 生产环境容器编排
├── Dockerfile.prod           # 生产环境镜像构建
├── start_dev.py              # 🛠️ 开发环境启动脚本
├── deploy.py                 # 📦 生产环境部署脚本
└── README.md                 # 📚 项目文档
```

## 🗄️ 数据模型

### 核心实体关系
```
User (用户) ←→ UserRoom (分配) ←→ Room (房间)
    ↓                              ↓
QualityIssue (质量问题)          Communication (沟通记录)
```

### 房间状态流转
```
整改中 → 闭户 → 已交付 → 已签约
  ↓        ↓       ↓        ↓
待分配   质检完成  客户验收   合同签署
```

### 数据表结构
- **users**: 用户信息（角色、权限、密码）
- **rooms**: 房间信息（楼栋、房号、三类状态）
- **user_rooms**: 用户房间分配关系
- **quality_issues**: 质量问题（描述、类型、状态、图片）
- **communications**: 客户沟通（内容、时间、反馈、落实状态）

## 🔌 API接口文档

### 认证相关
- `POST /token` - 用户登录认证
- `GET /users/me` - 获取当前用户信息

### 用户管理（管理员权限）
- `GET /users/` - 获取用户列表
- `POST /users/` - 创建新用户
- `POST /room-assignments/` - 分配房间给用户

### 房间管理
- `GET /rooms/` - 获取房间列表（支持筛选）
- `GET /rooms/{id}` - 获取房间详情
- `PUT /rooms/{id}` - 更新房间状态

### 质量问题管理
- `GET /quality-issues/` - 获取质量问题列表
- `POST /quality-issues/` - 创建质量问题
- `PUT /quality-issues/{id}/accept` - 验收质量问题
- `POST /quality-issues/{id}/upload-image` - 上传问题图片

### 客户沟通管理
- `GET /communications/` - 获取沟通记录列表
- `POST /communications/` - 创建沟通记录
- `PUT /communications/{id}` - 更新沟通记录

### 数据汇总（管理员）
- `GET /admin/summary` - 获取数据汇总统计
- `GET /admin/export` - 导出Excel报表

## 🔧 开发指南

### 添加新功能流程
1. **设计数据模型**: 在`models.py`中定义SQLAlchemy模型
2. **定义API模式**: 在`schemas.py`中定义Pydantic模式
3. **实现数据操作**: 在`crud.py`中添加CRUD函数
4. **创建API路由**: 在`main.py`中添加FastAPI路由
5. **封装API调用**: 在`frontend/src/api/`中添加axios调用
6. **创建Vue组件**: 实现用户界面和交互逻辑

### 数据库操作
```bash
# 完全重置数据库
rm backend/zwy_project.db
python backend/init_db.py

# 清理测试数据（生产部署前）
python backend/clean_test_data.py
```

### 前端构建
```bash
# 开发构建
cd frontend && npm run dev

# 生产构建
cd frontend && npm run build

# 构建文件复制到后端
cp -r frontend/dist/* backend/static/
```

## 🚀 生产环境部署

### 快速部署（Docker方式）
```bash
# 1. 构建前端
cd frontend && npm run build

# 2. 复制静态文件
cp -r dist/* ../backend/static/

# 3. 启动生产环境
docker-compose -f docker-compose.prod.yml up -d --build

# 4. 检查服务状态
docker-compose -f docker-compose.prod.yml ps
```

### 服务器部署步骤
1. **环境准备**: 安装Docker、Docker Compose
2. **文件上传**: 上传项目文件到服务器
3. **域名配置**: 配置域名解析和SSL证书
4. **服务启动**: 运行生产环境容器
5. **监控维护**: 设置日志监控和定期备份

详细部署文档请参考项目中的部署脚本和配置文件。

## 📊 系统特色功能

### 智能筛选系统
- **6维度筛选**: 楼栋、整改状态、交付状态、签约状态、问题、沟通
- **组合筛选**: 支持多条件组合查询
- **实时统计**: 筛选结果实时反映在统计卡片
- **筛选记忆**: 保持用户筛选偏好

### 分页展示优化
- **智能分页**: 避免338个房间的长列表滚动
- **自定义页数**: 支持20/50/100/200条每页
- **快速跳转**: 支持页码直接跳转
- **数量提示**: 显示当前筛选结果数量

### 数据导出功能
- **筛选导出**: 导出当前筛选条件的数据
- **Excel格式**: 标准Excel文件格式
- **字段完整**: 包含所有关键业务字段
- **文件命名**: 自动生成时间戳文件名

## 📈 版本发布记录

### v1.0.0 (当前版本) - 生产就绪版
- ✅ 完整的房间管理功能
- ✅ 多角色用户权限系统
- ✅ 质量问题全流程管理
- ✅ 客户沟通记录系统
- ✅ 数据汇总和导出功能
- ✅ 智能筛选和分页优化
- ✅ 生产环境部署支持
- ✅ 测试数据清理功能

### 开发路线图

#### v1.1.0 - 功能增强版
- [ ] 图片上传和压缩功能
- [ ] 实时通知和消息推送
- [ ] 操作日志和审计跟踪
- [ ] 高级Excel报表导出
- [ ] 移动端响应式优化

#### v1.2.0 - 企业级版本
- [ ] 数据可视化图表
- [ ] 工作流审批机制
- [ ] 微信集成和通知
- [ ] 多租户支持
- [ ] 性能优化和缓存

## 🤝 贡献指南

### 参与开发
1. Fork 本仓库
2. 创建特性分支 `git checkout -b feature/AmazingFeature`
3. 提交更改 `git commit -m 'Add some AmazingFeature'`
4. 推送分支 `git push origin feature/AmazingFeature`
5. 创建 Pull Request

### 代码规范
- **Python**: 遵循PEP 8规范，使用类型提示
- **JavaScript**: 使用ESLint，遵循Vue 3最佳实践
- **Git**: 使用语义化提交信息
- **文档**: 及时更新README和API文档

## 📝 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 📞 技术支持

### 问题反馈
- **GitHub Issues**: 提交bug和功能需求
- **技术文档**: 查看在线API文档
- **开发交流**: 参与项目讨论

### 联系方式
- 📧 邮箱: [your-email@example.com]
- 🔗 项目地址: [repository-url]
- 📚 文档地址: [docs-url]

---

<div align="center">

**🏠 ZWY项目管理系统 v1.0.0**

*让房间管理更简单，让质量跟踪更高效*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Vue 3](https://img.shields.io/badge/vue-3.x-green.svg)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-red.svg)](https://fastapi.tiangolo.com/)

</div>