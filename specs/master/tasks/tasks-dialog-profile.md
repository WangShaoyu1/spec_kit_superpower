# 任务文件: `pd-dialog-profile`

**输入**: `specs/master/pd-all/pd-dialog-profile/` + `specs/master/ad/ad-dialog-profile.md` + `specs/master/dd/dd-dialog-profile.md` + `specs/master/plans/plan-dialog-profile.md`  
**前置依赖**: `pd-knowledge-base = browser_verified`  
**TDD 约束**: 先写失败测试，再写最小实现，再验证通过  
**风险提示**: 不得伪造测试回复、调试 trace、发布成功或会话隔离结果

## 任务总览

- 总任务数: 12
- 测试任务: 5
- 后端任务: 4
- 前端任务: 3

## 任务列表

### Task 1. 后端契约测试: 方案目录与创建
- [x] 新增 `backend/tests/contract/test_dialog_profile_api.py`
- [x] 先写 `list/create/update profile` 失败测试，覆盖名称唯一、阈值校验和列表状态统计
- [x] 运行定向 pytest，确认失败原因正确
- [x] 在 `backend/app/models.py` 与 `backend/app/api/dialog_profile.py` 补最小实现
- [x] 重新运行定向 pytest，确认通过

### Task 2. 后端契约测试: 详情与发布门禁
- [x] 在 `test_dialog_profile_api.py` 增加详情、发布门禁、published 切换失败测试
- [x] 运行失败测试，确认接口与错误码缺口
- [x] 补齐详情接口、发布校验与 published_version 快照最小实现
- [x] 回归该测试文件

### Task 3. 后端集成测试: 测试会话与隔离
- [x] 新增 `backend/tests/test_dialog_profile_flow.py`
- [x] 写失败测试覆盖多会话隔离、消息写入、message_count 回读
- [x] 运行失败测试
- [x] 实现 `test_session` / `test_session_message` 流程
- [x] 回归通过

### Task 4. 后端集成测试: 调试 trace 与设备上下文
- [x] 在 `test_dialog_profile_flow.py` 写失败测试覆盖 route / intent / slots / model / response_time_ms
- [x] 运行失败测试
- [x] 实现手动测试消息处理、调试 trace、设备上下文回显
- [x] 回归通过

### Task 5. 后端契约测试: 发布成功与归档
- [x] 在 `test_dialog_profile_api.py` 写失败测试覆盖发布成功、旧 published 归档、新版本号递增
- [x] 运行失败测试
- [x] 完成发布状态切换与审计日志实现
- [x] 回归通过

### Task 6. 前端消费契约测试: API 适配层
- [x] 扩展 `frontend/src/services/api.js`
- [x] 新增 `frontend/src/services/api.dialog-profile.test.js`
- [x] 先写失败测试，覆盖列表、详情、发布、会话、发消息请求形态
- [x] 补最小实现并回归 Vitest

### Task 7. 前端页面测试: 方案列表页骨架
- [x] 新增 `frontend/src/modules/dialog-profile/DialogProfilePage.jsx`
- [x] 新增 `frontend/src/modules/dialog-profile/DialogProfilePage.test.jsx`
- [x] 先写失败测试，覆盖列表加载、新建方案、状态统计
- [x] 最小实现页面骨架并回归 Vitest

### Task 8. 前端页面测试: 详情页与发布门禁
- [x] 新增 `frontend/src/modules/dialog-profile/DialogProfileDetailPage.jsx`
- [x] 新增 `frontend/src/modules/dialog-profile/DialogProfileDetailPage.test.jsx`
- [x] 先写失败测试，覆盖详情配置、发布门禁结果与保存回读
- [x] 补详情页与交互，关键动作后强制回读

### Task 9. 前端页面测试: 手动测试页
- [x] 新增 `frontend/src/modules/dialog-profile/DialogProfileTestPage.jsx`
- [x] 新增 `frontend/src/modules/dialog-profile/DialogProfileTestPage.test.jsx`
- [x] 先写失败测试，覆盖会话切换、发消息、调试 trace 展示
- [x] 补测试页与会话隔离 UI，回归 Vitest

### Task 10. 前端壳层接入
- [x] 修改 `frontend/src/App.jsx`、`frontend/src/app/AppShell.jsx`
- [x] 打通 `/dialog-profiles`、`/dialog-profiles/:profileId`、`/dialog-profiles/:profileId/test` 路由与菜单导航
- [x] 回归已有登录、user-mgmt、intent-library、knowledge-base 测试，避免回归

### Task 11. Harness 文档与门禁
- [x] 跑 `plan/tasks` 相关 stage gate
- [x] 更新 `.specify/harness/module-state.json` 至 `tasks_ready` / `implementing`
- [x] 记录无 blocker，可进入实现

### Task 12. Browser smoke 与模块收口
- [x] 启动本地前后端
- [x] 验证 `profile_publish_gate`
- [x] 验证 `manual_test_trace`
- [x] 验证 `session_isolation`
- [x] 修复 smoke/review 问题后跑 pytest、vitest、lints
- [x] 更新模块状态到 `browser_verified`

## 完成定义

- [x] 方案可创建、编辑、查看并保持名称唯一
- [x] 发布门禁能真实阻断未满足条件的方案
- [x] 手动测试会话支持多会话隔离与消息历史回读
- [x] 调试面板展示 route / intent / slots / model / response_time_ms
- [x] browser smoke 通过且模块状态推进完成
