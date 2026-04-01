---
description: 执行 tasks 目录中的任务，按证据门禁完成实现
---

# Speckit Implement - 执行实现

## 目的
按照 `tasks/` 目录中的任务清单，**系统性地执行代码实现**。

## 执行模式
采用**MasterAgent + 子代理工人**模式：
- **MasterAgent（主对话）**: 读取 rollout/state/tasks 索引，选择唯一目标模块，派发任务、验证结果、标记进度
- **子代理（工人）**: 每个工人有独立上下文，只读取所需的模块任务文件和设计文档，完成具体任务

## 执行流程

### 前置检查
1. 运行 `.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequirePlan -RequireDesign -RequireTasks -IncludeTasks`，解析 `FEATURE_DIR` 和 `AVAILABLE_DOCS`
2. 运行 `.specify/scripts/powershell/get-module-rollout.ps1 -Json`，确认当前唯一允许推进的目标模块
3. 紧接着运行 `.specify/scripts/powershell/validate-stage-gates.ps1 -Stage implement -Module <target-module> -Json`
   - 若返回 `status=blocked` 或存在任一 `BLOCKER` 失败码，必须停止并先修上游制品
   - 若返回 `WARNING`，必须先向用户提示当前显式未完成风险，再决定是否继续
4. 后续所有读取与写入都必须以 `FEATURE_DIR` 解析出的绝对路径为准，例如 `FEATURE_DIR/tasks/README.md`、`FEATURE_DIR/checklists/`、`FEATURE_DIR/plans/plan-<module>.md`
5. 确认 `FEATURE_DIR/tasks/README.md` 与模块任务文件存在，且路径使用绝对路径
6. 若 `FEATURE_DIR/checklists/` 存在未完成项，必须先向用户提示当前风险，再决定是否继续
7. 若当前模块 plan 中仍存在未处理的 `BLOCKER` 或影响核心链路的 `Stub / Blocked By`，不得直接宣称进入可交付实现阶段

### 启动实现
```
/speckit.implement
```
`MasterAgent` 读取 `FEATURE_DIR/tasks/README.md` 与 rollout/state，识别当前唯一可执行的模块和任务。

### 断点续传
```
/speckit.implement continue
```
基于各模块任务文件中的 `[X]` 标记与 `module-state.json`，自动识别上次进度，继续执行。

### 任务派发策略
1. **读取索引**: 加载 `FEATURE_DIR/tasks/README.md`，再读取 `module-rollout.json` 与 `module-state.json`
2. **选择模块**: 只选择当前唯一允许推进的模块，并使用 rollout 中的 `task_slug` 打开 `FEATURE_DIR/tasks/tasks-<task-slug>.md`
3. **识别就绪任务**: 在模块文件内，找无依赖或依赖已完成的任务
4. **批次规划**: 每批 3-5 个可并行任务（标记为 [P]）
5. **创建子代理**: 为每个任务创建独立 worker，【如果Cursor系统能力支持，子代理使用Codex5.3、Gemini 3.1 pro、auto三种模型】
6. **并行执行**: 只允许同一模块内的 worker 并行，不允许跨模块并行争用服务或浏览器
7. **结果验证**: 检查输出是否符合设计文档和验收标准
8. **浏览器阶段**: 模块任务完成后，立即运行 browser stage，而不是等所有模块完成
9. **标记进度**: 更新对应模块任务文件中的 `[X]` 标记与 `module-state.json`
10. **更新索引**: 更新 `FEATURE_DIR/tasks/README.md` 中的模块进度统计

### 子代理工作流
每个子代理：
1. 读取分配的任务描述（来自具体的 `FEATURE_DIR/tasks/tasks-<task-slug>.md`）
2. 按需读取 `FEATURE_DIR/pd-all/pd-<module>/`、`FEATURE_DIR/ad/ad-<module>.md`、`FEATURE_DIR/dd/dd-<module>.md` 的相关章节
3. 实现代码（TDD: 先确认测试红灯，再实现，最后绿灯）
4. 运行测试
5. 返回结果和摘要

### 质量门禁（MUST 遵守，不可跳过）

> **来源**: `.specify/memory/constitution.md` §开发工作流与质量门禁。
> 本节将 constitution 中的质量要求**转化为可执行步骤**，确保实现过程中不遗漏。

#### A. 测试门禁 — 每个任务完成时

每个子代理交付的代码 MUST 包含与之配套的测试代码，缺少测试视为**未完成**：

| 任务类型 | 必须交付的测试 |
|----------|---------------|
| `[B-MODEL]` 数据模型 | 对应 ORM 模型的单元测试（字段、约束、默认值） |
| `[B-SERVICE]` 服务层 | 服务函数的单元测试（正常 + 异常路径，mock 数据库） |
| `[B-API]` API 端点 | 契约测试（验证 HTTP 状态码、响应结构、权限控制） |
| `[F-PAGE]` 前端页面 | E2E 冒烟测试（页面可渲染、关键交互可触发） |
| `[T-CONTRACT]` 契约测试 | 本身即测试任务 |
| `[T-INTEGRATION]` 集成测试 | 本身即测试任务 |

**执行规则**：
- 子代理 MUST 在实现代码**同一批次**中编写测试，禁止"先写代码、后补测试"
- 子代理 MUST 在交付前运行 `pytest` 并确认通过，将通过截图/输出包含在返回摘要中
- 子代理 MUST 说明该任务的**真实成功信号**是什么，以及已通过哪条证据验证
- 指挥官 MUST 在收到子代理结果后，检查测试是否存在且通过，否则**打回重做**
- 若子代理只能提供"页面存在 / toast 成功 / 状态字段更新"之类弱证据，任务仍视为**未完成**

#### B. 模块检查点 — 每个模块全部任务完成时

指挥官 MUST 依次执行以下验证（缺一不可）：

1. **全量测试通过**: 运行 `pytest tests/ -v --tb=short`，确认 0 失败
2. **枚举一致性校验**: 比对 DD 中定义的枚举值与代码中实际使用的值（防止 D017 类问题）
   - **权限点**: `init_db.py` 的 PERMISSIONS key 列表 vs 代码中 `@require_capability("xxx")` 的参数
   - **错误码**: DD 错误码表 vs 代码中 `BusinessException("Exxxxx", ...)` 的实际值
   - **状态枚举**: DD 状态机定义 vs ORM model 的枚举/约束
   - 不一致即为 **MAJOR**，MUST 修复后才能继续
3. **PD UI 覆盖率校验** [MUST]: 打开对应 PD HTML 交互稿（`specs/{branch}/pd-all/pd-<module>/`），逐项比对：
   - **统计卡**: PD 中定义的统计卡标签 vs 页面实际统计卡（标签名、数值来源）
   - **表格列**: PD 中定义的 Table 列 vs 页面实际列（列名、dataIndex）
   - **筛选器**: PD 中定义的筛选/搜索条件 vs 页面实际筛选器
   - **操作按钮**: PD 中定义的按钮/入口 vs 页面实际按钮
   - **交互方式**: PD 中定义的组件类型（Switch/弹窗/Timeline 等）vs 实际组件
   - **排除项**：「说明」按钮及 Drawer（AD/DD 逻辑参考文档）不纳入覆盖率计算
   - 差异项 MUST 标注为：「有意省略」（附理由，如后端未支持）或「待实现」
   - **覆盖率 < 80% 为 MAJOR 阻塞**，MUST 补齐后才能继续
4. **Placeholder 页面清零**: 检查前端路由表中所有注册的路由组件：
   - 渲染为 `Result`/`Empty`/「Coming soon」等占位内容的组件 → **MUST 实现完整功能或从路由表中移除**
   - Placeholder 的存在视为「未完成」，**不得通过模块检查点**
   - 若功能确需延期，MUST 从路由表移除该路由，并在 tasks 中标记为 P2/P3 延期
5. **业务链路验证** [MUST — 最高优先级检查点]:
   - 每个模块 MUST 定义"核心业务链路"（PD 交互稿中的主流程）
   - 核心链路的每一步 MUST 有对应的集成测试，且测试 MUST 验证状态转换的完整性（不只第一步）
   - 指挥官 MUST 明确区分"提交成功"与"业务成功"；只有最终真实结果可见，才算链路通过
   - **桩代码（stub）识别与管控**:
     - 任何函数如果只做了 DB 状态更新而未执行真实业务逻辑（如训练、推理、评估），视为"桩代码"
     - 桩代码 MUST 抛出 `NotImplementedError(f"任务 {task_id}: {描述} 尚未实现")` 或返回 HTTP 501
     - 桩代码 MUST 注册到 `specs/{branch}/stubs-registry.md`
     - **桩代码存在时，该模块不得通过检查点**
   - **前端对接桩 API 的处理**:
     - 前端调用返回 501 的 API 时，MUST 显示 "功能开发中" 提示而非假装正常
     - 前端不得隐藏桩 API 对应的 UI 入口（否则用户无法发现缺失）
   - **反假成功检查**:
     - 前端未真正调用 API 时，禁止提示"成功"
     - 硬编码统计、硬编码进度分母、mock 结果冒充真实结果，均视为失败
     - 异步任务如无状态查询和失败原因回传，不得视为完成
   - **垂直切片强制**:
     - 一个功能的后端服务 + API + 前端 + 测试 MUST 在同一切片中完成
     - 不允许"先铺完所有 API 桩再回头补逻辑"的水平推进策略
     - 每个切片完成时 MUST 运行该切片的集成测试并通过
6. **模块级 browser stage** [MUST]:
   - 先运行 `.specify/scripts/powershell/validate-stage-gates.ps1 -Stage browser -Module <target-module> -Json`
   - 再执行 `/speckit.smoke <target-module>`，完成 `UI smoke + business e2e + quality probes`
   - 重点模块必须额外检查性能与准确率信号
   - 未通过 browser stage 的模块不得标记为完成
7. **代码审查**: 召唤 `code-reviewer` 子代理，对本模块代码进行审查
   - 审查范围: 本模块所有新增/变更的文件
   - 审查标准: 安全、性能、错误处理、代码规范、设计一致性、**枚举一致性**
   - 审查输出: 结构化报告（CRITICAL / MAJOR / MINOR 分级）
   - **CRITICAL / MAJOR 问题 MUST 修复后才能标记模块完成**
8. **设计符合性**: 对照 PD 交互稿 + DD 数据模型 + AD 架构，验证功能正确性
9. **回归测试**: 确认先前模块的测试仍然通过
10. **构建验证**: 后端 `python -c "from app.main import create_app"` + 前端 `npm run build` 均成功

#### C. 全局完成门禁 — 所有模块完成时

1. **覆盖率**: 运行 `pytest --cov=app --cov-report=term-missing`，确认核心模块覆盖率 ≥ 80%
2. **Lint 清洁**: `ruff check app/` 零严重告警 + 前端 `npm run lint` 通过
3. **E2E 回归**: 运行 Playwright `npm run test:e2e`，确认全部通过
4. **README 更新**: 项目 README.md MUST 包含完整的启动说明（前置条件、安装步骤、启动命令、登录信息、测试运行）
5. **最终 Code Review**: 召唤 `code-reviewer` 子代理对全量代码做最终审查
6. **浏览器冒烟验证**: 执行 `/speckit.smoke`（全量模式），在真实浏览器中逐页验证
   - 启动后端 + 前端开发服务器
   - 登录系统，遍历所有页面
   - **9 项检查**（与 `/speckit.smoke` Phase 2 一致）: 可达性、控制台、数据渲染、布局、关键交互、性能感知、权限、PD 符合性、**业务链路冒烟**
   - 发现的**严重**问题 MUST 修复后才能标记全局完成
   - 详细流程参见 `/speckit.smoke` 命令

### 检查点验证（总结）
每个模块完成后，指挥官验证：
- [ ] 该模块所有任务标记为完成
- [ ] 每个任务都有配套测试且通过
- [ ] 每个任务都能提供完成证据（测试输出 / 构建输出 / review 结论 / smoke 结果）
- [ ] `validate-stage-gates.ps1 -Stage browser -Module <target-module>` 已通过
- [ ] `/speckit.smoke <target-module>` 已完成，模块状态已推进到 `browser_verified`
- [ ] 全量测试通过（单元 + 契约 + 集成 + E2E）
- [ ] Code Review 完成，CRITICAL/MAJOR 问题已修复
- [ ] 代码符合 DD 定义的数据模型和接口契约
- [ ] 对照 PD 交互稿验证功能正确性
- [ ] PD UI 覆盖率 ≥ 80%（统计卡、表格列、筛选器、操作按钮逐项比对）
- [ ] 无 Placeholder 页面（所有注册路由均渲染完整功能）
- [ ] 无假成功提示、假进度、假统计、仅更新状态但无真实业务逻辑的实现
- [ ] 无回归问题（先前模块的测试仍然通过）

## 验收标准

任务完成必须满足：
1. **测试通过**: 所有测试用例通过（TDD 保障），覆盖率 ≥ 80%
2. **Code Review**: 经过 `code-reviewer` 子代理审查，无 CRITICAL/MAJOR 未修复项
3. **交互符合**: 符合 pd-all/ 的状态矩阵和交互规范
4. **PD 覆盖率**: 每个模块的前端 UI 与 PD 交互稿覆盖率 ≥ 80%，无 Placeholder 页面
5. **架构对齐**: 符合 ad/ 的模块设计和数据流
6. **细节精确**: 符合 dd/ 的数据模型、状态机、错误码
7. **功能正确**: 符合 spec.md 的验收场景
8. **可启动**: README.md 完整，新开发者可按文档 5 分钟内启动项目
9. **浏览器冒烟**: `/speckit.smoke` 全量验证通过，无严重 UI 渲染/交互问题
10. **业务链路闭环**: 模块的核心业务链路（从创建到最终使用）在集成测试中可完整走通，无桩代码

## 中断与恢复
- 可随时中断，进度保存在各模块任务文件的 `[X]` 标记中
- `tasks/README.md` 汇总全局进度
- 重新启动时自动识别未完成模块和任务
- 支持单任务重试（失败时）

## 示例

```
用户: /speckit.implement

AI: 读取 tasks/README.md...
    当前进度: tasks-infra.md ✅, tasks-intent-library.md 进行中(12/35)

    加载 tasks/tasks-intent-library.md...
    就绪任务: T013(B-API), T014(B-API), T015(F-PAGE)
    创建 3 个子代理并行执行...

    [结果汇总]
    ✓ T013: 意图列表 API 端点完成
    ✓ T014: 意图详情 API 端点完成
    ✓ T015: 意图列表页面完成

    进度: 15/35 (43%)
    更新 tasks/tasks-intent-library.md 进度标记。
    更新 tasks/README.md 全局统计。
```
