# AI-PD: user-mgmt

```yaml
module_key: user-mgmt
based_on:
  - spec.md
  - pd-all/pd-index.md
  - pd-all/pd-user-mgmt/README.md
  - pd-all/pd-user-mgmt/index.html
status: pilot
```

## 模块摘要

- **模块目标**: 管理员可在单页内完成账号开通、角色调整和权限核对
- **来源 HumanPD**: `pd-all/pd-user-mgmt/`
- **覆盖 FR**: FR-001
- **转换口径**: 本文件由半自动脚本生成，用作 AI-PD scaffold，允许后续人工精修

## 页面索引

| page_id | page_name | page_boundary | route_or_entry | capability_count | related_fr |
|---------|-----------|---------------|----------------|------------------|------------|
| `user-mgmt.index` | 用户管理 | `main-page` | `index.html` | 10 | FR-001 |

## Page: user-mgmt.index

```yaml
page_id: user-mgmt.index
page_name: 用户管理
page_boundary: main-page
goal: 在单页内完成账号开通、角色分配和权限矩阵核对，保障 RBAC 策略透明可控
route_or_entry: index.html
parent_page: none
```

### primary_user_flows

- 点击新建用户 → 填写用户名/密码/角色 → 提交 → 用户列表回读新增项
- 选择用户 → 修改角色 → 预览能力点变化 → 确认保存
- 切换到角色 Tab → 查看角色-能力点矩阵 → 确认权限边界

### visible_ui

| ui_id | type | label | purpose | source |
|------|------|-------|---------|--------|
| `UI-INDEX-001` | `stats` | 统计卡 | 总账号数, 管理员, 产品经理, 测试人员 | prototype state |
| `UI-INDEX-002` | `table` | 表格 | 用户名, 姓名, 角色, 状态, 创建时间, 最后登录, 操作 | prototype columns |
| `UI-INDEX-003` | `table` | 表格 | 能力点, 说明, 系统管理员, 产品经理, 测试人员 | prototype columns |
| `UI-INDEX-004` | `actions` | 操作入口 | 编辑角色, 重置密码, 说明, 新建账号 | page actions |

### hidden_interactions

| hidden_id | container | classification | entry | purpose |
|-----------|-----------|----------------|-------|---------|
| `HID-INDEX-001` | `drawer` | `instructional` | 说明按钮 | 解释页面逻辑、状态流转、字段说明和易错点 |
| `HID-INDEX-002` | `modal` | `ui-capability` | 新建账号 | 创建账号并指定初始角色 |
| `HID-INDEX-003` | `modal` | `ui-capability` | 编辑角色 | 调整角色并预览能力点变化 |
| `HID-INDEX-004` | `confirm-modal` | `ui-capability` | 重置密码 | 重置账号密码并返回临时密码结果 |
| `HID-INDEX-005` | `inline-alert` | `domain-rule` | 状态开关 / 风险提示 | 约束内置 admin 与最后一个启用管理员保护 |

### capabilities

| capability_id | title | type | priority | done_signal |
|---------------|-------|------|----------|-------------|
| `CAP-UM-INDEX-001` | 查看页面主数据 | `DATA` | `P0` | 页面主数据来自真实回读，而非本地硬编码 |
| `CAP-UM-INDEX-002` | 创建账号 | `CRUD` | `P0` | 创建成功后列表新增账号且统计卡回读更新 |
| `CAP-UM-INDEX-003` | 调整角色与能力预览 | `STATE` | `P0` | 角色更新后列表回读，预览矩阵与新角色一致 |
| `CAP-UM-INDEX-004` | 重置密码 | `FEEDBACK` | `P1` | 确认后返回默认密码或明确失败原因 |
| `CAP-UM-INDEX-005` | 查看权限矩阵 | `PERMISSION` | `P0` | 管理员、PM、测试三类角色能力点可见且条件说明明确 |
| `CAP-UM-INDEX-006` | 执行手动测试 | `FEEDBACK` | `P0` | 手动测试结果与调试信息真实回读展示 |
| `CAP-UM-INDEX-007` | 编辑当前项 | `CRUD` | `P1` | 保存后页面主数据回读为最新值 |
| `CAP-UM-INDEX-008` | 删除当前项 | `CRUD` | `P1` | 删除后列表或详情不再显示目标项 |
| `CAP-UM-INDEX-009` | 发布模型 | `STATE` | `P0` | 发布完成后模型状态真实回读更新 |
| `CAP-UM-INDEX-010` | 配置告警规则 | `NAVIGATION` | `P0` | 可进入告警规则页配置并查看规则状态 |

### action_contracts

| action_id | action | preconditions | success_signal | failure_feedback | state_change |
|-----------|--------|---------------|----------------|------------------|--------------|
| `ACT-002` | 创建账号 | 必要字段合法且权限满足 | 创建成功后列表新增账号且统计卡回读更新 | 必须给出明确错误提示，不允许假成功 | 创建账号 |
| `ACT-003` | 调整角色与能力预览 | 必要字段合法且权限满足 | 角色更新后列表回读，预览矩阵与新角色一致 | 必须给出明确错误提示，不允许假成功 | 调整角色与能力预览 |
| `ACT-004` | 重置密码 | 必要字段合法且权限满足 | 确认后返回默认密码或明确失败原因 | 必须给出明确错误提示，不允许假成功 | 重置密码 |
| `ACT-006` | 执行手动测试 | 必要字段合法且权限满足 | 手动测试结果与调试信息真实回读展示 | 必须给出明确错误提示，不允许假成功 | 执行手动测试 |
| `ACT-007` | 编辑当前项 | 必要字段合法且权限满足 | 保存后页面主数据回读为最新值 | 必须给出明确错误提示，不允许假成功 | 编辑当前项 |
| `ACT-008` | 删除当前项 | 必要字段合法且权限满足 | 删除后列表或详情不再显示目标项 | 必须给出明确错误提示，不允许假成功 | 删除当前项 |
| `ACT-009` | 发布模型 | 必要字段合法且权限满足 | 发布完成后模型状态真实回读更新 | 必须给出明确错误提示，不允许假成功 | 发布模型 |
| `ACT-010` | 配置告警规则 | 必要字段合法且权限满足 | 可进入告警规则页配置并查看规则状态 | 必须给出明确错误提示，不允许假成功 | 配置告警规则 |

### data_contracts

| data_id | field_or_column | shape | required | source | notes |
|---------|-----------------|-------|----------|--------|-------|
| `DATA-INDEX-001` | `username` | `string` | `yes` | form field | 用户名 |
| `DATA-INDEX-002` | `name` | `string` | `yes` | form field | 姓名 |
| `DATA-INDEX-003` | `password` | `string` | `yes` | form field | 初始密码 |
| `DATA-INDEX-004` | `role` | `enum` | `yes` | form field | 角色 |
| `DATA-INDEX-005` | `newRole` | `enum` | `yes` | form field | 新角色 |

### business_rules

| rule_id | rule | scope | related_capability |
|---------|------|-------|--------------------|
| `RULE-001` | 权限判断必须基于 capability，而不是硬编码角色名 | user-mgmt.index | `CAP-UM-INDEX-001` |
| `RULE-002` | 内置管理员账号不可禁用 | user-mgmt.index | `CAP-UM-INDEX-001` |
| `RULE-003` | 系统至少保留一个启用中的管理员账号 | user-mgmt.index | `CAP-UM-INDEX-001` |

### exception_flows

| exception_id | scenario | expected_feedback | recovery |
|--------------|----------|-------------------|----------|
| `EX-001` | 尝试禁用内置管理员账号 | 立即回弹开关并提示不可禁用 | 保持原状态，管理员改为处理其他账号 |
| `EX-002` | 重置密码失败或被拒绝 | 提示失败原因，不得伪造成功提示 | 允许管理员重新发起操作 |


## acceptance_signals

- 页面关键结果必须能真实回读，不能只依赖 toast、静态 mock 或本地状态假更新。
- 隐藏交互只有在 AI-PD 中被标为 `instructional / non-actionable-note` 时才能排除出实现闭环。
- 当前输出为半自动 scaffold；若发现能力、契约或异常流缺项，必须继续人工补全。

## fr_mapping

| capability_id | fr_id | status |
|---------------|------|--------|
| `CAP-UM-INDEX-001` | `FR-001` | `full` |
| `CAP-UM-INDEX-002` | `FR-001` | `full` |
| `CAP-UM-INDEX-003` | `FR-001` | `full` |
| `CAP-UM-INDEX-004` | `FR-001` | `full` |
| `CAP-UM-INDEX-005` | `FR-001` | `full` |
| `CAP-UM-INDEX-006` | `FR-001` | `full` |
| `CAP-UM-INDEX-007` | `FR-001` | `full` |
| `CAP-UM-INDEX-008` | `FR-001` | `full` |
| `CAP-UM-INDEX-009` | `FR-001` | `full` |
| `CAP-UM-INDEX-010` | `FR-001` | `full` |

## out_of_scope

- 当前模块已覆盖对应 spec.md 范围
- 当前脚本不会从 HumanPD 自动恢复完整业务后端契约，只生成 AI-PD scaffold。
- 若 HumanPD 未显式表达真实路由、异常反馈或数据字段，生成结果会保留保守默认值，需后续人工精修。
