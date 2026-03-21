---
version: 2.0
updated: 2026-03-18
scope: 用户认证域 (user-mgmt)
covers_fr: FR-001,FR-053
based_on:
  - ad/ad-user-mgmt.md@v2.0
  - dd-global.md@v2.0
  - spec.md@v1.4
---

# 详细设计 (DD): 用户认证域 (User Management)

## 1. 文档说明

**定位**: 本文档为用户认证域的详细设计，聚焦于认证算法、登录流程、RBAC 中间件和模块级错误码。

**前置依赖**: dd-global.md 已定义以下公共内容（本文档不重复）：
- §3.1 User 实体 (字段、约束、索引)
- §3.2 Role 实体
- §3.3 Permission 实体
- §3.4 RolePermission 关联表
- §5 权限模型 (21 个能力点 + 角色映射)
- §6.1 系统级配置 (JWT_SECRET_KEY 等)
- §6.2 业务常量 (PASSWORD_BCRYPT_ROUNDS 等)
- §7 种子数据 (内置角色/用户/能力点 + 初始化伪代码)

**本文档新增内容**:
- TokenBlacklist / LoginAttempt 存储结构
- User 状态机
- 6 个核心算法伪代码
- 模块级错误码完整表
- 配置项聚合
- 20 个 API 端点实现映射

---

## 2. 设计原则

遵循 dd-global.md §2 + 以下模块级原则：
- **安全纵深**: 密码从不以明文存储或传输；Token 支持主动失效 (黑名单)
- **能力点驱动**: 权限校验按 `capability_key` 而非角色名判定 (FR-053)
- **最小信息泄露**: 登录失败统一返回 "用户名或密码错误"，不区分 "用户不存在" 与 "密码错误"

---

## 3. 数据模型 (模块补充)

> 基础实体 User / Role / Permission / RolePermission 定义见 dd-global.md §3.1~3.4。

### 3.1 TokenBlacklist (Redis)

用于登出和禁用用户时立即使 Token 失效。

**存储方式**: Redis SET + 单 key TTL

| Key 模式 | 值 | TTL | 说明 |
|----------|-----|-----|------|
| `token_blacklist:{jti}` | `"1"` | 等于该 Token 的剩余有效期 | access_token 黑名单条目 |
| `token_blacklist:refresh:{jti}` | `"1"` | 等于该 refresh_token 的剩余有效期 | refresh_token 黑名单条目 |
| `user_tokens:{user_id}` | SET of `{jti}` | 无 TTL (由代码维护) | 用户所有活跃 Token 的 jti 集合，用于禁用时批量加黑名单 |

**操作**:

| 场景 | 操作 |
|------|------|
| 用户登出 | SADD `token_blacklist:{jti}` + SREM `user_tokens:{user_id}` 移除该 jti |
| 用户被禁用 | SMEMBERS `user_tokens:{user_id}` → 逐个 SADD `token_blacklist:{jti}` → DEL `user_tokens:{user_id}` |
| 密码重置 | 同禁用用户操作 (批量加黑名单) |
| Token 校验 | EXISTS `token_blacklist:{jti}` — O(1) |

**容量估算**: 用户 ≤10，每人最多 1 个 access + 1 个 refresh = 最多 20 个 key，内存可忽略。

### 3.2 LoginAttempt (Redis)

用于登录频率限制和连续失败锁定。

**存储方式**: Redis String with TTL

| Key 模式 | 类型 | TTL | 说明 |
|----------|------|-----|------|
| `login_rate:{ip}` | Counter (INCR) | 60s | 同一 IP 每分钟登录尝试次数 |
| `login_fail:{username}` | Counter (INCR) | 900s (15min) | 同一用户名连续失败次数 |
| `login_lockout:{username}` | String `"1"` | 900s (15min) | 锁定标记，存在即表示锁定中 |

**操作**:

| 场景 | 操作 |
|------|------|
| 登录请求到达 | INCR `login_rate:{ip}` (首次设 EX=60); 若值 > 5 → 拒绝 (E00004) |
| 登录失败 | INCR `login_fail:{username}` (首次设 EX=900); 若值 ≥ 5 → SETEX `login_lockout:{username}` 900 |
| 登录成功 | DEL `login_fail:{username}`, DEL `login_lockout:{username}` |
| 登录前检查 | EXISTS `login_lockout:{username}` — 若存在 → 拒绝 (E10108) |

### 3.3 JWT Payload 结构 (补充字段说明)

```json
{
  "sub": "uuid — User.id",
  "jti": "uuid — Token 唯一标识，用于黑名单",
  "role_id": "uuid — 当前角色 ID",
  "capabilities": ["string[] — 能力点 key 数组"],
  "type": "access | refresh",
  "exp": "int — 过期时间戳 (UTC)",
  "iat": "int — 签发时间戳 (UTC)"
}
```

| 字段 | 类型 | access_token | refresh_token | 说明 |
|------|------|:---:|:---:|------|
| sub | string (UUID) | ✅ | ✅ | 用户 ID |
| jti | string (UUID) | ✅ | ✅ | Token 唯一标识 |
| role_id | string (UUID) | ✅ | ❌ | 角色 ID |
| capabilities | string[] | ✅ | ❌ | 能力点列表 |
| type | string | `"access"` | `"refresh"` | Token 类型区分 |
| exp | int | iat + 3600 | iat + 604800 | 过期时间 |
| iat | int | ✅ | ✅ | 签发时间 |

---

## 4. 状态机

### 4.1 User 状态机

```
                  create_user()
                       │
                       ▼
               ┌──────────────┐
               │    active     │◄──────────────┐
               └──────┬───────┘                │
                      │                        │
          disable_user()                enable_user()
          [非内置 admin]               [仅 admin 操作]
          [非最后 admin]
                      │                        │
                      ▼                        │
               ┌──────────────┐                │
               │   disabled    │───────────────┘
               └──────────────┘
```

**状态定义**:

| 状态 | 值 | 说明 |
|------|-----|------|
| active | `"active"` | 正常，可登录和使用系统 |
| disabled | `"disabled"` | 禁用，不可登录；已有 Token 全部加入黑名单 |

**转换规则**:

| 源状态 | 目标状态 | 触发条件 | 守卫条件 | 副作用 |
|--------|---------|---------|---------|--------|
| active | disabled | PUT /api/v1/users/{id} `{status: "disabled"}` | (1) 目标用户 `is_builtin = false` (2) 系统中 active 且拥有全部权限的管理员 ≥ 2 | 该用户所有 Token 加入 Redis 黑名单 |
| disabled | active | PUT /api/v1/users/{id} `{status: "active"}` | 操作者具有 `user_manage` 能力点 | 无额外副作用 |

**不变式**:
- 内置 admin (`is_builtin = true`) 永远不可被禁用 → 违反时返回 E10203
- 系统至少保留一个 active 的管理员用户 → 违反时返回 E10204

---

## 5. 核心算法

### 5.1 JWT Generation (令牌生成)

**输入**: User 对象 (含 role + permissions)
**输出**: `{access_token, refresh_token}`
**依赖**: `JWT_SECRET_KEY`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`, `JWT_REFRESH_TOKEN_EXPIRE_DAYS`

```python
import jwt
import uuid
from datetime import datetime, timedelta, timezone

def generate_tokens(user: User, permissions: list[Permission]) -> dict:
    now = datetime.now(timezone.utc)
    access_jti = str(uuid.uuid4())
    refresh_jti = str(uuid.uuid4())

    # --- access_token ---
    access_payload = {
        "sub": str(user.id),
        "jti": access_jti,
        "role_id": str(user.role_id),
        "capabilities": [p.key for p in permissions],
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()),
    }
    access_token = jwt.encode(access_payload, JWT_SECRET_KEY, algorithm="HS256")

    # --- refresh_token ---
    refresh_payload = {
        "sub": str(user.id),
        "jti": refresh_jti,
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)).timestamp()),
    }
    refresh_token = jwt.encode(refresh_payload, JWT_SECRET_KEY, algorithm="HS256")

    # --- 记录活跃 Token ---
    redis.sadd(f"user_tokens:{user.id}", access_jti, refresh_jti)
    redis.setex(f"token_blacklist_ttl:{access_jti}", JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60, "")
    redis.setex(f"token_blacklist_ttl:{refresh_jti}", JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400, "")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "expires_in": JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }
```

**边界条件**:
- `capabilities` 为空数组时仍可生成 Token (用户登录成功但无任何权限)
- `JWT_SECRET_KEY` 未配置时启动阶段直接 panic，不允许运行

### 5.2 JWT Verification (令牌校验)

**输入**: Authorization header 中的 Bearer token
**输出**: 解码后的 payload 或抛出认证异常
**时间复杂度**: O(1) — 签名校验 + Redis EXISTS

```python
def verify_access_token(token: str) -> dict:
    # Step 1: 解码并验证签名 + 过期时间
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=["HS256"],
            options={"require": ["sub", "jti", "role_id", "capabilities", "type", "exp"]}
        )
    except jwt.ExpiredSignatureError:
        raise AuthException("E10104", "Token 已过期，请重新登录", http_status=401)
    except jwt.InvalidTokenError:
        raise AuthException("E10105", "Token 无效", http_status=401)

    # Step 2: 校验 Token 类型
    if payload.get("type") != "access":
        raise AuthException("E10105", "Token 无效", http_status=401)

    # Step 3: 黑名单检查 (登出/禁用)
    if redis.exists(f"token_blacklist:{payload['jti']}"):
        raise AuthException("E10106", "Token 已失效", http_status=401)

    return payload
```

**边界条件**:
- HS256 签名无效 → E10105
- Token 缺少必需字段 (sub/jti/capabilities) → E10105
- Token 已在黑名单 → E10106
- 使用 refresh_token 访问受保护端点 → E10105 (type 不匹配)
- 时钟偏差: `jwt.decode` 默认允许 ≤ 0 秒 leeway；若部署多节点需通过 NTP 同步

### 5.3 Password Hashing (密码哈希)

**算法**: bcrypt, `PASSWORD_BCRYPT_ROUNDS = 12`
**输出**: 60 字符 bcrypt 哈希字符串 (`$2b$12$...`)

```python
import bcrypt

BCRYPT_ROUNDS = 12  # dd-global.md §6.2 PASSWORD_BCRYPT_ROUNDS

def hash_password(plain_password: str) -> str:
    """
    单次 hash 耗时约 250ms (rounds=12), 可防暴力破解。
    rounds 每 +1 耗时翻倍，12 为安全性与响应速度的平衡点。
    """
    validate_password_strength(plain_password)
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        password_hash.encode("utf-8")
    )


def validate_password_strength(password: str) -> None:
    """
    规则 (dd-global.md §3.1):
    - 长度 ≥ 8
    - 至少包含 1 个字母 + 1 个数字
    正则: ^(?=.*[a-zA-Z])(?=.*\d).{8,}$
    """
    import re
    if not re.match(r"^(?=.*[a-zA-Z])(?=.*\d).{8,}$", password):
        raise BusinessException("E10205", "密码至少 8 位，需包含字母和数字", http_status=422)
```

**边界条件**:
- 空字符串密码 → `validate_password_strength` 拦截 (长度不足)
- Unicode 密码 (中文等) → bcrypt 支持 UTF-8 编码后 hash，但密码策略要求至少包含字母+数字
- 极长密码 (> 72 bytes) → bcrypt 自动截断至 72 bytes；策略上不额外限制上限

### 5.4 Token Refresh Flow (令牌刷新)

**输入**: `refresh_token`
**输出**: 新的 `access_token` (refresh_token 不轮换)
**设计决策**: refresh_token 自身有效期内不轮换，降低并发刷新的竞态风险

```python
def refresh_access_token(refresh_token: str) -> dict:
    # Step 1: 解码 refresh_token
    try:
        payload = jwt.decode(
            refresh_token,
            JWT_SECRET_KEY,
            algorithms=["HS256"],
            options={"require": ["sub", "jti", "type", "exp"]}
        )
    except jwt.ExpiredSignatureError:
        raise AuthException("E10104", "Token 已过期，请重新登录", http_status=401)
    except jwt.InvalidTokenError:
        raise AuthException("E10105", "Token 无效", http_status=401)

    # Step 2: 校验类型
    if payload.get("type") != "refresh":
        raise AuthException("E10105", "Token 无效", http_status=401)

    # Step 3: 黑名单检查
    if redis.exists(f"token_blacklist:refresh:{payload['jti']}"):
        raise AuthException("E10106", "Token 已失效", http_status=401)

    # Step 4: 查库获取最新用户状态和权限
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user:
        raise AuthException("E10202", "用户不存在", http_status=404)
    if user.status == "disabled":
        raise AuthException("E10103", "账号已被禁用，请联系管理员", http_status=403)

    permissions = db.query(Permission).join(RolePermission).filter(
        RolePermission.role_id == user.role_id
    ).all()

    # Step 5: 生成新的 access_token
    now = datetime.now(timezone.utc)
    new_jti = str(uuid.uuid4())
    access_payload = {
        "sub": str(user.id),
        "jti": new_jti,
        "role_id": str(user.role_id),
        "capabilities": [p.key for p in permissions],
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()),
    }
    new_access_token = jwt.encode(access_payload, JWT_SECRET_KEY, algorithm="HS256")

    redis.sadd(f"user_tokens:{user.id}", new_jti)

    return {
        "access_token": new_access_token,
        "expires_in": JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }
```

**边界条件**:
- 用户在 refresh_token 有效期内被禁用 → Step 4 拦截 (E10103)
- 用户角色被修改 → Step 4 重新查库，新 access_token 反映最新权限
- 并发刷新 → 允许多个 access_token 同时有效（每个有独立 jti）
- refresh_token 已过期 → 必须重新登录

### 5.5 Login Rate Limiting (登录频率限制)

**策略**: 双层防护 — IP 级频率 + 用户名级连续失败锁定
**依赖**: Redis INCR + TTL

```python
LOGIN_MAX_ATTEMPTS = 5          # dd-global.md §6.2
LOGIN_LOCKOUT_MINUTES = 15      # dd-global.md §6.2
LOGIN_RATE_PER_MINUTE = 5       # 同一 IP 每分钟最大尝试次数

async def check_login_rate_limit(ip: str, username: str) -> None:
    """登录请求前置检查，任一条件触发即拒绝。"""

    # Layer 1: IP 级频率限制 (防分布式暴力破解)
    ip_key = f"login_rate:{ip}"
    count = await redis.incr(ip_key)
    if count == 1:
        await redis.expire(ip_key, 60)
    if count > LOGIN_RATE_PER_MINUTE:
        raise BusinessException("E00004", "请求过于频繁，请稍后再试", http_status=429)

    # Layer 2: 用户名级锁定检查 (防针对性暴力破解)
    lockout_key = f"login_lockout:{username}"
    if await redis.exists(lockout_key):
        ttl = await redis.ttl(lockout_key)
        raise AuthException(
            "E10108",
            f"登录失败次数过多，请 {ttl // 60 + 1} 分钟后再试",
            http_status=429
        )


async def record_login_failure(username: str) -> None:
    """登录失败后记录，达到阈值则锁定。"""
    fail_key = f"login_fail:{username}"
    count = await redis.incr(fail_key)
    if count == 1:
        await redis.expire(fail_key, LOGIN_LOCKOUT_MINUTES * 60)

    if count >= LOGIN_MAX_ATTEMPTS:
        await redis.setex(
            f"login_lockout:{username}",
            LOGIN_LOCKOUT_MINUTES * 60,
            "1"
        )


async def clear_login_failures(username: str) -> None:
    """登录成功后清除失败计数和锁定标记。"""
    await redis.delete(f"login_fail:{username}", f"login_lockout:{username}")
```

**边界条件**:
- Redis 不可用时，降级为允许登录 (可用性优先)；应记录 WARN 日志
- 同一 IP 不同用户名 → IP 层面仍受限 (防枚举)
- 锁定期间即使密码正确也拒绝 → 返回 E10108 且不暴露密码正确与否
- 服务重启 → Redis 数据持久，锁定状态不丢失

### 5.6 RBAC Middleware (能力点权限校验)

**原则**: 权限校验以 `capability_key` 为准，不直接检查 `role_id` 或角色名 (FR-053)

```python
from functools import wraps
from typing import Union

def require_capability(*capability_keys: str, require_all: bool = True):
    """
    路由装饰器: 校验当前用户是否具有指定能力点。

    参数:
        capability_keys: 一个或多个能力点 key
        require_all: True 则要求全部匹配 (AND), False 则任一匹配 (OR)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(request, *args, **kwargs):
            # Step 1: 提取并校验 Token (调用 §5.2)
            token = extract_bearer_token(request)
            if not token:
                raise AuthException("E10102", "请先登录", http_status=401)

            payload = verify_access_token(token)

            # Step 2: 能力点匹配
            user_caps = set(payload.get("capabilities", []))
            required = set(capability_keys)

            if require_all:
                missing = required - user_caps
                if missing:
                    raise AuthException("E10107", "无权限执行此操作", http_status=403)
            else:
                if not required & user_caps:
                    raise AuthException("E10107", "无权限执行此操作", http_status=403)

            # Step 3: 注入当前用户上下文
            request.state.current_user = CurrentUser(
                user_id=payload["sub"],
                role_id=payload["role_id"],
                capabilities=payload["capabilities"],
            )

            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


def extract_bearer_token(request) -> str | None:
    """从 Authorization header 提取 Bearer token。"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    return auth_header[7:]
```

**使用示例**:

```python
@router.post("/api/v1/users")
@require_capability("user_manage")
async def create_user(request, body: CreateUserRequest):
    ...

@router.post("/api/v1/intent-libraries/{id}/publish")
@require_capability("model_publish")
async def publish_model(request, id: str):
    ...

@router.delete("/api/v1/intent-libraries/{id}")
@require_capability("intent_library_delete")
async def delete_library(request, id: str):
    # 二次校验: PM 仅可删除自己创建的
    current = request.state.current_user
    library = await get_library(id)
    if "intent_library_delete" in current.capabilities and current.role_id != ADMIN_ROLE_ID:
        if library.created_by != current.user_id:
            raise AuthException("E10107", "无权限执行此操作", http_status=403)
    ...
```

**中间件注册顺序**:

```
Request → CORS → RateLimiter → JWTAuthMiddleware → CapabilityCheck → Route Handler
```

| 层级 | 职责 | 失败响应 |
|------|------|---------|
| JWTAuthMiddleware | 解析 Token, 验签, 过期检查, 黑名单检查 | 401 (E10102/E10104/E10105/E10106) |
| @require_capability | 从 payload.capabilities 校验能力点 | 403 (E10107) |
| 业务层 (可选) | 资源 owner 校验 (PM 限自己资源) | 403 (E10107) |

**免鉴权端点白名单**:

| 路径 | 方法 | 说明 |
|------|------|------|
| /api/v1/auth/login | POST | 登录 |
| /api/v1/auth/refresh | POST | 刷新 Token |
| /api/v1/health | GET | 健康检查 |
| /api/v1/device/dialog | POST | 设备对话 (走设备鉴权，非 JWT) |

---

## 6. 错误码

**编码规则**: `E1{sub}{seq}` — 模块编号 10 (用户认证域)

- `sub` = 01 (认证), 02 (用户), 03 (角色)
- `seq` = 01~99 序号

### 6.1 认证子模块 (E101xx)

| 错误码 | HTTP | 触发场景 | 用户提示 | 可重试 | 处理建议 |
|--------|------|---------|---------|--------|---------|
| E10101 | 401 | 用户名或密码错误 (含用户不存在) | 用户名或密码错误 | 否 (修正后重试) | 前端清空密码框 |
| E10102 | 401 | 请求未携带 Authorization header 或格式非 Bearer | 请先登录 | 否 | 前端跳转登录页 |
| E10103 | 403 | 用户账号处于 disabled 状态 | 账号已被禁用，请联系管理员 | 否 | 联系管理员启用 |
| E10104 | 401 | access_token 或 refresh_token 已过期 | Token 已过期，请重新登录 | 否 | 前端尝试 refresh → 若 refresh 也过期则跳转登录页 |
| E10105 | 401 | Token 签名无效 / 必需字段缺失 / 类型不匹配 | Token 无效 | 否 | 前端清除本地 Token 并跳转登录页 |
| E10106 | 401 | Token jti 存在于 Redis 黑名单 (已登出或被禁用) | Token 已失效 | 否 | 前端跳转登录页 |
| E10107 | 403 | 用户不具有路由所需的 capability_key | 无权限执行此操作 | 否 | 前端隐藏/禁用对应操作按钮 |
| E10108 | 429 | 同一用户名连续登录失败 ≥5 次，进入 15 分钟锁定 | 登录失败次数过多，请 {N} 分钟后再试 | 是 (等待) | 前端显示倒计时 |

### 6.2 用户子模块 (E102xx)

| 错误码 | HTTP | 触发场景 | 用户提示 | 可重试 | 处理建议 |
|--------|------|---------|---------|--------|---------|
| E10201 | 409 | 创建用户时 username 已存在 | 用户名已存在 | 否 (换名) | 前端标红 username 字段 |
| E10202 | 404 | 操作的目标用户 ID 不存在 | 用户不存在 | 否 | 前端刷新列表 |
| E10203 | 422 | 尝试禁用 `is_builtin=true` 的管理员账号 | 不能禁用内置管理员账号 | 否 | 前端禁用该用户的 "禁用" 按钮 |
| E10204 | 422 | 禁用后系统将无 active 管理员 | 系统至少需要一个启用的管理员 | 否 | 前端提示需先启用其他管理员 |
| E10205 | 422 | 密码不满足强度规则 (< 8位 / 缺字母 / 缺数字) | 密码至少 8 位，需包含字母和数字 | 否 (修正后重试) | 前端实时校验密码强度 |
| E10206 | 422 | 删除用户但用户处于 active 状态 | 请先禁用用户再删除 | 否 | 前端引导先禁用 |

### 6.3 角色子模块 (E103xx)

| 错误码 | HTTP | 触发场景 | 用户提示 | 可重试 | 处理建议 |
|--------|------|---------|---------|--------|---------|
| E10301 | 409 | 创建角色时 name 已存在 | 角色名称已存在 | 否 (换名) | 前端标红 name 字段 |
| E10302 | 422 | 删除角色时存在关联用户 (users.role_id 引用) | 该角色下有用户，请先迁移用户角色 | 否 | 前端展示关联用户数 |
| E10303 | 422 | 尝试删除 `is_builtin=true` 的内置角色 | 内置角色不可删除 | 否 | 前端隐藏内置角色的删除按钮 |
| E10304 | 404 | 操作的目标角色 ID 不存在 | 角色不存在 | 否 | 前端刷新列表 |
| E10305 | 422 | 更新角色权限时提交了不存在的 capability_key | 包含无效的能力点: {keys} | 否 (修正) | 前端从能力点列表选择 |

---

## 7. 完整登录流程 (组合算法)

将上述算法组合为完整的登录端点实现：

```python
async def login(request, body: LoginRequest) -> LoginResponse:
    ip = get_client_ip(request)

    # Phase 1: 频率限制 (§5.5)
    await check_login_rate_limit(ip, body.username)

    # Phase 2: 用户查询
    user = await db.query(User).filter(User.username == body.username).first()
    if not user:
        await record_login_failure(body.username)
        raise AuthException("E10101", "用户名或密码错误", http_status=401)

    # Phase 3: 密码验证 (§5.3)
    if not verify_password(body.password, user.password_hash):
        await record_login_failure(body.username)
        raise AuthException("E10101", "用户名或密码错误", http_status=401)

    # Phase 4: 状态检查 (§4.1)
    if user.status == "disabled":
        raise AuthException("E10103", "账号已被禁用，请联系管理员", http_status=403)

    # Phase 5: 加载权限
    permissions = await db.query(Permission).join(RolePermission).filter(
        RolePermission.role_id == user.role_id
    ).all()

    role = await db.query(Role).filter(Role.id == user.role_id).first()

    # Phase 6: 生成 Token (§5.1)
    tokens = generate_tokens(user, permissions)

    # Phase 7: 清除失败计数 (§5.5)
    await clear_login_failures(body.username)

    # Phase 8: 更新最后登录时间
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    return LoginResponse(
        code="000000",
        data={
            **tokens,
            "user": {
                "id": str(user.id),
                "username": user.username,
                "name": user.name,
                "role": {"id": str(role.id), "name": role.name},
                "capabilities": [p.key for p in permissions],
            }
        },
        msg="success"
    )
```

---

## 8. 配置与常量

> 所有配置项原始定义见 dd-global.md §6。本节聚合本模块使用的配置供快速参考。

### 8.1 认证配置

| 配置项 | 类型 | 默认值 | 范围 | 来源 |
|--------|------|--------|------|------|
| JWT_SECRET_KEY | string | (必填, 无默认) | ≥ 32 字符 | 环境变量 |
| JWT_ACCESS_TOKEN_EXPIRE_MINUTES | int | 60 | 5~1440 | 环境变量 |
| JWT_REFRESH_TOKEN_EXPIRE_DAYS | int | 7 | 1~30 | 环境变量 |
| JWT_ALGORITHM | string | `"HS256"` | 固定 | 代码常量 |

### 8.2 安全常量

| 常量 | 值 | 说明 | 来源 |
|------|----|------|------|
| PASSWORD_BCRYPT_ROUNDS | 12 | bcrypt 哈希轮数 | dd-global.md §6.2 |
| LOGIN_MAX_ATTEMPTS | 5 | 连续失败锁定阈值 | dd-global.md §6.2 |
| LOGIN_LOCKOUT_MINUTES | 15 | 锁定时间 (分钟) | dd-global.md §6.2 |
| LOGIN_RATE_PER_MINUTE | 5 | 同一 IP 每分钟最大登录尝试 | 本文档 §5.5 |

### 8.3 密码策略

| 规则 | 约束 | 正则 |
|------|------|------|
| 最小长度 | 8 字符 | `.{8,}` |
| 字符类型 | 至少 1 字母 + 1 数字 | `(?=.*[a-zA-Z])(?=.*\d)` |
| 完整正则 | — | `^(?=.*[a-zA-Z])(?=.*\d).{8,}$` |

### 8.4 Redis Key 前缀汇总

| Key 模式 | 用途 | TTL |
|----------|------|-----|
| `token_blacklist:{jti}` | access_token 黑名单 | ≤ 3600s |
| `token_blacklist:refresh:{jti}` | refresh_token 黑名单 | ≤ 604800s |
| `user_tokens:{user_id}` | 用户活跃 Token 集合 | 无 (代码维护) |
| `login_rate:{ip}` | IP 级登录频率 | 60s |
| `login_fail:{username}` | 用户名连续失败计数 | 900s |
| `login_lockout:{username}` | 用户名锁定标记 | 900s |

---

## 9. API 实现映射

### 9.1 认证 API (4 端点)

| # | 方法 | 路径 | 能力点 | Service 方法 | 核心算法 | 错误码 | FR |
|---|------|------|--------|-------------|---------|--------|-----|
| 1 | POST | /api/v1/auth/login | 无 (公开) | `AuthService.login()` | §5.5 频率限制 → §5.3 密码验证 → §5.1 Token 生成 | E10101, E10103, E10108, E00004 | FR-001 |
| 2 | POST | /api/v1/auth/logout | 已认证 | `AuthService.logout()` | 从 payload 取 jti → 加入黑名单 (§3.1) | E10102, E10105 | FR-001 |
| 3 | GET | /api/v1/auth/me | 已认证 | `AuthService.get_current_user()` | §5.2 Token 校验 → 查库返回用户+角色+权限 | E10102, E10104~E10106 | FR-001 |
| 4 | POST | /api/v1/auth/refresh | 无 (携带 refresh_token) | `AuthService.refresh_token()` | §5.4 Token 刷新 | E10103~E10106 | FR-001 |

#### 端点实现细节

**POST /api/v1/auth/login**

| 步骤 | 操作 | 失败响应 |
|------|------|---------|
| 1 | 输入校验: username 非空 (3~20 字母数字下划线), password 非空 (≥8 位) | 400 E00002/E00003 |
| 2 | IP 频率限制检查 | 429 E00004 |
| 3 | 用户名锁定检查 | 429 E10108 |
| 4 | 查询 User by username | 401 E10101 (不存在) |
| 5 | bcrypt 密码比对 | 401 E10101 (不匹配) |
| 6 | 状态检查 (disabled?) | 403 E10103 |
| 7 | 加载 Role + Permissions | — |
| 8 | 生成 access_token + refresh_token | — |
| 9 | 清除失败计数, 更新 last_login_at | — |
| 10 | 返回 200 + tokens + user_info | — |

**POST /api/v1/auth/logout**

| 步骤 | 操作 | 失败响应 |
|------|------|---------|
| 1 | 从 Authorization header 提取 Token | 401 E10102 |
| 2 | 验证 Token (可选: 即使过期也允许登出) | — |
| 3 | 取 jti, 计算剩余 TTL | — |
| 4 | SETEX `token_blacklist:{jti}` TTL "1" | — |
| 5 | 从 body 获取 refresh_token (如有), 同样加入黑名单 | — |
| 6 | SREM `user_tokens:{user_id}` 移除对应 jti | — |
| 7 | 返回 200 `{code: "000000", data: null, msg: "登出成功"}` | — |

**POST /api/v1/auth/refresh**

| 步骤 | 操作 | 失败响应 |
|------|------|---------|
| 1 | 输入校验: refresh_token 非空 | 400 E00002 |
| 2 | 解码 refresh_token, 验签+过期 | 401 E10104/E10105 |
| 3 | 校验 type == "refresh" | 401 E10105 |
| 4 | 黑名单检查 | 401 E10106 |
| 5 | 查库: 用户存在? 状态 active? | 404 E10202 / 403 E10103 |
| 6 | 加载最新 Role + Permissions | — |
| 7 | 生成新 access_token (新 jti) | — |
| 8 | 返回 200 `{access_token, expires_in}` | — |

### 9.2 用户管理 API (7 端点)

| # | 方法 | 路径 | 能力点 | Service 方法 | 错误码 | FR |
|---|------|------|--------|-------------|--------|-----|
| 5 | GET | /api/v1/users | user_manage | `UserService.list_users()` | E10107 | FR-001 |
| 6 | POST | /api/v1/users | user_manage | `UserService.create_user()` | E10107, E10201, E10205, E10304 | FR-001 |
| 7 | GET | /api/v1/users/{id} | user_manage | `UserService.get_user()` | E10107, E10202 | FR-001 |
| 8 | PUT | /api/v1/users/{id} | user_manage | `UserService.update_user()` | E10107, E10202, E10203, E10204 | FR-001 |
| 9 | DELETE | /api/v1/users/{id} | user_manage | `UserService.delete_user()` | E10107, E10202, E10203, E10206 | FR-001 |
| 10 | PUT | /api/v1/users/{id}/roles | user_manage | `UserService.assign_role()` | E10107, E10202, E10304 | FR-001 |
| 11 | PUT | /api/v1/users/{id}/password | user_manage | `UserService.reset_password()` | E10107, E10202, E10205 | FR-001 |

#### 关键端点实现

**POST /api/v1/users** (创建用户)

| 步骤 | 操作 | 失败响应 |
|------|------|---------|
| 1 | 能力点校验: user_manage | 403 E10107 |
| 2 | 输入校验: username (正则), name (≤50), password (强度), role_id (非空) | 400 E00002/E00003 |
| 3 | 唯一性检查: username | 409 E10201 |
| 4 | 角色存在性检查: role_id | 404 E10304 |
| 5 | 密码哈希: `hash_password(password)` | 422 E10205 |
| 6 | INSERT user (status=active, is_builtin=false) | — |
| 7 | 返回 201 + user_info (不含 password_hash) | — |

**PUT /api/v1/users/{id}** (更新用户 / 禁用)

| 步骤 | 操作 | 失败响应 |
|------|------|---------|
| 1 | 能力点校验: user_manage | 403 E10107 |
| 2 | 用户存在性检查 | 404 E10202 |
| 3 | 若 body.status == "disabled": | |
| 3a | — 检查 is_builtin | 422 E10203 |
| 3b | — 检查是否为最后 active 管理员 | 422 E10204 |
| 3c | — 批量加黑名单 (§3.1 操作) | — |
| 4 | UPDATE user 字段 | — |
| 5 | 返回 200 + updated user_info | — |

**PUT /api/v1/users/{id}/password** (重置密码)

| 步骤 | 操作 | 失败响应 |
|------|------|---------|
| 1 | 能力点校验: user_manage | 403 E10107 |
| 2 | 用户存在性检查 | 404 E10202 |
| 3 | 密码强度校验 | 422 E10205 |
| 4 | `hash_password(new_password)` → UPDATE password_hash | — |
| 5 | 批量加黑名单: 该用户所有 Token 失效 | — |
| 6 | 返回 200 `{msg: "密码已重置，用户需重新登录"}` | — |

### 9.3 角色管理 API (8 端点)

| # | 方法 | 路径 | 能力点 | Service 方法 | 错误码 | FR |
|---|------|------|--------|-------------|--------|-----|
| 12 | GET | /api/v1/roles | role_manage | `RoleService.list_roles()` | E10107 | FR-001 |
| 13 | POST | /api/v1/roles | role_manage | `RoleService.create_role()` | E10107, E10301, E10305 | FR-001 |
| 14 | GET | /api/v1/roles/{id} | role_manage | `RoleService.get_role()` | E10107, E10304 | FR-001 |
| 15 | PUT | /api/v1/roles/{id} | role_manage | `RoleService.update_role()` | E10107, E10303, E10304 | FR-001 |
| 16 | DELETE | /api/v1/roles/{id} | role_manage | `RoleService.delete_role()` | E10107, E10302, E10303, E10304 | FR-001 |
| 17 | GET | /api/v1/roles/{id}/permissions | role_manage | `RoleService.get_role_permissions()` | E10107, E10304 | FR-001 |
| 18 | PUT | /api/v1/roles/{id}/permissions | role_manage | `RoleService.update_role_permissions()` | E10107, E10303, E10304, E10305 | FR-001 |
| 19 | GET | /api/v1/permissions | role_manage | `PermissionService.list_permissions()` | E10107 | FR-001 |

#### 关键端点实现

**POST /api/v1/roles** (创建角色)

| 步骤 | 操作 | 失败响应 |
|------|------|---------|
| 1 | 能力点校验: role_manage | 403 E10107 |
| 2 | 输入校验: name (≤30), permissions (非空数组) | 400 E00002/E00003 |
| 3 | 唯一性检查: name | 409 E10301 |
| 4 | 能力点有效性: 校验 permissions[] 中每个 key 存在于 permissions 表 | 422 E10305 |
| 5 | INSERT role (is_builtin=false) | — |
| 6 | INSERT role_permissions 关联 | — |
| 7 | 返回 201 + role_info (含 permissions, user_count=0) | — |

**PUT /api/v1/roles/{id}/permissions** (更新角色权限)

| 步骤 | 操作 | 失败响应 |
|------|------|---------|
| 1 | 能力点校验: role_manage | 403 E10107 |
| 2 | 角色存在性检查 | 404 E10304 |
| 3 | 内置角色检查: `is_builtin` 可修改权限但保留 builtin 标记 | — |
| 4 | 能力点有效性: 校验 permissions[] 全部存在 | 422 E10305 |
| 5 | 事务内: DELETE old role_permissions → INSERT new | — |
| 6 | 返回 200 | — |

> **权限传播延迟**: 角色权限修改后，已登录用户的 JWT 中 capabilities 不会实时更新。需等 access_token 过期并通过 §5.4 Token Refresh 重新获取最新权限，或用户重新登录。access_token 1 小时有效期限制了影响窗口。

**DELETE /api/v1/roles/{id}** (删除角色)

| 步骤 | 操作 | 失败响应 |
|------|------|---------|
| 1 | 能力点校验: role_manage | 403 E10107 |
| 2 | 角色存在性检查 | 404 E10304 |
| 3 | 内置角色保护 | 422 E10303 |
| 4 | 关联用户检查: COUNT users WHERE role_id = {id} | 422 E10302 |
| 5 | DELETE role_permissions (CASCADE) → DELETE role | — |
| 6 | 返回 200 | — |

### 9.4 权限查询 API (1 端点)

| # | 方法 | 路径 | 能力点 | Service 方法 | 错误码 | FR |
|---|------|------|--------|-------------|--------|-----|
| 20 | GET | /api/v1/permissions | role_manage | `PermissionService.list_all()` | E10107 | FR-053 |

返回全部 21 个能力点（含 key, label, module），用于角色编辑页面的权限选择器。

### 9.5 端点总览 (20 个)

| 分组 | 端点数 | 认证方式 |
|------|--------|---------|
| 认证 (auth) | 4 | login/refresh 公开; logout/me 需 access_token |
| 用户 (users) | 7 | access_token + user_manage |
| 角色 (roles) | 8 | access_token + role_manage |
| 权限 (permissions) | 1 | access_token + role_manage |
| **合计** | **20** | — |

---

## 10. 前端 UI 组件清单

> 数据来源: pd-all/pd-user-mgmt/index.html

> **排除项**：「说明」按钮及其 Drawer 属于 AD/DD 逻辑参考文档，不纳入 PD 覆盖率。

### 10.1 统计卡片清单

| # | 卡片标题 | 数据来源 (API → 计算) | 图标 | 值样式 | 布局 |
|---|---------|----------------------|------|--------|------|
| 1 | 总账号数 | GET /api/v1/users → `list.length` | TeamOutlined | 默认色 | Row > Col span=6 |
| 2 | 管理员 | GET /api/v1/users → `filter(role=admin).length` | SafetyCertificateOutlined | `color: #ff4d4f` | Row > Col span=6 |
| 3 | 产品经理 | GET /api/v1/users → `filter(role=pm).length` | UserOutlined | `color: #1890ff` | Row > Col span=6 |
| 4 | 测试人员 | GET /api/v1/users → `filter(role=tester).length` | ExperimentOutlined | `color: #52c41a` | Row > Col span=6 |

组件: `Card` > `Statistic`，4 列等宽排列于 "账号管理" Tab 顶部。

### 10.2 表格列映射

#### 10.2.1 用户列表 Table (Tab "账号管理")

| # | 列标题 | dataIndex | 宽度 | 渲染方式 | API 字段映射 |
|---|--------|-----------|------|---------|-------------|
| 1 | 用户名 | username | 120px | `<span>` monospace 字体 | `User.username` |
| 2 | 姓名 | name | 100px | 纯文本 | `User.name` |
| 3 | 角色 | role | 120px | `Tag` (admin → red "系统管理员", pm → blue "产品经理", tester → green "测试人员") | `Role.name` |
| 4 | 状态 | status | 80px | `Tag` (active → green "启用", disabled → default "禁用") | `User.status` |
| 5 | 创建时间 | createdAt | 120px | 日期文本 (YYYY-MM-DD) | `User.created_at` |
| 6 | 最后登录 | lastLogin | 160px | 日期时间文本; 未登录显示 `"-"` | `User.last_login_at` |
| 7 | 操作 | — | 260px | `Button` 编辑角色 + `Button` 重置密码 + `Switch` 启用/禁用 | — |

- **pagination**: false (用户规模 ≤10，无需分页)
- **size**: middle
- **rowKey**: id

#### 10.2.2 能力点权限矩阵 Table (Tab "角色与权限")

| # | 列标题 | dataIndex | 宽度 | 对齐 | 渲染方式 |
|---|--------|-----------|------|------|---------|
| 1 | 能力点 | key | 180px | left | `<span>` monospace, fontSize=12 |
| 2 | 说明 | label | 180px | left | 纯文本 |
| 3 | 系统管理员 | admin | 120px | center | `PermIcon` — ✅ CheckCircleOutlined (green) |
| 4 | 产品经理 | pm | 120px | center | `PermIcon` — ✅ / ⚠ WarningOutlined (orange + Tooltip 条件说明) / ❌ |
| 5 | 测试人员 | tester | 120px | center | `PermIcon` — ✅ / ❌ CloseCircleOutlined (red) |

- **bordered**: true
- **size**: small
- **pagination**: false
- **rowKey**: key
- **数据行数**: 14 行 (14 个能力点, 见 dd-global.md §5)

`PermIcon` 图标含义:

| 图标 | 组件 | 颜色 | 含义 |
|------|------|------|------|
| ✅ | CheckCircleOutlined | `#52c41a` (green) | 拥有该能力点 |
| ❌ | CloseCircleOutlined | `#ff4d4f` (red) | 不拥有该能力点 |
| ⚠ | WarningOutlined | `#fa8c16` (orange) | 有条件拥有 (Tooltip 显示条件文案) |

### 10.3 筛选器 / 搜索条件

| # | 筛选项 | 组件类型 | 说明 |
|---|--------|---------|------|
| — | 无 | — | PD 明确说明用户规模 ≤10，不需要搜索/筛选功能，也无分页 |

> PD 原文: "用户总数不超过 10 人，无分页需求"、"不需要复杂的搜索/筛选功能"。

### 10.4 操作按钮 / 交互入口

| # | 按钮/入口 | 位置 | 组件类型 | 图标 | 权限控制 | 触发行为 |
|---|---------|------|---------|------|---------|---------|
| 1 | 新建账号 | 页面头部右侧 | `Button` (primary) | PlusOutlined | `user_manage` | 打开新建账号 Modal |
| 3 | 编辑角色 | 用户表格操作列 | `Button` (type=link, size=small) | EditOutlined | `user_manage` | 打开编辑角色 Modal，传入当前行 record |
| 4 | 重置密码 | 用户表格操作列 | `Button` (type=link, size=small) | KeyOutlined | `user_manage` | 打开 Modal.confirm 二次确认 |
| 5 | 启用/禁用 | 用户表格操作列 | `Switch` (size=small) | — | `user_manage`; 内置 admin 禁止禁用 (E10203) | 切换 `User.status` (active↔disabled); 禁用时 Token 立即失效 |

### 10.5 特殊交互组件

| # | 组件名 | 组件类型 | 触发方式 | 关键字段 / 内容 | 规格 |
|---|--------|---------|---------|---------------|------|
| 1 | 页面 Tabs | `Tabs` | 顶部标签切换 | Tab① "账号管理" (key=accounts, 默认选中): 统计卡片 + 用户表格; Tab② "角色与权限" (key=roles): 角色卡片组 + 能力点矩阵 | 两个 Tab |
| 2 | 新建账号 Modal | `Modal` + `Form` (layout=vertical) | 点击 "新建账号" 按钮 | username (`Input`, 正则 `^[a-zA-Z0-9_]{3,20}$`, required); name (`Input`, required); password (`Input.Password`, min=8, required); role (`Select`: admin/pm/tester, 默认 pm, required) | width=480, maskClosable=false, okText="创建" |
| 3 | 编辑角色 Modal | `Modal` + `Descriptions` + `Form` + 权限预览 `Table` | 点击 "编辑角色" 按钮 | `Descriptions` (column=2, bordered): 用户名 / 姓名 / 当前角色 Tag; `Form`: newRole `Select` (admin/pm/tester); `Divider` "权限预览"; 权限预览 Table (能力点 label + PermIcon) | width=600, maskClosable=false, okText="保存" |
| 4 | 重置密码 Confirm | `Modal.confirm` | 点击 "重置密码" 按钮 | title="重置密码"; content 含用户姓名+用户名, 告知默认密码 Abc12345; okText="确认重置" (danger); icon=ExclamationCircleOutlined | 危险操作二次确认 |
| 5 | 角色卡片组 | `Card` × 3 | "角色与权限" Tab 内静态展示 | 系统管理员 (border-top: #ff4d4f, SafetyCertificateOutlined); 产品经理 (border-top: #1890ff, TeamOutlined); 测试人员 (border-top: #52c41a, ExperimentOutlined); 各含 `List` 展示能力概要 | Row > Col span=8 × 3 |
| 7 | 角色权限 Alert | `Alert` (type=info) | "角色与权限" Tab 顶部静态展示 | "权限校验以能力点为准，不绑定角色名。角色是能力点的预设组合。" | showIcon |

---

## 11. 需求追溯与合规

### 11.1 需求追溯矩阵

| FR 编号 | 需求摘要 | DD 覆盖章节 | 覆盖状态 |
|---------|---------|------------|---------|
| FR-001 | 角色权限管理、内置管理员、创建账号、分配角色和菜单权限 | §3 TokenBlacklist/LoginAttempt; §4 User 状态机; §5 全部 6 个算法; §6 全部错误码; §9 全部 20 个端点 | ✅ 完整 |
| FR-053 | 权限校验以能力点为准，不绑定角色名 | §5.6 RBAC Middleware (能力点匹配, 不检查 role name); §9.4 权限查询 API | ✅ 完整 |

### 11.2 AD → DD 追溯

| AD 章节 (ad-user-mgmt.md) | DD 对应 | 变化说明 |
|---------------------------|---------|---------|
| §2.1 用户登录流程 | §7 完整登录流程 + §5.1/5.3/5.5 | 补充 jti/黑名单/频率限制伪代码 |
| §2.2 权限校验流程 | §5.2 JWT Verification + §5.6 RBAC Middleware | 补充 require_all/OR 逻辑 + 免鉴权白名单 |
| §2.3 角色与权限管理流程 | §9.3 角色管理 API (#12~#19) | 补充 E10305 (无效能力点) |
| §2.4 用户账号管理流程 | §9.2 用户管理 API (#5~#11) | 补充 E10206 (删除活跃用户) |
| §3.1~3.4 接口契约 | §9 全部端点映射 | 补充步骤级实现细节 |
| §4 异常处理汇总 | §6 错误码 | 新增 E10108/E10206/E10305 |
| §5 模块级风险 | §5.5 频率限制 + §8 配置 | 风险缓解策略落实为算法和配置 |

### 11.3 dd-template 合规检查表

| 模板条款 | 状态 | 说明 |
|---------|------|------|
| §3 数据模型有字段类型+约束 | ✅ | 基础实体引用 dd-global.md; TokenBlacklist/LoginAttempt 有完整 key 结构和 TTL |
| §4 状态机有守卫条件+副作用 | ✅ | User active↔disabled, 含内置 admin 保护和 Token 级联黑名单 |
| §5 核心算法有伪代码+边界条件 | ✅ | 6 个算法全部有 Python 伪代码 + boundary conditions |
| §6 错误码有 HTTP 状态+可重试+处理建议 | ✅ | 3 个子模块共 16 个错误码, 含前端处理建议 |
| §8 配置项有类型+默认值+范围 | ✅ | 聚合引用 dd-global.md + 本模块新增项 |
| §9 API 映射有 Service 方法+算法引用+错误码 | ✅ | 20 个端点全部映射, 关键端点有步骤级实现表 |
| §10 前端 UI 组件清单 | ✅ | 统计卡片/表格列/筛选器/操作按钮/特殊交互 5 个子表, 数据源 PD HTML |
| §11 追溯矩阵完整 | ✅ | FR→DD + AD→DD 双向追溯 |
