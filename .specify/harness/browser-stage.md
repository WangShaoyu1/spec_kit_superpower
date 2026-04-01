# Browser Stage

## 目标

把浏览器验证从“全量收尾动作”前移成“模块完成后的硬门禁”。

## 进入条件

- 目标模块当前状态为 `implementing`、`browser_verified` 或 `done`
- 该模块的单测、集成测试、构建验证已完成
- `validate-stage-gates.ps1 -Stage browser -Module <module>` 返回非 `blocked`

## 三层验证

### 1. UI smoke

验证页面可打开、核心按钮/表单/表格可操作、无白屏/永久 loading。

### 2. business e2e

对目标模块执行一条最小真实闭环，必须验证“最终结果可回读”，而不是只验证提交成功。

### 3. quality probes

验证以下信号：

- 错误提示真实可见
- 关键结果可回读
- 空态/异常态存在
- 关键操作响应时间可观测

## 重点模块附加要求

- `pd-intent-library`: 必查训练状态流转、批量评估反馈、准确率信号
- `pd-dialog-profile`: 必查方案绑定一致性、发布门禁、测试聊天结果

## 输出证据

模块浏览器阶段完成后，必须至少沉淀以下证据：

- smoke 结论
- 业务闭环结论
- quality probes 结论
- 当前失败清单或“无失败”结论

若目标模块通过，则将状态从 `implementing` 推进到 `browser_verified`。
