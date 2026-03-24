# 实施计划: 指令库管理冲突扫描示例

**分支**: `998-intent-library-conflict-demo` | **日期**: 2026-03-22 | **规范**: [spec.md](./spec.md)
**输入**: 来自 `/specs/998-intent-library-conflict-demo/` 的完整设计文档链

## 摘要

本示例不是为了进入实施，而是为了验证新的 pre-flight 规则能否在 `tasks` 之前拦截文档冲突。

## Pre-flight 一致性扫描

| 检查项 | 结果 (OK/WARNING/BLOCKER) | 结论 / 处理动作 |
|--------|---------------------------|----------------|
| FR 在 spec / AD / DD 中是否存在冲突 | BLOCKER | `spec/dd` 要求空训练集禁止创建模型草稿，但 `ad` 明确允许空训练集继续创建草稿；必须先统一口径 |
| PD 页面是否真实存在且被 AD 正确引用 | BLOCKER | `ad` 引用了 `model-download.html`，但 `pd-all/pd-intent-library/` 中不存在该页面 |
| plan 使用的源码路径是否与当前工程一致 | OK | 本示例未引入路径漂移 |
| PD 是否存在部分覆盖/待补充项 | WARNING | 页面只覆盖列表和详情；但由于已有 BLOCKER，本项不构成继续实施依据 |
| 关键外部依赖/异步链路是否定义真实成功信号 | OK | 本示例不进入异步链路 |

## 结论

**不得继续生成 `tasks/`。**

在新规范下，这个示例应该停在 `plan.md`，先修正以下问题后再进入 `/speckit.tasks`：

1. 统一“空训练集能否创建模型草稿”的规则
2. 删除或补齐 `model-download.html` 的 PD 引用

## 显式未完成声明

- **Deferred**: 无
- **Stub / 需要 501 的能力**: 无
- **Out of Scope**: 实际实施
- **Blocked By**: 上述两个 `BLOCKER`
- **路径单一真相源**: `smartchef-v2/backend` + `smartchef-v2/frontend`
