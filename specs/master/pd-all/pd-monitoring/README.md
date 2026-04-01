# pd-monitoring: 监控仪表盘交互原型

## 项目概述

本交互原型基于 `pd-template.md` v4.1 规范，完整实现监控仪表盘模块的全链路交互设计（实时指标 → 设备日志 → 会话链路 → 告警规则）。

**技术栈**: React 18 + Ant Design 6.x (CDN UMD, 无脚手架) + Babel Standalone + Dayjs

**对应规范**: `specs/master/spec.md` v1.4，覆盖 FR: FR-030~032, FR-034~035, FR-038

**PD 模块 Key**: `monitoring`（参见 `specs/master/pd-all/pd-index.md`）

## 模块定位

- 本模块用于运行态质量、链路和告警的统一观测
- 本模块关注被观测对象是“请求、设备、会话、告警规则”，不是配置型业务实体
- 本模块是发布后验证和问题排查的主入口

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

## 导航逻辑

```
index.html (监控总览) → 点击设备 / 会话 → device-logs.html (链路排查)
index.html (监控总览) → 点击告警规则 → alert-rules.html (规则配置)
```

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

**跨模块引用**：

| 引用方向 | 说明 |
|---------|------|
| 其他业务模块 → index.html | 发布后统一进入监控总览查看运行质量和异常趋势 |
| index.html → device-logs.html | 从指标或设备入口进入请求链路排查 |
| index.html → alert-rules.html | 从监控总览进入告警规则配置 |

## 产出物合规检查表 (vs pd-template.md v4.1)

| 模板条款 | 状态 | 说明 |
|---------|------|------|
| §2.3 下级页面不在侧边栏 | ✅ | device-logs/alert-rules 无独立一级菜单 |
| §2.3 返回按钮与标题同行 | ✅ | 两个下级页面均从标题区返回 |
| §2.4 每页有说明抽屉 | ✅ | 3 页均有"说明"按钮 + Drawer |
| §2.4 抽屉含 6 标签页 | ✅ | 数据流向/状态流转/字段说明/操作说明/业务逻辑/易错点 |
| §2.4 抽屉宽度切换 | ✅ | 3 页均支持 800/1200 切换 |
| §3.1 CDN 使用 unpkg | ✅ | 全部使用 unpkg |
| §3.3 useCallback for Menu | ✅ | handleOpenChange 使用 useCallback |
| §5.5 操作/排查流程图 | ✅ | 监控排查、规则配置等关键流程已在抽屉表达 |

## 业务价值

- **解决什么问题**：把线上运行质量、异常定位和告警治理集中在同一入口，避免发布后“看不见、查不清、反应慢”
- **用户是谁**：产品经理、测试人员、运维/研发排障人员
- **使用场景**：
  1. 观察 QPS、延迟、准确率和错误率的整体趋势
  2. 按设备 ID 回查历史会话，查看单轮请求处理链路
  3. 配置准确率下降、延迟超标、错误率突增的告警规则
- **成功标准**：出现质量异常时，团队可从仪表盘快速定位到具体设备和请求链路

## 技术约束

1. 无脚手架：纯 CDN 引入，无 build 步骤
2. 显式 window 访问：`const antd = window.antd; const icons = window.icons;`
3. 完整解构：所有使用的组件/图标都在顶部显式解构
4. Mock 数据：全部使用静态 mock 数据，无真实 API
5. 仪表盘自动刷新、链路展开和告警规则均以演示状态流转为主，不宣称真实监控后端已闭环

## 查看方式

直接在浏览器打开任意 HTML 文件（如 `index.html`），或使用本地 HTTP 服务器：
```bash
python -m http.server 8080
# 访问 http://localhost:8080/specs/master/pd-all/pd-monitoring/index.html
```

---

**创建时间**: 2026-03-18
**最后更新**: 2026-03-18 (v1.0)
**基于模板**: pd-template.md v4.1
**PD 模块**: monitoring
**对应 spec.md**: v1.4 (FR-030~032, FR-034~035, FR-038)
