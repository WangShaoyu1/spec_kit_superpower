# AI-PD: monitoring

```yaml
module_key: monitoring
based_on:
  - spec.md
  - pd-all/pd-index.md
  - pd-all/pd-monitoring/README.md
  - pd-all/pd-monitoring/alert-rules.html
  - pd-all/pd-monitoring/device-logs.html
  - pd-all/pd-monitoring/index.html
status: pilot
```

## 模块摘要

- **模块目标**: 出现质量异常时，团队可从仪表盘快速定位到具体设备和请求链路
- **来源 HumanPD**: `pd-all/pd-monitoring/`
- **覆盖 FR**: FR-030, FR-031, FR-032, FR-033, FR-034, FR-035, FR-036, FR-038
- **转换口径**: 本文件由半自动脚本生成，用作 AI-PD scaffold，允许后续人工精修

## 页面索引

| page_id | page_name | page_boundary | route_or_entry | capability_count | related_fr |
|---------|-----------|---------------|----------------|------------------|------------|
| `monitoring.alert-rules` | 告警规则配置 | `sub-page` | `alert-rules.html` | 3 | FR-030, FR-031, FR-032, FR-033, FR-034, FR-035, FR-036, FR-038 |
| `monitoring.device-logs` | 设备日志 | `sub-page` | `device-logs.html` | 1 | FR-030, FR-031, FR-032, FR-033, FR-034, FR-035, FR-036, FR-038 |
| `monitoring.index` | 监控仪表盘 | `main-page` | `index.html` | 1 | FR-030, FR-031, FR-032, FR-033, FR-034, FR-035, FR-036, FR-038 |

## Page: monitoring.alert-rules

```yaml
page_id: monitoring.alert-rules
page_name: 告警规则配置
page_boundary: sub-page
goal: 出现质量异常时，团队可从仪表盘快速定位到具体设备和请求链路
route_or_entry: alert-rules.html
parent_page: monitoring.index
```

### primary_user_flows

- 观察 QPS、延迟、准确率和错误率的整体趋势
- 按设备 ID 回查历史会话，查看单轮请求处理链路
- 配置准确率下降、延迟超标、错误率突增的告警规则

### visible_ui

| ui_id | type | label | purpose | source |
|------|------|-------|---------|--------|
| `UI-ALERT_RULES-001` | `stats` | 统计卡 | 规则总数, 已启用 | prototype state |
| `UI-ALERT_RULES-002` | `table` | 表格 | 规则名称, 监控指标, 条件, 持续时间, 通知方式, 状态, 上次触发, 操作 | prototype columns |
| `UI-ALERT_RULES-003` | `table` | 表格 | 告警时间, 规则名称, 指标, 触发值, 阈值, 持续时间, 状态 | prototype columns |
| `UI-ALERT_RULES-004` | `actions` | 操作入口 | 编辑, 删除, 返回, 说明, 新建规则 | page actions |

### hidden_interactions

| hidden_id | container | classification | entry | purpose |
|-----------|-----------|----------------|-------|---------|
| `HID-ALERT_RULES-001` | `drawer` | `instructional` | 说明按钮 | 解释页面逻辑、状态流转、字段说明和易错点 |

### capabilities

| capability_id | title | type | priority | done_signal |
|---------------|-------|------|----------|-------------|
| `CAP-M-ALERT_RULES-001` | 查看页面主数据 | `DATA` | `P0` | 页面主数据来自真实回读，而非本地硬编码 |
| `CAP-M-ALERT_RULES-002` | 编辑当前项 | `CRUD` | `P1` | 保存后页面主数据回读为最新值 |
| `CAP-M-ALERT_RULES-003` | 删除当前项 | `CRUD` | `P1` | 删除后列表或详情不再显示目标项 |

### action_contracts

| action_id | action | preconditions | success_signal | failure_feedback | state_change |
|-----------|--------|---------------|----------------|------------------|--------------|
| `ACT-002` | 编辑当前项 | 必要字段合法且权限满足 | 保存后页面主数据回读为最新值 | 必须给出明确错误提示，不允许假成功 | 编辑当前项 |
| `ACT-003` | 删除当前项 | 必要字段合法且权限满足 | 删除后列表或详情不再显示目标项 | 必须给出明确错误提示，不允许假成功 | 删除当前项 |

### data_contracts

| data_id | field_or_column | shape | required | source | notes |
|---------|-----------------|-------|----------|--------|-------|
| `DATA-ALERT_RULES-001` | `name` | `string` | `yes` | form field | 规则名称 |
| `DATA-ALERT_RULES-002` | `metric` | `string` | `yes` | form field | 监控指标 |
| `DATA-ALERT_RULES-003` | `conditionValue` | `string` | `yes` | form field | 条件 |
| `DATA-ALERT_RULES-004` | `duration` | `string` | `yes` | form field | 持续时间 |
| `DATA-ALERT_RULES-005` | `durationUnit` | `string` | `yes` | form field | 单位 |
| `DATA-ALERT_RULES-006` | `notify` | `string` | `yes` | form field | 通知方式 |
| `DATA-ALERT_RULES-007` | `webhookUrl` | `string` | `yes` | form field | Webhook URL |

### business_rules

| rule_id | rule | scope | related_capability |
|---------|------|-------|--------------------|
| `RULE-NONE` | 当前页面未自动识别到额外业务规则 | n/a | `n/a` |

### exception_flows

| exception_id | scenario | expected_feedback | recovery |
|--------------|----------|-------------------|----------|
| `EX-NONE` | 当前页面未自动识别到异常流 | - | - |

## Page: monitoring.device-logs

```yaml
page_id: monitoring.device-logs
page_name: 设备日志
page_boundary: sub-page
goal: 出现质量异常时，团队可从仪表盘快速定位到具体设备和请求链路
route_or_entry: device-logs.html
parent_page: monitoring.index
```

### primary_user_flows

- 观察 QPS、延迟、准确率和错误率的整体趋势
- 按设备 ID 回查历史会话，查看单轮请求处理链路
- 配置准确率下降、延迟超标、错误率突增的告警规则

### visible_ui

| ui_id | type | label | purpose | source |
|------|------|-------|---------|--------|


### hidden_interactions

| hidden_id | container | classification | entry | purpose |
|-----------|-----------|----------------|-------|---------|
| `HID-DEVICE_LOGS-001` | `drawer` | `instructional` | 说明按钮 | 解释页面逻辑、状态流转、字段说明和易错点 |

### capabilities

| capability_id | title | type | priority | done_signal |
|---------------|-------|------|----------|-------------|
| `CAP-M-DEVICE_LOGS-001` | 完成页面主要操作 | `STATE` | `P0` | 关键操作结果必须真实回读 |

### action_contracts

| action_id | action | preconditions | success_signal | failure_feedback | state_change |
|-----------|--------|---------------|----------------|------------------|--------------|
| `ACT-001` | 完成页面主要操作 | 必要字段合法且权限满足 | 关键操作结果必须真实回读 | 必须给出明确错误提示，不允许假成功 | 完成页面主要操作 |

### data_contracts

| data_id | field_or_column | shape | required | source | notes |
|---------|-----------------|-------|----------|--------|-------|
| `DATA-NONE` | `n/a` | `n/a` | `no` | derived | 当前页面未识别出表单字段 |

### business_rules

| rule_id | rule | scope | related_capability |
|---------|------|-------|--------------------|
| `RULE-NONE` | 当前页面未自动识别到额外业务规则 | n/a | `n/a` |

### exception_flows

| exception_id | scenario | expected_feedback | recovery |
|--------------|----------|-------------------|----------|
| `EX-NONE` | 当前页面未自动识别到异常流 | - | - |

## Page: monitoring.index

```yaml
page_id: monitoring.index
page_name: 监控仪表盘
page_boundary: main-page
goal: 出现质量异常时，团队可从仪表盘快速定位到具体设备和请求链路
route_or_entry: index.html
parent_page: none
```

### primary_user_flows

- 观察 QPS、延迟、准确率和错误率的整体趋势
- 按设备 ID 回查历史会话，查看单轮请求处理链路
- 配置准确率下降、延迟超标、错误率突增的告警规则

### visible_ui

| ui_id | type | label | purpose | source |
|------|------|-------|---------|--------|
| `UI-INDEX-001` | `table` | 表格 | 请求 ID, 时间, 设备 ID, 输入文本, 路由, 意图, 置信度, 响应耗时, 状态 | prototype columns |
| `UI-INDEX-002` | `actions` | 操作入口 | 手动刷新, 说明, 设备日志, 告警规则, 查询, 重置 | page actions |

### hidden_interactions

| hidden_id | container | classification | entry | purpose |
|-----------|-----------|----------------|-------|---------|
| `HID-INDEX-001` | `drawer` | `instructional` | 说明按钮 | 解释页面逻辑、状态流转、字段说明和易错点 |

### capabilities

| capability_id | title | type | priority | done_signal |
|---------------|-------|------|----------|-------------|
| `CAP-M-INDEX-001` | 查看页面主数据 | `DATA` | `P0` | 页面主数据来自真实回读，而非本地硬编码 |

### action_contracts

| action_id | action | preconditions | success_signal | failure_feedback | state_change |
|-----------|--------|---------------|----------------|------------------|--------------|
| `ACT-NONE` | 无需显式动作契约 | - | - | - | - |

### data_contracts

| data_id | field_or_column | shape | required | source | notes |
|---------|-----------------|-------|----------|--------|-------|
| `DATA-NONE` | `n/a` | `n/a` | `no` | derived | 当前页面未识别出表单字段 |

### business_rules

| rule_id | rule | scope | related_capability |
|---------|------|-------|--------------------|
| `RULE-NONE` | 当前页面未自动识别到额外业务规则 | n/a | `n/a` |

### exception_flows

| exception_id | scenario | expected_feedback | recovery |
|--------------|----------|-------------------|----------|
| `EX-NONE` | 当前页面未自动识别到异常流 | - | - |


## acceptance_signals

- 页面关键结果必须能真实回读，不能只依赖 toast、静态 mock 或本地状态假更新。
- 隐藏交互只有在 AI-PD 中被标为 `instructional / non-actionable-note` 时才能排除出实现闭环。
- 当前输出为半自动 scaffold；若发现能力、契约或异常流缺项，必须继续人工补全。

## fr_mapping

| capability_id | fr_id | status |
|---------------|------|--------|
| `CAP-M-ALERT_RULES-001` | `FR-030` | `full` |
| `CAP-M-ALERT_RULES-001` | `FR-031` | `full` |
| `CAP-M-ALERT_RULES-001` | `FR-032` | `full` |
| `CAP-M-ALERT_RULES-001` | `FR-033` | `full` |
| `CAP-M-ALERT_RULES-001` | `FR-034` | `full` |
| `CAP-M-ALERT_RULES-001` | `FR-035` | `full` |
| `CAP-M-ALERT_RULES-001` | `FR-036` | `full` |
| `CAP-M-ALERT_RULES-001` | `FR-038` | `full` |
| `CAP-M-ALERT_RULES-002` | `FR-030` | `full` |
| `CAP-M-ALERT_RULES-002` | `FR-031` | `full` |
| `CAP-M-ALERT_RULES-002` | `FR-032` | `full` |
| `CAP-M-ALERT_RULES-002` | `FR-033` | `full` |
| `CAP-M-ALERT_RULES-002` | `FR-034` | `full` |
| `CAP-M-ALERT_RULES-002` | `FR-035` | `full` |
| `CAP-M-ALERT_RULES-002` | `FR-036` | `full` |
| `CAP-M-ALERT_RULES-002` | `FR-038` | `full` |
| `CAP-M-ALERT_RULES-003` | `FR-030` | `full` |
| `CAP-M-ALERT_RULES-003` | `FR-031` | `full` |
| `CAP-M-ALERT_RULES-003` | `FR-032` | `full` |
| `CAP-M-ALERT_RULES-003` | `FR-033` | `full` |
| `CAP-M-ALERT_RULES-003` | `FR-034` | `full` |
| `CAP-M-ALERT_RULES-003` | `FR-035` | `full` |
| `CAP-M-ALERT_RULES-003` | `FR-036` | `full` |
| `CAP-M-ALERT_RULES-003` | `FR-038` | `full` |
| `CAP-M-DEVICE_LOGS-001` | `FR-030` | `full` |
| `CAP-M-DEVICE_LOGS-001` | `FR-031` | `full` |
| `CAP-M-DEVICE_LOGS-001` | `FR-032` | `full` |
| `CAP-M-DEVICE_LOGS-001` | `FR-033` | `full` |
| `CAP-M-DEVICE_LOGS-001` | `FR-034` | `full` |
| `CAP-M-DEVICE_LOGS-001` | `FR-035` | `full` |
| `CAP-M-DEVICE_LOGS-001` | `FR-036` | `full` |
| `CAP-M-DEVICE_LOGS-001` | `FR-038` | `full` |
| `CAP-M-INDEX-001` | `FR-030` | `full` |
| `CAP-M-INDEX-001` | `FR-031` | `full` |
| `CAP-M-INDEX-001` | `FR-032` | `full` |
| `CAP-M-INDEX-001` | `FR-033` | `full` |
| `CAP-M-INDEX-001` | `FR-034` | `full` |
| `CAP-M-INDEX-001` | `FR-035` | `full` |
| `CAP-M-INDEX-001` | `FR-036` | `full` |
| `CAP-M-INDEX-001` | `FR-038` | `full` |

## out_of_scope

- FR-033: API 结构化日志记录（🔲 属于 AD/DD）
- FR-036~037: 安全与隐私（🔲 属于 DD）
- 当前脚本不会从 HumanPD 自动恢复完整业务后端契约，只生成 AI-PD scaffold。
- 若 HumanPD 未显式表达真实路由、异常反馈或数据字段，生成结果会保留保守默认值，需后续人工精修。
