# E2E 功能场景与 spec 验收场景映射

**目的**: 确保端到端测试与 `specs/master/spec.md` 中用户故事验收场景一一对应，功能测试覆盖所有功能场景而不仅是接口通。

---

## 一、测试文件与运行方式

| 文件 | 说明 |
|------|------|
| `backend/tests/e2e/test_pm_workflow.py` | PM 全流程（意图→方案→测试会话→发布→设备调用）、SC-007/SC-002 时效 |
| `backend/tests/e2e/test_functional_scenarios.py` | 各用户故事单条验收场景的 API 级 E2E |

运行（需 DB 迁移 + init_db 或 conftest 提供 test DB + admin）：

```bash
cd smartchef-platform/backend
pytest tests/e2e/ -v
```

若出现 **Event loop is closed** 等异步 fixture 问题，可先单条验证：  
`pytest tests/e2e/test_functional_scenarios.py::test_us1_create_intent_with_slot -v`  
待 conftest 的 async 作用域修复后，再全量运行。

---

## 二、用户故事 → 验收场景 → 测试用例

| 用户故事 | spec 验收场景摘要 | 对应测试用例 |
|----------|-------------------|--------------|
| **US1** 指令配置管理 | 1. 创建指令「设置烹饪时间」+ 槽位 duration，列表可见 | `test_us1_create_intent_with_slot` |
| US1 | 2. 编辑「启动烹饪」提示词/训练数据，保存成功 | 合约 test_intents_api / test_training_data_api |
| US1 | 3. 删除「调高音量」，列表移除、训练数据清理 | 合约 test_delete_intent |
| US1 | 4. 按分类筛选「烹饪控制」 | `test_us1_list_intents_filter_by_category` |
| **US2** 知识库管理 | 1. 上传菜谱文档，解析索引，列表可见 | `test_us2_create_knowledge_base_and_list` + 合约 test_knowledge_api |
| US2 | 2. 搜索「银耳汤」命中菜谱 | 集成 test_knowledge_indexing / 手工 |
| US2 | 3. JSON 过滤无效字段 | 集成 test_json_parse_* |
| US2 | 4. 分类管理 | 知识库 API + 前端 |
| **US3** 对话方案 | 1. 创建方案 A（LLM+人设），保存成功 | `test_us3_create_profile_and_publish` |
| US3 | 2–3. 方案 A/B 手动测试同问句，回复差异 | test_pm_workflow + 手工 |
| US3 | 4. 发布方案 B，设备切换、会话重置 | `test_pm_workflow` 步骤 6–7、`test_us3_*` |
| **US4** 手动测试 | 1. 发送「设置温度180度」，调试面板完整链路 | `test_us4_test_session_and_chat_debug_info` |
| US4 | 2–5. 知识问句、设备上下文、指代、会话隔离 | 集成 test_nlu_pipeline / test_reference_resolution |
| **US5** 设备端指令 | 1–6. 开始烹饪/加热/槽位追问/多表达/英文 | test_pm_workflow 步骤 7、集成 test_nlu_pipeline |
| **US6** 知识问答与闲聊 | 1–5. 知识命中、未命中闲聊、联网、人设、英文 | 集成 test_knowledge_qa、test_chitchat |
| **US7** 路由与上下文 | 1–5. 路由策略、指代、跨域、设备隔离、版本重置 | 集成 test_router、test_reference_resolution、test_cross_domain |
| **US8** 批量测试 | 1–5. 自动生成用例、执行、报告、智能分析 | `test_us8_batch_test_create_job_and_cases` + 合约 test_batch_test_api |
| **US9** 监控与设备日志 | 1–5. 仪表盘指标、设备会话、单轮链路、告警、筛选 | `test_us9_monitoring_stats_and_logs` + 合约 test_monitoring_api |
| **US10** 角色权限 | 1–3. 管理员登录、创建受限角色、修改权限 | `test_us10_update_role_permissions` + 集成 test_rbac |

---

## 三、已修复的页面/接口问题

| 问题 | 处理 |
|------|------|
| 角色编辑：前端调用 `PUT /auth/roles/:id`，后端无此路由 | 后端新增 `PATCH /auth/roles/{role_id}` 与 `auth_service.update_role`，前端改为 `api.patch` |

---

## 四、未覆盖或需手工/Playwright 的验收

- 前端页面实际渲染与交互（如「调试面板展示路由/意图/槽位」需浏览器或 Playwright）。
- 知识库上传文件后「可搜索到银耳汤」依赖真实索引与检索，可放在集成测试或手工。
- 批量测试「智能分析报告」内容与图表需前端 E2E 或手工核对。

以上在表中已标注为「合约/集成/手工」，E2E 以 API 级覆盖为主，确保所有功能场景均有至少一条自动化或可执行验证路径。
