# Spec-Kit 设计模板体系

## 整体流程

```
/speckit.constitution    宪法 (项目级原则, 一次性)
        ↓
/speckit.specify         产出 spec.md (业务需求 + 模块映射 + FR 标签)
        ↓
/speckit.clarify         澄清 spec.md 中的模糊点 (可选, 推荐)
        ↓
/speckit.design-pd       产出 pd-all/ (模块化产品交互原型)
        ↓
/speckit.design-ad       产出 ad/ (模块化架构设计)
        ↓
/speckit.design-dd       产出 dd/ (模块化详细设计)
        ↓
/speckit.plan            产出 plan.md (实施规划桥梁)
        ↓
/speckit.tasks           产出 tasks/ (按 PD 模块拆分的任务目录, TDD 强制)
        ↓
/speckit.implement       执行代码实现 (指挥官+子代理模式)
        ↓
人工验收 → defects/ → /speckit.defects → 下一轮研发
```

## 框架文件 vs 项目产出物

Spec-Kit 有两类文件, 不要混淆:

### 框架文件 (项目无关, 所有项目共享)

模板分布在两个位置:

**框架级模板 (`.specify/templates/`)**

| 文件 | 作用 | 对应命令 |
|------|------|---------|
| `spec-template.md` | 定义 spec.md 的结构 | `/speckit.specify` |
| `plan-template.md` | 定义 plan.md 的结构 | `/speckit.plan` |
| `tasks-template.md` | 定义 tasks/ 目录的结构 | `/speckit.tasks` |
| `checklist-template.md` | 定义检查清单的结构 | `/speckit.checklist` |

**设计规范模板 (`specs/_template/`)**

| 文件 | 作用 | 对应命令 |
|------|------|---------|
| `pd-template.md` | 定义 PD 交互原型的设计规范 | `/speckit.design-pd` |
| `ad-template.md` | 定义架构设计规范 | `/speckit.design-ad` |
| `dd-template.md` | 定义详细设计规范 | `/speckit.design-dd` |

**命令定义**: `.cursor/commands/speckit.*.md` — 定义每个阶段的执行流程

### 项目产出物 (每个项目/分支独立)

```
specs/{branch}/
├── spec.md                        # 业务需求 (含模块映射表 + FR 标签)
├── pd-all/                        # 产品交互设计 (模块化)
│   ├── pd-hub.html                #   统一查看入口 (iframe 导航)
│   ├── pd-index.md                #   PD 模块覆盖索引
│   └── pd-<module>/               #   各模块交互原型 (HTML)
│       ├── README.md
│       ├── index.html
│       └── ...
├── ad/                            # 架构设计 (模块化; 模块数 ≤ 3 时为 ad.md)
│   ├── README.md                  #   模块索引
│   ├── ad-global.md               #   全局架构
│   └── ad-<module>.md             #   各模块架构设计
├── dd/                            # 详细设计 (模块化; 模块数 ≤ 3 时为 dd.md)
│   ├── README.md                  #   模块索引
│   ├── dd-global.md               #   全局详设 (共享实体/错误码/权限/配置)
│   └── dd-<module>.md             #   各模块详细设计
├── plan.md                        # 实施计划 (实施规划桥梁)
├── tasks/                         # 任务目录 (按 PD 模块拆分, TDD 强制)
│   ├── README.md                  #   索引 (模块列表/统计/依赖/策略/进度)
│   ├── tasks-infra.md             #   基础设施任务
│   ├── tasks-<module>.md          #   各 PD 模块任务 (测试→后端→前端)
│   └── tasks-refinement.md        #   横切关注点 + 完善
├── checklists/                    # 验收检查清单
└── defects/                       # 缺陷管理
    ├── INDEX.md
    └── D0xx.md
```

## 各文档职责

| 文档 | 目的 | 回答的问题 | 读者 |
|-----|------|-----------|------|
| **spec.md** | 业务需求 | 做什么? 为什么做? 哪些是 UI / API / 基础设施? | PM、业务方 |
| **pd-all/** | 产品交互设计 | 用户如何操作? 页面如何流转? 状态如何变化? | UI/UX、前端 |
| **ad/** | 架构设计 | 系统如何组织? 数据如何流动? API 契约是什么? | 架构师、后端 |
| **dd/** | 详细设计 | 具体如何实现? 边界如何处理? 算法逻辑? | 开发工程师 |
| **plan.md** | 实施计划 | 如何分阶段实施? 测试策略? 风险? | 技术负责人 |
| **tasks/** | 任务目录 | 具体执行哪些任务? 什么顺序? 谁做? | AI / 开发者 |

## 文档间的追溯关系

```
spec.md → PD → AD → DD → plan → tasks/ → implement → 人工验收 → defects → 下一轮
```

每个文档都必须包含与上游文档的追溯矩阵:

```markdown
## 追溯矩阵

| 本文档章节 | 上游文档章节 | 说明 |
|-----------|-------------|------|
| PD-3.1 状态矩阵 | spec.md US4 | 手动测试页面状态 |
| DD-2.1 模型状态机 | spec.md FR-044 | 小模型版本状态流转 |
```

## 命令对照表

| 命令 | 阶段 | 输入 | 输出 | 核心规范模板 |
|-----|------|------|------|-------------|
| `/speckit.constitution` | 项目宪法 | 项目原则 | constitution.md | - |
| `/speckit.specify` | 需求定义 | 业务背景 | spec.md | `.specify/templates/spec-template.md` |
| `/speckit.clarify` | 需求澄清 | spec.md | spec.md (补充) | - |
| `/speckit.design-pd` | 产品交互设计 | spec.md | pd-all/ | `specs/_template/pd-template.md` |
| `/speckit.design-ad` | 架构设计 | spec.md + pd-all/ | ad/ | `specs/_template/ad-template.md` |
| `/speckit.design-dd` | 详细设计 | spec.md + pd-all/ + ad/ | dd/ | `specs/_template/dd-template.md` |
| `/speckit.plan` | 实施计划 | spec + pd + ad + dd | plan.md | `.specify/templates/plan-template.md` |
| `/speckit.tasks` | 任务拆解 | pd + ad + dd + plan | tasks/ | `.specify/templates/tasks-template.md` |
| `/speckit.implement` | 执行实现 | tasks/ | 代码 | - |
| `/speckit.defects` | 缺陷管理 | defects/ | 缺陷修复 | `specs/master/defects/_template.md` |

## 为什么需要 PD/AD/DD?

### 之前的问题
- spec.md 只有业务需求
- AI 直接根据 spec 生成 plan → 代码
- 缺失交互细节 → 大量逻辑偏差和遗漏

### 现在的改进
- **PD**: 补充交互细节, 减少 UI/UX 偏差; 按模块拆分, 确保完整覆盖
- **AD**: 补充架构设计, 减少技术决策偏差
- **DD**: 补充详细设计, 减少实现细节偏差

### spec.md 为 PD 提供的关键结构

spec.md 中的**模块映射表**和**FR 标签**是 PD 阶段的核心输入:
- `[UI:<module>]` 标签 → 告诉 PD 哪些 FR 需要交互设计
- 模块映射表 → 告诉 PD 如何拆分独立的 PD 项目
- 交互提示 → 给 PD 设计者初始方向 (非强制约束)

这些结构定义在 spec 模板 (`.specify/templates/spec-template.md`) 中, 对所有项目生效。

## 快速开始

1. 确认模板文件完整:
   - `.specify/templates/` 下有 spec-template、plan-template、tasks-template
   - `specs/_template/` 下有 pd-template、ad-template、dd-template
2. 按顺序执行命令:
   ```
   /speckit.constitution  → 产出 constitution.md (一次性)
   /speckit.specify       → 产出 spec.md (含模块映射 + FR 标签)
   /speckit.clarify       → 澄清 spec.md (可选)
   /speckit.design-pd     → 产出 pd-all/
   /speckit.design-ad     → 产出 ad/
   /speckit.design-dd     → 产出 dd/
   /speckit.plan          → 产出 plan.md
   /speckit.tasks         → 产出 tasks/
   /speckit.implement     → 产出代码
   ```

## 模板文件

| 模板 | 路径 | 说明 |
|------|------|------|
| spec 模板 | `.specify/templates/spec-template.md` | 业务需求结构 (含模块映射表和 FR 标签规范) |
| PD 模板 | `specs/_template/pd-template.md` | 交互原型设计规范 (模块拆分、页面框架、交互表达) |
| AD 模板 | `specs/_template/ad-template.md` | 架构设计规范 (领域划分、API 契约、数据流) |
| DD 模板 | `specs/_template/dd-template.md` | 详细设计规范 (数据模型、状态机、算法、错误码) |
| plan 模板 | `.specify/templates/plan-template.md` | 实施计划结构 (实施规划桥梁) |
| tasks 模板 | `.specify/templates/tasks-template.md` | 任务目录结构 (按 PD 模块拆分, TDD 强制) |
| checklist 模板 | `.specify/templates/checklist-template.md` | 验收检查清单结构 |
