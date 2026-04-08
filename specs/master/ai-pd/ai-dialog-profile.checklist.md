# AI-PD 人工校对清单: dialog-profile

## 使用方式

- 本清单只覆盖高风险语义点，不要求对 `ai-dialog-profile.md` 做全文重审
- 校对时必须直接修改 `ai-dialog-profile.md`
- 本清单只作为审核辅助，不是第二份语义真相，也不是“是否已修改完成”的状态记录
- `visible_ui`、显性表格列、显性按钮、显性表单字段默认按“自动可信项”处理，除非你发现明显抽取错误

## 模块级必查项

- [ ] 模块 `覆盖 FR` 只包含当前模块真实覆盖范围，不含跨模块引用或 `out_of_scope`
- [ ] `out_of_scope` 已显式写清 Deferred / Blocked By / 跨模块引用 / AD-DD 范围项
- [ ] 页面索引完整，页面数量与 `pd-all/pd-dialog-profile/` 中 HTML 文件一致
- [ ] 所有页面都有稳定 `page_id`，且主页面的 `parent_page` 为 `none`
- [ ] 若模块存在隐藏交互承载真实产品能力，相关项已在 `hidden_interactions / capabilities / action_contracts` 中显式落地

## 页面快速校对索引

| page_id | page_name | boundary | route_or_entry | parent_page | capability_count | 含隐藏交互 |
|---------|-----------|----------|----------------|-------------|------------------|------------|
| `dialog-profile.detail` | 对话方案详情 | `sub-page` | `detail.html` | `dialog-profile.index` | 8 | 是 |
| `dialog-profile.index` | 对话方案管理 | `main-page` | `index.html` | `dialog-profile.detail` | 7 | 是 |
| `dialog-profile.test-chat` | 手动测试 | `sub-page` | `test-chat.html` | `dialog-profile.detail` | 2 | 是 |

## 页面级高风险校对

### dialog-profile.detail

- [ ] `page_boundary` / `parent_page` 正确，未把跨模块跳转误记为当前模块父子页
- [ ] `hidden_interactions` 分类准确；若本页含 Drawer / Modal / Tabs / Collapse 中的真实产品能力，未被误标为 `instructional`
- [ ] `capabilities` 粒度正确：没有关键能力遗漏，也没有把多个能力错误合并
- [ ] `action_contracts` 的 `success_signal` 可用于验收，不是 toast、前端本地状态或静态 mock 假成功
- [ ] 若本页 `business_rules / exception_flows` 明显缺失，已直接回写到 `ai-dialog-profile.md`

### dialog-profile.index

- [ ] `page_boundary` / `parent_page` 正确，未把跨模块跳转误记为当前模块父子页
- [ ] `hidden_interactions` 分类准确；若本页含 Drawer / Modal / Tabs / Collapse 中的真实产品能力，未被误标为 `instructional`
- [ ] `capabilities` 粒度正确：没有关键能力遗漏，也没有把多个能力错误合并
- [ ] `action_contracts` 的 `success_signal` 可用于验收，不是 toast、前端本地状态或静态 mock 假成功
- [ ] 若本页 `business_rules / exception_flows` 明显缺失，已直接回写到 `ai-dialog-profile.md`

### dialog-profile.test-chat

- [ ] `page_boundary` / `parent_page` 正确，未把跨模块跳转误记为当前模块父子页
- [ ] `hidden_interactions` 分类准确；若本页含 Drawer / Modal / Tabs / Collapse 中的真实产品能力，未被误标为 `instructional`
- [ ] `capabilities` 粒度正确：没有关键能力遗漏，也没有把多个能力错误合并
- [ ] `action_contracts` 的 `success_signal` 可用于验收，不是 toast、前端本地状态或静态 mock 假成功
- [ ] 若本页 `business_rules / exception_flows` 明显缺失，已直接回写到 `ai-dialog-profile.md`

