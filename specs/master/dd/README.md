# 详细设计 (DD) 索引

| 文档 | 覆盖范围 | 覆盖 FR | 实体数 | 状态 |
|------|---------|---------|--------|------|
| `dd-global.md` | 全局共享实体、错误码、权限模型、配置与种子策略 | FR-001 及后续模块共享约束 | 4 | ✅ |
| `dd-user-mgmt.md` | 用户管理模块内部实现、状态机、算法与 UI 规格 | FR-001 | 4 | ✅ |
| `dd-intent-library.md` | 指令库实体、模型状态机、阈值快照、验证集和页面行为 | FR-002, FR-003, FR-039~FR-054 | 4 | ✅ |
| `dd-knowledge-base.md` | 知识分类、文档状态机、字段过滤、检索验证与 UI 规格 | FR-004, FR-005, FR-006 | 3 | ✅ |
| `dd-dialog-profile.md` | 对话方案实体、发布门禁、测试会话、调试 trace 与 UI 规格 | FR-007~011, FR-015~016, FR-040, FR-047 | 4 | ✅ |
| `dd-batch-test.md` | 批量测试批次、用例、结果、分析报告与 UI 规格 | FR-012, FR-013, FR-014 | 4 | ✅ |
| `dd-monitoring.md` | 请求日志、监控快照、告警规则/事件与监控页面规格 | FR-030~032, FR-034, FR-035, FR-038 | 4 | ✅ |

## 当前口径

- 正式文档链仅先落 `pd-user-mgmt`
- `pd-intent-library` 已补齐 DD，但仍需沿用 `FR-050 Partial` 条件准入口径
- `pd-knowledge-base` 已补齐 DD，可直接进入任务与实现阶段
- `pd-dialog-profile` 已补齐 DD，可直接进入任务与实现阶段
- `pd-batch-test` 已补齐 DD，可直接进入任务与实现阶段
- `pd-monitoring` 已补齐 DD，可直接进入任务与实现阶段
- 后续模块将在 rollout 顺序推进时继续补充 `dd-<module>.md`
