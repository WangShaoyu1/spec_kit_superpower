# 实施计划: master / pd-monitoring

**分支**: `master` | **日期**: 2026-03-31 | **规范**: `specs/master/spec.md`  
**输入**: `specs/master/` 下的 `spec.md + pd-all + ad/ + dd/`

## 摘要

在正式 `backend/ + frontend/` 单体工程中完成 `pd-monitoring` 模块，交付运行态监控总览、请求日志多维筛选、设备会话链路排查和告警规则配置三类能力。实现策略采用 FastAPI + PostgreSQL 保存请求日志、监控快照、告警规则与事件；前端采用 React + Ant Design 实现监控仪表盘、设备日志页和告警规则页，并确保所有指标、会话链路和告警状态都来自后端真实回读。

## Pre-flight 一致性扫描

| 检查项 | 结果 (OK/WARNING/BLOCKER) | 结论 / 处理动作 |
|--------|---------------------------|----------------|
| FR 在 spec / AD / DD 中是否存在冲突 | OK | FR-030~032,034~035,038 已收口到 `pd-monitoring` |
| PD 页面是否真实存在且被 AD 正确引用 | OK | `pd-monitoring` 的 dashboard/device-logs/alert-rules 页面已存在 |
| plan 使用的源码路径是否与当前工程一致 | OK | 唯一真相源仍为 `backend/ + frontend/` |
| 依赖模块是否已达到可接入状态 | OK | 前序模块均为 `browser_verified`，可提供请求日志/批测/方案引用 |
| 关键成功信号是否可真实观测 | OK | overview 指标、session trace、alert event 都要求后端回读 |

## 技术背景

**语言/版本**: Python 3.10 + React 18  
**主要依赖**: FastAPI、SQLAlchemy、Pydantic Settings、React Router、Ant Design  
**存储**: PostgreSQL (`postgresql+psycopg://smartchef:smartchef@127.0.0.1:5432/smartchef`)  
**测试**: pytest、Vitest、browser smoke  
**目标平台**: Windows 本地研发环境，后续切换线上 PG  
**项目类型**: Web 应用（`backend/` + `frontend/`）  
**性能目标**: 近 15 分钟 overview 查询在 2 秒内返回；日志筛选支持分页；单会话 trace 可完整回读  
**约束条件**: 不允许前端自行聚合关键监控指标；告警规则不能只存配置不产出事件；请求日志字段必须覆盖 FR-033 所需链路信息  
**规模/范围**: 首版支持 overview、请求日志筛选、设备会话 trace、规则创建/停用与最近触发记录

## 章程检查

- 文档链顺序固定：`spec -> PD -> AD -> DD -> plan -> tasks -> implement -> browser`
- `pd-batch-test` 已达到 `browser_verified`，满足本模块实现依赖
- 不允许用静态文案冒充 QPS、延迟、准确率、会话链路或告警触发
- 继续沿用“每个业务模块单独 router、`main.py` 只装配”的拆分规则

## 项目结构

### 设计文档（上游输入）

```text
specs/master/
├── spec.md
├── pd-all/
│   └── pd-monitoring/
├── ad/
│   ├── README.md
│   ├── ad-global.md
│   └── ad-monitoring.md
├── dd/
│   ├── README.md
│   ├── dd-global.md
│   └── dd-monitoring.md
├── plans/
│   ├── README.md
│   └── plan-monitoring.md
└── tasks/
```

### 源代码

```text
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
│   │   └── monitoring/
│   └── services/
└── tests/
```

**结构决策**: 在 `backend/app/api/monitoring.py` 中实现监控接口；前端新增 `modules/monitoring` 页面，并通过 router 接入仪表盘、设备日志和告警规则三个页面。

## 阶段规划

### 阶段 1: 文档链补齐与 gate 对齐
**目标**: 补齐 `ad-monitoring.md`、`dd-monitoring.md`、`plans/plan-monitoring.md`、`tasks-monitoring.md`  
**检查点**: `ad/dd/tasks` gate 无 blocker

### 阶段 2: 后端核心闭环
**目标**: 实现 overview 聚合、请求日志筛选、设备会话 trace、告警规则与事件收敛  
**检查点**: 契约/集成测试覆盖指标、筛选、trace、规则

### 阶段 3: 前端模块接入
**目标**: 实现监控仪表盘、设备日志页、告警规则页与路由菜单  
**检查点**: 登录后可进入 `/monitoring` 并完成刷新、筛选、查看 trace、管理规则主链路

### 阶段 4: 模块验证与收口
**目标**: 完成 browser stage、修复缺陷并推进到 `browser_verified`  
**检查点**: `overview_real_metrics`、`device_trace_drilldown`、`alert_rule_feedback` 均通过 smoke

## 模块核心业务链路

| 模块 | 链路名称 | 起点 | 终点/真实成功信号 | 覆盖方式 |
|------|---------|------|------------------|---------|
| `pd-monitoring` | 查看监控总览 | PM 打开页面或点击刷新 | overview 指标、路由分布、最近告警真实回读 | contract + UI test + smoke |
| `pd-monitoring` | 设备日志排查 | PM 输入设备 ID 并点开会话 | session list 与逐轮 trace 真实回读 | contract + UI test + smoke |
| `pd-monitoring` | 管理告警规则 | PM 创建或停用规则 | 规则列表与最近事件真实变化 | contract + integration + smoke |

## 显式未完成声明

- **Deferred**: 外部告警通知通道、长时间窗口趋势图、设备侧满意度/完成率回传
- **Stub / 需要 501 的能力**: 无
- **Out of Scope**: 生产级日志采集管道、真实消息通知基础设施
- **Blocked By**: 无
- **路径单一真相源**: `backend/ + frontend/`

## 测试策略

| 测试类型 | 时机 | 覆盖目标 | 工具 |
|---------|------|---------|------|
| 契约测试 | API 完成后 | overview、日志筛选、会话详情、规则 CRUD | pytest + TestClient |
| 集成测试 | 后端闭环完成时 | 告警规则求值、事件状态收敛、overview 聚合 | pytest |
| 消费契约测试 | 前端联调前 | API 请求形态、分页与筛选参数 | Vitest |
| 页面测试 | 前端页面接入时 | dashboard/device logs/alert rules 关键回读流程 | Vitest |
| Browser smoke | 页面接近完成时 | `overview_real_metrics`、`device_trace_drilldown`、`alert_rule_feedback` | browser automation |

## 风险与缓解

| 风险类型 | 描述 | 缓解策略 |
|---------|------|---------|
| 技术风险 | 请求日志字段不全导致 trace 无法闭环 | 先固定 `request_log` JSON 口径，再做 UI |
| 指标风险 | 准确率/延迟由前端聚合导致假成功 | 后端统一聚合 overview 返回 |
| 进度风险 | 三个页面分散、接口较多 | 先打通 overview -> trace -> rules 主闭环 |
| 假成功风险 | 规则保存成功但永不触发事件 | 引入 `alert_event` 并在读取时执行收敛判断 |
