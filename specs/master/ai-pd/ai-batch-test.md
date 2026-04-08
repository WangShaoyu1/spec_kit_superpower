# AI-PD: batch-test

```yaml
module_key: batch-test
based_on:
  - spec.md
  - pd-all/pd-index.md
  - pd-all/pd-batch-test/README.md
  - pd-all/pd-batch-test/detail.html
  - pd-all/pd-batch-test/index.html
status: pilot
```

## 模块摘要

- **模块目标**: 团队可以基于统一批次结果决定哪个对话方案更适合进入发布链路
- **来源 HumanPD**: `pd-all/pd-batch-test/`
- **覆盖 FR**: FR-012, FR-013, FR-014
- **转换口径**: 本文件由半自动脚本生成，用作 AI-PD scaffold，允许后续人工精修

## 页面索引

| page_id | page_name | page_boundary | route_or_entry | capability_count | related_fr |
|---------|-----------|---------------|----------------|------------------|------------|
| `batch-test.detail` | 对话方案批次详情 | `sub-page` | `detail.html` | 6 | FR-012, FR-013, FR-014 |
| `batch-test.index` | 对话方案批量测试 | `main-page` | `index.html` | 9 | FR-012, FR-013, FR-014 |

## Page: batch-test.detail

```yaml
page_id: batch-test.detail
page_name: 对话方案批次详情
page_boundary: sub-page
goal: 查看批量测试结果与智能分析报告，定位未达标用例并获取优化建议
route_or_entry: detail.html
parent_page: batch-test.index
```

### primary_user_flows

- 进入批次详情 → 查看用例级结果表格（预期 vs 实际、得分、耗时、达标）
- 点击智能分析 Tab → 查看准确率排名、混淆矩阵、归因分析、建议
- 筛选未达标用例 → 分析混淆模式 → 导出结果

### visible_ui

| ui_id | type | label | purpose | source |
|------|------|-------|---------|--------|
| `UI-DETAIL-001` | `table` | 表格 | 用例编号, 用例语句, 预期路由, 实际路由, 预期意图, 实际意图, 预期槽位, 实际槽位, 匹配得分, 响应耗时, 达标, 标记 | prototype columns |
| `UI-DETAIL-002` | `table` | 表格 | 意图, 测试数, 通过, 准确率, 趋势 | prototype columns |
| `UI-DETAIL-003` | `actions` | 操作入口 | 返回, 说明, 重新执行, 导出报告 | page actions |

### hidden_interactions

| hidden_id | container | classification | entry | purpose |
|-----------|-----------|----------------|-------|---------|
| `HID-DETAIL-001` | `drawer` | `instructional` | 说明按钮 | 解释页面逻辑、状态流转、字段说明和易错点 |

### capabilities

| capability_id | title | type | priority | done_signal |
|---------------|-------|------|----------|-------------|
| `CAP-BT-DETAIL-001` | 查看页面主数据 | `DATA` | `P0` | 页面主数据来自真实回读，而非本地硬编码 |
| `CAP-BT-DETAIL-002` | 执行手动测试 | `FEEDBACK` | `P0` | 手动测试结果与调试信息真实回读展示 |
| `CAP-BT-DETAIL-003` | 编辑当前项 | `CRUD` | `P1` | 保存后页面主数据回读为最新值 |
| `CAP-BT-DETAIL-004` | 重新执行测试批次 | `ASYNC` | `P1` | 重新执行后批次结果与状态真实回读更新 |
| `CAP-BT-DETAIL-005` | 导出测试报告 | `FEEDBACK` | `P1` | 导出动作返回真实报告文件或明确失败原因 |
| `CAP-BT-DETAIL-006` | 查看智能分析 | `FEEDBACK` | `P1` | 分析结果必须来自真实计算或明确失败原因 |

### action_contracts

| action_id | action | preconditions | success_signal | failure_feedback | state_change |
|-----------|--------|---------------|----------------|------------------|--------------|
| `ACT-002` | 执行手动测试 | 必要字段合法且权限满足 | 手动测试结果与调试信息真实回读展示 | 必须给出明确错误提示，不允许假成功 | 执行手动测试 |
| `ACT-003` | 编辑当前项 | 必要字段合法且权限满足 | 保存后页面主数据回读为最新值 | 必须给出明确错误提示，不允许假成功 | 编辑当前项 |
| `ACT-004` | 重新执行测试批次 | 必要字段合法且权限满足 | 重新执行后批次结果与状态真实回读更新 | 必须给出明确错误提示，不允许假成功 | 重新执行测试批次 |
| `ACT-005` | 导出测试报告 | 必要字段合法且权限满足 | 导出动作返回真实报告文件或明确失败原因 | 必须给出明确错误提示，不允许假成功 | 导出测试报告 |

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

## Page: batch-test.index

```yaml
page_id: batch-test.index
page_name: 对话方案批量测试
page_boundary: main-page
goal: 管理对话方案的批量测试批次，创建新批次并发起执行
route_or_entry: index.html
parent_page: batch-test.detail
```

### primary_user_flows

- 点击新建批次 → 选择对话方案/版本 → 上传或生成用例 → 提交 → 列表回读新批次
- 选择已有批次 → 点击执行 → 状态从 draft → running → completed
- 点击批次行 → 跳转 detail.html 查看结果

### visible_ui

| ui_id | type | label | purpose | source |
|------|------|-------|---------|--------|


### hidden_interactions

| hidden_id | container | classification | entry | purpose |
|-----------|-----------|----------------|-------|---------|
| `HID-INDEX-001` | `drawer` | `instructional` | 说明按钮 | 解释页面逻辑、状态流转、字段说明和易错点 |

### capabilities

| capability_id | title | type | priority | done_signal |
|---------------|-------|------|----------|-------------|
| `CAP-BT-INDEX-001` | 绑定指令库 | `DATA` | `P0` | 绑定结果真实回读并反映到方案详情 |
| `CAP-BT-INDEX-002` | 执行手动测试 | `FEEDBACK` | `P0` | 手动测试结果与调试信息真实回读展示 |
| `CAP-BT-INDEX-003` | 编辑当前项 | `CRUD` | `P1` | 保存后页面主数据回读为最新值 |
| `CAP-BT-INDEX-004` | 删除当前项 | `CRUD` | `P1` | 删除后列表或详情不再显示目标项 |
| `CAP-BT-INDEX-005` | 创建测试批次 | `ASYNC` | `P0` | 测试批次创建后列表真实回读出现新批次 |
| `CAP-BT-INDEX-006` | 上传测试用例 | `DATA` | `P0` | 上传后用例列表真实回读更新 |
| `CAP-BT-INDEX-007` | 生成测试用例 | `ASYNC` | `P1` | 生成后用例列表与摘要真实回读更新 |
| `CAP-BT-INDEX-008` | 重新执行测试批次 | `ASYNC` | `P1` | 重新执行后批次结果与状态真实回读更新 |
| `CAP-BT-INDEX-009` | 查看智能分析 | `FEEDBACK` | `P1` | 分析结果必须来自真实计算或明确失败原因 |

### action_contracts

| action_id | action | preconditions | success_signal | failure_feedback | state_change |
|-----------|--------|---------------|----------------|------------------|--------------|
| `ACT-001` | 绑定指令库 | 必要字段合法且权限满足 | 绑定结果真实回读并反映到方案详情 | 必须给出明确错误提示，不允许假成功 | 绑定指令库 |
| `ACT-002` | 执行手动测试 | 必要字段合法且权限满足 | 手动测试结果与调试信息真实回读展示 | 必须给出明确错误提示，不允许假成功 | 执行手动测试 |
| `ACT-003` | 编辑当前项 | 必要字段合法且权限满足 | 保存后页面主数据回读为最新值 | 必须给出明确错误提示，不允许假成功 | 编辑当前项 |
| `ACT-004` | 删除当前项 | 必要字段合法且权限满足 | 删除后列表或详情不再显示目标项 | 必须给出明确错误提示，不允许假成功 | 删除当前项 |
| `ACT-005` | 创建测试批次 | 必要字段合法且权限满足 | 测试批次创建后列表真实回读出现新批次 | 必须给出明确错误提示，不允许假成功 | 创建测试批次 |
| `ACT-006` | 上传测试用例 | 必要字段合法且权限满足 | 上传后用例列表真实回读更新 | 必须给出明确错误提示，不允许假成功 | 上传测试用例 |
| `ACT-007` | 生成测试用例 | 必要字段合法且权限满足 | 生成后用例列表与摘要真实回读更新 | 必须给出明确错误提示，不允许假成功 | 生成测试用例 |
| `ACT-008` | 重新执行测试批次 | 必要字段合法且权限满足 | 重新执行后批次结果与状态真实回读更新 | 必须给出明确错误提示，不允许假成功 | 重新执行测试批次 |

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
| `CAP-BT-DETAIL-001` | `FR-012` | `full` |
| `CAP-BT-DETAIL-001` | `FR-013` | `full` |
| `CAP-BT-DETAIL-001` | `FR-014` | `full` |
| `CAP-BT-DETAIL-002` | `FR-012` | `full` |
| `CAP-BT-DETAIL-002` | `FR-013` | `full` |
| `CAP-BT-DETAIL-002` | `FR-014` | `full` |
| `CAP-BT-DETAIL-003` | `FR-012` | `full` |
| `CAP-BT-DETAIL-003` | `FR-013` | `full` |
| `CAP-BT-DETAIL-003` | `FR-014` | `full` |
| `CAP-BT-DETAIL-004` | `FR-012` | `full` |
| `CAP-BT-DETAIL-004` | `FR-013` | `full` |
| `CAP-BT-DETAIL-004` | `FR-014` | `full` |
| `CAP-BT-DETAIL-005` | `FR-012` | `full` |
| `CAP-BT-DETAIL-005` | `FR-013` | `full` |
| `CAP-BT-DETAIL-005` | `FR-014` | `full` |
| `CAP-BT-DETAIL-006` | `FR-012` | `full` |
| `CAP-BT-DETAIL-006` | `FR-013` | `full` |
| `CAP-BT-DETAIL-006` | `FR-014` | `full` |
| `CAP-BT-INDEX-001` | `FR-012` | `full` |
| `CAP-BT-INDEX-001` | `FR-013` | `full` |
| `CAP-BT-INDEX-001` | `FR-014` | `full` |
| `CAP-BT-INDEX-002` | `FR-012` | `full` |
| `CAP-BT-INDEX-002` | `FR-013` | `full` |
| `CAP-BT-INDEX-002` | `FR-014` | `full` |
| `CAP-BT-INDEX-003` | `FR-012` | `full` |
| `CAP-BT-INDEX-003` | `FR-013` | `full` |
| `CAP-BT-INDEX-003` | `FR-014` | `full` |
| `CAP-BT-INDEX-004` | `FR-012` | `full` |
| `CAP-BT-INDEX-004` | `FR-013` | `full` |
| `CAP-BT-INDEX-004` | `FR-014` | `full` |
| `CAP-BT-INDEX-005` | `FR-012` | `full` |
| `CAP-BT-INDEX-005` | `FR-013` | `full` |
| `CAP-BT-INDEX-005` | `FR-014` | `full` |
| `CAP-BT-INDEX-006` | `FR-012` | `full` |
| `CAP-BT-INDEX-006` | `FR-013` | `full` |
| `CAP-BT-INDEX-006` | `FR-014` | `full` |
| `CAP-BT-INDEX-007` | `FR-012` | `full` |
| `CAP-BT-INDEX-007` | `FR-013` | `full` |
| `CAP-BT-INDEX-007` | `FR-014` | `full` |
| `CAP-BT-INDEX-008` | `FR-012` | `full` |
| `CAP-BT-INDEX-008` | `FR-013` | `full` |
| `CAP-BT-INDEX-008` | `FR-014` | `full` |
| `CAP-BT-INDEX-009` | `FR-012` | `full` |
| `CAP-BT-INDEX-009` | `FR-013` | `full` |
| `CAP-BT-INDEX-009` | `FR-014` | `full` |

## out_of_scope

- 当前脚本不会从 HumanPD 自动恢复完整业务后端契约，只生成 AI-PD scaffold。
- 若 HumanPD 未显式表达真实路由、异常反馈或数据字段，生成结果会保留保守默认值，需后续人工精修。
