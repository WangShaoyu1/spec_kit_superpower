---
description: "按 PD 模块拆分的任务目录模板"
---

# 任务目录结构说明

> 本模板定义 `tasks/` 目录的生成规范。`/speckit.tasks` 命令根据此模板生成一组任务文件。

## 输出结构

```
specs/{branch}/tasks/
├── README.md                    # 索引(模块列表/统计/依赖/策略/进度)
├── tasks-infra.md               # 设置 + 基础设施(阻塞所有模块)
├── tasks-<module-1>.md          # PD 模块 1 的全部任务(测试+后端+前端)
├── tasks-<module-2>.md          # PD 模块 2 的全部任务
├── ...
└── tasks-refinement.md          # 横切关注点 + 完善
```

## 输入来源

**前置条件**: ai-pd/(AI-PD，**首要驱动源**)、pd-all/(HumanPD 视觉参考)、ad/(架构设计)、dd/(详细设计)、模块 plan(阶段规划，含 AI-PD 承接矩阵)、spec.md(优先级参考)

**TDD 强制**: 每个功能模块**必须**包含测试任务，测试先于实现编写。

**组织原则**: 每个 PD 模块生成一个独立的任务文件，模块内按 `测试 → 后端 → 前端 → 检查点` 排列；任务拆分以 AI-PD capability 为主骨架。

**AI-PD 能力下传**:
- `tasks-<module>.md` 不能只按页面名拆任务，必须继承模块 plan 的 `AI-PD 承接矩阵`
- 每个 `[F-PAGE]` 任务至少覆盖：`visible_ui`、`hidden_interactions`、`capabilities`
- 若隐藏交互被标记为 `ui-capability / domain-rule`，必须在任务正文中显式列出，不能写成“说明略”

**证据驱动完成**:
- 任务是否完成, 只能由勾选状态 + 检查点证据决定, 不能靠人工写"100%"或在备注中自认完成
- 任务正文若出现 `未实现`、`UI only`、`待确认`、`placeholder`、`TODO`、`mock`、`stub` 等字样, 该任务不得标记完成, 必须移入显式未完成声明区
- `tasks/README.md` 的模块进度 MUST 由各任务文件的勾选状态自动汇总, 不得手填完成率

## 任务 ID 格式: `[ID] [P] [Type] 描述`
- **[ID]**: 模块内顺序编号(T001、T002...)
- **[P]**: 可以并行运行(不同文件, 无依赖关系)
- **[Type]**: 任务类型标签:
  - `[T-CONTRACT]` 契约测试(覆盖 AD API)
  - `[T-INTEGRATION]` 集成测试(覆盖 AD 数据流)
  - `[T-E2E]` E2E 测试(覆盖 PD 交互路径)
  - `[T-UNIT]` 单元测试(覆盖 DD 算法边界)
  - `[B-MODEL]` 数据模型 + 迁移(来自 DD 实体)
  - `[B-SERVICE]` 服务层/算法(来自 DD 算法)
  - `[B-API]` API 端点(来自 AD 契约)
  - `[B-CONFIG]` 配置/中间件
  - `[F-PAGE]` 前端页面(来自 PD 交互)
  - `[F-COMPONENT]` 可复用组件
  - `[F-STORE]` 状态管理
  - `[F-API]` 前端 API 对接层
- 在描述中包含确切的文件路径和设计文档引用

## 路径约定
- **Web 应用**: `backend/`、`frontend/`
- **单一项目**: `src/`、`tests/`
- 根据模块 plan 项目结构进行调整

---

# 以下为各文件的模板

---

## tasks/README.md 模板

```markdown
# 任务索引: [FEATURE NAME]

**生成时间**: [DATE]
**设计依据**: ai-pd/ + pd-all/ + ad/ + dd/ + plans/
**TDD 模式**: 强制(每个模块包含测试任务, 测试先于实现)
**进度口径**: 由任务勾选状态自动汇总, 显式未完成声明区中的事项会阻止模块被标记为 ✅ 完成

## 模块执行顺序

| 序号 | 文件 | PD 模块 | 优先级 | 任务数 | 依赖 | 状态 |
|------|------|---------|--------|--------|------|------|
| 0 | tasks-infra.md | 基础设施 | - | [N] | 无 | ⬜ |
| 1 | tasks-[module-1].md | [模块名] | P1 | [N] | infra | ⬜ |
| 2 | tasks-[module-2].md | [模块名] | P1 | [N] | infra | ⬜ |
| ... | ... | ... | ... | ... | ... | ... |
| N | tasks-refinement.md | 横切关注点 | - | [N] | 全部模块 | ⬜ |

**状态**: ⬜ 未开始 | 🔄 进行中 | ✅ 完成

## 全局统计

| 维度 | 数量 |
|------|------|
| 任务文件总数 | [N] |
| 任务总数 | [N] |
| 测试任务 | [N] (T-CONTRACT + T-INTEGRATION + T-E2E + T-UNIT) |
| 后端任务 | [N] (B-MODEL + B-SERVICE + B-API + B-CONFIG) |
| 前端任务 | [N] (F-PAGE + F-COMPONENT + F-STORE + F-API) |
| 可并行任务 [P] | [N] |

## 未完成声明汇总

| 模块 | Deferred | Stub | Out of Scope | Blocked By |
|------|----------|------|--------------|------------|
| [module-1] | [无/摘要] | [无/摘要] | [无/摘要] | [无/摘要] |
| [module-2] | [无/摘要] | [无/摘要] | [无/摘要] | [无/摘要] |

## 跨模块依赖关系

- tasks-infra.md → 阻塞所有模块(必须先完成)
- tasks-[module-1].md → 独立(基础完成后即可开始)
- tasks-[module-2].md → 独立(可与模块 1 并行)
- ...
- tasks-refinement.md → 依赖所有模块完成

## 执行策略

### 串行模式(单人)
infra → module-1 → module-2 → ... → refinement

### 并行模式(多 subagent)
infra → [module-1 | module-2 | module-3] → refinement

### MVP 模式
infra → module-1(P1 核心) → 验收

## 全局完成定义（Definition of Done）

- [ ] 所有已纳入范围的任务均已勾选完成
- [ ] 所有 `Deferred / Stub / Out of Scope / Blocked By` 已显式登记, 且未被误算为完成
- [ ] 每个模块至少 1 条核心业务链路有验证证据
- [ ] 前后端消费契约（字段名、分页结构、下载/数组/对象返回）已有对应验证
- [ ] 不存在假成功提示、假进度、假统计、placeholder 页面被计入完成
```

---

## tasks/tasks-infra.md 模板

```markdown
# 基础设施任务

**目的**: 项目初始化 + 阻塞所有 PD 模块的先决条件
**完成标志**: 项目可启动、数据库可连接、认证可用、基础中间件就绪

## Definition of Done

- [ ] 基础设施的真实成功信号已验证（不是仅能启动命令）
- [ ] 阻塞后续模块的共享路径、环境变量、认证方式已经统一
- [ ] 不存在以 mock / placeholder 冒充基础能力的项

## 阶段 1: 设置(项目初始化)

- [ ] T001 [B-CONFIG] 按照模块 plan 项目结构创建目录骨架
- [ ] T002 [B-CONFIG] 初始化后端项目依赖
- [ ] T003 [P] [B-CONFIG] 初始化前端项目依赖
- [ ] T004 [P] [B-CONFIG] 配置代码检查和格式化工具

## 阶段 2: 基础(阻塞先决条件)

### 测试(TDD: 先写测试)

- [ ] T005 [P] [T-CONTRACT] 编写认证 API 契约测试 → ad/ad-user-mgmt.md
- [ ] T006 [P] [T-UNIT] 编写 JWT 生成/验证单元测试 → dd/dd-user-mgmt.md §3

### 后端基础

- [ ] T007 [B-CONFIG] 创建应用入口和配置模块
- [ ] T008 [P] [B-MODEL] 创建数据库连接 + ORM 基类 → dd/dd-global.md §1
- [ ] T009 [P] [B-CONFIG] 创建 Redis 连接模块
- [ ] T010 [P] [B-MODEL] 创建 User/Role 模型 → dd/dd-global.md §1.1
- [ ] T011 [B-SERVICE] 创建认证服务 → dd/dd-user-mgmt.md §3
- [ ] T012 [B-API] 创建认证 API 路由 → ad/ad-user-mgmt.md §3.1
- [ ] T013 [B-CONFIG] 初始化 Alembic 迁移 + 运行首次迁移

### 前端基础

- [ ] T014 [P] [F-PAGE] 创建路由框架和布局组件
- [ ] T015 [P] [F-API] 创建 API 调用基础层(axios + JWT 拦截器)
- [ ] T016 [P] [F-PAGE] 创建登录页面 → pd-all/pd-user-mgmt/
- [ ] T017 [P] [F-STORE] 创建认证状态管理

**检查点**: 基础就绪 — 可登录、JWT 认证工作、数据库/Redis 连接正常
```

---

## tasks/tasks-\<module\>.md 模板（每个 PD 模块一个文件）

```markdown
# [PD 模块名] 任务

**AI-PD 主输入**: ai-pd/ai-<module>.md
**PD 交互原型**: pd-all/pd-<module>/
**架构设计**: ad/ad-<module>.md
**详细设计**: dd/dd-<module>.md
**AI-PD 承接矩阵**: plans/plan-<module>.md §AI-PD 承接矩阵
**优先级**: [P1/P2/P3]
**依赖**: tasks-infra.md 必须先完成

## 模块核心业务链路

<!--
  从对应模块 plan 直接下传. 至少 1 条, 最多建议 3 条.
  每条链路都要对应后续测试和 smoke 验证.
-->

| 链路 | 起点 | 终点/真实成功信号 | 对应任务 |
|------|------|------------------|---------|
| [链路 1] | [入口操作] | [真实数据/状态/结果] | [T00x, T00y] |
| [链路 2（如需要）] | [入口操作] | [真实数据/状态/结果] | [T00x, T00y] |

## 显式未完成声明

- **Deferred**: [如无则写"无"]
- **Stub**: [如无则写"无"; 若存在, 必须返回 501 或显式 NotImplementedError]
- **Out of Scope**: [如无则写"无"]
- **Blocked By**: [如无则写"无"]

## AI-PD 承接矩阵

| 页面 | `visible_ui` | `hidden_interactions` | `capabilities` / 对应任务 | 状态 |
|------|--------------|-----------------------|-----------------------------|------|
| [page-key] | [Table/筛选器/统计卡/按钮] | [`ui-capability` / `domain-rule` ...] | [CAP-xxx -> T00x, T00y] | [未开始/进行中/完成] |

## 测试任务(TDD: 先写测试, 确保红灯)

### 契约测试(覆盖 AD API)

- [ ] T001 [P] [T-CONTRACT] [API名称] 契约测试 → ad/ad-<module>.md §3.x
- [ ] T002 [P] [T-CONTRACT] [API名称] 契约测试 → ad/ad-<module>.md §3.x
...

### 集成测试(覆盖 AD 数据流)

- [ ] T00N [P] [T-INTEGRATION] [流程名称] 集成测试 → ad/ad-<module>.md §2.x
...

### 消费契约 / 状态机测试（防字段错位与假成功）

- [ ] T00N [P] [T-CONTRACT] 验证前端真实请求字段、分页结构、数组/对象返回形态 → ad/ad-<module>.md §3.x
- [ ] T00N [P] [T-INTEGRATION] 验证异步任务状态机（提交中/处理中/成功/失败）→ dd/dd-<module>.md §状态机
- [ ] T00N [P] [T-INTEGRATION] 验证真实成功信号与失败回传，不允许仅以 toast/状态文案判定成功

### E2E 测试(覆盖 PD 交互路径)

- [ ] T00N [P] [T-E2E] [交互场景名称] E2E 测试 → pd-all/pd-<module>/
...

## 后端任务

### 数据模型(来自 DD 实体定义)

- [ ] T00N [P] [B-MODEL] 创建 [实体名] ORM 模型 → dd/dd-<module>.md §1.x
- [ ] T00N [P] [B-MODEL] 创建 [实体名] Pydantic Schema
- [ ] T00N [B-MODEL] 生成 Alembic 迁移并运行
...

### 服务层(来自 DD 算法)

- [ ] T00N [B-SERVICE] 实施 [算法/服务名称] → dd/dd-<module>.md §4.x
- [ ] T00N [T-UNIT] [算法/服务名称] 单元测试(正常 + 异常路径) → dd/dd-<module>.md §4.x
...

### API 端点(来自 AD 接口契约)

- [ ] T00N [B-API] 实施 [HTTP方法] [路径] → ad/ad-<module>.md §3.x
- [ ] T00N [T-CONTRACT] [HTTP方法] [路径] 契约测试(状态码 + 响应结构 + 权限) → ad/ad-<module>.md §3.x
...

## 前端任务

### 页面(来自 PD 交互原型)

- [ ] T00N [F-PAGE] 实施 [页面名称] → pd-all/pd-<module>/（主页面元素 + `functional-hidden-ui` + 成功/失败反馈）
...

### 组件(可复用)

- [ ] T00N [P] [F-COMPONENT] 实施 [组件名称]
...

### 状态管理与 API 对接

- [ ] T00N [F-STORE] 创建 [store名称] 状态管理
- [ ] T00N [F-API] 对接 [API名称] 前后端联调
...

## 检查点

### 模块完成定义（Definition of Done）

- [ ] 任务正文中不存在 `未实现 / UI only / placeholder / TODO / 待确认 / mock / stub` 仍被勾选完成的情况
- [ ] 所有显式未完成项已登记在 `Deferred / Stub / Out of Scope / Blocked By`
- [ ] 每条核心业务链路至少有一组通过的测试或 smoke 证据
- [ ] 前后端消费契约已验证（字段名、分页、下载、数组/对象返回）
- [ ] 没有假成功提示、假进度、假统计、仅更新状态但无真实业务逻辑的实现
- [ ] 所有页面能力清单中的 `functional-hidden-ui` 均已有对应任务与证据，不存在“只做页面骨架”

**模块验收标准**(对照 PD 交互稿):
- [ ] 每个 [B-SERVICE] 都有配套 [T-UNIT] 且通过
- [ ] 每个 [B-API] 都有配套 [T-CONTRACT] 且通过
- [ ] 全量测试通过: `pytest tests/ -v --tb=short` 0 失败
- [ ] Code Review: 召唤 `code-reviewer` 子代理，CRITICAL/MAJOR 已修复
- [ ] [列出 PD 中该模块的关键交互场景验证项]
- [ ] [列出该模块核心业务链路的最终结果验证项]
- [ ] [列出本模块 `functional-hidden-ui` 的能力验证项，如 Drawer/Modal 内 CRUD、导入导出、状态切换]
- [ ] 无回归(先前模块测试仍通过)
```

---

## tasks/tasks-refinement.md 模板

```markdown
# 完善与横切关注点

**目的**: 影响多个模块的改进, 在所有核心模块完成后执行
**依赖**: 所有 PD 模块任务完成

## 安全加固

- [ ] T001 [B-SERVICE] 完善输入校验和 XSS 防护
- [ ] T002 [B-CONFIG] 安全头配置
...

## 性能优化

- [ ] T00N [B-SERVICE] 数据库查询优化
- [ ] T00N [F-COMPONENT] 前端性能优化(懒加载/虚拟列表)
...

## 集成验证

- [ ] T00N [T-E2E] 全系统端到端集成验证(基于 pd-all/ 交互流程)
- [ ] T00N [T-INTEGRATION] 跨模块集成测试

## 文档

- [ ] T00N [B-CONFIG] 更新 README 和部署文档

**最终检查点**: 全系统可交付, 所有测试通过, 对照 PD + spec.md 验收
```

---

## 注意事项

- 每个模块文件的任务编号独立(每个文件从 T001 开始)
- `[P]` 标记的任务可在模块内并行执行
- TDD 是强制的: 测试**必须**在对应实现之前
- 模块间尽量保持独立, 跨模块依赖在 README.md 中声明
- 进度通过 `[X]` 标记追踪, README.md 汇总全局进度
- README.md 的完成百分比和 ✅ 状态必须由勾选状态自动汇总, 不得手工宣称"100% 完成"
- 若某任务或模块存在 `Deferred / Stub / Out of Scope / Blocked By`, 必须显式记录并影响完成判断

## 测试配对规则（MUST 遵守）

> 来源: `.specify/memory/constitution.md` §开发工作流与质量门禁

每个实现任务 MUST 有配套的测试任务，确保测试在任务层面可追踪：

| 实现任务类型 | 必须配套的测试任务 | 说明 |
|-------------|-------------------|------|
| `[B-SERVICE]` 服务层 | `[T-UNIT]` 单元测试 | 覆盖正常+异常路径，mock 数据库 |
| `[B-API]` API 端点 | `[T-CONTRACT]` 契约测试 | 覆盖状态码、响应结构、权限控制 |
| `[B-MODEL]` 数据模型 | `[T-UNIT]` 单元测试 | 覆盖字段约束、默认值、关联关系 |
| `[F-PAGE]` 前端页面 | `[T-E2E]` E2E 测试 | 覆盖页面渲染、关键交互可触发 |

**配对写法**: 测试任务紧跟在对应实现任务后面（同一小节内），而非统一放在文件顶部。
这样在任务派发时，子代理可以同时收到实现任务和对应的测试任务，实现"代码与测试同批次交付"。

**检查点更新**: 模块检查点中增加"每个实现任务都有配套测试任务且已完成"的验证项。
