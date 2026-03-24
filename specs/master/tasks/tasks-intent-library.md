# 指令库管理 (Intent Library) 任务

**PD 交互原型**: pd-all/pd-intent-library/ (5 pages: index, detail, datasets, dataset-detail, test)
**架构设计**: ad/ad-intent-library.md
**详细设计**: dd/dd-intent-library.md
**优先级**: P1
**依赖**: tasks-infra.md 必须先完成

**进度口径**: 基线重做中。历史 `41/41` 仅代表旧任务链记录，不作为当前完成证明。

## 模块核心业务链路

1. 创建指令库并维护基础信息
2. 创建训练/评估数据集，并在 `dataset-detail.html` 维护意图、词槽、实体、相似问/排除问
3. 基于训练集创建模型版本并推进 `draft -> training -> trained`
4. 在 `test.html` 完成单条测试与批量测试，看到真实结果、真实进度和真实分析状态
5. 设置 `testable` / `published`，下载模型，并被对话方案发布门禁正确消费

## 本轮真实任务切片

- [ ] R01 [DOC] 校正文档链口径：PD/AD/DD/plan/tasks 对齐 5 页边界、FR 追溯、假成功禁令
  - 完成定义: `pd-all/pd-intent-library/README.md`、`ad/ad-intent-library.md`、`dd/dd-intent-library.md`、`plan.md`、本文件口径一致
- [ ] R02 [T-CONTRACT] 补齐数据集与测试消费契约
  - 范围: LLM 合成真实返回、消息列表包络/分页、批量测试分析空态、样本数展示口径
  - 完成定义: 至少存在失败场景与成功场景契约测试，不再只验证 happy path
- [ ] R03 [B/FIX] 修补后端闭环缺口
  - 范围: 训练状态推进、LLM 合成错误透传、模型测试/分析真实状态源
  - 完成定义: 核心写路径无 500 / 无伪成功返回
- [ ] R04 [F/FIX] 修补前端消费与展示缺口
  - 范围: 数据集样本数、LLM 合成反馈、测试会话/消息、批量测试结果与分析展示
  - 完成定义: 前端严格按真实响应包络消费，不伪造进度、不硬编码结果
- [ ] R05 [VERIFY] 跑通核心业务链路验证
  - 范围: 建库 → 数据集 → 训练 → 测试 → 发布
  - 完成定义: 形成可引用的测试/运行证据，失败点需记录为缺陷或延期项
- [ ] R06 [REVIEW] 执行 review / smoke / 缺陷回灌
  - 完成定义: 输出阻塞项、剩余风险、显式未完成声明

## 显式未完成声明

| 项目 | 当前状态 | 处理原则 |
|------|---------|---------|
| 数据集 Excel 导入/导出 | Deferred | 当前仅保留文件校验与延期提示；若未接入真实解析/导出服务，UI 不得伪装已完成 |
| `FR-050` 阈值继承说明 UI | 部分覆盖 | 本轮至少补齐真实阈值快照和消费契约 |
| 批量测试 / 智能分析闭环 | 已闭环 | `test.html` 已改为创建真实 `batch-tests` 任务并跳转详情页；结果与分析统一以 `/batch-test/{id}` 状态源为准 |
| LLM 按意图子集定向生成 | Deferred | 当前仅支持按数据集关联的全部意图生成；UI 必须明确为只读预览，不得伪装为可选范围 |

## 模块完成定义（Definition of Done）

- 核心业务链路至少跑通 1 次，并保留验证证据
- 关键缺陷对应链路无 `placeholder`、无“演示成功”、无硬编码假数据
- `tasks` 中的完成状态、测试结果、显式未完成声明三者一致
- 若存在延期项，必须写清 `Deferred / Out of Scope / Blocked By`

## 历史任务记录（仅供对照，不作为当前完成证明）

## 测试任务（TDD: 先写测试, 确保红灯）

### 契约测试（覆盖 AD API — 57 端点分组测试）

- [x] T001 [P] [T-CONTRACT] 指令库 CRUD 契约测试: GET/POST /intent-libraries, GET/PUT/DELETE /intent-libraries/{id}
  - 文件: `backend/tests/contract/test_intent_libraries_api.py`
  - 依据: ad/ad-intent-library.md §3.1
  - ✅ 已实现: list/create/get/get-404/delete/no-auth-401, mock service
- [x] T002 [P] [T-CONTRACT] 模型版本 CRUD + 生命周期契约测试: GET/POST /intent-libraries/{lib_id}/models, POST /models/{id}/train, /evaluate, /set-testable, /publish, /archive, /restore, GET /models/{id}/download
  - 文件: `backend/tests/contract/test_model_versions_api.py`
  - 依据: ad/ad-intent-library.md §3.2
  - ✅ 已实现: list/create/train/evaluate/set-testable/publish/archive/get/download/no-auth-401, 10 tests passed
- [x] T003 [P] [T-CONTRACT] 数据集 CRUD + 导入导出契约测试: GET/POST /intent-libraries/{lib_id}/datasets, GET/PUT/DELETE /datasets/{id}, POST /datasets/{id}/import, GET /datasets/{id}/export, POST /datasets/{id}/generate-training, /generate-evaluation
  - 文件: `backend/tests/contract/test_datasets_api.py`
  - 依据: ad/ad-intent-library.md §3.3
  - ⚠️ 历史记录：当前已补到 training/evaluation 的 get/update/delete + generate-training/generate-evaluation 契约覆盖；导入/导出仍待后续补齐
- [x] T004 [P] [T-CONTRACT] 意图 CRUD 契约测试: GET/POST /datasets/{id}/intents, GET/PUT/DELETE /datasets/{id}/intents/{intent_id}
  - 文件: `backend/tests/contract/test_intents_api.py`
  - 依据: ad/ad-intent-library.md §3.4
  - ✅ 已实现: list/create/get/update/delete/no-auth-401, 6 tests passed
- [x] T005 [P] [T-CONTRACT] 词槽/实体/相似问/排除问 CRUD 契约测试
  - 文件: `backend/tests/contract/test_slots_entities_api.py`
  - 依据: ad/ad-intent-library.md §3.5~§3.6
  - ✅ 已实现: slots(list/create/get/update/delete) + entities(list/create/update/delete) + sq(list/create/update/delete) + neg(list/create/delete) + no-auth-401, 17 tests passed
- [x] T006 [P] [T-CONTRACT] 测试会话 + 消息链路契约测试: POST/GET/PUT/DELETE sessions, POST /test-sessions/{sid}/messages, GET /test-sessions/{sid}/messages
  - 文件: `backend/tests/contract/test_intent_testing_api.py`
  - 依据: ad/ad-intent-library.md §3.7
  - ⚠️ 历史记录：当前已锁定 create-session/list-sessions/update/delete/send-message/list-messages/no-auth-401；标准批量测试/test-run/analysis 契约不在该文件内

### 集成测试（覆盖 AD 数据流）

- [x] T007 [P] [T-INTEGRATION] 模型生命周期集成测试: draft→training→trained→evaluating→testable→published→archived 完整流转
  - 文件: `backend/tests/integration/test_model_lifecycle.py`
  - 依据: ad/ad-intent-library.md §2.1 模型生命周期数据流
  - ✅ 已实现: 4 个 API 契约测试 (library_crud, dataset_intent_crud, model_version_crud, eval_dataset_crud)
- [x] T008 [P] [T-INTEGRATION] 训练流水线集成测试: 数据准备→训练→产物导出→评估 端到端
  - 文件: `backend/tests/integration/test_training_pipeline.py`
  - 依据: ad/ad-intent-library.md §2.2 训练数据流
  - ✅ 已实现: 完整 E2E — seed data → JointBERT train → ONNX export → inference → evaluation → publish; Intent F1=0.556, Eval Acc=0.75

### E2E 测试（覆盖 PD 交互路径）

- [x] T009 [P] [T-E2E] 指令库列表页 E2E: 搜索/筛选/新建/编辑/删除 交互路径
  - 文件: `frontend/tests/e2e/intent-library-list.spec.js`
  - 依据: pd-all/pd-intent-library/index.html
  - ✅ 已实现: 6 tests — page-load/table/search/create-modal/create-flow/console-errors
- [x] T010 [P] [T-E2E] 指令库详情页 E2E: 模型版本创建/训练/发布/归档 交互路径
  - 文件: `frontend/tests/e2e/intent-library-detail.spec.js`
  - 依据: pd-all/pd-intent-library/detail.html
  - ✅ 已实现: 7 tests — detail-info/model-table/create-model-btn/create-modal/datasets-nav/status-tags/console-errors

## 后端任务

### 数据模型（来自 DD 实体定义）

- [x] T011 [P] [B-MODEL] 创建 IntentLibrary ORM 模型 (id, name, library_key, language, description, status, model_count_limit)
  - 文件: `backend/app/models/intent_library.py` (38 行)
  - 依据: dd/dd-intent-library.md §1.1
  - ✅ 已实现: library_key, name, language, thresholds, relationships
- [x] T012 [P] [B-MODEL] 创建 LibraryModelVersion ORM 模型 (id, library_id, version_number, status, training_dataset_id, training_params, model_artifacts_path, metrics, published_at) + 状态枚举
  - 文件: `backend/app/models/model_version.py` (66 行)
  - 依据: dd/dd-intent-library.md §1.2
  - ✅ 已实现: 完整状态生命周期, artifact_uri, train_config, is_testable, is_published
- [x] T013 [P] [B-MODEL] 创建 TrainingDataset / EvaluationDataset ORM 模型
  - 文件: `backend/app/models/dataset.py` (66 行)
  - 依据: dd/dd-intent-library.md §1.3~§1.4
  - ✅ 已实现: library_id, samples, sample_count, intent_count, config
- [x] T014 [P] [B-MODEL] 创建 Intent / Slot / SlotEntity / SimilarQuestion / NegativeExample ORM 模型
  - 文件: `backend/app/models/intent.py` (71 行), `backend/app/models/slot.py` (49 行)
  - 依据: dd/dd-intent-library.md §1.5~§1.9
  - ✅ 已实现: 全部 5 个模型
- [x] T015 [P] [B-MODEL] 创建 EvaluationRun / IntentTestSession / IntentTestMessage ORM 模型
  - 文件: `backend/app/models/evaluation.py` (47 行), `backend/app/models/test_session.py` (57 行)
  - 依据: dd/dd-intent-library.md §1.10~§1.12
  - ✅ 已实现
- [x] T016 [P] [B-MODEL] 创建全部 Pydantic Schema (Request/Response) 用于上述实体
  - 文件: `backend/app/schemas/intent_library.py` (346 行)
  - 依据: ad/ad-intent-library.md §3 请求/响应示例
  - ✅ 已实现: 统一在 intent_library.py，包含 Library/Model/Dataset/Intent/Slot/Session 全部 schemas
- [x] T017 [B-MODEL] 生成 Alembic 迁移并运行 (intent_libraries, model_versions, datasets, intents, slots, entities, evaluations, test_sessions 等表)
  - 文件: `backend/migrations/versions/8c578b45942c_002_intent_library_module.py`
  - ✅ 已实现: 12 张表全部创建

### 服务层（来自 DD 算法）

- [x] T018 [B-SERVICE] 指令库 CRUD 服务 (含 library_key 唯一性校验, 语种约束)
  - 文件: `backend/app/services/intent_library_service.py` (231 行)
  - 依据: dd/dd-intent-library.md §4.1
  - ✅ 已实现: CRUD, search, language filters, total_zh/total_en, delete guard
- [x] T019 [B-SERVICE] 模型版本管理服务 (状态机转移, 上限校验 max=5, testable/published 互斥)
  - 文件: `backend/app/services/model_version_service.py` (272 行)
  - 依据: dd/dd-intent-library.md §3 状态机 + §4.2
  - ✅ 已实现: 完整状态机, MAX_NON_ARCHIVED=5, start_training, complete_training, start_evaluation, set_testable, publish, archive, restore
- [x] T020 [B-SERVICE] 数据集管理服务 (CRUD + Excel 导入导出 + 1:1 训练集绑定)
  - 文件: `backend/app/services/dataset_service.py` (200 行)
  - 依据: dd/dd-intent-library.md §4.3
  - ✅ 已实现: CRUD + pagination + delete guard; ⚠️ Excel 导入导出尚未实现
- [x] T021 [B-SERVICE] 意图/词槽/实体/相似问/排除问 CRUD 服务
  - 文件: `backend/app/services/intent_data_service.py` (314 行)
  - 依据: dd/dd-intent-library.md §4.4~§4.5
  - ✅ 已实现: Intent, Slot, SlotEntity, SimilarQuestion, NegativeExample 全部 CRUD + _update_dataset_counts
- [x] T022 [B-SERVICE] LLM 数据生成服务 (训练集/评估集 LLM 合成)
  - 文件: `backend/app/services/data_generation_service.py` (245 行)
  - 依据: dd/dd-intent-library.md §4.6 LLM 数据生成算法
  - ✅ 已实现: generate_training_data + generate_evaluation_data + _call_llm (AsyncOpenAI), API 端点 POST /datasets/{id}/generate-training + POST /eval-datasets/{id}/generate
- [x] T023 [B-SERVICE] 模型训练服务 (JointBERT 训练流水线 + ONNX 导出)
  - 文件: `backend/app/services/training/trainer.py` (358 行) + `exporter.py` (100 行) + `joint_model.py` (41 行) + `data_prep.py` (254 行)
  - 依据: dd/dd-intent-library.md §4.7 训练流水线算法
  - ✅ 已实现: 真实 PyTorch 训练 + ONNX 导出 + 产物打包, 集成测试通过
- [x] T024 [B-SERVICE] 模型评估服务 (批量评估执行 + 智能分析生成)
  - 文件: `backend/app/services/training/evaluator.py` (279 行)
  - 依据: dd/dd-intent-library.md §4.8 评估算法
  - ✅ 已实现: 批量推理 + intent/slot F1 + confusion pairs + slot errors
- [x] T025 [B-SERVICE] 模型推理服务 (意图分类 + 槽位提取 ONNX Runtime)
  - 文件: `backend/app/services/inference/engine.py` (200 行) + `model_cache.py` (31 行)
  - 依据: dd/dd-intent-library.md §4.9 推理算法
  - ✅ 已实现: ONNX Runtime 推理, classify_intent + extract_slots + BIO 解码, LRU 缓存
- [x] T026 [B-SERVICE] 测试会话管理服务 (单条测试 + 会话 CRUD + 消息管理)
  - 文件: `backend/app/services/test_session_service.py` (167 行)
  - 依据: dd/dd-intent-library.md §4.10
  - ✅ 已实现: create/list/update/delete sessions, send_message 调用真实推理

### API 端点（来自 AD 接口契约）

- [x] T027 [B-API] 指令库 CRUD API: GET/POST /intent-libraries, GET/PUT/DELETE /intent-libraries/{id}
  - 文件: `backend/app/api/v1/intent_libraries.py` (79 行)
  - 依据: ad/ad-intent-library.md §3.1
  - ✅ 已实现
- [x] T028 [B-API] 模型版本 API: GET/POST /models, POST /models/{id}/train|evaluate|set-testable|publish|archive|restore, GET /models/{id}/download
  - 文件: `backend/app/api/v1/model_versions.py` (170 行)
  - 依据: ad/ad-intent-library.md §3.2
  - ✅ 已实现: 全部生命周期端点 + download
- [x] T029 [B-API] 数据集 API: CRUD + import/export + LLM generate
  - 文件: `backend/app/api/v1/datasets.py` (130 行)
  - 依据: ad/ad-intent-library.md §3.3
  - ✅ 已实现: CRUD + generate-training/generate-evaluation 端点完成; ⚠️ Excel import/export 端点未实现
- [x] T030 [B-API] 意图/词槽/实体/相似问/排除问 API
  - 文件: `backend/app/api/v1/intents.py` (284 行)
  - 依据: ad/ad-intent-library.md §3.4~§3.6
  - ✅ 已实现: 全部 CRUD 端点
- [x] T031 [B-API] 测试会话与消息 API
  - 文件: `backend/app/api/v1/intent_testing.py` (88 行)
  - 依据: ad/ad-intent-library.md §3.7
  - ⚠️ 历史记录：当前文件仅覆盖 sessions CRUD + send_message + list_messages；标准批量测试/test-run/analysis 不在该文件内

## 前端任务

### 页面（来自 PD 交互原型）

- [x] T032 [F-PAGE] 指令库列表页: 搜索+筛选+Table+统计卡片+新建弹窗+编辑弹窗+删除确认
  - 文件: `frontend/src/pages/IntentLibrary/index.jsx` (526 行)
  - 依据: pd-all/pd-intent-library/index.html
  - ✅ 已实现: 4 统计卡 + 筛选栏 + 表格 + CRUD 弹窗 + DangerConfirmModal
  - PD UI Checklist:
    - [x] 4 统计卡片: 总库数量、已发布 (绿)、训练中 (蓝)、即将满额 (黄, ≥4/5)
    - [x] 筛选栏: 名称/Key 搜索 (Input+SearchOutlined)、语种 (Select: zh/en)、状态 (Select: published/draft)、查询/重置按钮
    - [x] 表格列: 名称/ID (a链接+mono id)、Library Key (Tag blue)、语种、模型数量 (Progress, ≥4 exception)、意图数、状态 (Tag+Icon)、更新时间、操作
    - [x] 操作列: 查看 (link→详情)、编辑 (link, 权限Tooltip)、删除 (link danger, published禁用+权限Tooltip)
    - [x] 页面头部按钮: 新建指令库 (primary)、导入
    - [x] 新建指令库弹窗: name, library_key, language (Select), description
    - [x] 编辑弹窗: name/description 可编辑; library_key/language 只读 (disabled)
    - [x] 删除确认: Modal.confirm, published 状态禁止删除
- [x] T033 [F-PAGE] 指令库详情页: 基本信息+模型版本列表+状态Tag+训练/评估/发布/归档操作弹窗
  - 文件: `frontend/src/pages/IntentLibrary/Detail.jsx` (612 行)
  - 依据: pd-all/pd-intent-library/detail.html
  - ✅ 已实现: breadcrumb + Descriptions + model table + 操作弹窗
  - PD UI Checklist:
    - [x] 页面头部: 返回按钮、库名称+Key Tag+语种、数据集按钮、新建训练 (primary)
    - [x] 训练操作卡片: 新建训练任务 (primary)、导入数据集
    - [x] 发布操作卡片: 发布模型 (primary danger, 仅有testable时可用)、归档版本、下载模型
    - [x] 模型版本列表表格: 版本、状态 (Badge 7态)、F1-Score、训练数据集 (Tag)、创建时间、操作
    - [x] 模型行操作: 发布 (仅testable)、测试 (testable/published)、归档 (danger link, Modal.confirm)
    - [x] 训练弹窗: 任务名称、选择训练集 Select
    - [x] 发布确认弹窗: 危险Alert、版本对比、Checkbox "我已确认"、倒计时
    - [ ] 关联数据集表格: 数据集列表 (⚠️ 在详情页中未直接渲染，需通过导航到数据集页)
- [x] T034 [F-PAGE] 数据集管理页: 数据集列表+训练集/评估集区分+导入导出+LLM生成
  - 文件: `frontend/src/pages/IntentLibrary/Placeholder.jsx` → DatasetsPage (≈ 行 83-419)
  - 依据: pd-all/pd-intent-library/datasets.html
  - ⚠️ 历史记录：当前已补齐训练/评估集同页展示、按类型分流 CRUD、LLM 合成真实接口；筛选栏和 Excel 导入导出仍未闭环
  - PD UI Checklist:
    - [ ] 筛选栏: 名称/ID搜索、类型 Select、绑定状态 Select、查询/重置
    - [x] 表格列: 名称/ID、类型 (Tag)、样本数 (Progress)、意图数、绑定模型、创建时间、操作
    - [x] 操作列: 管理数据 (跳转dataset-detail)、下载、删除 (绑定时disabled)
    - [ ] 页面头部按钮: 仍未完全拆成训练/评估集双入口，当前为统一入口 + 类型化数据集选择
    - [x] LLM合成弹窗: LLM模型Select、样本数Slider、提示词TextArea + 真实目标数据集选择
    - [ ] 文件上传弹窗: Excel 上传/导出仍未闭环
- [x] T035 [F-PAGE] 数据集详情页: 意图/词槽/实体/相似问/排除问 Tab管理+行内编辑
  - 文件: `frontend/src/pages/IntentLibrary/Placeholder.jsx` → DatasetDetailPage (≈ 行 436-1056)
  - 依据: pd-all/pd-intent-library/dataset-detail.html
  - ✅ 已实现: 5 统计卡 + Tabs (意图/词槽) + 意图表格 + 配置抽屉
  - PD UI Checklist:
    - [x] 5 统计卡片: 意图总数、词槽总数、实体值总数、相似问总数、排除问总数
    - [x] 页面头部: 返回按钮、数据集名称Tag+类型
    - [x] 顶级 Tabs: 意图列表 / 词槽与实体
    - [x] 意图列表表格: 英文标识、中文名、描述、词槽、追问、相似问、排除问、操作
    - [x] 意图行操作: 配置 (抽屉)、相似问 (抽屉)、复制、删除
    - [x] 意图配置抽屉: intent_key、name_zh、description、词槽引用、追问、命中/未命中话术
    - [x] 相似问管理抽屉: Tabs (相似问/排除问)、列表项、添加按钮
    - [x] 词槽卡片组: 系统/自定义词槽
- [x] T036 [F-PAGE] 模型测试页: 单条测试(聊天界面)+批量测试任务+测试结果+智能分析报告
  - 文件: `frontend/src/pages/IntentLibrary/Placeholder.jsx` → ModelTestPage (≈ 行 1664-2310)
  - 依据: pd-all/pd-intent-library/test.html
  - ⚠️ 历史记录：当前已补齐单条测试消息链路与 Debug 面板；BatchTestTab 仍是前端逐条会话校验，尚未对齐标准批量评估/智能分析闭环
  - PD UI Checklist:
    - [x] 顶级 Tabs: 单条测试 / 批量测试
    - [x] 单条测试-会话面板: 新建会话、会话列表、删除
    - [x] 单条测试-模型信息栏: 版本Tag、状态、Debug Tag
    - [x] 单条测试-消息区: 用户消息+Bot消息+时间戳+空会话引导
    - [x] 单条测试-Debug面板: 意图Tag、置信度、槽位列表、耗时
    - [x] 单条测试-输入区: TextArea + 发送按钮
    - [x] 批量测试任务入口: 真实 `batch-tests` 创建/导入/执行闭环
    - [x] 批量测试跳转详情: `/batch-test/{id}` 读取真实状态 / runs / analysis
    - [x] 智能分析报告入口: 详情页按真实分析接口展示空态或结果

### 组件（可复用）

- [x] T037 [P] [F-COMPONENT] 模型状态Tag组件 (draft/training/trained/evaluating/testable/published/archived 颜色映射)
  - 文件: `frontend/src/components/ModelStatusTag.jsx` (25 行)
  - ✅ 已实现
- [x] T038 [P] [F-COMPONENT] 危险操作确认弹窗组件 (倒计时+勾选+影响说明)
  - 文件: `frontend/src/components/DangerConfirmModal.jsx` (122 行)
  - ✅ 已实现: checkbox "我已了解影响" + 3 秒倒计时

### 状态管理与 API 对接

- [x] T040 [F-STORE] 指令库状态管理 (zustand): 列表/筛选/当前库/模型版本
  - 文件: `frontend/src/stores/intentLibraryStore.js` (172 行)
  - ✅ 已实现: libraries, loading, pagination, search, languageFilter, currentLibrary, models, 全部 CRUD actions + AbortController
- [x] T041 [F-API] 指令库 API 对接层: 全部 57 端点的前端调用封装
  - 文件: `frontend/src/services/intentLibraryApi.js` (61 行)
  - ✅ 已实现: libraries/models/datasets/intents/slots/entities/similar-questions/negative-examples/test-sessions/messages

## 当前收口检查点

**模块验收标准**（对照 PD 交互稿）:
- [ ] 全量验收通过
  - 当前仅有本轮局部证据：`test_datasets_api.py`、`test_model_lifecycle.py`、`test_intent_testing_api.py`、`src/pages/IntentLibrary/*.test.js`、登录后 smoke
- [x] 指令库列表页: 搜索/筛选/CRUD 主链路可用
- [x] 模型生命周期: 核心状态流转与评估集生成防串库已有验证证据
- [ ] 数据集管理: 训练集/评估集 LLM 生成可用且导入导出闭环
  - 当前状态：LLM 生成与统一列表已验证；Excel 导入/导出仍 `Deferred`
- [x] 单条测试: 会话创建/消息发送/结果展示可用（调用真实 ONNX 推理）
- [x] 模型上限 5 的约束生效
- [x] testable/published 库内互斥正确
- [x] 批量测试 / 智能分析闭环可验
  - 当前证据：`test_batch_tests_api.py`、`test_batch_service.py`、`test_batch_executor.py`、`test_case_service.py`、真实环境 smoke（创建 batch / 导入 cases / 执行 / `/batch-test/{id}` 打开详情页）
