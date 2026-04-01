# 实施计划索引

## 设计原则

- `plans/plan-<module>.md` 是唯一真实的模块实施计划。
- 根目录 `plan.md` 不再承载单模块详细内容，只作为索引、迁移说明和当前模块入口。
- 每个业务模块各自保留自己的 plan，后续推进新模块时不得覆盖旧模块内容。

## 当前文件

| 文件 | 模块 | 状态 | 说明 |
|------|------|------|------|
| `plan-knowledge-base.md` | `pd-knowledge-base` | 已归档 | 知识库管理模块实施计划 |
| `plan-dialog-profile.md` | `pd-dialog-profile` | 已归档 | 对话方案模块实施计划 |
| `plan-batch-test.md` | `pd-batch-test` | 已归档 | 批量测试模块实施计划 |
| `plan-monitoring.md` | `pd-monitoring` | 当前模块 | 监控仪表盘模块实施计划 |

## 约定

- 文件命名统一为 `plan-<task-slug>.md`
- 例如：
  - `pd-dialog-profile` -> `plan-dialog-profile.md`
  - `pd-batch-test` -> `plan-batch-test.md`
  - `pd-monitoring` -> `plan-monitoring.md`

## 当前模块解析口径

- 自动化脚本优先读取当前 rollout 模块对应的 `plans/plan-<task-slug>.md`
- 若模块化 plan 尚未落地，才允许回退读取旧的根目录 `plan.md`
- 当前仓库已切换到模块化 plan 模式，后续新模块不再使用“覆盖式单文件 plan”
