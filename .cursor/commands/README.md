# Spec-Kit 命令索引（增强版）

## 完整流程图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Spec-Kit 增强流程                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   /speckit.specify                                                          │
│   ├── 输入: 业务背景/需求描述                                                │
│   ├── 输出: spec.md (业务需求)                                               │
│   └── 检查点: 用户故事、验收场景、成功标准                                    │
│                          ↓                                                  │
│   /speckit.design-pd                                                        │
│   ├── 输入: spec.md                                                         │
│   ├── 输出: pd-all/ (HumanPD: 模块化产品交互设计)                            │
│   └── 检查点: 页面映射、状态矩阵、异常处理、每页 `page_goal / primary_user_flows` │
│                          ↓                                                  │
│   /speckit.transform-pd                                                     │
│   ├── 输入: pd-all/ + spec.md                                               │
│   ├── 输出: ai-pd/ (AI-PD: AI 主输入)                                    │
│   └── 检查点: capability IDs、动作契约、异常流、语义分类完整；缺少页面级 `goal/flows` 直接 blocker │
│                          ↓                                                  │
│   /speckit.design-ad                                                        │
│   ├── 输入: spec.md + ai-pd/ + pd-all/                                    │
│   ├── 输出: ad/ (模块化架构设计)                                             │
│   └── 检查点: 模块结构、数据流、接口契约                                      │
│                          ↓                                                  │
│   /speckit.design-dd                                                        │
│   ├── 输入: spec.md + ai-pd/ + pd-all/ + ad/                              │
│   ├── 输出: dd/ (模块化详细设计)                                             │
│   └── 检查点: 数据模型、状态机、算法、错误码                                  │
│                          ↓                                                  │
│   /speckit.plan                                                             │
│   ├── 输入: spec.md + ai-pd/ + pd-all/ + ad/ + dd/                        │
│   ├── 输出: plans/plan-<module>.md (实施规划桥梁)                           │
│   └── 检查点: 阶段规划、测试策略、风险识别                                    │
│                          ↓                                                  │
│   /speckit.tasks                                                            │
│   ├── 输入: ai-pd/ + pd-all/ + ad/ + dd/ + plans/plan-<module>.md         │
│   ├── 输出: tasks/ (按 PD 模块拆分的任务目录, TDD 强制)                      │
│   └── 检查点: 每模块独立可测、依赖清晰、覆盖全部 PD 交互                     │
│                          ↓                                                  │
│   /speckit.implement                                                        │
│   ├── 输入: tasks/ + module-rollout/state                                   │
│   ├── 输出: 代码实现                                                        │
│   └── 检查点: 单模块主控、测试通过、枚举一致性校验                            │
│                          ↓                                                  │
│   /speckit.smoke [module]                                                   │
│   ├── 输入: 运行中的前后端服务 + 目标模块                                    │
│   ├── 输出: 模块级浏览器验证报告（UI smoke + business e2e + probes）         │
│   └── 检查点: browser_verified                                              │
│                          ↓                                                  │
│   /speckit.review                                                           │
│   ├── 输入: 已实现代码 + ad/ + dd/ + constitution.md                        │
│   ├── 输出: Code Review 报告 (CRITICAL/MAJOR/MINOR)                         │
│   └── 检查点: CRITICAL/MAJOR 问题已修复、枚举一致性通过                      │
│                          ↓                                                  │
│   /speckit.smoke (全量，在 implement 全局完成门禁 C.6 触发)                  │
│   ├── 输入: 运行中的前后端服务                                              │
│   ├── 输出: 浏览器冒烟验证报告（逐页 9 项检查）                             │
│   └── 检查点: 严重问题已修复                                                │
│                          ↓                                                  │
│   人工验收                                                                  │
│   ├── 对照: PD 交互稿 + spec.md 验收场景                                    │
│   ├── 产出: defects/ (缺陷、需求优化)                                       │
│   └── 闭环: /speckit.defects → 分类路由 → 修复/设计补充/需求回溯             │
│                          ↓                                                  │
│   /speckit.defects (缺陷全生命周期)                                         │
│   ├── Phase 1: 扫描发现 → Phase 2: 分类路由                                │
│   ├── 代码修复路径: Phase 3-6 (分析→修复→设计回溯→验证)                     │
│   ├── 设计补充路径: → /speckit.design-dd → 补tasks → /speckit.implement     │
│   └── 需求回溯路径: → /speckit.specify 或 /speckit.design-pd → 重走设计链   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 研发主链与 Harness

### 研发主链

```text
spec
  -> HumanPD (pd-all/)
  -> AI-PD (ai-pd/)
  -> AD
  -> DD
  -> plan
  -> tasks
  -> implement
  -> smoke
  -> review / 验收
```

### Harness 的位置

`harness` 不是单独插在主链中的一个产物阶段，而是贯穿 `AI-PD -> AD -> DD -> plan -> tasks -> implement -> smoke` 的执行控制层与门禁层。

```text
研发产物流:
spec -> HumanPD -> AI-PD -> AD -> DD -> plan -> tasks -> implement -> smoke -> review

Harness 治理层:
          [前置检查 / gate / 模块状态 / 风险继承 / browser probes]
          └────────────────────────────────────────────────────────┘
```

### Harness 负责什么

- 检查阶段输入是否齐全
- 检查上游风险是否被下游显式继承
- 控制模块推进顺序与状态流转
- 在 `tasks / implement / browser` 等阶段执行 gate
- 防止跳过文档链直接进入实现或验收

## 命令详解

### 1. /speckit.specify - 需求澄清
**目的**: 将业务背景转化为结构化的业务需求文档

**使用场景**:
- 新项目启动
- 新增功能需求
- 需求澄清阶段

**输出**: `specs/{branch}/spec.md`

---

### 2. /speckit.design-pd - 产品交互设计
**目的**: 定义页面流程、状态变化和用户体验细节

**使用场景**:
- spec.md 完成后
- 需要定义交互细节时
- 前后端协作前

**输出**: `specs/{branch}/pd-all/`（HumanPD：含 pd-hub.html 统一入口 + pd-index.md 索引 + pd-<module>/ 各模块原型）

**关键产出**:
- 页面与需求映射表
- 页面状态矩阵
- 异常处理规范
- 可交互 HTML 原型
- 每个 HTML 页面对应的页面能力清单，其中 `page_goal` 与 `primary_user_flows` 为必填

---

### 2.5 /speckit.transform-pd - PD 转 AI-PD
**目的**: 将 HumanPD 转换为 AI、harness 和下游文档优先消费的 AI-PD

**使用场景**:
- `/speckit.design-pd` 完成后
- 进入 AD/DD/plan/tasks 前
- 需要把人类 PD 转成 AI 最佳阅读范式时

**输出**: `specs/{branch}/ai-pd/`（README.md 索引 + ai-<module>.md + ai-<module>.checklist.md）

**关键产出**:
- 页面级结构化语义块
- capability IDs
- action/data/rule/exception 契约
- 隐藏交互语义分类

**关键前置约束**:
- `pd-all/pd-<module>/README.md` 中每个 HTML 页面都必须显式提供 `page_goal`
- `pd-all/pd-<module>/README.md` 中每个 HTML 页面都必须显式提供 `primary_user_flows`
- 若缺失，`validate-stage-gates.ps1` 会触发 `GATE-PD-003`，下游不得继续

---

### 3. /speckit.design-ad - 架构设计
**目的**: 定义系统模块结构、数据流向和接口契约

**使用场景**:
- ai-pd/ 完成后（pd-all/ 作为视觉参考）
- 需要技术方案决策时
- 多模块协作前

**输出**: `specs/{branch}/ad/`（含 README.md 索引 + ad-global.md + ad-<module>.md；模块数 ≤ 3 时为单文件 ad.md）

**关键产出**:
- 领域划分
- 模块关系图
- 核心数据流（Mermaid 时序图）
- 接口契约（完整 API 表 + 示例）
- 技术选型

---

### 4. /speckit.design-dd - 详细设计
**目的**: 定义可实现的技术细节（数据模型、算法、状态机）

**使用场景**:
- ad.md 完成后
- 进入编码前
- 需要精确实现指导时

**输出**: `specs/{branch}/dd/`（含 README.md 索引 + dd-global.md + dd-<module>.md；模块数 ≤ 3 时为单文件 dd.md）

**关键产出**:
- 字段级数据模型（含 ER 图）
- 状态机转移规则
- 算法伪代码（含边界条件）
- 错误码体系（6 位编码）
- 权限点定义
- API 实现映射

---

### 5. /speckit.plan - 实施计划
**目的**: 基于完整设计制定可执行的实施计划（**实施规划桥梁**——承上设计、启下任务）

**使用场景**:
- 所有设计文档（spec + pd + ad + dd）完成后
- 需要精确估算和规划时

**输出**: `specs/{branch}/plans/plan-<module>.md`

**关键产出**:
- 技术背景速查（不重复 AD/DD 内容）
- 阶段规划（含检查点）
- 测试策略
- 风险识别

---

### 6. /speckit.tasks - 任务拆解
**目的**: 基于 AI-PD 拆解为独立的任务文件（AI-PD 是首要驱动源，HumanPD 作为视觉参考，AD/DD 提供实现细节，plan 提供阶段规划，TDD 强制）

**使用场景**:
- 所有设计文档 + 模块 plan 完成后
- 准备进入开发时

**输出**: `specs/{branch}/tasks/`（README.md 索引 + tasks-infra.md + tasks-\<module\>.md + tasks-refinement.md）

---

### 7. /speckit.implement - 执行实现
**目的**: 按照 tasks/ 目录中的任务文件执行实现，产出代码

**使用场景**:
- 随时开始开发
- 断点续传

**模式**:
- 指挥官+子代理工人模式
- `MasterAgent` 读取 tasks/README.md + module-rollout/state 调度，按模块派发任务
- 只允许单模块实现；同模块内任务可并行
- 自动进度追踪（各模块文件 + 全局索引）
- **模块检查点含枚举一致性校验**（DD 定义 vs 代码实际使用的权限点/错误码/状态枚举）

**命令**:
- `/speckit.implement` - 启动新实现
- `/speckit.implement continue` - 断点续传

---

### 8. /speckit.review - 代码审查
**目的**: 对已实现的代码发起结构化 Code Review，确保符合项目章程质量门禁

**使用场景**:
- 模块任务全部完成后（MUST）
- 全部模块完成准备交付时（MUST）
- 缺陷修复后（建议）
- 开发者主动请求

**命令**:
- `/speckit.review [module-name]` - 模块级审查
- `/speckit.review all` - 全量审查
- `/speckit.review [file-or-description]` - 针对性审查

**审查维度**: 安全 / 性能 / 错误处理 / 测试覆盖 / 代码规范 / 设计一致性 / **枚举一致性** / 前端质量

---

### 9. /speckit.defects - 缺陷全生命周期管理
**目的**: 统一管理缺陷的发现、分类、修复、设计回溯与验证闭环

**使用场景**:
- 手动触发扫描与统计
- 新增缺陷后的修复
- 缺陷状态检查

**命令**:
- `/speckit.defects` - 仅扫描与统计
- `/speckit.defects --auto` - 扫描并自动写入 related 字段
- `/speckit.defects 新增了缺陷 D0xx.md，请解决` - 扫描 + 修复

**六阶段流程**: 扫描发现 → 分类路由 → 根因分析 → 修复实施 → 设计回溯 → 验证闭环

**分类路由**:

| 缺陷类型 | 判断依据 | 处置路径 |
|----------|---------|---------|
| 代码 bug | category=接口/UI | Phase 3-6（本命令内完成） |
| 设计遗漏 | category=业务/规范 | 回到 /speckit.design-dd 补设计 |
| 需求变更 | category=需求 | 回到 /speckit.specify 或 /speckit.design-pd |

> **注意**: 原 `/speckit.fixbug` 命令已废弃，其功能已完整并入本命令。

---

## 辅助命令

### 10. /speckit.smoke - 浏览器冒烟验证
**目的**: 在真实浏览器中模拟用户操作，发现脚本化测试无法覆盖的 UI 渲染与交互问题

**使用场景**:
- implement 模块完成后的前移浏览器门禁
- implement 全局完成门禁（全量冒烟）
- 缺陷修复后验证涉及前端的页面（指定范围）
- 开发过程中随时自查

**命令**:
- `/speckit.smoke` - 全量：遍历所有页面
- `/speckit.smoke [module-name]` - 模块级：使用 rollout key，如 `pd-monitoring`
- `/speckit.smoke [page-path]` - 页面级：如 `/monitoring/device-logs`

**9 项检查**: 页面可达性、控制台、数据渲染、布局、关键交互、性能感知、权限、PD 符合性、业务链路冒烟

---

### 11. /speckit.clarify
**目的**: 对需求或设计进行澄清问答

**使用场景**:
- spec.md 有疑问时
- 设计决策需要讨论时

### 12. /speckit.analyze
**目的**: 分析代码或设计问题

**使用场景**:
- 排查缺陷根因
- 评审设计方案

### 13. /speckit.checklist
**目的**: 生成验收检查清单

**使用场景**:
- 功能完成前验收
- 确保覆盖所有需求点

### 14. /speckit.constitution
**目的**: 查看或引用项目章程

---

## 文档模板

模板分布在两个位置：

### 框架级模板（`.specify/templates/`）

| 模板 | 用途 | 对应命令 |
|-----|------|---------|
| `spec-template.md` | 业务需求结构 | `/speckit.specify` |
| `plan-template.md` | 实施计划结构（实施规划桥梁） | `/speckit.plan` |
| `tasks-template.md` | 任务目录结构（tasks/ 文件夹, TDD 强制） | `/speckit.tasks` |
| `checklist-template.md` | 验收检查清单结构 | `/speckit.checklist` |

### 设计规范模板（`specs/_template/`）

| 模板 | 用途 | 对应命令 |
|-----|------|---------|
| `pd-template.md` | 产品交互设计规范（pd-all/ 文件夹结构） | `/speckit.design-pd` |
| `ad-template.md` | 架构设计规范（ad/ 文件夹结构） | `/speckit.design-ad` |
| `dd-template.md` | 详细设计规范（dd/ 文件夹结构） | `/speckit.design-dd` |

### 缺陷模板（`specs/master/defects/`）

| 模板 | 用途 | 对应命令 |
|-----|------|---------|
| `_template.md` | 缺陷文件结构（含 design_ref 字段） | `/speckit.defects` |

---

## 快速参考

### 新建功能的完整流程

```bash
# 1. 创建分支目录
mkdir -p specs/feature-xxx

# 2. 按顺序执行（每个命令完成后检查输出）
/speckit.specify    # → spec.md
/speckit.design-pd  # → pd-all/
/speckit.design-ad  # → ad/ (或 ad.md)
/speckit.design-dd  # → dd/ (或 dd.md)
/speckit.plan       # → plans/plan-<module>.md
/speckit.tasks      # → tasks/ (任务目录)
/speckit.implement  # → 代码
/speckit.smoke pd-<module>  # → 模块级浏览器门禁
/speckit.review     # → Code Review 报告
/speckit.smoke      # → 全量浏览器冒烟
```

### 缺陷修复流程

```bash
# 1. 新增缺陷文件
cp specs/master/defects/_template.md specs/master/defects/D0xx.md
# 编辑 D0xx.md 填写现象、期望、复现步骤

# 2. 执行修复（扫描 + 分类 + 修复 + 回溯 + 验证 一站式）
/speckit.defects 新增了缺陷 D0xx.md，请解决
```

### 已有功能的迭代优化

```bash
# 只需补充缺失的设计文档
/speckit.design-pd  # 如交互有变更 → pd-all/
/speckit.design-ad  # 如架构有变更 → ad/
/speckit.design-dd  # 如细节有变更 → dd/
/speckit.plan       # 更新计划
/speckit.implement  # 执行变更
```

---

## 迁移指南

### 从旧流程迁移

如果你之前使用旧流程（spec → plan → tasks）:

1. **当前迭代**: 立即使用新流程补充 pd-all/ / ad/ / dd/
2. **历史功能**: 高优先级缺陷相关功能追溯补全设计
3. **模板更新**: 复制 `specs/_template/` 到新分支使用

### 从 /speckit.fixbug 迁移

`/speckit.fixbug` 已废弃，请改用：
```
/speckit.defects 新增了缺陷 D0xx.md，请解决
```

### 检查清单

- [ ] 已阅读当前命令索引与对应命令说明
- [ ] 已查看 `.specify/templates/` 与 `specs/_template/` 中的模板约定
- [ ] 已理解 `pd-all/ / ad/ / dd/ / plans/ / tasks/` 的阶段作用与先后顺序
- [ ] 已了解缺陷分类路由机制（代码修复 / 设计补充 / 需求回溯）
- [ ] 已准备按 `specify -> clarify -> design-pd -> design-ad -> design-dd -> plan -> tasks` 的顺序推进
