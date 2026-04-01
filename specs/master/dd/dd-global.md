---
version: 1.0
scope: global
based_on:
  - specs/master/ad/ad-global.md
  - specs/master/ad/ad-user-mgmt.md
---

# 全局详细设计

## 1. 共享实体

### 1.1 实体: `user_account`

| 字段 | 类型 | 约束 | 默认值 | 索引 | 说明 |
|------|------|------|--------|------|------|
| `id` | `VARCHAR(32)` | PK | `user_###` | 主键 | 与 PD 原型保持 `user_001` 风格 |
| `username` | `VARCHAR(20)` | NOT NULL, UNIQUE, regex `^[A-Za-z0-9_]{3,20}$` | - | 唯一索引 | 登录用户名 |
| `display_name` | `VARCHAR(50)` | NOT NULL | - | - | 前端显示姓名 |
| `password_hash` | `VARCHAR(255)` | NOT NULL | - | - | 哈希口令 |
| `role_key` | `VARCHAR(20)` | NOT NULL, FK `role_definition.role_key` | - | 普通索引 | 当前角色 |
| `status` | `VARCHAR(20)` | NOT NULL, enum `active/disabled` | `active` | 普通索引 | 账号状态 |
| `token_version` | `INT` | NOT NULL, >=1 | `1` | - | 用于让旧 token 失效 |
| `is_builtin_admin` | `BOOLEAN` | NOT NULL | `false` | - | 内置管理员保护标记 |
| `created_at` | `TIMESTAMP` | NOT NULL | `now()` | - | 创建时间 |
| `updated_at` | `TIMESTAMP` | NOT NULL | `now()` | - | 更新时间 |
| `last_login_at` | `TIMESTAMP` | NULL | `null` | - | 最近登录时间 |

### 1.2 实体: `role_definition`

| 字段 | 类型 | 约束 | 默认值 | 索引 | 说明 |
|------|------|------|--------|------|------|
| `role_key` | `VARCHAR(20)` | PK | - | 主键 | `admin/pm/tester` |
| `role_label` | `VARCHAR(50)` | NOT NULL | - | - | 中文名称 |
| `is_builtin` | `BOOLEAN` | NOT NULL | `true` | - | 首版均为内置 |
| `created_at` | `TIMESTAMP` | NOT NULL | `now()` | - | 创建时间 |

### 1.3 实体: `capability_definition`

| 字段 | 类型 | 约束 | 默认值 | 索引 | 说明 |
|------|------|------|--------|------|------|
| `capability_key` | `VARCHAR(64)` | PK | - | 主键 | 例如 `intent_library_write` |
| `description` | `VARCHAR(100)` | NOT NULL | - | - | 中文描述 |
| `condition_note` | `VARCHAR(100)` | NULL | `null` | - | 如“仅自己+草稿” |
| `module_key` | `VARCHAR(40)` | NOT NULL | - | 普通索引 | 对应业务模块 |

### 1.4 实体: `role_capability_binding`

| 字段 | 类型 | 约束 | 默认值 | 索引 | 说明 |
|------|------|------|--------|------|------|
| `role_key` | `VARCHAR(20)` | PK(FK) | - | 组合主键 | 角色 |
| `capability_key` | `VARCHAR(64)` | PK(FK) | - | 组合主键 | 能力点 |
| `condition_note` | `VARCHAR(100)` | NULL | `null` | - | 角色层条件说明 |

### 1.5 ER 总图

```mermaid
erDiagram
    role_definition ||--o{ user_account : grants
    role_definition ||--o{ role_capability_binding : owns
    capability_definition ||--o{ role_capability_binding : maps
```

## 2. 全局错误码体系

| 错误码 | 分类 | 含义 |
|--------|------|------|
| `AUTH-401-TOKEN` | 鉴权 | Token 缺失、失效或版本落后 |
| `AUTH-403-CAPABILITY` | 鉴权 | 当前会话缺少能力点 |
| `USER-404-NOT-FOUND` | 业务 | 目标用户不存在 |
| `USER-409-USERNAME` | 业务 | 用户名重复 |
| `USER-409-BUILTIN-ADMIN` | 业务 | 禁用/修改内置 admin 失败 |
| `USER-409-LAST-ADMIN` | 业务 | 触发最少管理员保护 |
| `USER-422-ROLE` | 输入 | 角色值非法 |
| `USER-422-STATUS` | 输入 | 状态值非法 |
| `USER-422-FORM` | 输入 | 表单字段校验失败 |

## 3. 权限模型

### 3.1 角色与能力点

- `admin`: 全量 14 个能力点
- `pm`: 10 个能力点，其中 `intent_library_write`、`intent_library_delete`、`model_publish` 带条件说明
- `tester`: 6 个能力点，以查看与执行测试为主

### 3.2 能力点判定规则

1. API 中间件只认 `capability_key`，不直接认角色名
2. 前端菜单由 `/api/v1/auth/me` 或登录响应中的 capability 集合决定
3. 角色变更或禁用用户时，必须递增 `token_version`

## 4. 系统级配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `APP_ENV` | `local` | 本地研发环境 |
| `DATABASE_URL` | `postgresql+psycopg://smartchef:smartchef@127.0.0.1:5432/smartchef` | 本地 PG |
| `PASSWORD_RESET_DEFAULT` | `Abc12345` | 首版沿用 PD 口径 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480` | 后台会话默认 8 小时 |

## 5. 预置/种子数据

### 5.1 固定角色

| role_key | role_label |
|----------|------------|
| `admin` | 系统管理员 |
| `pm` | 产品经理 |
| `tester` | 测试人员 |

### 5.2 内置管理员

| username | role_key | status | is_builtin_admin |
|----------|----------|--------|------------------|
| `admin` | `admin` | `active` | `true` |

### 5.3 能力点清单

- `intent_library_read`
- `intent_library_write`
- `intent_library_delete`
- `model_train`
- `model_test_manage`
- `model_publish`
- `profile_read`
- `profile_write`
- `profile_publish`
- `knowledge_write`
- `test_execute`
- `monitoring_read`
- `alert_manage`
- `user_manage`
