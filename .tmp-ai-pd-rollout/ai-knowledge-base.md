# AI-PD: knowledge-base

```yaml
module_key: knowledge-base
based_on:
  - spec.md
  - pd-all/pd-index.md
  - pd-all/pd-knowledge-base/README.md
  - pd-all/pd-knowledge-base/detail.html
  - pd-all/pd-knowledge-base/index.html
status: pilot
```

## 模块摘要

- **模块目标**: 文档上传后可被知识问答检索命中
- **来源 HumanPD**: `pd-all/pd-knowledge-base/`
- **覆盖 FR**: FR-004, FR-005, FR-006, FR-007, FR-021
- **转换口径**: 本文件由半自动脚本生成，用作 AI-PD scaffold，允许后续人工精修

## 页面索引

| page_id | page_name | page_boundary | route_or_entry | capability_count | related_fr |
|---------|-----------|---------------|----------------|------------------|------------|
| `knowledge-base.detail` | 文档详情 | `sub-page` | `detail.html` | 2 | FR-004, FR-005, FR-006, FR-007, FR-021 |
| `knowledge-base.index` | 知识库管理 | `main-page` | `index.html` | 3 | FR-004, FR-005, FR-006, FR-007, FR-021 |

## Page: knowledge-base.detail

```yaml
page_id: knowledge-base.detail
page_name: 文档详情
page_boundary: sub-page
goal: 文档上传后可被知识问答检索命中
route_or_entry: detail.html
parent_page: knowledge-base.index
```

### primary_user_flows

- 创建分类 → 上传菜谱 JSON → 系统自动解析过滤 → 验证检索结果
- 上传公司信息文档 → 归类管理 → 确认索引质量

### visible_ui

| ui_id | type | label | purpose | source |
|------|------|-------|---------|--------|
| `UI-DETAIL-001` | `table` | 表格 | 字段, 值, 类型 | prototype columns |
| `UI-DETAIL-002` | `table` | 表格 | 字段, 原值, 过滤原因 | prototype columns |

### hidden_interactions

| hidden_id | container | classification | entry | purpose |
|-----------|-----------|----------------|-------|---------|
| `HID-DETAIL-001` | `drawer` | `instructional` | 说明按钮 | 解释页面逻辑、状态流转、字段说明和易错点 |

### capabilities

| capability_id | title | type | priority | done_signal |
|---------------|-------|------|----------|-------------|
| `CAP-KB-DETAIL-001` | 查看页面主数据 | `DATA` | `P0` | 页面主数据来自真实回读，而非本地硬编码 |
| `CAP-KB-DETAIL-002` | 删除当前项 | `CRUD` | `P1` | 删除后列表或详情不再显示目标项 |

### action_contracts

| action_id | action | preconditions | success_signal | failure_feedback | state_change |
|-----------|--------|---------------|----------------|------------------|--------------|
| `ACT-002` | 删除当前项 | 必要字段合法且权限满足 | 删除后列表或详情不再显示目标项 | 必须给出明确错误提示，不允许假成功 | 删除当前项 |

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

## Page: knowledge-base.index

```yaml
page_id: knowledge-base.index
page_name: 知识库管理
page_boundary: main-page
goal: 文档上传后可被知识问答检索命中
route_or_entry: index.html
parent_page: knowledge-base.detail
```

### primary_user_flows

- 创建分类 → 上传菜谱 JSON → 系统自动解析过滤 → 验证检索结果
- 上传公司信息文档 → 归类管理 → 确认索引质量

### visible_ui

| ui_id | type | label | purpose | source |
|------|------|-------|---------|--------|
| `UI-INDEX-001` | `stats` | 统计卡 | 分类总数, 文档总数, 已索引, 索引中 | prototype state |
| `UI-INDEX-002` | `actions` | 操作入口 | 查看, 说明, 新建分类, 上传文档, 检索测试, 重置, 关闭, 模拟上传, 搜索 | page actions |

### hidden_interactions

| hidden_id | container | classification | entry | purpose |
|-----------|-----------|----------------|-------|---------|
| `HID-INDEX-001` | `drawer` | `instructional` | 说明按钮 | 解释页面逻辑、状态流转、字段说明和易错点 |

### capabilities

| capability_id | title | type | priority | done_signal |
|---------------|-------|------|----------|-------------|
| `CAP-KB-INDEX-001` | 查看页面主数据 | `DATA` | `P0` | 页面主数据来自真实回读，而非本地硬编码 |
| `CAP-KB-INDEX-002` | 编辑当前项 | `CRUD` | `P1` | 保存后页面主数据回读为最新值 |
| `CAP-KB-INDEX-003` | 删除当前项 | `CRUD` | `P1` | 删除后列表或详情不再显示目标项 |

### action_contracts

| action_id | action | preconditions | success_signal | failure_feedback | state_change |
|-----------|--------|---------------|----------------|------------------|--------------|
| `ACT-002` | 编辑当前项 | 必要字段合法且权限满足 | 保存后页面主数据回读为最新值 | 必须给出明确错误提示，不允许假成功 | 编辑当前项 |
| `ACT-003` | 删除当前项 | 必要字段合法且权限满足 | 删除后列表或详情不再显示目标项 | 必须给出明确错误提示，不允许假成功 | 删除当前项 |

### data_contracts

| data_id | field_or_column | shape | required | source | notes |
|---------|-----------------|-------|----------|--------|-------|
| `DATA-INDEX-001` | `name` | `string` | `yes` | form field | 分类名称 |
| `DATA-INDEX-002` | `icon` | `string` | `yes` | form field | 分类图标 |
| `DATA-INDEX-003` | `description` | `string` | `yes` | form field | 分类描述 |

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
| `CAP-KB-DETAIL-001` | `FR-004` | `full` |
| `CAP-KB-DETAIL-001` | `FR-005` | `full` |
| `CAP-KB-DETAIL-001` | `FR-006` | `full` |
| `CAP-KB-DETAIL-001` | `FR-007` | `full` |
| `CAP-KB-DETAIL-001` | `FR-021` | `full` |
| `CAP-KB-DETAIL-002` | `FR-004` | `full` |
| `CAP-KB-DETAIL-002` | `FR-005` | `full` |
| `CAP-KB-DETAIL-002` | `FR-006` | `full` |
| `CAP-KB-DETAIL-002` | `FR-007` | `full` |
| `CAP-KB-DETAIL-002` | `FR-021` | `full` |
| `CAP-KB-INDEX-001` | `FR-004` | `full` |
| `CAP-KB-INDEX-001` | `FR-005` | `full` |
| `CAP-KB-INDEX-001` | `FR-006` | `full` |
| `CAP-KB-INDEX-001` | `FR-007` | `full` |
| `CAP-KB-INDEX-001` | `FR-021` | `full` |
| `CAP-KB-INDEX-002` | `FR-004` | `full` |
| `CAP-KB-INDEX-002` | `FR-005` | `full` |
| `CAP-KB-INDEX-002` | `FR-006` | `full` |
| `CAP-KB-INDEX-002` | `FR-007` | `full` |
| `CAP-KB-INDEX-002` | `FR-021` | `full` |
| `CAP-KB-INDEX-003` | `FR-004` | `full` |
| `CAP-KB-INDEX-003` | `FR-005` | `full` |
| `CAP-KB-INDEX-003` | `FR-006` | `full` |
| `CAP-KB-INDEX-003` | `FR-007` | `full` |
| `CAP-KB-INDEX-003` | `FR-021` | `full` |

## out_of_scope

- FR-021: 知识域检索匹配（API 层）（🔲 属于 AD/DD）
- FR-007: 对话方案引用知识库（🔗 跨模块: pd-dialog-profile）
- 当前脚本不会从 HumanPD 自动恢复完整业务后端契约，只生成 AI-PD scaffold。
- 若 HumanPD 未显式表达真实路由、异常反馈或数据字段，生成结果会保留保守默认值，需后续人工精修。
