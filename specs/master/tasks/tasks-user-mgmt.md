# 用户管理 (User Management) 任务

**PD 交互原型**: pd-all/pd-user-mgmt/ (1 page: index)
**架构设计**: ad/ad-user-mgmt.md
**详细设计**: dd/dd-user-mgmt.md
**优先级**: P3
**依赖**: tasks-infra.md 必须先完成 (认证 API + User/Role 模型已在 infra 中创建)

> 注意: 基础认证（登录/登出/JWT）和 User/Role/Permission 模型已在 tasks-infra.md 中完成。
> 本模块聚焦于**用户管理后台页面**和**角色权限配置** CRUD。

## 测试任务（TDD: 先写测试, 确保红灯）

### 契约测试（覆盖 AD API — 扣除 infra 已覆盖的认证 API 后剩余 16 端点）

- [ ] T001 [P] [T-CONTRACT] 用户 CRUD 契约测试: GET/POST /users, GET/PUT/DELETE /users/{id}, PUT /users/{id}/roles, PUT /users/{id}/password
  - 文件: `backend/tests/contract/test_user_management_api.py`
  - 依据: ad/ad-user-mgmt.md §3.2
- [ ] T002 [P] [T-CONTRACT] 角色 CRUD 契约测试: GET/POST /roles, GET/PUT/DELETE /roles/{id}, GET/PUT /roles/{id}/permissions
  - 文件: `backend/tests/contract/test_roles_api.py`
  - 依据: ad/ad-user-mgmt.md §3.3
- [ ] T003 [P] [T-CONTRACT] 能力点列表 契约测试: GET /permissions
  - 文件: `backend/tests/contract/test_permissions_api.py`
  - 依据: ad/ad-user-mgmt.md §3.4

### 集成测试（覆盖 AD 数据流）

- [ ] T004 [P] [T-INTEGRATION] 用户创建→分配角色→权限校验 端到端集成测试
  - 文件: `backend/tests/integration/test_user_rbac_flow.py`
  - 依据: ad/ad-user-mgmt.md §2.1 用户管理数据流

### E2E 测试（覆盖 PD 交互路径）

- [ ] T005 [P] [T-E2E] 用户管理页 E2E: 用户列表/新建/编辑/禁用/角色分配/角色管理 交互路径
  - 文件: `frontend/tests/e2e/user-management.spec.js`
  - 依据: pd-all/pd-user-mgmt/index.html

## 后端任务

### 服务层（模型已在 infra 创建, 此处补充管理服务）

- [ ] T006 [B-SERVICE] 用户管理服务 (CRUD + 密码重置 + 状态切换 active⇄disabled + 内置管理员保护)
  - 文件: `backend/app/services/user_service.py`
  - 依据: dd/dd-user-mgmt.md §4.1
- [ ] T007 [B-SERVICE] 角色管理服务 (CRUD + 权限分配 + 内置角色保护)
  - 文件: `backend/app/services/role_service.py`
  - 依据: dd/dd-user-mgmt.md §4.2

### API 端点（来自 AD 接口契约）

- [ ] T008 [B-API] 用户 CRUD API: GET/POST /users, GET/PUT/DELETE /users/{id}, PUT /users/{id}/roles, PUT /users/{id}/password
  - 文件: `backend/app/api/v1/users.py`
  - 依据: ad/ad-user-mgmt.md §3.2
- [ ] T009 [B-API] 角色 CRUD + 权限分配 API: GET/POST /roles, GET/PUT/DELETE /roles/{id}, GET/PUT /roles/{id}/permissions
  - 文件: `backend/app/api/v1/roles.py`
  - 依据: ad/ad-user-mgmt.md §3.3
- [ ] T010 [B-API] 能力点列表 API: GET /permissions
  - 文件: `backend/app/api/v1/permissions.py`
  - 依据: ad/ad-user-mgmt.md §3.4

## 前端任务

### 页面（来自 PD 交互原型）

- [ ] T011 [F-PAGE] 用户管理页: 用户列表Table+新建弹窗+编辑弹窗+角色分配+密码重置+禁用/启用
  - 文件: `frontend/src/pages/UserManager/index.jsx`
  - 依据: pd-all/pd-user-mgmt/index.html
  - **PD UI Checklist**:
    - [ ] 统计卡片 ×4: 总账号数 (TeamOutlined) / 管理员 (SafetyCertificateOutlined, red) / 产品经理 (UserOutlined, blue) / 测试人员 (ExperimentOutlined, green) — Row 4-Col 布局
    - [ ] Tabs 两个标签: "账号管理" (默认) / "角色与权限"
    - [ ] 用户列表 Table: 列 = 用户名 (monospace) / 姓名 / 角色 (Tag 按 ROLE_MAP 着色) / 状态 (Tag green/default) / 创建时间 / 最后登录 / 操作; pagination=false, size=middle
    - [ ] 操作列: 编辑角色 Button (link, EditOutlined) + 重置密码 Button (link, KeyOutlined) + 启用/禁用 Switch (内置 admin 不可禁用)
    - [ ] 新建账号 Modal (width=480): Form 字段 = username (Input, 正则 3-20位) / name (Input) / password (Password, ≥8位) / role (Select: admin/pm/tester, 默认 pm)
    - [ ] 编辑角色 Modal (width=600): Descriptions 展示用户信息 + newRole Select + Divider "权限预览" + 权限预览 Table (能力点×PermIcon)
    - [ ] 重置密码 Modal.confirm: danger 确认按钮, 文案含用户名+默认密码 Abc12345
    - [ ] 角色卡片组 ×3: 系统管理员/产品经理/测试人员, 各含能力概要 List — Row 3-Col
    - [ ] 能力点权限矩阵 Table: 列 = 能力点 key (monospace) / 说明 / 系统管理员 / 产品经理 / 测试人员; PermIcon (✅/❌/⚠+Tooltip); bordered, 14 行
    - [ ] 页面头部: "新建账号" Button (primary, PlusOutlined)

### 组件（可复用）

- [ ] T012 [P] [F-COMPONENT] 角色编辑器组件 (角色CRUD+权限矩阵Checkbox)
  - 文件: `frontend/src/pages/UserManager/RoleEditor.jsx`
- [ ] T013 [P] [F-COMPONENT] 权限矩阵组件 (21 能力点按模块分组的 Checkbox Grid)
  - 文件: `frontend/src/pages/UserManager/PermissionMatrix.jsx`

### 状态管理与 API 对接

- [ ] T014 [F-STORE] 用户管理状态管理 (zustand): 用户列表/角色列表/能力点
  - 文件: `frontend/src/stores/userStore.js`
- [ ] T015 [F-API] 用户管理 API 对接层: 全部 16 端点的前端调用封装
  - 文件: `frontend/src/services/userApi.js`

## 检查点

**模块验收标准**（对照 PD 交互稿）:
- [ ] 所有测试通过（T001~T005 红灯→绿灯）
- [ ] 用户管理: CRUD + 角色分配 + 密码重置 + 禁用/启用 全链路可用
- [ ] 角色管理: CRUD + 21 能力点权限矩阵配置 可用
- [ ] 内置保护: 内置管理员不可删除, 内置角色不可删除
- [ ] User 状态流转 active⇄disabled 正确
- [ ] 能力点列表: 按模块分组展示 21 个能力点
- [ ] 无回归（infra + 先前模块测试仍通过）
