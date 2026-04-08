# AI-PD 生成排期表

## 目标

在 `specs/master/pd-all/` 已完成的 6 个 HumanPD 模块基础上，补齐剩余 4 个模块的 `ai-pd/ai-<module>.md`，形成可被 AI、harness 和下游设计/实施阶段稳定消费的语义主输入层。

## 当前进度

| 模块 | HumanPD | AI-PD | 状态 | 说明 |
|------|---------|-------|------|------|
| `pd-user-mgmt` | 已有 | 已生成 | 完成 | 单页+模态交互试点 |
| `pd-intent-library` | 已有 | 已生成 | 完成 | 多页+隐藏交互复杂试点 |
| `pd-knowledge-base` | 已有 | 已生成 | 完成 | 已按排期第 1 项生成 |
| `pd-dialog-profile` | 已有 | 已生成 | 完成 | 已按排期第 2 项生成 |
| `pd-batch-test` | 已有 | 已生成 | 完成 | 已按排期第 3 项生成 |
| `pd-monitoring` | 已有 | 已生成 | 完成 | 已按排期第 4 项生成 |

## 排期顺序

| 顺序 | 模块 | 页面数 | 复杂度 | 排期理由 | 预期产出 |
|------|------|--------|--------|---------|---------|
| 1 | `pd-knowledge-base` | 2 | 低 | 结构最简单，先验证脚本对双页文档管理模块的泛化能力 | `ai-pd/ai-knowledge-base.md` |
| 2 | `pd-dialog-profile` | 3 | 高 | 核心链路模块，绑定指令库、人设、测试、发布，最值得优先语义化 | `ai-pd/ai-dialog-profile.md` |
| 3 | `pd-batch-test` | 2 | 中 | 依赖 dialog-profile 的语义边界，放在其后更稳 | `ai-pd/ai-batch-test.md` |
| 4 | `pd-monitoring` | 3 | 中 | 相对独立，适合作为本轮 AI-PD 回补收尾模块 | `ai-pd/ai-monitoring.md` |

## 每个模块的完成定义

- 已生成对应 `ai-pd/ai-<module>.md`
- `ai-pd/README.md` 已登记该模块
- 页面索引、`page_id`、`page_boundary`、`primary_user_flows` 完整
- `visible_ui / hidden_interactions / capabilities / action_contracts / data_contracts / business_rules / exception_flows / fr_mapping / out_of_scope` 结构完整
- 不出现跨模块语义串台
- 输出可通过现有 `transform_pd.py` 测试与 gate 兼容检查

## 风险提示

- 当前部分 PD README 只有需求追溯矩阵，没有 `intent-library` 那样细粒度的页面语义块，因此某些模块生成结果会更偏 scaffold，需要后续人工精修
- `dialog-profile` 与 `batch-test` 存在跨模块引用，生成时要特别检查页面边界和 FR 归属，避免把跨模块能力错误内联
- `monitoring` 偏运行态观测，若 README 未明确异常流或动作契约，脚本会保守生成默认项

## 本轮交付结果

- 已完成 `knowledge-base / dialog-profile / batch-test / monitoring` 4 个剩余模块的 `AI-PD` 生成
- `specs/master/ai-pd/README.md` 已更新为 6 个模块全量索引
- `transform_pd.py` 已补强 3 类能力：`FR` 覆盖范围提纯、导航父子页识别收敛、常见模块动作能力扩展
- `backend/tests/test_transform_pd.py` 已新增剩余模块回归校验，当前回归通过

## 当前结论

- `HumanPD`: 6 / 6
- `AI-PD`: 6 / 6
- 当前 `master` 分支已具备“剩余模块继续按同一脚本批量生成 AI-PD”的基础能力
