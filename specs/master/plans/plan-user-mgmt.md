# 实施计划: master / pd-user-mgmt

**分支**: `master` | **日期**: 2026-04-02 | **规范**: `specs/master/spec.md`  
**输入**: `specs/master/` 下的 `spec.md + pd-all + ai-pd/ai-user-mgmt.md + ad/ + dd/`

## 摘要

`pd-user-mgmt` 是平台权限与账号治理的基础模块。本模块已具备单页 HumanPD、AD、DD 和既有 tasks，但此前缺少模块 plan，也未把 `AI-PD` 接入下游链路，导致 `tasks / implement` gate 被阻断。本轮目标是把 `ai-user-mgmt.md` 作为主输入接入 `plan/tasks`，显式声明页面能力、隐藏交互、真实成功信号和范围边界，使后续阶段不再直接依赖 HumanPD 自行脑补。

## Pre-flight 一致性扫描

| 检查项 | 结果 (OK/WARNING/BLOCKER) | 结论 / 处理动作 |
|--------|---------------------------|----------------|
| FR 在 spec / AD / DD 中是否存在冲突 | OK | `FR-001` 在 HumanPD、AD、DD 中口径一致 |
| HumanPD 页面是否真实存在且可映射到 AI-PD | OK | `pd-user-mgmt/index.html` 已稳定映射到 `ai-user-mgmt.md` |
| AI-PD 是否覆盖 capability / action / data / rule / exception / hidden_interactions | OK | `ai-user-mgmt.md` 已覆盖单页主能力、两个业务弹窗、确认框和管理员保护规则 |
| plan 使用的源码路径是否与当前工程一致 | OK | 当前模块沿用既有 `backend/ + frontend/` 结构 |
| PD 是否存在部分覆盖/待补充项 | WARNING | `user-mgmt` 本地模块无部分覆盖，但当前 workspace 仍存在 `pd-intent-library` 条件准入，后续阶段不得把整个 feature 误判为“全模块无风险” |
| 关键外部依赖/异步链路是否定义真实成功信号 | OK | 用户目录、角色调整、状态切换、权限矩阵均可用同步回读验证 |

## 技术背景

**语言/版本**: Python 3.11 + React 18  
**主要依赖**: FastAPI、SQLAlchemy、Pydantic、Ant Design、React Router  
**存储**: PostgreSQL  
**测试**: pytest、Vitest、browser smoke  
**目标平台**: Windows 本地研发环境  
**项目类型**: Web 应用（`backend/` + `frontend/`）  
**性能目标**: 用户列表、统计卡、权限矩阵和角色变更结果均可在单次操作后真实回读  
**约束条件**: 权限判断必须基于 capability；不得用本地状态伪造列表/统计卡回读；至少保留一个启用管理员  
**规模/范围**: 单页用户管理模块，覆盖账号 CRUD 子集、角色调整、启停用、重置密码、权限矩阵

## 章程检查

- 文档链顺序固定：`spec -> PD -> AD -> DD -> plan -> tasks -> implement -> browser`
- 当前模块主输入固定为 `ai-pd/ai-user-mgmt.md`；`pd-all/pd-user-mgmt/` 仅作为 HumanPD 视觉参考
- `tasks-user-mgmt.md` 必须显式引用 `plans/plan-user-mgmt.md` 与 `ai-pd/ai-user-mgmt.md`
- 当前模块虽无局部 `Partial`，但 feature 级仍存在 `pd-intent-library` 条件准入，后续结论必须保留这一全局 warning

## 项目结构

### 设计文档（上游输入）

```text
specs/master/
├── spec.md
├── pd-all/
│   └── pd-user-mgmt/
├── ai-pd/
│   ├── README.md
│   └── ai-user-mgmt.md
├── ad/
│   └── ad-user-mgmt.md
├── dd/
│   └── dd-user-mgmt.md
├── plans/
│   └── plan-user-mgmt.md
└── tasks/
    └── tasks-user-mgmt.md
```

### 源代码

```text
backend/
├── app/
│   ├── api/
│   ├── services/
│   └── models/
└── tests/

frontend/
├── src/
│   ├── app/
│   ├── modules/
│   │   └── user-mgmt/
│   └── services/
```

**结构决策**: 用户管理保持“单页主入口 + 模态交互”的结构，前端所有关键结果必须依赖后端真实接口回读；后端继续以 capability-based RBAC 和管理员保护规则作为核心真相源。

## AI-PD 输入锚点

- **主输入文件**: `specs/master/ai-pd/ai-user-mgmt.md`
- **消费原则**:
  - capability / action / data / rule / exception 以 AI-PD 为准
  - 页面边界、单页布局和说明抽屉以 `pd-all/pd-user-mgmt/` 为参考
  - 若 HumanPD 与 AI-PD 不一致，必须先回修上游，不允许在实现阶段自行裁决

## 阶段规划

### 阶段 1: 文档链补齐
**目标**: 新增 `plan-user-mgmt.md`，让 `tasks-user-mgmt.md` 和 gate 显式接入 AI-PD  
**检查点**: `validate-stage-gates -Stage tasks -Module pd-user-mgmt` 不再因缺 plan / 缺 AI-PD 引用而阻断

### 阶段 2: 单页能力承接
**目标**: 以 `ai-user-mgmt.md` 的 capability/action/data/rule 为基线，确认单页能力与既有任务一一对应  
**检查点**: 创建账号、调整角色、启停用、重置密码、权限矩阵都有明确承接任务

### 阶段 3: 结果真实性验证
**目标**: 以列表回读、统计卡回读、token version 变化、管理员保护为真实成功信号  
**检查点**: 不存在用本地状态假更新替代接口回读的结论

## 模块核心业务链路

| 模块 | 链路名称 | 起点 | 终点/真实成功信号 | 覆盖方式 |
|------|---------|------|------------------|---------|
| `pd-user-mgmt` | 创建账号闭环 | 管理员打开“新建账号”弹窗并提交 | 列表新增用户、统计卡回读更新、审计日志落库 | contract + integration + page test |
| `pd-user-mgmt` | 角色调整闭环 | 管理员打开“编辑角色”弹窗并保存 | 用户角色更新、权限预览与新角色一致、旧 token 失效 | contract + integration + smoke |
| `pd-user-mgmt` | 启停用保护闭环 | 管理员切换状态开关 | 目标用户状态回读更新，内置 admin / 最后一个管理员保护生效 | contract + integration + smoke |

## AI-PD 承接矩阵（页面能力清单）

兼容当前 gate 检查口径：下表中的 `hidden_interactions` 同时承担旧 `interactive_containers` 字段语义。
其中 `ui-capability` 对应旧 `functional-hidden-ui`，`instructional` 对应旧 `explanatory-only`。

| 页面 | `page_boundary` | `visible_ui` | `hidden_interactions` | `capabilities` | 真实成功信号 / 风险 |
|------|-----------------|--------------|-----------------------|----------------|--------------------|
| `index` | `main-page` | 统计卡、用户列表、权限矩阵、操作按钮 | `instructional`: 说明抽屉；`ui-capability`: 新建账号 Modal / 编辑角色 Modal / 重置密码确认框；`domain-rule`: 管理员保护提示 | `CAP-UM-INDEX-001` ~ `CAP-UM-INDEX-006`；创建账号、调整角色、重置密码、启停用账号、查看权限矩阵 | 列表与统计卡来自真实回读；权限判断基于 capability；不得用本地假更新伪造成功 |

### 页面动作契约

| 页面 | `action_id` / 动作 | 前置条件 | 成功信号 | 失败反馈 | 状态变化 / 对应 API |
|------|--------------------|---------|---------|---------|--------------------|
| `index` | `ACT-002 / 创建账号` | 用户名、姓名、密码、角色合法 | 列表新增用户且统计卡回读更新 | 表单级错误 | `POST /api/v1/admin/users` |
| `index` | `ACT-003 / 调整角色与能力预览` | 目标用户存在且角色合法 | 列表回读更新、能力预览一致 | 弹窗内明确错误提示 | `PATCH /api/v1/admin/users/{id}/role` |
| `index` | `ACT-004 / 重置密码` | 目标用户存在 | 返回默认密码或重置结果 | 明确失败原因 | `POST /api/v1/admin/users/{id}/reset-password` |
| `index` | `ACT-005 / 启停用账号` | 目标用户存在且不触发管理员保护 | 状态切换后列表回读更新 | 开关回弹 + 错误提示 | `POST /api/v1/admin/users/{id}/status` |

### 数据契约 / 业务规则 / FR 映射

| 页面 | `data_contracts` / `business_rules` | 关联字段 / payload | 关联 FR |
|------|----------------------------------|--------------------|--------|
| `index` | `DATA-INDEX-001` ~ `DATA-INDEX-005` | `username`、`name`、`password`、`role`、`newRole` | `FR-001` |
| `index` | `RULE-001` | 权限判断必须基于 capability | `FR-001` |
| `index` | `RULE-002` / `RULE-003` | 内置管理员不可禁用；至少保留一个启用管理员 | `FR-001` |

## 显式未完成声明

- **Deferred**: 用户自主修改密码、SSO
- **Stub / 需要 501 的能力**: 无
- **Out of Scope**: 批量导入导出用户、自定义角色管理器
- **Blocked By**: 无
- **全局风险继承**: 当前 feature 仍存在 `pd-intent-library` 条件准入 warning；`user-mgmt` 本地模块不因此转为 Partial，但下游总结不得宣称整个 feature 已无设计风险

## 测试策略

| 测试类型 | 时机 | 覆盖目标 | 工具 |
|---------|------|---------|------|
| 契约测试 | API 稳定后 | 创建账号、改角色、改状态、权限矩阵 | pytest |
| 集成测试 | 服务层就绪后 | 审计日志、token version 递增、最后一个管理员保护 | pytest |
| 消费契约测试 | 前端联调前 | 列表、统计卡、权限矩阵数据回读形态 | Vitest |
| 页面测试 | 单页交互收口时 | 创建弹窗、角色弹窗、结果回读 | Vitest |
| Browser smoke | 模块收口时 | `permission_visibility`、`form_reset`、`result_readback` | browser automation |

## 风险与缓解

| 风险类型 | 描述 | 缓解策略 |
|---------|------|---------|
| 假成功风险 | 角色调整或状态切换仅更新前端本地状态 | 强制以接口回读作为完成信号 |
| 权限风险 | 继续按角色名硬编码权限判断 | 所有校验以 capability 为准，并在 AI-PD / DD / tests 中统一引用 |
| 全局文档风险 | feature 内仍有 `intent-library` 条件准入 warning | 在 plan / tasks 中显式继承全局风险，不误报“全局无风险” |
