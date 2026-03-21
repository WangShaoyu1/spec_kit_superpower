# 快速启动指南: SmartChef 智能对话管理平台

## 前置条件

| 工具 | 版本 | 用途 |
|------|------|------|
| Python | 3.11+ | 后端服务、模型训练 |
| Node.js | 18+ | 前端构建 |
| Docker & Docker Compose | 24+ | 本地开发环境编排 |
| PostgreSQL | 16+ | 数据存储（Docker 提供） |
| Redis | 7+ | 会话缓存（Docker 提供） |
| Git | 2.40+ | 版本控制 |
| NVIDIA CUDA Toolkit | 12.x（可选） | GPU 加速模型训练 |

## 1. 克隆仓库

```bash
git clone <repo-url> smartchef-platform
cd smartchef-platform
```

## 2. 启动基础设施（Docker Compose）

```bash
docker-compose up -d postgres redis
```

等待服务就绪后检查状态：

```bash
docker-compose ps
```

PostgreSQL 默认端口 `5432`，Redis 默认端口 `6379`。

## 3. 后端环境搭建

```bash
cd backend

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 安装依赖
pip install -e ".[dev]"

# 复制环境配置
cp .env.example .env
# 编辑 .env 填入数据库连接、Redis 地址、LLM API Key 等
```

### 关键环境变量

```env
# 数据库
DATABASE_URL=postgresql+asyncpg://smartchef:smartchef@localhost:5432/smartchef

# Redis
REDIS_URL=redis://localhost:6379/0

# LLM（通过 ZenMux 统一网关调用，一个 Key 覆盖所有模型）
ZENMUX_API_KEY=your-zenmux-api-key
ZENMUX_BASE_URL=https://zenmux.ai/api/v1

# 联网搜索
BRAVE_SEARCH_API_KEY=your-brave-search-api-key

# 安全
SECRET_KEY=your-secret-key-here
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

> **说明**: ZenMux 是统一 LLM 网关，通过 OpenAI SDK 兼容接口调用 120+ 模型（GPT-5、Claude、千问、DeepSeek 等），对话方案中配置模型标识如 `openai/gpt-5`、`qwen/qwen3.5-plus` 即可切换。详见 [ZenMux 文档](https://zenmux.ai/docs/zh/guide/quickstart.html)。

### 初始化数据库

```bash
# 执行迁移
alembic upgrade head

# 初始化管理员账号和默认角色
python -m app.scripts.init_db
```

### 启动后端

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端 API 文档：http://localhost:8000/docs

## 4. 前端环境搭建

```bash
cd frontend

# 安装依赖
npm install

# 复制环境配置
cp .env.example .env.local
# 编辑 API 地址
# VITE_API_BASE_URL=http://localhost:8000/api/v1

# 启动开发服务器
npm run dev
```

前端访问：http://localhost:5173

## 5. 模型训练（首次）

```bash
cd backend

# 准备训练数据（从数据库导出意图和训练语料）
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

# 导出量化 ONNX（设备端推理，可选）
python -m scripts.export_onnx \
  --model models/joint_nlu/ \
  --output models/joint_nlu/model_int8.onnx \
  --quantize int8
```

## 6. 验证核心流程

### 6.1 后台管理

1. 浏览器打开 http://localhost:5173
2. 使用管理员账号登录
3. 创建意图（如"启动烹饪"）并添加训练数据
4. 上传菜谱文档到知识库
5. 创建对话方案，配置 LLM 和人设
6. 在手动测试页面验证对话效果

### 6.2 API 调用

```bash
# 获取当前版本
curl http://localhost:8000/v1/dialog/version

# 对话解析
curl -X POST http://localhost:8000/v1/dialog/parse \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "test_device_001",
    "text": "开始烹饪",
    "device_context": {
      "cooking_state": "idle",
      "door_closed": true,
      "current_temp": 25
    }
  }'

# 健康检查
curl http://localhost:8000/v1/health
```

## 7. 运行测试

```bash
# 后端单元测试
cd backend
pytest tests/unit/ -v

# 后端集成测试（需要数据库和 Redis）
pytest tests/integration/ -v

# 前端测试
cd frontend
npm run test
```

## 8. 常见问题

| 问题 | 解决方案 |
|------|---------|
| pgvector 扩展未安装 | `docker exec -it postgres psql -U smartchef -c "CREATE EXTENSION vector;"` |
| Redis 连接失败 | 检查 Docker 容器是否运行：`docker-compose ps` |
| LLM API 超时 | 检查 .env 中的 ZENMUX_API_KEY 和网络代理配置；ZenMux 端点 `https://zenmux.ai/api/v1` |
| 模型训练 OOM | 减小 batch_size 或使用 gradient accumulation |
| 前端 CORS 错误 | 确认后端 CORS 配置包含 `http://localhost:5173` |
