# SmartChef 需求追溯矩阵

**评价日期**: 2026-03-10  
**基准**: `specs/master/spec.md`（FR-001～FR-038、SC-001～SC-013、US1～US10）

---

## 一、功能需求（FR）追溯

| FR 编号 | 描述摘要 | 实现位置（后端/前端） | 状态 |
|---------|----------|------------------------|------|
| FR-001 | 角色权限管理、管理员账号 | `app/api/v1/auth.py`、`app/api/v1/users.py`、`app/services/auth_service.py`、前端 UserManager、RoleEditor | 实现 |
| FR-002 | 指令增删改查、槽位定义 | `app/api/v1/intents.py`、`app/models/intent.py`、`app/services/intent_service.py`、IntentManager、SlotEditor | 实现 |
| FR-003 | 指令提示词与训练数据编辑 | `app/schemas/intent.py`、TrainingDataEditor、合约 test_training_data_api | 实现 |
| FR-004 | 知识库文档上传（JSON/Markdown）、解析索引 | `app/api/v1/knowledge.py`、`app/services/knowledge/parser.py`、indexer.py、KnowledgeBase、DocumentUpload | 实现 |
| FR-005 | 过滤无效字段 | `app/services/knowledge/parser.py`、集成 test_knowledge_indexing | 实现 |
| FR-006 | 知识库分类管理 | `app/models/knowledge.py`、knowledge API、前端 KnowledgeBase | 实现 |
| FR-007 | 多对话方案、大模型/人设/路由配置 | `app/api/v1/profiles.py`、`app/models/dialog_profile.py`、DialogProfile、ModelSelector | 实现 |
| FR-008 | 闲聊人设自定义 | `app/models/dialog_profile.py`（Persona）、PersonaEditor | 实现 |
| FR-009 | 手动单条对话测试、会话隔离 | `app/api/v1/testing.py`、`app/services/testing/manual_test.py`、ManualTest、TestChat | 实现 |
| FR-010 | 手动测试完整调试信息 | DebugPanel、manual_test 返回 debug_info | 实现 |
| FR-011 | 模拟设备上下文 | DeviceContextSimulator、device_context 入参 | 实现 |
| FR-012 | 批量测试、自动生成用例 | `app/api/v1/batch_test.py`、case_generator、BatchTest 页面 | 实现 |
| FR-013 | 批量测试用例模板字段 | `app/schemas/test_suite.py`、batch_test 服务 | 实现 |
| FR-014 | 智能分析报告 | `app/services/testing/analyzer.py`、AnalysisReport 组件 | 实现 |
| FR-015 | 版本发布、单版本生效 | `app/api/v1/versions.py`、`app/services/version/publisher.py`、Versions 页面 | 实现 |
| FR-016 | 发布后设备切换、会话重置 | publisher 清除会话、loader 加载活跃版本 | 实现 |
| FR-017 | API 接收文本与设备上下文、统一响应 | `app/api/v1/device.py`（/dialog/chat）、pipeline、response_builder | 实现 |
| FR-018 | 可配置路由策略 | `app/services/nlu/router.py`、DialogProfile.routing_strategy | 实现 |
| FR-019 | 指令域结构化输出、高风险二次确认 | response_builder、dialog_manager | 实现 |
| FR-020 | 渐进式错误处理（3 级） | `app/services/nlu/dialog_manager.py`（单元 test_progressive_error_level_*） | 实现 |
| FR-021 | 知识域检索、未命中降级闲聊 | pipeline、retriever、qa_generator | 实现 |
| FR-022 | 闲聊人设、联网内容 | llm_adapter、persona、web_search | 实现 |
| FR-023 | 会话按设备隔离、指代/省略、超时 | device_session、context、reference_resolver | 实现 |
| FR-024 | 中英文检测与回复 | preprocessor（语言检测）、response_builder | 实现 |
| FR-025 | 英文训练数据翻译 | scripts/translate_training_data.py | 实现 |
| FR-026 | 统一响应格式（三域） | response_builder、schemas | 实现 |
| FR-027 | 小模型+大模型、Jetson 可运行 | pipeline（intent_classifier ONNX）、research 决策；device-inference 可选 | 部分（云端已实现，设备端 C++ 可选） |
| FR-028 | 小模型共用、方案独立配大模型 | loader、profiles | 实现 |
| FR-029 | Brave Search 联网 | `app/services/chitchat/web_search.py` | 实现 |
| FR-030 | 监控仪表盘核心指标 | `app/api/v1/monitoring.py`、metrics、Dashboard | 实现 |
| FR-031 | 按设备 ID 历史会话 | log_query、DeviceLogs | 实现 |
| FR-032 | 单会话每轮完整链路 | log_query、请求日志详情 | 实现 |
| FR-033 | 每次请求结构化日志 | log_writer、RequestLog 模型 | 实现 |
| FR-034 | 日志多维筛选 | log_query、monitoring API | 实现 |
| FR-035 | 告警规则配置与触发 | alert_rule 模型、alerting、AlertRules 页面 | 实现 |
| FR-036 | 敏感数据 AES-256、DB TLS | `app/core/encryption.py` | 实现 |
| FR-037 | 设备维度数据导出/删除、GDPR | `app/api/v1/data_management.py` | 实现 |
| FR-038 | 仪表盘 30 秒轮询、手动刷新 | 前端 Dashboard 轮询 | 实现 |

**汇总**: 实现 36，部分 1（FR-027 设备端 C++），未实现 0。

---

## 二、成功标准（SC）验证

| SC 编号 | 成功标准摘要 | 验证方式 | 实际数据/结果 |
|---------|--------------|----------|----------------|
| SC-001 | 指令意图准确率 ≥ 95%，39 意图 | 批量测试 / evaluate_model | 需在已发布版本+模型下运行后填写 |
| SC-002 | 指令类 P95 延迟 < 200ms | 压测 / 集成测试打点 | 需运行延迟采样脚本后填写 |
| SC-003 | 知识/闲聊 2～4s | 集成测试或手工 | 需运行后填写 |
| SC-004 | 同一意图 10+ 表达正确识别 | 训练数据覆盖+批量测试 | 依赖训练数据与模型 |
| SC-005 | 中英双语、自动检测回复 | 单元 test_preprocessor 语言检测、集成 test_nlu_pipeline 英文 | 单元通过 |
| SC-006 | 10 QPS 并发、设备隔离 | 压测 | 需运行后填写 |
| SC-007 | PM 全流程 ≤ 1h | E2E test_pm_workflow、quickstart_verify | 需后端+DB 运行时执行 |
| SC-008 | 智能分析根因识别 ≥ 80% | 批量测试报告抽样 | 需运行后填写 |
| SC-009 | 迭代准确率可度量 | 批量测试对比 | 功能已实现 |
| SC-010 | 小模型 Jetson Nano 运行 | device-inference C++（可选） | N/A（V1 未实现设备端） |
| SC-011 | 按设备 ID 查会话与链路 | 合约 test_monitoring_api、DeviceLogs | 合约/集成需清洁 DB |
| SC-012 | 仪表盘指标、告警可配置 | monitoring API、AlertRules | 实现 |
| SC-013 | 敏感数据加密、导出/删除 API | 集成测试、data_management API | 实现 |

---

## 三、用户故事验收映射

| 用户故事 | 验收场景摘要 | 对应测试/验证方式 |
|----------|--------------|--------------------|
| US1 | 创建指令+槽位、列表可见 | contract test_intents_api、E2E |
| US1 | 编辑指令提示词/训练数据 | contract test_training_data_api |
| US1 | 删除指令及关联数据 | test_intents_api |
| US1 | 按分类筛选指令 | test_intents_api test_list_intents_filter_by_category |
| US2 | 上传菜谱文档、解析索引、可搜索 | contract test_knowledge_api、integration test_knowledge_indexing |
| US2 | 上传 JSON 过滤无效字段 | test_upload_json_document_filters_invalid_fields、test_json_parse_* |
| US2 | 分类管理 | knowledge API、前端 |
| US3 | 创建方案 A/B、不同配置、手动测试差异 | contract test_profiles_api、E2E |
| US3 | 发布方案、设备切换 | contract test_device_api、E2E |
| US4 | 发送指令、调试面板完整链路 | contract test_manual_test_api test_chat_returns_debug_info |
| US4 | 设备上下文、剩余时间理解 | 集成 NLU、手动 |
| US4 | 指代「收藏它」、会话隔离 | integration test_reference_resolution、test_pm_workflow |
| US5 | 设备 API 意图+回复、< 200ms | integration test_nlu_pipeline、性能脚本 |
| US5 | 槽位缺失追问、补全 | unit test_dialog_manager、integration |
| US5 | 同意图多表达、英文 | test_stop_cooking_synonyms、test_english_start_cooking |
| US6 | 知识命中、未命中闲聊、联网 | integration test_knowledge_qa、test_chitchat |
| US7 | 路由策略、指代/省略、跨域、设备隔离 | test_router、test_reference_resolution、test_cross_domain |
| US8 | 批量生成用例、执行、智能报告 | contract test_batch_test_api、BatchTest 页面 |
| US9 | 监控仪表盘、设备会话、单轮链路、告警 | contract test_monitoring_api、Dashboard、DeviceLogs、AlertRules |
| US10 | 管理员/受限角色、菜单权限 | integration test_rbac、UserManager、RoleEditor、Sidebar |

---

## 四、意图覆盖（config.json 39 个）

意图清单已从 `temp_data/config.json` 提取，共 **39** 个。后台意图管理支持 CRUD 及导入；NLU 使用当前发布版本加载的意图配置进行识别。是否全部 39 个均已在后台配置并参与训练/推理，需在环境中核对「意图列表 API」或种子数据。

| 状态 | 说明 |
|------|------|
| 配置结构支持 | 是（intent_key、slots、training_data 等与 config 对应） |
| 39 个均已在库 | 需在运行环境查询意图列表确认 |
| NLU 识别覆盖 | 依赖已发布版本与模型训练数据 |

---

## 五、缺口与备注

- **测试环境**：合约/集成测试当前因 **async 事件循环与 DB 会话/表已存在** 导致大量 ERROR，非功能缺失。建议：使用独立测试库或 fixture 每次建表/清理、统一 async fixture 作用域。
- **ruff**：当前环境未安装 ruff，代码质量静态检查未执行；可在 `pip install -e ".[dev]"` 后执行 `ruff check app/`。
- **性能与准确率**：SC-001/002/003/006/007 需在**后端+DB+Redis+可选模型**运行后，用报告中的脚本与测试产出实际数据填入上表。
- **设备端 C++**：FR-027/SC-010 设备端推理为 V1 可选，标为部分/N/A。
