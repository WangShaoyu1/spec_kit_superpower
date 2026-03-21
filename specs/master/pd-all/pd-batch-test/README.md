# pd-batch-test: 批量测试交互原型

## 项目概述

本交互原型基于 `pd-template.md` v4.1 规范，实现批量测试模块的全链路交互设计（新建测试批次 → 上传/生成用例 → 执行测试 → 查看报告 → 智能分析）。

**技术栈**: React 18 + Ant Design 6.x (CDN UMD, 无脚手架) + Babel Standalone + Dayjs

**对应规范**: `specs/master/spec.md` v1.4，覆盖 FR: FR-012, FR-013, FR-014

**PD 模块 Key**: `batch-test`（参见 `specs/master/pd-index.md`）

## 文件结构与页面层级

```
pd-batch-test/
├── index.html              # 批量测试列表页（主导航页面）
├── detail.html             # 测试批次详情/结果页（下级页面）
└── README.md
```

| 页面 | 类型 | 侧边栏菜单 | 返回按钮 | 说明抽屉 |
|------|------|-----------|---------|---------|
| index.html | 主导航页面 | ✅ 批量测试高亮 | 无 | ✅ 6 Tab |
| detail.html | 下级页面 | ✅ 批量测试高亮 | ✅ 返回列表 | ✅ 6 Tab |

## 需求追溯矩阵 (FR → PD)

| FR 编号 | 需求摘要 | PD 页面 | 交互组件 | 覆盖状态 |
|---------|---------|---------|---------|---------|
| FR-012 | 批量测试：自动生成用例，PM 可手动修改微调 | index.html | 新建批次弹窗 + 用例生成/上传 | ✅ 完整 |
| FR-013 | 用例模板：编号、语句、预期/实际路由/意图/槽位、得分、耗时、达标 | detail.html | 测试结果 Table（完整字段） | ✅ 完整 |
| FR-014 | 未达标智能分析报告：总体汇总、准确率排名、混淆矩阵、归因分析、建议 | detail.html | 分析报告 Tabs + Collapse 面板 | ✅ 完整 |

**跨模块引用**：

| 引用方向 | 说明 |
|---------|------|
| pd-intent-library/test.html → index.html | 指令库测试页可跳转批量测试 |
| index.html → pd-dialog-profile | 批量测试关联对话方案 |

---

**创建时间**: 2026-03-18
**最后更新**: 2026-03-18 (v1.0)
**PD 模块**: batch-test
**对应 spec.md**: v1.4 (FR-012, FR-013, FR-014)
