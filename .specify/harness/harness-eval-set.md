# Harness Eval Set

## 目的

本评估集用于持续验证当前 harness 是否稳定拦截高频问题，并保证 `AD / DD / tasks / implement / browser` 的判断结果可回归、可比较、可扩展。

## 分层

### A. 当前仓库可直接回归

这些用例无需额外 fixture，可直接在当前仓库执行：

| ID | Stage | 目标 | 期望状态 | 期望失败码 |
|----|-------|------|---------|-----------|
| `EVAL-001` | `ad` | 当前 `master` 工作空间进入 AD | `warning` | `GATE-PD-002` |
| `EVAL-002` | `dd` | 当前 `user-mgmt` 试点进入 DD | `warning` | `GATE-PD-002` |
| `EVAL-003` | `tasks` | 当前 `user-mgmt` 试点进入 tasks | `warning` | `GATE-PD-002` |
| `EVAL-004` | `implement` | 当前 `user-mgmt` 试点进入 implement | `warning` | `GATE-PD-002`, `GATE-IMPL-003` |

### B. 需要 fixture / worktree 的标准回归

这些用例代表后续必须自动化的场景：

| ID | Stage | 场景 | 期望状态 | 期望失败码 |
|----|-------|------|---------|-----------|
| `EVAL-005` | `ad` | 缺少 `spec.md` | `blocked` | `GATE-COMMON-001` |
| `EVAL-006` | `ad` | 缺少 `pd-all/` | `blocked` | `GATE-COMMON-002` |
| `EVAL-007` | `ad` | 规则仍引用失效文档 | `blocked` | `GATE-COMMON-004` |
| `EVAL-008` | `ad` | PD README 含“部分覆盖”但无准入声明 | `blocked` | `GATE-PD-001` |
| `EVAL-009` | `dd` | 已有 spec/PD，但缺少 AD | `blocked` | `GATE-DD-001` |
| `EVAL-010` | `tasks` | plan 未定义核心业务链路或真实成功信号 | `blocked` | `GATE-TASKS-001` |
| `EVAL-011` | `tasks` | PD 条件准入未在 plan 下传 | `blocked` | `GATE-TASKS-002` |
| `EVAL-012` | `implement` | 缺少 `tasks/` | `blocked` | `GATE-IMPL-001` |
| `EVAL-013` | `implement` | plan/tasks 中存在真实 `BLOCKER` 行 | `blocked` | `GATE-IMPL-002` |
| `EVAL-014` | `implement` | 只有显式未完成声明，无真实 blocker | `warning` | `GATE-IMPL-003` |
| `EVAL-015` | `implement` | 目标模块同时未登记到 rollout 与 state | `blocked` | `GATE-MODULE-001`, `GATE-MODULE-002` |
| `EVAL-016` | `implement` | 目标模块依赖尚未 `browser_verified` | `blocked` | `GATE-MODULE-004` |
| `EVAL-017` | `browser` | browser 阶段未指定模块或状态错误 | `blocked` | `GATE-BROWSER-001` |
| `EVAL-018` | `browser` | 重点模块仅缺少性能/准确率探针 | `warning` | `GATE-BROWSER-003` |

## 推荐运行频率

- 每次修改 `common.ps1`、`check-prerequisites.ps1`、`validate-stage-gates.ps1` 后：至少执行 `EVAL-001` ~ `EVAL-004`
- 每次修改 gate failure code 或阶段命令后：执行全部 current-workspace 用例，并抽样执行 2-3 个 fixture 用例
- 每次准备扩大到新模块自动生成前：执行全部 18 个用例

## 未来自动化建议

### Phase 1

- 先把 `EVAL-001` ~ `EVAL-004` 做成脚本化回归

### Phase 2

- 为 `EVAL-005` ~ `EVAL-018` 建立独立 fixture worktree
- 每个 fixture 只改变一个变量，避免多因素混杂

### Phase 3

- 记录每次回归输出：`status`、失败码、运行时间、是否与期望一致
- 对 failure code 变更建立基线对比
