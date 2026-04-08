# 实施计划: [FEATURE]

**分支**: `[###-feature-name]` | **日期**: [DATE] | **规范**: [link]
**输入**: 来自 `/specs/[###-feature-name]/` 的完整设计文档链（`spec.md + pd-all/ + ai-pd/ + ad/ + dd/`）

**注意**: 此模板由 `/speckit.plan` 命令填充。模块 plan (`plans/plan-<module>.md`) 定位为"**实施规划桥梁**"——承上（设计文档）启下（tasks/ + 编码），不重复 AD/DD 已有的设计内容，聚焦于技术实施层面的决策与规划。

## 摘要

[从 spec.md 功能需求 + AD 架构决策 + DD 技术细节中提炼: 系统要做什么 + 怎么做]

## Pre-flight 一致性扫描

<!--
  在进入实施规划前, 必须先记录设计链路是否存在冲突.
  若出现 BLOCKER, 不得继续进入 tasks 阶段.
-->

| 检查项 | 结果 (OK/WARNING/BLOCKER) | 结论 / 处理动作 |
|--------|---------------------------|----------------|
| FR 在 spec / AD / DD 中是否存在冲突 | [OK/WARNING/BLOCKER] | [说明] |
| HumanPD 页面是否真实存在且可映射到 AI-PD | [OK/WARNING/BLOCKER] | [说明] |
| AI-PD 是否覆盖 capability / action / data / rule / exception / hidden_interactions | [OK/WARNING/BLOCKER] | [说明, 若缺失则不得继续只按页面名规划] |
| plan 使用的源码路径是否与当前工程一致 | [OK/WARNING/BLOCKER] | [说明] |
| PD 是否存在部分覆盖/待补充项 | [OK/WARNING/BLOCKER] | [说明, 以及如何下传到 tasks] |
| 关键外部依赖/异步链路是否定义真实成功信号 | [OK/WARNING/BLOCKER] | [说明] |

## 技术背景

<!--
  需要操作: 将此部分内容替换为项目的技术细节.
  技术栈和架构决策应来源于 AD，字段级细节在 DD 中已定义——此处仅做汇总速查.
-->

**语言/版本**: [例如: Python 3.11、Swift 5.9、Rust 1.75 或 NEEDS CLARIFICATION]
**主要依赖**: [例如: FastAPI、UIKit、LLVM 或 NEEDS CLARIFICATION]
**存储**: [如适用, 例如: PostgreSQL、CoreData、文件 或 N/A]
**测试**: [例如: pytest、XCTest、cargo test 或 NEEDS CLARIFICATION]
**目标平台**: [例如: Linux 服务器、iOS 15+、WASM 或 NEEDS CLARIFICATION]
**项目类型**: [单一/网页/移动 - 决定源代码结构]
**性能目标**: [领域特定, 例如: 1000 请求/秒、10k 行/秒、60 fps 或 NEEDS CLARIFICATION]
**约束条件**: [领域特定, 例如: <200ms p95、<100MB 内存、离线可用 或 NEEDS CLARIFICATION]
**规模/范围**: [领域特定, 例如: 10k 用户、1M 行代码、50 个屏幕 或 NEEDS CLARIFICATION]

## 章程检查

*门控: 必须在设计阶段之前通过. Plan 编写时重新检查.*

[基于章程文件确定的门控条件]

## 项目结构

### 设计文档（上游输入）

```
specs/[###-feature]/
├── spec.md              # 业务需求 (/speckit.specify 输出)
├── pd-all/              # HumanPD (/speckit.design-pd 输出)
│   ├── pd-hub.html      # 统一查看入口（iframe 导航）
│   ├── pd-index.md      # PD 模块覆盖索引
│   └── pd-<module>/     # 各模块交互原型 (HTML)
├── ai-pd/             # AI-PD (/speckit.transform-pd 输出)
│   ├── README.md        # AI-PD 模块索引
│   └── ai-<module>.md   # 各模块 AI-PD
├── ad/                  # 架构设计 (/speckit.design-ad 输出, >3 模块时)
│   ├── README.md        # AD 模块索引
│   ├── ad-global.md     # 全局架构
│   └── ad-<module>.md   # 各模块架构设计
├── dd/                  # 详细设计 (/speckit.design-dd 输出, >3 模块时)
│   ├── README.md        # DD 模块索引
│   ├── dd-global.md     # 全局详设（共享实体/错误码/权限/配置）
│   └── dd-<module>.md   # 各模块详细设计
├── plans/
│   ├── README.md
│   └── plan-<module>.md # 此文件 (/speckit.plan 输出)
└── tasks/               # 任务目录 (/speckit.tasks 输出)
    ├── README.md        # 索引(模块列表/统计/依赖/策略/进度)
    ├── tasks-infra.md   # 设置 + 基础设施
    ├── tasks-<module>.md # 各 PD 模块任务(TDD: 测试→后端→前端)
    └── tasks-refinement.md # 横切关注点 + 完善
```

> 若模块数量较少，`AD/DD` 也可能以单文件 `ad.md` / `dd.md` 形式存在；plan 必须按当前 feature 的真实结构填写，而不是机械保留目录树占位。

<!--
  注意: 旧流程中的 research.md、data-model.md、contracts/、quickstart.md 已由
  PD（交互原型）、AD（架构设计/接口契约）、DD（数据模型/算法/错误码）完全替代.
  新项目不再生成这些旧制品.
-->

### 源代码(仓库根目录)
<!--
  需要操作: 将下面的占位符树结构替换为此功能的具体布局.
  删除未使用的选项, 并使用真实路径(例如: apps/admin、packages/something)扩展所选结构.
  交付的计划不得包含选项标签.
-->

```
# [如未使用请删除] 选项 1: 单一项目(默认)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [如未使用请删除] 选项 2: Web 应用程序(检测到"前端" + "后端"时)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [如未使用请删除] 选项 3: 移动端 + API(检测到 "iOS/Android" 时)
api/
└── [同上后端结构]

ios/ 或 android/
└── [平台特定结构: 功能模块、UI 流程、平台测试]
```

**结构决策**: [记录所选结构并引用上面捕获的真实目录]

## 阶段规划

<!--
  模块 plan 的核心——将 PD 模块按依赖关系编排为可执行的实施阶段.
  每个阶段有明确的目标、交付物和验收检查点.
  详细的数据模型、API 契约、状态机等在 AD/DD 中已定义，此处仅做阶段性引用.

  设计链路: spec.md → HumanPD → AI-PD → AD → DD → plan → tasks
  AI-PD capability 是阶段规划的首要组织单元, HumanPD 仅补充页面结构与视觉参考.
-->

### 阶段 1: 基础设施
**目标**: 项目初始化 + 阻塞前置条件
**检查点**: 项目可运行，数据库可连接，基础中间件就绪

### 阶段 2: 核心功能（按 PD 模块优先级）
**目标**: 按模块优先级顺序交付 PD 模块
**检查点**: 每个模块可对照 PD 交互稿独立验证

### 阶段 3: 横切关注点
**目标**: 权限、监控、安全、性能优化
**检查点**: 非功能需求满足

### 阶段 4: 完善与优化
**目标**: 文档、代码清理、端到端集成验证
**检查点**: 可交付

## 模块核心业务链路

<!--
  每个 UI 模块至少定义 1-3 条闭环链路, 并明确真实成功信号.
  这些链路会被 tasks / review / smoke 直接引用.
-->

| 模块 | 链路名称 | 起点 | 终点/真实成功信号 | 覆盖方式 |
|------|---------|------|------------------|---------|
| [module-key] | [链路 1] | [入口操作] | [真实数据/状态/结果] | [integration/e2e/smoke] |
| [module-key] | [链路 2（如需要）] | [入口操作] | [真实数据/状态/结果] | [integration/e2e/smoke] |

## AI-PD 承接矩阵

<!--
  不是简单罗列页面名，而是把 AI-PD 中对实现真正有约束力的能力项结构化下传。
  HumanPD 用于补充页面边界和入口，AI-PD 负责定义 capability、contract、rule、exception。
-->

| 页面 | `page_boundary` | `visible_ui` | `hidden_interactions` | `capabilities` | 真实成功信号 / 风险 |
|------|-----------------|--------------|-----------------------|----------------|--------------------|
| [page-key] | [page/drawer/modal/... ] | [Table/筛选器/统计卡/按钮] | [`ui-capability` / `domain-rule` / `instructional` / `non-actionable-note`] | [capability IDs + 标题] | [说明] |

### 页面动作契约

| 页面 | `action_id` / 动作 | 前置条件 | 成功信号 | 失败反馈 | 状态变化 / 对应 API |
|------|--------------------|---------|---------|---------|--------------------|
| [page-key] | [ACT-001 / 按钮或入口] | [说明] | [真实回读 / 状态切换 / 下载结果] | [toast / alert / inline error] | [API / route / local state] |

### 数据契约 / 业务规则 / FR 映射

| 页面 | `data_contracts` / `business_rules` | 关联字段 / payload | 关联 FR |
|------|----------------------------------|--------------------|--------|
| [page-key] | [DATA-001 / RULE-001 ...] | [字段 / 列 / payload] | [FR-xxx] |

## 显式未完成声明

<!--
  本节不是可选备注，而是后续 tasks 进度和实现门禁的直接输入.
  任何部分覆盖、延期、桩实现、外部阻塞都必须在这里登记.
-->

- **Deferred**: [延期能力；如无则写"无"]
- **Stub / 需要 501 的能力**: [允许临时桩实现的项；如无则写"无"]
- **Out of Scope**: [不在本轮范围；如无则写"无"]
- **Blocked By**: [依赖外部条件；如无则写"无"]
- **路径单一真相源**: [写明唯一工程根路径, 如 `smartchef-v2/` 或 `backend/ + frontend/`]

## 测试策略

<!--
  定义各阶段的测试类型和标准. 具体测试场景来自 PD 的交互规范 + DD 的边界条件.
-->

| 测试类型 | 时机 | 覆盖目标 | 工具 |
|---------|------|---------|------|
| 单元测试 | 开发同步 | 算法逻辑（DD 定义） | [测试框架] |
| 契约测试 | API 稳定后 | 接口契约（AD 定义） | [测试框架] |
| 消费契约测试 | 前后端联调前 | 前端实际请求/响应形态（字段名、分页、下载、数组/对象） | [测试框架] |
| 集成测试 | 阶段完成 | 数据流（AD 流程图） | [测试框架] |
| E2E 测试 | 故事闭环 | 用户操作路径（PD 交互） | [测试框架] |
| 状态机测试 | 异步链路实现时 | 提交中 / 处理中 / 成功 / 失败全状态转换 | [测试框架] |

## 风险与缓解

| 风险类型 | 描述 | 缓解策略 |
|---------|------|---------|
| 技术风险 | [新技术学习曲线/性能瓶颈] | [应对措施] |
| 依赖风险 | [第三方服务/API] | [应对措施] |
| 进度风险 | [任务估不准] | [应对措施] |
| 假成功风险 | [前端假提示/硬编码统计/异步结果不可观测] | [明确成功信号 + 状态查询 + smoke 验证] |
| 文档漂移风险 | [spec/PD/AD/DD/plan 路径或规则不一致] | [pre-flight 扫描 + BLOCKER 处理] |

## 复杂度跟踪

*仅在章程检查有必须证明的违规时填写*

| 违规 | 为什么需要 | 拒绝更简单替代方案的原因 |
|-----------|------------|-------------------------------------|
| [例如: 第 4 个项目] | [当前需求] | [为什么 3 个项目不够] |
| [例如: 仓储模式] | [特定问题] | [为什么直接数据库访问不够] |
