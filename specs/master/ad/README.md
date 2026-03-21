---
version: 2.0
updated: 2026-03-18
based_on:
  - spec.md@v1.4
  - pd-index.md (全部 6 模块已完成)
  - pd-all/ (v1.0~v3.3)
  - constitution.md@v1.3.0
  - ad-template.md@v2.2
changelog: |
  2.0: 基于全部 PD 重构为 ad/ 文件夹结构; 补齐知识库/对话方案/监控/批量测试/用户管理 5 个模块的数据流与 API 契约; 更新追溯矩阵至全量覆盖
  1.1: 指令库域补充测试流程; LLM超时改8s; 数据集/意图/词槽/实体完整API; 新增§5.5小模型训练推理架构; 追溯矩阵细化
  1.0: 初始版本 (领域划分、模块结构、3条数据流、接口契约、技术选型、追溯矩阵)
---

# 架构设计 (AD) 索引

> SmartChef 智能对话管理平台 — 架构设计文档集
>
> 按 `ad-template.md` v2.2 §7.1 拆分规则（> 3 模块），采用文件夹结构组织。

## 文档索引

| 文档 | 覆盖范围 | 覆盖 FR | 状态 |
|------|---------|---------|------|
| [ad-global.md](ad-global.md) | 全局架构（领域划分 / 模块关系 / 通信方式 / 技术选型 / 部署 / 安全 / 横切关注点 / 追溯矩阵） | 全部 | ✅ |
| [ad-intent-library.md](ad-intent-library.md) | 指令库域（模型生命周期 / 测试流程 / 完整 API 契约 / ML 训练推理架构） | FR-002,003,039~054 | ✅ |
| [ad-dialog-profile.md](ad-dialog-profile.md) | 对话方案域（方案 CRUD / 指令库绑定 / 人设配置 / 手动测试 / 版本发布） | FR-007~011,015~016,040,047 | ✅ |
| [ad-knowledge-base.md](ad-knowledge-base.md) | 知识库域（文档上传解析 / 分类管理 / 向量索引 / 语义检索） | FR-004~006 | ✅ |
| [ad-monitoring.md](ad-monitoring.md) | 监控域（实时仪表盘 / 设备日志 / 会话链路 / 告警规则） | FR-030~035,038 | ✅ |
| [ad-batch-test.md](ad-batch-test.md) | 测试域（批量测试 / 用例生成 / 智能分析 / 对话方案级测试） | FR-012~014 | ✅ |
| [ad-user-mgmt.md](ad-user-mgmt.md) | 用户认证域（角色权限 / 用户 CRUD / RBAC 能力点） | FR-001 | ✅ |

## 跨文档依赖关系

```
ad-global.md (全局架构)
  ├── 对话推理数据流 → 引用 ad-intent-library (模型推理)
  ├── 版本发布数据流 → 引用 ad-dialog-profile (发布门禁)
  └── 追溯矩阵 → 聚合所有模块覆盖状态

ad-intent-library.md
  ├── 模型生命周期 → 被 ad-dialog-profile 引用 (FR-047 发布门禁)
  └── 测试流程 → 被 ad-batch-test 引用 (FR-051 测试入口)

ad-dialog-profile.md
  ├── 指令库绑定 → 引用 ad-intent-library (FR-040)
  ├── 发布门禁 → 引用 ad-intent-library (FR-047)
  └── 手动测试 → 引用 ad-global (对话推理流程)

ad-batch-test.md
  └── 批量执行 → 引用 ad-global (对话推理管道)

ad-monitoring.md
  └── 请求日志写入 → 引用 ad-global (横切关注点 §6.2)
```

## 阅读顺序建议

1. **ad-global.md** — 先了解全局架构和模块关系
2. **ad-intent-library.md** — 核心域，最复杂的模块
3. **ad-dialog-profile.md** — 核心链路，连接指令库和测试
4. 其他模块按需阅读

---

**基于 spec.md**: v1.4
**基于 pd-template.md**: v4.3
**基于 ad-template.md**: v2.2
**创建时间**: 2026-03-18
