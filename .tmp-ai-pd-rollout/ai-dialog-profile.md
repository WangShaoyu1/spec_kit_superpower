# AI-PD: dialog-profile

```yaml
module_key: dialog-profile
based_on:
  - spec.md
  - pd-all/pd-index.md
  - pd-all/pd-dialog-profile/README.md
  - pd-all/pd-dialog-profile/detail.html
  - pd-all/pd-dialog-profile/index.html
  - pd-all/pd-dialog-profile/test-chat.html
status: pilot
```

## 模块摘要

- **模块目标**: PM 从创建方案到手动测试并发布，整个流程可在 1 小时内完成（SC-007）
- **来源 HumanPD**: `pd-all/pd-dialog-profile/`
- **覆盖 FR**: FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-015, FR-016, FR-017, FR-040, FR-041, FR-047
- **转换口径**: 本文件由半自动脚本生成，用作 AI-PD scaffold，允许后续人工精修

## 页面索引

| page_id | page_name | page_boundary | route_or_entry | capability_count | related_fr |
|---------|-----------|---------------|----------------|------------------|------------|
| `dialog-profile.detail` | 对话方案详情 | `sub-page` | `detail.html` | 2 | FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-015, FR-016, FR-017, FR-040, FR-041, FR-047 |
| `dialog-profile.index` | 对话方案管理 | `main-page` | `index.html` | 4 | FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-015, FR-016, FR-017, FR-040, FR-041, FR-047 |
| `dialog-profile.test-chat` | 手动测试 | `sub-page` | `test-chat.html` | 1 | FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-015, FR-016, FR-017, FR-040, FR-041, FR-047 |

## Page: dialog-profile.detail

```yaml
page_id: dialog-profile.detail
page_name: 对话方案详情
page_boundary: sub-page
goal: PM 从创建方案到手动测试并发布，整个流程可在 1 小时内完成（SC-007）
route_or_entry: detail.html
parent_page: dialog-profile.index
```

### primary_user_flows

- 创建多个方案 → 配置不同 LLM + 人设 → 手动测试对比效果 → 发布最佳方案
- 绑定中文+英文指令库 → 配置指令阈值 → 验证双语识别效果
- 修改闲聊人设 → 测试回复风格是否符合预期

### visible_ui

| ui_id | type | label | purpose | source |
|------|------|-------|---------|--------|
| `UI-DETAIL-001` | `actions` | 操作入口 | 返回, 说明, 手动测试, 平台级批量测试, 编辑基本信息, 绑定指令库, 切换人设, 编辑人设, 新建人设, 取消 | page actions |

### hidden_interactions

| hidden_id | container | classification | entry | purpose |
|-----------|-----------|----------------|-------|---------|
| `HID-DETAIL-001` | `drawer` | `instructional` | 说明按钮 | 解释页面逻辑、状态流转、字段说明和易错点 |

### capabilities

| capability_id | title | type | priority | done_signal |
|---------------|-------|------|----------|-------------|
| `CAP-DP-DETAIL-001` | 编辑当前项 | `CRUD` | `P1` | 保存后页面主数据回读为最新值 |
| `CAP-DP-DETAIL-002` | 发布模型 | `STATE` | `P0` | 发布完成后模型状态真实回读更新 |

### action_contracts

| action_id | action | preconditions | success_signal | failure_feedback | state_change |
|-----------|--------|---------------|----------------|------------------|--------------|
| `ACT-001` | 编辑当前项 | 必要字段合法且权限满足 | 保存后页面主数据回读为最新值 | 必须给出明确错误提示，不允许假成功 | 编辑当前项 |
| `ACT-002` | 发布模型 | 必要字段合法且权限满足 | 发布完成后模型状态真实回读更新 | 必须给出明确错误提示，不允许假成功 | 发布模型 |

### data_contracts

| data_id | field_or_column | shape | required | source | notes |
|---------|-----------------|-------|----------|--------|-------|
| `DATA-DETAIL-001` | `name` | `string` | `yes` | form field | 方案名称 |
| `DATA-DETAIL-002` | `llmModel` | `string` | `yes` | form field | 大模型选型 |
| `DATA-DETAIL-003` | `routeStrategy` | `string` | `yes` | form field | 路由策略 |
| `DATA-DETAIL-004` | `sessionTimeout` | `string` | `yes` | form field | 会话超时（分钟） |
| `DATA-DETAIL-005` | `name` | `string` | `yes` | form field | 助手名称 |
| `DATA-DETAIL-006` | `personality` | `string` | `yes` | form field | 性格特征 |
| `DATA-DETAIL-007` | `toneStyle` | `string` | `yes` | form field | 语气风格 |

### business_rules

| rule_id | rule | scope | related_capability |
|---------|------|-------|--------------------|
| `RULE-NONE` | 当前页面未自动识别到额外业务规则 | n/a | `n/a` |

### exception_flows

| exception_id | scenario | expected_feedback | recovery |
|--------------|----------|-------------------|----------|
| `EX-NONE` | 当前页面未自动识别到异常流 | - | - |

## Page: dialog-profile.index

```yaml
page_id: dialog-profile.index
page_name: 对话方案管理
page_boundary: main-page
goal: PM 从创建方案到手动测试并发布，整个流程可在 1 小时内完成（SC-007）
route_or_entry: index.html
parent_page: dialog-profile.detail
```

### primary_user_flows

- 创建多个方案 → 配置不同 LLM + 人设 → 手动测试对比效果 → 发布最佳方案
- 绑定中文+英文指令库 → 配置指令阈值 → 验证双语识别效果
- 修改闲聊人设 → 测试回复风格是否符合预期

### visible_ui

| ui_id | type | label | purpose | source |
|------|------|-------|---------|--------|
| `UI-INDEX-001` | `stats` | 统计卡 | 方案总数, 已发布, 草稿, 测试中 | prototype state |
| `UI-INDEX-002` | `actions` | 操作入口 | 查看, 编辑, 删除, 说明, 新建方案, 查询, 重置 | page actions |

### hidden_interactions

| hidden_id | container | classification | entry | purpose |
|-----------|-----------|----------------|-------|---------|
| `HID-INDEX-001` | `drawer` | `instructional` | 说明按钮 | 解释页面逻辑、状态流转、字段说明和易错点 |

### capabilities

| capability_id | title | type | priority | done_signal |
|---------------|-------|------|----------|-------------|
| `CAP-DP-INDEX-001` | 查看页面主数据 | `DATA` | `P0` | 页面主数据来自真实回读，而非本地硬编码 |
| `CAP-DP-INDEX-002` | 编辑当前项 | `CRUD` | `P1` | 保存后页面主数据回读为最新值 |
| `CAP-DP-INDEX-003` | 删除当前项 | `CRUD` | `P1` | 删除后列表或详情不再显示目标项 |
| `CAP-DP-INDEX-004` | 发布模型 | `STATE` | `P0` | 发布完成后模型状态真实回读更新 |

### action_contracts

| action_id | action | preconditions | success_signal | failure_feedback | state_change |
|-----------|--------|---------------|----------------|------------------|--------------|
| `ACT-002` | 编辑当前项 | 必要字段合法且权限满足 | 保存后页面主数据回读为最新值 | 必须给出明确错误提示，不允许假成功 | 编辑当前项 |
| `ACT-003` | 删除当前项 | 必要字段合法且权限满足 | 删除后列表或详情不再显示目标项 | 必须给出明确错误提示，不允许假成功 | 删除当前项 |
| `ACT-004` | 发布模型 | 必要字段合法且权限满足 | 发布完成后模型状态真实回读更新 | 必须给出明确错误提示，不允许假成功 | 发布模型 |

### data_contracts

| data_id | field_or_column | shape | required | source | notes |
|---------|-----------------|-------|----------|--------|-------|
| `DATA-INDEX-001` | `name` | `string` | `yes` | form field | 方案名称 |
| `DATA-INDEX-002` | `llmModel` | `string` | `yes` | form field | 大模型选型 |
| `DATA-INDEX-003` | `routingStrategy` | `string` | `yes` | form field | 路由策略 |
| `DATA-INDEX-004` | `personaName` | `string` | `yes` | form field | 闲聊人设 |
| `DATA-INDEX-005` | `sessionTimeout` | `string` | `yes` | form field | 会话超时 |
| `DATA-INDEX-006` | `libraries` | `string` | `yes` | form field | 指令库绑定 |

### business_rules

| rule_id | rule | scope | related_capability |
|---------|------|-------|--------------------|
| `RULE-NONE` | 当前页面未自动识别到额外业务规则 | n/a | `n/a` |

### exception_flows

| exception_id | scenario | expected_feedback | recovery |
|--------------|----------|-------------------|----------|
| `EX-NONE` | 当前页面未自动识别到异常流 | - | - |

## Page: dialog-profile.test-chat

```yaml
page_id: dialog-profile.test-chat
page_name: 手动测试
page_boundary: sub-page
goal: PM 从创建方案到手动测试并发布，整个流程可在 1 小时内完成（SC-007）
route_or_entry: test-chat.html
parent_page: dialog-profile.detail
```

### primary_user_flows

- 创建多个方案 → 配置不同 LLM + 人设 → 手动测试对比效果 → 发布最佳方案
- 绑定中文+英文指令库 → 配置指令阈值 → 验证双语识别效果
- 修改闲聊人设 → 测试回复风格是否符合预期

### visible_ui

| ui_id | type | label | purpose | source |
|------|------|-------|---------|--------|
| `UI-TEST_CHAT-001` | `actions` | 操作入口 | 返回, 说明, 新建会话, 应用, 空闲-主页, 正在烹饪, 菜谱浏览 | page actions |

### hidden_interactions

| hidden_id | container | classification | entry | purpose |
|-----------|-----------|----------------|-------|---------|
| `HID-TEST_CHAT-001` | `drawer` | `instructional` | 说明按钮 | 解释页面逻辑、状态流转、字段说明和易错点 |

### capabilities

| capability_id | title | type | priority | done_signal |
|---------------|-------|------|----------|-------------|
| `CAP-DP-TEST_CHAT-001` | 删除当前项 | `CRUD` | `P1` | 删除后列表或详情不再显示目标项 |

### action_contracts

| action_id | action | preconditions | success_signal | failure_feedback | state_change |
|-----------|--------|---------------|----------------|------------------|--------------|
| `ACT-001` | 删除当前项 | 必要字段合法且权限满足 | 删除后列表或详情不再显示目标项 | 必须给出明确错误提示，不允许假成功 | 删除当前项 |

### data_contracts

| data_id | field_or_column | shape | required | source | notes |
|---------|-----------------|-------|----------|--------|-------|
| `DATA-TEST_CHAT-001` | `name` | `string` | `yes` | form field | 会话名称 |
| `DATA-TEST_CHAT-002` | `profile` | `string` | `yes` | form field | 关联方案 |
| `DATA-TEST_CHAT-003` | `preset` | `string` | `yes` | form field | 设备上下文预设 |
| `DATA-TEST_CHAT-004` | `remark` | `string` | `yes` | form field | 备注 |

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
| `CAP-DP-DETAIL-001` | `FR-007` | `full` |
| `CAP-DP-DETAIL-001` | `FR-008` | `full` |
| `CAP-DP-DETAIL-001` | `FR-009` | `full` |
| `CAP-DP-DETAIL-001` | `FR-010` | `full` |
| `CAP-DP-DETAIL-001` | `FR-011` | `full` |
| `CAP-DP-DETAIL-001` | `FR-012` | `full` |
| `CAP-DP-DETAIL-001` | `FR-015` | `full` |
| `CAP-DP-DETAIL-001` | `FR-016` | `full` |
| `CAP-DP-DETAIL-001` | `FR-017` | `full` |
| `CAP-DP-DETAIL-001` | `FR-040` | `full` |
| `CAP-DP-DETAIL-001` | `FR-041` | `full` |
| `CAP-DP-DETAIL-001` | `FR-047` | `full` |
| `CAP-DP-DETAIL-002` | `FR-007` | `full` |
| `CAP-DP-DETAIL-002` | `FR-008` | `full` |
| `CAP-DP-DETAIL-002` | `FR-009` | `full` |
| `CAP-DP-DETAIL-002` | `FR-010` | `full` |
| `CAP-DP-DETAIL-002` | `FR-011` | `full` |
| `CAP-DP-DETAIL-002` | `FR-012` | `full` |
| `CAP-DP-DETAIL-002` | `FR-015` | `full` |
| `CAP-DP-DETAIL-002` | `FR-016` | `full` |
| `CAP-DP-DETAIL-002` | `FR-017` | `full` |
| `CAP-DP-DETAIL-002` | `FR-040` | `full` |
| `CAP-DP-DETAIL-002` | `FR-041` | `full` |
| `CAP-DP-DETAIL-002` | `FR-047` | `full` |
| `CAP-DP-INDEX-001` | `FR-007` | `full` |
| `CAP-DP-INDEX-001` | `FR-008` | `full` |
| `CAP-DP-INDEX-001` | `FR-009` | `full` |
| `CAP-DP-INDEX-001` | `FR-010` | `full` |
| `CAP-DP-INDEX-001` | `FR-011` | `full` |
| `CAP-DP-INDEX-001` | `FR-012` | `full` |
| `CAP-DP-INDEX-001` | `FR-015` | `full` |
| `CAP-DP-INDEX-001` | `FR-016` | `full` |
| `CAP-DP-INDEX-001` | `FR-017` | `full` |
| `CAP-DP-INDEX-001` | `FR-040` | `full` |
| `CAP-DP-INDEX-001` | `FR-041` | `full` |
| `CAP-DP-INDEX-001` | `FR-047` | `full` |
| `CAP-DP-INDEX-002` | `FR-007` | `full` |
| `CAP-DP-INDEX-002` | `FR-008` | `full` |
| `CAP-DP-INDEX-002` | `FR-009` | `full` |
| `CAP-DP-INDEX-002` | `FR-010` | `full` |
| `CAP-DP-INDEX-002` | `FR-011` | `full` |
| `CAP-DP-INDEX-002` | `FR-012` | `full` |
| `CAP-DP-INDEX-002` | `FR-015` | `full` |
| `CAP-DP-INDEX-002` | `FR-016` | `full` |
| `CAP-DP-INDEX-002` | `FR-017` | `full` |
| `CAP-DP-INDEX-002` | `FR-040` | `full` |
| `CAP-DP-INDEX-002` | `FR-041` | `full` |
| `CAP-DP-INDEX-002` | `FR-047` | `full` |
| `CAP-DP-INDEX-003` | `FR-007` | `full` |
| `CAP-DP-INDEX-003` | `FR-008` | `full` |
| `CAP-DP-INDEX-003` | `FR-009` | `full` |
| `CAP-DP-INDEX-003` | `FR-010` | `full` |
| `CAP-DP-INDEX-003` | `FR-011` | `full` |
| `CAP-DP-INDEX-003` | `FR-012` | `full` |
| `CAP-DP-INDEX-003` | `FR-015` | `full` |
| `CAP-DP-INDEX-003` | `FR-016` | `full` |
| `CAP-DP-INDEX-003` | `FR-017` | `full` |
| `CAP-DP-INDEX-003` | `FR-040` | `full` |
| `CAP-DP-INDEX-003` | `FR-041` | `full` |
| `CAP-DP-INDEX-003` | `FR-047` | `full` |
| `CAP-DP-INDEX-004` | `FR-007` | `full` |
| `CAP-DP-INDEX-004` | `FR-008` | `full` |
| `CAP-DP-INDEX-004` | `FR-009` | `full` |
| `CAP-DP-INDEX-004` | `FR-010` | `full` |
| `CAP-DP-INDEX-004` | `FR-011` | `full` |
| `CAP-DP-INDEX-004` | `FR-012` | `full` |
| `CAP-DP-INDEX-004` | `FR-015` | `full` |
| `CAP-DP-INDEX-004` | `FR-016` | `full` |
| `CAP-DP-INDEX-004` | `FR-017` | `full` |
| `CAP-DP-INDEX-004` | `FR-040` | `full` |
| `CAP-DP-INDEX-004` | `FR-041` | `full` |
| `CAP-DP-INDEX-004` | `FR-047` | `full` |
| `CAP-DP-TEST_CHAT-001` | `FR-007` | `full` |
| `CAP-DP-TEST_CHAT-001` | `FR-008` | `full` |
| `CAP-DP-TEST_CHAT-001` | `FR-009` | `full` |
| `CAP-DP-TEST_CHAT-001` | `FR-010` | `full` |
| `CAP-DP-TEST_CHAT-001` | `FR-011` | `full` |
| `CAP-DP-TEST_CHAT-001` | `FR-012` | `full` |
| `CAP-DP-TEST_CHAT-001` | `FR-015` | `full` |
| `CAP-DP-TEST_CHAT-001` | `FR-016` | `full` |
| `CAP-DP-TEST_CHAT-001` | `FR-017` | `full` |
| `CAP-DP-TEST_CHAT-001` | `FR-040` | `full` |
| `CAP-DP-TEST_CHAT-001` | `FR-041` | `full` |
| `CAP-DP-TEST_CHAT-001` | `FR-047` | `full` |

## out_of_scope

- 当前脚本不会从 HumanPD 自动恢复完整业务后端契约，只生成 AI-PD scaffold。
- 当前脚本不会从 HumanPD 自动恢复完整业务后端契约，只生成 AI-PD scaffold。
- 若 HumanPD 未显式表达真实路由、异常反馈或数据字段，生成结果会保留保守默认值，需后续人工精修。
