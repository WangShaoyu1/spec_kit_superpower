# Speckit Design-PD - 产品交互设计

## 目的

将 spec.md 的业务需求转化为**模块化的可交互产品原型**，定义页面流程、状态变化和用户体验细节。

**核心规范**: `specs/_template/pd-template.md` — 所有 PD 设计 MUST 遵循此模板。

## 前提条件

- `specs/{branch}/spec.md` 已完成, 且包含:
  - **模块与交付物映射表** (标注哪些 FR 需要 PD)
  - **FR 交付物类型标签** (`[UI:<module>]` / `[API]` / `[Infra]`)
- 如果 spec.md 缺少上述结构, MUST 先补充再开始 PD 设计

## 输入

- `specs/{branch}/spec.md` - 业务需求基线 (含模块映射表)
- `specs/_template/pd-template.md` - PD 设计规范 (框架级模板, 非项目定制)

## 执行流程

### Phase 1: 模块拆分

从 spec.md 的"模块与交付物映射表"提取所有 `[UI:<module>]` 类模块:

1. 筛选需要 PD 的模块 (交付物类型 = 后台 UI)
2. 确认模块边界符合 `pd-template.md` §7.1 的拆分判定规则
3. 确定各模块的设计优先级 (与 spec.md 用户故事优先级对齐)
4. 跳过 `[API]` 和 `[Infra]` 类 FR (由 AD/DD 覆盖)

```
spec.md 模块映射表
├── [UI:intent-library]  → pd-intent-library/  ← 需要 PD
├── [UI:knowledge-base]  → pd-knowledge-base/  ← 需要 PD
├── [API]                → 跳过, AD/DD 覆盖
└── [Infra]              → 跳过, DD 覆盖
```

### Phase 2: 按模块逐一生成 PD

对每个 UI 模块, 按 `pd-template.md` §7.3 的转化步骤执行:

1. **需求层级拆分**: 模块内 FR → 识别主导航页面 vs 子功能/操作
2. **交互流程图绘制**: 每个 CRUD 操作绘制 Mermaid 流程图 (§5.5)
3. **页面与操作映射**: 主导航页 → 下级页 → 弹窗/抽屉
4. **数据流向设计**: 输入→处理→输出链路 (§5.1)
5. **状态机设计**: 所有状态和流转规则 (§5.2)
6. **约束识别**: 业务规则 (数量限制、绑定关系、权限等) (§5.3~5.4)
7. **交互原型实现**: 使用 React + Ant Design (CDN UMD) 实现页面 (§3)

每个模块的产出目录结构:
```
specs/{branch}/pd-<module-key>/
├── README.md          # 模块说明 + FR追溯矩阵 + 合规检查表
├── index.html         # 列表页 (主导航页面)
├── detail.html        # 详情页 (下级页面)
├── [其他页面].html    # 根据模块复杂度增加
└── ...
```

### Phase 3: 维护 pd-index.md

在 `specs/{branch}/` 下创建/更新 `pd-index.md` (§7.2):
- 列出所有 PD 模块的覆盖状态
- 列出非 UI 类 FR (不需要 PD)
- 标注跨模块引用关系
- 建议设计优先级

### Phase 4: 质量检查

对每个已完成的 PD 模块, 逐项检查 `pd-template.md` §10 的输出检查清单:
- §10.1 技术检查 (CDN 加载、组件引入)
- §10.2 导航检查 (侧边栏、下级页面、返回按钮)
- §10.3 抽屉检查 (说明按钮、6 标签页)
- §10.4 交互检查 (流程图、状态机、数据绑定)
- §10.5 模块与追溯检查 (命名规范、FR 映射)

## 输出产物

```
specs/{branch}/
├── pd-index.md                    # 全局 PD 覆盖索引
├── pd-<module-key-1>/             # PD 模块 1
│   ├── README.md
│   ├── index.html
│   ├── detail.html
│   └── ...
├── pd-<module-key-2>/             # PD 模块 2
│   ├── README.md
│   └── ...
└── ...
```

**命名规范**: `pd-<module-key>/`, module-key 使用小写 + 短横线, 禁止使用缺陷/任务编号。

## PD 完整性检查清单

- [ ] spec.md 包含模块映射表和 FR 标签 (Phase 1 前提)
- [ ] 所有 UI 类模块都有对应的 `pd-<module>/` 目录
- [ ] 每个模块的 README 包含 FR → PD 追溯矩阵
- [ ] 每个模块的 README 包含合规检查表
- [ ] `pd-index.md` 已创建且状态准确
- [ ] 每个页面都遵循 pd-template.md 的页面框架 (§4)
- [ ] 每个操作都有 Mermaid 流程图 (§5.5)
- [ ] 关键页面都有状态矩阵 (§5.2)
- [ ] 异常场景有明确的用户反馈 (§9)
- [ ] 危险操作都有二次确认 + 倒计时 (§5.4)
- [ ] 跨模块引用有明确标注 (§7.1.4)

## 交互式工作流

PD 设计通常需要多轮对话:

1. **首轮**: 完成模块拆分 (Phase 1), 确认模块列表和优先级
2. **逐模块**: 按优先级依次设计每个模块, 每个模块可能需要多轮反馈
3. **收尾**: 更新 pd-index.md, 进行全局一致性检查

用户可以在任何阶段提出修改意见, AI 应基于 pd-template.md 规范评估修改的合理性。

## 注意事项

- pd-template.md 是**框架级规范**, 不要为特定项目修改它
- 如果 spec.md 结构不满足 Phase 1 的要求, 应先引导用户补充 (或协助补充)
- 纯 API / CLI / SDK 项目没有 UI 模块时, 本阶段可标注"无 UI 模块, 跳过 PD" 并跳过

## 下一步

所有 PD 模块完成后, 进入 `/speckit.design-ad` (架构设计) 阶段。
PD 是 AD 的重要输入: AD 需要基于 PD 确定的页面结构来设计 API 契约和数据模型。
