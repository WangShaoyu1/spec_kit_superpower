# PD 交互设计索引

> 本文件汇总 `specs/master/` 下所有 PD 交互设计模块的覆盖状态，与 `spec.md` v1.4 的模块映射表保持同步。
> 命名规范参见 `specs/_template/pd-template.md` v4.0 §7.1。

## 模块覆盖状态

| PD 模块 | 目录 | 覆盖 US | 覆盖 FR | 状态 | 页面数 | 版本 |
|---------|------|---------|---------|------|--------|------|
| 指令库管理 | `pd-intent-library/` | US1 | FR-002,003,039-054 | ⚠️ 基线重做中 | 5 | v3.4 |
| 知识库管理 | `pd-knowledge-base/` | US2 | FR-004-006 | ✅ 已完成 | 2 | v1.0 |
| 对话方案 | `pd-dialog-profile/` | US3,US4 | FR-007-011,015-016,040,047 | ✅ 已完成 | 3 | v1.0 |
| 批量测试 | `pd-batch-test/` | US8 | FR-012-014 | ✅ 已完成 | 2 | v1.0 |
| 监控仪表盘 | `pd-monitoring/` | US9 | FR-030-032,034-035,038 | ✅ 已完成 | 3 | v1.0 |
| 用户管理 | `pd-user-mgmt/` | US10 | FR-001 | ✅ 已完成 | 1 | v1.0 |

**状态枚举**：✅ 已完成 / ⚠️ 基线重做中 / 🚧 设计中 / 🔲 待设计 / ⏸️ 暂缓

## 未覆盖 FR（非 UI 类，不需要 PD）

| FR 范围 | 类型 | 说明 | 覆盖文档 |
|---------|------|------|---------|
| FR-017~029 | `[API]` | 对话管理 API、对话路由、技术能力 | AD/DD |
| FR-033 | `[API]` | API 结构化日志 | AD/DD |
| FR-036~037 | `[Infra]` | 安全与隐私 | DD |
| FR-041 | `[API]` | 运行时语言检测 | AD/DD |
| FR-042 | `[Infra]` | 存量迁移 | DD |

## 跨模块引用关系

```
pd-intent-library/
  ├── detail.html → 引用 pd-dialog-profile (FR-047: 方案发布门禁)
  └── test.html   → 引用 pd-batch-test (FR-012~014: 批量测试任务)

pd-dialog-profile/
  ├── detail.html → 引用 pd-intent-library (FR-040: 绑定指令库)
  └── test-chat.html → 手动测试入口 (FR-009~011)
```

## 设计优先级建议

基于 spec.md 用户故事优先级和依赖关系：

1. **pd-intent-library** (US1, P1) — ⚠️ 正在按真实交付链路重做基线
2. **pd-dialog-profile** (US3+US4, P1) — 核心链路，连接指令库和测试
3. **pd-knowledge-base** (US2, P1) — 独立模块，与指令库无强依赖
4. **pd-monitoring** (US9, P2) — 依赖 API 层就绪
5. **pd-user-mgmt** (US10, P2) — 独立模块，可并行设计
6. **pd-batch-test** (US8, P3) — 可后续补充

---

**创建时间**: 2026-03-17
**最后更新**: 2026-03-22
**对应 spec.md 版本**: v1.4
**对应 pd-template.md 版本**: v4.0
