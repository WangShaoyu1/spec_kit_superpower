---
version: 2.0
updated: 2026-03-18
based_on:
  - spec.md@v1.4
  - ad/ (全部 7 文档, v2.0)
  - pd-all/ (全部 6 PD 模块)
  - dd-template.md@v2.3
changelog: |
  2.0: 基于全量 AD(6模块)+PD 重构为 dd/ 文件夹结构; 7 个文档覆盖全部 FR
---

# 详细设计 (DD) 索引

> SmartChef 智能对话管理平台 — 详细设计文档集
>
> 按 `dd-template.md` v2.3 §1.3 拆分规则（> 3 模块），采用文件夹结构组织。

## 文档索引

| 文档 | 覆盖范围 | 覆盖 FR | 实体数 | 状态 |
|------|---------|---------|--------|------|
| [dd-global.md](dd-global.md) | 全局 (公共实体/错误码/权限/配置/种子数据) | 全部 | 6 | ✅ |
| [dd-intent-library.md](dd-intent-library.md) | 指令库域 (模型生命周期/训练推理/测试) | FR-002,003,025,039~054 | 12 | ✅ |
| [dd-dialog-profile.md](dd-dialog-profile.md) | 对话方案域 (方案配置/人设/手动测试/版本发布) | FR-007~011,015~016,040,047 | 5 | ✅ |
| [dd-knowledge-base.md](dd-knowledge-base.md) | 知识库域 (文档管理/向量索引/语义检索) | FR-004~006,021 | 3 | ✅ |
| [dd-monitoring.md](dd-monitoring.md) | 监控域 (实时仪表盘/设备日志/告警规则) | FR-030~035,038 | 3 | ✅ |
| [dd-batch-test.md](dd-batch-test.md) | 测试域 (批量测试/用例管理/智能分析) | FR-012~014,051~052 | 4 | ✅ |
| [dd-user-mgmt.md](dd-user-mgmt.md) | 用户认证域 (登录/JWT/RBAC/角色管理) | FR-001,053 | 3 (+Redis) | ✅ |

**总计**: 7 个文档, ~8,900 行, 36+ 实体, 54 个 FR 全覆盖

## 全局统计

| 维度 | 统计 |
|------|------|
| PostgreSQL 实体 | 28+ (含关联表/分区表) |
| Redis 实体 | 4 (DeviceSession, TokenBlacklist, LoginAttempt, DashboardCache) |
| 状态机 | 6 (ModelVersion, Document, BatchTest, TestRun, AlertEvent, User) |
| 核心算法 | 25+ (含伪代码 + 边界条件) |
| 错误码 | 120+ (6 模块 × 子模块, E10xxx~E60xxx) |
| API 端点映射 | 130+ (覆盖全部 AD 定义的 API) |
| 能力点 | 21 (完整 RBAC 映射) |
| 业务常量 | 60+ |

## 跨文档依赖关系

```
dd-global.md (基础设施)
  ├── User/Role/Permission 实体 → 被全部模块引用 (权限校验)
  ├── PublishedVersion 实体 → 被 dd-dialog-profile 引用 (版本发布)
  ├── DeviceSession 实体 → 被 dd-monitoring 引用 (会话追踪)
  ├── 错误码格式 → 被全部模块遵循 (E{module}{sub}{seq})
  └── 能力点清单 → 被全部模块引用 (RBAC)

dd-intent-library.md (核心域)
  ├── IntentLibrary 实体 → 被 dd-dialog-profile 引用 (指令库绑定)
  ├── LibraryModelVersion 实体 → 被 dd-dialog-profile 引用 (发布门禁)
  └── 分类推理算法 → 被 dd-batch-test 引用 (批量执行)

dd-dialog-profile.md (核心域)
  ├── DialogProfile 实体 → 被 dd-batch-test 引用 (测试集归属)
  └── 发布门禁算法 → 引用 dd-intent-library (模型状态校验)

dd-batch-test.md
  └── 批量执行算法 → 引用 dd-intent-library (推理管道)

dd-monitoring.md
  └── RequestLog 实体 → 源自 dd-global 横切关注点 (异步日志写入)
```

## 阅读顺序建议

1. **dd-global.md** — 先了解公共实体、错误码体系和权限模型
2. **dd-intent-library.md** — 核心域，最复杂的模块 (12 实体 + 状态机 + 训练推理)
3. **dd-dialog-profile.md** — 核心链路，连接指令库和版本发布
4. 其他模块按需阅读

---

**基于 spec.md**: v1.4
**基于 ad-template.md**: v2.2
**基于 dd-template.md**: v2.3
**创建时间**: 2026-03-18
