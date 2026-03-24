# SmartChef v2 — 智能对话管理平台

## 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| **后端** | Python, FastAPI, SQLAlchemy (async), Pydantic v2, Alembic | Python 3.11+ |
| **前端** | React, Ant Design 5, Vite, Zustand | React 18 / Node 18+ |
| **数据库** | PostgreSQL (asyncpg), pgvector | 16 |
| **缓存** | Redis | 7.x |
| **部署** | Docker, Docker Compose, nginx | - |

---

## 前置条件

| 工具 | 用途 | 安装 |
|------|------|------|
| **Python 3.11+** | 后端运行时 | https://python.org |
| **uv** | Python 包管理器 | `pip install uv` 或 `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| **Node.js 18+** | 前端运行时 | https://nodejs.org |
| **PostgreSQL 16** | 关系数据库 | 本地安装或 Docker |
| **Redis 7** | 缓存/会话 | 本地安装或 Docker |
| **Docker** (可选) | 容器化部署 | https://docker.com |

---

## 快速启动

### 方式一：本地开发（推荐）

#### 1. 启动基础设施

如果本地已安装 PostgreSQL 和 Redis，确保它们已启动。否则用 Docker 启动：

```bash
cd smartchef-v2
docker compose up postgres redis -d
```

#### 2. 创建数据库

```bash
# 连接 PostgreSQL 并创建数据库（如尚未创建）
psql -U postgres -c "CREATE DATABASE smartchef_v2;" 2>/dev/null || true
```

#### 3. 启动后端

```bash
cd smartchef-v2/backend

# 安装依赖
uv sync

# 运行数据库迁移
uv run alembic upgrade head

# 初始化种子数据（管理员账号、角色、权限）
uv run python -m app.scripts.init_db

# 启动开发服务器
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

后端启动后可访问：
- API 根路径: http://localhost:8001
- Swagger 文档: http://localhost:8001/docs
- ReDoc 文档: http://localhost:8001/redoc

#### 4. 启动前端

```bash
cd smartchef-v2/frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端启动后可访问: http://localhost:5173

#### 5. 登录

使用种子管理员账号登录：
- 用户名: `admin`
- 密码: `admin123456`

---

### 方式二：Docker Compose（一键启动）

```bash
cd smartchef-v2

# 确保 backend/uv.lock 存在
cd backend && uv lock && cd ..

# 启动全部服务
docker compose up --build
```

服务地址：
| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:80 |
| 后端 API | http://localhost:8001 |
| API 文档 | http://localhost:8001/docs |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

> Docker 启动后仍需手动执行迁移和种子数据（首次）：
> ```bash
> docker compose exec backend uv run alembic upgrade head
> docker compose exec backend uv run python -m app.scripts.init_db
> ```

---

## 环境变量

在 `backend/.env` 中配置（已提供开发默认值）：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | PostgreSQL 连接串 | `postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/smartchef_v2` |
| `REDIS_URL` | Redis 连接串 | `redis://127.0.0.1:6379/1` |
| `SECRET_KEY` | JWT 签名密钥 | 开发默认值（**生产环境必须修改**） |
| `ADMIN_USERNAME` | 种子管理员用户名 | `admin` |
| `ADMIN_PASSWORD` | 种子管理员密码 | `admin123456` |
| `DEBUG` | 调试模式（启用 API 文档） | `true` |
| `DEVICE_API_KEY` | 设备端对话接口 API Key（空=不校验） | 空 |
| `ZENMUX_API_KEY` / `ZENMUX_BASE_URL` | LLM 合成相似问（训练集） | 见 `app.core.config` |
| `HF_HOME` | Hugging Face 缓存根目录（留空则 `backend/data/hf_cache`） | 空 |
| `HF_LOCAL_FILES_ONLY` | `true` 时训练/推理加载预训练**仅读本地**（缓存或本机目录），**不发起 Hub 下载**；内网/离线请先 prefetch 或拷贝缓存后再开 | `false` |

**训练集「LLM 合成相似问」**：前端默认走异步任务（`POST .../generate-training/jobs` 返回 `202` + `job_id`，再每 **6s** 轮询 `GET .../generate-training/jobs/{job_id}`）；后台由 **`asyncio.create_task`** 执行（避免直接 `return JSONResponse` 时 `BackgroundTasks` 未挂载导致任务永远不跑、状态一直 `queued`）。任务状态存 **Redis**，需本地 Redis 可用。仍保留同步接口 `POST .../generate-training`（长耗时易超时，仅供调试）。

**意图模型训练进度**：`POST /models/{id}/train` 后，`progress` 在准备阶段为 **0–5%**（读库、分词等），进入 PyTorch 线程后为 **10%**；**加载 BERT 整模与跑完第 1 个 epoch 之前**进度可能长时间停在 **10–19%**（CPU 上更慢），控制台 **epoch 日志只在每个 epoch 结束后**打印。若本地 `HF_HOME` 下**已有** Hub 缓存，则**不会**再联网拉取。

**停止训练 / 删除版本**：`POST /api/v1/models/{id}/cancel-training` 将训练中任务标记为失败，后台在 **epoch 边界**退出；`DELETE /api/v1/models/{id}` 可删除草稿/失败/已归档/训练中记录（已训练未归档的请先归档）。指令库详情页「模型版本」表操作列提供 **停止训练**、**删除**。

**离线 / 预置预训练模型（推荐内网）**：

1. **方式 A：只填 Hub 名，但文件只存在本机**  
   在可联网机器执行一次 `python -m app.scripts.prefetch_hf_cache`（或 `--migrate-user-cache`），把整个 `backend/data/hf_cache` 拷到内网；内网 `.env` 设 `HF_LOCAL_FILES_ONLY=true`（或 `HF_HUB_OFFLINE=1`）。  
   此时 `bert-base-chinese` 仍从**缓存**读取，**不访问外网**。

2. **方式 B：你手上有完整模型目录**（含 `config.json`、tokenizer、`pytorch_model.bin` 或 `model.safetensors` 等）  
   放到 `backend/data/models/pretrained/<任意文件夹名>/`，训练配置里「基础模型」填 **`<文件夹名>`**（或填绝对路径）。后端会识别为本地目录并 `local_files_only=True`。

3. **不要把**数 GB 权重提交进 git；`data/hf_cache/` 已在 `.gitignore`。

---

## 运行测试

### 后端测试

```bash
cd backend

# 运行全部测试
uv run pytest tests/ -v

# 分层运行
uv run pytest tests/unit/          # 单元测试（84 个，无需数据库）
uv run pytest tests/contract/      # 契约测试（68 个，无需数据库）
uv run pytest tests/integration/   # 集成测试（17 个，需要 PG + Redis）

# 带覆盖率
uv run pytest tests/ --cov=app --cov-report=term-missing
```

### 前端 E2E 测试

```bash
cd frontend

# 安装 Playwright 浏览器（首次）
npx playwright install chromium

# 运行 E2E 测试（会自动启动 dev server）
npm run test:e2e
```

### 代码质量

```bash
# 后端 lint
cd backend && uv run ruff check app/

# 前端 lint + format
cd frontend && npm run lint && npm run format
```

---

## 项目结构

```
smartchef-v2/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API 路由层（auth, users, roles, intents, ...）
│   │   ├── core/            # 基础设施（config, database, redis, security, ...）
│   │   ├── models/          # SQLAlchemy ORM 模型
│   │   ├── schemas/         # Pydantic 请求/响应模型
│   │   ├── services/        # 业务逻辑层
│   │   │   ├── knowledge/   # 知识库服务
│   │   │   ├── nlu/         # NLU 管道（pipeline, router, dialog_manager）
│   │   │   ├── testing/     # 批量测试服务
│   │   │   └── version/     # 版本管理
│   │   ├── scripts/         # 数据库初始化脚本
│   │   └── main.py          # FastAPI 应用入口
│   ├── migrations/          # Alembic 数据库迁移
│   ├── tests/
│   │   ├── unit/            # 单元测试（mock 数据库）
│   │   ├── contract/        # API 契约测试（mock 服务层）
│   │   └── integration/     # 集成测试（真实数据库）
│   ├── pyproject.toml       # Python 项目配置
│   ├── alembic.ini          # Alembic 配置
│   ├── Dockerfile
│   └── .env                 # 环境变量（开发用）
├── frontend/
│   ├── src/
│   │   ├── components/      # 通用组件（Layout, ProtectedRoute, ErrorBoundary）
│   │   ├── pages/           # 页面组件
│   │   ├── stores/          # Zustand 状态管理
│   │   ├── services/        # API 客户端
│   │   ├── App.jsx          # 路由配置
│   │   ├── main.jsx         # 应用入口
│   │   └── global.css       # 全局样式 + Ant Design 主题覆盖
│   ├── tests/e2e/           # Playwright E2E 测试
│   ├── package.json
│   ├── vite.config.js
│   ├── playwright.config.js
│   └── Dockerfile
└── docker-compose.yml       # 多服务编排
```

---

## 功能模块

| 模块 | 说明 | 后端 API | 前端页面 |
|------|------|----------|----------|
| **认证** | JWT 登录/登出/刷新, RBAC 权限 | `/api/v1/auth/*` | `/login` |
| **指令库管理** | NLU 意图库 CRUD、模型版本、数据集 | `/api/v1/intent-libraries/*` | `/intent-library` |
| **知识库** | 文档上传、分类管理、语义检索 | `/api/v1/knowledge/*` | `/knowledge-base` |
| **对话方案** | 方案配置、人设管理、发布版本 | `/api/v1/profiles/*` | `/dialog-profile` |
| **批量测试** | 测试用例管理、批量执行、结果分析 | `/api/v1/batch-tests/*` | `/batch-test` |
| **监控** | 仪表盘指标、设备日志、告警规则 | `/api/v1/monitoring/*` | `/monitoring` |
| **用户管理** | 用户/角色/权限 CRUD | `/api/v1/users/*`, `/api/v1/roles/*` | `/user-manager` |
| **手动测试** | 对话测试会话 | `/api/v1/test-sessions/*` | `/test-chat` |

---

## 常见问题

### Q: 后端启动报 `RuntimeError: SECRET_KEY must be set`
A: 需要在 `.env` 中设置 `DEBUG=true`（开发环境），或设置一个强随机 `SECRET_KEY`（生产环境）。

### Q: 数据库迁移报错
A: 确认 PostgreSQL 已启动且 `smartchef_v2` 数据库已创建。检查 `.env` 中 `DATABASE_URL` 是否正确。

### Q: 前端 API 请求 404
A: 确认后端已在 `8001` 端口启动。Vite 开发服务器会将 `/api` 请求代理到 `http://localhost:8001`。

### Q: Docker 构建失败 `uv.lock not found`
A: 先在 `backend/` 目录执行 `uv lock` 生成 lock 文件。
