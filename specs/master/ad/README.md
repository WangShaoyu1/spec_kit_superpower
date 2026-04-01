# 架构设计 (AD) 索引

| 文档 | 覆盖范围 | 覆盖 FR | 状态 |
|------|---------|---------|------|
| `ad-global.md` | 正式单体工程骨架、共享鉴权、响应约定、数据存储边界 | FR-001 及后续模块共用约束 | ✅ |
| `ad-user-mgmt.md` | 用户管理模块：账号、角色、能力点、菜单可见性 | FR-001 | ✅ |
| `ad-intent-library.md` | 指令库、数据集、模型训练/评估/发布、下载与测试链路 | FR-002, FR-003, FR-039~FR-054 | ✅ |
| `ad-knowledge-base.md` | 知识分类、文档上传、字段过滤、索引状态与检索验证 | FR-004, FR-005, FR-006 | ✅ |
| `ad-dialog-profile.md` | 对话方案、手动测试、发布门禁、会话隔离与调试 trace | FR-007~011, FR-015~016, FR-040, FR-047 | ✅ |
| `ad-batch-test.md` | 方案级批量测试、执行引擎、报告聚合与分析回读 | FR-012, FR-013, FR-014 | ✅ |
| `ad-monitoring.md` | 监控总览、请求日志筛选、设备会话 trace 与告警规则 | FR-030~032, FR-034, FR-035, FR-038 | ✅ |

## 当前口径

- 正式工程根路径固定为 `backend/ + frontend/`
- `pd-user-mgmt` 是 harness rollout 的首个模块，本文档链仅覆盖 `FR-001`
- `pd-intent-library` 已按条件准入口径补齐 AD，必须持续继承 `FR-050 Partial`
- `pd-knowledge-base` 已补齐 AD，可进入 DD / plan / tasks / implement
- `pd-dialog-profile` 已补齐 AD，可进入实现与测试阶段
- `pd-batch-test` 已补齐 AD，可进入 DD / plan / tasks / implement
- `pd-monitoring` 已补齐 AD，可进入 DD / plan / tasks / implement
- 其他业务模块将在 rollout 顺序推进时继续补齐各自 `ad-<module>.md`
