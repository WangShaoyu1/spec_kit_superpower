# SmartChef UI / 效果偏差清单

说明:
- `文档型偏差`: 能直接对照 `pd-template`、PD README 或 `spec.md`
- `派生型偏差`: 规范未明说，但与当前正式壳层的一致性或“真实回读”原则冲突

| 级别 | 类型 | 模块 | 偏差描述 | 证据 |
|------|------|------|----------|------|
| INFO | 文档型 | `monitoring` | 仪表盘此前缺少 30s 自动轮询，现已补齐并有前端测试锁定 | `frontend/src/modules/monitoring/MonitoringDashboardPage.jsx`, `src/modules/monitoring/MonitoringDashboardPage.test.jsx`, `specs/master/spec.md`, `specs/master/pd-all/pd-monitoring/README.md` |
| INFO | 文档型 | `monitoring` | 请求日志筛选已补时间范围、意图、耗时、异常等完整维度，并有前后端测试锁定 | `frontend/src/modules/monitoring/MonitoringDashboardPage.jsx`, `frontend/src/modules/monitoring/MonitoringDashboardPage.test.jsx`, `backend/app/api/monitoring.py`, `backend/tests/contract/test_monitoring_api.py` |
| INFO | 文档型 | `monitoring` | 设备会话列表已补 version 展示，并有页面回归测试覆盖 | `frontend/src/modules/monitoring/MonitoringDeviceLogsPage.jsx`, `frontend/src/modules/monitoring/MonitoringDeviceLogsPage.test.jsx`, `backend/app/api/monitoring.py`, `specs/master/pd-all/pd-monitoring/README.md` |
| INFO | 文档型 | `monitoring` | 链路详情 UI 已展示路由置信度、意图置信度、槽位详情、响应文本、设备上下文快照 | `frontend/src/modules/monitoring/MonitoringDeviceLogsPage.jsx`, `frontend/src/modules/monitoring/MonitoringDeviceLogsPage.test.jsx`, `specs/master/spec.md` |
| INFO | 文档型 | `dialog-profile` | 手动测试 trace 已补 route/intent 置信度、response text、slots、context snapshot，并有页面回归测试锁定 | `backend/app/api/dialog_profile.py`, `frontend/src/modules/dialog-profile/DialogProfileTestPage.jsx`, `frontend/src/modules/dialog-profile/DialogProfileTestPage.test.jsx`, `specs/master/spec.md` |
| INFO | 文档型 | `batch-test` | 智能分析页已补混淆矩阵，结果表已补预期/实际槽位、通过态与命名阈值口径，并有前后端回归锁定 | `frontend/src/modules/batch-test/BatchTestDetailPage.jsx`, `frontend/src/modules/batch-test/BatchTestDetailPage.test.jsx`, `backend/app/api/batch_test.py`, `backend/tests/contract/test_batch_test_api.py` |
| INFO | 文档型 | `dialog-profile` | 详情页知识库绑定控件与 `knowledge_base_id` 持久化已补齐，并有前端回归测试锁定 | `frontend/src/modules/dialog-profile/DialogProfileDetailPage.jsx`, `src/modules/dialog-profile/DialogProfileDetailPage.test.jsx`, `frontend/src/modules/dialog-profile/DialogProfilePage.jsx` |
| INFO | 文档型 | `user-mgmt` | 权限矩阵把 PM 的受限权限压缩成二值显示，弱化了权限边界表达 | `frontend/src/modules/user-mgmt/UserMgmtPage.jsx`, `backend/app/constants.py` |
| INFO | 派生型 | `batch-test` | 执行批次已改为轮询直到 `running -> completed/failed` 收敛后再提示成功，并有前端回归测试锁定 | `frontend/src/modules/batch-test/BatchTestDetailPage.jsx`, `frontend/src/modules/batch-test/BatchTestDetailPage.test.jsx`, `backend/app/api/batch_test.py` |
| INFO | 派生型 | `monitoring` | 用金色 Tag 展示“30s 轮询口径”但没有对应动态倒计时或自动刷新反馈，易产生完成错觉 | `frontend/src/modules/monitoring/MonitoringDashboardPage.jsx` |
| INFO | 派生型 | `intent-library` | 当前正式 React 页面没有覆盖 PD 五页面的信息密度和工作流深度，存在“PD 丰富、正式页偏薄”的感知落差 | `specs/master/pd-all/pd-intent-library/README.md`, `frontend/src/modules/intent-library/*` |
| INFO | 派生型 | 全局 | 虽然多数模块沿用了 `page-stack` / `module-card` / `hero-eyebrow` 统一壳层，但“成功反馈后是否一定伴随真实刷新”在不同模块上并不完全一致 | `frontend/src/modules/*`, `frontend/src/app/AppShell.jsx` |

## 审核建议
- 先修正文档型偏差，再处理派生型偏差。
- 所有“成功提示”类交互统一增加真实回读或状态收敛判断。
- 对于未被规范明文要求但已形成统一体验基线的项，后续建议沉淀成正式 UI 约束文档，避免再次出现“实现者各自理解”的偏差。
