# 日志模块方案（细化版）

**目标**：为 SmartChef 平台建立统一、可排查的日志体系，覆盖所有接口与模块，支持问题快速定位。

**实施状态**：✅ 已完成（2026-03-11）
- `app/core/logging_config.py`：按天文件夹 + 2MB 滚动，backend/api 双 logger，**app.* 业务日志汇聚到 backend**
- `app/core/logging_middleware.py`：**请求开始时立即记 START**，含入参 body、出参 resp，按 path 分流
- Pipeline/LLM：链式步骤日志 `[pipeline] START -> route -> command|knowledge|chitchat -> DONE`
- `test/chat`、`dialog/chat`：Pipeline 超时可配置（默认 5 秒，`PIPELINE_CHAT_TIMEOUT_SECONDS`），超时抛 TimeoutError 写入 error.txt
- 单元测试：`tests/unit/test_logging_middleware.py`

---

## 一、需求对照

| 需求 | 方案要点 |
|------|----------|
| 请求日志详细、排查一目了然 | 单条日志含请求上下文、处理链路、耗时、结果；可读文本格式 |
| 报错信息完整 | 异常类型、消息、完整 traceback；HTTP 错误含 status、detail |
| 至少两类日志 | 后台系统日志 + 开放 API 日志，分目录存储 |
| 按天记录、backend 目录下 | `backend/logs/`，按日期建立子文件夹 |

---

## 二、日志分类与目录结构

### 2.1 两类日志定义

| 类型 | 范围 | 用途 | 告警集成 |
|------|------|------|----------|
| **后台系统日志** | 除 `/api/v1/dialog` 外的所有 API；内部服务、启动/关闭 | PM 操作、配置变更、内部异常排查 | 不集成 |
| **开放 API 日志** | `/api/v1/dialog/*`（设备端对话接口） | 设备调用、对话链路、设备维度排查 | **需集成** |

**路由归属**：
- **后台**：`/api/v1/auth`、`/api/v1/intents`、`/api/v1/libraries`、`/api/v1/knowledge`、`/api/v1/profiles`、`/api/v1/test`、`/api/v1/versions`、`/api/v1/batch-test`、`/api/v1/monitoring`、`/api/v1/users`、`/api/v1/health`、`/api/v1/data-management`、`/api/v1/device`（设备管理，非对话）、`/api/v1/testing`
- **开放 API**：`/api/v1/dialog/chat`、`/api/v1/dialog/parse`（若存在）等设备端对话相关

### 2.2 目录结构（按用户确认）

```
smartchef-platform/backend/
├── logs/                                    # 日志根目录（.gitignore）
│   ├── backend_2026-03-10/                  # 后台日志（按天建文件夹）
│   │   ├── app.txt                          # 常规请求日志（超 2MB 滚动为 app.1.txt ...）
│   │   └── error.txt                       # 错误专用（超 2MB 滚动为 error.1.txt ...）
│   └── api_2026-03-10/                     # 开放 API 日志（按天建文件夹）
│       ├── app.txt                         # 常规请求日志（超 2MB 滚动）
│       └── error.txt                       # 错误专用（超 2MB 滚动）
└── app/
    └── core/
        └── logging_config.py                # 日志配置模块
```

**说明**：
- 每天 0 点创建新文件夹，格式 `backend_YYYY-MM-DD`、`api_YYYY-MM-DD`
- 同一请求：成功写 `app.txt`，失败同时写 `app.txt` 与 `error.txt`
- **单文件大小**：若 `app.txt` 或 `error.txt` 超过 2MB，则滚动新建（如 `app.1.txt`、`app.2.txt` 或 `app_1.txt`）
- 无脱敏策略（暂不实现）

---

## 三、单条日志内容规范

### 3.1 常规请求日志（app.txt，可读文本）

**格式示例**：

```
2026-03-10 14:32:01.123 [INFO] [req=abc-123] POST /api/v1/intents 200 45ms ip=192.168.1.1 user=u-001
  body: {"intent_key":"voice_cmd_start","display_name":"启动烹饪"}
  resp: {"id":"...","intent_key":"voice_cmd_start"}
```

**字段约定**：

| 字段 | 说明 | 后台 | 开放 API |
|------|------|------|----------|
| `ts` | 时间戳 `YYYY-MM-DD HH:MM:SS.mmm` | ✓ | ✓ |
| `level` | INFO / WARNING | ✓ | ✓ |
| `request_id` | 请求追踪 ID | ✓ | ✓ |
| `method` | HTTP 方法 | ✓ | ✓ |
| `path` | 请求路径 | ✓ | ✓ |
| `status_code` | HTTP 状态码 | ✓ | ✓ |
| `latency_ms` | 耗时毫秒 | ✓ | ✓ |
| `client_ip` | 客户端 IP | ✓ | ✓ |
| `user_id` | 已登录用户 ID | ✓ | - |
| `device_id` | 设备 ID | - | ✓ |
| `body_preview` | 请求体摘要（前 200 字符） | ✓ | - |
| `input_text` | 用户输入 | - | ✓ |
| `route_result` | 路由结果 | - | ✓ |
| `intent` | 意图 | - | ✓ |
| `intent_confidence` | 意图置信度 | - | ✓ |
| `response_preview` | 响应摘要（前 200 字符） | 可选 | ✓ |

### 3.2 错误日志（error.txt，可读文本）

**格式示例**：

```
2026-03-10 14:35:22.456 [ERROR] [req=def-456] POST /api/v1/dialog/chat 500 120ms ip=10.0.0.1 device=device-001
  input: 帮我加热两分钟
  error_type: HTTPException
  error_message: 无已发布的对话方案版本
  traceback:
Traceback (most recent call last):
  File "...", line 123, in ...
    ...
HTTPException: 503 无已发布的对话方案版本
---
```

**必须包含**：

| 字段 | 说明 |
|------|------|
| `ts` | 时间戳 |
| `level` | ERROR |
| `request_id` | 请求追踪 ID |
| `method` `path` `status_code` `latency_ms` | 请求上下文 |
| `client_ip` / `user_id` / `device_id` | 按类型选择 |
| `error_type` | 异常类名 |
| `error_message` | 异常消息 |
| `traceback` | 完整堆栈 `traceback.format_exc()` |
| `detail` | HTTP 异常的 detail 字段（若有） |
| `input_text` | 开放 API 的用户输入 |

---

## 四、实现方案

### 4.1 技术选型

- **Python 标准库**：`logging` + 自定义 Handler
- **按天文件夹**：启动时或首次写入时创建 `logs/{type}_{date}/`，无 `TimedRotatingFileHandler`（因需文件夹而非单文件滚动）
- **单文件大小限制**：`RotatingFileHandler`，`maxBytes=2*1024*1024`，超 2MB 滚动为 `app.1.txt`、`app.2.txt` 等
- **双文件**：同一 logger 绑定两个 Handler，分别对应 `app.txt` 与 `error.txt`（通过 Filter 或不同 level）

### 4.2 文件与 Handler 策略

- **backend**：`logging.getLogger("app.backend")`
  - Handler 1：`app.txt`，level=INFO，格式为可读文本
  - Handler 2：`error.txt`，level=ERROR，格式为可读文本（含 traceback）
- **api**：`logging.getLogger("app.api")`
  - Handler 1：`app.txt`，level=INFO
  - Handler 2：`error.txt`，level=ERROR
- **路径解析**：根据 `request.url.path` 是否以 `/api/v1/dialog` 前缀判断写 backend 或 api

### 4.3 架构示意

```
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI 应用                                   │
├─────────────────────────────────────────────────────────────────┤
│  LoggingMiddleware（outermost）                                    │
│    - 生成 request_id，写入 request.state                          │
│    - 记录请求开始                                                 │
│    - 请求结束后：根据 path 选择 backend 或 api logger               │
│    - 写 app.txt（INFO）；若异常则同时写 error.txt（ERROR）          │
├─────────────────────────────────────────────────────────────────┤
│  Exception Handlers（增强）                                        │
│    - 捕获异常后调用 log_error()，写入 traceback 到 error.txt        │
├─────────────────────────────────────────────────────────────────┤
│  app/core/logging_config.py                                       │
│    - 日初或首次写入时创建 logs/backend_YYYY-MM-DD/、logs/api_YYYY-MM-DD/ │
│    - 配置 backend / api 两个 Logger，各 2 个 FileHandler            │
└─────────────────────────────────────────────────────────────────┘
```

### 4.4 开放 API 与告警集成

**要求**：开放 API 错误需接入告警。

**实现**：
1. **RequestLog**：开放 API 每次请求（含错误）已写入 `RequestLog`，`extra.is_error=true` 标识异常
2. **metrics.error_rate**：`get_dashboard_metrics` 需从 `RequestLog.extra->>'is_error'='true'` 或等价条件统计错误率（当前若用 `domain='error'` 则需调整为 extra）
3. **check_alerts**：定时任务（如每分钟）或后台 worker 调用 `check_alerts(db)`，根据 error_rate、p95_latency 等触发 AlertRule
4. **日志侧**：开放 API 发生 ERROR 时，除写入 `api_yyyy-mm-dd/error.txt` 外，确保对应请求已写入 RequestLog（is_error=true），以便 metrics 与告警正确统计

**可选增强**：在写入 api error.txt 时，异步触发一次 `check_alerts`，实现准实时告警（需评估性能）。

---

## 五、配置项（.env / config）

| 配置 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `LOG_DIR` | path | `backend/logs` | 日志根目录 |
| `LOG_LEVEL_BACKEND` | string | `INFO` | 后台日志级别 |
| `LOG_LEVEL_API` | string | `INFO` | 开放 API 日志级别 |
| `LOG_RETENTION_DAYS` | int | `30` | 保留天数（过期文件夹可定时清理） |
| `LOG_MAX_BYTES` | int | `2097152` (2MB) | 单文件最大字节，超过则滚动新建 |

---

## 六、实施步骤

1. ~~**Phase 1**~~：`logging_config.py` 实现 ✅
   - 按日期创建 `logs/{type}_{date}/` 目录
   - 配置 backend、api 两套 Logger，各 app.txt + error.txt
   - AppFormatter（单行无 traceback）/ ErrorFormatter（含 traceback）
2. ~~**Phase 2**~~：LoggingMiddleware ✅
   - 生成 request_id，按 path 分流到对应 logger
   - 记录请求/响应/耗时到 app.txt
   - 异常时写 error.txt（含 exc_info）
3. ~~**Phase 3**~~：Exception Handler ✅
   - 异常在 Middleware 中捕获并记录，含完整 traceback
4. ~~**Phase 4**~~：开放 API 告警集成 ✅
   - metrics.error_rate 支持 `extra->>'is_error'='true'`
   - device 路由注入 device_id 到 request.state
5. **Phase 5**（可选）：各模块 request_id 透传（业务日志串联）

---

## 七、与现有组件关系

| 组件 | 关系 |
|------|------|
| **RequestLog 表** | 开放 API 请求的结构化数据，供监控仪表盘、设备历史、error_rate 统计 |
| **api_*/app.txt、error.txt** | 开放 API 的全文日志，含完整 traceback，用于人工排查 |
| **AlertRule** | 基于 metrics（含 error_rate）触发，需确保开放 API 错误正确计入 |
| **后台日志** | 不参与告警，仅用于运维排查 |
