# 实施计划: master / pd-dialog-profile

**分支**: `master` | **日期**: 2026-03-31 | **规范**: `specs/master/spec.md`
**输入**: `specs/master/` 下的 `spec.md + pd-all + ad/ + dd/`

## 摘要

在正式 `backend/ + frontend/` 单体工程中完成 `pd-dialog-profile` 模块，交付对话方案目录、详情配置、发布门禁、手动测试聊天页与会话隔离。实现策略采用 FastAPI + PostgreSQL 保存方案、绑定库、测试会话和消息记录，继续沿用模块化路由；前端采用 React + Ant Design 实现方案列表、详情编辑页与测试页，并以真实后端回读展示调试 trace。

## Pre-flight 一致性扫描

| 检查项 | 结果 (OK/WARNING/BLOCKER) | 结论 / 处理动作 |
|--------|---------------------------|----------------|
| FR 在 spec / AD / DD 中是否存在冲突 | OK | `FR-007~011`、`FR-015~016`、`FR-040`、`FR-047` 已收口到对话方案模块职责 |
| PD 页面是否真实存在且被 AD 正确引用 | OK | `pd-dialog-profile` 的 `index/detail/test-chat` 页面完整存在 |
| plan 使用的源码路径是否与当前工程一致 | OK | 唯一真相源仍为 `backend/ + frontend/` |
| PD 是否存在部分覆盖/待补充项 | OK | 批量测试链路明确归属 `pd-batch-test`，本模块边界清晰 |
| 关键外部依赖/异步链路是否定义真实成功信号 | OK | 发布门禁、手动测试 trace、会话隔离均定义了真实成功信号 |

## 技术背景

**语言/版本**: Python 3.10 + React 18  
**主要依赖**: FastAPI、SQLAlchemy、Pydantic Settings、React Router、Ant Design  
**存储**: PostgreSQL (`postgres:postgres@127.0.0.1:5432/smartchef`)  
**测试**: pytest、Vitest、browser smoke  
**目标平台**: Windows 本地研发环境，后续切换线上 PG  
**项目类型**: Web 应用（`backend/` + `frontend/`）  
**性能目标**: 手动测试单条响应 p95 < 1500ms，调试 trace 展示无缺项  
**约束条件**: 不允许前端自造 assistant 消息、调试 trace 或发布成功；会话必须按 `session_id` 隔离  
**规模/范围**: 首版支持方案 CRUD、库绑定、基础人设、发布门禁、手动测试与调试面板

## 章程检查

- 文档链顺序固定：`spec -> PD -> AD -> DD -> plan -> tasks -> implement -> browser`
- `pd-knowledge-base` 已达到 `browser_verified`，满足本模块实现依赖
- 不允许用静态文案冒充 assistant 回复、发布成功、调试 trace 或会话隔离
- 继续沿用“每个业务模块单独 router、`main.py` 只装配”的拆分规则

## 项目结构

### 设计文档（上游输入）

```
specs/master/
├── spec.md
├── pd-all/
│   └── pd-dialog-profile/
├── ad/
│   ├── README.md
│   ├── ad-global.md
│   └── ad-dialog-profile.md
├── dd/
│   ├── README.md
│   ├── dd-global.md
│   └── dd-dialog-profile.md
├── plans/
│   ├── README.md
│   └── plan-dialog-profile.md
└── tasks/
```

### 源代码

```
backend/
├── app/
│   ├── api/
│   ├── dependencies.py
│   ├── models.py
│   └── main.py
└── tests/

frontend/
├── src/
│   ├── app/
│   ├── modules/
│   │   └── dialog-profile/
│   └── services/
└── tests/
```

**结构决策**: 沿用已经完成的模块化后端结构，在 `backend/app/api/dialog_profile.py` 中实现对话方案接口；前端新增 `modules/dialog-profile` 页面，并复用统一菜单壳、权限体系与 API 客户端。

## 阶段规划

### 阶段 1: 文档链补齐与 gate 对齐
**目标**: 补齐 `ad-dialog-profile.md`、`dd-dialog-profile.md`、`plans/plan-dialog-profile.md`、`tasks-dialog-profile.md`  
**检查点**: `ad/dd/tasks` gate 无 blocker

### 阶段 2: 后端核心闭环
**目标**: 实现方案目录、详情、发布门禁、测试会话与消息接口  
**检查点**: 契约测试覆盖方案 CRUD、发布门禁、会话创建、发消息与 trace 字段

### 阶段 3: 前端模块接入
**目标**: 实现对话方案列表页、详情页、测试页与路由接入  
**检查点**: 登录后可进入 `/dialog-profiles` 并完成新建、编辑、测试、发布门禁主链路

### 阶段 4: 模块验证与收口
**目标**: 完成 browser stage、修复缺陷并推进到 `browser_verified`  
**检查点**: `profile_publish_gate`、`manual_test_trace`、`session_isolation` 均通过 smoke

## 模块核心业务链路

| 模块 | 链路名称 | 起点 | 终点/真实成功信号 | 覆盖方式 |
|------|---------|------|------------------|---------|
| `pd-dialog-profile` | 创建方案 | PM 提交新建方案弹窗 | 列表新增记录，状态统计回读更新 | contract + UI test + smoke |
| `pd-dialog-profile` | 保存详情配置 | PM 修改模型/人设/阈值/绑定库 | 详情接口回读与保存结果一致 | contract + UI test |
| `pd-dialog-profile` | 手动测试消息 | 测试页发送文本 | 返回 assistant 消息、debug trace、response_time_ms | contract + integration + UI test + smoke |
| `pd-dialog-profile` | 发布门禁 | 详情页点击发布 | 未满足条件时真实阻断并展示 blocker；满足时 published 切换成功 | contract + smoke |

## 显式未完成声明

- **Deferred**: 多版本回滚、真实在线 LLM 调用、复杂多轮上下文状态机
- **Stub / 需要 501 的能力**: 无
- **Out of Scope**: 生产 API 路由编排、批量测试分析、线上设备热更新执行链路
- **Blocked By**: 无
- **路径单一真相源**: `backend/ + frontend/`

## 测试策略

| 测试类型 | 时机 | 覆盖目标 | 工具 |
|---------|------|---------|------|
| 契约测试 | API 完成后 | 方案 CRUD、发布门禁、会话创建、发消息、published 切换 | pytest + TestClient |
| 集成测试 | 后端闭环完成时 | 会话隔离、trace 字段、message_count 与版本归档 | pytest |
| 消费契约测试 | 前端联调前 | 列表、详情、测试页、发布与 trace 形态 | Vitest |
| Browser smoke | 页面接近完成时 | `profile_publish_gate`、`manual_test_trace`、`session_isolation` | browser automation |

## 风险与缓解

| 风险类型 | 描述 | 缓解策略 |
|---------|------|---------|
| 技术风险 | 手动测试容易被做成前端假回复 | 所有消息和调试信息以后端回读为准 |
| 发布风险 | 前端门禁和后端门禁口径不一致 | 发布前统一走后端 `publish guard` |
| 进度风险 | 列表、详情、测试页点位较多 | 先打通方案→测试→发布主闭环，再补 UI 细节 |
| 假成功风险 | trace 或 response_time 使用硬编码 | contract + integration + smoke 同时校验关键字段 |
