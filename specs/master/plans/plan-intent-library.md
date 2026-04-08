# 实施计划: master / pd-intent-library

**分支**: `master` | **日期**: 2026-04-03 | **规范**: `specs/master/spec.md`  
**输入**: `specs/master/spec.md + specs/master/ai-pd/ai-intent-library.md + specs/master/ad/ad-intent-library.md + specs/master/dd/dd-intent-library.md + specs/master/pd-all/pd-intent-library/README.md`

## 摘要

本轮以 `ai-intent-library.md` 为唯一主输入，重新执行 `AD -> DD -> plan -> tasks -> implement -> smoke -> review`。目标不是推倒重写所有代码，而是重建文档链、重置完成性结论，并在新任务基线下重新验证现有实现是否真的承接了五页边界、页面能力和 critical browser probes。

## Pre-flight 一致性扫描

| 检查项 | 结果 | 结论 / 处理动作 |
|--------|------|----------------|
| AI-PD 页面级语义是否完备 | OK | `index/detail/datasets/dataset-detail/test` 均有 `goal / primary_user_flows` |
| HumanPD 页面边界是否稳定 | OK | `pd-intent-library` 的五页边界和导航链明确 |
| harness 状态是否已归零 | OK | `pd-intent-library` 已回退到 `not_started` |
| 旧 AD/DD/plan/tasks 是否可信为执行基线 | OK | 已全部降级为参考层，并由本轮新文档链替换 |
| 现有代码能否完全覆盖 AI-PD | WARNING | `index`/`datasets`/`dataset-detail` 仍缺明显能力点，需要新任务验证 |
| 依赖模块是否可复用 | OK | `pd-user-mgmt = browser_verified`，满足本模块权限与壳层依赖 |

## AI-PD 消费原则

- 主真相源固定为 `specs/master/ai-pd/ai-intent-library.md`
- `pd-all/pd-intent-library/README.md` 与对应 HTML 仅负责页面边界、导航入口和视觉提示
- 若 `AI-PD` 与当前实现冲突，优先修正设计链和实现，不以旧代码反推需求
- `hidden_interactions` 兼容当前 gate 口径时，同时显式标注旧词汇：
  - `ui-capability` = `functional-hidden-ui`
  - `instructional` = `explanatory-only`

## 试验范围

### 纳入范围

- `index`：筛选、创建、删除、进入详情
- `detail`：训练、发布、下载、导航到数据集/测试、状态回读
- `datasets`：数据集目录、导入、LLM 合成、进入数据详情
- `dataset-detail`：intent/slot/entity/sample 深交互最小闭环
- `test`：单条测试和库内批量评估同页闭环

### 不纳入本轮闭环

- `FR-050` 的继承链路可视化，继续保留 `Partial`
- 运行时设备侧加载、跨模块绑定细节、真实模型二进制产物下载
- 复杂 Excel 解析器和复杂 LLM 提示词编辑器，可保留为 `Deferred`

## 当前差距判断

| 页面 | AI-PD 目标 | 当前实现观察 | 本轮策略 |
|------|------------|--------------|---------|
| `index` | 筛选/删除/创建/跳详情 | 已有创建和跳详情，但筛选/删除能力未明确 | 补 UI + API 契约或显式延期 |
| `detail` | 生命周期闭环 | 已有训练/发布/下载/跳页骨架 | 重点验证状态回读与门禁反馈 |
| `datasets` | 数据集目录 + 导入/LLM 合成 | 当前以详情接口派生目录，只读倾向明显 | 补目录动作与回读 |
| `dataset-detail` | deep UI capability 主页 | 当前更接近只读样本列表 | 本轮重点补齐最小闭环 |
| `test` | 单条测试 + 批量评估 | 基本骨架已存在 | 重点验证真实评估回读 |

## 阶段规划

### 阶段 1: 设计链重建

**目标**: 用新的 `AD / DD / plan / tasks` 完整替换旧完成叙事  
**检查点**:
- `plan-intent-library.md` 明确引用 `ai-pd/ai-intent-library.md`
- 页面能力清单明确继承 `functional-hidden-ui / explanatory-only`
- `tasks-intent-library.md` 重新回到未完成状态

### 阶段 2: 测试先行

**目标**: 先用失败测试锁定本轮要补的缺口  
**检查点**:
- 前端路由与页面测试覆盖五页边界
- 前端 API 测试覆盖列表/详情/数据集详情/测试页请求形态
- 后端 contract/flow 测试覆盖训练、评估、发布、阈值快照

### 阶段 3: 最小实现修订

**目标**: 在现有前后端骨架上做定向修订，而不是盲目重写  
**检查点**:
- 所有新增或调整代码都对应新 tasks
- `dataset-detail` 至少有一组真正可保存并回读的深交互
- `index`/`datasets` 的目录动作不再只剩导航骨架

### 阶段 4: 模块级验证与收口

**目标**: 用测试、smoke、review 重新获得“可信”状态  
**检查点**:
- `pytest`、`Vitest`、最近编辑文件 lint 通过
- browser smoke 证明 `page_boundary_parity / route_navigation_chain / capability_parity / training_state_transition / batch_eval_feedback / result_readback`
- `review` 重点检查是否仍存在旧结论复用

## 页面能力清单

兼容当前 gate 检查口径：下表中的 `hidden_interactions` 同时承担旧 `interactive_containers` 字段语义。
其中 `ui-capability` 对应旧 `functional-hidden-ui`，`instructional` 对应旧 `explanatory-only`。

| 页面 | `visible_ui` | `hidden_interactions` | 核心能力 | 本轮目标 |
|------|--------------|-----------------------|----------|---------|
| `index` | 指令库表格、筛选、新建、删除、详情入口 | `instructional`: 说明抽屉 | 目录管理与状态概览 | 闭环 |
| `detail` | 模型列表、训练、发布、下载、子页跳转 | `ui-capability`: 发布门禁反馈；`instructional`: 说明抽屉 | 生命周期闭环 | 闭环 |
| `datasets` | 数据集表格、导入、LLM 合成、返回链路 | `instructional`: 说明抽屉 | 数据集目录和绑定状态 | 闭环 |
| `dataset-detail` | 样本明细、保存、返回链路 | `ui-capability`: 意图配置 Drawer / 相似问 Drawer / 词槽 Drawer / 实体导入 Modal / 新增问法 Modal；`instructional`: 导入说明 | deep UI capability 承接 | 最小闭环，剩余可 `Deferred` |
| `test` | 单条测试、批量评估、分析摘要、返回链路 | `ui-capability`: 批量评估配置 / 结果分析面板；`instructional`: 说明抽屉 | 模型测试闭环 | 闭环 |

## 核心业务链路

| 链路 | 起点 | 终点/真实成功信号 | 证据 |
|------|------|------------------|------|
| 创建并进入详情 | 列表页新建库 | 列表回读新增项并进入详情页 | contract + page test + smoke |
| 训练与发布 | 详情页发起训练/发布 | 状态真实回读，唯一 `testable/published` 正确 | flow test + page test + smoke |
| 数据集目录到内容 | 详情页进入数据集，再进入数据详情 | 两页独立存在，返回链正确 | routes test + smoke |
| 数据内容维护 | `dataset-detail` 保存 intent/slot/entity/sample | 保存后详情快照回读 | page test + smoke |
| 模型测试 | 测试页单条测试/批量评估 | 结果、分析摘要、指标快照真实回读 | contract + page test + smoke |

## 显式未完成声明

- **Deferred**: 复杂 Excel 解析器、复杂 LLM 合成提示词编辑器、全部 dataset-detail 深交互的高级编辑体验
- **Partial**: `FR-050` 仅闭环默认阈值与任务快照，不闭环继承链可视化
- **Out of Scope**: 运行时设备侧加载、跨模块绑定细节、真实二进制模型产物下载
- **Blocked By**: 无

## 测试策略

| 测试类型 | 覆盖目标 | 工具 |
|---------|---------|------|
| frontend API 测试 | 列表/详情/数据集详情/测试页请求形态 | Vitest |
| frontend page 测试 | 五页成功信号与 deep UI capability | Vitest |
| frontend routes 测试 | 五页边界、返回链路、菜单高亮 | Vitest |
| backend contract 测试 | 列表、详情、数据集详情、单条测试、评估返回 | pytest |
| backend flow 测试 | 状态机、唯一 `testable/published`、阈值快照 | pytest |
| browser smoke | critical probes | browser automation |

## Browser Probes 映射

| probe | 动作 | 通过标准 |
|------|------|---------|
| `page_boundary_parity` | 逐页访问五条路由 | 五页均为独立承接页 |
| `route_navigation_chain` | `index -> detail -> datasets -> dataset-detail -> detail -> test` | 返回链与菜单高亮正确 |
| `capability_parity` | 打开 `dataset-detail` 的关键 Drawer / Modal | 真能力没有被降级为说明性内容 |
| `training_state_transition` | 发起训练并刷新详情 | 状态真实从 `draft/training/trained` 演进 |
| `batch_eval_feedback` | 测试页发起评估并查看结果 | 指标快照和分析摘要真实可见 |
| `result_readback` | 创建库/导入数据/保存数据内容 | 页面状态经接口回读刷新 |

## 风险与缓解

| 风险 | 描述 | 缓解 |
|------|------|------|
| 旧实现叙事残留 | 旧文件和旧代码容易被误当作“已完成” | 以新 tasks 和新验证结果重新记账 |
| `dataset-detail` 工期膨胀 | 深交互点多且历史实现薄弱 | 先做最小闭环，再显式保留 `Deferred` |
| 假成功 | 训练/发布/保存只显示 toast | 所有结论以回读和 smoke 为准 |
| `FR-050` 被误报闭环 | 阈值继承链仍未可视化 | 全链路持续携带 `Partial` |
