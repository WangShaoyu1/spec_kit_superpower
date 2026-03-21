# 监控仪表盘 (Monitoring) 任务

**PD 交互原型**: pd-all/pd-monitoring/ (3 pages: index, device-logs, alert-rules)
**架构设计**: ad/ad-monitoring.md
**详细设计**: dd/dd-monitoring.md
**优先级**: P2
**依赖**: tasks-infra.md 必须先完成 (日志中间件已在 infra 中创建)

## 测试任务（TDD: 先写测试, 确保红灯）

### 契约测试（覆盖 AD API — 10 端点）

- [ ] T001 [P] [T-CONTRACT] 仪表盘 API 契约测试: GET /monitoring/dashboard
  - 文件: `backend/tests/contract/test_monitoring_dashboard_api.py`
  - 依据: ad/ad-monitoring.md §3.1
- [ ] T002 [P] [T-CONTRACT] 设备日志 + 会话链路 契约测试: GET /monitoring/device-logs, GET /monitoring/sessions/{id}/traces, GET /monitoring/logs
  - 文件: `backend/tests/contract/test_monitoring_logs_api.py`
  - 依据: ad/ad-monitoring.md §3.2
- [ ] T003 [P] [T-CONTRACT] 告警规则 CRUD + 事件 契约测试: GET/POST/PUT/DELETE /alert-rules, PUT /alert-rules/{id}/toggle, GET /alert-events
  - 文件: `backend/tests/contract/test_monitoring_alerts_api.py`
  - 依据: ad/ad-monitoring.md §3.3

### 集成测试（覆盖 AD 数据流）

- [ ] T004 [P] [T-INTEGRATION] 日志写入→指标聚合→仪表盘展示 集成测试
  - 文件: `backend/tests/integration/test_monitoring_pipeline.py`
  - 依据: ad/ad-monitoring.md §2.1 监控数据流
- [ ] T005 [P] [T-INTEGRATION] 告警规则评估→事件生成→状态流转 集成测试
  - 文件: `backend/tests/integration/test_alert_pipeline.py`
  - 依据: ad/ad-monitoring.md §2.2 告警数据流

### E2E 测试（覆盖 PD 交互路径）

- [ ] T006 [P] [T-E2E] 监控仪表盘页 E2E: 核心指标卡片+趋势图+实时刷新
  - 文件: `frontend/tests/e2e/monitoring-dashboard.spec.js`
  - 依据: pd-all/pd-monitoring/index.html
- [ ] T007 [P] [T-E2E] 告警规则页 E2E: 规则CRUD+启用禁用+事件列表
  - 文件: `frontend/tests/e2e/monitoring-alerts.spec.js`
  - 依据: pd-all/pd-monitoring/alert-rules.html

## 后端任务

### 数据模型（来自 DD 实体定义）

- [ ] T008 [P] [B-MODEL] 创建 RequestLog ORM 模型 (id, session_id, device_id, input_text, domain, intent, slots, confidence, latency_ms, status, created_at) + 按月分区策略
  - 文件: `backend/app/models/request_log.py`
  - 依据: dd/dd-monitoring.md §1.1
- [ ] T009 [P] [B-MODEL] 创建 AlertRule ORM 模型 (id, name, metric, operator, threshold, window_minutes, is_enabled, notification_channels)
  - 文件: `backend/app/models/alert_rule.py`
  - 依据: dd/dd-monitoring.md §1.2
- [ ] T010 [P] [B-MODEL] 创建 AlertEvent ORM 模型 (id, rule_id, status, fired_at, resolved_at, value)
  - 文件: `backend/app/models/alert_event.py`
  - 依据: dd/dd-monitoring.md §1.3
- [ ] T011 [P] [B-MODEL] 创建 Pydantic Schema (Dashboard/DeviceLog/AlertRule/AlertEvent Request/Response)
  - 文件: `backend/app/schemas/monitoring.py`
- [ ] T012 [B-MODEL] 生成 Alembic 迁移并运行 (request_logs 分区表, alert_rules, alert_events 表)
  - 文件: `backend/migrations/versions/006_monitoring.py`

### 服务层（来自 DD 算法）

- [ ] T013 [B-SERVICE] 指标聚合服务 (Redis 缓存 30s + 多维度聚合: 请求量/成功率/延迟/域分布)
  - 文件: `backend/app/services/monitoring/metrics.py`
  - 依据: dd/dd-monitoring.md §4.2 指标聚合算法
- [ ] T014 [B-SERVICE] 多维日志查询服务 (按设备/时间/域/意图 筛选 + 分页)
  - 文件: `backend/app/services/monitoring/log_query.py`
  - 依据: dd/dd-monitoring.md §4.3 多维日志查询
- [ ] T015 [B-SERVICE] 会话链路追踪服务 (按 session_id 聚合完整对话链路)
  - 文件: `backend/app/services/monitoring/log_query.py` (扩展)
  - 依据: dd/dd-monitoring.md §4.4
- [ ] T016 [B-SERVICE] 告警规则管理服务 (CRUD + 启用/禁用)
  - 文件: `backend/app/services/monitoring/alert_service.py`
  - 依据: dd/dd-monitoring.md §4.5
- [ ] T017 [B-SERVICE] 告警评估引擎 (30s 定时评估 + 事件生成 + 状态机: pending→firing→resolved + 同规则去重)
  - 文件: `backend/app/services/monitoring/alert_engine.py`
  - 依据: dd/dd-monitoring.md §4.6 告警评估算法

### API 端点（来自 AD 接口契约）

- [ ] T018 [B-API] 仪表盘 API: GET /monitoring/dashboard
  - 文件: `backend/app/api/v1/monitoring.py`
  - 依据: ad/ad-monitoring.md §3.1
- [ ] T019 [B-API] 设备日志 + 会话链路 + 请求日志 API
  - 文件: `backend/app/api/v1/monitoring.py` (扩展)
  - 依据: ad/ad-monitoring.md §3.2
- [ ] T020 [B-API] 告警规则 CRUD + 启用禁用 + 事件列表 API
  - 文件: `backend/app/api/v1/monitoring.py` (扩展)
  - 依据: ad/ad-monitoring.md §3.3

## 前端任务

### 页面（来自 PD 交互原型）

- [ ] T021 [F-PAGE] 监控仪表盘页: 核心指标卡片+趋势折线图+域分布饼图+自动刷新(30s)
  - 文件: `frontend/src/pages/Monitoring/index.jsx`
  - 依据: pd-all/pd-monitoring/index.html
  - **PD UI Checklist** (dd-monitoring.md §10):
    - [ ] 8 个指标卡片 (§10.1): 总请求量(24h) / 实时 QPS / 平均延迟 / P95·P99 延迟 / 意图识别准确率 / 错误率 / 平均对话轮次 / 路由分布迷你 Progress
    - [ ] 路由分布水平条形图 (§10.5 #2): 三行渐变色条 (指令蓝/知识绿/闲聊紫) + 请求数 + 涨跌 Tag
    - [ ] 请求日志表 9 列 (§10.2.1): 请求ID / 时间 / 设备ID(超链接) / 输入文本(ellipsis+Tooltip) / 路由(Tag) / 意图 / 置信度(Progress色阶) / 响应耗时(色阶Tag+可排序) / 状态(Tag)
    - [ ] 多维筛选器 6 项 (§10.3.1): 时间范围(RangePicker) / 设备ID(Input) / 路由类型(Select) / 意图名称(Input) / 响应耗时(Select 5档) / 是否异常(Select) + 查询·重置按钮
    - [ ] 30s 自动刷新倒计时 Badge (§10.5 #1): ≤5s 变橙; 归零自动刷新; 手动刷新重置; Spin 覆盖
    - [ ] 页面顶部按钮 (§10.4.1): 手动刷新 / 设备日志导航 / 告警规则导航
    - [ ] 设备 ID 列超链接跳转 device-logs.html?device={id}
- [ ] T022 [F-PAGE] 设备日志页: 设备会话列表+会话链路详情(消息流)+多维筛选
  - 文件: `frontend/src/pages/Monitoring/DeviceLogs.jsx`
  - 依据: pd-all/pd-monitoring/device-logs.html
  - **PD UI Checklist** (dd-monitoring.md §10):
    - [ ] 设备 ID 搜索框 (§10.3.2): Input(prefix=SearchOutlined, size=large) + 查询按钮; Enter 触发; 空值 warning
    - [ ] 设备信息网格 6 格 (§10.1 / §10.5 #6): 首次接入 / 最后活跃 / 总会话数 / 总请求数 / 使用版本(Tag cyan) / 设备状态(Tag green)
    - [ ] 会话列表表 7 列 (§10.2.2): 会话ID(monospace) / 开始时间 / 结束时间(或"进行中"Tag) / 对话轮次(Badge蓝) / 使用版本(Tag) / 路由分布(多Tag) / 操作(查看链路/收起链路)
    - [ ] 会话摘要卡片 (§10.1): 会话ID / 持续时间 / 对话轮次 / 使用版本 / 路由分布 (链路展开时顶部 inner Card)
    - [ ] 会话链路 Timeline (§10.5 #7): dot 颜色按域 (蓝=指令/绿=知识/橙=闲聊); "第N轮" Tag + request_id; 时序正排
    - [ ] 请求链路 Collapse 详情 (§10.5 #8): 输入→路由(Progress)→意图→槽位表(§10.2.5)→知识命中(Descriptions)→指代消解→人设→对话状态→响应(蓝边框)→耗时(Statistic色阶)→设备上下文JSON
    - [ ] 空状态引导 (§10.5 #14): 未搜索时 Empty + DesktopOutlined 图标 + 引导文案
    - [ ] 页面按钮 (§10.4.2): 返回 / 查询 / 查看链路·收起链路
- [ ] T023 [F-PAGE] 告警规则页: 规则列表+新建/编辑弹窗+启用/禁用开关+告警事件时间线
  - 文件: `frontend/src/pages/Monitoring/AlertRules.jsx`
  - 依据: pd-all/pd-monitoring/alert-rules.html
  - **PD UI Checklist** (dd-monitoring.md §10):
    - [ ] 3 个统计卡片 (§10.1): 活跃告警(红色+pulse动画) / 规则总数 / 已启用(绿色)+已禁用
    - [ ] 告警事件 Collapse (§10.5 #12): "最近告警记录" + 事件数Tag; 默认展开; 内嵌事件表(size=small, 无分页)
    - [ ] 告警事件表 7 列 (§10.2.4): 告警时间 / 规则名称 / 指标(Tag) / 触发值 / 阈值 / 持续时间 / 状态(红=触发中/绿=已恢复)
    - [ ] 告警规则表 8 列 (§10.2.3): 规则名称 / 监控指标(Tag) / 条件 / 持续时间 / 通知方式(多Tag) / 状态(Switch启用/禁用) / 上次触发 / 操作(编辑+删除)
    - [ ] 新建/编辑规则 Modal (§10.5 #10): 规则名称(Input) / 监控指标(Select 6选项) / 条件(动态InputNumber按指标类型) / 持续时间+单位(秒/分钟/小时) / 通知方式(Checkbox.Group) / Webhook URL(条件显示)
    - [ ] 删除确认 Modal (§10.5 #11): Modal.confirm, okType=danger, 含规则名称
    - [ ] 页面按钮 (§10.4.3): 返回 / 新建规则(primary) / 编辑(link) / 删除(danger link) / 启用禁用Switch

### 组件（可复用）

- [ ] T024 [P] [F-COMPONENT] 指标趋势图组件 (ECharts/Ant Design Charts 折线图+自动刷新)
  - 文件: `frontend/src/pages/Monitoring/MetricsChart.jsx`
- [ ] T025 [P] [F-COMPONENT] 会话链路组件 (消息流时间线+分域标记+耗时标注)
  - 文件: `frontend/src/pages/Monitoring/SessionTrace.jsx`

### 状态管理与 API 对接

- [ ] T026 [F-STORE] 监控状态管理 (zustand): 仪表盘数据/日志列表/告警规则/事件
  - 文件: `frontend/src/stores/monitoringStore.js`
- [ ] T027 [F-API] 监控 API 对接层: 全部 10 端点的前端调用封装
  - 文件: `frontend/src/services/monitoringApi.js`

## 检查点

**模块验收标准**（对照 PD 交互稿）:
- [ ] 所有测试通过（T001~T007 红灯→绿灯）
- [ ] 仪表盘: 核心指标(请求量/成功率/延迟/域分布)实时展示+30s 自动刷新
- [ ] 设备日志: 按设备/时间/域/意图 多维筛选+会话链路追踪 可用
- [ ] 告警规则: CRUD+启用禁用+30s 定时评估+事件生成 可用
- [ ] 告警事件: 状态流转 pending→firing→resolved 正确
- [ ] RequestLog 分区表按月分区正常工作
- [ ] 无回归（infra + 先前模块测试仍通过）
