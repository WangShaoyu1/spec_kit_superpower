# SmartChef 问题分级与整改建议

| 级别 | 编号 | 状态 | 问题 | 影响范围 | 建议整改方向 | 是否阻塞验收 |
|------|------|------|------|----------|--------------|--------------|
| BLOCKER | P0-01 | 已落地 | 模块 plan 缺失时，`check-prerequisites / validate-stage-gates` 仍可能按“当前模块”兜底继续推进 | `plan -> tasks -> implement` 治理链 | 强制支持 `-Module` 解析；命中 `GATE-PLAN-001 / 002` 后直接阻断 | 否 |
| BLOCKER | P0-02 | 已落地 | critical 模块缺少页面边界 / 路由矩阵 probe 时，browser gate 无法识别结构性缺口 | `browser` gate、手动验收可信度 | 为 critical 模块强制声明 `page_boundary_parity / route_navigation_chain`，缺失即 `GATE-BROWSER-004` | 否 |
| BLOCKER | P0-03 | 已落地 | 审核模板和总报告曾把“缺页面 / 缺主流程”降级为 `INFO/条件闭环` | 审核结论、是否允许进入验收 | 收紧 audit 分级口径：结构性缺口默认 `BLOCKER` | 否 |
| WARNING | P1-01 | 待整改 | `intent-library` 单条测试仍是启发式结果，不是真正基于当前模型的测试回读 | `FR-051`, `FR-052`, 手动验收可信度 | 将 `single-test` 语义与真实模型状态对齐，避免“页面有结果但不是当前模型” | 是 |
| WARNING | P1-02 | 待整改 | `intent-library` 发布动作缺少更强前置引导，非 `testable` 模型发布失败时解释偏弱 | `FR-045~047`, PM 操作闭环 | 在详情页显式提示“需先完成评估进入 testable”，并处理失败反馈 | 是 |
| WARNING | P1-03 | 待整改 | 前端列表页未统一使用 `Table` 组件 | UI 规范一致性、信息密度 | 把“列表默认使用 Ant Design Table”写入规则真源，并逐模块清理 `List` 型目录页 | 否 |
| WARNING | P1-04 | 待整改 | `intent-library` 的 `dataset-detail` 仍以只读样本展示为主，未达到 PD 中 FR-002 / FR-003 的深度 | `FR-002`, `FR-003`, 数据配置深度 | 继续补齐意图/槽位/追问/样本编辑能力，或在 PD/FR 覆盖矩阵中明确降级范围 | 否 |
| INFO | A-01 | 已落地 | 设备侧生产对话 API 契约已补齐 | `FR-017~029`, 设备侧交付 | 已新增 runtime API、设备会话模型与 contract/flow tests | 否 |
| INFO | A-02 | 已落地 | 真实请求自动写入 `RequestLog` 已修复 | `FR-033`, `US9`, 监控可信度 | runtime 入口已统一落日志，监控读侧可直接回读 | 否 |
| INFO | A-03 | 已落地 | 安全与隐私关键缺口已补齐 | `FR-036~037`, `SC-013` | 已补 AES-256 存储、DB TLS 参数、设备维导出/删除 API 与管理员二次确认链 | 否 |
| INFO | B-01 | 已落地 | 监控 30s 自动轮询缺口已修复 | `FR-038` | 已补前端定时轮询与 Vitest 回归 | 否 |
| INFO | B-02 | 已落地 | 监控多维筛选缺口已修复 | `FR-034` | 已补时间窗口、意图、耗时、异常等筛选项，并有前后端测试锁定 | 否 |
| INFO | B-03 | 已落地 | 批量测试“假成功”提示风险已修复 | `FR-012~014`, 结果可信度 | 已改为轮询直到 `running -> completed/failed` 收敛后再提示成功 | 否 |
| INFO | B-04 | 已落地 | 对话方案 `knowledge_base_id` 丢失问题已修复 | `FR-007`, `FR-015` | 已补知识库字段、保存保留真实值，并补前端回归测试 | 否 |
| INFO | B-05 | 已落地 | 手动测试与监控 trace 字段深度缺口已修复 | `FR-010`, `FR-032`, `US9` | 已补 route/intent 置信度、槽位详情、响应文本、设备上下文快照等字段与展示 | 否 |
| INFO | B-06 | 持续治理 | Harness 状态与 `tasks` 文档漂移已完成首轮收敛，但仍需保持增量同步 | 审核可信度、后续交接 | 每轮审计/实现结束后同步 `tasks/*.md`、`module-state.json`、SMARTCHEF 文档 | 否 |

## 建议整改顺序
1. 先收敛 `P1-01 / P1-02`，避免 `intent-library` 在第二轮人工验收中继续出现“页面在、语义弱”的问题。
2. 再收敛 `P1-03 / P1-04`，统一 UI 规范与 PD 深度。
3. 最后继续推进高风险确认、渐进式澄清、真实联网与迁移策略等后续能力。

## 建议反馈闭环
- 每个 `BLOCKER / WARNING` 生成一条独立缺陷或整改任务，附带复现证据、影响 FR、预期行为、修复证据。
- 修复完成后重新跑与该问题直接对应的 contract / integration / frontend / browser 验证，不接受“只改代码不补证据”。
- 在下一轮总验收前，先同步 `tasks/*.md`、`module-state.json` 与 `docs/SMARTCHEF_*.md`，避免再次出现状态漂移。
