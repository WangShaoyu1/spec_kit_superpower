# 实施计划: SmartChef 智能对话管理平台

**分支**: `master` | **日期**: 2026-03-03 | **规范**: [spec.md](./spec.md)
**输入**: 来自 `/specs/master/spec.md` 的功能规范（澄清完毕，10 个用户故事，35 条 FR，12 条 SC）

## 摘要

为智能微波炉构建完全自研的对话管理平台，替换讯飞旧方案。包含两个交付物：

1. **后台管理系统**（Web）：PM 配置指令/知识库/人设、手动测试、批量测试、监控仪表盘、版本发布
2. **对话管理 API**（云端）：设备端 APP 调用，按设备 ID 隔离会话，统一路由（指令/知识/闲聊）

技术方案采用**小模型 + 大模型混合架构**：小模型（JointBERT 类）负责指令意图分类与槽位提取（< 200ms），大模型（可配置 LLM）负责知识问答与开放闲聊（2-4s）。小模型需导出为 ONNX/TensorRT 格式，支持在 Jetson Nano 上以 C++ 运行。

## 技术背景

**语言/版本**: Python 3.11+（后端服务、模型训练）、TypeScript 5.x（前端管理系统）、C++17（设备端小模型推理）
**主要依赖**:
- 后端 API: FastAPI + Uvicorn + Pydantic v2
- NLU 模型: PyTorch 2.x + Transformers（训练）、ONNX Runtime（推理加速）
- 知识检索: PostgreSQL + pgvector（复用主存储，万级向量规模足够，详见 research.md R1）
- 大模型: LiteLLM（统一多 LLM 调用接口，支持 GPT-4o/千问/DeepSeek 等可配置切换）
- 联网搜索: Tavily Search API（AI-native，LLM 友好，~1.9s 响应，详见 research.md R2）
- 前端: React 18 + Ant Design 5 + Vite
- 缓存/会话: Redis 7.x

**存储**:
- PostgreSQL 16（持久化：指令配置、知识库元数据、对话方案、版本记录、用户账号、请求日志）
- Redis 7.x（运行时：设备会话状态、对话上下文、缓存）
- 向量数据库: pgvector（PostgreSQL 扩展，与主库统一，详见 research.md R1）

**测试**:
- 后端: pytest + pytest-asyncio + httpx（单元/集成/E2E）
- 前端: Vitest + Playwright（组件/E2E）
- NLU 模型: 标准化评估脚本（F1-Score、混淆矩阵、延迟基准）

**目标平台**:
- 云端服务: Linux 服务器（Docker 容器化部署）
- 设备端小模型: NVIDIA Jetson Nano（Linux / C++17 / QT、1.1-1.5GB 可用内存）

**项目类型**: Web 应用程序（后端 API + 前端管理系统 + 模型训练工具链 + 设备端推理引擎）

**性能目标**:
- 指令类意图识别: < 200ms（P95）
- 知识问答/闲聊: 2-4s
- API 并发: 10 QPS，按设备 ID 隔离
- 意图识别准确率: ≥ 95%

**约束条件**:
- 小模型推理: < 1.5GB 内存，C++ 运行在 Jetson Nano
- 离线能力: V2 规划（V1 依赖在线 ASR）
- 会话超时: 可配置（默认 10 分钟）
- 单版本生产: 同一时间仅一个版本生效

**规模/范围**:
- 2-3 名 PM 使用后台
- ~39 个已定义意图（可扩展）
- ~1000 道菜谱文档
- 中英文双语支持

## 章程检查

*门控: 必须在阶段 0 研究前通过. 阶段 1 设计后重新检查.*

| # | 章程原则 | 状态 | 计划对齐说明 |
|---|---------|------|-------------|
| I | 意图优先架构 | ✅ 通过 | NLU Pipeline 严格分层：文本预处理 → 路由分类 → 意图分类 → 槽位提取 → 对话状态 → 响应生成；意图通过注册机制接入（PM 后台 CRUD）；低置信度触发澄清对话 |
| II | 领域驱动设计 | ✅ 通过 | 指令域 + 闲聊域（含知识子域）独立设计；用户偏好域标注 V2；领域间通过路由器统一调度，无直接依赖 |
| III | 测试驱动开发 | ✅ 通过 | pytest + Vitest + 模型评估脚本；F1 基线（指令 ≥ 0.95、闲聊 ≥ 0.85）；批量测试闭环 |
| IV | 数据管道完整性 | ✅ 通过 | 训练数据版本化；模型产物含元数据；对话方案版本发布机制；CI/CD 管道强制 |
| V | 对话体验一致性 | ✅ 通过 | Persona 人设配置；分层回复架构（确认 → 补充 → 引导）；渐进式错误处理；i18n 中英文 |
| VI | 可观测性与指标驱动 | ✅ 通过 | 完整监控仪表盘（FR-030~035）；结构化请求日志；按设备 ID 维度查看历史；告警规则可配置 |
| VII | 安全与隐私优先 | ✅ 通过 | RBAC 权限管理；高风险操作二次确认；数据加密存储；最小权限原则 |

**门控结论（阶段 0 前）**: 全部通过，无违规项。已进入阶段 0。

### 阶段 1 设计后重新检查

| # | 章程原则 | 状态 | 设计对齐验证 |
|---|---------|------|-------------|
| I | 意图优先架构 | ✅ 通过 | data-model: Intent/Slot/TrainingData 实体完整定义；API: `/dialog/parse` 返回 intent+slots 结构化结果；research: JointBERT 联合模型架构确认 |
| II | 领域驱动设计 | ✅ 通过 | 项目结构按 nlu/knowledge/chitchat/session 领域组织；API 路由三域分离；DialogProfile 可配置路由策略 |
| III | 测试驱动开发 | ✅ 通过 | data-model: TestSuite/TestCase/TestReport 完整建模；API: 批量测试+智能分析端点；quickstart 包含测试命令 |
| IV | 数据管道完整性 | ✅ 通过 | data-model: PublishedVersion 含完整快照+模型产物路径；TrainingData 含语言和标注信息；research: 模型导出 ONNX 流程 |
| V | 对话体验一致性 | ✅ 通过 | data-model: Persona 实体含 system_prompt；API: 响应格式统一三域；DeviceSession FSM 状态机完整 |
| VI | 可观测性与指标驱动 | ✅ 通过 | data-model: RequestLog 含完整链路字段+多维索引；AlertRule 告警规则；API: 监控仪表盘+设备日志端点 |
| VII | 安全与隐私优先 | ✅ 通过 | data-model: User/Role RBAC；API: JWT BearerAuth；password_hash 加密存储 |

**门控结论（阶段 1 后）**: 全部通过，设计制品与章程完全对齐。

## 项目结构

### 文档(此功能)

```
specs/master/
├── plan.md              # 此文件
├── research.md          # 阶段 0 输出
├── data-model.md        # 阶段 1 输出
├── quickstart.md        # 阶段 1 输出
├── contracts/           # 阶段 1 输出（OpenAPI 定义）
└── tasks.md             # 阶段 2 输出（/speckit.tasks）
```

### 源代码(仓库根目录)

```
smartchef-platform/
├── backend/                          # Python 后端服务
│   ├── app/
│   │   ├── api/                      # FastAPI 路由层
│   │   │   ├── v1/
│   │   │   │   ├── dialog.py         # 对话管理 API（设备端调用）
│   │   │   │   ├── intents.py        # 意图配置 CRUD
│   │   │   │   ├── knowledge.py      # 知识库管理
│   │   │   │   ├── profiles.py       # 对话方案管理
│   │   │   │   ├── testing.py        # 手动/批量测试
│   │   │   │   ├── monitoring.py     # 监控与日志查询
│   │   │   │   ├── versions.py       # 版本发布
│   │   │   │   └── auth.py           # 认证与权限
│   │   │   └── deps.py               # 依赖注入
│   │   ├── core/                     # 核心配置
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── database.py
│   │   ├── models/                   # SQLAlchemy ORM 模型
│   │   ├── schemas/                  # Pydantic 请求/响应模型
│   │   ├── services/                 # 业务逻辑层
│   │   │   ├── nlu/                  # NLU Pipeline
│   │   │   │   ├── pipeline.py       # 主管道调度
│   │   │   │   ├── router.py         # 域路由（指令/知识/闲聊）
│   │   │   │   ├── intent_classifier.py
│   │   │   │   ├── slot_extractor.py
│   │   │   │   ├── dialog_manager.py # 对话状态管理
│   │   │   │   ├── reference_resolver.py # 指代消解
│   │   │   │   └── preprocessor.py   # 文本预处理 + 语言检测
│   │   │   ├── knowledge/            # 知识域
│   │   │   │   ├── indexer.py        # 文档解析与向量索引
│   │   │   │   ├── retriever.py      # 检索匹配
│   │   │   │   └── qa_generator.py   # 知识问答生成
│   │   │   ├── chitchat/             # 闲聊域
│   │   │   │   ├── persona.py        # 人设管理
│   │   │   │   ├── llm_adapter.py    # 大模型统一接口
│   │   │   │   └── web_search.py     # 联网内容查询
│   │   │   ├── session/              # 会话管理
│   │   │   │   ├── device_session.py # 设备会话（Redis）
│   │   │   │   └── context.py        # 上下文维护
│   │   │   ├── version/              # 版本发布
│   │   │   ├── testing/              # 测试引擎
│   │   │   │   ├── manual_test.py    # 手动单条测试
│   │   │   │   ├── batch_test.py     # 批量测试执行
│   │   │   │   ├── case_generator.py # 测试用例自动生成
│   │   │   │   └── analyzer.py       # 智能分析报告
│   │   │   └── monitoring/           # 监控与告警
│   │   │       ├── metrics.py        # 指标采集与聚合
│   │   │       ├── log_query.py      # 日志查询服务
│   │   │       └── alerting.py       # 告警引擎
│   │   └── utils/
│   ├── migrations/                   # Alembic 数据库迁移
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── e2e/
│   ├── scripts/                      # 模型训练与评估脚本
│   │   ├── train_intent_model.py
│   │   ├── train_slot_model.py
│   │   ├── evaluate_model.py
│   │   ├── export_onnx.py           # 导出 ONNX 格式
│   │   └── translate_training_data.py # 中→英训练数据翻译
│   ├── pyproject.toml
│   └── Dockerfile
│
├── frontend/                         # React 管理系统前端
│   ├── src/
│   │   ├── components/               # 通用组件
│   │   ├── pages/
│   │   │   ├── IntentManager/        # 意图配置管理
│   │   │   ├── KnowledgeBase/        # 知识库管理
│   │   │   ├── DialogProfile/        # 对话方案管理
│   │   │   ├── ManualTest/           # 手动测试（聊天+调试面板）
│   │   │   ├── BatchTest/            # 批量测试与分析报告
│   │   │   ├── Monitoring/           # 监控仪表盘与设备日志
│   │   │   ├── VersionManager/       # 版本发布管理
│   │   │   └── UserManager/          # 用户与权限管理
│   │   ├── services/                 # API 调用层
│   │   ├── stores/                   # 状态管理
│   │   └── utils/
│   ├── tests/
│   ├── package.json
│   └── Dockerfile
│
├── device-inference/                 # 设备端 C++ 推理引擎（可选交付）
│   ├── src/
│   │   ├── onnx_runtime.cpp         # ONNX Runtime C++ 推理
│   │   ├── intent_classifier.cpp
│   │   ├── slot_extractor.cpp
│   │   └── tokenizer.cpp            # 文本分词器
│   ├── include/
│   ├── CMakeLists.txt
│   └── tests/
│
├── docker-compose.yml               # 本地开发环境编排
├── docker-compose.prod.yml          # 生产部署编排
└── README.md
```

**结构决策**: 采用 Web 应用程序结构（后端 + 前端分离），额外增加 device-inference 模块用于设备端小模型推理。后端采用分层架构（API → Services → Models），NLU 服务按领域驱动设计组织（nlu/knowledge/chitchat/session）。

## 复杂度跟踪

*无章程违规，无需额外复杂度证明。*
