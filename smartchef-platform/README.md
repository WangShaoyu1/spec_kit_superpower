# SmartChef 智能对话管理平台

> 为智能微波炉构建的完全自研对话管理平台，替换讯飞旧方案。采用小模型 + 大模型混合架构，支持指令识别、知识问答、开放闲聊三域统一路由。

## 项目概述

SmartChef 智能对话管理平台包含两个核心交付物：

1. **后台管理系统**（Web）— 供产品经理配置指令、知识库、闲聊人设，进行手动/批量测试和版本发布
2. **对话管理 API**（云端服务）— 供智能微波炉设备端 APP 直连调用，按设备 ID 隔离会话

系统接收上游 ASR 模块输出的文本，执行语义理解与对话管理，输出结构化指令和回复文本。

### 核心能力

- **指令识别**：小模型（JointBERT）意图分类 + 槽位提取，延迟 < 200ms（P95）
- **知识问答**：基于 pgvector 向量检索，命中知识库条目后生成回答
- **开放闲聊**：大模型生成回复，支持联网搜索（天气、新闻等）
- **多轮对话**：指代消解、省略恢复、跨域切换
- **中英双语**：自动检测语言，对应语言回复
- **版本管理**：对话方案打包发布，单版本生效，发布即时切换

## 系统架构

```mermaid
graph TB
    subgraph 设备端
        Device[智能微波炉<br/>Jetson Nano]
        ASR[ASR 语音识别]
    end

    subgraph 前端管理系统
        FE[React 18 + Ant Design 5<br/>Vite 构建]
    end

    subgraph 后端 API 服务
        Gateway[FastAPI Gateway<br/>认证 / 限流 / 输入校验]

        subgraph NLU Pipeline
            Preprocessor[文本预处理<br/>语言检测]
            Router[域路由器<br/>指令/知识/闲聊]
            IC[意图分类器<br/>ONNX Runtime]
            SE[槽位提取器]
            DM[对话状态管理<br/>多轮 / 指代消解]
            RB[响应构建器]
        end

        subgraph 业务服务
            KnowledgeSvc[知识检索<br/>pgvector]
            ChitchatSvc[闲聊服务<br/>ZenMux LLM]
            WebSearch[联网搜索<br/>Brave Search]
            TestingSvc[测试引擎<br/>手动 / 批量]
            MonitorSvc[监控告警]
            VersionSvc[版本发布]
        end
    end

    subgraph 数据层
        PG[(PostgreSQL 16<br/>+ pgvector)]
        Redis[(Redis 7<br/>会话缓存)]
    end

    Device -->|文本 + 设备上下文| Gateway
    ASR -->|转写文本| Device
    FE -->|管理 API| Gateway
    Gateway --> Preprocessor
    Preprocessor --> Router
    Router -->|指令域| IC
    IC --> SE --> DM --> RB
    Router -->|知识域| KnowledgeSvc
    Router -->|闲聊域| ChitchatSvc
    ChitchatSvc --> WebSearch
    KnowledgeSvc --> PG
    DM --> Redis
    Gateway --> PG
```

## 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| **后端框架** | FastAPI + Uvicorn + Pydantic v2 | FastAPI ≥ 0.115 |
| **前端框架** | React + Ant Design + Vite | React 18, AntD 5, Vite 6 |
| **NLU 模型** | PyTorch + Transformers（训练）/ ONNX Runtime（推理） | PyTorch 2.x |
| **大模型网关** | ZenMux（OpenAI 兼容接口，120+ 模型） | — |
| **联网搜索** | Brave Search API | — |
| **向量检索** | PostgreSQL + pgvector | PG 16, pgvector 0.3+ |
| **数据库** | PostgreSQL（持久化） | 16+ |
| **缓存** | Redis（会话状态、对话上下文） | 7+ |
| **ORM** | SQLAlchemy（async） | 2.0+ |
| **数据库迁移** | Alembic | 1.14+ |
| **状态管理** | Zustand | 5.0+ |
| **包管理** | pip + pyproject.toml / npm | — |
| **测试** | pytest + pytest-asyncio / Vitest | — |

## 快速启动

### 环境要求

| 工具 | 版本 | 用途 |
|------|------|------|
| Python | 3.11+ | 后端服务、模型训练 |
| Node.js | 18+ | 前端构建 |
| PostgreSQL | 16+ | 数据存储 |
| Redis | 7+ | 会话缓存 |
| Git | 2.40+ | 版本控制 |

### 1. 启动基础设施

使用项目自带的服务管理脚本启动 PostgreSQL 和 Redis：

```bash
python scripts/manage_services.py start
```

> 也可以使用 Docker Compose（如已配置）：`docker-compose up -d postgres redis`

### 2. 后端环境搭建

```bash
cd backend

# 创建虚拟环境
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / Mac
source .venv/bin/activate

# 安装依赖
pip install -e ".[dev]"

# 复制环境配置并编辑
cp .env.example .env
```

编辑 `.env` 文件，填入关键配置：

```env
DATABASE_URL=postgresql+asyncpg://smartchef:smartchef@localhost:5432/smartchef
REDIS_URL=redis://localhost:6379/0
ZENMUX_API_KEY=your-zenmux-api-key
ZENMUX_BASE_URL=https://zenmux.ai/api/v1
BRAVE_SEARCH_API_KEY=your-brave-search-api-key
SECRET_KEY=your-secret-key-here
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123456
```

> **ZenMux** 是统一 LLM 网关，通过 OpenAI SDK 兼容接口调用 120+ 模型（GPT-5、Claude、千问、DeepSeek 等），对话方案中配置模型标识如 `openai/gpt-5`、`qwen/qwen3.5-plus` 即可切换。

### 3. 初始化数据库

```bash
# 执行迁移
alembic upgrade head

# 初始化管理员账号和默认角色
python -m app.scripts.init_db
```

### 4. 启动后端服务

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

验证后端启动成功：

```bash
curl http://localhost:8000/api/v1/health
```

### 5. 前端环境搭建

```bash
cd frontend

# 安装依赖
npm install

# 复制环境配置
cp .env.example .env.local
# 编辑 VITE_API_BASE_URL=http://localhost:8000/api/v1

# 启动开发服务器
npm run dev
```

前端访问：http://localhost:5173

## API 文档

后端启动后，可通过以下地址访问自动生成的 API 文档：

| 文档类型 | 地址 |
|---------|------|
| **Swagger UI**（交互式） | http://localhost:8000/docs |
| **ReDoc**（阅读式） | http://localhost:8000/redoc |

### 核心 API 端点

| 模块 | 前缀 | 说明 |
|------|------|------|
| 认证 | `/api/v1/auth` | 登录、用户管理、角色权限 |
| 意图配置 | `/api/v1/intents` | 意图 CRUD、槽位管理、训练数据 |
| 知识库 | `/api/v1/knowledge` | 知识库管理、文档上传、搜索 |
| 对话方案 | `/api/v1/profiles` | 方案配置、人设管理 |
| 手动测试 | `/api/v1/test` | 测试会话、聊天调试 |
| 批量测试 | `/api/v1/batch-test` | 用例管理、批量执行、分析报告 |
| 版本发布 | `/api/v1/versions` | 版本发布、激活 |
| 设备端 API | `/api/v1/dialog` | 对话解析、会话管理、版本查询 |
| 监控 | `/api/v1/monitoring` | 仪表盘指标、日志查询、告警规则 |
| 用户管理 | `/api/v1/users` | 用户列表、权限分配 |
| 健康检查 | `/api/v1/health` | PostgreSQL / Redis 连接状态 |

## 项目结构

```
smartchef-platform/
├── backend/                          # Python 后端服务
│   ├── app/
│   │   ├── api/v1/                   # FastAPI 路由层
│   │   │   ├── auth.py               # 认证与权限
│   │   │   ├── intents.py            # 意图配置 CRUD
│   │   │   ├── knowledge.py          # 知识库管理
│   │   │   ├── profiles.py           # 对话方案管理
│   │   │   ├── device.py             # 设备端对话 API
│   │   │   ├── test.py               # 手动测试
│   │   │   ├── batch_test.py         # 批量测试
│   │   │   ├── versions.py           # 版本发布
│   │   │   ├── monitoring.py         # 监控与日志
│   │   │   └── health.py             # 健康检查
│   │   ├── core/                     # 核心配置（数据库、Redis、安全）
│   │   ├── models/                   # SQLAlchemy ORM 模型
│   │   ├── schemas/                  # Pydantic 请求/响应模型
│   │   └── services/                 # 业务逻辑层
│   │       ├── nlu/                  # NLU Pipeline（路由、意图、槽位、对话管理）
│   │       ├── knowledge/            # 知识检索与问答
│   │       ├── chitchat/             # 闲聊 + 联网搜索
│   │       ├── session/              # 设备会话管理（Redis）
│   │       ├── testing/              # 测试引擎（手动/批量/智能分析）
│   │       ├── monitoring/           # 监控指标、日志查询、告警
│   │       └── version/              # 版本发布
│   ├── migrations/                   # Alembic 数据库迁移
│   ├── scripts/                      # 模型训练与评估脚本
│   ├── tests/                        # 测试用例（unit / integration / contract）
│   └── pyproject.toml                # 后端依赖与工具配置
│
├── frontend/                         # React 管理系统前端（JavaScript）
│   ├── src/
│   │   ├── components/               # 通用组件
│   │   ├── pages/                    # 页面（意图/知识库/方案/测试/监控/版本/用户）
│   │   ├── services/                 # API 调用层
│   │   ├── stores/                   # Zustand 状态管理
│   │   └── utils/                    # 工具函数
│   └── package.json
│
├── scripts/
│   ├── manage_services.py            # PostgreSQL + Redis 启停脚本
│   └── quickstart_verify.py          # 端到端验证脚本
│
└── README.md
```

## 开发指南

### 运行测试

```bash
# 后端单元测试
cd backend
pytest tests/unit/ -v

# 后端集成测试（需要数据库和 Redis）
pytest tests/integration/ -v

# 后端合约测试
pytest tests/contract/ -v

# 前端测试
cd frontend
npm run test
```

### 模型训练（首次）

```bash
cd backend

# 导出训练数据
python -m scripts.export_training_data --output data/training/

# 训练意图分类 + 槽位提取联合模型
python -m scripts.train_intent_model \
  --data data/training/ \
  --base-model hfl/chinese-roberta-wwm-ext \
  --output models/joint_nlu/ \
  --epochs 10

# 评估模型
python -m scripts.evaluate_model \
  --model models/joint_nlu/ \
  --test-data data/training/test.json

# 导出 ONNX（云端推理）
python -m scripts.export_onnx \
  --model models/joint_nlu/ \
  --output models/joint_nlu/model.onnx
```

### 代码规范

- 后端使用 [Ruff](https://docs.astral.sh/ruff/) 进行 lint 和格式化（配置见 `pyproject.toml`）
- 前端使用 ESLint + Prettier
- 代码注释使用中文

### 端到端验证

使用验证脚本快速检查核心流程是否通畅：

```bash
cd smartchef-platform
python scripts/quickstart_verify.py
```

该脚本会依次执行：健康检查 → 登录 → 创建意图 → 创建知识库 → 创建对话方案 → 发布版本 → 测试对话 API。

## 常见问题

| 问题 | 解决方案 |
|------|---------|
| pgvector 扩展未安装 | `psql -U smartchef -c "CREATE EXTENSION vector;"` |
| Redis 连接失败 | 检查 Redis 是否运行：`python scripts/manage_services.py start` |
| LLM API 超时 | 检查 `.env` 中的 `ZENMUX_API_KEY` 和网络配置 |
| 前端 CORS 错误 | 确认后端 CORS 配置包含 `http://localhost:5173` |
| 模型训练 OOM | 减小 batch_size 或使用 gradient accumulation |

## 许可证

本项目为内部项目，仅限公司内部使用。
