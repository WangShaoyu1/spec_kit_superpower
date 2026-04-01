# Harness Gates

## 目的

本文件定义 `speckit` 在 `AD / DD / tasks / implement / browser` 阶段的最小机器门禁。

这些 gate 不替代人工判断，但会优先拦住以下问题：

- 输入制品缺失
- 规则引用失效
- PD 存在“部分覆盖/条件准入”但未显式下传
- 计划与任务存在未收口的 `BLOCKER`

## 结果等级

- `BLOCKER`: 不得进入下一阶段
- `WARNING`: 允许继续，但必须显式继承风险
- `INFO`: 仅记录

## 失败码

### 通用

- `GATE-COMMON-001`: `spec.md` 缺失
- `GATE-COMMON-002`: `pd-all/` 缺失
- `GATE-COMMON-003`: `pd-index.md` 缺失
- `GATE-COMMON-004`: 规则文件仍引用已失效文档

### PD 条件准入

- `GATE-PD-001`: PD README 出现“部分覆盖/待补充/待确认”等风险标记，但未提供显式准入声明
- `GATE-PD-002`: 当前存在条件准入模块，下游必须显式继承风险

### DD 阶段

- `GATE-DD-001`: 进入 DD 前缺少 AD 产物

### 模块主控

- `GATE-MODULE-001`: 目标模块未登记到 `module-rollout.json`
- `GATE-MODULE-002`: 目标模块未登记到 `module-state.json`
- `GATE-MODULE-003`: 目标模块缺少 `README.md`、HTML 原型，或未登记到 `pd-index.md`
- `GATE-MODULE-004`: 目标模块依赖模块尚未达到 `browser_verified / done`
- `GATE-MODULE-005`: 已有其他模块占用 `implement` 资源锁

### Tasks 阶段

- `GATE-TASKS-001`: 当前模块 plan 未显式定义核心业务链路或真实成功信号
- `GATE-TASKS-002`: PD 条件准入/部分覆盖未在当前模块 plan 中显式继承

### Implement 阶段

- `GATE-IMPL-001`: 缺少 `tasks/` 或 `tasks.md`
- `GATE-IMPL-002`: 当前模块 plan 或 `tasks/` 中仍存在未处理 `BLOCKER`
- `GATE-IMPL-003`: 当前模块 plan 或 `tasks/` 中仍存在显式未完成声明，继续实现前必须确认风险范围

### Browser 阶段

- `GATE-BROWSER-001`: 目标模块未指定或当前状态不允许进入 browser 阶段
- `GATE-BROWSER-002`: 目标模块缺少 `ui_smoke / business_e2e / quality_probes` 配置
- `GATE-BROWSER-003`: 重点模块缺少性能/准确率探针

## 响应规则

### AD

- 必须通过通用 gate
- 如果存在条件准入模块，可以继续，但必须带 `WARNING`

### DD

- 必须通过通用 gate
- 必须已有 AD 产物

### Tasks

- 必须通过通用 gate
- 必须已有 AD / DD / plan
- 必须确认条件准入或部分覆盖已被当前模块 plan 继承

### Implement

- 必须通过通用 gate
- 必须已有 AD / DD / plan / tasks
- 若存在 `BLOCKER`，直接停止
- 若存在 `Stub / Deferred / Out of Scope / Blocked By`，只能在显式风险接受前提下继续

### Browser

- 必须通过通用 gate
- 必须指定目标模块
- 目标模块必须处于 `implementing`、`browser_verified` 或 `done`
- 依赖模块必须至少达到 `browser_verified`
- 重点模块必须具备性能/准确率探针
