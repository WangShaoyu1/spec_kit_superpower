# 语言字段约定 (zh / en 统一)

## 规范

**全项目统一**：语言字段仅使用 `zh`（中文）和 `en`（英文）。与 DD §4.1 一致。

| 场景 | 规范 |
|------|------|
| **存储** | 数据库、API 响应一律为 `zh` 或 `en` |
| **创建入参** | 接受 `zh`/`en`，也接受 `zh-CN`/`en-US` 等 locale，**存储前自动归一化为 zh/en** |
| **列表筛选** | `language=zh` 精确匹配存储为 `zh` 的记录 |
| **前端展示/判断** | 使用 `=== 'zh'` 或 `=== 'en'`，不再使用 `startsWith` |

## 后端

- `intent_library_service.py`：`SUPPORTED_LANGUAGES = {"zh", "en"}`，`LOCALE_TO_LANG` 做入参归一化
- 数据迁移：`65a8134d3ff4` 将已有 `zh-CN`/`en-US` 等标准化为 `zh`/`en`

## 前端

- 表单 value、过滤参数、判断逻辑统一使用 `zh` / `en`
- 统计、表格、详情页均用 `=== 'zh'` / `=== 'en'`

## 新增代码注意

涉及 `language` 时，一律使用 `zh` / `en`，不要引入 `zh-CN`、`en-US` 等 locale 形式到存储和业务逻辑。
