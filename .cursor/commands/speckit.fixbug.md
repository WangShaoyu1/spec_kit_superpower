---
description: 已合并到 /speckit.defects，请使用 /speckit.defects 代替本命令。
---

> **⚠️ 此命令已废弃，功能已合并到 `/speckit.defects`**
>
> 请改用：
> ```
> /speckit.defects 新增了缺陷 D0xx.md，请解决
> ```
>
> `/speckit.defects` 现在覆盖缺陷全生命周期：
> 扫描发现 → 分类路由 → 根因分析 → 修复实施 → 设计回溯 → 验证闭环

**如果用户仍使用了 `/speckit.fixbug`，请自动转发到 `/speckit.defects` 的修复流程（Phase 3-6）执行。**

## 用户输入

```text
$ARGUMENTS
```

**自动转发**: 读取 `/speckit.defects` 命令文件，从 Phase 3（根因分析与定位）开始执行。
