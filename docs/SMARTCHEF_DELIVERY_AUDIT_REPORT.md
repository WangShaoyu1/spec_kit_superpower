# SmartChef 交付物总体验收审核报告

**审核范围**: `spec.md`、`pd-all/*`、`ad/dd/plan/tasks`、`frontend/src`、`backend/app`、`backend/tests`、`.specify/harness/*`  
**审核口径**: 业务定义优先，PD/AD/DD/plan/tasks 为约束链，代码/测试/浏览器证据为落地事实  
**本轮审核结论**: `P0 治理闭环已落地，但不建议直接给出“全系统完全符合 spec / PD / UI / harness”的结论`

## 总评

本轮复核后，`intent-library` 的 `5` 页结构、主导航链路、模块级 browser probe、`plan/tasks` 强制校验已经回到硬门禁体系内。也就是说，**“缺少 `plan-intent-library.md` 还能继续做、主要页面缺失还能验收通过”** 这一类事故，已经不再是流程的默认行为，而会被新的 harness/gate 阻断。

但这并不等于系统已经达到“全量完全通过”的口径。当前更准确的结论应是：

- **P0 治理问题已完成整改**
- **主流程类结构性事故已被硬门禁吸收**
- **系统仍存在若干 P1/P2 级实现与 UI 规范偏差，需要在第二轮验收前继续收敛**

## 审核基线

- 业务真源: `specs/master/spec.md`
- PD 真源: `specs/master/pd-all/pd-index.md` 与各模块 `README.md`
- 页面规范真源: `specs/_template/pd-template.md`
- 规则真源: `.cursor/rules/specify-rules.mdc`
- Harness 真源: `.specify/harness/harness-gates.md`、`.specify/harness/module-rollout.json`、`.specify/harness/module-state.json`
- 实现事实: `frontend/src`、`backend/app`、`backend/tests`

## 历史事故根因（已治理）

### 已确认的本质原因
1. **计划层缺位**
说明: `intent-library` 曾缺少 `plans/plan-intent-library.md`，而旧流程仍可沿着“当前模块”或旧状态继续推进。  
现状: 已通过 `check-prerequisites.ps1`、`validate-stage-gates.ps1` 的 `-Module` 解析和 `GATE-PLAN-001 / 002` 收紧。  
证据: `.specify/scripts/powershell/check-prerequisites.ps1`, `.specify/scripts/powershell/validate-stage-gates.ps1`, `backend/tests/test_harness_gates.py`

2. **Browser gate 不检查页面边界**
说明: 旧 browser 验证更像行为冒烟，能在单页聚合实现上“看起来通过”，却无法证明页面边界、路由矩阵和主流程链路。  
现状: critical 模块已强制要求 `page_boundary_parity` 与 `route_navigation_chain`。  
证据: `.specify/harness/module-rollout.json`, `.specify/harness/harness-gates.md`

3. **Audit 分级过软**
说明: 旧审核文档把“缺页面 / 缺主流程”降成了 `INFO / 条件闭环`，导致结构性问题没有在验收前被拦下。  
现状: 审核模板和整改台账已改成“结构性缺口默认 `BLOCKER`”。  
证据: `docs/SMARTCHEF_AUDIT_FEEDBACK_TEMPLATE.md`, `docs/SMARTCHEF_REMEDIATION_REGISTER.md`

## 本轮复核发现

### WARNING
1. `intent-library` 的单条测试仍是启发式结果，不是真正基于当前模型产物的推理回读。  
说明: 页面入口已经恢复，但“对当前模型做单条测试”的业务语义仍偏弱。  
证据: `backend/app/api/intent_library.py`, `frontend/src/modules/intent-library/IntentLibraryTestPage.jsx`

2. `intent-library` 的发布动作仍缺少更强的前置引导。  
说明: 当前模型若尚未进入 `testable`，后端会拒绝发布，但前端引导仍偏弱，容易形成“为什么失败”的认知落差。  
证据: `frontend/src/modules/intent-library/IntentLibraryDetailPage.jsx`, `backend/app/api/intent_library.py`

3. 前端列表页未统一采用 `Table` 组件。  
说明: `pd-template.md` 已明确“列表用 Table”，但部分正式页仍使用 `List`，属于 UI 规范偏差，而不是主流程阻断。  
证据: `specs/_template/pd-template.md`, `frontend/src/modules/intent-library/IntentLibraryPage.jsx`, `frontend/src/modules/intent-library/IntentLibraryDatasetsPage.jsx`

4. `dataset-detail` 页面目前以样本明细只读为主，和 PD 中 FR-002 / FR-003 的深度仍有差距。  
说明: 页面边界已恢复，但信息密度和编辑深度尚未完全追平交互稿。  
证据: `frontend/src/modules/intent-library/IntentLibraryDatasetDetailPage.jsx`, `specs/master/pd-all/pd-intent-library/README.md`

### INFO
1. `pd-user-mgmt` 的权限矩阵仍把 PM 的“有条件权限”简化成了二值表达。  
证据: `frontend/src/modules/user-mgmt/UserMgmtPage.jsx`

2. 高风险二次确认、渐进式澄清、真实联网与迁移策略仍属于后续深化能力。  
证据: `backend/app`, `specs/master/spec.md`

## 模块级判断

| 模块 | 本轮结论 | 说明 |
|------|----------|------|
| `pd-user-mgmt` | `Closed` | 主链路、测试与权限门禁成立；剩余为权限矩阵表达偏差 |
| `pd-intent-library` | `Partial` | `5` 页边界、路由链路与 browser probe 已恢复；剩余问题集中在单条测试语义、列表组件规范、数据集深度 |
| `pd-knowledge-base` | `Partial` | 管理主链存在，但真实索引/生产问答证据仍需复核 |
| `pd-dialog-profile` | `Partial` | 手测链、发布门禁、知识库绑定成立；生产级多轮对话证据仍需加强 |
| `pd-batch-test` | `Closed` | 执行收敛、结果字段、智能分析与回读主链成立 |
| `pd-monitoring` | `Closed` | 三页面、筛选、trace、自动轮询与真实日志回读成立 |

## 已确认闭环

- `intent-library` 已重新拥有 `list / detail / datasets / dataset-detail / test` 五条正式路由
- `plan-intent-library.md` 已补齐，`tasks-intent-library.md` 已重建，并与 gate 强绑定
- `check-prerequisites` 与 `validate-stage-gates` 已支持模块级强校验
- critical 模块的 browser probe 已明确要求 `page_boundary_parity` 与 `route_navigation_chain`
- 多数核心模块已具备 contract / integration / frontend / smoke 的证据组合

## 主要残余风险

- 运行时高级能力仍未全部闭环: 高风险确认、渐进式澄清、真实联网、迁移策略
- `intent-library` 的单条测试与数据集深度仍有“页面存在但业务语义偏弱”的问题
- UI 规范层面尚未彻底统一: 列表页组件、信息密度、成功反馈后的真实回读体验

## 建议验收结论

### 结论建议
- 建议给出“**P0 治理整改已完成，系统进入第二轮严格人工验收**”的结论。
- 不建议给出“**全部交付物完全符合 spec / PD / UI / harness**”的结论。

### 建议整改优先级
1. 先处理 `intent-library` 的 P1 偏差: 单条测试语义、发布前置引导、列表 `Table` 规范、数据集深度
2. 再处理跨系统深化能力: 高风险确认、渐进式澄清、真实联网、迁移策略
3. 最后统一 UI/审计文档卫生，避免文档口径再漂移

## 配套交付物

- `docs/SMARTCHEF_REMEDIATION_REGISTER.md`
- `docs/SMARTCHEF_AUDIT_FEEDBACK_TEMPLATE.md`
- `docs/SMARTCHEF_UI_EFFECT_DEVIATION_LOG.md`
- `docs/SMARTCHEF_MODULE_AUDIT_CARDS.md`
- `docs/SMARTCHEF_FR_COVERAGE_MATRIX.md`
