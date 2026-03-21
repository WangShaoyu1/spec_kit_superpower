# Speckit Plan - 实施计划

**核心规范**: `.specify/templates/plan-template.md` — plan.md 的结构和格式 MUST 遵循此模板。

## 目的
基于完成的设计文档（spec + pd + ad + dd），制定**可执行的技术实施计划**。
plan.md 定位为"**实施规划桥梁**"——承上（设计文档链）启下（tasks/ + 编码），不重复 AD/DD 已有的设计内容，聚焦于技术实施层面的决策与阶段规划。

## 输入（必须全部完成）
- `specs/{branch}/spec.md` - 业务需求 (含模块映射表 + FR 标签) ✓
- `specs/{branch}/pd-all/` - 模块化产品交互设计（含 pd-hub.html 统一入口 + pd-index.md 索引） ✓
- `specs/{branch}/ad/` - 架构设计（含 README.md 索引 + ad-global.md + ad-<module>.md） ✓
- `specs/{branch}/dd/` - 详细设计（含 README.md 索引 + dd-global.md + dd-<module>.md） ✓

## 执行流程

### Phase 0: Pre-flight 一致性扫描
在编写 plan.md 前, 必须先检查以下冲突并给出 `OK / WARNING / BLOCKER` 结论:
- 同一 FR 在 `spec / AD / DD` 中是否存在口径冲突
- `AD` 引用的 PD 页面或流程是否真实存在
- `plan` 将使用的源码路径是否与当前工程目录一致
- `PD` 是否存在部分覆盖/待补充项, 以及这些项是否需要显式下传到 `tasks`
- 关键异步链路是否已经定义真实成功信号、状态回传和失败处理

若出现 `BLOCKER`, 必须先回到上游设计文档修正, **不得直接继续生成 plan.md**。

### Phase 1: 技术方案细化
基于 AD 和 DD，细化技术实现方案：
- 技术栈版本确认（AD 中已选型，此处锁定具体版本）
- 项目目录结构设计（源码 + 测试 + 配置）
- 依赖清单（生产 + 开发依赖）

### Phase 2: 阶段规划
按依赖关系组织实施阶段（以 PD 模块为首要组织单元）：
1. 阶段 1: 基础设施（阻塞后续所有工作）
2. 阶段 2: 核心功能（按 PD 模块优先级，参考 spec.md 用户故事优先级排序）
3. 阶段 3: 横切关注点（权限、监控、安全）
4. 阶段 4: 完善与优化

每个阶段定义：
- 目标与交付物（对应 PD 模块的交互功能）
- 验收检查点（对照 PD 交互稿验证）
- 对应的 PD/AD/DD 章节引用（不复制内容）
- 对应模块的核心业务链路与真实成功信号
- 显式未完成声明（`Deferred / Stub / Out of Scope / Blocked By`）

### Phase 3: 测试策略
定义各阶段的测试类型：
- 单元测试（开发同步，覆盖 DD 定义的算法逻辑）
- 契约测试（API 稳定后，验证 AD 定义的接口契约）
- 消费契约测试（前后端联调前，验证字段名、分页、下载、数组/对象返回形态）
- 集成测试（阶段完成，验证 AD 数据流）
- E2E 测试（功能闭环后，覆盖 PD 交互路径）
- 状态机测试（异步链路实现时，覆盖提交/处理中/成功/失败全状态）

### Phase 4: 风险与缓解
识别实施风险：
- 技术风险（新技术学习曲线）
- 依赖风险（第三方服务/API）
- 进度风险（任务估不准）

## 输出产物

```yaml
# specs/{branch}/plan.md
---
version: 2.0
based_on:
  - spec.md
  - pd-all/ (pd-index.md + pd-<module>/)
  - ad/ (ad-global.md + ad-<module>.md)
  - dd/ (dd-global.md + dd-<module>.md)
---

# 1. 摘要
# 2. 技术背景（速查，不重复 AD/DD）
# 3. 项目结构（设计文档 + 源代码）
# 4. 阶段规划（含检查点）
# 5. 测试策略
# 6. 风险与缓解
```

## Plan 完整性检查清单

- [ ] 每个阶段都能追溯到 spec/pd/ad/dd 的具体章节
- [ ] Pre-flight 一致性扫描已完成，且无未处理的 BLOCKER
- [ ] 阶段依赖关系无循环
- [ ] 阶段划分有明确的检查点（Checkpoint）
- [ ] 每个 UI 模块都定义了 1-3 条核心业务链路与真实成功信号
- [ ] 测试策略覆盖所有 PD 模块交互流程
- [ ] 测试策略覆盖前后端消费契约和异步状态机
- [ ] 性能目标有对应的测试任务
- [ ] 不重复 AD/DD 中已定义的详细内容（仅做引用）
- [ ] **项目路径一致性**: plan.md 中引用的项目目录（如 `smartchef-v2/`）与 tasks/ 中的路径引用完全一致
- [ ] **PD 模块路径映射**: 每个 PD 模块有明确的源码目录映射（如 `pd-intent-library/ → frontend/src/pages/IntentLibrary/`）
- [ ] 已显式记录 Deferred / Stub / Out of Scope / Blocked By，不允许把“部分覆盖”藏在备注里

## 下一步
plan.md 完成后，运行 `/speckit.tasks` 生成 tasks/ 任务目录，然后 `/speckit.implement` 开始执行。
