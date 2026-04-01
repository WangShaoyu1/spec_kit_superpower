# Defect Loop

## 目标

让 harness 对失败结果进行统一分流，优先自动处理“可稳定复现、根因明确、局部可修复”的问题。

## 固定循环

`实现/验证 -> 收集失败 -> 分类 -> 自动修复或停止 -> 重跑验证 -> 记录结果`

## 失败分类

| 类型 | 判断依据 | 默认回流位置 |
|------|----------|--------------|
| `contract_failure` | 接口结构、字段、错误码与 AD/DD 不一致 | `AD/DD -> tasks -> implement` |
| `ui_mismatch` | 页面交互、字段、状态与 PD 不一致 | `PD/前端实现` |
| `logic_failure` | 业务规则、状态机、权限、算法失败 | `DD/服务实现` |
| `performance_failure` | 响应时间、准确率、重复请求等未达标 | `实现/索引/缓存/评估` |
| `env_failure` | 端口冲突、服务未启动、数据库未就绪 | `MasterAgent` 编排层 |

## 自动修复边界

只有满足以下条件才允许自动修复：

- 失败可以稳定复现
- 根因已经定位到单模块、单链路
- 修复不需要跨模块重构
- 修复后存在可立即重跑的验证命令

## 必须停止并请求人工确认的情况

- 涉及 `spec / PD / AD / DD` 的口径冲突
- 涉及多个模块的共享接口或数据模型重构
- 失败原因不稳定或不可复现
- 关键模块的性能/准确率指标需要重新定义

## 缺陷记录口径

每次失败至少记录：

- 来源阶段：`ad / dd / tasks / implement / browser`
- 模块
- 失败类型
- 根因摘要
- 是否进入自动修复
- 重跑结果

## 推荐脚本

- 阶段 gate：`.specify/scripts/powershell/validate-stage-gates.ps1`
- 失败分流：`.specify/scripts/powershell/classify-harness-failure.ps1`
