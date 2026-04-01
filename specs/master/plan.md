# 实施计划入口索引

## 为什么从单文件改成目录

之前的 `specs/master/plan.md` 采用“当前模块覆盖式”写法，所以每推进一个模块，前一个模块的实施计划就会被新内容替换。这个结构不适合现在的模块级持续研发。

现在改为：

- 根入口：`specs/master/plan.md`
- 模块计划目录：`specs/master/plans/plan-<module>.md`

这样每个模块都会保留独立计划文件，不再覆盖前一模块。

## 当前约定

| 用途 | 路径 |
|------|------|
| 入口索引 | `specs/master/plan.md` |
| 计划目录 | `specs/master/plans/` |
| 当前模块计划 | `specs/master/plans/plan-monitoring.md` |
| 上一模块计划 | `specs/master/plans/plan-batch-test.md` |

## 规则

- 模块计划文件命名统一为 `plan-<task-slug>.md`
- 例如：
  - `pd-dialog-profile` -> `plan-dialog-profile.md`
  - `pd-batch-test` -> `plan-batch-test.md`
  - `pd-monitoring` -> `plan-monitoring.md`
- `tasks-<module>.md` 必须引用对应模块 plan，而不是笼统引用根入口 `plan.md`
- 自动化脚本优先解析当前模块的 `plans/plan-<task-slug>.md`

## 当前已保留的模块计划

- `plans/plan-knowledge-base.md`
- `plans/plan-dialog-profile.md`
- `plans/plan-batch-test.md`

## 下一步口径

- `pd-monitoring` 已切换到 `plans/plan-monitoring.md`
- 根目录 `plan.md` 只保留索引、迁移说明和当前模块入口，不再承载单模块详细实施内容
