# SmartChef FR 覆盖核对矩阵

说明:
- `状态` 口径: `Closed` = 当前证据基本支持；`Partial` = 有实现但不完整；`Open` = 未见足够证据或明显未实现
- 本表用于验收核对，不替代 `spec.md`

| FR | 主题 | 承接交付物 | 主要证据 | 审核状态 | 备注 |
|----|------|------------|----------|----------|------|
| FR-001 | 角色权限管理 | `user-mgmt` UI + admin API | `frontend/src/modules/user-mgmt/*`, `backend/app/api/user_mgmt.py`, `backend/tests/contract/test_user_api.py` | Closed | 主链路闭环，剩余问题仅为权限矩阵表达层面的 `INFO` 级偏差 |
| FR-002 | 指令配置管理 | `intent-library` | `pd-all/pd-intent-library/README.md`, `frontend/src/modules/intent-library/*`, `backend/app/api/intent_library.py` | Partial | React 实现范围小于 PD 页面集合 |
| FR-003 | 训练数据维护 | `intent-library` | 同上 | Partial | 后端与部分页面存在，完整数据集管理仍需继续核 |
| FR-004 | 知识库上传/解析/索引 | `knowledge-base` | `frontend/src/modules/knowledge-base/*`, `backend/app/api/knowledge_base.py`, `backend/tests/*knowledge*` | Partial | 主链路存在，真实索引能力需继续验收 |
| FR-005 | 知识检索 | `knowledge-base` | 同上 | Partial | 可见检索主线，生产问答命中质量需另证 |
| FR-006 | 分类与文档管理 | `knowledge-base` | 同上 | Closed | 分类、文档、过滤与详情主线较完整 |
| FR-007 | 对话方案管理 | `dialog-profile` | `frontend/src/modules/dialog-profile/*`, `backend/app/api/dialog_profile.py` | Closed | 方案管理主线与知识库绑定持久化已落稳 |
| FR-008 | 人设自定义 | `dialog-profile` | 同上 | Closed | 人设名称/描述可配置并回读 |
| FR-009 | 手动单条测试 | `dialog-profile` | `DialogProfileTestPage.jsx`, `dialog_profile.py`, 页面测试 | Partial | 会话与发消息可用，但仍是后台手测链路 |
| FR-010 | 调试 trace 展示 | `dialog-profile` | `DialogProfileTestPage.jsx`, `DialogProfileTestPage.test.jsx`, `dialog_profile.py` | Closed | 已补 route/intent 置信度、slots、response text、context snapshot 的真实回读与展示 |
| FR-011 | 设备上下文模拟 | `dialog-profile` | `DialogProfileTestPage.jsx`, `dialog_profile.py` | Partial | 支持基础上下文，但语义利用深度有限 |
| FR-012 | 批量测试入口 | `batch-test` | `frontend/src/modules/batch-test/*`, `backend/app/api/batch_test.py` | Closed | 批次列表、创建、详情入口存在 |
| FR-013 | 结果报告 | `batch-test` | `BatchTestDetailPage.jsx`, `BatchTestDetailPage.test.jsx`, `batch_test.py` | Closed | 结果表已展示预期/实际路由、意图、槽位、通过状态与命名阈值口径 |
| FR-014 | 智能分析 | `batch-test` | `batch_test.py`, `BatchTestDetailPage.jsx`, `BatchTestDetailPage.test.jsx` | Closed | 混淆矩阵、根因切片、建议与汇总均已由后端回读展示 |
| FR-015 | 方案发布 | `dialog-profile` | `DialogProfileDetailPage.jsx`, `dialog_profile.py`, contract tests | Closed | 发布动作与版本号回读存在 |
| FR-016 | 发布后设备切换/会话重置 | `dialog-profile` + API | `spec.md`, `dialog_profile.py`, `plans/tasks` | Open | 未见设备级生产切换与会话重置证据 |
| FR-017 | 设备侧对话 API 入口 | API | `runtime.py`, `main.py`, `test_dialog_profile_api.py` | Closed | 已新增设备侧 runtime API 契约并补 contract/flow tests |
| FR-018 | 指令识别/槽位提取 | API | `dialog_profile.py`, `batch_test.py` | Partial | 当前以启发式/测试链为主，不足以证明生产级识别 |
| FR-019 | 高风险指令确认 | API | `backend/app` | Open | 未见二次确认链路 |
| FR-020 | 渐进式澄清 | API | `backend/app` | Open | 未见三段式澄清实现 |
| FR-021 | 知识问答 | API | `knowledge_base.py`, `dialog_profile.py` | Partial | 后台知识管理存在，但生产问答链路证据不足 |
| FR-022 | 开放闲聊 | API | `dialog_profile.py` | Partial | 有兜底回复，未见真实大模型链路 |
| FR-023 | 设备会话管理 | API | `runtime.py`, `models.py`, `test_dialog_profile_flow.py` | Partial | 已补设备维 session 复用与隔离，但复杂多轮上下文能力仍需深化 |
| FR-024 | 双语支持 | API | `dialog_profile.py`, `runtime.py`, `batch_test.py`, `test_dialog_profile_flow.py` | Closed | 已补语言检测、mixed 中文优先与同语回复规则，并让三条入口共用主链 |
| FR-025 | 中英回复一致性 | API | `dialog_profile.py`, `runtime.py`, tests | Partial | 运行时中英回复一致性已落地，但训练数据翻译生成链路仍待单独证据 |
| FR-026 | 统一响应信封 | API | `app/dependencies`, contract tests | Closed | 成功/错误信封已在多模块验证 |
| FR-027 | 小模型+大模型分工 | API | `spec.md`, `dialog_profile.py` | Open | 仅见模型名称配置，未见真实分工链路 |
| FR-028 | 小模型跨方案共用 | API + intent-library | `intent_library.py`, `dialog_profile.py` | Partial | 数据结构支持，但生产验证证据不足 |
| FR-029 | Brave Search 联网能力 | API | `backend/app` | Open | 未见 Brave Search 集成 |
| FR-030 | 监控仪表盘指标 | `monitoring` | `MonitoringDashboardPage.jsx`, `monitoring.py`, tests | Partial | 主指标有，但 P99/完整口径未全展示 |
| FR-031 | 按设备查看历史会话 | `monitoring` | `MonitoringDeviceLogsPage.jsx`, `MonitoringDeviceLogsPage.test.jsx`, `monitoring.py` | Closed | 会话列表已支持 version 回读展示并可下钻链路 |
| FR-032 | 单会话完整链路 | `monitoring` | `MonitoringDeviceLogsPage.jsx`, `MonitoringDeviceLogsPage.test.jsx`, `monitoring.py` | Closed | 已展示 route/intent 置信度、槽位、响应文本、上下文快照 |
| FR-033 | API 结构化日志 | API + monitoring | `runtime.py`, `dialog_profile.py`, `monitoring.py`, `test_dialog_profile_api.py` | Closed | runtime 请求已自动写入 `RequestLog`，监控读侧可直接回读 |
| FR-034 | 请求日志多维筛选 | `monitoring` | `MonitoringDashboardPage.jsx`, `MonitoringDashboardPage.test.jsx`, `monitoring.py`, `backend/tests/contract/test_monitoring_api.py` | Closed | 已补时间窗口、意图、耗时区间、异常状态等完整维度，并前后端对齐 |
| FR-035 | 告警规则配置 | `monitoring` | `MonitoringAlertRulesPage.jsx`, `monitoring.py`, tests | Partial | 规则管理有，通知/跌幅语义仍不完整 |
| FR-036 | 敏感数据加密与 TLS | Infra | `crypto.py`, `config.py`, `db.py`, `test_security_privacy.py` | Closed | 已补 AES-256 存储与 TLS 连接参数入口，并有 at-rest 测试 |
| FR-037 | 设备维导出/删除 | Infra | `privacy.py`, `test_security_privacy.py` | Closed | 已补设备维导出/删除 API 与管理员二次确认链 |
| FR-038 | 监控 30s 自动轮询 | `monitoring` | `MonitoringDashboardPage.jsx`, `MonitoringDashboardPage.test.jsx`, `pd-all/pd-monitoring/README.md`, `spec.md` | Closed | 仪表盘已补自动轮询，并有前端测试锁定 |
| FR-039 | `library_key` 唯一不可改 | `intent-library` | API/tests + PD docs | Closed | 有唯一性与创建约束证据 |
| FR-040 | 方案并行绑定多个指令库 | `dialog-profile` | `DialogProfileDetailPage.jsx`, `dialog_profile.py` | Partial | 指令库与知识库绑定表单已齐，但多库策略的生产验证证据仍不足 |
| FR-041 | 英文不回退中文指令库 | API | `dialog_profile.py`, `runtime.py`, `batch_test.py`, tests | Closed | 英文输入已限制在英文库内匹配，未命中时不再回退中文指令库 |
| FR-042 | 存量迁移策略 | Infra | `spec.md`, repo docs | Open | 未见迁移脚本/策略落地证据 |
| FR-043 | 单库模型上限 5 | `intent-library` | `intent_library.py`, PD docs, tests | Closed | 规则存在且有下游文档承接 |
| FR-044 | 模型状态机 | `intent-library` | API/tests + PD docs | Closed | 状态机与训练/评估链有证据 |
| FR-045 | `testable/published` 唯一 | `intent-library` | flow tests + API | Closed | 已有测试覆盖 |
| FR-046 | 同时 `testable+published` | `intent-library` | API/tests + PD docs | Closed | 已有规则表达与实现 |
| FR-047 | 发布前校验库已发布模型 | `dialog-profile` | `dialog_profile.py`, `DialogProfileDetailPage.jsx`, tests | Closed | 门禁真实存在 |
| FR-048 | 训练集/评估集关联规则 | `intent-library` | API/tests + PD docs | Partial | 文档口径明确，前端完整页面未全实现 |
| FR-049 | 训练/评估导入口径 | `intent-library` | PD docs + API/tests | Partial | 后端部分具备，前端页面覆盖有限 |
| FR-050 | 阈值继承与快照 | `intent-library` | `pd-index.md`, `pd-intent-library/README.md`, API/tests | Partial | 当前活文档链正确保留 Partial，不可误报完成 |
| FR-051 | 单条+批量测试入口 | `intent-library` | API/tests + PD docs | Partial | API 有，React 交互覆盖仍偏薄 |
| FR-052 | 自动智能分析 | `intent-library` | API/tests + PD docs | Partial | 有分析结构，但 UI 展示完整性待补 |
| FR-053 | 发布/测试能力点控制 | `intent-library` | `constants.py`, shell/UI, tests | Partial | 有能力点模型，仍需端到端角色验收 |
| FR-054 | 平台无关模型下载 | `intent-library` | API/docs/tests | Partial | 下载元数据有证据，Python/C++ 一致性验收未见实证 |
