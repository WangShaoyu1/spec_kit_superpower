# 任务文件: `pd-intent-library`

**输入**: `specs/master/pd-all/pd-intent-library/` + `specs/master/ad/ad-intent-library.md` + `specs/master/dd/dd-intent-library.md` + `specs/master/plans/plan-intent-library.md`  
**前置依赖**: `pd-user-mgmt = browser_verified`  
**TDD 约束**: 先写失败测试，再写最小实现，再验证通过  
**风险提示**: `FR-050 Partial` 必须持续可见，不得在实现中掩盖

## 任务总览

- 总任务数: 12
- 测试任务: 5
- 后端任务: 4
- 前端任务: 3

## 任务列表

### Task 1. 后端契约测试: 指令库目录与创建
- [x] 新增 `backend/tests/contract/test_intent_library_api.py`
- [x] 先写 `list/create library` 的失败测试，覆盖唯一 key、默认阈值与列表回读
- [x] 运行定向 pytest，确认失败原因正确
- [x] 在 `backend/app/models.py` 与 `backend/app/main.py` 补最小实现
- [x] 重新运行定向 pytest，确认通过

### Task 2. 后端契约测试: 详情、数据集与下载元数据
- [x] 在 `test_intent_library_api.py` 增加详情/数据集/下载元数据失败测试
- [x] 运行失败测试，确认缺失接口或字段
- [x] 补齐实体与接口最小实现
- [x] 回归该测试文件

### Task 3. 后端集成测试: 训练状态机
- [x] 新增/补充 `backend/tests/test_intent_library_flow.py`
- [x] 写失败测试覆盖 `draft -> training -> trained`
- [x] 运行失败测试
- [x] 实现训练任务刷新逻辑、模型上限和训练集绑定规则
- [x] 回归通过

### Task 4. 后端集成测试: 评估快照与发布唯一性
- [x] 在 `test_intent_library_flow.py` 写失败测试覆盖阈值快照、`testable/published` 唯一性
- [x] 运行失败测试
- [x] 实现评估结果回写、发布切换和下载元数据
- [x] 回归通过

### Task 5. 后端契约测试: 单条测试与分析回读
- [x] 在 `test_intent_library_api.py` 写失败测试覆盖 `single test`、批量评估结果字段
- [x] 运行失败测试
- [x] 实现单条测试接口与分析返回
- [x] 回归通过

### Task 6. 前端消费契约测试: API 适配层
- [x] 扩展 `frontend/src/services/api.js`
- [x] 新增或补充 `frontend/src/services/api.intent-library.test.js`
- [x] 先写失败测试，覆盖列表、创建、训练、评估、发布、测试请求形态
- [x] 补最小实现并回归 Vitest

### Task 7. 前端页面测试: 指令库页面骨架
- [x] 新增 `frontend/src/modules/intent-library/IntentLibraryPage.jsx`
- [x] 新增 `frontend/src/modules/intent-library/IntentLibraryPage.test.jsx`
- [x] 先写失败测试，覆盖加载列表、创建弹窗、选择库详情
- [x] 最小实现页面骨架并回归 Vitest

### Task 8. 前端页面测试: 训练/评估/发布操作
- [x] 在 `IntentLibraryPage.test.jsx` 增加失败测试，覆盖训练、评估、发布、下载元数据展示
- [x] 运行失败测试
- [x] 补详情区与测试区交互，所有关键动作后强制回读
- [x] 回归 Vitest

### Task 9. 前端壳层接入
- [x] 修改 `frontend/src/App.jsx`、`frontend/src/app/AppShell.jsx`
- [x] 打通 `/intent-library` 路由与菜单导航
- [x] 回归已有登录和 user-mgmt 测试，避免回归

### Task 10. Harness 文档与门禁
- [x] 跑 `plan/tasks` 相关 stage gate
- [x] 更新 `.specify/harness/module-state.json` 至 `tasks_ready` / `implementing`
- [x] 记录 `FR-050 Partial` warning 仍存在但无 blocker

### Task 11. Browser smoke
- [x] 启动本地前后端
- [x] 验证 `training_state_transition`
- [x] 验证 `batch_eval_feedback`
- [x] 验证 `result_readback`

### Task 12. 缺陷修复与模块收口
- [x] 修复 smoke/review 发现的问题
- [x] 跑后端 pytest、前端 vitest、最近编辑文件 lints
- [x] 更新模块状态到 `browser_verified`
- [x] 为下一模块保留顺推条件

## 完成定义

- [x] 指令库可创建且 `library_key` 唯一
- [x] 数据集、模型、评估结果和下载元数据均来自真实后端回读
- [x] 模型状态可完成训练、评估、发布闭环
- [x] 单条测试返回意图、置信度、槽位和耗时
- [x] `FR-050 Partial` 仍明确保留
- [x] browser smoke 通过且模块状态推进完成
