# AI-PD: intent-library

```yaml
module_key: intent-library
based_on:
  - spec.md
  - pd-all/pd-index.md
  - pd-all/pd-intent-library/README.md
  - pd-all/pd-intent-library/dataset-detail.html
  - pd-all/pd-intent-library/datasets.html
  - pd-all/pd-intent-library/detail.html
  - pd-all/pd-intent-library/index.html
  - pd-all/pd-intent-library/test.html
status: pilot
```

## 模块摘要

- **模块目标**: 形成"数据→训练→评估→发布→生效"的完整闭环
- **来源 HumanPD**: `pd-all/pd-intent-library/`
- **覆盖 FR**: FR-002, FR-003, FR-039, FR-043, FR-044, FR-045, FR-046, FR-047, FR-048, FR-049, FR-050, FR-051, FR-052, FR-053, FR-054
- **转换口径**: 本文件由半自动脚本生成，用作 AI-PD scaffold，允许后续人工精修

## 页面索引

| page_id | page_name | page_boundary | route_or_entry | capability_count | related_fr |
|---------|-----------|---------------|----------------|------------------|------------|
| `intent-library.dataset-detail` | 管理数据 | `sub-page` | `dataset-detail.html` | 7 | FR-002, FR-003, FR-049 |
| `intent-library.datasets` | 数据集管理 | `main-page` | `datasets.html` | 7 | FR-002, FR-003, FR-039, FR-043, FR-044, FR-045, FR-046, FR-047, FR-048, FR-049, FR-050, FR-051, FR-052, FR-053, FR-054 |
| `intent-library.detail` | 指令库详情 | `sub-page` | `detail.html` | 7 | FR-002, FR-003, FR-039, FR-043, FR-044, FR-045, FR-046, FR-047, FR-048, FR-049, FR-050, FR-051, FR-052, FR-053, FR-054 |
| `intent-library.index` | 指令库管理 | `main-page` | `index.html` | 4 | FR-002, FR-003, FR-039, FR-043, FR-044, FR-045, FR-046, FR-047, FR-048, FR-049, FR-050, FR-051, FR-052, FR-053, FR-054 |
| `intent-library.test` | 模型测试 | `sub-page` | `test.html` | 4 | FR-002, FR-003, FR-039, FR-043, FR-044, FR-045, FR-046, FR-047, FR-048, FR-049, FR-050, FR-051, FR-052, FR-053, FR-054 |

## Page: intent-library.dataset-detail

```yaml
page_id: intent-library.dataset-detail
page_name: 管理数据
page_boundary: sub-page
goal: 维护意图、词槽、实体和问法数据，并确保保存/导入结果真实回读
route_or_entry: dataset-detail.html
parent_page: intent-library.datasets
```

### primary_user_flows

- 进入数据管理页 → 保存意图配置 → 列表回读最新值
- 打开相似问/排除问 Drawer → 新增训练样本 → Drawer 列表回读新增项
- 打开实体批量导入 Modal → 导入实体值/同义词 → 实体列表同步回读

### visible_ui

| ui_id | type | label | purpose | source |
|------|------|-------|---------|--------|
| `UI-DATASET_DETAIL-001` | `actions` | 操作入口 | 配置, 相似问, 返回, 说明, 导出数据, 新建意图, 新建自定义词槽, 保存, 添加词槽引用, 添加相似问, 添加排除问, 单个添加, 批量导入, 下载模板, 下载 Excel 模板 | page actions |

### hidden_interactions

| hidden_id | container | classification | entry | purpose |
|-----------|-----------|----------------|-------|---------|
| `HID-DATASET_DETAIL-001` | `drawer-or-modal` | `ui-capability` | 意图配置 Drawer | 意图配置 Drawer |
| `HID-DATASET_DETAIL-002` | `drawer-or-modal` | `ui-capability` | 相似问 / 排除问 Drawer | 相似问 / 排除问 Drawer |
| `HID-DATASET_DETAIL-003` | `drawer-or-modal` | `ui-capability` | 自定义词槽 Drawer | 自定义词槽 Drawer |
| `HID-DATASET_DETAIL-004` | `drawer-or-modal` | `ui-capability` | 实体批量导入 Modal | 实体批量导入 Modal |
| `HID-DATASET_DETAIL-005` | `drawer-or-modal` | `ui-capability` | 新增问法 Modal | 新增问法 Modal |
| `HID-DATASET_DETAIL-006` | `drawer-or-modal` | `instructional` | 数据模型 / 批量导入说明 / 易错点标签页 | 数据模型 / 批量导入说明 / 易错点标签页 |

### capabilities

| capability_id | title | type | priority | done_signal |
|---------------|-------|------|----------|-------------|
| `CAP-IL-DATASET_DETAIL-001` | CRUD 意图定义（intent_key、中文名、描述） | `DATA` | `P0` | CRUD 意图定义（intent_key、中文名、描述） 的结果必须真实回读 |
| `CAP-IL-DATASET_DETAIL-002` | 配置命中话术 / 未命中话术，支持 {slot} 变量占位 | `STATE` | `P0` | 配置命中话术 / 未命中话术，支持 {slot} 变量占位 的结果必须真实回读 |
| `CAP-IL-DATASET_DETAIL-003` | 配置追问开关与追问文案 | `STATE` | `P0` | 配置追问开关与追问文案 的结果必须真实回读 |
| `CAP-IL-DATASET_DETAIL-004` | 管理系统词槽引用与自定义词槽 | `DATA` | `P0` | 管理系统词槽引用与自定义词槽 的结果必须真实回读 |
| `CAP-IL-DATASET_DETAIL-005` | 管理实体值与同义词 | `DATA` | `P0` | 管理实体值与同义词 的结果必须真实回读 |
| `CAP-IL-DATASET_DETAIL-006` | 管理相似问（正样本）与排除问（反例） | `DATA` | `P0` | 管理相似问（正样本）与排除问（反例） 的结果必须真实回读 |
| `CAP-IL-DATASET_DETAIL-007` | 支持 Excel / 文本 / 粘贴三类实体导入 | `STATE` | `P0` | 支持 Excel / 文本 / 粘贴三类实体导入 的结果必须真实回读 |

### action_contracts

| action_id | action | preconditions | success_signal | failure_feedback | state_change |
|-----------|--------|---------------|----------------|------------------|--------------|
| `ACT-001` | 保存意图 | 前置字段与权限满足 | 必填字段合法后写回意图定义，成功信号为列表回读出现最新值 | 必须给出明确失败反馈 | 保存意图 |
| `ACT-002` | 新增相似问/排除问 | 前置字段与权限满足 | 成功信号为 Drawer 列表回读新增项，失败需给出表单级错误 | 必须给出明确失败反馈 | 新增相似问/排除问 |
| `ACT-003` | 保存词槽 | 前置字段与权限满足 | 成功信号为词槽卡片与实体列表回读更新 | 必须给出明确失败反馈 | 保存词槽 |
| `ACT-004` | 批量导入实体 | 前置字段与权限满足 | 成功信号为实体值列表与同义词同步回读；若未实现，必须显式延期 | 必须给出明确失败反馈 | 批量导入实体 |

### data_contracts

| data_id | field_or_column | shape | required | source | notes |
|---------|-----------------|-------|----------|--------|-------|
| `DATA-NONE` | `n/a` | `n/a` | `no` | derived | 当前页面未识别出表单字段 |

### business_rules

| rule_id | rule | scope | related_capability |
|---------|------|-------|--------------------|
| `RULE-001` | “命中/未命中话术”属于系统回复，不等于“相似问/排除问” | intent-library.dataset-detail | `CAP-IL-DATASET_DETAIL-001` |
| `RULE-002` | “词槽”与“实体值/同义词”是两层结构，不可混淆 | intent-library.dataset-detail | `CAP-IL-DATASET_DETAIL-001` |
| `RULE-003` | 实体数量超过 50 时默认建议批量导入 | intent-library.dataset-detail | `CAP-IL-DATASET_DETAIL-001` |
| `RULE-004` | 相似问用于正样本训练，排除问用于负样本约束 | intent-library.dataset-detail | `CAP-IL-DATASET_DETAIL-001` |

### exception_flows

| exception_id | scenario | expected_feedback | recovery |
|--------------|----------|-------------------|----------|
| `EX-NONE` | 当前页面未自动识别到异常流 | - | - |

## Page: intent-library.datasets

```yaml
page_id: intent-library.datasets
page_name: 数据集管理
page_boundary: main-page
goal: 统一管理指令库的训练数据集和评估数据集，支持手工创建和 LLM 合成扩充
route_or_entry: datasets.html
parent_page: intent-library.detail
```

### primary_user_flows

- 进入列表 → 点击新建数据集 → 填写名称/类型 → 提交 → 列表回读
- 点击 LLM 合成 → 选择数据集/模型/样本数/提示词 → 提交 → 展示生成结果条数
- 点击管理数据 → 跳转 dataset-detail.html

### visible_ui

| ui_id | type | label | purpose | source |
|------|------|-------|---------|--------|
| `UI-DATASETS-001` | `actions` | 操作入口 | 管理数据, 下载, 删除, 说明, LLM生成训练集, LLM生成评估集, 导入训练集, 导入评估集, 查询, 重置, 恢复默认提示词 | page actions |

### hidden_interactions

| hidden_id | container | classification | entry | purpose |
|-----------|-----------|----------------|-------|---------|
| `HID-DATASETS-001` | `drawer` | `instructional` | 说明按钮 | 解释页面逻辑、状态流转、字段说明和易错点 |

### capabilities

| capability_id | title | type | priority | done_signal |
|---------------|-------|------|----------|-------------|
| `CAP-IL-DATASETS-001` | 编辑当前项 | `CRUD` | `P1` | 保存后页面主数据回读为最新值 |
| `CAP-IL-DATASETS-002` | 删除当前项 | `CRUD` | `P1` | 删除后列表或详情不再显示目标项 |
| `CAP-IL-DATASETS-003` | 导入训练集 | `DATA` | `P0` | 训练集导入结果必须真实回读 |
| `CAP-IL-DATASETS-004` | 导入评估集 | `DATA` | `P0` | 评估集导入结果必须真实回读 |
| `CAP-IL-DATASETS-005` | LLM 生成训练集 | `ASYNC` | `P1` | 生成任务必须返回真实结果或明确失败原因 |
| `CAP-IL-DATASETS-006` | LLM 生成评估集 | `ASYNC` | `P1` | 生成任务必须返回真实结果或明确失败原因 |
| `CAP-IL-DATASETS-007` | 管理数据集内容 | `DATA` | `P0` | 进入数据管理页后应可回读最新数据 |

### action_contracts

| action_id | action | preconditions | success_signal | failure_feedback | state_change |
|-----------|--------|---------------|----------------|------------------|--------------|
| `ACT-001` | 编辑当前项 | 必要字段合法且权限满足 | 保存后页面主数据回读为最新值 | 必须给出明确错误提示，不允许假成功 | 编辑当前项 |
| `ACT-002` | 删除当前项 | 必要字段合法且权限满足 | 删除后列表或详情不再显示目标项 | 必须给出明确错误提示，不允许假成功 | 删除当前项 |
| `ACT-003` | 导入训练集 | 必要字段合法且权限满足 | 训练集导入结果必须真实回读 | 必须给出明确错误提示，不允许假成功 | 导入训练集 |
| `ACT-004` | 导入评估集 | 必要字段合法且权限满足 | 评估集导入结果必须真实回读 | 必须给出明确错误提示，不允许假成功 | 导入评估集 |
| `ACT-005` | LLM 生成训练集 | 必要字段合法且权限满足 | 生成任务必须返回真实结果或明确失败原因 | 必须给出明确错误提示，不允许假成功 | LLM 生成训练集 |
| `ACT-006` | LLM 生成评估集 | 必要字段合法且权限满足 | 生成任务必须返回真实结果或明确失败原因 | 必须给出明确错误提示，不允许假成功 | LLM 生成评估集 |
| `ACT-007` | 管理数据集内容 | 必要字段合法且权限满足 | 进入数据管理页后应可回读最新数据 | 必须给出明确错误提示，不允许假成功 | 管理数据集内容 |

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

## Page: intent-library.detail

```yaml
page_id: intent-library.detail
page_name: 指令库详情
page_boundary: sub-page
goal: 管理单个指令库的模型生命周期，从创建训练任务到评估、测试、发布、归档
route_or_entry: detail.html
parent_page: intent-library.index
```

### primary_user_flows

- 进入详情 → 查看模型版本列表 → 点击新建训练 → 选择训练集 → 提交 → 状态变为 training → 轮询至 trained
- 选择 trained 模型 → 发布 → 确认弹窗(版本对比+勾选+倒计时) → published
- 选择 testable/published 模型 → 点击测试 → 跳转 test.html

### visible_ui

| ui_id | type | label | purpose | source |
|------|------|-------|---------|--------|
| `UI-DETAIL-001` | `actions` | 操作入口 | 说明, 数据集, 新建训练, 新建训练任务, 导入数据集, 发布模型, 归档版本, 下载模型, 查看, 删除, 取消 | page actions |

### hidden_interactions

| hidden_id | container | classification | entry | purpose |
|-----------|-----------|----------------|-------|---------|
| `HID-DETAIL-001` | `drawer` | `instructional` | 说明按钮 | 解释页面逻辑、状态流转、字段说明和易错点 |

### capabilities

| capability_id | title | type | priority | done_signal |
|---------------|-------|------|----------|-------------|
| `CAP-IL-DETAIL-001` | 编辑当前项 | `CRUD` | `P1` | 保存后页面主数据回读为最新值 |
| `CAP-IL-DETAIL-002` | 删除当前项 | `CRUD` | `P1` | 删除后列表或详情不再显示目标项 |
| `CAP-IL-DETAIL-003` | 导入训练集 | `DATA` | `P0` | 训练集导入结果必须真实回读 |
| `CAP-IL-DETAIL-004` | 创建训练任务 | `ASYNC` | `P0` | 训练任务创建后列表回读出现新任务 |
| `CAP-IL-DETAIL-005` | 发布模型 | `STATE` | `P0` | 发布完成后模型状态真实回读更新 |
| `CAP-IL-DETAIL-006` | 归档模型版本 | `STATE` | `P1` | 归档后版本状态真实回读更新 |
| `CAP-IL-DETAIL-007` | 下载模型 | `FEEDBACK` | `P1` | 下载动作返回真实文件或明确失败原因 |

### action_contracts

| action_id | action | preconditions | success_signal | failure_feedback | state_change |
|-----------|--------|---------------|----------------|------------------|--------------|
| `ACT-001` | 编辑当前项 | 必要字段合法且权限满足 | 保存后页面主数据回读为最新值 | 必须给出明确错误提示，不允许假成功 | 编辑当前项 |
| `ACT-002` | 删除当前项 | 必要字段合法且权限满足 | 删除后列表或详情不再显示目标项 | 必须给出明确错误提示，不允许假成功 | 删除当前项 |
| `ACT-003` | 导入训练集 | 必要字段合法且权限满足 | 训练集导入结果必须真实回读 | 必须给出明确错误提示，不允许假成功 | 导入训练集 |
| `ACT-004` | 创建训练任务 | 必要字段合法且权限满足 | 训练任务创建后列表回读出现新任务 | 必须给出明确错误提示，不允许假成功 | 创建训练任务 |
| `ACT-005` | 发布模型 | 必要字段合法且权限满足 | 发布完成后模型状态真实回读更新 | 必须给出明确错误提示，不允许假成功 | 发布模型 |
| `ACT-006` | 归档模型版本 | 必要字段合法且权限满足 | 归档后版本状态真实回读更新 | 必须给出明确错误提示，不允许假成功 | 归档模型版本 |
| `ACT-007` | 下载模型 | 必要字段合法且权限满足 | 下载动作返回真实文件或明确失败原因 | 必须给出明确错误提示，不允许假成功 | 下载模型 |

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

## Page: intent-library.index

```yaml
page_id: intent-library.index
page_name: 指令库管理
page_boundary: main-page
goal: 快速检索、筛选并管理所有指令库，一目了然掌握各库模型容量和发布状态
route_or_entry: index.html
parent_page: none
```

### primary_user_flows

- 进入列表页 → 通过名称/Key/语种筛选 → 定位目标库 → 点击行进入详情
- 点击新建 → 填写 library_key / 名称 / 语种 → 提交 → 列表回读新增项
- 点击删除 → 确认弹窗 → 列表移除（published 状态禁止删除）

### visible_ui

| ui_id | type | label | purpose | source |
|------|------|-------|---------|--------|
| `UI-INDEX-001` | `stats` | 统计卡 | 总库数量, 已发布, 训练中, 即将满额 | prototype state |
| `UI-INDEX-002` | `actions` | 操作入口 | 查看, 编辑, 删除, 说明, 导入, 新建指令库, 查询, 重置 | page actions |

### hidden_interactions

| hidden_id | container | classification | entry | purpose |
|-----------|-----------|----------------|-------|---------|
| `HID-INDEX-001` | `drawer` | `instructional` | 说明按钮 | 解释页面逻辑、状态流转、字段说明和易错点 |

### capabilities

| capability_id | title | type | priority | done_signal |
|---------------|-------|------|----------|-------------|
| `CAP-IL-INDEX-001` | 查看页面主数据 | `DATA` | `P0` | 页面主数据来自真实回读，而非本地硬编码 |
| `CAP-IL-INDEX-002` | 新建指令库 | `CRUD` | `P0` | 新建成功后列表回读出现新库 |
| `CAP-IL-INDEX-003` | 编辑当前项 | `CRUD` | `P1` | 保存后页面主数据回读为最新值 |
| `CAP-IL-INDEX-004` | 删除当前项 | `CRUD` | `P1` | 删除后列表或详情不再显示目标项 |

### action_contracts

| action_id | action | preconditions | success_signal | failure_feedback | state_change |
|-----------|--------|---------------|----------------|------------------|--------------|
| `ACT-002` | 新建指令库 | 必要字段合法且权限满足 | 新建成功后列表回读出现新库 | 必须给出明确错误提示，不允许假成功 | 新建指令库 |
| `ACT-003` | 编辑当前项 | 必要字段合法且权限满足 | 保存后页面主数据回读为最新值 | 必须给出明确错误提示，不允许假成功 | 编辑当前项 |
| `ACT-004` | 删除当前项 | 必要字段合法且权限满足 | 删除后列表或详情不再显示目标项 | 必须给出明确错误提示，不允许假成功 | 删除当前项 |

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

## Page: intent-library.test

```yaml
page_id: intent-library.test
page_name: 模型测试
page_boundary: sub-page
goal: 验证模型推理质量，通过单条对话式测试和库内批量评估确认模型可用性
route_or_entry: test.html
parent_page: intent-library.detail
```

### primary_user_flows

- 选择模型 → 新建会话 → 输入测试文本 → 发送 → 查看意图/置信度/槽位/耗时
- 新建批量测试 → 填写测试输入 → 执行 → 查看每条结果的实际 vs 预期对比
- 切换到批量测试 Tab → 查看历史批次 → 点击查看智能分析报告

### visible_ui

| ui_id | type | label | purpose | source |
|------|------|-------|---------|--------|
| `UI-TEST-001` | `actions` | 操作入口 | 智能分析, 查看, 新建测试任务, 关闭, 返回, 说明 | page actions |

### hidden_interactions

| hidden_id | container | classification | entry | purpose |
|-----------|-----------|----------------|-------|---------|
| `HID-TEST-001` | `drawer` | `instructional` | 说明按钮 | 解释页面逻辑、状态流转、字段说明和易错点 |

### capabilities

| capability_id | title | type | priority | done_signal |
|---------------|-------|------|----------|-------------|
| `CAP-IL-TEST-001` | 进入平台级批量测试 | `NAVIGATION` | `P1` | 可跳转到批量测试模块入口 |
| `CAP-IL-TEST-002` | 删除当前项 | `CRUD` | `P1` | 删除后列表或详情不再显示目标项 |
| `CAP-IL-TEST-003` | 创建测试任务 | `ASYNC` | `P0` | 测试任务创建后列表回读出现新任务 |
| `CAP-IL-TEST-004` | 查看智能分析 | `FEEDBACK` | `P1` | 分析结果必须来自真实计算或明确失败原因 |

### action_contracts

| action_id | action | preconditions | success_signal | failure_feedback | state_change |
|-----------|--------|---------------|----------------|------------------|--------------|
| `ACT-001` | 进入平台级批量测试 | 必要字段合法且权限满足 | 可跳转到批量测试模块入口 | 必须给出明确错误提示，不允许假成功 | 进入平台级批量测试 |
| `ACT-002` | 删除当前项 | 必要字段合法且权限满足 | 删除后列表或详情不再显示目标项 | 必须给出明确错误提示，不允许假成功 | 删除当前项 |
| `ACT-003` | 创建测试任务 | 必要字段合法且权限满足 | 测试任务创建后列表回读出现新任务 | 必须给出明确错误提示，不允许假成功 | 创建测试任务 |

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
| `CAP-IL-DATASET_DETAIL-001` | `FR-002` | `full` |
| `CAP-IL-DATASET_DETAIL-001` | `FR-003` | `full` |
| `CAP-IL-DATASET_DETAIL-001` | `FR-049` | `full` |
| `CAP-IL-DATASET_DETAIL-002` | `FR-002` | `full` |
| `CAP-IL-DATASET_DETAIL-002` | `FR-003` | `full` |
| `CAP-IL-DATASET_DETAIL-002` | `FR-049` | `full` |
| `CAP-IL-DATASET_DETAIL-003` | `FR-002` | `full` |
| `CAP-IL-DATASET_DETAIL-003` | `FR-003` | `full` |
| `CAP-IL-DATASET_DETAIL-003` | `FR-049` | `full` |
| `CAP-IL-DATASET_DETAIL-004` | `FR-002` | `full` |
| `CAP-IL-DATASET_DETAIL-004` | `FR-003` | `full` |
| `CAP-IL-DATASET_DETAIL-004` | `FR-049` | `full` |
| `CAP-IL-DATASET_DETAIL-005` | `FR-002` | `full` |
| `CAP-IL-DATASET_DETAIL-005` | `FR-003` | `full` |
| `CAP-IL-DATASET_DETAIL-005` | `FR-049` | `full` |
| `CAP-IL-DATASET_DETAIL-006` | `FR-002` | `full` |
| `CAP-IL-DATASET_DETAIL-006` | `FR-003` | `full` |
| `CAP-IL-DATASET_DETAIL-006` | `FR-049` | `full` |
| `CAP-IL-DATASET_DETAIL-007` | `FR-002` | `full` |
| `CAP-IL-DATASET_DETAIL-007` | `FR-003` | `full` |
| `CAP-IL-DATASET_DETAIL-007` | `FR-049` | `full` |
| `CAP-IL-DATASETS-001` | `FR-002` | `full` |
| `CAP-IL-DATASETS-001` | `FR-003` | `full` |
| `CAP-IL-DATASETS-001` | `FR-039` | `full` |
| `CAP-IL-DATASETS-001` | `FR-043` | `full` |
| `CAP-IL-DATASETS-001` | `FR-044` | `full` |
| `CAP-IL-DATASETS-001` | `FR-045` | `full` |
| `CAP-IL-DATASETS-001` | `FR-046` | `full` |
| `CAP-IL-DATASETS-001` | `FR-047` | `full` |
| `CAP-IL-DATASETS-001` | `FR-048` | `full` |
| `CAP-IL-DATASETS-001` | `FR-049` | `full` |
| `CAP-IL-DATASETS-001` | `FR-050` | `full` |
| `CAP-IL-DATASETS-001` | `FR-051` | `full` |
| `CAP-IL-DATASETS-001` | `FR-052` | `full` |
| `CAP-IL-DATASETS-001` | `FR-053` | `full` |
| `CAP-IL-DATASETS-001` | `FR-054` | `full` |
| `CAP-IL-DATASETS-002` | `FR-002` | `full` |
| `CAP-IL-DATASETS-002` | `FR-003` | `full` |
| `CAP-IL-DATASETS-002` | `FR-039` | `full` |
| `CAP-IL-DATASETS-002` | `FR-043` | `full` |
| `CAP-IL-DATASETS-002` | `FR-044` | `full` |
| `CAP-IL-DATASETS-002` | `FR-045` | `full` |
| `CAP-IL-DATASETS-002` | `FR-046` | `full` |
| `CAP-IL-DATASETS-002` | `FR-047` | `full` |
| `CAP-IL-DATASETS-002` | `FR-048` | `full` |
| `CAP-IL-DATASETS-002` | `FR-049` | `full` |
| `CAP-IL-DATASETS-002` | `FR-050` | `full` |
| `CAP-IL-DATASETS-002` | `FR-051` | `full` |
| `CAP-IL-DATASETS-002` | `FR-052` | `full` |
| `CAP-IL-DATASETS-002` | `FR-053` | `full` |
| `CAP-IL-DATASETS-002` | `FR-054` | `full` |
| `CAP-IL-DATASETS-003` | `FR-002` | `full` |
| `CAP-IL-DATASETS-003` | `FR-003` | `full` |
| `CAP-IL-DATASETS-003` | `FR-039` | `full` |
| `CAP-IL-DATASETS-003` | `FR-043` | `full` |
| `CAP-IL-DATASETS-003` | `FR-044` | `full` |
| `CAP-IL-DATASETS-003` | `FR-045` | `full` |
| `CAP-IL-DATASETS-003` | `FR-046` | `full` |
| `CAP-IL-DATASETS-003` | `FR-047` | `full` |
| `CAP-IL-DATASETS-003` | `FR-048` | `full` |
| `CAP-IL-DATASETS-003` | `FR-049` | `full` |
| `CAP-IL-DATASETS-003` | `FR-050` | `full` |
| `CAP-IL-DATASETS-003` | `FR-051` | `full` |
| `CAP-IL-DATASETS-003` | `FR-052` | `full` |
| `CAP-IL-DATASETS-003` | `FR-053` | `full` |
| `CAP-IL-DATASETS-003` | `FR-054` | `full` |
| `CAP-IL-DATASETS-004` | `FR-002` | `full` |
| `CAP-IL-DATASETS-004` | `FR-003` | `full` |
| `CAP-IL-DATASETS-004` | `FR-039` | `full` |
| `CAP-IL-DATASETS-004` | `FR-043` | `full` |
| `CAP-IL-DATASETS-004` | `FR-044` | `full` |
| `CAP-IL-DATASETS-004` | `FR-045` | `full` |
| `CAP-IL-DATASETS-004` | `FR-046` | `full` |
| `CAP-IL-DATASETS-004` | `FR-047` | `full` |
| `CAP-IL-DATASETS-004` | `FR-048` | `full` |
| `CAP-IL-DATASETS-004` | `FR-049` | `full` |
| `CAP-IL-DATASETS-004` | `FR-050` | `full` |
| `CAP-IL-DATASETS-004` | `FR-051` | `full` |
| `CAP-IL-DATASETS-004` | `FR-052` | `full` |
| `CAP-IL-DATASETS-004` | `FR-053` | `full` |
| `CAP-IL-DATASETS-004` | `FR-054` | `full` |
| `CAP-IL-DATASETS-005` | `FR-002` | `full` |
| `CAP-IL-DATASETS-005` | `FR-003` | `full` |
| `CAP-IL-DATASETS-005` | `FR-039` | `full` |
| `CAP-IL-DATASETS-005` | `FR-043` | `full` |
| `CAP-IL-DATASETS-005` | `FR-044` | `full` |
| `CAP-IL-DATASETS-005` | `FR-045` | `full` |
| `CAP-IL-DATASETS-005` | `FR-046` | `full` |
| `CAP-IL-DATASETS-005` | `FR-047` | `full` |
| `CAP-IL-DATASETS-005` | `FR-048` | `full` |
| `CAP-IL-DATASETS-005` | `FR-049` | `full` |
| `CAP-IL-DATASETS-005` | `FR-050` | `full` |
| `CAP-IL-DATASETS-005` | `FR-051` | `full` |
| `CAP-IL-DATASETS-005` | `FR-052` | `full` |
| `CAP-IL-DATASETS-005` | `FR-053` | `full` |
| `CAP-IL-DATASETS-005` | `FR-054` | `full` |
| `CAP-IL-DATASETS-006` | `FR-002` | `full` |
| `CAP-IL-DATASETS-006` | `FR-003` | `full` |
| `CAP-IL-DATASETS-006` | `FR-039` | `full` |
| `CAP-IL-DATASETS-006` | `FR-043` | `full` |
| `CAP-IL-DATASETS-006` | `FR-044` | `full` |
| `CAP-IL-DATASETS-006` | `FR-045` | `full` |
| `CAP-IL-DATASETS-006` | `FR-046` | `full` |
| `CAP-IL-DATASETS-006` | `FR-047` | `full` |
| `CAP-IL-DATASETS-006` | `FR-048` | `full` |
| `CAP-IL-DATASETS-006` | `FR-049` | `full` |
| `CAP-IL-DATASETS-006` | `FR-050` | `full` |
| `CAP-IL-DATASETS-006` | `FR-051` | `full` |
| `CAP-IL-DATASETS-006` | `FR-052` | `full` |
| `CAP-IL-DATASETS-006` | `FR-053` | `full` |
| `CAP-IL-DATASETS-006` | `FR-054` | `full` |
| `CAP-IL-DATASETS-007` | `FR-002` | `full` |
| `CAP-IL-DATASETS-007` | `FR-003` | `full` |
| `CAP-IL-DATASETS-007` | `FR-039` | `full` |
| `CAP-IL-DATASETS-007` | `FR-043` | `full` |
| `CAP-IL-DATASETS-007` | `FR-044` | `full` |
| `CAP-IL-DATASETS-007` | `FR-045` | `full` |
| `CAP-IL-DATASETS-007` | `FR-046` | `full` |
| `CAP-IL-DATASETS-007` | `FR-047` | `full` |
| `CAP-IL-DATASETS-007` | `FR-048` | `full` |
| `CAP-IL-DATASETS-007` | `FR-049` | `full` |
| `CAP-IL-DATASETS-007` | `FR-050` | `full` |
| `CAP-IL-DATASETS-007` | `FR-051` | `full` |
| `CAP-IL-DATASETS-007` | `FR-052` | `full` |
| `CAP-IL-DATASETS-007` | `FR-053` | `full` |
| `CAP-IL-DATASETS-007` | `FR-054` | `full` |
| `CAP-IL-DETAIL-001` | `FR-002` | `full` |
| `CAP-IL-DETAIL-001` | `FR-003` | `full` |
| `CAP-IL-DETAIL-001` | `FR-039` | `full` |
| `CAP-IL-DETAIL-001` | `FR-043` | `full` |
| `CAP-IL-DETAIL-001` | `FR-044` | `full` |
| `CAP-IL-DETAIL-001` | `FR-045` | `full` |
| `CAP-IL-DETAIL-001` | `FR-046` | `full` |
| `CAP-IL-DETAIL-001` | `FR-047` | `full` |
| `CAP-IL-DETAIL-001` | `FR-048` | `full` |
| `CAP-IL-DETAIL-001` | `FR-049` | `full` |
| `CAP-IL-DETAIL-001` | `FR-050` | `full` |
| `CAP-IL-DETAIL-001` | `FR-051` | `full` |
| `CAP-IL-DETAIL-001` | `FR-052` | `full` |
| `CAP-IL-DETAIL-001` | `FR-053` | `full` |
| `CAP-IL-DETAIL-001` | `FR-054` | `full` |
| `CAP-IL-DETAIL-002` | `FR-002` | `full` |
| `CAP-IL-DETAIL-002` | `FR-003` | `full` |
| `CAP-IL-DETAIL-002` | `FR-039` | `full` |
| `CAP-IL-DETAIL-002` | `FR-043` | `full` |
| `CAP-IL-DETAIL-002` | `FR-044` | `full` |
| `CAP-IL-DETAIL-002` | `FR-045` | `full` |
| `CAP-IL-DETAIL-002` | `FR-046` | `full` |
| `CAP-IL-DETAIL-002` | `FR-047` | `full` |
| `CAP-IL-DETAIL-002` | `FR-048` | `full` |
| `CAP-IL-DETAIL-002` | `FR-049` | `full` |
| `CAP-IL-DETAIL-002` | `FR-050` | `full` |
| `CAP-IL-DETAIL-002` | `FR-051` | `full` |
| `CAP-IL-DETAIL-002` | `FR-052` | `full` |
| `CAP-IL-DETAIL-002` | `FR-053` | `full` |
| `CAP-IL-DETAIL-002` | `FR-054` | `full` |
| `CAP-IL-DETAIL-003` | `FR-002` | `full` |
| `CAP-IL-DETAIL-003` | `FR-003` | `full` |
| `CAP-IL-DETAIL-003` | `FR-039` | `full` |
| `CAP-IL-DETAIL-003` | `FR-043` | `full` |
| `CAP-IL-DETAIL-003` | `FR-044` | `full` |
| `CAP-IL-DETAIL-003` | `FR-045` | `full` |
| `CAP-IL-DETAIL-003` | `FR-046` | `full` |
| `CAP-IL-DETAIL-003` | `FR-047` | `full` |
| `CAP-IL-DETAIL-003` | `FR-048` | `full` |
| `CAP-IL-DETAIL-003` | `FR-049` | `full` |
| `CAP-IL-DETAIL-003` | `FR-050` | `full` |
| `CAP-IL-DETAIL-003` | `FR-051` | `full` |
| `CAP-IL-DETAIL-003` | `FR-052` | `full` |
| `CAP-IL-DETAIL-003` | `FR-053` | `full` |
| `CAP-IL-DETAIL-003` | `FR-054` | `full` |
| `CAP-IL-DETAIL-004` | `FR-002` | `full` |
| `CAP-IL-DETAIL-004` | `FR-003` | `full` |
| `CAP-IL-DETAIL-004` | `FR-039` | `full` |
| `CAP-IL-DETAIL-004` | `FR-043` | `full` |
| `CAP-IL-DETAIL-004` | `FR-044` | `full` |
| `CAP-IL-DETAIL-004` | `FR-045` | `full` |
| `CAP-IL-DETAIL-004` | `FR-046` | `full` |
| `CAP-IL-DETAIL-004` | `FR-047` | `full` |
| `CAP-IL-DETAIL-004` | `FR-048` | `full` |
| `CAP-IL-DETAIL-004` | `FR-049` | `full` |
| `CAP-IL-DETAIL-004` | `FR-050` | `full` |
| `CAP-IL-DETAIL-004` | `FR-051` | `full` |
| `CAP-IL-DETAIL-004` | `FR-052` | `full` |
| `CAP-IL-DETAIL-004` | `FR-053` | `full` |
| `CAP-IL-DETAIL-004` | `FR-054` | `full` |
| `CAP-IL-DETAIL-005` | `FR-002` | `full` |
| `CAP-IL-DETAIL-005` | `FR-003` | `full` |
| `CAP-IL-DETAIL-005` | `FR-039` | `full` |
| `CAP-IL-DETAIL-005` | `FR-043` | `full` |
| `CAP-IL-DETAIL-005` | `FR-044` | `full` |
| `CAP-IL-DETAIL-005` | `FR-045` | `full` |
| `CAP-IL-DETAIL-005` | `FR-046` | `full` |
| `CAP-IL-DETAIL-005` | `FR-047` | `full` |
| `CAP-IL-DETAIL-005` | `FR-048` | `full` |
| `CAP-IL-DETAIL-005` | `FR-049` | `full` |
| `CAP-IL-DETAIL-005` | `FR-050` | `full` |
| `CAP-IL-DETAIL-005` | `FR-051` | `full` |
| `CAP-IL-DETAIL-005` | `FR-052` | `full` |
| `CAP-IL-DETAIL-005` | `FR-053` | `full` |
| `CAP-IL-DETAIL-005` | `FR-054` | `full` |
| `CAP-IL-DETAIL-006` | `FR-002` | `full` |
| `CAP-IL-DETAIL-006` | `FR-003` | `full` |
| `CAP-IL-DETAIL-006` | `FR-039` | `full` |
| `CAP-IL-DETAIL-006` | `FR-043` | `full` |
| `CAP-IL-DETAIL-006` | `FR-044` | `full` |
| `CAP-IL-DETAIL-006` | `FR-045` | `full` |
| `CAP-IL-DETAIL-006` | `FR-046` | `full` |
| `CAP-IL-DETAIL-006` | `FR-047` | `full` |
| `CAP-IL-DETAIL-006` | `FR-048` | `full` |
| `CAP-IL-DETAIL-006` | `FR-049` | `full` |
| `CAP-IL-DETAIL-006` | `FR-050` | `full` |
| `CAP-IL-DETAIL-006` | `FR-051` | `full` |
| `CAP-IL-DETAIL-006` | `FR-052` | `full` |
| `CAP-IL-DETAIL-006` | `FR-053` | `full` |
| `CAP-IL-DETAIL-006` | `FR-054` | `full` |
| `CAP-IL-DETAIL-007` | `FR-002` | `full` |
| `CAP-IL-DETAIL-007` | `FR-003` | `full` |
| `CAP-IL-DETAIL-007` | `FR-039` | `full` |
| `CAP-IL-DETAIL-007` | `FR-043` | `full` |
| `CAP-IL-DETAIL-007` | `FR-044` | `full` |
| `CAP-IL-DETAIL-007` | `FR-045` | `full` |
| `CAP-IL-DETAIL-007` | `FR-046` | `full` |
| `CAP-IL-DETAIL-007` | `FR-047` | `full` |
| `CAP-IL-DETAIL-007` | `FR-048` | `full` |
| `CAP-IL-DETAIL-007` | `FR-049` | `full` |
| `CAP-IL-DETAIL-007` | `FR-050` | `full` |
| `CAP-IL-DETAIL-007` | `FR-051` | `full` |
| `CAP-IL-DETAIL-007` | `FR-052` | `full` |
| `CAP-IL-DETAIL-007` | `FR-053` | `full` |
| `CAP-IL-DETAIL-007` | `FR-054` | `full` |
| `CAP-IL-INDEX-001` | `FR-002` | `full` |
| `CAP-IL-INDEX-001` | `FR-003` | `full` |
| `CAP-IL-INDEX-001` | `FR-039` | `full` |
| `CAP-IL-INDEX-001` | `FR-043` | `full` |
| `CAP-IL-INDEX-001` | `FR-044` | `full` |
| `CAP-IL-INDEX-001` | `FR-045` | `full` |
| `CAP-IL-INDEX-001` | `FR-046` | `full` |
| `CAP-IL-INDEX-001` | `FR-047` | `full` |
| `CAP-IL-INDEX-001` | `FR-048` | `full` |
| `CAP-IL-INDEX-001` | `FR-049` | `full` |
| `CAP-IL-INDEX-001` | `FR-050` | `full` |
| `CAP-IL-INDEX-001` | `FR-051` | `full` |
| `CAP-IL-INDEX-001` | `FR-052` | `full` |
| `CAP-IL-INDEX-001` | `FR-053` | `full` |
| `CAP-IL-INDEX-001` | `FR-054` | `full` |
| `CAP-IL-INDEX-002` | `FR-002` | `full` |
| `CAP-IL-INDEX-002` | `FR-003` | `full` |
| `CAP-IL-INDEX-002` | `FR-039` | `full` |
| `CAP-IL-INDEX-002` | `FR-043` | `full` |
| `CAP-IL-INDEX-002` | `FR-044` | `full` |
| `CAP-IL-INDEX-002` | `FR-045` | `full` |
| `CAP-IL-INDEX-002` | `FR-046` | `full` |
| `CAP-IL-INDEX-002` | `FR-047` | `full` |
| `CAP-IL-INDEX-002` | `FR-048` | `full` |
| `CAP-IL-INDEX-002` | `FR-049` | `full` |
| `CAP-IL-INDEX-002` | `FR-050` | `full` |
| `CAP-IL-INDEX-002` | `FR-051` | `full` |
| `CAP-IL-INDEX-002` | `FR-052` | `full` |
| `CAP-IL-INDEX-002` | `FR-053` | `full` |
| `CAP-IL-INDEX-002` | `FR-054` | `full` |
| `CAP-IL-INDEX-003` | `FR-002` | `full` |
| `CAP-IL-INDEX-003` | `FR-003` | `full` |
| `CAP-IL-INDEX-003` | `FR-039` | `full` |
| `CAP-IL-INDEX-003` | `FR-043` | `full` |
| `CAP-IL-INDEX-003` | `FR-044` | `full` |
| `CAP-IL-INDEX-003` | `FR-045` | `full` |
| `CAP-IL-INDEX-003` | `FR-046` | `full` |
| `CAP-IL-INDEX-003` | `FR-047` | `full` |
| `CAP-IL-INDEX-003` | `FR-048` | `full` |
| `CAP-IL-INDEX-003` | `FR-049` | `full` |
| `CAP-IL-INDEX-003` | `FR-050` | `full` |
| `CAP-IL-INDEX-003` | `FR-051` | `full` |
| `CAP-IL-INDEX-003` | `FR-052` | `full` |
| `CAP-IL-INDEX-003` | `FR-053` | `full` |
| `CAP-IL-INDEX-003` | `FR-054` | `full` |
| `CAP-IL-INDEX-004` | `FR-002` | `full` |
| `CAP-IL-INDEX-004` | `FR-003` | `full` |
| `CAP-IL-INDEX-004` | `FR-039` | `full` |
| `CAP-IL-INDEX-004` | `FR-043` | `full` |
| `CAP-IL-INDEX-004` | `FR-044` | `full` |
| `CAP-IL-INDEX-004` | `FR-045` | `full` |
| `CAP-IL-INDEX-004` | `FR-046` | `full` |
| `CAP-IL-INDEX-004` | `FR-047` | `full` |
| `CAP-IL-INDEX-004` | `FR-048` | `full` |
| `CAP-IL-INDEX-004` | `FR-049` | `full` |
| `CAP-IL-INDEX-004` | `FR-050` | `full` |
| `CAP-IL-INDEX-004` | `FR-051` | `full` |
| `CAP-IL-INDEX-004` | `FR-052` | `full` |
| `CAP-IL-INDEX-004` | `FR-053` | `full` |
| `CAP-IL-INDEX-004` | `FR-054` | `full` |
| `CAP-IL-TEST-001` | `FR-002` | `full` |
| `CAP-IL-TEST-001` | `FR-003` | `full` |
| `CAP-IL-TEST-001` | `FR-039` | `full` |
| `CAP-IL-TEST-001` | `FR-043` | `full` |
| `CAP-IL-TEST-001` | `FR-044` | `full` |
| `CAP-IL-TEST-001` | `FR-045` | `full` |
| `CAP-IL-TEST-001` | `FR-046` | `full` |
| `CAP-IL-TEST-001` | `FR-047` | `full` |
| `CAP-IL-TEST-001` | `FR-048` | `full` |
| `CAP-IL-TEST-001` | `FR-049` | `full` |
| `CAP-IL-TEST-001` | `FR-050` | `full` |
| `CAP-IL-TEST-001` | `FR-051` | `full` |
| `CAP-IL-TEST-001` | `FR-052` | `full` |
| `CAP-IL-TEST-001` | `FR-053` | `full` |
| `CAP-IL-TEST-001` | `FR-054` | `full` |
| `CAP-IL-TEST-002` | `FR-002` | `full` |
| `CAP-IL-TEST-002` | `FR-003` | `full` |
| `CAP-IL-TEST-002` | `FR-039` | `full` |
| `CAP-IL-TEST-002` | `FR-043` | `full` |
| `CAP-IL-TEST-002` | `FR-044` | `full` |
| `CAP-IL-TEST-002` | `FR-045` | `full` |
| `CAP-IL-TEST-002` | `FR-046` | `full` |
| `CAP-IL-TEST-002` | `FR-047` | `full` |
| `CAP-IL-TEST-002` | `FR-048` | `full` |
| `CAP-IL-TEST-002` | `FR-049` | `full` |
| `CAP-IL-TEST-002` | `FR-050` | `full` |
| `CAP-IL-TEST-002` | `FR-051` | `full` |
| `CAP-IL-TEST-002` | `FR-052` | `full` |
| `CAP-IL-TEST-002` | `FR-053` | `full` |
| `CAP-IL-TEST-002` | `FR-054` | `full` |
| `CAP-IL-TEST-003` | `FR-002` | `full` |
| `CAP-IL-TEST-003` | `FR-003` | `full` |
| `CAP-IL-TEST-003` | `FR-039` | `full` |
| `CAP-IL-TEST-003` | `FR-043` | `full` |
| `CAP-IL-TEST-003` | `FR-044` | `full` |
| `CAP-IL-TEST-003` | `FR-045` | `full` |
| `CAP-IL-TEST-003` | `FR-046` | `full` |
| `CAP-IL-TEST-003` | `FR-047` | `full` |
| `CAP-IL-TEST-003` | `FR-048` | `full` |
| `CAP-IL-TEST-003` | `FR-049` | `full` |
| `CAP-IL-TEST-003` | `FR-050` | `full` |
| `CAP-IL-TEST-003` | `FR-051` | `full` |
| `CAP-IL-TEST-003` | `FR-052` | `full` |
| `CAP-IL-TEST-003` | `FR-053` | `full` |
| `CAP-IL-TEST-003` | `FR-054` | `full` |
| `CAP-IL-TEST-004` | `FR-002` | `full` |
| `CAP-IL-TEST-004` | `FR-003` | `full` |
| `CAP-IL-TEST-004` | `FR-039` | `full` |
| `CAP-IL-TEST-004` | `FR-043` | `full` |
| `CAP-IL-TEST-004` | `FR-044` | `full` |
| `CAP-IL-TEST-004` | `FR-045` | `full` |
| `CAP-IL-TEST-004` | `FR-046` | `full` |
| `CAP-IL-TEST-004` | `FR-047` | `full` |
| `CAP-IL-TEST-004` | `FR-048` | `full` |
| `CAP-IL-TEST-004` | `FR-049` | `full` |
| `CAP-IL-TEST-004` | `FR-050` | `full` |
| `CAP-IL-TEST-004` | `FR-051` | `full` |
| `CAP-IL-TEST-004` | `FR-052` | `full` |
| `CAP-IL-TEST-004` | `FR-053` | `full` |
| `CAP-IL-TEST-004` | `FR-054` | `full` |

## out_of_scope

- 当前脚本不会从 HumanPD 自动恢复完整业务后端契约，只生成 AI-PD scaffold。
- 若 HumanPD 未显式表达真实路由、异常反馈或数据字段，生成结果会保留保守默认值，需后续人工精修。
