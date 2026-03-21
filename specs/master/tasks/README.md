# 任务目录索引

> 基于完整设计文档链 (spec.md → PD → AD → DD → plan) 按 PD 模块拆分的可执行任务集。
>
> 设计链路: `spec.md → pd-all/ → ad/ → dd/ → plan.md → tasks/`

## 全局统计

| 维度 | 统计 |
|------|------|
| 任务文件数 | 8 |
| 总任务数 | **218** |
| 基础设施 | 26 |
| PD 模块任务 | 173 (6 模块) |
| 横切/完善 | 19 |
| 覆盖 AD API 端点 | ~139 (全覆盖) |
| 覆盖 DD 实体 | 36+ (全覆盖) |
| 覆盖 PD 页面 | 17 页 (全覆盖) |

## 模块执行顺序

| 顺序 | 模块 | 优先级 | 文件 | 任务数 | 测试 | 后端 | 前端 | 依赖 | 状态 |
|------|------|--------|------|--------|------|------|------|------|------|
| 0 | 基础设施 | 阻塞 | [tasks-infra.md](tasks-infra.md) | 26 | 4 | 17 | 5 | 无 | 🔲 |
| 1 | 指令库管理 | P1 | [tasks-intent-library.md](tasks-intent-library.md) | 41 | 10 | 21 | 10 | infra | ✅ 100% |
| 2 | 知识库管理 | P1 | [tasks-knowledge-base.md](tasks-knowledge-base.md) | 27 | 7 | 14 | 6 | infra | 🔲 |
| 3 | 对话方案 | P1 | [tasks-dialog-profile.md](tasks-dialog-profile.md) | 38 | 9 | 22 | 7 | infra, intent-library(弱) | 🔲 |
| 4 | 批量测试 | P2 | [tasks-batch-test.md](tasks-batch-test.md) | 25 | 6 | 13 | 6 | infra, dialog-profile | 🔲 |
| 5 | 监控仪表盘 | P2 | [tasks-monitoring.md](tasks-monitoring.md) | 27 | 7 | 13 | 7 | infra | 🔲 |
| 6 | 用户管理 | P3 | [tasks-user-mgmt.md](tasks-user-mgmt.md) | 15 | 5 | 5 | 5 | infra (User/Role 已创建) | 🔲 |
| 7 | 横切/完善 | 收尾 | [tasks-refinement.md](tasks-refinement.md) | 19 | 4 | 11 | 4 | 所有模块基本完成 | 🔲 |

**状态枚举**: 🔲 待开始 / 🚧 进行中 / ✅ 已完成 / ⏸️ 暂缓

## 跨模块依赖关系

```
tasks-infra (阶段 0 — 阻塞所有)
  │
  ├── tasks-intent-library (P1) ─────┐
  ├── tasks-knowledge-base (P1) [P] ─┤ (可并行)
  │                                   │
  ├── tasks-dialog-profile (P1) ──────┤ (弱依赖 intent-library: 指令库绑定/发布门禁)
  │   │                               │
  │   └── tasks-batch-test (P2) ──────┤ (依赖 dialog-profile: 测试管道)
  │                                   │
  ├── tasks-monitoring (P2) [P] ──────┤ (可与 P1 模块并行)
  ├── tasks-user-mgmt (P3) [P] ──────┤ (可与其他模块并行)
  │                                   │
  └── tasks-refinement (收尾) ────────┘ (所有模块基本完成后)
```

## 执行策略

### 串行路径（关键链路）

```
infra → intent-library → dialog-profile → batch-test → refinement
```

### 并行窗口

| 窗口 | 可并行模块 | 条件 |
|------|-----------|------|
| W1 | intent-library + knowledge-base + monitoring + user-mgmt | infra 完成后 |
| W2 | dialog-profile + monitoring + user-mgmt | intent-library 完成后 |
| W3 | batch-test + user-mgmt | dialog-profile 完成后 |

### TDD 执行规则

每个模块内部严格遵循:
```
测试(红灯) → 数据模型 → 服务层 → API端点 → 前端页面 → 集成验证(绿灯)
```

### 子代理分派建议

基于 `speckit.implement.md` 子代理策略:
- **后端代理**: 每次处理一个模块的 [B-MODEL] + [B-SERVICE] + [B-API] 任务
- **前端代理**: 每次处理一个模块的 [F-PAGE] + [F-COMPONENT] + [F-STORE] + [F-API] 任务
- **测试代理**: 每次处理一个模块的 [T-CONTRACT] + [T-INTEGRATION] + [T-E2E] 任务
- **并行上限**: 不同文件标记 [P] 的任务可同时分派给不同代理

## 进度追踪

| 模块 | 总数 | 已完成 | 进度 |
|------|------|--------|------|
| 基础设施 | 26 | - | 待核查 |
| 指令库管理 | 41 | 41 | **100%** |
| 知识库管理 | 27 | - | 待核查 |
| 对话方案 | 38 | - | 待核查 |
| 批量测试 | 25 | - | 待核查 |
| 监控仪表盘 | 27 | - | 待核查 |
| 用户管理 | 15 | - | 待核查 |
| 横切/完善 | 19 | - | 待核查 |
| **合计** | **218** | **41+** | **待全量核查** |

## MVP 建议

**最小可行产品范围** (infra + P1 模块):
- tasks-infra.md: 26 任务
- tasks-intent-library.md: 41 任务
- tasks-knowledge-base.md: 27 任务
- tasks-dialog-profile.md: 38 任务
- **MVP 合计: 132 任务**

完成 MVP 后即可进行首轮人工验收 (对照 PD 交互稿 + spec.md)。

---

**创建时间**: 2026-03-18
**基于 spec.md**: v1.4
**基于 plan.md**: v2.0
**基于 tasks-template.md**: v1.0
