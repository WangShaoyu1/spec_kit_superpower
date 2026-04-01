# 任务文件: `pd-batch-test`

**输入**: `specs/master/pd-all/pd-batch-test/` + `specs/master/ad/ad-batch-test.md` + `specs/master/dd/dd-batch-test.md` + `specs/master/plans/plan-batch-test.md`  
**前置依赖**: `pd-dialog-profile = browser_verified`  
**TDD 约束**: 先写失败测试，再写最小实现，再验证通过  
**风险提示**: 不得伪造达标结果、准确率、耗时或智能分析建议

## 任务总览

- 总任务数: 12
- 测试任务: 5
- 后端任务: 4
- 前端任务: 3

## 任务列表

### Task 1. 后端契约测试: 批次目录与创建
- [x] 新增 `backend/tests/contract/test_batch_test_api.py`
- [x] 先写 `list/create batch` 失败测试，覆盖方案不存在、批次重名、状态统计
- [x] 运行定向 pytest，确认失败原因正确
- [x] 在 `backend/app/models.py` 与 `backend/app/api/batch_test.py` 补最小实现
- [x] 重新运行定向 pytest，确认通过

### Task 2. 后端契约测试: 用例生成与详情回读
- [x] 在 `test_batch_test_api.py` 增加生成用例、详情、结果字段失败测试
- [x] 运行失败测试，确认接口与字段缺口
- [x] 补齐 `generate-cases` 与详情接口最小实现
- [x] 回归该测试文件

### Task 3. 后端集成测试: 批次执行状态机
- [x] 新增 `backend/tests/test_batch_test_flow.py`
- [x] 写失败测试覆盖 `draft -> ready -> running -> completed/failed`
- [x] 运行失败测试
- [x] 实现执行引擎、状态推进与结果回写
- [x] 回归通过

### Task 4. 后端集成测试: 指标聚合与分析报告
- [x] 在 `test_batch_test_flow.py` 写失败测试覆盖 accuracy、response_p95_ms、分析报告生成
- [x] 运行失败测试
- [x] 实现指标聚合、混淆矩阵、失败归因与建议
- [x] 回归通过

### Task 5. 后端契约测试: 结果口径一致性
- [x] 在 `test_batch_test_api.py` 写失败测试覆盖 case_count / executed_count / result_count 一致性
- [x] 运行失败测试
- [x] 修正详情汇总和状态快照返回
- [x] 回归通过

### Task 6. 前端消费契约测试: API 适配层
- [x] 扩展 `frontend/src/services/api.js`
- [x] 新增 `frontend/src/services/api.batch-test.test.js`
- [x] 先写失败测试，覆盖列表、创建、生成用例、执行、详情请求形态
- [x] 补最小实现并回归 Vitest

### Task 7. 前端页面测试: 批次列表页骨架
- [x] 新增 `frontend/src/modules/batch-test/BatchTestPage.jsx`
- [x] 新增 `frontend/src/modules/batch-test/BatchTestPage.test.jsx`
- [x] 先写失败测试，覆盖列表加载、新建批次、状态统计
- [x] 最小实现页面骨架并回归 Vitest

### Task 8. 前端页面测试: 详情页结果与分析
- [x] 新增 `frontend/src/modules/batch-test/BatchTestDetailPage.jsx`
- [x] 新增 `frontend/src/modules/batch-test/BatchTestDetailPage.test.jsx`
- [x] 先写失败测试，覆盖结果表、执行入口、分析报告展示
- [x] 补详情页与交互，关键动作后强制回读

### Task 9. 前端壳层接入
- [x] 修改 `frontend/src/App.jsx`、`frontend/src/app/AppShell.jsx`
- [x] 打通 `/batch-test` 与 `/batch-test/:batchId` 路由及菜单导航
- [x] 回归已有登录、intent-library、knowledge-base、dialog-profile 测试，避免回归

### Task 10. Harness 文档与门禁
- [x] 跑 `plan/tasks` 相关 stage gate
- [x] 更新 `.specify/harness/module-state.json` 至 `tasks_ready` / `implementing`
- [x] 记录无 blocker，可进入实现

### Task 11. Browser smoke
- [x] 启动本地前后端
- [x] 验证 `case_count_consistency`
- [x] 验证 `latency_feedback`
- [x] 验证 `accuracy_feedback`

### Task 12. 缺陷修复与模块收口
- [x] 修复 smoke/review 发现的问题
- [x] 跑后端 pytest、前端 vitest、最近编辑文件 lints
- [x] 更新模块状态到 `browser_verified`
- [x] 为下一模块保留顺推条件

## 完成定义

- [x] 批次可创建并绑定被测对话方案
- [x] 用例总数、执行结果数与详情统计一致
- [x] 批次执行后可真实回读 accuracy、response_p95_ms 和 pass/fail
- [x] 智能分析报告展示混淆矩阵、失败归因和建议
- [x] browser smoke 通过且模块状态推进完成
