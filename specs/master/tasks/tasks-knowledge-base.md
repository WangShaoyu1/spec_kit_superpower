# 任务文件: `pd-knowledge-base`

**输入**: `specs/master/pd-all/pd-knowledge-base/` + `specs/master/ad/ad-knowledge-base.md` + `specs/master/dd/dd-knowledge-base.md` + `specs/master/plans/plan-knowledge-base.md`  
**前置依赖**: `pd-intent-library = browser_verified`  
**TDD 约束**: 先写失败测试，再写最小实现，再验证通过  
**风险提示**: 不得用前端文案伪造上传成功、索引成功或检索命中

## 任务总览

- 总任务数: 12
- 测试任务: 5
- 后端任务: 4
- 前端任务: 3

## 任务列表

### Task 1. 后端契约测试: 分类目录与创建
- [x] 新增 `backend/tests/contract/test_knowledge_base_api.py`
- [x] 先写 `list/create/update category` 的失败测试，覆盖名称唯一、统计回读与空态分类
- [x] 运行定向 pytest，确认失败原因正确
- [x] 在 `backend/app/models.py` 与 `backend/app/api/knowledge_base.py` 补最小实现
- [x] 重新运行定向 pytest，确认通过

### Task 2. 后端契约测试: 上传接口与详情
- [x] 在 `test_knowledge_base_api.py` 增加文档上传、详情、删除的失败测试
- [x] 运行失败测试，确认缺失接口或字段
- [x] 补齐文档实体、上传接口、详情回读最小实现
- [x] 回归该测试文件

### Task 3. 后端集成测试: 索引状态机
- [x] 新增/补充 `backend/tests/test_knowledge_base_flow.py`
- [x] 写失败测试覆盖 `uploading -> parsing -> indexing -> ready/failed`
- [x] 运行失败测试
- [x] 实现索引刷新逻辑、分类状态联动与索引版本递增
- [x] 回归通过

### Task 4. 后端集成测试: 字段过滤与重新索引
- [x] 在 `test_knowledge_base_flow.py` 写失败测试覆盖 JSON 字段过滤、Markdown 分段和重新索引
- [x] 运行失败测试
- [x] 实现过滤算法、结构化内容回写和重新索引入口
- [x] 回归通过

### Task 5. 后端契约测试: 检索验证
- [x] 在 `test_knowledge_base_api.py` 写失败测试覆盖 `retrieve test` 命中/未命中结果字段
- [x] 运行失败测试
- [x] 实现检索测试接口与 probe 持久化
- [x] 回归通过

### Task 6. 前端消费契约测试: API 适配层
- [x] 扩展 `frontend/src/services/api.js`
- [x] 新增或补充 `frontend/src/services/api.knowledge-base.test.js`
- [x] 先写失败测试，覆盖分类、上传、详情、重新索引、检索请求形态
- [x] 补最小实现并回归 Vitest

### Task 7. 前端页面测试: 知识库列表页骨架
- [x] 新增 `frontend/src/modules/knowledge-base/KnowledgeBasePage.jsx`
- [x] 新增 `frontend/src/modules/knowledge-base/KnowledgeBasePage.test.jsx`
- [x] 先写失败测试，覆盖分类选择、空态、上传弹窗与文档列表
- [x] 最小实现页面骨架并回归 Vitest

### Task 8. 前端页面测试: 详情与检索验证
- [x] 新增 `frontend/src/modules/knowledge-base/KnowledgeDocumentDetailPage.jsx`
- [x] 新增 `frontend/src/modules/knowledge-base/KnowledgeDocumentDetailPage.test.jsx`
- [x] 先写失败测试，覆盖过滤结果展示、重新索引、检索测试
- [x] 补详情页与交互，所有关键动作后强制回读

### Task 9. 前端壳层接入
- [x] 修改 `frontend/src/App.jsx`、`frontend/src/app/AppShell.jsx`
- [x] 打通 `/knowledge-base` 与 `/knowledge-base/:documentId` 路由及菜单导航
- [x] 回归已有登录、user-mgmt、intent-library 测试，避免回归

### Task 10. Harness 文档与门禁
- [x] 跑 `plan/tasks` 相关 stage gate
- [x] 更新 `.specify/harness/module-state.json` 至 `tasks_ready` / `implementing`
- [x] 记录无 blocker，可进入实现

### Task 11. Browser smoke
- [x] 启动本地前后端
- [x] 验证 `upload_feedback`
- [x] 验证 `indexing_result_readback`
- [x] 验证 `empty_state`

### Task 12. 缺陷修复与模块收口
- [x] 修复 smoke/review 发现的问题
- [x] 跑后端 pytest、前端 vitest、最近编辑文件 lints
- [x] 更新模块状态到 `browser_verified`
- [x] 为下一模块保留顺推条件

## 完成定义

- [x] 分类可创建、编辑并保持名称唯一
- [x] 文档上传后能真实完成索引状态流转
- [x] 详情页可回读有效字段、过滤字段与索引版本
- [x] 检索测试可返回命中/未命中、得分与片段
- [x] browser smoke 通过且模块状态推进完成
