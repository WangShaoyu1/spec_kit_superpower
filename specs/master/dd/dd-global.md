---
version: 2.0
updated: 2026-03-18
scope: 全局 (公共实体/错误码体系/权限模型/系统配置/种子数据/迁移规范)
based_on:
  - spec.md@v1.4
  - ad/ad-global.md@v2.0
  - ad/ad-user-mgmt.md@v2.0
  - dd-template.md@v2.3
changelog: |
  2.0: 基于全量 AD(6模块) 重构为 dd/ 文件夹结构; 公共实体+错误码+权限+配置+种子数据
---

# 详细设计 (DD): 全局公共定义

## 1. 文档说明

本文档包含跨模块共享的基础设施定义，是所有 `dd-<module>.md` 的前置依赖。

**内容范围**:
- 公共实体 (User, Role, Permission, PublishedVersion, DeviceSession)
- 全局错误码格式与分类
- RBAC 权限模型
- 系统级配置项
- 预置种子数据
- 数据迁移规范

---

## 2. 设计原则

遵循 dd-template.md §2 定义的原则:
- **一对一可编码**: 每个定义可直接映射为 ORM Model / 枚举 / 中间件配置
- **约束显式化**: 字符串有 max_length, 数值有 range, 枚举列出所有值
- **向后兼容**: 字段新增不移除, 枚举新增不删除

---

## 3. 公共数据模型

### 3.1 实体: User (用户)

**对应 FR**: FR-001
**对应 AD**: ad-user-mgmt.md §2
**表名**: `users`

| 字段 | 类型 | 约束 | 默认值 | 索引 | 说明 |
|------|------|------|--------|------|------|
| id | UUID | PK | gen_random_uuid() | 主键 | 唯一标识 |
| username | VARCHAR(20) | NOT NULL, UNIQUE | - | 唯一索引 | 登录名, 3~20 位字母数字下划线 |
| name | VARCHAR(50) | NOT NULL | - | - | 显示名称 |
| password_hash | VARCHAR(128) | NOT NULL | - | - | bcrypt 哈希, 原文不落库 |
| role_id | UUID | NOT NULL, FK(roles.id) | - | 普通索引 | 所属角色 |
| status | VARCHAR(16) | NOT NULL | 'active' | 普通索引 | 枚举: active / disabled |
| is_builtin | BOOLEAN | NOT NULL | false | - | 是否内置账号 (admin) |
| last_login_at | TIMESTAMP(TZ) | NULL | NULL | - | 最后登录时间 |
| created_at | TIMESTAMP(TZ) | NOT NULL | now() | - | 创建时间 |
| updated_at | TIMESTAMP(TZ) | NOT NULL | now() | - | 更新时间 |

**字段校验规则**:

| 字段 | 正则/规则 | 说明 |
|------|----------|------|
| username | `^[a-zA-Z][a-zA-Z0-9_]{2,19}$` | 字母开头, 3~20 位 |
| password (明文) | `^(?=.*[a-zA-Z])(?=.*\d).{8,}$` | 至少 8 位, 含字母+数字 |

#### 索引

| 索引名 | 字段 | 类型 | 用途 |
|--------|------|------|------|
| uq_users_username | (username) | B-Tree, UNIQUE | 登录名唯一 |
| idx_users_role_id | (role_id) | B-Tree | 按角色筛选 |
| idx_users_status | (status) | B-Tree | 按状态筛选 |

### 3.2 实体: Role (角色)

**对应 FR**: FR-001
**表名**: `roles`

| 字段 | 类型 | 约束 | 默认值 | 索引 | 说明 |
|------|------|------|--------|------|------|
| id | UUID | PK | gen_random_uuid() | 主键 | 唯一标识 |
| name | VARCHAR(30) | NOT NULL, UNIQUE | - | 唯一索引 | 角色名称 |
| description | VARCHAR(200) | NULL | - | - | 角色描述 |
| is_builtin | BOOLEAN | NOT NULL | false | - | 内置角色 (admin/pm/tester) 不可删除 |
| created_at | TIMESTAMP(TZ) | NOT NULL | now() | - | 创建时间 |
| updated_at | TIMESTAMP(TZ) | NOT NULL | now() | - | 更新时间 |

### 3.3 实体: Permission (能力点)

**对应 FR**: FR-001, FR-053
**表名**: `permissions`

| 字段 | 类型 | 约束 | 默认值 | 索引 | 说明 |
|------|------|------|--------|------|------|
| id | UUID | PK | gen_random_uuid() | 主键 | 唯一标识 |
| key | VARCHAR(64) | NOT NULL, UNIQUE | - | 唯一索引 | 能力点标识, 如 `intent_library_read` |
| label | VARCHAR(50) | NOT NULL | - | - | 中文显示名 |
| module | VARCHAR(30) | NOT NULL | - | 普通索引 | 所属模块 (指令库/对话方案/知识库/监控/批量测试/系统) |

### 3.4 关联表: RolePermission

**表名**: `role_permissions`

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| role_id | UUID | FK(roles.id), NOT NULL | 角色 ID |
| permission_id | UUID | FK(permissions.id), NOT NULL | 能力点 ID |

**约束**: PRIMARY KEY (role_id, permission_id)
**级联**: 删除 Role → CASCADE DELETE 关联记录; 删除 Permission → RESTRICT

### 3.5 实体: PublishedVersion (发布版本)

**对应 FR**: FR-015~016
**对应 AD**: ad-global.md §3.2 + ad-dialog-profile.md §3.4
**表名**: `published_versions`

| 字段 | 类型 | 约束 | 默认值 | 索引 | 说明 |
|------|------|------|--------|------|------|
| id | UUID | PK | gen_random_uuid() | 主键 | 唯一标识 |
| version_number | VARCHAR(20) | NOT NULL | - | - | 版本号, 格式 `vX.Y` 自增 |
| profile_id | UUID | NOT NULL, FK(dialog_profiles.id) | - | 普通索引 | 来源方案 |
| config_snapshot | JSONB | NOT NULL | - | - | 完整配置快照 (见下方 schema) |
| status | VARCHAR(16) | NOT NULL | 'active' | 普通索引 | 枚举: active / archived |
| published_by | UUID | NOT NULL, FK(users.id) | - | - | 发布人 |
| published_at | TIMESTAMP(TZ) | NOT NULL | now() | - | 发布时间 |
| archived_at | TIMESTAMP(TZ) | NULL | NULL | - | 归档时间 |

**config_snapshot JSONB Schema**:

```json
{
  "profile_name": "string",
  "threshold": "float, 0.0~1.0",
  "llm_provider": "string",
  "llm_model": "string",
  "persona": { "name": "string", "personality": "string" },
  "bound_libraries": [
    {
      "library_id": "uuid",
      "library_key": "string",
      "language": "zh|en",
      "published_model_id": "uuid",
      "model_version": "string"
    }
  ],
  "knowledge_enabled": "boolean",
  "session_timeout_min": "int"
}
```

**唯一性约束**: 同一时间仅一个 `status='active'` 的版本 (UNIQUE partial index on status='active')

#### 索引

| 索引名 | 字段 | 类型 | 用途 |
|--------|------|------|------|
| idx_pv_profile_id | (profile_id) | B-Tree | 按方案查版本列表 |
| uq_pv_active | (status) WHERE status='active' | B-Tree, UNIQUE partial | 仅一个活跃版本 |
| idx_pv_published_at | (published_at DESC) | B-Tree | 时间排序 |

### 3.6 实体: DeviceSession (设备会话)

**对应 FR**: FR-023
**对应 AD**: ad-global.md §3.1
**存储**: Redis Hash (非 PostgreSQL)

| 字段 | 类型 | 说明 |
|------|------|------|
| session_id | string | 唯一标识, 格式 `sess_{device_id}_{uuid}` |
| device_id | string | 设备 ID |
| version_id | string | 当前生效版本 ID |
| dialog_history | list[object] | 最近 N 轮对话 (默认 10), 按 FIFO 策略 |
| active_entity_stack | list[string] | 活跃实体栈 (指代消解用) |
| current_domain | string | 当前域: command / knowledge / chitchat |
| slot_buffer | object | 未完成的槽位收集缓冲 |
| clarification_count | int | 当前意图连续澄清次数 (FR-020, max=3) |
| device_context | object | 最新设备上下文快照 |
| created_at | string (ISO 8601) | 会话创建时间 |
| last_active_at | string (ISO 8601) | 最后活跃时间 |

**Redis Key**: `session:{device_id}` (一个设备同一时刻只有一个活跃会话)
**TTL**: 配置项 `SESSION_TIMEOUT_MIN` × 60 秒 (默认 600s / 10 分钟)
**版本重置**: 发布新版本时, 执行 `DEL session:*` 清除所有会话 (FR-016)

### 3.7 ER 关系总图

```
用户认证域:
  User (*) ──(N:1)── Role (1)
  Role (1) ──(1:N)── RolePermission (*) ──(N:1)── Permission (1)

指令库域:
  IntentLibrary (1) ──(1:N)── Intent (*)
  Intent (1) ──(1:N)── Slot (*)
  IntentLibrary (1) ──(1:N)── LibraryModelVersion (*)
  IntentLibrary (1) ──(1:N)── TrainingDataset (*)
  IntentLibrary (1) ──(1:N)── EvaluationDataset (*)
  LibraryModelVersion (1) ──(1:1)── TrainingDataset (1)   [训练集 1:1 绑定]
  LibraryModelVersion (1) ──(1:N)── EvaluationRun (*)
  LibraryModelVersion (1) ──(1:N)── IntentTestSession (*)
  IntentTestSession (1) ──(1:N)── IntentTestMessage (*)

对话方案域:
  DialogProfile (1) ──(1:N)── Persona (*)
  DialogProfile (1) ──(1:N)── ProfileLibraryBinding (*)
  ProfileLibraryBinding (*) ──(N:1)── IntentLibrary (1)
  DialogProfile (1) ──(1:N)── PublishedVersion (*)
  DialogProfile (1) ──(1:N)── ProfileTestSession (*)
  ProfileTestSession (1) ──(1:N)── ProfileTestMessage (*)

知识库域:
  KnowledgeCategory (1) ──(1:N)── KnowledgeDocument (*)
  KnowledgeDocument (1) ──(1:N)── DocumentChunk (*)

批量测试域:
  BatchTest (1) ──(1:N)── TestCase (*)
  BatchTest (1) ──(1:N)── TestRun (*)
  TestRun (1) ──(1:1)── TestRunAnalysis (0..1)

监控域:
  RequestLog (独立, 无外键依赖)
  AlertRule (1) ──(1:N)── AlertEvent (*)

跨域外键:
  User.role_id → Role.id
  PublishedVersion.profile_id → DialogProfile.id
  PublishedVersion.published_by → User.id
  ProfileLibraryBinding.library_id → IntentLibrary.id
  BatchTest.profile_id → DialogProfile.id
```

### 3.8 数据迁移规范

**工具**: Alembic (SQLAlchemy 配套)
**命名**: `V{timestamp}__描述.py` (Alembic auto-generate)

| 变更类型 | 迁移策略 | 停机要求 |
|---------|---------|---------|
| 新增表 | `op.create_table(...)` | 无 |
| 新增列 (有默认值) | `op.add_column(..., server_default=...)` | 无 |
| 新增列 (无默认值, NOT NULL) | 分两步: ①nullable ADD COLUMN ②UPDATE backfill ③ALTER NOT NULL | 无 |
| 删除列 | 先标记弃用 → 下一版 `op.drop_column(...)` | 无 |
| 修改类型 | 新增列 → 数据迁移 → 删旧列 | 无 |
| 新增索引 | `op.create_index(..., if_not_exists=True)` + CONCURRENTLY | 无 |
| 删除表 | 确认无外键引用后 `op.drop_table(...)` | 需确认 |

---

## 4. 错误码体系

### 4.1 编码格式

**格式**: `E{module}{sub}{seq}` — 6 位 (含前缀 E 共 6 字符)

```
E 10 1 01
│ │  │ │
│ │  │ └─ 序号 (01~99)
│ │  └─── 子模块 (0~9)
│ └────── 模块编号 (10~60)
└──────── 前缀
```

### 4.2 模块编号分配

| 模块编号 | 模块名称 | 子模块编号 |
|---------|---------|-----------|
| 10 | 用户认证 (auth) | 01=认证, 02=用户, 03=角色 |
| 20 | 对话方案 (dialog-profile) | 01=方案CRUD, 02=发布, 03=测试, 04=人设, 05=指令库绑定 |
| 30 | 知识库 (knowledge-base) | 01=分类, 02=文档 |
| 40 | 批量测试 (batch-test) | 01=测试集, 02=用例, 03=执行 |
| 50 | 指令库 (intent-library) | 01=库, 02=意图, 03=词槽, 04=模型, 05=数据集, 06=测试 |
| 60 | 监控 (monitoring) | 01=仪表盘, 02=日志, 03=告警 |

### 4.3 HTTP 状态码映射

| 错误类别 | 子模块编号范围 | HTTP 状态 | 是否可重试 |
|---------|-------------|----------|----------|
| 参数校验 | seq 01~19 | 400 | 否 (修正后重试) |
| 业务规则冲突 | seq 20~49 | 409 / 422 | 否 |
| 资源不存在 | seq 50~59 | 404 | 否 |
| 系统错误 | seq 80~99 | 500 | 是 (指数退避) |

### 4.4 通用错误码

| 错误码 | HTTP | 场景 | 用户提示 | 重试 |
|--------|------|------|---------|------|
| E00001 | 400 | 请求体 JSON 格式错误 | 请求格式错误 | 否 |
| E00002 | 400 | 必填字段缺失 | {字段名}不能为空 | 否 |
| E00003 | 400 | 字段格式/范围校验失败 | {字段名}格式错误 | 否 |
| E00004 | 429 | 请求频率超限 | 请求过于频繁，请稍后再试 | 是 (等待) |
| E00080 | 500 | 未捕获的内部错误 | 系统繁忙，请稍后重试 | 是 |
| E00081 | 502 | 外部服务超时 (LLM/Brave) | 依赖服务异常，请稍后重试 | 是 |
| E00082 | 503 | 数据库连接池耗尽 | 系统繁忙，请稍后重试 | 是 |

> 模块级错误码在各 `dd-<module>.md` 中定义。

---

## 5. 权限模型

### 5.1 完整能力点清单

| # | 能力点 Key | 说明 | 所属模块 | 守护 API 路径 |
|---|-----------|------|---------|-------------|
| 1 | intent_library_read | 查看指令库 | 指令库 | GET /api/v1/intent-libraries[/{id}] |
| 2 | intent_library_create | 创建指令库 | 指令库 | POST /api/v1/intent-libraries |
| 3 | intent_library_update | 编辑指令库 | 指令库 | PUT /api/v1/intent-libraries/{id} |
| 4 | intent_library_delete | 删除指令库 | 指令库 | DELETE /api/v1/intent-libraries/{id} |
| 5 | model_train | 创建训练/评估任务 | 指令库 | POST .../train, .../evaluate |
| 6 | model_test_manage | 管理 testable 状态 | 指令库 | POST .../set-testable |
| 7 | model_publish | 发布模型 | 指令库 | POST .../publish |
| 8 | profile_read | 查看对话方案 | 对话方案 | GET /api/v1/profiles[/{id}] |
| 9 | profile_create | 创建对话方案 | 对话方案 | POST /api/v1/profiles |
| 10 | profile_update | 编辑对话方案 | 对话方案 | PUT /api/v1/profiles/{id} |
| 11 | profile_delete | 删除对话方案 | 对话方案 | DELETE /api/v1/profiles/{id} |
| 12 | profile_publish | 发布对话方案版本 | 对话方案 | POST .../publish |
| 13 | profile_test | 手动测试对话 | 对话方案 | POST .../test/* |
| 14 | knowledge_read | 查看知识库 | 知识库 | GET /api/v1/knowledge/* |
| 15 | knowledge_manage | 管理知识库 | 知识库 | POST/PUT/DELETE /api/v1/knowledge/* |
| 16 | monitoring_read | 查看监控 | 监控 | GET /api/v1/monitoring/* |
| 17 | monitoring_alert_manage | 管理告警规则 | 监控 | POST/PUT/DELETE .../alert-rules/* |
| 18 | batch_test_read | 查看批量测试 | 测试 | GET /api/v1/batch-tests/* |
| 19 | batch_test_manage | 管理批量测试 | 测试 | POST/PUT/DELETE /api/v1/batch-tests/* |
| 20 | user_manage | 管理用户 | 系统 | /api/v1/users/* |
| 21 | role_manage | 管理角色 | 系统 | /api/v1/roles/* |

### 5.2 预设角色与权限映射

| 能力点 | admin | pm | tester |
|--------|-------|----|--------|
| intent_library_read | ✅ | ✅ | ✅ |
| intent_library_create | ✅ | ✅ | ❌ |
| intent_library_update | ✅ | ✅* | ❌ |
| intent_library_delete | ✅ | ✅* | ❌ |
| model_train | ✅ | ✅ | ❌ |
| model_test_manage | ✅ | ✅ | ✅ |
| model_publish | ✅ | ❌ | ❌ |
| profile_read | ✅ | ✅ | ✅ |
| profile_create | ✅ | ✅ | ❌ |
| profile_update | ✅ | ✅ | ❌ |
| profile_delete | ✅ | ✅ | ❌ |
| profile_publish | ✅ | ❌ | ❌ |
| profile_test | ✅ | ✅ | ✅ |
| knowledge_read | ✅ | ✅ | ✅ |
| knowledge_manage | ✅ | ✅ | ❌ |
| monitoring_read | ✅ | ✅ | ✅ |
| monitoring_alert_manage | ✅ | ❌ | ❌ |
| batch_test_read | ✅ | ✅ | ✅ |
| batch_test_manage | ✅ | ✅ | ✅ |
| user_manage | ✅ | ❌ | ❌ |
| role_manage | ✅ | ❌ | ❌ |

> `*` pm 的 update/delete 仅限自己创建的资源 (业务层校验 `created_by`)

### 5.3 权限校验伪代码

```python
def require_capability(capability_key: str):
    """装饰器: 从 JWT 提取 capabilities, 校验是否包含目标能力点"""
    def decorator(func):
        async def wrapper(request, *args, **kwargs):
            token = extract_bearer_token(request)
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

            if capability_key not in payload["capabilities"]:
                raise BusinessException("E10107", "无权限执行此操作", http_status=403)

            request.state.current_user = {
                "user_id": payload["sub"],
                "role_id": payload["role_id"],
                "capabilities": payload["capabilities"]
            }
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
```

---

## 6. 系统级配置

### 6.1 配置项清单

| 配置项 | 类型 | 默认值 | 范围 | 说明 | 对应 |
|--------|------|--------|------|------|------|
| JWT_SECRET_KEY | string | - | - | JWT 签名密钥, 必须通过环境变量设置 | FR-001 |
| JWT_ACCESS_TOKEN_EXPIRE_MINUTES | int | 60 | 5~1440 | access_token 有效期 (分钟) | FR-001 |
| JWT_REFRESH_TOKEN_EXPIRE_DAYS | int | 7 | 1~30 | refresh_token 有效期 (天) | FR-001 |
| SESSION_TIMEOUT_MIN | int | 10 | 1~60 | 设备会话超时 (分钟) | FR-023 |
| DEFAULT_PAGE_SIZE | int | 20 | 1~100 | 默认分页大小 | - |
| MAX_PAGE_SIZE | int | 100 | 20~500 | 最大分页大小 | - |
| DATABASE_URL | string | - | - | PostgreSQL 连接串 | - |
| REDIS_URL | string | - | - | Redis 连接串 | - |
| ZENMUX_API_URL | string | - | - | LLM API 地址 | FR-022 |
| ZENMUX_API_KEY | string | - | - | LLM API 密钥 | FR-022 |
| BRAVE_SEARCH_API_KEY | string | - | - | Brave Search API 密钥 | FR-029 |
| LLM_TIMEOUT_SECONDS | int | 8 | 3~30 | LLM 首字符超时 | FR-022 |
| BRAVE_TIMEOUT_SECONDS | int | 5 | 3~15 | Brave Search 超时 | FR-029 |
| RATE_LIMIT_DIALOG_QPS | int | 10 | 1~100 | /dialog 端点每设备 QPS | SC-006 |
| RATE_LIMIT_ADMIN_RPM | int | 100 | 10~1000 | 后台管理 API 每用户 RPM | - |
| AES_ENCRYPTION_KEY | string | - | - | AES-256 加密密钥 (对话历史/文档) | FR-036 |
| LOG_QUEUE_MAX_SIZE | int | 10000 | 1000~50000 | 异步日志队列上限 | FR-033 |
| LOG_BATCH_SIZE | int | 100 | 10~500 | 日志批量写入大小 | FR-033 |

### 6.2 业务常量

| 常量名 | 值 | 类型 | 说明 | 对应 FR |
|--------|----|------|------|---------|
| MAX_TEXT_INPUT_LENGTH | 500 | int | 用户输入文本最大长度 | FR-017 |
| MAX_MODELS_PER_LIBRARY | 5 | int | 单库模型版本上限 | FR-043 |
| MAX_PERSONAS_PER_PROFILE | 10 | int | 单方案人设上限 | FR-008 |
| DIALOG_HISTORY_WINDOW | 10 | int | 对话历史保留轮数 | FR-023 |
| CLARIFICATION_MAX_ROUNDS | 3 | int | 渐进式澄清最大轮数 | FR-020 |
| HIGH_RISK_TEMP_THRESHOLD | 200 | int | 高风险温度阈值 (°C) | FR-019 |
| HIGH_RISK_DURATION_THRESHOLD | 30 | int | 高风险时长阈值 (分钟) | FR-019 |
| KNOWLEDGE_TOP_K | 5 | int | 知识检索返回条数 | FR-004 |
| KNOWLEDGE_SIMILARITY_THRESHOLD | 0.7 | float | 知识命中最低相似度 | FR-021 |
| TRAINING_TIMEOUT_HOURS | 2 | int | 训练任务超时保护 | FR-044 |
| EVAL_DEFAULT_CASES_PER_INTENT | 10 | int | 默认每意图生成评估用例数 | FR-012 |
| VECTOR_DIMENSION | 768 | int | pgvector 向量维度 (BERT-base) | FR-004 |
| PASSWORD_BCRYPT_ROUNDS | 12 | int | bcrypt 加密轮数 | FR-001 |
| LOGIN_MAX_ATTEMPTS | 5 | int | 登录连续失败锁定阈值 | FR-001 |
| LOGIN_LOCKOUT_MINUTES | 15 | int | 登录锁定时间 (分钟) | FR-001 |

---

## 7. 预置种子数据

### 7.1 内置角色

| ID | 名称 | 描述 | is_builtin |
|----|------|------|-----------|
| role_admin | 系统管理员 | 拥有所有权限 | true |
| role_pm | 产品经理 | 管理指令库、方案、知识库，不可发布模型/方案 | true |
| role_tester | 测试人员 | 只读访问 + 执行测试 | true |

### 7.2 内置用户

| ID | 用户名 | 名称 | 角色 | is_builtin | 说明 |
|----|--------|------|------|-----------|------|
| user_admin | admin | 管理员 | role_admin | true | 初始密码随机生成并写入初始化日志, 首次登录强制修改 |

### 7.3 能力点种子 (21 个)

完整列表见 §5.1。系统初始化时 INSERT 全部 21 个能力点并建立角色映射关系。

### 7.4 种子数据初始化伪代码

```python
async def init_seed_data(db: AsyncSession):
    # 1. 创建能力点
    permissions = [
        Permission(key="intent_library_read", label="查看指令库", module="指令库"),
        # ... 共 21 个
    ]
    db.add_all(permissions)

    # 2. 创建内置角色
    admin_role = Role(id="role_admin", name="系统管理员", is_builtin=True)
    pm_role = Role(id="role_pm", name="产品经理", is_builtin=True)
    tester_role = Role(id="role_tester", name="测试人员", is_builtin=True)
    db.add_all([admin_role, pm_role, tester_role])

    # 3. 分配权限 (admin 全部, pm/tester 按映射表)
    admin_perms = permissions  # 全部
    pm_perms = [p for p in permissions if p.key not in [
        "model_publish", "profile_publish",
        "monitoring_alert_manage", "user_manage", "role_manage"
    ]]
    tester_perms = [p for p in permissions if p.key.endswith("_read")
                    or p.key in ["model_test_manage", "profile_test",
                                 "batch_test_manage", "batch_test_read"]]

    # 4. 创建管理员账号
    initial_password = secrets.token_urlsafe(16)
    admin_user = User(
        id="user_admin", username="admin", name="管理员",
        password_hash=bcrypt.hash(initial_password),
        role_id="role_admin", is_builtin=True
    )
    db.add(admin_user)
    logger.info(f"Admin initial password: {initial_password}")

    await db.commit()
```

---

## 8. 需求追溯矩阵

> 全局文档覆盖跨模块共享需求。模块级追溯在各 dd-<module>.md 中。

| FR 编号 | 需求摘要 | DD 章节 | 覆盖状态 |
|---------|---------|---------|---------|
| FR-001 | 角色权限管理 | §3.1~3.4 实体 + §5 权限模型 + §7 种子数据 | ✅ 完整 |
| FR-015~016 | 版本发布 + 设备重置 | §3.5 PublishedVersion 实体 | ✅ 完整 |
| FR-017 | API 输入格式 | §6.2 MAX_TEXT_INPUT_LENGTH | ✅ 完整 |
| FR-019 | 高风险操作确认 | §6.2 HIGH_RISK 常量 | ✅ 完整 |
| FR-020 | 渐进式多轮澄清 | §3.6 clarification_count + §6.2 CLARIFICATION_MAX_ROUNDS | ✅ 完整 |
| FR-023 | 设备会话管理 | §3.6 DeviceSession 实体 | ✅ 完整 |
| FR-033 | 请求日志配置 | §6.1 LOG_* 配置项 | ✅ 完整 |
| FR-036 | AES-256 加密 | §6.1 AES_ENCRYPTION_KEY | ✅ 完整 |
| FR-053 | 能力点权限 | §3.3 Permission + §5 权限模型 | ✅ 完整 |

---

## 9. 产出物合规检查表

| 模板条款 | 状态 | 说明 |
|---------|------|------|
| §2.1 一对一可编码 | ✅ | 每个实体可直接映射 SQLAlchemy Model |
| §2.2 约束显式化 | ✅ | 所有字段有类型/约束/默认值, 无模糊词 |
| §3 字段有类型+约束+索引 | ✅ | 5 个 PostgreSQL 实体 + 1 个 Redis 实体 |
| §3.3 ER 关系总图 | ✅ | §3.7 覆盖所有模块全部实体关系 |
| §6 错误码分类完整 | ✅ | 6 位编码 + 6 模块 + 通用错误码 |
| §7 权限点对应 API | ✅ | 21 个能力点全部映射到 API 路径 |
| §8.3 种子数据 | ✅ | 3 角色 + 1 用户 + 21 能力点 + 初始化伪代码 |
