# 批量测试 (Batch Test) 任务

**PD 交互原型**: pd-all/pd-batch-test/ (2 pages: index, detail)
**架构设计**: ad/ad-batch-test.md
**详细设计**: dd/dd-batch-test.md
**优先级**: P2
**依赖**: tasks-infra.md 必须先完成; tasks-dialog-profile.md 提供测试管道

## 测试任务（TDD: 先写测试, 确保红灯）

### 契约测试（覆盖 AD API — 17 端点）

- [ ] T001 [P] [T-CONTRACT] 批次 CRUD 契约测试: GET/POST /batch-tests, GET/DELETE /batch-tests/{id}
  - 文件: `backend/tests/contract/test_batch_tests_api.py`
  - 依据: ad/ad-batch-test.md §3.1
- [ ] T002 [P] [T-CONTRACT] 用例 CRUD + 导入导出 + LLM 生成 契约测试: GET/POST/PUT/DELETE cases, POST generate-cases, POST import-cases, GET export-cases
  - 文件: `backend/tests/contract/test_batch_cases_api.py`
  - 依据: ad/ad-batch-test.md §3.2
- [ ] T003 [P] [T-CONTRACT] 执行 + 分析 + 对比 契约测试: POST execute, GET analysis, GET compare
  - 文件: `backend/tests/contract/test_batch_execution_api.py`
  - 依据: ad/ad-batch-test.md §3.3

### 集成测试（覆盖 AD 数据流）

- [ ] T004 [P] [T-INTEGRATION] 批量测试执行集成测试: 创建批次→导入用例→执行→结果回写→智能分析
  - 文件: `backend/tests/integration/test_batch_execution.py`
  - 依据: ad/ad-batch-test.md §2.1 批量执行数据流

### E2E 测试（覆盖 PD 交互路径）

- [ ] T005 [P] [T-E2E] 批量测试列表页 E2E: 新建批次/导入用例/执行/查看结果
  - 文件: `frontend/tests/e2e/batch-test-list.spec.js`
  - 依据: pd-all/pd-batch-test/index.html
- [ ] T006 [P] [T-E2E] 批量测试详情页 E2E: 用例管理/执行进度/结果展示/智能分析
  - 文件: `frontend/tests/e2e/batch-test-detail.spec.js`
  - 依据: pd-all/pd-batch-test/detail.html

## 后端任务

### 数据模型（来自 DD 实体定义）

- [ ] T007 [P] [B-MODEL] 创建 BatchTest ORM 模型 (id, name, profile_id, status, total_cases, completed_cases, accuracy)
  - 文件: `backend/app/models/batch_test.py`
  - 依据: dd/dd-batch-test.md §1.1
- [ ] T008 [P] [B-MODEL] 创建 TestCase ORM 模型 (id, batch_id, input_text, expected_intent, expected_slots, actual_result, is_hit, score)
  - 文件: `backend/app/models/test_case.py`
  - 依据: dd/dd-batch-test.md §1.2
- [ ] T009 [P] [B-MODEL] 创建 TestRun / TestRunAnalysis ORM 模型
  - 文件: `backend/app/models/test_run.py`
  - 依据: dd/dd-batch-test.md §1.3~§1.4
- [ ] T010 [P] [B-MODEL] 创建 Pydantic Schema (BatchTest/TestCase/TestRun/Analysis Request/Response)
  - 文件: `backend/app/schemas/batch_test.py`
- [ ] T011 [B-MODEL] 生成 Alembic 迁移并运行 (batch_tests, test_cases, test_runs, test_run_analyses 表)
  - 文件: `backend/migrations/versions/005_batch_test.py`

### 服务层（来自 DD 算法）

- [ ] T012 [B-SERVICE] 批次管理服务 (CRUD + 状态管理: draft⇄ready⇄running⇄completed)
  - 文件: `backend/app/services/testing/batch_test.py`
  - 依据: dd/dd-batch-test.md §3 状态机 + §4.1
- [ ] T013 [B-SERVICE] 用例管理服务 (CRUD + Excel 导入/导出 + 批量删除)
  - 文件: `backend/app/services/testing/case_manager.py`
  - 依据: dd/dd-batch-test.md §4.2
- [ ] T014 [B-SERVICE] LLM 用例自动生成服务 (基于意图/槽位定义生成测试用例)
  - 文件: `backend/app/services/testing/case_generator.py`
  - 依据: dd/dd-batch-test.md §4.3 LLM 用例生成算法
- [ ] T015 [B-SERVICE] 批量执行引擎 (异步并发执行 + 进度追踪 + 结果回写)
  - 文件: `backend/app/services/testing/batch_executor.py`
  - 依据: dd/dd-batch-test.md §4.4 批量执行算法
- [ ] T016 [B-SERVICE] 智能分析服务 (总体结论/混淆TopN/槽位错误分布/低分样本/改进建议)
  - 文件: `backend/app/services/testing/analyzer.py`
  - 依据: dd/dd-batch-test.md §4.5 智能分析算法

### API 端点（来自 AD 接口契约）

- [ ] T017 [B-API] 批次 CRUD API: GET/POST /batch-tests, GET/DELETE /batch-tests/{id}
  - 文件: `backend/app/api/v1/batch_tests.py`
  - 依据: ad/ad-batch-test.md §3.1
- [ ] T018 [B-API] 用例 CRUD + 导入导出 + LLM 生成 API
  - 文件: `backend/app/api/v1/batch_tests.py` (扩展)
  - 依据: ad/ad-batch-test.md §3.2
- [ ] T019 [B-API] 执行 + 分析 + 对比 API
  - 文件: `backend/app/api/v1/batch_tests.py` (扩展)
  - 依据: ad/ad-batch-test.md §3.3

## 前端任务

### 页面（来自 PD 交互原型）

- [ ] T020 [F-PAGE] 批量测试列表页: 批次Table+新建弹窗+状态筛选+执行按钮
  - 文件: `frontend/src/pages/BatchTest/index.jsx`
  - 依据: pd-all/pd-batch-test/index.html
  - PD UI Checklist:
    - [ ] 统计卡片 ×4: 测试批次总数 / 已完成 (green) / 执行中 (blue, spin 图标) / 未达标 (red) — dd §10.1
    - [ ] 筛选条件 ×4: 搜索批次名称 (Input+SearchOutlined) / 关联方案 (Select) / 执行状态 (Select: pending/running/completed/failed) / 达标状态 (Select: passed/failed) + 查询/重置按钮 — dd §10.3.1
    - [ ] 批次列表 Table ×9 列: 批次名称(name link+id) / 关联方案 / 用例数 / 执行状态(Tag) / 达标(Tag) / 准确率(条件色) / 平均耗时(条件色) / 创建时间 / 操作(3 buttons) — dd §10.2.1
    - [ ] 操作列: 查看详情 (EyeOutlined→detail) / 重新执行 (ReloadOutlined, 确认弹窗, running 禁用) / 删除 (DeleteOutlined danger, 确认弹窗, running 禁用) — dd §10.4.1
    - [ ] 新建批次两步弹窗: Step1 基本信息 (name/profile/accuracyThreshold/latencyThreshold) + Step2 用例来源 (Radio: 自动生成+LLM配置 / 上传Excel+Dragger+下载模板 / 手动添加) — dd §10.5 #1
    - [ ] 删除确认弹窗 (Modal.confirm danger, 显示批次名称) — dd §10.5 #2
    - [ ] 重新执行确认弹窗 (Modal.confirm, 提示覆盖历史) — dd §10.5 #3
    - [ ] 分页: showSizeChanger / showQuickJumper / showTotal / scroll.x=1400
- [ ] T021 [F-PAGE] 批量测试详情页: 用例管理Tab+执行进度+结果统计卡片+智能分析报告+对比视图
  - 文件: `frontend/src/pages/BatchTest/Detail.jsx`
  - 依据: pd-all/pd-batch-test/detail.html
  - PD UI Checklist:
    - [ ] 批次概览统计卡片 ×8 (2 行 ×4 列): Row1: 关联方案(blue) / 用例总数 / 通过数(green) / 失败数(red); Row2: 准确率(%,条件色+目标Tag) / 平均耗时(ms,条件色+目标Tag) / 执行时间 / 达标状态(Tag) — dd §10.1
    - [ ] 测试结果明细 Table ×12 列: 用例编号(code,fixed left) / 用例语句(ellipsis+Tooltip,fixed left) / 预期路由(Tag色) / 实际路由(匹配色) / 预期意图(code) / 实际意图(匹配色底) / 预期槽位(JSON tooltip) / 实际槽位(JSON tooltip,不匹配红) / 匹配得分(Progress bar,sortable) / 响应耗时(Tag色,sortable) / 达标(✓/✗) / 标记(auto/manual Tag) — dd §10.2.2
    - [ ] 结果明细筛选 ×3 (Card extra): 达标状态(Select) / 路由类型(Select) / 意图名称(Select showSearch) — dd §10.3.2
    - [ ] 失败行高亮: is_pass=false 行 rowClassName="ant-table-row-error" — dd §10.5 #6
    - [ ] 智能分析报告 Tabs ×5: 总体结论(Alert cards) / 意图准确率排名(Table 5 列 dd §10.2.3) / 混淆矩阵(Table 5 列 dd §10.2.4 + 关系图) / 失败归因分析(Card.inner 列表+归因统计Alert) / 优化建议(Steps vertical 优先级着色+预期效果Alert) — dd §10.5 #5
    - [ ] 页头按钮: 返回(→列表) / 重新执行(确认弹窗) / 导出报告(primary, 下载) — dd §10.4.2
    - [ ] 分页: pageSize=10 / showSizeChanger / showTotal / scroll.x=1600

### 组件（可复用）

- [ ] T022 [P] [F-COMPONENT] 测试结果图表组件 (准确率/混淆矩阵/槽位错误分布)
  - 文件: `frontend/src/pages/BatchTest/ResultCharts.jsx`
- [ ] T023 [P] [F-COMPONENT] 用例导入弹窗组件 (Excel 模板下载+上传+预览)
  - 文件: `frontend/src/pages/BatchTest/ImportCasesModal.jsx`

### 状态管理与 API 对接

- [ ] T024 [F-STORE] 批量测试状态管理 (zustand): 批次列表/当前批次/用例/执行进度
  - 文件: `frontend/src/stores/batchTestStore.js`
- [ ] T025 [F-API] 批量测试 API 对接层: 全部 17 端点的前端调用封装
  - 文件: `frontend/src/services/batchTestApi.js`

## 检查点

**模块验收标准**（对照 PD 交互稿）:
- [ ] 所有测试通过（T001~T006 红灯→绿灯）
- [ ] 批次管理: CRUD + 状态流转 (draft⇄ready⇄running⇄completed) 正确
- [ ] 用例管理: 手动CRUD + Excel导入导出 + LLM自动生成 可用
- [ ] 批量执行: 异步执行 + 进度追踪 + 结果回写 可用
- [ ] 智能分析: 执行完成后自动生成分析报告
- [ ] 结果对比: 两次测试结果可视化对比 可用
- [ ] 无回归（infra + 先前模块测试仍通过）
