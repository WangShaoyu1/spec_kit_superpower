# 任务索引: 指令库管理最小闭环示例

**生成时间**: 2026-03-22
**设计依据**: pd-all/ + ad/ + dd/ + plan.md
**TDD 模式**: 强制(每个模块包含测试任务, 测试先于实现)
**进度口径**: 由任务勾选状态自动汇总, 显式未完成声明区中的事项会阻止模块被标记为 ✅ 完成

## 模块执行顺序

| 序号 | 文件 | PD 模块 | 优先级 | 任务数 | 依赖 | 状态 |
|------|------|---------|--------|--------|------|------|
| 0 | tasks-infra.md | 基础设施 | - | 3 | 无 | ⬜ |
| 1 | tasks-intent-library.md | 指令库管理最小闭环 | P1 | 8 | infra | ⬜ |
| 2 | tasks-refinement.md | 横切关注点 | - | 2 | 全部模块 | ⬜ |

**状态**: ⬜ 未开始 | 🔄 进行中 | ✅ 完成

## 全局统计

| 维度 | 数量 |
|------|------|
| 任务文件总数 | 3 |
| 任务总数 | 13 |
| 测试任务 | 5 |
| 后端任务 | 4 |
| 前端任务 | 2 |
| 可并行任务 [P] | 6 |

## 未完成声明汇总

| 模块 | Deferred | Stub | Out of Scope | Blocked By |
|------|----------|------|--------------|------------|
| intent-library | 训练、评估、testable、发布 | 无 | 下载、批量测试、智能分析 | 无 |

## 跨模块依赖关系

- tasks-infra.md → 阻塞所有模块
- tasks-intent-library.md → 依赖 infra 完成
- tasks-refinement.md → 依赖 intent-library 完成

## 执行策略

### 串行模式(单人)
infra → intent-library → refinement

### MVP 模式
infra → intent-library(P1 核心) → 验收

## 全局完成定义（Definition of Done）

- [ ] 所有已纳入范围的任务均已勾选完成
- [ ] 所有 `Deferred / Stub / Out of Scope / Blocked By` 已显式登记, 且未被误算为完成
- [ ] 每个模块至少 1 条核心业务链路有验证证据
- [ ] 前后端消费契约（字段名、分页结构、下载/数组/对象返回）已有对应验证
- [ ] 不存在假成功提示、假进度、假统计、placeholder 页面被计入完成
