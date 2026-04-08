# AI-PD 模板

## 1. 定位

### 1.1 在研发流程中的位置

```text
spec.md -> HumanPD (pd-all/) -> AI-PD (ai-pd/) -> ad -> dd -> plan -> tasks -> implement -> smoke
```

### 1.2 HumanPD 与 AI-PD 的职责边界

| 维度 | HumanPD (`pd-all/`) | AI-PD (`ai-pd/`) |
|------|---------------------|---------------------|
| 主要读者 | 人类产品/设计/评审者 | AI、harness、下游设计与实施命令 |
| 关注点 | 页面结构、视觉布局、交互演示、评审沟通 | 能力定义、动作契约、数据契约、业务规则、异常流 |
| 表达形式 | HTML 原型 + README | 结构化 Markdown / YAML |
| 是否保留视觉噪音 | 是 | 否 |
| 是否作为下游主输入 | 否，作为参考 | 是 |

### 1.3 AI-PD 的核心目标

1. 把人类可读的 PD 转成 AI 最稳定可消费的语义输入
2. 让 AD / DD / plan / tasks / implement / smoke 共享同一套 capability IDs
3. 降低 HTML 原型中的演示代码、组件噪音、说明性长文对 AI 的干扰
4. 让门禁可以检查“是否覆盖了语义能力”，而不是只检查“是否有页面”

## 2. 输出结构

建议按模块输出：

```text
specs/<branch>/
└── ai-pd/
    ├── README.md
    ├── ai-<module>.md
├── ai-<module>.checklist.md
    └── ai-<module>.yaml   # 可选：若需要更强的程序消费
```

其中：

- `README.md`: 索引、模块列表、状态、生成时间
- `ai-<module>.md`: 人类可读 + AI 可读的主语义规格；人工校对修改必须直接落在这个文件上
- `ai-<module>.checklist.md`: 人工校对高风险语义点的伴生清单；仅供参考，不作为第二真相源，也不作为完成状态记录
- `ai-<module>.yaml`: 可选的机器校验格式

## 3. 模块级结构

每个 `ai-<module>.md` 至少包含：

### 3.1 模块元信息

```yaml
module_key: <module-key>
based_on:
  - spec.md
  - pd-all/pd-index.md
  - pd-all/pd-<module>/README.md
  - pd-all/pd-<module>/*.html
status: draft
```

### 3.2 模块摘要

- 模块目标
- 主要用户
- 主导航链路
- 下游必须继承的显式风险

### 3.3 页面索引

| page_id | page_name | page_boundary | route_or_entry | capability_count | related_fr |
|---------|-----------|---------------|----------------|------------------|------------|
| intent-library.dataset-detail | 数据集详情页 | page | `/intent-library/:libraryId/datasets/:datasetId` | 7 | FR-002, FR-003, FR-049 |

## 4. 页面级结构

每个页面按以下 schema 输出：

### 4.1 页面元信息

```yaml
page_id: <module>.<page>
page_name: <页面名>
page_boundary: page | drawer | modal | popover | inline-block
goal: <页面的业务目标>
route_or_entry: <路由或入口>
parent_page: <父页面，如无则写 none>
```

### 4.2 primary_user_flows

列出该页面承载的核心用户流，按“起点 -> 中间动作 -> 终点/成功信号”描述。

### 4.3 visible_ui

| ui_id | type | label | purpose | source |
|------|------|-------|---------|--------|
| ui-001 | table | 意图列表 | 展示和进入管理 | dataset detail API |

### 4.4 hidden_interactions

| hidden_id | container | classification | entry | purpose |
|-----------|-----------|----------------|-------|---------|
| hidden-001 | Drawer | ui-capability | 编辑意图 | 维护意图配置 |
| hidden-002 | Drawer | instructional | 说明按钮 | 解释数据模型 |

分类值固定为：

- `ui-capability`: 必须被实现、测试、验收
- `domain-rule`: 不是独立 UI，但属于必须继承的业务约束
- `instructional`: 辅助理解，不单独要求实现
- `non-actionable-note`: 纯备注

### 4.5 capabilities

| capability_id | title | type | priority | done_signal |
|---------------|-------|------|----------|-------------|
| CAP-INTENT-001 | CRUD 意图定义 | CRUD | P0 | 列表与详情回读一致 |
| CAP-INTENT-002 | 管理相似问/排除问 | DATA | P0 | Drawer 列表回读新增项 |

能力类型建议：

- `CRUD`
- `DATA`
- `STATE`
- `VALIDATION`
- `FEEDBACK`
- `NAVIGATION`
- `PERMISSION`
- `IMPORT_EXPORT`

### 4.6 action_contracts

| action_id | action | preconditions | success_signal | failure_feedback | state_change |
|-----------|--------|---------------|----------------|------------------|--------------|
| ACT-001 | 保存意图 | key 和中文名合法 | 列表回读新值 | 表单级错误 | intent updated |

### 4.7 data_contracts

| data_id | field_or_column | shape | required | source | notes |
|---------|-----------------|-------|----------|--------|-------|
| DATA-001 | intent_key | string | yes | API payload | 英文唯一标识 |

### 4.8 business_rules

| rule_id | rule | scope | related_capability |
|---------|------|-------|--------------------|
| RULE-001 | 命中/未命中话术与相似问/排除问不能混淆 | dataset-detail | CAP-INTENT-001 |

### 4.9 exception_flows

| exception_id | scenario | expected_feedback | recovery |
|--------------|----------|-------------------|----------|
| EX-001 | 导入格式错误 | 显示字段级错误 | 保留用户输入并允许重试 |

### 4.10 acceptance_signals

- 真实回读信号
- 状态收敛信号
- 必须存在的失败反馈
- 不允许出现的假成功信号

### 4.11 fr_mapping

| capability_id | fr_id | status |
|---------------|------|--------|
| CAP-INTENT-001 | FR-002 | full |
| CAP-INTENT-002 | FR-003 | full |

### 4.12 out_of_scope

- 显式不在本轮范围的内容
- Partial / Deferred / Blocked By

## 5. 转换规则

从 HumanPD 转 AI-PD 时必须遵循：

1. 不复制 HTML 演示代码、组件导入、样式实现细节
2. 只保留会影响实现与验收的产品语义
3. 同一能力必须有稳定 `capability_id`
4. 所有动作必须映射到 `action_contracts`
5. 所有字段、表格列、导入项必须映射到 `data_contracts`
6. 所有约束必须映射到 `business_rules`
7. 所有错误、空态、失败态必须映射到 `exception_flows`
8. 所有隐藏交互必须分类为 `ui-capability / domain-rule / instructional / non-actionable-note`

## 6. 输出检查清单

- [ ] 已覆盖模块内全部页面
- [ ] 每个页面都有稳定 `page_id`
- [ ] 每个能力都有稳定 `capability_id`
- [ ] 每个动作都有 `action_contracts`
- [ ] 每个字段/列/导入项都有 `data_contracts`
- [ ] 每条业务规则都有 `business_rules`
- [ ] 每个异常场景都有 `exception_flows`
- [ ] 所有隐藏交互都已完成语义分类
- [ ] `fr_mapping` 可追溯到 capability 级别
- [ ] Partial / Deferred / Blocked By 已显式登记
- [ ] 已同步生成 `ai-<module>.checklist.md`
- [ ] 人工校对清单只覆盖高风险语义点，而不是要求全文重审

## 7. 人工校对清单要求

每个 `ai-<module>.md` 生成后，必须伴随一个 `ai-<module>.checklist.md`，用于人工快速校对以下内容：

- 页面索引、`page_boundary`、`parent_page`
- `hidden_interactions` 分类是否准确，尤其 Drawer / Modal / Tabs / Collapse 中的真实产品能力
- `capabilities` 粒度是否合理，是否存在关键遗漏或错误合并
- `action_contracts` 的 `success_signal` 是否可用于验收，是否存在假成功表述
- `fr_mapping` 是否只覆盖当前模块真实范围
- `business_rules / exception_flows` 是否存在明显缺失

人工校对要求：

- 所有修改必须直接回写到 `ai-<module>.md`
- `ai-<module>.checklist.md` 只用于提醒“看哪些地方”，不记录独立语义结论
- 不允许把“已校对/已修改”的真实状态只写在 checklist 而不回写 AI-PD 主文件

下列内容默认属于自动可信项，只需抽样查看，不要求逐项全文复核：

- 显性按钮、表格列、统计卡、表单字段
- `page_id` / `route_or_entry` 的格式化结果
- 已在 README 中明确写出的 `使用场景` 和 `成功标准`
