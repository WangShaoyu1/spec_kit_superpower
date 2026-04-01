# 任务文件: `pd-monitoring`

**输入**: `specs/master/pd-all/pd-monitoring/` + `specs/master/ad/ad-monitoring.md` + `specs/master/dd/dd-monitoring.md` + `specs/master/plans/plan-monitoring.md`  
**前置依赖**: `pd-batch-test = browser_verified`、`tasks-refinement = completed`  
**TDD 约束**: 先写失败测试，再写最小实现，再验证通过  
**风险提示**: 不得伪造 overview 指标、会话链路或告警触发

## 任务总览

- 总任务数: 12
- 测试任务: 5
- 后端任务: 4
- 前端任务: 3

## 任务列表

### Task 1. 后端契约测试: overview 指标与最近告警
- [x] 新增 `backend/tests/contract/test_monitoring_api.py`
- [x] 先写 `overview` 失败测试，覆盖指标卡、路由分布、最近告警字段
- [x] 运行定向 pytest，确认失败原因正确
- [x] 在 `backend/app/models.py` 与 `backend/app/api/monitoring.py` 补最小实现
- [x] 重新运行定向 pytest，确认通过

### Task 2. 后端契约测试: 请求日志筛选与分页
- [x] 在 `test_monitoring_api.py` 增加日志筛选、分页结构、空态与错误码失败测试
- [x] 运行失败测试，确认接口与字段缺口
- [x] 补齐 `request-logs` 查询最小实现
- [x] 回归该测试文件

### Task 3. 后端契约测试: 设备会话与 trace 详情
- [x] 在 `test_monitoring_api.py` 增加 `device-sessions`、`session detail` 失败测试
- [x] 运行失败测试
- [x] 实现设备会话聚合与逐轮链路回读
- [x] 回归通过

### Task 4. 后端集成测试: 告警规则与事件收敛
- [x] 新增 `backend/tests/test_monitoring_flow.py`
- [x] 写失败测试覆盖规则创建、停用、触发事件、恢复关闭
- [x] 运行失败测试
- [x] 实现 `alert_rule` / `alert_event` 与 evaluator
- [x] 回归通过

### Task 5. 后端契约测试: 结构化日志口径
- [x] 在 `test_monitoring_api.py` 写失败测试覆盖 request/response trace 字段完整性
- [x] 运行失败测试
- [x] 修正 `request_log` 序列化与详情返回
- [x] 回归通过

### Task 6. 前端消费契约测试: API 适配层
- [x] 扩展 `frontend/src/services/api.js`
- [x] 新增 `frontend/src/services/api.monitoring.test.js`
- [x] 先写失败测试，覆盖 overview、request-logs、session detail、alert-rules 请求形态
- [x] 补最小实现并回归 Vitest

### Task 7. 前端页面测试: 监控总览页骨架
- [x] 新增 `frontend/src/modules/monitoring/MonitoringDashboardPage.jsx`
- [x] 新增 `frontend/src/modules/monitoring/MonitoringDashboardPage.test.jsx`
- [x] 先写失败测试，覆盖指标加载、手动刷新、日志筛选
- [x] 最小实现页面骨架并回归 Vitest

### Task 8. 前端页面测试: 设备日志与 trace
- [x] 新增 `frontend/src/modules/monitoring/MonitoringDeviceLogsPage.jsx`
- [x] 新增 `frontend/src/modules/monitoring/MonitoringDeviceLogsPage.test.jsx`
- [x] 先写失败测试，覆盖设备搜索、会话列表、逐轮链路展示
- [x] 补详情页与交互，关键动作后强制回读

### Task 9. 前端页面测试: 告警规则
- [x] 新增 `frontend/src/modules/monitoring/MonitoringAlertRulesPage.jsx`
- [x] 新增 `frontend/src/modules/monitoring/MonitoringAlertRulesPage.test.jsx`
- [x] 先写失败测试，覆盖规则列表、新建/停用、最近事件展示
- [x] 补页面与交互，保存后强制回读

### Task 10. 前端壳层接入与 Harness 门禁
- [x] 修改 `frontend/src/App.jsx`、`frontend/src/app/AppShell.jsx`
- [x] 打通 `/monitoring`、`/monitoring/device-logs`、`/monitoring/alert-rules` 路由及菜单导航
- [x] 更新 `.specify/harness/module-state.json` 至 `tasks_ready` / `implementing`
- [x] 记录无 blocker，可进入实现

### Task 11. Browser smoke
- [x] 启动本地前后端
- [x] 验证 `overview_real_metrics`
- [x] 验证 `device_trace_drilldown`
- [x] 验证 `alert_rule_feedback`

### Task 12. 缺陷修复与模块收口
- [x] 修复 smoke/review 发现的问题
- [x] 跑后端 pytest、前端 vitest、最近编辑文件 lints
- [x] 更新模块状态到 `browser_verified`
- [x] 为下一步收口保留顺推条件

## 收口结果

- 后端补齐 `RequestLog` / `MonitoringAlertRule` / `MonitoringAlertEvent` 实体与监控路由，overview、日志筛选、会话 trace、规则治理全部回到统一响应信封
- 新增 `backend/tests/test_monitoring_flow.py`，把规则触发、停用与恢复关闭做成真实 evaluator 收敛，而不是静态告警样本
- 前端补齐 monitoring API 适配层与三张页面测试，关键动作后统一强制回读，避免本地 toast/状态冒充成功
- 浏览器 smoke 已验证 overview 真指标、设备会话回读，以及规则创建后列表刷新与停用开关回读；其中规则创建因 AntD `Select` 自动化限制采用 API 注入后做页面回读确认

## 检查点

- [x] `python -m pytest backend/tests/contract/test_monitoring_api.py backend/tests/test_monitoring_flow.py` 通过
- [x] `npm test -- src/services/api.monitoring.test.js src/modules/monitoring/MonitoringDashboardPage.test.jsx src/modules/monitoring/MonitoringDeviceLogsPage.test.jsx src/modules/monitoring/MonitoringAlertRulesPage.test.jsx` 通过
- [x] 最近编辑文件 lints 为 0
- [x] `.specify/harness/module-state.json` 已推进到 `browser_verified`

## 完成定义

- [x] overview 可真实展示请求量、QPS、延迟、准确率、路由分布与最近告警
- [x] 请求日志支持多维筛选与分页，结果结构统一
- [x] 设备会话与逐轮 trace 可真实回读
- [x] 告警规则可创建/停用，并能看到真实事件状态
- [x] browser smoke 通过且模块状态推进完成
