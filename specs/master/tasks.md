# 任务: SmartChef 智能对话管理平台

**输入**: 来自 `/specs/master/` 的设计文档（plan.md、spec.md、data-model.md、contracts/、research.md、quickstart.md）
**前置条件**: 所有阶段 0/1 制品已就绪
**本地环境**: Windows，PostgreSQL + Redis + pgvector 已安装（`python scripts/manage_services.py start` 启动服务）
**前端技术栈**: React + JavaScript（不使用 TypeScript），Vite + Ant Design + Zustand

**测试**: 章程要求 TDD（不可协商），每个用户故事包含测试任务。

**组织结构**: 任务按用户故事分组，10 个用户故事按优先级排序（P1×5 → P2×4 → P3×1）。

## 格式: `[ID] [P] [Story] 描述`
- **[P]**: 可以并行运行（不同文件，无依赖关系）
- **[Story]**: 此任务属于哪个用户故事（US1-US10）
- 描述中包含确切的文件路径

---

## 阶段 1: 设置（共享基础设施）

**目的**: 项目初始化、依赖安装、基本目录结构

- [ ] T001 按照 plan.md 项目结构创建 `smartchef-platform/` 目录骨架（backend/、frontend/、device-inference/[可选，V1 不实现]）
- [ ] T002 初始化 Python 后端项目：创建 `backend/pyproject.toml`，声明依赖（fastapi、uvicorn、pydantic、sqlalchemy[asyncio]、asyncpg、redis、transformers、onnxruntime、openai、httpx、alembic、python-jose、passlib、bcrypt）
- [ ] T003 [P] 初始化前端项目：在 `frontend/` 运行 `npm create vite@latest`（React + JavaScript），安装 antd、axios、zustand、react-router-dom
- [ ] T004 [P] 将 `temp_data/manage_services.py` 复制到项目根目录 `scripts/manage_services.py`，用于本地启动/停止 PostgreSQL + Redis（`python scripts/manage_services.py start`）
- [ ] T005 [P] 创建 `backend/.env.example`，包含 DATABASE_URL、REDIS_URL、ZENMUX_API_KEY、ZENMUX_BASE_URL、BRAVE_SEARCH_API_KEY、SECRET_KEY、ADMIN_USERNAME、ADMIN_PASSWORD
- [ ] T006 [P] 配置后端代码检查：创建 `backend/pyproject.toml` 中的 ruff + mypy 配置
- [ ] T007 [P] 配置前端代码检查：`frontend/.eslintrc.cjs` + `prettier.config.js`

---

## 阶段 2: 基础（阻塞前置条件）

**目的**: 在任何用户故事开始前必须完成的核心基础设施

**⚠️ 关键**: 在此阶段完成之前，无法开始任何用户故事工作

- [ ] T008 创建 FastAPI 应用入口 `backend/app/main.py`：CORS 配置、路由注册、启动事件
- [ ] T009 创建核心配置模块 `backend/app/core/config.py`：Pydantic Settings，从 .env 加载所有配置项
- [ ] T010 [P] 创建数据库连接模块 `backend/app/core/database.py`：AsyncSession、SQLAlchemy async engine、pgvector 扩展初始化
- [ ] T011 [P] 创建 Redis 连接模块 `backend/app/core/redis.py`：aioredis 连接池、会话操作封装
- [ ] T012 [P] 创建安全模块 `backend/app/core/security.py`：JWT 生成/验证、密码哈希（bcrypt）、权限检查装饰器
- [ ] T013 初始化 Alembic 迁移框架：`backend/alembic.ini` + `backend/migrations/env.py`
- [ ] T014 创建 ORM 基类和共享 Mixin `backend/app/models/base.py`：BaseModel（id、created_at、updated_at）、UUIDMixin
- [ ] T015 创建 User 和 Role ORM 模型 `backend/app/models/user.py`：按 data-model.md User/Role 表定义
- [ ] T016 创建 User 和 Role Pydantic Schema `backend/app/schemas/user.py`：UserCreate、UserInfo、RoleCreate、RoleInfo、TokenResponse
- [ ] T017 [P] 创建认证服务 `backend/app/services/auth_service.py`：login、create_user、list_users、check_permission
- [ ] T018 [P] 创建认证 API 路由 `backend/app/api/v1/auth.py`：POST /auth/login、GET /auth/users、POST /auth/users、GET /auth/roles、POST /auth/roles
- [ ] T019 创建依赖注入模块 `backend/app/api/deps.py`：get_db、get_redis、get_current_user、require_permission
- [ ] T020 创建数据库初始化脚本 `backend/app/scripts/init_db.py`：创建默认管理员账号和系统角色
- [ ] T021 生成并运行首次 Alembic 迁移（User + Role 表 + pgvector 扩展）
- [ ] T022 [P] 创建前端路由框架 `frontend/src/App.jsx`：React Router 配置、布局组件、侧边栏菜单
- [ ] T023 [P] 创建前端 API 调用基础层 `frontend/src/services/api.js`：axios 实例、JWT 拦截器、错误处理
- [ ] T024 [P] 创建前端登录页面 `frontend/src/pages/Login/index.jsx`：登录表单、JWT 存储、跳转逻辑
- [ ] T025 [P] 创建前端状态管理 `frontend/src/stores/authStore.js`：Zustand store，用户信息、Token、权限

**检查点**: 基础就绪 — 可登录后台、JWT 认证工作、数据库/Redis 连接正常。

---

## 阶段 3: 用户故事 1 — 指令配置管理（优先级: P1）🎯 MVP

**目标**: PM 可在后台对意图和槽位进行增删改查，管理训练数据。

**独立测试**: 创建/编辑/删除意图，验证持久化和展示正确。

### 测试

- [ ] T026 [P] [US1] 编写 Intent CRUD API 合约测试 `backend/tests/contract/test_intents_api.py`
- [ ] T027 [P] [US1] 编写 TrainingData API 合约测试 `backend/tests/contract/test_training_data_api.py`

### 实施

- [ ] T028 [P] [US1] 创建 Intent ORM 模型 `backend/app/models/intent.py`：按 data-model.md Intent 表
- [ ] T029 [P] [US1] 创建 Slot ORM 模型 `backend/app/models/slot.py`：按 data-model.md Slot 表
- [ ] T030 [P] [US1] 创建 TrainingData ORM 模型 `backend/app/models/training_data.py`：按 data-model.md TrainingData 表
- [ ] T031 [P] [US1] 创建 Intent/Slot/TrainingData Pydantic Schema `backend/app/schemas/intent.py`
- [ ] T032 [US1] 创建意图管理服务 `backend/app/services/intent_service.py`：CRUD 操作、级联删除槽位和训练数据
- [ ] T033 [US1] 创建意图 API 路由 `backend/app/api/v1/intents.py`：按 admin-api.yaml Intents 部分
- [ ] T034 [US1] 生成 Alembic 迁移（Intent + Slot + TrainingData 表）
- [ ] T035 [P] [US1] 创建前端意图管理页面 `frontend/src/pages/IntentManager/index.jsx`：列表、筛选、CRUD 表单
- [ ] T036 [P] [US1] 创建前端槽位编辑组件 `frontend/src/pages/IntentManager/SlotEditor.jsx`
- [ ] T037 [P] [US1] 创建前端训练数据编辑组件 `frontend/src/pages/IntentManager/TrainingDataEditor.jsx`

**检查点**: PM 可登录后台，创建/编辑/删除意图及其槽位和训练数据。

---

## 阶段 4: 用户故事 2 — 知识库管理（优先级: P1）

**目标**: PM 可上传文档建立知识库，系统自动解析索引。

**独立测试**: 上传菜谱文档，验证解析、过滤无效字段、建立索引。

### 测试

- [ ] T038 [P] [US2] 编写知识库 CRUD + 文档上传 API 合约测试 `backend/tests/contract/test_knowledge_api.py`
- [ ] T039 [P] [US2] 编写文档解析与索引集成测试 `backend/tests/integration/test_knowledge_indexing.py`

### 实施

- [ ] T040 [P] [US2] 创建 KnowledgeBase ORM 模型 `backend/app/models/knowledge_base.py`
- [ ] T041 [P] [US2] 创建 KnowledgeDocument ORM 模型 `backend/app/models/knowledge_document.py`
- [ ] T042 [P] [US2] 创建 DocumentChunk ORM 模型 `backend/app/models/document_chunk.py`：含 pgvector embedding 字段
- [ ] T043 [P] [US2] 创建 Knowledge Schema `backend/app/schemas/knowledge.py`
- [ ] T044 [US2] 创建文档解析器 `backend/app/services/knowledge/parser.py`：JSON 解析（过滤无效字段）、Markdown 解析、文本分块
- [ ] T045 [US2] 创建向量索引器 `backend/app/services/knowledge/indexer.py`：调用 embedding 模型生成向量、写入 pgvector
- [ ] T046 [US2] 创建知识检索器 `backend/app/services/knowledge/retriever.py`：向量相似度搜索 + 重排序
- [ ] T047 [US2] 创建知识库管理服务 `backend/app/services/knowledge/service.py`：CRUD、文档上传触发异步索引
- [ ] T048 [US2] 创建知识库 API 路由 `backend/app/api/v1/knowledge.py`：按 admin-api.yaml Knowledge 部分
- [ ] T049 [US2] 生成 Alembic 迁移（KnowledgeBase + KnowledgeDocument + DocumentChunk 表 + HNSW 索引）
- [ ] T050 [P] [US2] 创建前端知识库管理页面 `frontend/src/pages/KnowledgeBase/index.jsx`：分类列表、文档上传、搜索测试
- [ ] T051 [P] [US2] 创建前端文档上传组件 `frontend/src/pages/KnowledgeBase/DocumentUpload.jsx`

**检查点**: PM 可上传 JSON/Markdown 文档，系统自动解析、过滤、索引，可搜索验证。

---

## 阶段 5: 用户故事 3 — 对话方案配置（优先级: P1）

**目标**: PM 可创建多个对话方案，配置大模型、人设、路由策略。

**独立测试**: 创建两个不同配置的方案，验证保存和切换。

### 测试

- [ ] T052 [P] [US3] 编写 DialogProfile CRUD API 合约测试 `backend/tests/contract/test_profiles_api.py`

### 实施

- [ ] T053 [P] [US3] 创建 Persona ORM 模型 `backend/app/models/persona.py`
- [ ] T054 [P] [US3] 创建 DialogProfile ORM 模型 `backend/app/models/dialog_profile.py`
- [ ] T055 [P] [US3] 创建 Profile/Persona Schema `backend/app/schemas/profile.py`
- [ ] T056 [US3] 创建对话方案管理服务 `backend/app/services/profile_service.py`：CRUD、关联意图/知识库/人设
- [ ] T057 [US3] 创建对话方案 API 路由 `backend/app/api/v1/profiles.py`：按 admin-api.yaml Profiles 部分
- [ ] T058 [US3] 生成 Alembic 迁移（Persona + DialogProfile 表）
- [ ] T059 [P] [US3] 创建前端对话方案页面 `frontend/src/pages/DialogProfile/index.jsx`：方案列表、创建/编辑表单
- [ ] T060 [P] [US3] 创建前端人设编辑组件 `frontend/src/pages/DialogProfile/PersonaEditor.jsx`
- [ ] T061 [P] [US3] 创建前端模型选择组件 `frontend/src/pages/DialogProfile/ModelSelector.jsx`：展示 ZenMux 可用模型列表

**检查点**: PM 可创建多个对话方案，配置不同 LLM 和人设。

---

## 阶段 6: 用户故事 4 — 手动单条对话测试（优先级: P1）

**目标**: PM 可在聊天界面测试对话方案，查看完整调试信息。

**独立测试**: 发送指令/知识/闲聊消息，验证调试面板展示完整链路。

### 测试

- [ ] T062 [P] [US4] 编写手动测试会话 API 合约测试 `backend/tests/contract/test_manual_test_api.py`

### 实施

- [ ] T063 [US4] 创建 NLU Pipeline 核心调度器 `backend/app/services/nlu/pipeline.py`：文本预处理 → 路由 → 意图/知识/闲聊 → 响应
- [ ] T064 [US4] 创建文本预处理器 `backend/app/services/nlu/preprocessor.py`：文本清洗、语言检测（中/英）、截断
- [ ] T065 [US4] 创建域路由器 `backend/app/services/nlu/router.py`：指令/知识/闲聊三域分类，可配置优先策略
- [ ] T066 [US4] 创建意图分类器 `backend/app/services/nlu/intent_classifier.py`：加载 JointBERT ONNX 模型、推理、返回 top-k 意图+置信度
- [ ] T067 [US4] 创建槽位提取器 `backend/app/services/nlu/slot_extractor.py`：从 JointBERT 输出提取 BIO 标注的槽位
- [ ] T068 [US4] 创建对话状态管理器 `backend/app/services/nlu/dialog_manager.py`：FSM 状态机、槽位填充、多轮追问
- [ ] T069 [US4] 创建指代消解模块 `backend/app/services/nlu/reference_resolver.py`：实体栈 + 规则引擎
- [ ] T070 [US4] 创建知识问答生成器 `backend/app/services/knowledge/qa_generator.py`：检索 + LLM 生成回复
- [ ] T071 [US4] 创建闲聊回复模块 `backend/app/services/chitchat/llm_adapter.py`：通过 ZenMux OpenAI SDK 调用大模型
- [ ] T072 [US4] 创建人设管理模块 `backend/app/services/chitchat/persona.py`：将 Persona 转为 system_prompt
- [ ] T073 [US4] 创建联网搜索模块 `backend/app/services/chitchat/web_search.py`：Brave Search API 调用封装
- [ ] T074 [US4] 创建会话管理器 `backend/app/services/session/device_session.py`：Redis Hash 读写、TTL 管理
- [ ] T075 [US4] 创建上下文维护模块 `backend/app/services/session/context.py`：对话历史、实体栈
- [ ] T076 [US4] 创建手动测试服务 `backend/app/services/testing/manual_test.py`：创建测试会话、发送消息、返回调试信息
- [ ] T077 [US4] 创建手动测试 API 路由 `backend/app/api/v1/testing.py`：POST sessions、POST chat（含 debug_info）
- [ ] T078 [P] [US4] 创建前端手动测试页面 `frontend/src/pages/ManualTest/index.jsx`：聊天界面 + 调试面板
- [ ] T079 [P] [US4] 创建前端调试面板组件 `frontend/src/pages/ManualTest/DebugPanel.jsx`：路由/意图/槽位/状态/耗时
- [ ] T080 [P] [US4] 创建前端设备上下文模拟器 `frontend/src/pages/ManualTest/DeviceContextSimulator.jsx`

**检查点**: PM 可在聊天界面测试对话方案，调试面板展示完整链路信息，NLU Pipeline 端到端运行。

---

## 阶段 7: 用户故事 5 — 设备端指令语义理解 API（优先级: P1）

**目标**: 对外暴露对话管理 API，设备端 APP 可直接调用。

**独立测试**: 通过 API 发送指令文本，验证准确率 ≥ 95%，延迟 < 200ms。

### 测试

- [ ] T081 [P] [US5] 编写 Dialog Parse API 合约测试 `backend/tests/contract/test_dialog_api.py`：按 dialog-api.yaml
- [ ] T082 [P] [US5] 编写 NLU Pipeline 端到端集成测试 `backend/tests/integration/test_nlu_pipeline.py`：覆盖 39 个意图

### 实施

- [ ] T083 [US5] 创建统一响应构建器 `backend/app/services/nlu/response_builder.py`：构造 DialogResponse（兼容指令/知识/闲聊三域）
- [ ] T084 [US5] 创建对话管理 API 路由 `backend/app/api/v1/dialog.py`：按 dialog-api.yaml（POST /dialog/parse、GET/DELETE /dialog/sessions/{device_id}、GET /dialog/version）
- [ ] T085 [US5] 创建版本加载器 `backend/app/services/version/loader.py`：从 PublishedVersion 加载活跃版本配置到内存
- [ ] T086 [US5] 创建健康检查端点 `backend/app/api/v1/health.py`：检查 DB/Redis/NLU 模型状态

**检查点**: 设备端可通过 API 发送文本，获得结构化的语义理解结果。

---

## 阶段 8: 用户故事 6 — 知识问答与开放闲聊（优先级: P2）

**目标**: 终端用户可进行知识问答和开放闲聊，支持联网内容。

**独立测试**: 发送菜谱问题和天气查询，验证知识命中和联网回复。

### 测试

- [ ] T087 [P] [US6] 编写知识问答集成测试 `backend/tests/integration/test_knowledge_qa.py`
- [ ] T088 [P] [US6] 编写闲聊（含联网）集成测试 `backend/tests/integration/test_chitchat.py`

### 实施

- [ ] T089 [US6] 增强知识问答流程：知识检索 → 未命中时降级到闲聊 `backend/app/services/nlu/pipeline.py` 补充逻辑
- [ ] T090 [US6] 增强联网搜索：识别需要实时信息的查询（天气/股票/新闻），调用 Brave Search `backend/app/services/chitchat/web_search.py` 补充策略
- [ ] T091 [US6] 增强多语言支持：英文输入检测 → 英文回复 `backend/app/services/nlu/preprocessor.py` + `response_builder.py`

**检查点**: 知识问答命中菜谱，联网查询天气成功，闲聊回复符合人设。

---

## 阶段 9: 用户故事 7 — 对话路由与上下文管理（优先级: P2）

**目标**: 路由策略可配置，多轮对话支持指代消解和省略恢复。

**独立测试**: 构造跨域、指代、省略等多轮对话用例，验证准确性。

### 测试

- [ ] T092 [P] [US7] 编写指代消解/省略恢复测试 `backend/tests/integration/test_reference_resolution.py`
- [ ] T093 [P] [US7] 编写跨域切换测试 `backend/tests/integration/test_cross_domain.py`

### 实施

- [ ] T094 [US7] 增强指代消解模块：处理"它"、"这个"、"刚才那个" `backend/app/services/nlu/reference_resolver.py`
- [ ] T095 [US7] 增强省略恢复：上下文继承活跃实体 `backend/app/services/nlu/reference_resolver.py`
- [ ] T096 [US7] 增强跨域切换：闲聊中检测到指令意图时切换到指令域 `backend/app/services/nlu/router.py`
- [ ] T097 [US7] 版本发布时批量清除会话：Redis SCAN + DEL `backend/app/services/version/publisher.py`

**检查点**: "搜个红烧肉" → "收藏它" 正确消解；闲聊中说"暂停烹饪"正确切换。

---

## 阶段 10: 用户故事 8 — 批量测试与智能分析（优先级: P3）

**目标**: PM 可自动生成测试用例、批量执行、查看智能分析报告。

**独立测试**: 生成测试集并执行，验证报告生成和分析准确性。

### 测试

- [ ] T098 [P] [US8] 编写批量测试 API 合约测试 `backend/tests/contract/test_batch_test_api.py`

### 实施

- [ ] T099 [P] [US8] 创建 TestSuite/TestCase/TestReport ORM 模型 `backend/app/models/test_suite.py`
- [ ] T100 [P] [US8] 创建 TestSuite Schema `backend/app/schemas/test_suite.py`
- [ ] T101 [US8] 创建测试用例自动生成器 `backend/app/services/testing/case_generator.py`：基于意图配置和知识库生成覆盖性用例
- [ ] T102 [US8] 创建批量测试执行器 `backend/app/services/testing/batch_test.py`：异步执行、收集结果
- [ ] T103 [US8] 创建智能分析引擎 `backend/app/services/testing/analyzer.py`：混淆矩阵、归因分析、优化建议（可调用 LLM 辅助分析）
- [ ] T104 [US8] 创建批量测试 API 路由 `backend/app/api/v1/testing.py`（补充 batch 部分）：生成、执行、查看报告
- [ ] T105 [US8] 生成 Alembic 迁移（TestSuite + TestCase + TestReport 表）
- [ ] T106 [P] [US8] 创建前端批量测试页面 `frontend/src/pages/BatchTest/index.jsx`：用例管理、执行、报告展示
- [ ] T107 [P] [US8] 创建前端分析报告组件 `frontend/src/pages/BatchTest/AnalysisReport.jsx`：混淆矩阵、趋势对比

**检查点**: PM 可自动生成测试用例、批量执行、查看智能分析报告。

---

## 阶段 11: 用户故事 9 — 生产 API 监控与设备日志（优先级: P2）

**目标**: PM 可在后台查看监控仪表盘和按设备 ID 查看历史会话日志。

**独立测试**: API 发送请求后，监控页面可查看日志，按设备 ID 筛选。

### 测试

- [ ] T108 [P] [US9] 编写监控 API 合约测试 `backend/tests/contract/test_monitoring_api.py`

### 实施

- [ ] T109 [P] [US9] 创建 RequestLog ORM 模型 `backend/app/models/request_log.py`：按 data-model.md，含多维索引
- [ ] T110 [P] [US9] 创建 AlertRule ORM 模型 `backend/app/models/alert_rule.py`
- [ ] T111 [P] [US9] 创建 Monitoring Schema `backend/app/schemas/monitoring.py`
- [ ] T112 [US9] 创建请求日志记录中间件 `backend/app/services/monitoring/log_writer.py`：每次 /dialog/parse 请求自动记录
- [ ] T113 [US9] 创建指标聚合服务 `backend/app/services/monitoring/metrics.py`：实时统计 QPS/延迟/准确率/路由分布
- [ ] T114 [US9] 创建日志查询服务 `backend/app/services/monitoring/log_query.py`：按设备 ID、时间、路由、意图等多维筛选
- [ ] T115 [US9] 创建告警引擎 `backend/app/services/monitoring/alerting.py`：规则匹配、触发通知
- [ ] T116 [US9] 创建监控 API 路由 `backend/app/api/v1/monitoring.py`：按 admin-api.yaml Monitoring 部分
- [ ] T117 [US9] 生成 Alembic 迁移（RequestLog + AlertRule 表 + 索引）
- [ ] T118 [P] [US9] 创建前端监控仪表盘 `frontend/src/pages/Monitoring/Dashboard.jsx`：实时指标、图表
- [ ] T119 [P] [US9] 创建前端设备日志页面 `frontend/src/pages/Monitoring/DeviceLogs.jsx`：设备搜索 → 会话列表 → 请求链路
- [ ] T120 [P] [US9] 创建前端告警规则页面 `frontend/src/pages/Monitoring/AlertRules.jsx`

**检查点**: PM 可查看实时仪表盘，按设备 ID 查看历史会话和每轮请求链路。

---

## 阶段 12: 用户故事 10 — 角色权限管理（优先级: P2）

**目标**: 管理员可创建账号、分配角色和菜单权限。

**独立测试**: 创建受限角色账号，验证只能访问授权菜单。

### 测试

- [ ] T121 [P] [US10] 编写 RBAC 权限控制集成测试 `backend/tests/integration/test_rbac.py`：验证受限角色无法访问未授权 API
- [ ] T122 [P] [US10] 编写用户管理 API 合约测试 `backend/tests/contract/test_user_management_api.py`

### 实施

- [ ] T123 [US10] 增强前端权限控制：根据 role.permissions 动态渲染菜单 `frontend/src/components/Layout/Sidebar.jsx`
- [ ] T124 [US10] 创建前端用户管理页面 `frontend/src/pages/UserManager/index.jsx`：用户列表、创建/编辑、角色分配
- [ ] T125 [US10] 创建前端角色管理组件 `frontend/src/pages/UserManager/RoleEditor.jsx`：权限矩阵编辑

**检查点**: 管理员可创建用户、分配角色，受限用户只能看到授权菜单。

---

## 阶段 13: 用户故事 — 版本发布（横切，P1 依赖）

**目标**: PM 可将对话方案打包发布为版本，设备立即切换。

### 实施

- [ ] T126 [P] [US3/US5] 创建 PublishedVersion ORM 模型 `backend/app/models/published_version.py`
- [ ] T127 [US3/US5] 创建版本发布服务 `backend/app/services/version/publisher.py`：快照方案、切换活跃版本、清除所有设备会话
- [ ] T128 [US3/US5] 创建版本管理 API 路由 `backend/app/api/v1/versions.py`：按 admin-api.yaml Versions 部分
- [ ] T129 [US3/US5] 生成 Alembic 迁移（PublishedVersion 表）
- [ ] T130 [P] [US3/US5] 创建前端版本管理页面 `frontend/src/pages/VersionManager/index.jsx`：版本历史、发布确认

**检查点**: PM 可发布版本，设备会话立即重置。

---

## 阶段 14: 完善与横切关注点

**目的**: 跨故事集成、性能优化、安全加固

- [ ] T131 [P] NLU 模型训练脚本 `backend/scripts/train_intent_model.py`：基于 chinese-roberta-wwm-ext 的 JointBERT 训练
- [ ] T132 [P] NLU 模型评估脚本 `backend/scripts/evaluate_model.py`：F1-Score、混淆矩阵、延迟基准
- [ ] T133 [P] ONNX 导出脚本 `backend/scripts/export_onnx.py`：PyTorch → ONNX + INT8 量化
- [ ] T134 [P] 英文训练数据翻译脚本 `backend/scripts/translate_training_data.py`：中→英翻译（ZenMux LLM 调用）
- [ ] T135 [P] 导出训练数据脚本 `backend/scripts/export_training_data.py`：从数据库导出标注数据
- [ ] T136 [P] DVC 数据版本管理初始化 `backend/.dvc/`：配置 DVC 跟踪训练数据集和模型产物，确保训练管道可审计可复现
- [ ] T137 性能优化：ONNX Runtime 推理加速、批量处理、模型预加载
- [ ] T138 [P] 安全加固 — API 限流（10 QPS）、输入校验、SQL 注入防护
- [ ] T139 [P] 安全加固 — 数据加密：对话历史和知识库文档的 AES-256 存储加密，数据库连接 TLS 配置 `backend/app/core/encryption.py`（对应 FR-036）
- [ ] T140 [P] 安全加固 — GDPR 合规：按设备 ID 维度的数据导出（JSON）和数据删除 API `backend/app/api/v1/data_management.py`（对应 FR-037）
- [ ] T141 增强 NLU Pipeline — 高风险操作二次确认：识别高温/长时操作，标记需确认 `backend/app/services/nlu/response_builder.py`（对应 FR-019）
- [ ] T142 增强 NLU Pipeline — 渐进式 3 级错误处理：未识别重试计数、选项列表、兜底话术 `backend/app/services/nlu/dialog_manager.py`（对应 FR-020）
- [ ] T143 [P] 编写端到端验收测试 `backend/tests/e2e/test_pm_workflow.py`：模拟 PM 全流程（创建方案 → 测试 → 发布 → 设备调用），验证 SC-007 时效约束
- [ ] T144 [P] 编写 README.md：项目概述、架构图、快速启动（本地环境）、API 文档链接
- [ ] T145 运行 quickstart.md 端到端验证

---

## 依赖关系与执行顺序

### 阶段依赖关系

- **阶段 1（设置）**: 无依赖 — 可立即开始
- **阶段 2（基础）**: 依赖阶段 1 — 阻塞所有用户故事
- **阶段 3-7（P1 故事）**: 依赖阶段 2，按顺序推荐（US1 → US2 → US3 → US4 → US5）
  - US1（意图配置）是 US4/US5 的数据前提
  - US2（知识库）是 US4 的数据前提
  - US3（对话方案）是 US4/US5 的配置前提
  - US4（手动测试）构建 NLU Pipeline，是 US5 的核心引擎
- **阶段 8-12（P2/P3 故事）**: 依赖阶段 7（NLU Pipeline 就绪），可并行
- **阶段 13（版本发布）**: 依赖阶段 5+7（方案 + API）
- **阶段 14（完善）**: 依赖所有用户故事完成；T139/T140（安全加固）可与 T131-T135（训练脚本）并行

### 用户故事依赖图

```
阶段1(设置) → 阶段2(基础)
                   │
                   ├→ US1(意图配置) ──┐
                   ├→ US2(知识库) ────┤
                   ├→ US3(对话方案) ──┤
                   │                  ▼
                   │              US4(手动测试/NLU Pipeline)
                   │                  │
                   │                  ▼
                   │              US5(设备端API)
                   │                  │
                   │    ┌─────────────┤──────────────┐
                   │    ▼             ▼              ▼
                   │  US6(知识/闲聊) US7(路由/上下文) US9(监控)
                   │                                 │
                   │    US8(批量测试) ◄───────────────┘
                   │    US10(权限管理)
                   │    版本发布 ◄── US3+US5
                   │
                   └→ 阶段14(完善)
```

### 并行机会

- 阶段 1 内：T003/T004/T005/T006/T007 全部可并行
- 阶段 2 内：T010/T011/T012 可并行，T022/T023/T024/T025 可并行
- US1 内：T028/T029/T030/T031 可并行，T035/T036/T037 可并行
- US8/US9/US10 可并行（依赖 NLU Pipeline 就绪即可）

---

## 实施策略

### MVP（仅 US1-US5，核心闭环）

1. 完成阶段 1-2：设置 + 基础
2. 完成 US1-US3：后台配置能力
3. 完成 US4：NLU Pipeline + 手动测试
4. 完成 US5 + 版本发布：设备端 API 可调用
5. **停止并验证**：PM 可配置 → 测试 → 发布 → 设备调用，闭环成立

### 增量交付

1. MVP 验证后 → 追加 US6（知识/闲聊增强）→ US7（上下文增强）
2. 追加 US8（批量测试）→ US9（监控）→ US10（权限）
3. 最后完善阶段（模型训练脚本、文档）

---

## 摘要

| 指标 | 数量 |
|------|------|
| **总任务数** | **145** |
| P1 用户故事任务 | 86（US1-US5 + 版本发布） |
| P2 用户故事任务 | 35（US6/US7/US9/US10，含 US10 新增测试） |
| P3 用户故事任务 | 9（US8） |
| 完善任务 | 15（含安全加固、DVC、渐进式错误处理、高风险确认、E2E 验收） |
| 可并行任务 [P] | 63 |
| MVP 范围 | US1-US5（阶段 1-7 + 阶段 13） |
