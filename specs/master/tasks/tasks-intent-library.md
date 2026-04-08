# 任务文件: `pd-intent-library`

**输入**: `specs/master/ai-pd/ai-intent-library.md` + `specs/master/pd-all/pd-intent-library/` + `specs/master/ad/ad-intent-library.md` + `specs/master/dd/dd-intent-library.md` + `specs/master/plans/plan-intent-library.md`  
**前置依赖**: `pd-user-mgmt = browser_verified`  
**TDD 约束**: 先写失败测试，再写最小实现，再验证通过  
**风险提示**: `FR-050 Partial` 必须持续可见，不得在实现中掩盖

## 任务总览

- 总任务数: 10
- 测试任务: 4
- 后端任务: 2
- 前端任务: 3
- 验证/收口任务: 1

## AI-PD 消费说明

- 主输入: `ai-pd/ai-intent-library.md`
- HumanPD 参考: `pd-all/pd-intent-library/`
- 本文件中的页面、动作、字段、异常和隐藏交互，优先继承 AI-PD 的 `capabilities / action_contracts / data_contracts / exception_flows / hidden_interactions`
- 旧 `AD / DD / plan / tasks / code` 只作为参考层，不作为当前完成性结论

## AI-PD 承接矩阵（页面能力清单）

兼容当前 gate 检查口径：下表中的 `hidden_interactions` 同时承担旧 `interactive_containers` 字段语义。
其中 `ui-capability` 对应旧 `functional-hidden-ui`，`instructional` 对应旧 `explanatory-only`。

| 页面 | `visible_ui` | `hidden_interactions` | 对应任务 | 当前状态 |
|------|--------------|-----------------------|---------|---------|
| `index` | 指令库表格、筛选、新建、删除、详情跳转 | `instructional`: 说明抽屉 | Task 3 | 已完成 |
| `detail` | 模型摘要、训练/发布/下载、子页跳转 | `ui-capability`: 发布门禁反馈；`instructional`: 规则说明 Drawer | Task 4 | 已验证 |
| `datasets` | 数据集表格、导入、LLM 合成、返回链路 | `instructional`: 说明抽屉 | Task 5 | 已完成 |
| `dataset-detail` | 样本明细、保存、返回链路 | `ui-capability`: 意图配置 Drawer、相似问/排除问 Drawer、词槽 Drawer、实体导入 Modal、新增问法 Modal | Task 6 + Task 7 + Task 8 | 已完成 |
| `test` | 单条测试、批量评估、分析摘要、返回链路 | `ui-capability`: 批量评估配置 / 结果分析面板 | Task 9 | 已验证 |

## AI-PD 关键能力映射

| capability_id | 页面 | 对应任务 | 说明 |
|---------------|------|---------|------|
| `CAP-IL-INDEX-001` | `index` | Task 3 | 列表筛选、创建、删除、跳详情 |
| `CAP-IL-DETAIL-004` | `detail` | Task 4 | 创建训练任务与状态回读 |
| `CAP-IL-DATASETS-003` ~ `CAP-IL-DATASETS-007` | `datasets` | Task 5 | 导入、LLM 合成、进入数据详情 |
| `CAP-IL-DATASET_DETAIL-001` ~ `CAP-IL-DATASET_DETAIL-007` | `dataset-detail` | Task 6 + Task 7 + Task 8 | deep UI capability 最小闭环 |
| `CAP-IL-TEST-001` | `test` | Task 9 | 单条测试与批量评估同页闭环 |

## 任务列表

### Task 1. 前端 API 与契约测试先行
- [x] 补强 `frontend/src/services/api.intent-library.test.js`
- [x] 先写失败测试锁定列表筛选/删除、数据集动作、dataset-detail 写接口请求形态
- [x] 先写失败测试锁定测试页评估结果和分析摘要回读
- [x] 运行定向 Vitest，确认失败原因正确

### Task 2. 路由与页面边界测试先行
- [x] 补强 `frontend/src/modules/intent-library/IntentLibraryRoutes.test.jsx`
- [x] 锁定五条路由 `index/detail/datasets/dataset-detail/test`
- [x] 锁定 `index -> detail -> datasets -> dataset-detail -> detail -> test` 导航链
- [x] 锁定 `/intent-library/**` 菜单高亮

### Task 3. 列表页闭环
- [x] 校正 `frontend/src/modules/intent-library/IntentLibraryPage.jsx`
- [x] 补齐筛选、删除和状态概览，不再只有创建 + 跳详情
- [x] 创建/删除后列表必须真实回读
- [x] 回归列表页 Vitest

### Task 4. 详情页生命周期闭环
- [x] 校正 `frontend/src/modules/intent-library/IntentLibraryDetailPage.jsx`
- [x] 训练、发布、下载、数据集/测试导航都必须基于真实详情回读
- [x] 显式展示发布门禁反馈，不允许只有按钮禁用无解释
- [x] 回归 detail 相关 Vitest

### Task 5. 数据集目录页闭环
- [x] 校正 `frontend/src/modules/intent-library/IntentLibraryDatasetsPage.jsx`
- [x] 补齐数据集创建/导入/LLM 合成入口及最小反馈
- [x] `datasets` 页必须明确承接目录动作，不能只做详情派生只读页
- [x] 回归 datasets 页 Vitest

### Task 6. dataset-detail 失败测试与契约先行
- [x] 为 `IntentLibraryDatasetDetailPage.jsx` 先写失败测试，锁定 deep UI capability 的最小闭环
- [x] 至少锁定：保存 intent、保存词槽/实体、新增相似问/排除问、实体导入反馈
- [x] 后端若缺写接口，先写 pytest/contract 红灯测试复现

### Task 7. dataset-detail 最小实现闭环
- [x] 校正 `frontend/src/modules/intent-library/IntentLibraryDatasetDetailPage.jsx`
- [x] 落地 `functional-hidden-ui`：意图配置 Drawer、相似问/排除问 Drawer、词槽 Drawer、实体导入 Modal、新增问法 Modal
- [x] 至少完成一组真实保存并回读的 deep UI capability
- [x] 对无法在本轮完成的高级编辑体验显式登记 `Deferred`

### Task 8. 后端缺口补齐
- [x] 复核并按需补齐 `backend/app/api/intent_library.py`
- [x] 补齐列表删除、数据集动作或 dataset-detail 写接口的最小后端承接
- [x] 回归 `backend/tests/contract/test_intent_library_api.py` 与相关 flow tests
- [x] 继续保持 `FR-050 Partial` 可见

### Task 9. 测试页与状态机回归
- [x] 校正 `frontend/src/modules/intent-library/IntentLibraryTestPage.jsx`
- [x] 确保单条测试与批量评估留在同页，且分析摘要来自真实回读
- [x] 回归 `backend/tests/test_intent_library_flow.py`
- [x] 锁定唯一 `testable/published` 与阈值快照

### Task 10. 门禁、smoke 与 review 收口
- [x] 运行 `validate-stage-gates` 当前支持的 `ad/dd/tasks/implement/browser` 校验
- [x] 运行定向 `pytest`、`Vitest`、最近编辑文件 lints
- [x] 完成 intent-library 模块级 smoke，覆盖 `page_boundary_parity / route_navigation_chain / capability_parity / training_state_transition / batch_eval_feedback / result_readback`
- [x] 进行 `review`，确认新结论来自新链路而非旧结论复用
- [x] 更新 `tasks-intent-library.md`、`tasks/README.md`、`module-state.json` 到最终真实状态

## 完成定义

- [x] 五页页面边界与主导航链路重新被测试和 smoke 证明
- [x] `index`/`datasets` 不再只剩骨架导航，具备真实目录动作
- [x] `dataset-detail` 至少存在一组 deep UI capability 的真实闭环
- [x] 训练、发布、单条测试、批量评估都能通过真实回读收敛
- [x] `FR-050 Partial` 仍明确保留
- [x] browser smoke 已证明 critical probes
