---
description: 将 HumanPD 转换为 AI 优先消费的 AI-PD 语义规格
---

# Speckit Transform-PD - HumanPD 到 AI-PD

## 目的

把 `pd-all/` 中服务人类阅读的 HTML/README 转换为服务 AI、harness 和下游命令的 `AI-PD`。

**核心规范**: `specs/_template/ai-pd-template.md`

## 输入

- `specs/{branch}/spec.md`
- `specs/{branch}/pd-all/pd-index.md`
- `specs/{branch}/pd-all/pd-<module>/README.md`
- `specs/{branch}/pd-all/pd-<module>/*.html`

其中 `pd-<module>/README.md` 中每个页面的页面能力清单必须显式提供：

- `page_goal`
- `primary_user_flows`

## 输出

```text
specs/{branch}/ai-pd/
├── README.md
├── ai-<module>.md
└── ai-<module>.checklist.md
```

## 半自动脚本入口

优先使用脚本入口生成 AI-PD scaffold：

```powershell
python scripts/transform_pd.py --feature <branch> --module pd-<module>
pwsh -File .specify/scripts/powershell/transform-pd.ps1 -Feature <branch> -Module pd-<module>
```

说明：

- 脚本会从 `README.md + *.html` 提取页面、FR、字段、按钮、隐藏交互线索
- 脚本在生成前会先校验每个 HTML 页面是否显式提供 `page_goal / primary_user_flows`
- 若缺失，脚本会直接以非 0 退出，并输出 `GATE-PD-003` 风格的缺失清单；不允许继续生成下游 AI-PD
- 输出是 **AI-PD scaffold**，不是“可跳过审阅的最终语义真相”
- 每生成一个 `ai-<module>.md`，必须同步生成一个 `ai-<module>.checklist.md`，用于人工校对高风险语义点
- `ai-<module>.checklist.md` 仅是人工校对参考清单，不是第二份语义真相，也不是需要持续维护的状态文件；人工校对时必须直接修改原 `ai-<module>.md`
- 生成后仍需人工补齐无法从 HumanPD 稳定推断出的 contract / exception / out_of_scope 细节

## 转换原则

1. 不复制 HTML 中的演示代码、组件导入和样式细节
2. 只保留会影响实现、测试、验收、门禁的产品语义
3. 为每个页面生成稳定 `page_id`
4. 为每项能力生成稳定 `capability_id`
5. 显式输出：
   - `primary_user_flows`
   - `capabilities`
   - `action_contracts`
   - `data_contracts`
   - `business_rules`
   - `exception_flows`
   - `hidden_interactions`
   - `acceptance_signals`
   - `fr_mapping`

## 执行流程

### Phase 1: 读取 HumanPD

- 读取 `pd-index.md`，确定模块列表
- 读取模块 README，提取 FR、页面边界、业务说明
- 读取对应 HTML，提取页面、入口、字段、操作、异常态

### Phase 2: 语义归一化

将 HumanPD 内容分类为：

- `ui-capability`
- `domain-rule`
- `instructional`
- `non-actionable-note`

同时要求 PD 协同提供页面级语义锚点：

- `page_goal`
- `primary_user_flows`

若 README 中缺少上述字段，`transform-pd` 必须立即失败并提示补齐；不允许再以近似推断结果继续向下游流转。

### Phase 3: 生成 AI-PD

对每个模块生成 `ai-<module>.md`：

- 页面索引
- 页面级能力块
- 稳定 capability IDs
- Partial / Deferred / Blocked By

同时生成 `ai-<module>.checklist.md`：

- 不要求全文复核
- 只聚焦页面边界、父子关系、隐藏交互分类、capability 粒度、action_contract 成功信号、FR 范围和明显缺失项
- 人工校对时必须直接修改 `ai-<module>.md`
- checklist 不作为“是否已修改完成”的记录源，也不允许承载独立语义结论

### Phase 4: 建立索引

更新 `ai-pd/README.md`：

- 模块列表
- 来源 PD
- 覆盖页面数
- 风险状态

## 质量检查

- [ ] `ai-pd/README.md` 已生成
- [ ] 每个 PD 模块都有对应 `ai-<module>.md`
- [ ] 每个 `ai-<module>.md` 都有对应 `ai-<module>.checklist.md`
- [ ] `pd-all/` 中每个 HTML 页面都已提供 `page_goal / primary_user_flows`
- [ ] 所有页面都有 `page_id`
- [ ] 所有能力都有 `capability_id`
- [ ] 所有隐藏交互已完成语义分类
- [ ] 人工校对只需覆盖高风险语义点，不要求全文重审
- [ ] 所有 Partial / Deferred / Blocked By 已显式继承

## 下游关系

转换完成后：

- `/speckit.design-ad` 优先读取 `ai-pd/`
- `/speckit.design-dd` 优先读取 `ai-pd/`
- `/speckit.plan` / `/speckit.tasks` / `/speckit.implement` / `/speckit.smoke` 以 `ai-pd/` 为主输入
- `pd-all/` 继续保留为人类视觉参考层
