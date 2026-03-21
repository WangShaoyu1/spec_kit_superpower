# pd-monitoring: 监控仪表盘交互原型

## 项目概述

本交互原型基于 `pd-template.md` v4.1 规范，完整实现监控仪表盘模块的全链路交互设计（实时指标 → 设备日志 → 会话链路 → 告警规则）。

**技术栈**: React 18 + Ant Design 6.x (CDN UMD, 无脚手架) + Babel Standalone + Dayjs

**对应规范**: `specs/master/spec.md` v1.4，覆盖 FR: FR-030~032, FR-034~035, FR-038

**PD 模块 Key**: `monitoring`（参见 `specs/master/pd-index.md`）

## 文件结构与页面层级

```
pd-monitoring/
├── index.html              # 监控仪表盘主页（主导航页面）
├── device-logs.html        # 设备日志与会话详情（下级页面）
├── alert-rules.html        # 告警规则配置（下级页面）
└── README.md
```

| 页面 | 类型 | 侧边栏菜单 | 返回按钮 | 说明抽屉 |
|------|------|-----------|---------|---------|
| index.html | 主导航页面 | ✅ 监控仪表盘高亮 | 无 | ✅ 6 Tab |
| device-logs.html | 下级页面 | ✅ 监控仪表盘高亮 | ✅ 返回仪表盘 | ✅ 6 Tab |
| alert-rules.html | 下级页面 | ✅ 监控仪表盘高亮 | ✅ 返回仪表盘 | ✅ 6 Tab |

## 需求追溯矩阵 (FR → PD)

| FR 编号 | 需求摘要 | PD 页面 | 交互组件 | 覆盖状态 |
|---------|---------|---------|---------|---------|
| FR-030 | 实时监控仪表盘（QPS、延迟、准确率、路由分布、错误率） | index.html | Statistic 卡片 + 路由分布饼图 | ✅ 完整 |
| FR-031 | 按设备 ID 查看历史会话列表 | device-logs.html | 设备搜索 + 会话 Table | ✅ 完整 |
| FR-032 | 查看单个会话每轮请求的完整处理链路 | device-logs.html | 链路展开 Collapse + Timeline | ✅ 完整 |
| FR-034 | 请求日志多维筛选（时间/设备/路由/意图/耗时/异常） | index.html + device-logs.html | 多维筛选 Form | ✅ 完整 |
| FR-035 | 告警规则配置（准确率下降/延迟超标/错误率突增） | alert-rules.html | 规则 Table + 新建弹窗 | ✅ 完整 |
| FR-038 | 仪表盘数据 30s 自动轮询 + 手动刷新 | index.html | 倒计时 + 手动刷新按钮 | ✅ 完整 |

**范围外 FR**：

| FR 编号 | 需求摘要 | 状态 |
|---------|---------|------|
| FR-033 | API 结构化日志记录 | 🔲 属于 AD/DD |
| FR-036~037 | 安全与隐私 | 🔲 属于 DD |

---

**创建时间**: 2026-03-18
**最后更新**: 2026-03-18 (v1.0)
**基于模板**: pd-template.md v4.1
**PD 模块**: monitoring
**对应 spec.md**: v1.4 (FR-030~032, FR-034~035, FR-038)
