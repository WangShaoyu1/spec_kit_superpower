# D016 验收清单（执行版）

更新时间：2026-03-13

## 1. 准备环境

- 启动后端依赖：`python scripts/manage_services.py start`
- 启动后端服务：`uvicorn app.main:app --reload --port 8000`
- 启动前端服务：`npm run dev`
- 使用具备 `model_publish`、`model_test_manage` 权限账号登录后台

## 2. 指令库与模型生命周期

- 新建一个指令库（例如 `d016_zh`，语种 `zh`）
- 新建训练集、评估集
- 导入训练 Excel（最小字段）
- 导入评估 Excel（全字段，允许结果列为空）
- 发起训练，确认模型创建成功
- 将模型设为 `testable`，确认同库原 testable 被自动取消
- 发布模型时必须勾选“确认发布”，备注可空
- 校验发布后模型为库内唯一 `published`

预期结果：
- 状态流转符合 D016 约束
- 二次确认未勾选时发布被拦截
- 发布备注可存储

## 3. 单条测试与评估分析

- 在“模型管理”页执行单条测试，输入测试语句
- 查看简要结果（预测意图、置信度）和展开详情
- 发起一次评估任务（可覆盖阈值）
- 打开评估记录，查看结构化分析

预期结果：
- 单条测试返回完整结构（summary + detail）
- 评估结果包含：总体结论、Top 混淆、槽位错误分布、低分样本、建议
- 评估集样本回填 `actual_result/actual_score/is_hit`

## 4. 方案发布门禁

- 创建并绑定上述指令库的对话方案
- 当该库无 `published` 模型时尝试发布方案
- 发布一个库模型后再次发布方案

预期结果：
- 无 published 模型时，方案发布被阻断并提示
- 存在 published 模型后，方案可发布

## 5. 模型产物下载与校验

- 为模型登记产物（ONNX 文件路径）
- 调用下载接口并传入正确 `expected_sha256`
- 再传入错误 `expected_sha256`

预期结果：
- 正确哈希下载成功，响应包含 `X-Artifact-Sha256`
- 错误哈希返回 409
- 若登记哈希与文件实际哈希不一致，返回 409

## 6. 自动化回归（建议作为验收前置）

- 后端契约：
  - `pytest tests/contract/test_intent_libraries_api.py -q`
  - `pytest tests/contract/test_versions_api.py -q`
- 后端集成：
  - `pytest tests/integration/test_model_portability_script.py -q`
- 前端：
  - `npm run build`
  - `npm run e2e`

预期结果：
- 全部通过，无阻断失败

## 7. 未完成项（保留跟踪）

- T193：补齐 D016 专项集成测试矩阵（状态机互斥、阈值快照、未命中后续链路）
- T194：补齐 D016 专项前端 E2E（发布确认、Excel 导入导出、权限可见性）
- T197：补齐同一发布模型在 Python 与 C++ 双链路真实推理一致性验证
