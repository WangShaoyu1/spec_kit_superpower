# MasterAgent Runbook

## 目标

把 `pd-all` 的模块级研发从“按感觉推进”变成“有状态、有顺序、有资源锁”的单主控执行流。

## 唯一真相源

- 模块顺序与依赖：`./module-rollout.json`
- 模块当前状态：`./module-state.json`
- 阶段门禁：`./harness-gates.md`

## 状态机

模块状态只允许按以下顺序推进：

`not_started -> ad_ready -> dd_ready -> tasks_ready -> implementing -> browser_verified -> done`

含义：

- `not_started`: 仅有 PD/spec，未进入正式研发链
- `ad_ready`: AD 已完成并通过 gate
- `dd_ready`: DD 已完成并通过 gate
- `tasks_ready`: tasks 已完成并通过 gate
- `implementing`: 正在执行真实实现与测试
- `browser_verified`: 已完成模块级浏览器验证
- `done`: 模块关闭，允许下游模块依赖

## 主控规则

- 同一时间只允许一个模块处于 `implementing`
- 同一时间只允许一个浏览器验证任务占用真实浏览器
- 模块进入 `implementing` 前，其 `depends_on` 模块必须至少达到 `browser_verified`
- `critical=true` 的模块必须在浏览器阶段额外检查性能与准确率信号

## MasterAgent 职责

1. 读取 `module-rollout.json` 与 `module-state.json`
2. 选择当前唯一允许推进的模块
3. 从目标模块的 `task_slug` 推导 `tasks/tasks-<task_slug>.md`
4. 按 `ad -> dd -> tasks -> implement -> browser` 顺序触发 gate
5. 在每一阶段完成后更新模块状态
6. 发现超出自动修复边界的问题时暂停并请求人工确认

## 子 Agent 职责

- `ADAgent`: 仅负责目标模块 AD
- `DDAgent`: 仅负责目标模块 DD
- `TaskAgent`: 仅负责目标模块 tasks
- `ImplementAgent`: 仅负责当前切片实现与测试
- `BrowserTestAgent`: 仅负责当前模块浏览器验证
- `ReviewerAgent`: 仅负责模块级或全量 review

## 资源锁

资源上限来自 `module-rollout.json`：

- `frontend_dev_server = 1`
- `backend_dev_server = 1`
- `browser_sessions = 1`
- `module_in_implement = 1`

任何子 Agent 发现资源锁冲突，必须停止启动新服务或新浏览器任务，并交还控制权给 `MasterAgent`。

## 操作脚本

- 读取顺序与状态：`.specify/scripts/powershell/get-module-rollout.ps1`
- 更新模块状态：`.specify/scripts/powershell/update-module-state.ps1`
- 执行阶段 gate：`.specify/scripts/powershell/validate-stage-gates.ps1`
- 本地栈编排入口：`.specify/scripts/powershell/start-rollout-stack.ps1`

## 正式 rollout 口径

当前正式顺序固定为：

1. `pd-user-mgmt`
2. `pd-intent-library`
3. `pd-knowledge-base`
4. `pd-dialog-profile`
5. `pd-batch-test`
6. `pd-monitoring`

除 `allow_parallel_design=true` 的模块外，不允许越序推进到实现阶段。
