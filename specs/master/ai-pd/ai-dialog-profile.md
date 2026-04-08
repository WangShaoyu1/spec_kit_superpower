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
- **覆盖 FR**: FR-007, FR-008, FR-009, FR-010, FR-011, FR-015, FR-016, FR-040, FR-047
- **转换口径**: 本文件由半自动脚本生成，用作 AI-PD scaffold，允许后续人工精修

## 页面索引

| page_id | page_name | page_boundary | route_or_entry | capability_count | related_fr |
|---------|-----------|---------------|----------------|------------------|------------|
| `dialog-profile.detail` | 对话方案详情 | `sub-page` | `detail.html` | 8 | FR-007, FR-008, FR-009, FR-010, FR-011, FR-015, FR-016, FR-040, FR-047 |
| `dialog-profile.index` | 对话方案管理 | `main-page` | `index.html` | 7 | FR-007, FR-008, FR-009, FR-010, FR-011, FR-015, FR-016, FR-040, FR-047 |
| `dialog-profile.test-chat` | 手动测试 | `sub-page` | `test-chat.html` | 2 | FR-007, FR-008, FR-009, FR-010, FR-011, FR-015, FR-016, FR-040, FR-047 |

## Page: dialog-profile.detail

```yaml
page_id: dialog-profile.detail
page_name: 对话方案详情
page_boundary: sub-page
goal: 完成对话方案的全部配置（指令库绑定、人设、阈值）并发布上线
route_or_entry: detail.html
parent_page: dialog-profile.index
```

### primary_user_flows

- 进入详情 → 绑定指令库(多选) → 配置指令阈值 Slider → 保存
- 点击人设管理 → 新建/编辑人设(名称/性格/语气) → 激活 → 保存
- 点击发布 → 门禁校验(指令库有 published 模型) → 版本对比 → 勾选确认 → 倒计时 → 发布成功
- 点击手动测试 → 跳转 test-chat.html

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
| `CAP-DP-DETAIL-001` | 绑定指令库 | `DATA` | `P0` | 绑定结果真实回读并反映到方案详情 |
| `CAP-DP-DETAIL-002` | 切换人设 | `STATE` | `P1` | 切换后当前方案人设真实回读更新 |
| `CAP-DP-DETAIL-003` | 编辑人设 | `CRUD` | `P1` | 保存后人设配置真实回读更新 |
| `CAP-DP-DETAIL-004` | 新建人设 | `CRUD` | `P1` | 创建后人设列表真实回读更新 |
| `CAP-DP-DETAIL-005` | 执行手动测试 | `FEEDBACK` | `P0` | 手动测试结果与调试信息真实回读展示 |
| `CAP-DP-DETAIL-006` | 进入平台级批量测试 | `NAVIGATION` | `P1` | 可跳转到批量测试模块入口 |
| `CAP-DP-DETAIL-007` | 编辑当前项 | `CRUD` | `P1` | 保存后页面主数据回读为最新值 |
| `CAP-DP-DETAIL-008` | 发布模型 | `STATE` | `P0` | 发布完成后模型状态真实回读更新 |

### action_contracts

| action_id | action | preconditions | success_signal | failure_feedback | state_change |
|-----------|--------|---------------|----------------|------------------|--------------|
| `ACT-001` | 绑定指令库 | 必要字段合法且权限满足 | 绑定结果真实回读并反映到方案详情 | 必须给出明确错误提示，不允许假成功 | 绑定指令库 |
| `ACT-002` | 切换人设 | 必要字段合法且权限满足 | 切换后当前方案人设真实回读更新 | 必须给出明确错误提示，不允许假成功 | 切换人设 |
| `ACT-003` | 编辑人设 | 必要字段合法且权限满足 | 保存后人设配置真实回读更新 | 必须给出明确错误提示，不允许假成功 | 编辑人设 |
| `ACT-004` | 新建人设 | 必要字段合法且权限满足 | 创建后人设列表真实回读更新 | 必须给出明确错误提示，不允许假成功 | 新建人设 |
| `ACT-005` | 执行手动测试 | 必要字段合法且权限满足 | 手动测试结果与调试信息真实回读展示 | 必须给出明确错误提示，不允许假成功 | 执行手动测试 |
| `ACT-006` | 进入平台级批量测试 | 必要字段合法且权限满足 | 可跳转到批量测试模块入口 | 必须给出明确错误提示，不允许假成功 | 进入平台级批量测试 |
| `ACT-007` | 编辑当前项 | 必要字段合法且权限满足 | 保存后页面主数据回读为最新值 | 必须给出明确错误提示，不允许假成功 | 编辑当前项 |
| `ACT-008` | 发布模型 | 必要字段合法且权限满足 | 发布完成后模型状态真实回读更新 | 必须给出明确错误提示，不允许假成功 | 发布模型 |

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
goal: 检索和管理所有对话方案，快速了解各方案的版本与发布状态
route_or_entry: index.html
parent_page: dialog-profile.detail
```

### primary_user_flows

- 点击新建方案 → 填写名称/LLM 模型/路由策略 → 提交 → 列表回读
- 点击方案行 → 跳转 detail.html 进入配置详情
- 筛选方案列表（按状态/名称）→ 定位目标方案

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
| `CAP-DP-INDEX-002` | 创建方案 | `CRUD` | `P0` | 创建成功后列表回读出现新方案 |
| `CAP-DP-INDEX-003` | 绑定指令库 | `DATA` | `P0` | 绑定结果真实回读并反映到方案详情 |
| `CAP-DP-INDEX-004` | 执行手动测试 | `FEEDBACK` | `P0` | 手动测试结果与调试信息真实回读展示 |
| `CAP-DP-INDEX-005` | 编辑当前项 | `CRUD` | `P1` | 保存后页面主数据回读为最新值 |
| `CAP-DP-INDEX-006` | 删除当前项 | `CRUD` | `P1` | 删除后列表或详情不再显示目标项 |
| `CAP-DP-INDEX-007` | 发布模型 | `STATE` | `P0` | 发布完成后模型状态真实回读更新 |

### action_contracts

| action_id | action | preconditions | success_signal | failure_feedback | state_change |
|-----------|--------|---------------|----------------|------------------|--------------|
| `ACT-002` | 创建方案 | 必要字段合法且权限满足 | 创建成功后列表回读出现新方案 | 必须给出明确错误提示，不允许假成功 | 创建方案 |
| `ACT-003` | 绑定指令库 | 必要字段合法且权限满足 | 绑定结果真实回读并反映到方案详情 | 必须给出明确错误提示，不允许假成功 | 绑定指令库 |
| `ACT-004` | 执行手动测试 | 必要字段合法且权限满足 | 手动测试结果与调试信息真实回读展示 | 必须给出明确错误提示，不允许假成功 | 执行手动测试 |
| `ACT-005` | 编辑当前项 | 必要字段合法且权限满足 | 保存后页面主数据回读为最新值 | 必须给出明确错误提示，不允许假成功 | 编辑当前项 |
| `ACT-006` | 删除当前项 | 必要字段合法且权限满足 | 删除后列表或详情不再显示目标项 | 必须给出明确错误提示，不允许假成功 | 删除当前项 |
| `ACT-007` | 发布模型 | 必要字段合法且权限满足 | 发布完成后模型状态真实回读更新 | 必须给出明确错误提示，不允许假成功 | 发布模型 |

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
goal: 通过对话式交互验证对话方案的端到端效果（路由、意图、槽位、闲聊）
route_or_entry: test-chat.html
parent_page: dialog-profile.detail
```

### primary_user_flows

- 新建会话 → 输入测试文本 → 发送 → 查看 Bot 回复 + Debug 面板(路由/意图/置信度/耗时)
- 配置设备上下文(设备类型/型号/位置) → 发送同一文本 → 对比不同上下文下的路由结果
- 切换会话 → 对比不同会话的回复质量

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
| `CAP-DP-TEST_CHAT-001` | 执行手动测试 | `FEEDBACK` | `P0` | 手动测试结果与调试信息真实回读展示 |
| `CAP-DP-TEST_CHAT-002` | 删除当前项 | `CRUD` | `P1` | 删除后列表或详情不再显示目标项 |

### action_contracts

| action_id | action | preconditions | success_signal | failure_feedback | state_change |
|-----------|--------|---------------|----------------|------------------|--------------|
| `ACT-001` | 执行手动测试 | 必要字段合法且权限满足 | 手动测试结果与调试信息真实回读展示 | 必须给出明确错误提示，不允许假成功 | 执行手动测试 |
| `ACT-002` | 删除当前项 | 必要字段合法且权限满足 | 删除后列表或详情不再显示目标项 | 必须给出明确错误提示，不允许假成功 | 删除当前项 |

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
| `CAP-DP-DETAIL-001` | `FR-015` | `full` |
| `CAP-DP-DETAIL-001` | `FR-016` | `full` |
| `CAP-DP-DETAIL-001` | `FR-040` | `full` |
| `CAP-DP-DETAIL-001` | `FR-047` | `full` |
| `CAP-DP-DETAIL-002` | `FR-007` | `full` |
| `CAP-DP-DETAIL-002` | `FR-008` | `full` |
| `CAP-DP-DETAIL-002` | `FR-009` | `full` |
| `CAP-DP-DETAIL-002` | `FR-010` | `full` |
| `CAP-DP-DETAIL-002` | `FR-011` | `full` |
| `CAP-DP-DETAIL-002` | `FR-015` | `full` |
| `CAP-DP-DETAIL-002` | `FR-016` | `full` |
| `CAP-DP-DETAIL-002` | `FR-040` | `full` |
| `CAP-DP-DETAIL-002` | `FR-047` | `full` |
| `CAP-DP-DETAIL-003` | `FR-007` | `full` |
| `CAP-DP-DETAIL-003` | `FR-008` | `full` |
| `CAP-DP-DETAIL-003` | `FR-009` | `full` |
| `CAP-DP-DETAIL-003` | `FR-010` | `full` |
| `CAP-DP-DETAIL-003` | `FR-011` | `full` |
| `CAP-DP-DETAIL-003` | `FR-015` | `full` |
| `CAP-DP-DETAIL-003` | `FR-016` | `full` |
| `CAP-DP-DETAIL-003` | `FR-040` | `full` |
| `CAP-DP-DETAIL-003` | `FR-047` | `full` |
| `CAP-DP-DETAIL-004` | `FR-007` | `full` |
| `CAP-DP-DETAIL-004` | `FR-008` | `full` |
| `CAP-DP-DETAIL-004` | `FR-009` | `full` |
| `CAP-DP-DETAIL-004` | `FR-010` | `full` |
| `CAP-DP-DETAIL-004` | `FR-011` | `full` |
| `CAP-DP-DETAIL-004` | `FR-015` | `full` |
| `CAP-DP-DETAIL-004` | `FR-016` | `full` |
| `CAP-DP-DETAIL-004` | `FR-040` | `full` |
| `CAP-DP-DETAIL-004` | `FR-047` | `full` |
| `CAP-DP-DETAIL-005` | `FR-007` | `full` |
| `CAP-DP-DETAIL-005` | `FR-008` | `full` |
| `CAP-DP-DETAIL-005` | `FR-009` | `full` |
| `CAP-DP-DETAIL-005` | `FR-010` | `full` |
| `CAP-DP-DETAIL-005` | `FR-011` | `full` |
| `CAP-DP-DETAIL-005` | `FR-015` | `full` |
| `CAP-DP-DETAIL-005` | `FR-016` | `full` |
| `CAP-DP-DETAIL-005` | `FR-040` | `full` |
| `CAP-DP-DETAIL-005` | `FR-047` | `full` |
| `CAP-DP-DETAIL-006` | `FR-007` | `full` |
| `CAP-DP-DETAIL-006` | `FR-008` | `full` |
| `CAP-DP-DETAIL-006` | `FR-009` | `full` |
| `CAP-DP-DETAIL-006` | `FR-010` | `full` |
| `CAP-DP-DETAIL-006` | `FR-011` | `full` |
| `CAP-DP-DETAIL-006` | `FR-015` | `full` |
| `CAP-DP-DETAIL-006` | `FR-016` | `full` |
| `CAP-DP-DETAIL-006` | `FR-040` | `full` |
| `CAP-DP-DETAIL-006` | `FR-047` | `full` |
| `CAP-DP-DETAIL-007` | `FR-007` | `full` |
| `CAP-DP-DETAIL-007` | `FR-008` | `full` |
| `CAP-DP-DETAIL-007` | `FR-009` | `full` |
| `CAP-DP-DETAIL-007` | `FR-010` | `full` |
| `CAP-DP-DETAIL-007` | `FR-011` | `full` |
| `CAP-DP-DETAIL-007` | `FR-015` | `full` |
| `CAP-DP-DETAIL-007` | `FR-016` | `full` |
| `CAP-DP-DETAIL-007` | `FR-040` | `full` |
| `CAP-DP-DETAIL-007` | `FR-047` | `full` |
| `CAP-DP-DETAIL-008` | `FR-007` | `full` |
| `CAP-DP-DETAIL-008` | `FR-008` | `full` |
| `CAP-DP-DETAIL-008` | `FR-009` | `full` |
| `CAP-DP-DETAIL-008` | `FR-010` | `full` |
| `CAP-DP-DETAIL-008` | `FR-011` | `full` |
| `CAP-DP-DETAIL-008` | `FR-015` | `full` |
| `CAP-DP-DETAIL-008` | `FR-016` | `full` |
| `CAP-DP-DETAIL-008` | `FR-040` | `full` |
| `CAP-DP-DETAIL-008` | `FR-047` | `full` |
| `CAP-DP-INDEX-001` | `FR-007` | `full` |
| `CAP-DP-INDEX-001` | `FR-008` | `full` |
| `CAP-DP-INDEX-001` | `FR-009` | `full` |
| `CAP-DP-INDEX-001` | `FR-010` | `full` |
| `CAP-DP-INDEX-001` | `FR-011` | `full` |
| `CAP-DP-INDEX-001` | `FR-015` | `full` |
| `CAP-DP-INDEX-001` | `FR-016` | `full` |
| `CAP-DP-INDEX-001` | `FR-040` | `full` |
| `CAP-DP-INDEX-001` | `FR-047` | `full` |
| `CAP-DP-INDEX-002` | `FR-007` | `full` |
| `CAP-DP-INDEX-002` | `FR-008` | `full` |
| `CAP-DP-INDEX-002` | `FR-009` | `full` |
| `CAP-DP-INDEX-002` | `FR-010` | `full` |
| `CAP-DP-INDEX-002` | `FR-011` | `full` |
| `CAP-DP-INDEX-002` | `FR-015` | `full` |
| `CAP-DP-INDEX-002` | `FR-016` | `full` |
| `CAP-DP-INDEX-002` | `FR-040` | `full` |
| `CAP-DP-INDEX-002` | `FR-047` | `full` |
| `CAP-DP-INDEX-003` | `FR-007` | `full` |
| `CAP-DP-INDEX-003` | `FR-008` | `full` |
| `CAP-DP-INDEX-003` | `FR-009` | `full` |
| `CAP-DP-INDEX-003` | `FR-010` | `full` |
| `CAP-DP-INDEX-003` | `FR-011` | `full` |
| `CAP-DP-INDEX-003` | `FR-015` | `full` |
| `CAP-DP-INDEX-003` | `FR-016` | `full` |
| `CAP-DP-INDEX-003` | `FR-040` | `full` |
| `CAP-DP-INDEX-003` | `FR-047` | `full` |
| `CAP-DP-INDEX-004` | `FR-007` | `full` |
| `CAP-DP-INDEX-004` | `FR-008` | `full` |
| `CAP-DP-INDEX-004` | `FR-009` | `full` |
| `CAP-DP-INDEX-004` | `FR-010` | `full` |
| `CAP-DP-INDEX-004` | `FR-011` | `full` |
| `CAP-DP-INDEX-004` | `FR-015` | `full` |
| `CAP-DP-INDEX-004` | `FR-016` | `full` |
| `CAP-DP-INDEX-004` | `FR-040` | `full` |
| `CAP-DP-INDEX-004` | `FR-047` | `full` |
| `CAP-DP-INDEX-005` | `FR-007` | `full` |
| `CAP-DP-INDEX-005` | `FR-008` | `full` |
| `CAP-DP-INDEX-005` | `FR-009` | `full` |
| `CAP-DP-INDEX-005` | `FR-010` | `full` |
| `CAP-DP-INDEX-005` | `FR-011` | `full` |
| `CAP-DP-INDEX-005` | `FR-015` | `full` |
| `CAP-DP-INDEX-005` | `FR-016` | `full` |
| `CAP-DP-INDEX-005` | `FR-040` | `full` |
| `CAP-DP-INDEX-005` | `FR-047` | `full` |
| `CAP-DP-INDEX-006` | `FR-007` | `full` |
| `CAP-DP-INDEX-006` | `FR-008` | `full` |
| `CAP-DP-INDEX-006` | `FR-009` | `full` |
| `CAP-DP-INDEX-006` | `FR-010` | `full` |
| `CAP-DP-INDEX-006` | `FR-011` | `full` |
| `CAP-DP-INDEX-006` | `FR-015` | `full` |
| `CAP-DP-INDEX-006` | `FR-016` | `full` |
| `CAP-DP-INDEX-006` | `FR-040` | `full` |
| `CAP-DP-INDEX-006` | `FR-047` | `full` |
| `CAP-DP-INDEX-007` | `FR-007` | `full` |
| `CAP-DP-INDEX-007` | `FR-008` | `full` |
| `CAP-DP-INDEX-007` | `FR-009` | `full` |
| `CAP-DP-INDEX-007` | `FR-010` | `full` |
| `CAP-DP-INDEX-007` | `FR-011` | `full` |
| `CAP-DP-INDEX-007` | `FR-015` | `full` |
| `CAP-DP-INDEX-007` | `FR-016` | `full` |
| `CAP-DP-INDEX-007` | `FR-040` | `full` |
| `CAP-DP-INDEX-007` | `FR-047` | `full` |
| `CAP-DP-TEST_CHAT-001` | `FR-007` | `full` |
| `CAP-DP-TEST_CHAT-001` | `FR-008` | `full` |
| `CAP-DP-TEST_CHAT-001` | `FR-009` | `full` |
| `CAP-DP-TEST_CHAT-001` | `FR-010` | `full` |
| `CAP-DP-TEST_CHAT-001` | `FR-011` | `full` |
| `CAP-DP-TEST_CHAT-001` | `FR-015` | `full` |
| `CAP-DP-TEST_CHAT-001` | `FR-016` | `full` |
| `CAP-DP-TEST_CHAT-001` | `FR-040` | `full` |
| `CAP-DP-TEST_CHAT-001` | `FR-047` | `full` |
| `CAP-DP-TEST_CHAT-002` | `FR-007` | `full` |
| `CAP-DP-TEST_CHAT-002` | `FR-008` | `full` |
| `CAP-DP-TEST_CHAT-002` | `FR-009` | `full` |
| `CAP-DP-TEST_CHAT-002` | `FR-010` | `full` |
| `CAP-DP-TEST_CHAT-002` | `FR-011` | `full` |
| `CAP-DP-TEST_CHAT-002` | `FR-015` | `full` |
| `CAP-DP-TEST_CHAT-002` | `FR-016` | `full` |
| `CAP-DP-TEST_CHAT-002` | `FR-040` | `full` |
| `CAP-DP-TEST_CHAT-002` | `FR-047` | `full` |

## out_of_scope

- 当前脚本不会从 HumanPD 自动恢复完整业务后端契约，只生成 AI-PD scaffold。
- 若 HumanPD 未显式表达真实路由、异常反馈或数据字段，生成结果会保留保守默认值，需后续人工精修。
