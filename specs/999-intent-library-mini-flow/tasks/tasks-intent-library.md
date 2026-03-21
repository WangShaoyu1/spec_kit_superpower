# 指令库管理最小闭环任务

**PD 交互原型**: pd-all/pd-intent-library/
**架构设计**: ad/ad-intent-library.md
**详细设计**: dd/dd-intent-library.md
**优先级**: P1
**依赖**: tasks-infra.md 必须先完成

## 模块核心业务链路

| 链路 | 起点 | 终点/真实成功信号 | 对应任务 |
|------|------|------------------|---------|
| 最小资产闭环 | 新建指令库 | 详情页可见 draft 模型、绑定训练集名称、意图数量、语种 | T001, T002, T003, T004, T005, T006 |

## 显式未完成声明

- **Deferred**: 模型训练、评估、设为 testable、发布
- **Stub**: 无；本示例不允许用 501 伪装训练链路已经覆盖
- **Out of Scope**: 模型下载、批量测试、智能分析
- **Blocked By**: 无

## 测试任务(TDD: 先写测试, 确保红灯)

### 契约测试(覆盖 AD API)

- [ ] T001 [P] [T-CONTRACT] 指令库/数据集/意图/模型草稿 API 契约测试 → ad/ad-intent-library.md §3

### 集成测试(覆盖 AD 数据流)

- [ ] T002 [P] [T-INTEGRATION] 新建库 -> 新建训练集 -> 新建意图 -> 创建模型草稿 集成测试 → ad/ad-intent-library.md §2.1
- [ ] T003 [P] [T-INTEGRATION] 消费契约测试：详情页需要的 `library_key`、训练集名称、意图数量字段完整返回 → ad/ad-intent-library.md §3

### E2E 测试(覆盖 PD 交互路径)

- [ ] T004 [P] [T-E2E] 列表页/详情页/数据集页最小交互 E2E → pd-all/pd-intent-library/

## 后端任务

### 数据模型(来自 DD 实体定义)

- [ ] T005 [P] [B-MODEL] 创建 IntentLibrary、TrainingDataset、Intent、LibraryModelVersion 最小模型 → dd/dd-intent-library.md §1

### 服务层(来自 DD 算法)

- [ ] T006 [B-SERVICE] 实施创建模型草稿服务，校验空数据集和重复绑定 → dd/dd-intent-library.md §3.1
- [ ] T007 [T-UNIT] 创建模型草稿服务单元测试（正常 + 空数据集 + 重复绑定）→ dd/dd-intent-library.md §3.1

### API 端点(来自 AD 接口契约)

- [ ] T008 [B-API] 实施指令库/数据集/意图/模型草稿端点 → ad/ad-intent-library.md §3

## 前端任务

### 页面(来自 PD 交互原型)

- [ ] T009 [F-PAGE] 实施指令库列表页 → pd-all/pd-intent-library/index.html
  PD UI Checklist:
  - [ ] 统计卡
  - [ ] 搜索框
  - [ ] 新建指令库按钮
  - [ ] 列表表格
  - [ ] 详情入口
- [ ] T010 [F-PAGE] 实施指令库详情页与数据集详情页最小信息展示 → pd-all/pd-intent-library/detail.html, dataset-detail.html
  PD UI Checklist:
  - [ ] 返回按钮
  - [ ] 库基础信息
  - [ ] draft 模型表格
  - [ ] 绑定训练集名称
  - [ ] 意图数量与语种

## 检查点

### 模块完成定义（Definition of Done）

- [ ] 任务正文中不存在 `未实现 / UI only / placeholder / TODO / 待确认 / mock / stub` 仍被勾选完成的情况
- [ ] 所有显式未完成项已登记在 `Deferred / Stub / Out of Scope / Blocked By`
- [ ] 每条核心业务链路至少有一组通过的测试或 smoke 证据
- [ ] 前后端消费契约已验证（字段名、分页、下载、数组/对象返回）
- [ ] 没有假成功提示、假进度、假统计、仅更新状态但无真实业务逻辑的实现

**模块验收标准**(对照 PD 交互稿):
- [ ] 每个 [B-SERVICE] 都有配套 [T-UNIT] 且通过
- [ ] 每个 [B-API] 都有配套 [T-CONTRACT] 且通过
- [ ] 最小闭环集成测试通过
- [ ] Code Review 已完成
- [ ] 列表页与详情页的最小 UI Checklist 已逐项核对
- [ ] 核心链路最终结果：详情页可见 draft 模型、训练集名称、意图数量、语种
- [ ] 无回归
