# SmartChef UI / 效果偏差清单

说明:
- `文档型偏差`: 能直接对照 `pd-template`、PD README 或 `spec.md`
- `派生型偏差`: 规范未明说，但与当前正式壳层的一致性或“真实回读”原则冲突

| 级别 | 类型 | 模块 | 偏差描述 | 证据 |
|------|------|------|----------|------|
| WARNING | 文档型 | `intent-library` | 列表页与数据集页当前仍使用 `List`，不符合 `pd-template` §2.1 “列表用 Table” 的默认规范 | `specs/_template/pd-template.md`, `frontend/src/modules/intent-library/IntentLibraryPage.jsx`, `frontend/src/modules/intent-library/IntentLibraryDatasetsPage.jsx` |
| WARNING | 文档型 | `intent-library` | `dataset-detail` 当前以样本只读展示为主，尚未达到 PD 中 FR-002 / FR-003 的交互深度 | `specs/master/pd-all/pd-intent-library/README.md`, `frontend/src/modules/intent-library/IntentLibraryDatasetDetailPage.jsx` |
| WARNING | 派生型 | `intent-library` | 单条测试虽已恢复到独立测试页，但结果仍主要来自启发式返回，不足以等价为“当前模型推理结果” | `backend/app/api/intent_library.py`, `frontend/src/modules/intent-library/IntentLibraryTestPage.jsx` |
| WARNING | 派生型 | `intent-library` | 详情页发布动作在模型未进入 `testable` 时缺少更强的前置引导与失败说明 | `frontend/src/modules/intent-library/IntentLibraryDetailPage.jsx`, `backend/app/api/intent_library.py` |
| INFO | 文档型 | `user-mgmt` | 权限矩阵把 PM 的受限权限压缩成二值显示，弱化了权限边界表达 | `frontend/src/modules/user-mgmt/UserMgmtPage.jsx`, `backend/app/constants.py` |
| INFO | 派生型 | `monitoring` | 30s 自动轮询已存在，但页面上的刷新反馈仍可进一步可视化 | `frontend/src/modules/monitoring/MonitoringDashboardPage.jsx` |
| INFO | 派生型 | 全局 | 多数模块已统一壳层，但“成功反馈后是否伴随真实刷新”的表达仍不完全一致 | `frontend/src/modules/*`, `frontend/src/app/AppShell.jsx` |

## 审核建议
- 先处理会影响主流程可信度的 `WARNING`，尤其是 `intent-library` 的单条测试语义与发布引导。
- 所有列表型页面默认使用 `Table`；若确需使用非表格组件，必须在 PD/plan 中写明例外原因。
- 所有“成功提示”类交互统一增加真实回读或状态收敛判断。
