# 基础设施任务

**目的**: 项目初始化 + 阻塞所有 PD 模块的先决条件
**完成标志**: 项目可启动、数据库可连接、认证可用、RBAC 框架就绪、统一响应/错误码/日志可用
**设计依据**: plan.md §阶段1 + ad/ad-global.md + dd/dd-global.md + dd/dd-user-mgmt.md

## 阶段 1: 设置（项目初始化）

- [ ] T001 [B-CONFIG] 按照 plan.md 项目结构创建目录骨架 `smartchef-platform/{backend,frontend,device-inference}`
  - 文件: `smartchef-platform/` 顶层目录结构
- [ ] T002 [B-CONFIG] 初始化后端项目: pyproject.toml + FastAPI 应用入口 `app/main.py` + 配置模块 `app/core/config.py`
  - 文件: `backend/pyproject.toml`, `backend/app/main.py`, `backend/app/core/config.py`
  - 依据: ad/ad-global.md §2 技术选型
- [ ] T003 [P] [F-PAGE] 初始化前端项目: package.json + Vite 配置 + React 18 + Ant Design 5 + 路由框架
  - 文件: `frontend/package.json`, `frontend/vite.config.js`, `frontend/src/main.jsx`
  - 依据: plan.md 技术背景 (React 18 + Vite + Ant Design 5, JavaScript)
- [ ] T004 [P] [B-CONFIG] 配置代码检查和格式化工具 (ruff/black 后端, eslint/prettier 前端)
  - 文件: `backend/pyproject.toml [tool.ruff]`, `frontend/.eslintrc.js`

## 阶段 2: 基础（阻塞先决条件）

### 测试（TDD: 先写测试）

- [ ] T005 [P] [T-CONTRACT] 认证 API 契约测试: POST /auth/login, POST /auth/logout, GET /auth/me, POST /auth/refresh
  - 文件: `backend/tests/contract/test_auth_api.py`
  - 依据: ad/ad-user-mgmt.md §3 认证 API
- [ ] T006 [P] [T-UNIT] JWT 生成/验证/刷新 单元测试
  - 文件: `backend/tests/unit/test_security.py`
  - 依据: dd/dd-user-mgmt.md §3 JWT 算法
- [ ] T007 [P] [T-UNIT] RBAC `require_capability` 中间件单元测试 (21 能力点)
  - 文件: `backend/tests/unit/test_rbac.py`
  - 依据: dd/dd-global.md §3 RBAC 能力点
- [ ] T008 [P] [T-UNIT] 统一响应包络 + 错误码格式 单元测试
  - 文件: `backend/tests/unit/test_api_response.py`
  - 依据: ad/ad-global.md §4 + dd/dd-global.md §2 错误码体系

### 后端基础

- [ ] T009 [B-CONFIG] 创建数据库连接模块 (async SQLAlchemy + 连接池)
  - 文件: `backend/app/core/database.py`
  - 依据: dd/dd-global.md §1 PostgreSQL 配置
- [ ] T010 [P] [B-CONFIG] 创建 Redis 连接模块
  - 文件: `backend/app/core/redis.py`
  - 依据: dd/dd-global.md §1.5 Redis 配置
- [ ] T011 [B-MODEL] 创建 ORM 基类 (id/created_at/updated_at/version) + SQLAlchemy Base
  - 文件: `backend/app/models/base.py`
  - 依据: dd/dd-global.md §1 公共字段约定
- [ ] T012 [B-MODEL] 创建 User/Role/Permission/RolePermission ORM 模型
  - 文件: `backend/app/models/user.py`, `backend/app/models/role.py`
  - 依据: dd/dd-global.md §1.1~§1.3 实体定义
- [ ] T013 [B-CONFIG] 初始化 Alembic + 创建首次迁移 (users/roles/permissions 表)
  - 文件: `backend/migrations/env.py`, `backend/migrations/versions/001_initial.py`
- [ ] T014 [B-CONFIG] 种子数据脚本: 内置管理员账号 + 3 个默认角色 + 21 个能力点
  - 文件: `backend/app/scripts/init_db.py`
  - 依据: dd/dd-global.md §5 种子数据
- [ ] T015 [B-SERVICE] 创建安全模块: JWT 生成/验证/刷新 + 密码哈希 (bcrypt)
  - 文件: `backend/app/core/security.py`
  - 依据: dd/dd-user-mgmt.md §3 JWT 算法 + 密码哈希
- [ ] T016 [B-SERVICE] 创建认证服务: 登录/登出/Token 刷新/当前用户
  - 文件: `backend/app/services/auth_service.py`
  - 依据: dd/dd-user-mgmt.md §4 登录/登出算法
- [ ] T017 [B-SERVICE] 创建 RBAC 中间件: `require_capability` 装饰器
  - 文件: `backend/app/core/security.py` (扩展)
  - 依据: dd/dd-global.md §3 权限校验伪代码
- [ ] T018 [B-API] 创建认证 API 路由: login/logout/me/refresh
  - 文件: `backend/app/api/v1/auth.py`
  - 依据: ad/ad-user-mgmt.md §3.1 认证端点
- [ ] T019 [B-CONFIG] 统一响应包络 (`code/data/msg`) + 错误码框架 (E{module}{sub}{seq})
  - 文件: `backend/app/core/api_response.py`
  - 依据: ad/ad-global.md §4 响应格式 + dd/dd-global.md §2 错误码体系
- [ ] T020 [B-CONFIG] 输入校验中间件 + 请求大小限制
  - 文件: `backend/app/core/input_validator.py`
  - 依据: ad/ad-global.md §6.1 输入校验
- [ ] T021 [B-CONFIG] 日志中间件: 异步写入 RequestLog + 结构化格式
  - 文件: `backend/app/core/logging_middleware.py`
  - 依据: dd/dd-monitoring.md §4.1 异步日志写入算法
- [ ] T022 [B-CONFIG] 频率限制中间件 (登录防爆破: IP + 用户名锁定)
  - 文件: `backend/app/core/rate_limiter.py`
  - 依据: dd/dd-user-mgmt.md §4.3 登录频率限制

### 前端基础

- [ ] T023 [P] [F-PAGE] 创建全局布局组件: Layout + Sider 侧边栏菜单
  - 文件: `frontend/src/components/Layout/MainLayout.jsx`
  - 依据: pd-all/ 各模块共享的侧边栏导航结构
- [ ] T024 [P] [F-API] 创建 API 调用基础层: axios 实例 + JWT 拦截器 + 错误统一处理
  - 文件: `frontend/src/services/api.js`
  - 依据: ad/ad-global.md §4 响应格式
- [ ] T025 [P] [F-STORE] 创建认证状态管理 (zustand): 登录/登出/Token 刷新
  - 文件: `frontend/src/stores/authStore.js`
- [ ] T026 [F-PAGE] 创建登录页面
  - 文件: `frontend/src/pages/Login/index.jsx`
  - 依据: pd-all/pd-user-mgmt/ 登录交互

## 检查点

**基础就绪标准**:
- [ ] 后端可启动 (`uvicorn app.main:app`)
- [ ] 数据库迁移成功，种子数据导入
- [ ] Redis 连接正常
- [ ] 登录 → 获取 JWT → 访问受保护接口 → 权限校验 全链路可用
- [ ] 统一响应包络生效，错误码正确返回
- [ ] 日志中间件异步写入正常
- [ ] 前端可启动，登录页可用，JWT 自动附加
- [ ] 所有测试通过（T005~T008 绿灯）
