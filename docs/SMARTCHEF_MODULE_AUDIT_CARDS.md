# SmartChef 模块审查卡

## `pd-user-mgmt`
- 目标 FR: `FR-001`
- 审查对象: `pd-all/pd-user-mgmt/README.md`, `frontend/src/modules/user-mgmt/*`, `backend/app/api/user_mgmt.py`, `backend/tests/contract/test_user_api.py`
- 已确认:
  - 账号创建、角色调整、启停用、密码重置、权限矩阵均有页面入口
  - 后端有能力点校验、默认管理员保护、审计日志、统一错误信封
  - 壳层菜单按 capability 控制
- 主要问题:
  - 权限矩阵对 PM 的条件权限只显示 `有/-`，没有体现真实限制
- 审查结论: `Closed`

## `pd-intent-library`
- 目标 FR: `FR-002,003,039~054`
- 审查对象: `pd-all/pd-intent-library/README.md`, `plans/plan-intent-library.md`, `tasks/tasks-intent-library.md`, `frontend/src/modules/intent-library/*`, `backend/app/api/intent_library.py`, 相关 tests
- 已确认:
  - `5` 页边界已恢复：列表、详情、数据集、数据集详情、测试页均有正式路由与页面承接
  - `page_boundary_parity`、`route_navigation_chain` 已进入 critical 模块 browser probe 口径
  - `FR-050 Partial` 在活文档链、后端、前端警示里都被保留
  - 模型状态机、唯一性规则、下载元数据、阈值快照有实现和测试承接
- 主要问题:
  - 单条测试结果仍偏启发式，不足以完全等价为“当前模型推理结果”
  - 列表页与数据集页仍未统一使用 `Table`
  - `dataset-detail` 仍以只读样本展示为主，FR-002 / FR-003 深度不足
- 审查结论: `Partial`

## `pd-knowledge-base`
- 目标 FR: `FR-004~006`
- 审查对象: `pd-all/pd-knowledge-base/README.md`, `frontend/src/modules/knowledge-base/*`, `backend/app/api/knowledge_base.py`, 相关 tests
- 已确认:
  - 分类、文档上传、详情、过滤字段展示、重新索引/删除有实现面
  - PD 与实现的页面边界整体一致
- 主要问题:
  - README 已明确“不宣称真实索引后端闭环”，因此生产问答效果不能仅凭后台文档管理页通过
- 审查结论: `Partial`

## `pd-dialog-profile`
- 目标 FR: `FR-007~011,015~016,040,047`
- 审查对象: `pd-all/pd-dialog-profile/README.md`, `frontend/src/modules/dialog-profile/*`, `backend/app/api/dialog_profile.py`, `tasks-dialog-profile.md`
- 已确认:
  - 方案 CRUD、人设配置、指令库绑定、手动测试入口、发布门禁都已有实现
  - 知识库绑定控件已补齐，保存时可保留 `knowledge_base_id`
  - 手动测试 trace 已补 route/intent 置信度、response text、slots 与 context snapshot
  - 发布门禁真实依赖绑定库是否存在 published 模型
  - 手测 / runtime / batch 已共用语言路由主链，支持英文不回退中文与 mixed 中文优先
- 主要问题:
  - 发布后设备会话即时切换仍建议补更强证据
- 审查结论: `Closed`

## `pd-batch-test`
- 目标 FR: `FR-012~014`
- 审查对象: `pd-all/pd-batch-test/README.md`, `frontend/src/modules/batch-test/*`, `backend/app/api/batch_test.py`, `tasks-batch-test.md`
- 已确认:
  - 批次列表、详情、生成用例、执行、结果与分析 API 已存在
  - 后端有 accuracy、p95、分析结果与执行状态聚合
  - 前端执行已改为等待异步收敛后再提示完成
  - 结果表已补预期/实际槽位、通过状态与命名阈值口径
  - 智能分析页已补混淆矩阵展示，并与后端回读结构一致
- 主要问题:
  - 无阻塞性缺口，剩余仅为后续体验深化
- 审查结论: `Closed`

## `pd-monitoring`
- 目标 FR: `FR-030~032,034~035,038`
- 审查对象: `pd-all/pd-monitoring/README.md`, `frontend/src/modules/monitoring/*`, `backend/app/api/monitoring.py`, `backend/tests/contract/test_monitoring_api.py`, `backend/tests/test_monitoring_flow.py`
- 已确认:
  - 仪表盘、设备日志、告警规则三页面均已落地
  - overview、device trace、alert rule 的基础回读与测试存在
  - 30 秒自动轮询已补齐，并有前端测试锁定
  - 请求日志已补时间窗口、意图、耗时、异常等多维筛选
  - 会话列表已展示 version，链路详情已展示置信度、槽位、回复文本与上下文快照
  - runtime 真请求已自动写入 `RequestLog`，监控回读不再依赖纯种子数据
- 主要问题:
  - 无阻塞性缺口，剩余主要是告警语义与体验深化
- 审查结论: `Closed`

## 横切对象: API / Infra / Harness
- 目标 FR: `FR-017~029,033,036~037,041~042`
- 审查对象: `backend/app`, `backend/tests`, `.specify/harness/*`, `specs/master/tasks/*`, `specs/master/plans/*`
- 已确认:
  - Harness 状态机、模块顺序、browser stage、quality probes 结构完整
  - `check-prerequisites` / `validate-stage-gates` 已具备模块级 plan 强校验
  - critical 模块已强制声明 `page_boundary_parity` 与 `route_navigation_chain`
  - 多个后台模块已经有 contract/integration/frontend 测试基础
  - `tasks-infra.md`、`tasks-user-mgmt.md` 以及多个模块任务文件的漂移已清理
  - 设备侧 runtime API、真实请求日志、AES-256 存储/TLS、设备维导出删除与语言路由都已落地
- 主要问题:
  - Brave Search、迁移策略与更复杂的确认/澄清对话仍待后续版本继续实现
  - 审计结论与模块状态虽已显著收敛，但仍需保持每轮实现后的增量同步
- 审查结论: `Partial`
