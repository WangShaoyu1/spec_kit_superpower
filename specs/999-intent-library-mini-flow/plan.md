# 实施计划: 指令库管理最小闭环示例

**分支**: `999-intent-library-mini-flow` | **日期**: 2026-03-22 | **规范**: [spec.md](./spec.md)
**输入**: 来自 `/specs/999-intent-library-mini-flow/` 的完整设计文档链

## 摘要

本示例用“指令库管理”的最小切片验证新 Speckit 规范是否真的把上游约束传到下游。范围只覆盖：

1. 新建指令库
2. 新建训练数据集
3. 在数据集中维护最小意图数据
4. 创建并展示模型草稿

## Pre-flight 一致性扫描

| 检查项 | 结果 (OK/WARNING/BLOCKER) | 结论 / 处理动作 |
|--------|---------------------------|----------------|
| FR 在 spec / AD / DD 中是否存在冲突 | OK | FR-039/043/048/049 口径一致 |
| PD 页面是否真实存在且被 AD 正确引用 | OK | `index/detail/datasets/dataset-detail` 页面均已创建 |
| plan 使用的源码路径是否与当前工程一致 | OK | 唯一路径声明为 `smartchef-v2/backend + smartchef-v2/frontend` |
| PD 是否存在部分覆盖/待补充项 | WARNING | PD 只覆盖到模型草稿创建；训练/评估/发布必须在 tasks 中显式标记 `Deferred` |
| 关键外部依赖/异步链路是否定义真实成功信号 | OK | 本示例不进入异步训练链路；真实成功信号已定义为 draft 模型和训练集绑定可见 |

## 技术背景

**语言/版本**: Python 3.11 + JavaScript ES2022
**主要依赖**: FastAPI、SQLAlchemy、React 18、Ant Design 5
**存储**: PostgreSQL
**测试**: pytest、Playwright
**目标平台**: Web 管理后台
**项目类型**: Web 应用程序
**性能目标**: 列表和详情操作为普通 CRUD，无额外性能目标
**约束条件**: 不允许把训练/发布链路伪装成已完成
**规模/范围**: 单模块、单条核心链路验证

## 章程检查

*门控: 必须在设计阶段之前通过. Plan 编写时重新检查.*

- TDD 必须在 `tasks/` 中体现
- 完成定义必须基于证据
- 不允许假成功、假进度、placeholder 冒充完成

## 项目结构

### 设计文档（上游输入）

```text
specs/999-intent-library-mini-flow/
├── spec.md
├── pd-all/
│   ├── pd-index.md
│   └── pd-intent-library/
│       ├── README.md
│       ├── index.html
│       ├── detail.html
│       ├── datasets.html
│       └── dataset-detail.html
├── ad/
│   └── ad-intent-library.md
├── dd/
│   └── dd-intent-library.md
├── plan.md
└── tasks/
```

### 源代码(仓库根目录)

```text
smartchef-v2/
├── backend/
│   ├── app/models/
│   ├── app/services/
│   ├── app/api/
│   └── tests/
└── frontend/
    ├── src/pages/IntentLibrary/
    ├── src/services/
    └── tests/
```

**结构决策**: 唯一路径声明为 `smartchef-v2/backend` 与 `smartchef-v2/frontend`，禁止写出第二套工程根路径。

## 阶段规划

### 阶段 1: 基础设施
**目标**: 保证最小模块能落在正确的前后端目录
**检查点**: 路径一致、基础 API 层和页面路由存在

### 阶段 2: 核心功能（按 PD 模块优先级）
**目标**: 交付指令库最小闭环
**检查点**: 可完成“新建库 -> 新建训练集 -> 新建意图 -> 创建模型草稿”

### 阶段 3: 横切关注点
**目标**: 补上消费契约和错误处理
**检查点**: 字段名、列表返回形态和失败提示一致

### 阶段 4: 完善与优化
**目标**: 验证证据、审查和 smoke 准备完成
**检查点**: 无假成功、延期项已显式声明

## 模块核心业务链路

| 模块 | 链路名称 | 起点 | 终点/真实成功信号 | 覆盖方式 |
|------|---------|------|------------------|---------|
| intent-library | 最小资产闭环 | 新建指令库 | 库详情页可见 draft 模型、绑定训练集名称、意图数量、语种 | integration + e2e + smoke |

## 显式未完成声明

- **Deferred**: 模型训练、评估、设为 testable、发布
- **Stub / 需要 501 的能力**: 无；本示例不生成伪训练接口
- **Out of Scope**: 模型下载、智能分析、批量测试
- **Blocked By**: 无
- **路径单一真相源**: `smartchef-v2/backend` + `smartchef-v2/frontend`

## 测试策略

| 测试类型 | 时机 | 覆盖目标 | 工具 |
|---------|------|---------|------|
| 单元测试 | 服务层实现时 | 创建模型草稿的非空校验和绑定校验 | pytest |
| 契约测试 | API 稳定后 | 指令库/数据集/意图/模型草稿接口 | pytest + httpx |
| 消费契约测试 | 前后端联调前 | `library_key`、数据集名称、意图数量字段与详情页消费方式一致 | pytest |
| 集成测试 | 阶段完成 | 最小资产闭环真实走通 | pytest |
| E2E 测试 | 页面完成 | 列表页/详情页/数据集页最小交互 | Playwright |
| 状态机测试 | 不适用 | 本示例不进入异步链路 | N/A |

## 风险与缓解

| 风险类型 | 描述 | 缓解策略 |
|---------|------|---------|
| 技术风险 | 可能只做出表面页面而无真实绑定关系 | 用集成测试验证最终详情页数据 |
| 依赖风险 | 现有正式模块文档体量大，容易把最小示例又做重 | 只保留一条核心链路 |
| 进度风险 | 训练/发布需求容易被误写进完成态 | 通过 `Deferred` 显式阻断 |
| 假成功风险 | 页面 toast 成功但后端未真实创建模型草稿 | 以 draft 记录和训练集名称可见作为真实成功信号 |
| 文档漂移风险 | `spec/pd/ad/dd/plan/tasks` 写出不同路径或覆盖范围 | 在 Pre-flight 中保留 `WARNING` 并写入 tasks |
