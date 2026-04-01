# 任务索引: master / modules

**生成时间**: 2026-03-31  
**设计依据**: `pd-all/ + ad/ + dd/ + plans/`  
**TDD 模式**: 强制  
**进度口径**: 以任务勾选和检查点证据为准

## 模块执行顺序

| 序号 | 文件 | PD 模块 | 优先级 | 任务数 | 依赖 | 状态 |
|------|------|---------|--------|--------|------|------|
| 0 | `tasks-infra.md` | 基础设施 | - | 5 | 无 | ✅ |
| 1 | `tasks-user-mgmt.md` | `pd-user-mgmt` | P1 | 13 | infra | ✅ |
| 2 | `tasks-intent-library.md` | `pd-intent-library` | P1 | 12 | `pd-user-mgmt` | ✅ |
| 3 | `tasks-knowledge-base.md` | `pd-knowledge-base` | P1 | 12 | `pd-intent-library` | ✅ |
| 4 | `tasks-dialog-profile.md` | `pd-dialog-profile` | P1 | 12 | `pd-knowledge-base` | ✅ |
| 5 | `tasks-batch-test.md` | `pd-batch-test` | P1 | 12 | `pd-dialog-profile` | ✅ |
| 6 | `tasks-refinement.md` | 横切关注点 | - | 4 | `tasks-batch-test.md` | ✅ |
| 7 | `tasks-monitoring.md` | `pd-monitoring` | P2 | 12 | `tasks-refinement.md` | ✅ |

**状态**: ⬜ 未开始 | 🔄 进行中 | ✅ 完成

## 全局统计

| 维度 | 数量 |
|------|------|
| 任务文件总数 | 8 |
| 任务总数 | 82 |
| 测试任务 | 33 |
| 后端任务 | 28 |
| 前端任务 | 21 |
| 可并行任务 `[P]` | 28 |

## 未完成声明汇总

| 模块 | Deferred | Partial | Out of Scope | Blocked By |
|------|----------|---------|--------------|------------|
| `user-mgmt` | 用户自主改密、SSO | 无 | 批量导入导出、自定义角色 | 无 |
| `intent-library` | Excel 解析器、复杂 LLM 提示词 | `FR-050` 继承链路可视化 | 运行时设备侧加载、跨模块绑定细节 | 无 |
| `knowledge-base` | 批量压缩包导入、真正的向量数据库接入 | 无 | 运行时知识路由、对话方案绑定 | 无 |
| `dialog-profile` | 多版本回滚、真实在线 LLM 调用、跨设备版本热更新 | 无 | 生产 API 路由编排、批量测试分析 | 无 |
| `batch-test` | 批量上传压缩包、跨批次趋势对比、真实 LLM 归因分析 | 无 | 生产压测、线上流量回放、监控联动 | 无 |

## 跨模块依赖关系

- `tasks-infra.md` 已完成，为正式骨架提供基础设施
- `tasks-user-mgmt.md` 已完成，为所有后续模块提供 capability 权限基线
- `tasks-intent-library.md` 已完成，为知识库和对话方案模块提供菜单与模块化后端模式
- `tasks-knowledge-base.md` 已完成，为对话方案模块提供知识库绑定前置能力
- `tasks-dialog-profile.md` 已完成，为批量测试模块提供方案级测试对象与调试基础能力
- `tasks-batch-test.md` 已完成，为后续横切收敛与监控模块提供真实批量验证入口
- `tasks-refinement.md` 已完成，统一了 user-mgmt 横切验证口径并为监控模块启动清场
- `tasks-monitoring.md` 已完成，补齐了运行态观测、会话链路与告警治理闭环

## 执行策略

### 串行模式
infra → user-mgmt → intent-library → knowledge-base → dialog-profile → batch-test → refinement

### 当前模块模式
monitoring → 已完成 browser 验证，等待下一模块

## 全局完成定义

- [ ] 所有纳入范围的任务均已勾选完成
- [ ] 显式未完成声明已登记且未被误算为完成
- [ ] `pd-user-mgmt`、`pd-intent-library`、`pd-knowledge-base`、`pd-dialog-profile` 与 `pd-batch-test` 均有 browser 证据
- [ ] 关键模块性能门槛已冻结并在实现中回读
- [ ] 不存在前端假成功提示或未回读的状态/统计
