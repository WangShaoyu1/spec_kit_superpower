---
version: 2.0
updated: 2026-03-18
based_on:
  - spec.md@v1.4
  - pd-all/ (6 模块 PD 交互原型)
  - ad/ (7 文档, v2.0)
  - dd/ (7 文档, v2.0)
changelog: |
  2.0: 对齐 PD/AD/DD 新设计链路, 移除旧制品引用 (research.md/data-model.md/contracts/quickstart.md), 重新定位为"实施规划桥梁"
  1.3: 补充小模型平台无关训练产物要求（可下载、Python/C++双端运行）并将训练/运行逻辑改为 S1~S10 时序步骤
  1.2: 同步 D016 定稿实施计划（小模型闭环：模型版本治理、数据集流程、测试与发布门禁）
  1.1: 同步 D014 定稿实施计划（语种指令库、方案阈值、路由约束、迁移与验收）
  1.0: 初始版本
---
# 实施计划: SmartChef 智能对话管理平台

**分支**: `master` | **日期**: 2026-03-18 | **规范**: [spec.md](./spec.md)
**输入**: 完整设计文档链（spec.md + pd-all/ + ad/ + dd/）

## 摘要

为智能微波炉构建完全自研的对话管理平台，替换讯飞旧方案。包含两个交付物：

1. **后台管理系统**（Web）：PM 配置指令/知识库/人设、手动测试、批量测试、监控仪表盘、版本发布
2. **对话管理 API**（云端）：设备端 APP 调用，按设备 ID 隔离会话，统一路由（指令/知识/闲聊）

技术方案采用**小模型 + 大模型混合架构**：小模型（JointBERT 类）负责指令意图分类与槽位提取（< 200ms），大模型（通过 ZenMux 统一网关调用 GPT-5/千问/DeepSeek/Claude 等 120+ 模型）负责知识问答与开放闲聊（2-4s）。小模型需导出为 ONNX/TensorRT 格式，支持在 Jetson Nano 上以 C++ 运行。

## 技术背景

**语言/版本**: Python 3.11+（后端服务、模型训练）、JavaScript ES2022+（前端管理系统，React + Vite，不使用 TypeScript）、C++17（设备端小模型推理）
**主要依赖**:
- 后端 API: FastAPI + Uvicorn + Pydantic v2
- NLU 模型: PyTorch 2.x + Transformers（训练）、ONNX Runtime（推理加速）
- 知识检索: PostgreSQL + pgvector（复用主存储，万级向量规模足够，详见 ad/ad-knowledge-base.md §5）
- 大模型: ZenMux API Gateway（统一 OpenAI 兼容接口，120+ 模型，`base_url=https://zenmux.ai/api/v1`）
- 联网搜索: Brave Search API（自建索引，隐私友好，团队已有 Key）
- 前端: React 18 + Ant Design 5 + Vite（JavaScript，不使用 TypeScript）
- 缓存/会话: Redis 7.x

**存储**:
- PostgreSQL 16（持久化：指令配置、知识库元数据、对话方案、版本记录、用户账号、请求日志）
- Redis 7.x（运行时：设备会话状态、对话上下文、缓存）
- 向量数据库: pgvector（PostgreSQL 扩展，与主库统一，详见 dd/dd-knowledge-base.md）

**测试**:
- 后端: pytest + pytest-asyncio + httpx（单元/集成/E2E）
- 前端: Vitest + Playwright（组件/E2E，JavaScript）
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

*门控: 必须在设计阶段之前通过. Plan 编写时重新检查.*

| # | 章程原则 | 状态 | 计划对齐说明 |
|---|---------|------|-------------|
| I | 意图优先架构 | ✅ 通过 | NLU Pipeline 严格分层：文本预处理 → 路由分类 → 意图分类 → 槽位提取 → 对话状态 → 响应生成；意图通过注册机制接入（PM 后台 CRUD）；低置信度触发澄清对话 |
| II | 领域驱动设计 | ✅ 通过 | 指令域 + 闲聊域（含知识子域）独立设计；用户偏好域标注 V2；领域间通过路由器统一调度，无直接依赖 |
| III | 测试驱动开发 | ✅ 通过 | pytest + Vitest + 模型评估脚本；F1 基线（指令 ≥ 0.95、闲聊 ≥ 0.85）；批量测试闭环 |
| IV | 数据管道完整性 | ✅ 通过 | 训练数据版本化；模型产物含元数据；对话方案版本发布机制；CI/CD 管道强制 |
| V | 对话体验一致性 | ✅ 通过 | Persona 人设配置；分层回复架构（确认 → 补充 → 引导）；渐进式错误处理；i18n 中英文 |
| VI | 可观测性与指标驱动 | ✅ 通过 | 完整监控仪表盘（FR-030~035）；结构化请求日志；按设备 ID 维度查看历史；告警规则可配置 |
| VII | 安全与隐私优先 | ✅ 通过 | RBAC 权限管理；高风险操作二次确认；数据加密存储；最小权限原则 |

**门控结论（设计前）**: 全部通过，无违规项。已进入设计阶段。

### PD/AD/DD 设计后重新检查

| # | 章程原则 | 状态 | 设计对齐验证 |
|---|---------|------|-------------|
| I | 意图优先架构 | ✅ 通过 | dd/dd-intent-library: Intent/Slot/TrainingData 实体完整定义（12 实体）；ad/ad-global: `/dialog/parse` 返回 intent+slots 结构化结果；dd/dd-intent-library §4: JointBERT 联合模型训练推理算法 |
| II | 领域驱动设计 | ✅ 通过 | ad/ad-global: 6 大领域划分；项目结构按 nlu/knowledge/chitchat/session 领域组织；API 路由三域分离；DialogProfile 可配置路由策略 |
| III | 测试驱动开发 | ✅ 通过 | dd/dd-batch-test: BatchTest/TestCase/TestRun/TestRunAnalysis 完整建模（4 实体）；ad/ad-batch-test: 批量测试 + 智能分析 17 个 API 端点 |
| IV | 数据管道完整性 | ✅ 通过 | dd/dd-global: PublishedVersion 含完整快照 + 模型产物路径；dd/dd-intent-library: TrainingData 含语言和标注信息 + ONNX 导出流程 |
| V | 对话体验一致性 | ✅ 通过 | dd/dd-dialog-profile: Persona 实体含 system_prompt；ad/ad-global: 响应格式统一三域 + 渐进式错误处理 3 步策略；dd/dd-global: DeviceSession Redis 状态管理 |
| VI | 可观测性与指标驱动 | ✅ 通过 | dd/dd-monitoring: RequestLog 含完整链路字段 + 多维索引 + 分区策略；AlertRule 告警规则 + AlertEvent 状态机；ad/ad-monitoring: 监控仪表盘 + 设备日志端点（含 Redis 缓存） |
| VII | 安全与隐私优先 | ✅ 通过 | dd/dd-user-mgmt: User/Role RBAC + 21 个能力点完整映射；JWT + bcrypt + Token 黑名单；dd/dd-global: `require_capability` 装饰器伪代码 |

**门控结论（设计后）**: 全部通过，PD/AD/DD 设计制品与章程完全对齐。

## 项目结构

### 设计文档（上游输入）

```
specs/master/
├── spec.md              # 业务需求 (/speckit.specify 输出)
├── pd-all/              # 产品交互设计 (/speckit.design-pd 输出)
│   ├── pd-hub.html      # 统一查看入口（iframe 导航）
│   ├── pd-index.md      # PD 模块覆盖索引
│   └── pd-<module>/     # 各模块交互原型 (HTML)
├── ad/                  # 架构设计 (/speckit.design-ad 输出)
│   ├── README.md        # AD 模块索引
│   ├── ad-global.md     # 全局架构
│   └── ad-<module>.md   # 7 个模块架构设计
├── dd/                  # 详细设计 (/speckit.design-dd 输出)
│   ├── README.md        # DD 模块索引
│   ├── dd-global.md     # 全局详设（共享实体/错误码/权限/配置）
│   └── dd-<module>.md   # 7 个模块详细设计
├── plan.md              # 此文件 (/speckit.plan 输出)
└── tasks/               # 任务目录 (/speckit.tasks 输出)
    ├── README.md        # 索引(模块列表/统计/依赖/策略/进度)
    ├── tasks-infra.md   # 基础设施
    ├── tasks-<module>.md # 各 PD 模块任务
    └── tasks-refinement.md # 横切关注点
```

> **注**: 旧流程中的 `research.md`、`data-model.md`、`contracts/`、`quickstart.md` 已由 PD/AD/DD 完全替代，已归档至 `_archive/` 目录。

### 源代码(仓库根目录)

```
smartchef-v2/
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
│   │   ├── train_intent_model.py      # JointBERT 联合训练（意图+槽位）
│   │   ├── evaluate_model.py
│   │   ├── export_onnx.py           # 导出 ONNX 格式
│   │   ├── translate_training_data.py # 中→英训练数据翻译
│   │   └── export_training_data.py  # 导出标注数据
│   └── pyproject.toml
│
├── frontend/                         # React 管理系统前端（JavaScript）
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
│   └── package.json
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
├── scripts/
│   └── manage_services.py           # 本地 PostgreSQL + Redis 启停脚本
└── README.md
```

**结构决策**: 采用 Web 应用程序结构（后端 + 前端分离），额外增加 device-inference 模块用于设备端小模型推理。后端采用分层架构（API → Services → Models），NLU 服务按领域驱动设计组织（nlu/knowledge/chitchat/session）。

## 前端设计规范

> 前端实现 MUST 同时遵守以下两项规范，确保界面既美观又高性能。

### 设计美学 — `frontend-design` Skill

- **风格定位**: 企业级智能对话管理平台 — 精致、专业、高信息密度
- **色彩**: 采用深色/浅色双主题，主色为冷蓝 (#1677ff 系)，辅以中性灰阶，强调色用于状态指示
- **排版**: 选用有质感的字体组合（标题/数据用等宽字体），避免 Inter/Arial 等泛用字体
- **动效**: 关键交互（页面切换、弹窗、状态变更）使用流畅过渡动画，优先 CSS-only 方案
- **布局**: 侧边栏 + 内容区经典布局，内容区善用统计卡片、Table、抽屉面板组合
- **细节**: 背景使用微妙纹理/渐变增加层次感，避免纯白/纯灰平铺；所有图标、间距、阴影精心调校

### React 性能 — `vercel-react-best-practices` Skill

前端代码 MUST 遵循 Vercel React 最佳实践（58 规则 / 8 类别），重点关注:
- **CRITICAL**: 消除请求瀑布流（Promise.all 并行、Suspense 边界）
- **CRITICAL**: Bundle 优化（直接导入避免 barrel files、动态 import 重组件）
- **HIGH**: 最小化序列化数据、并行数据获取
- **MEDIUM**: 减少不必要 re-render（useMemo/useCallback 恰当使用、派生状态直接计算）
- **JS 性能**: Set/Map O(1) 查找、early return、toSorted() 不可变排序

## 复杂度跟踪

*无章程违规，无需额外复杂度证明。*

## 阶段规划

> plan.md 的核心章节——将 PD 模块按依赖关系编排为可执行的实施阶段。
> 设计链路: spec.md → PD → AD → DD → plan → tasks。PD 模块是阶段规划的首要组织单元。
> 详细的数据模型、API 契约、状态机等在 AD/DD 中已定义，此处仅做阶段性引用。

### 阶段 1: 基础设施（阻塞后续所有工作）

**目标**: 项目初始化 + 数据库 + 认证 + 基础中间件
**检查点**: 项目可启动、数据库可连接、JWT 认证流程可用、RBAC 框架就绪

| 交付项 | 设计依据 |
|--------|---------|
| 项目骨架 + 配置体系 | ad/ad-global.md §2 |
| PostgreSQL 模型 + Alembic 迁移 | dd/dd-global.md §1 |
| JWT 认证 + RBAC 中间件 | dd/dd-user-mgmt.md §3~§5 |
| Redis 连接 + 设备会话 | dd/dd-global.md §1.5 |
| 统一响应包络 + 错误码框架 | ad/ad-global.md §4 + dd/dd-global.md §2 |
| 日志中间件（异步写入） | dd/dd-monitoring.md §4.1 |

### 阶段 2: 核心功能（按 PD 模块优先级）

**目标**: 按 P1 → P2 → P3 顺序交付 PD 模块
**检查点**: 每个模块可对照 PD 交互稿独立验证

| 优先级 | PD 模块 | PD 交互原型 | 设计依据(AD + DD) |
|--------|---------|------------|------------------|
| P1 | 指令库管理 | pd-all/pd-intent-library/ | ad/ad-intent-library.md + dd/dd-intent-library.md |
| P1 | 知识库管理 | pd-all/pd-knowledge-base/ | ad/ad-knowledge-base.md + dd/dd-knowledge-base.md |
| P1 | 对话方案(含手动测试) | pd-all/pd-dialog-profile/ | ad/ad-dialog-profile.md + dd/dd-dialog-profile.md |
| P2 | 批量测试 | pd-all/pd-batch-test/ | ad/ad-batch-test.md + dd/dd-batch-test.md |
| P2 | 监控仪表盘 | pd-all/pd-monitoring/ | ad/ad-monitoring.md + dd/dd-monitoring.md |
| P3 | 用户管理 | pd-all/pd-user-mgmt/ | ad/ad-user-mgmt.md + dd/dd-user-mgmt.md |

### 阶段 3: 横切关注点

**目标**: 权限完善、性能优化、安全加固
**检查点**: 非功能需求满足

| 交付项 | 设计依据 |
|--------|---------|
| 完整 RBAC 21 能力点 | dd/dd-global.md §3 |
| 监控 Redis 缓存 + 仪表盘指标 | dd/dd-monitoring.md §4.2 |
| 输入校验 + XSS 防护 | ad/ad-global.md §6.1 |
| 性能基线（P95 < 200ms 指令，< 4s 知识问答） | spec.md SC-001~SC-004 |

### 阶段 4: 完善与优化

**目标**: 文档、代码清理、端到端集成验证
**检查点**: 可交付

## 测试策略

> 具体测试场景来自 PD 的交互规范 + DD 的边界条件。

| 测试类型 | 时机 | 覆盖目标 | 工具 |
|---------|------|---------|------|
| 单元测试 | 开发同步 | DD 定义的算法逻辑（状态机转移/边界条件） | pytest + pytest-asyncio |
| 契约测试 | API 稳定后 | AD 定义的接口契约（130+ API 端点） | pytest + httpx |
| 集成测试 | 阶段完成 | AD 数据流（对话推理管道/版本发布流程） | pytest + httpx |
| E2E 测试 | 故事闭环 | PD 交互路径（用户操作路径 + 状态矩阵） | Playwright |
| 模型评估 | 训练完成 | F1 基线（指令 ≥ 0.95、闲聊 ≥ 0.85） | 自研评估脚本 |

## 风险与缓解

| 风险类型 | 描述 | 缓解策略 |
|---------|------|---------|
| 技术风险 | JointBERT 训练效果不达标 | 准备 fallback（调大 LLM 权重）；评估阈值可配置 |
| 依赖风险 | ZenMux API 不稳定 | 超时 8s + 3 次重试；降级到本地缓存回复 |
| 性能风险 | pgvector 检索延迟高 | HNSW 索引 + 预加载；必要时迁移独立向量库 |
| 进度风险 | 设计文档量大，实施节奏难把控 | 按阶段交付、每阶段有独立检查点 |

---

## 反馈迭代计划（第 1 轮）

**输入依据**: `specs/master/feedback_1.md`
**迭代方式**: 文档先行，小步快跑，按优先级闭环交付。

### 优先级与范围

- **P0（立即处理）**
  - 接口响应包络统一（`code/data/msg`）
  - `test/chat` CSRF 问题修复
  - 全站弹窗 `maskClosable=false`
  - 全站 Input `allowClear`

- **P1（本轮核心功能）**
  - 手动测试会话编辑/删除
  - 对话方案草稿状态流转
  - 闲聊人设编辑能力
  - 批量测试拆分流（新建批次/上传用例）+ Excel 模板解析 + 结果大弹窗
  - 指令库两级路由（指令库 → 意图）
  - 角色定义与能力模型

- **P2（文档与交互资产）**
  - docs 聚合 Hub（带 TOC，索引现有文档）
  - 交互界面 PRD HTML
  - 文档一致性校对（spec/plan/tasks）

### 验收准入（Exit Criteria）

- **EC-1**: P0 全量完成并通过基本回归（接口契约 + 页面关键交互）。
- **EC-2**: P1 功能可在后台完成端到端操作（创建、编辑、执行、查看结果）。
- **EC-3**: P2 文档可直接用于评审，链接可达，章节完整。
- **EC-4**: 迭代产物均可追溯到任务项与测试记录。

### 显式执行顺序（必须遵循）

1. **Docs**：先改 `spec.md` / `plan.md` / `tasks/`，再补设计文档更新（pd-all/ / ad/ / dd/）。
2. **Implementation**：按 P0 → P1 → P2 开发，禁止跳过 P0。
3. **Testing**：先契约测试，再集成测试，最后 E2E 与手工回归，输出迭代测试报告。

## 反馈迭代计划（第 2 轮：D014 定稿）

**输入依据**: `specs/master/defects/D014.md`（已定稿）
**目标**: 完成“指令库语种化 + 对话方案并行绑定 + 指令阈值 + 英文未命中不回退中文”的一致性实现。

### 范围与约束

- 指令库固定两种语种：中文、英文（当前阶段不扩展多语言）。
- 对话方案不配置语种字段，改为并行绑定多个指令库（典型：中文库 + 英文库）。
- 英文输入若英文库未命中，直接进入知识/闲聊链路，不回退中文库。
- `library_key` 全局唯一、不可修改，变更通过“删库重建”完成。
- 存量迁移采用“现有意图默认归入中文库，英文后续补齐”。

### 设计落地点

- **后端模型与接口**: 增补指令库实体字段约束（语种、不可变 `library_key`），完善对话方案与指令库多对多关联及阈值字段。
- **运行时路由**: 在 NLU pipeline 中接入“语种感知 + 指令阈值判定 + 英文未命中不回退”策略。
- **前端交互**: 对话方案新增“多指令库选择 + 指令阈值”配置；编辑弹窗采用“简单项双列、复杂项整行”布局规则。
- **数据迁移**: 提供一次性迁移脚本/迁移任务，将存量意图默认归入中文库。

### 验收准入（Exit Criteria）

- **EC-2-1**: 指令库新增/编辑流程可区分语种，`library_key` 冲突和修改被正确拦截。
- **EC-2-2**: 对话方案可并行绑定多个指令库并保存“指令阈值”，发布校验通过。
- **EC-2-3**: 英文输入在英文库未命中时进入知识/闲聊链路，且不会回退中文库。
- **EC-2-4**: 完成迁移后，存量意图可在中文库视图正常检索与维护。
- **EC-2-5**: 完成契约测试、集成测试、E2E 回归，并更新缺陷状态到可验收。

## 反馈迭代计划（第 3 轮：D016 小模型闭环）

**输入依据**: `specs/master/defects/D016.md`（已定稿）
**目标**: 完成“指令库小模型从数据到生效”的规范化闭环设计，作为后续研发唯一执行基线。

### 范围与约束

- 本轮先完成文档同步，不直接进入开发。
- 模型治理按“每库多模型、库内唯一 published/testable、同模型可同时 published+testable”执行。
- 单库模型上限固定为 5（代码常量），超限时禁止新建训练任务。
- 训练集与评估集分离：训练集与模型 1:1，评估集与模型非 1:1。
- 评估阈值采用“库级默认 + 任务级覆盖并快照”。
- 方案层不强制绑定指令库；但绑定库时必须有 published 模型才允许方案发布。

### 设计落地点

- **模型版本治理**: 增补 `LibraryModelVersion` 概念和状态机，定义 testable/published 互斥范围与切换规则。
- **数据管道**: 定义训练集/评估集 Excel 口径和 LLM 合成治理规则，明确训练、评估任务输入输出边界。
- **测试体系**: 在“指令库 -> 模型 -> 测试”下统一单条测试与批量测试；评估完成自动触发智能分析。
- **权限与发布控制**: 新增 `model_publish`、`model_test_manage` 能力点，发布动作要求二次确认。
- **方案发布门禁**: 方案绑定库时检查库是否存在 published 模型，缺失则阻断方案发布并提示。
- **跨平台产物**: 训练产物必须为平台无关模型格式并支持下载，确保同一版本可在 Python 服务端与 C++ 设备端加载运行。

### D016 时序化步骤（S1~S10）

**训练与评估（S1~S6）**

- **S1 数据准备（训练集）**: 在库级准备训练数据（人工 + LLM 合成），字段口径 `intent_key, utterance, language, slots(json), source`，满足“全 intent 覆盖 + 每 intent 最小样本数 N”。
- **S2 训练任务创建**: 选择一个训练集创建训练任务（训练集与模型 1:1）；若库内模型数已达 5，阻断创建并提示先归档/删除。
- **S3 模型训练执行**: 状态推进 `draft -> training -> trained`，记录训练参数、训练集版本、产物元数据。
- **S4 产物导出与登记**: 导出平台无关模型产物（如 ONNX/TensorRT），生成可下载地址与哈希签名，并登记到模型版本记录。
- **S5 评估任务执行**: 选择评估集发起评估（模型与评估集非 1:1）；阈值默认继承库级，可在本次任务覆盖并写快照；状态推进 `trained -> evaluating -> testable`。
- **S6 评估结果沉淀**: 回填 `actual_result/actual_score/is_hit`，自动生成智能分析（总体结论、混淆 TopN=5、槽位错误分布、低分样本、改进建议）。

**发布与运行（S7~S10）**

- **S7 测试态管理**: 在“指令库 -> 模型 -> 测试”页进行单条/批量测试；切换 testable 自动互斥（库内最多 1 个），权限 `model_test_manage`。
- **S8 人工发布**: 执行模型发布（需二次确认，备注可空，权限 `model_publish`）；库内保持 published 唯一，允许同模型同时 testable + published。
- **S9 方案发布校验**: 对话方案发布前校验绑定库是否均存在 published 模型；未满足则阻断并提示。方案可不绑定指令库。
- **S10 运行时加载与推理**: 版本加载器仅装载各绑定库的 published 模型；请求推理时按语种与库映射命中模型，若 `unknown` 或 `score < command_threshold` 则判定未命中，直接进入后续链路（知识/闲聊），不跨库回退。

### 验收准入（Exit Criteria）

- **EC-3-1**: `spec.md`、`plan.md`、`tasks/` 完成 D016 一致性同步，术语与规则无冲突。
- **EC-3-2**: 模型状态机、上限、权限、门禁、阈值配置层级在三份文档中口径一致。
- **EC-3-3**: 训练/评估数据字段规范、LLM 生成规则、单条/批量测试边界在三份文档中可追溯。
- **EC-3-4**: 形成可直接进入研发的任务拆解（实现与测试项完整，默认未完成状态）。

## 版本迭代表

| 版本 | 日期 | 变更摘要 | 来源 |
|---|---|---|---|
| 2.0 | 2026-03-18 | 对齐 PD/AD/DD 新设计链路; 移除旧制品引用; 新增阶段规划/测试策略/风险章节; 重新定位为实施规划桥梁 | PD/AD/DD 全量完成 |
| 1.3 | 2026-03-12 | 补充跨平台模型产物要求，并将 D016 训练/运行逻辑时序化为 S1~S10 | `specs/master/defects/D016.md` |
| 1.2 | 2026-03-12 | 新增 D016 小模型闭环实施计划（模型治理、数据管道、测试与权限门禁） | `specs/master/defects/D016.md` |
| 1.1 | 2026-03-10 | 新增 D014 定稿实施计划与验收标准（模型/API/路由/UI/迁移） | `specs/master/defects/D014.md` |
| 1.0 | 2026-03-10 | 初始计划版本 | 初始建档 |
