# Speckit Review - 代码审查

## 目的
对已实现的代码发起**结构化 Code Review**，确保符合项目章程（constitution.md）中的质量门禁要求。

> 来源: `.specify/memory/constitution.md` §开发工作流与质量门禁  
> "所有合并到主分支的代码 MUST 通过至少一人的 Code Review"

## 触发时机

| 时机 | 说明 |
|------|------|
| 模块完成后 | 每个 tasks-\<module\>.md 全部任务完成时，MUST 触发模块级审查 |
| 全部完成后 | 所有模块完成、准备交付时，MUST 触发全量审查 |
| 缺陷修复后 | /speckit.defects 修复完成后，建议触发针对性审查 |
| 主动请求 | 开发者对某段代码不确定时，可主动触发 |

## 使用方式

### 模块级审查
```
/speckit.review [module-name]
```
审查指定模块的所有新增/变更文件。

### 全量审查
```
/speckit.review all
```
审查整个项目的代码质量。

### 针对性审查
```
/speckit.review [file-path-or-description]
```
审查特定文件或特定关注点。

## 执行流程

### 1. 确定审查范围

根据参数确定需要审查的文件范围：
- **模块级**: 读取 `tasks/tasks-<module>.md`，定位该模块涉及的所有源文件
- **全量级**: 扫描 `backend/app/` + `frontend/src/` 全部文件
- **针对性**: 仅审查指定的文件或目录

在进入审查前，MUST 同时收集该范围对应的**验证证据**：
- 已运行的测试结果
- 如涉及前端交互，则包含 smoke / E2E 结果
- 如涉及异步链路，则包含状态机或最终结果验证

若实现方无法提供最基本的验证证据，审查结论必须标记为 `BLOCKED`，不得输出"可交付"结论。

### 2. 召唤 code-reviewer 子代理

创建 `code-reviewer` 类型的子代理，传入以下上下文：

```
审查范围: [文件列表]
项目章程: .specify/memory/constitution.md
架构设计: specs/{branch}/ad/
详细设计: specs/{branch}/dd/
```

### 3. 审查维度

子代理 MUST 按以下维度逐一检查：

| 维度 | 检查内容 | 来源 |
|------|----------|------|
| **安全** | JWT 处理、密码存储、SQL 注入、XSS、RBAC 一致性 | constitution §VII |
| **性能** | N+1 查询、内存泄漏、前端 re-render、bundle size | constitution §技术约束 |
| **错误处理** | 异常传播、错误码一致性、用户友好提示 | dd/ 错误码定义 |
| **测试覆盖** | 是否有配套测试、覆盖率是否达标 | constitution §III |
| **代码规范** | 命名、结构、注释、lint 清洁 | constitution §代码质量 |
| **设计一致性** | 是否符合 AD/DD 定义的接口和数据模型 | ad/ + dd/ |
| **枚举一致性** | DD 定义的枚举值（权限点 key、错误码、状态枚举）与代码中实际使用的值是否**精确匹配** | dd/ 枚举定义 vs 代码 |
| **前端质量** | React memo/useCallback 使用、Ant Design 主题一致性 | 模块 plan 前端规范 |
| **PD 覆盖率** | 前端页面的统计卡、表格列、筛选器、操作按钮是否与 PD 交互稿一致；Placeholder 页面是否存在（排除「说明」Drawer） | pd-all/ 交互稿 |
| **业务链路完整性** | 核心业务流程是否端到端可用（非桩代码），集成测试是否覆盖完整状态转换 | 链路断裂/桩代码未替换 = CRITICAL |
| **验证证据充分性** | 是否有测试 / 构建 / smoke / 状态机结果支撑“完成”声明 | 无证据 = BLOCKED |
| **反假成功** | 是否存在假成功提示、假进度、假统计、仅更新状态但无真实逻辑的实现 | 一经发现至少 MAJOR |

#### 枚举一致性校验（重点说明）

> 来源：D017 根因 — DD 定义 `monitoring_read`，代码使用 `monitor_read`，名称不匹配导致权限校验永远失败。

子代理 MUST 执行以下精确文本比对（不限于此列表，按项目实际扩展）：

| 枚举类型 | DD 定义位置 | 代码使用位置 | 校验方法 |
|----------|-----------|-------------|---------|
| 权限点 key | dd-user-mgmt §5.6 / init_db.py PERMISSIONS | `@require_capability("xxx")` | grep 所有 require_capability 调用，与种子数据 key 列表比对 |
| 错误码 | dd-global §错误码体系 | `BusinessException("Exxxxx", ...)` / `AuthException(...)` | grep 所有异常构造调用，与 DD 错误码表比对 |
| 状态枚举 | dd-\<module\> §状态机 | ORM model `status` 字段的 Enum / CheckConstraint | 比对 DD 状态列表与代码中的枚举值 |

名称不匹配即为 **MAJOR** 级问题。

### 4. 输出格式

审查结果 MUST 使用以下结构化格式：

```markdown
## Code Review 报告

**范围**: [模块名/全量/文件路径]
**审查时间**: [日期]
**评分**: [1-10]

### BLOCKED (证据不足，暂不接受)
- [B1] [文件/模块] 缺少必要验证证据
  - **缺失证据**: ...
  - **需要补充**: ...

### CRITICAL (必须修复，阻断交付)
- [C1] [文件:行号] 问题描述
  - **影响**: ...
  - **建议修复**: ...

### MAJOR (应修复，显著影响质量)
- [M1] [文件:行号] 问题描述
  - **影响**: ...
  - **建议修复**: ...

### MINOR (建议修复，提升质量)
- [m1] [文件:行号] 问题描述

### 亮点 (做得好的地方)
- [P1] ...

### 测试覆盖评估
| 模块 | 单元 | 契约 | 集成 | E2E | 评估 |
|------|------|------|------|-----|------|
| ... | ... | ... | ... | ... | ... |
```

### 5. 问题处置

| 级别 | 处置要求 |
|------|----------|
| **CRITICAL** | MUST 立即修复，修复后重新运行审查确认 |
| **MAJOR** | MUST 在当前迭代内修复，修复后可标记完成 |
| **MINOR** | SHOULD 修复，可纳入下一迭代 backlog |

### 6. 修复验证

对于 CRITICAL 和 MAJOR 问题：
1. 修复代码
2. 运行全量测试确认无回归: `pytest tests/ -v --tb=short`
3. 再次召唤 `code-reviewer` 子代理，仅审查修复部分
4. 确认问题已关闭

## 与其他命令的关系

```
/speckit.implement  →  模块完成  →  /speckit.review [module]  →  标记完成
                    →  全部完成  →  /speckit.review all       →  准备交付
/speckit.defects    →  修复完成  →  /speckit.review [fix]     →  关闭缺陷
```

## 审查记录

审查报告建议保存在 `specs/{branch}/reviews/` 目录下：
```
specs/{branch}/reviews/
├── review-infra.md
├── review-intent-library.md
├── review-final.md
└── ...
```

## 示例

```
用户: /speckit.review intent-library

AI: 读取 tasks/tasks-intent-library.md 确定审查范围...
    涉及文件:
    - backend/app/models/intent_library.py
    - backend/app/services/intent_library_service.py
    - backend/app/api/v1/intent_libraries.py
    - backend/tests/unit/test_intent_library_service.py
    - backend/tests/contract/test_intent_libraries_api.py
    - frontend/src/pages/IntentLibrary/index.jsx
    - frontend/src/stores/intentLibraryStore.js
    
    召唤 code-reviewer 子代理...
    
    [Code Review 报告]
    评分: 8/10
    
    CRITICAL: 0 项
    MAJOR: 2 项
    - [M1] intent_library_service.py:45 — list_libraries 对每个 lib 执行 N+1 子查询
    - [M2] intentLibraryStore.js:43 — createLibrary 后 fetchLibraries 未 await
    MINOR: 3 项
    ...
    
    建议: 修复 2 个 MAJOR 后即可标记模块完成。
```
