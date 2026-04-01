# 缺陷闭环规范

## 一、目的

本文档只描述**当前仍有效**的缺陷闭环做法。

目标是把缺陷处理收敛为一条统一路径：

**发现 -> 记录 -> 分类 -> 修复 -> 设计回溯 -> 验证闭环**

## 二、当前适用范围

- 缺陷目录：`specs/master/defects/`
- 统一命令：`/speckit.defects`
- 扫描脚本：`python scripts/scan_defects.py`

本文档不再描述历史项目的业务代码路径，也不再依赖旧的 `specs/master/plan.md`、`tasks.md` 单文件结构。

## 三、核心流程

### 1. 记录缺陷

新增缺陷时：

1. 复制 `specs/master/defects/_template.md`
2. 重命名为 `D0xx.md`
3. 按模板填写现象、期望、复现步骤、当前状态
4. 若有截图，放入 `specs/master/defects/images/`

### 2. 扫描与索引

执行：

```bash
python scripts/scan_defects.py
```

作用：

- 校验缺陷 frontmatter 是否完整
- 刷新 `specs/master/defects/INDEX.md`
- 输出状态、分类和待处理项

如需自动写回可关联字段：

```bash
python scripts/scan_defects.py --auto
```

### 3. 分类路由

缺陷处理不只分“修代码”，而是分三类：

- **代码修复**：问题已知，直接修实现
- **设计补充**：问题根因在设计链，需回到 `/speckit.design-pd`、`/speckit.design-ad`、`/speckit.design-dd`
- **需求回溯**：问题本质是需求边界变化，需回到 `/speckit.specify`

### 4. 修复时必须做的事

处理缺陷时，必须同时完成：

1. 修业务问题本身
2. 判断它本应被哪个阶段拦住
3. 必要时回改规则、模板、命令或设计文档
4. 补验证证据

### 5. 验证闭环

缺陷修复后，至少要完成：

- 回归验证
- 相关测试通过
- 状态从“修复完成/待确认”推进到最终状态

没有验证，不得把缺陷当作已闭环。

## 四、缺陷文件最小约定

缺陷文件采用：

- Markdown 正文
- YAML frontmatter

建议最小字段：

| 字段 | 说明 |
|------|------|
| `id` | 缺陷编号，如 `D001` |
| `status` | 当前状态 |
| `category` | 分类，如 UI / 接口 / 业务 / 规范 / 需求 |
| `created` | 创建日期 |
| `fix_ref` | 修复记录（可选） |
| `related` | 关联规范/任务（可选） |
| `design_ref` | 关联设计文档（可选） |
| `should_have_been_caught_by` | 本应拦住该问题的阶段（建议） |

## 五、状态定义

建议使用以下状态：

| 状态 | 含义 |
|------|------|
| 新建 | 已创建，待补充完整信息 |
| 待理解 | 已记录，待分析归因 |
| 已理解 | 已明确根因与处理方向 |
| 修复中 | 正在处理 |
| 修复完成 | 代码或设计已修改，待验证 |
| 待确认 | 等待回归或验收 |
| 重新打开 | 验证失败，重新进入处理 |
| 已确认 | 已完成闭环 |
| 已关闭 | 不再处理 |

## 六、与当前研发体系的关系

缺陷不是旁路流程，而是当前研发体系的一部分。

它必须与以下环节联动：

- `/speckit.specify`
- `/speckit.design-pd`
- `/speckit.design-ad`
- `/speckit.design-dd`
- `/speckit.plan`
- `/speckit.tasks`
- `/speckit.implement`
- `/speckit.review`
- `/speckit.smoke`

缺陷处理的目标不是“补一个洞”，而是尽量让同类问题下次在更早阶段被拦住。

## 七、使用原则

1. `docs/` 中的缺陷说明只保留当前有效做法，不保留历史案例堆叠。
2. 真正执行时，以 `/speckit.defects` 命令和 `scripts/scan_defects.py` 的实际行为为准。
3. 如果缺陷流程未来再次变化，应优先更新命令、规则、脚本，再同步更新本文档。
