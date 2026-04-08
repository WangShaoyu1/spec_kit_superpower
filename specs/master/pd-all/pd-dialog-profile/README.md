# pd-dialog-profile: 对话方案管理交互原型

## 项目概述

本交互原型基于 `pd-template.md` v4.1 规范，完整实现对话方案管理模块的全链路交互设计（方案 CRUD → 指令库绑定 → 人设配置 → 手动测试 → 版本发布）。

**技术栈**: React 18 + Ant Design 6.x (CDN UMD, 无脚手架) + Babel Standalone + Dayjs

**对应规范**: `specs/master/spec.md` v1.4，覆盖 FR: FR-007~011, FR-015~016, FR-040, FR-047

**PD 模块 Key**: `dialog-profile`（参见 `specs/master/pd-all/pd-index.md`）

## 文件结构与页面层级

```
pd-dialog-profile/
├── index.html              # 对话方案列表页（主导航页面）
├── detail.html             # 对话方案详情/配置页（下级页面，从 index 进入）
├── test-chat.html          # 手动单条测试页（下级页面，从 detail 进入）
└── README.md
```

| 页面 | 类型 | 侧边栏菜单 | 返回按钮 | 说明抽屉 |
|------|------|-----------|---------|---------|
| index.html | 主导航页面 | ✅ 对话方案高亮 | 无 | ✅ 6 Tab |
| detail.html | 下级页面 | ✅ 对话方案高亮 | ✅ 返回列表 | ✅ 6 Tab |
| test-chat.html | 下级页面 | ✅ 对话方案高亮 | ✅ 返回详情 | ✅ 6 Tab |

**导航逻辑**：
```
index.html (方案列表) → 点击行 → detail.html (方案详情/配置)
detail.html (详情) → 点击手动测试 → test-chat.html (聊天测试)
detail.html (详情) → 点击平台级批量测试 → ../pd-batch-test/index.html (不同对话方案批量测试)
detail.html (详情) → 点击发布 → 发布确认弹窗 (含校验)
```

## 需求追溯矩阵 (FR → PD)

基于 `spec.md` v1.4 中对话方案相关的功能需求：

| FR 编号 | 需求摘要 | PD 页面 | 交互组件 | 覆盖状态 |
|---------|---------|---------|---------|---------|
| FR-007 | 创建和管理多个对话方案（大模型选型、人设、路由策略） | index.html + detail.html | Table + 新建弹窗 + 配置区 | ✅ 完整 |
| FR-008 | 闲聊人设自定义（助手名称、性格特征、语气风格） | detail.html | 人设管理卡片 + 人设编辑弹窗 | ✅ 完整 |
| FR-009 | 手动单条对话测试功能，会话隔离 | test-chat.html | 聊天窗口 + 会话列表 | ✅ 完整 |
| FR-010 | 手动测试展示完整调试信息（路由、意图、槽位、耗时） | test-chat.html | Debug 面板 + Collapse 展开 | ✅ 完整 |
| FR-011 | 手动测试支持模拟设备上下文 | test-chat.html | 设备上下文配置卡片 + 预设 | ✅ 完整 |
| FR-015 | 版本发布功能：方案打包为版本 | detail.html | 发布确认弹窗（版本对比 + 勾选 + 倒计时） | ✅ 完整 |
| FR-016 | 版本发布后设备立即切换，会话上下文重置 | detail.html | 发布弹窗影响说明 + 设备统计 | ✅ 完整 |
| FR-040 | 方案并行配置多个指令库 + 指令阈值 | detail.html | 指令库绑定多选 + 阈值 Slider | ✅ 完整 |
| FR-047 | 发布前校验指令库存在 published 模型 | detail.html | 发布门禁 Alert + 校验逻辑 | ✅ 完整 |

**范围外 FR（本次 PD 不覆盖）**：

| FR 编号 | 需求摘要 | 状态 |
|---------|---------|------|
| FR-012~014 | 平台级批量测试与智能分析（不同对话方案） | 🔲 属于 pd-batch-test |
| FR-017~029 | 对话管理 API（路由、NLU、会话管理） | 🔲 属于 AD/DD |
| FR-041 | 运行时语言检测 + 英文不回退中文 | 🔲 属于 API 设计 |

**跨模块引用**：

| 引用方向 | 说明 |
|---------|------|
| detail.html → pd-intent-library | FR-040: 绑定指令库，展示指令库名称、语种、published 状态 |
| detail.html → pd-batch-test | FR-012: 跳转平台级批量测试，用于不同对话方案的回归验证和横向比较 |
| pd-intent-library/detail.html → detail.html | FR-047: 方案发布门禁引用指令库 published 状态 |

## 页面能力清单

### index.html

- `page_goal`: 检索和管理所有对话方案，快速了解各方案的版本与发布状态
- `primary_user_flows`:
  - 点击新建方案 → 填写名称/LLM 模型/路由策略 → 提交 → 列表回读
  - 点击方案行 → 跳转 detail.html 进入配置详情
  - 筛选方案列表（按状态/名称）→ 定位目标方案

### detail.html

- `page_goal`: 完成对话方案的全部配置（指令库绑定、人设、阈值）并发布上线
- `primary_user_flows`:
  - 进入详情 → 绑定指令库(多选) → 配置指令阈值 Slider → 保存
  - 点击人设管理 → 新建/编辑人设(名称/性格/语气) → 激活 → 保存
  - 点击发布 → 门禁校验(指令库有 published 模型) → 版本对比 → 勾选确认 → 倒计时 → 发布成功
  - 点击手动测试 → 跳转 test-chat.html

### test-chat.html

- `page_goal`: 通过对话式交互验证对话方案的端到端效果（路由、意图、槽位、闲聊）
- `primary_user_flows`:
  - 新建会话 → 输入测试文本 → 发送 → 查看 Bot 回复 + Debug 面板(路由/意图/置信度/耗时)
  - 配置设备上下文(设备类型/型号/位置) → 发送同一文本 → 对比不同上下文下的路由结果
  - 切换会话 → 对比不同会话的回复质量

## 产出物合规检查表 (vs pd-template.md v4.1)

| 模板条款 | 状态 | 说明 |
|---------|------|------|
| §2.3 下级页面不在侧边栏 | ✅ | detail/test-chat 无独立菜单项 |
| §2.3 返回按钮与标题同行 | ✅ | detail/test-chat 返回按钮在标题左侧 |
| §2.4 每页有说明抽屉 | ✅ | 3 页均有"说明"按钮 + Drawer |
| §2.4 抽屉含 6 标签页 | ✅ | 数据流向/状态流转/字段说明/操作说明/业务逻辑/易错点 |
| §2.4 信息密度控制 | ✅ | 配置详情、字段说明等复杂内容在抽屉中 |
| §2.4 抽屉宽度切换 | ✅ | 3 页均有 800/1200 切换 |
| §3.1 CDN 使用 unpkg | ✅ | 全部使用 unpkg |
| §3.3 useCallback for Menu | ✅ | 3 页 handleOpenChange 均用 useCallback |
| §5.5 操作 CRUD 流程图 | ✅ | 新建/编辑/删除/发布 均有 Mermaid 流程图 |
| §5.3 数据绑定 1:N 标注 | ✅ | 方案-指令库 1:N、方案-人设 1:1 在抽屉标注 |
| §5.4 危险操作确认 | ✅ | 发布弹窗：版本对比 + 勾选 + 5s 倒计时 |
| §7.1 模块命名规范 | ✅ | pd-dialog-profile/ |
| §8 权限模型 | ✅ | 发布需 profile_publish 权限 + Tooltip |

## 业务价值

- **解决什么问题**：对话方案是平台核心抽象，连接指令库配置与生产 API 运行时
- **用户是谁**：产品经理（配置方案、测试效果、发布上线）
- **使用场景**：
  1. 创建多个方案 → 配置不同 LLM + 人设 → 手动测试对比效果 → 发布最佳方案
  2. 绑定中文+英文指令库 → 配置指令阈值 → 验证双语识别效果
  3. 修改闲聊人设 → 测试回复风格是否符合预期
- **成功标准**：PM 从创建方案到手动测试并发布，整个流程可在 1 小时内完成（SC-007）

## 技术约束

1. 无脚手架：纯 CDN 引入，无 build 步骤
2. 显式 window 访问：`const antd = window.antd; const icons = window.icons;`
3. 完整解构：所有使用的组件/图标都在顶部显式解构
4. Dayjs 前置：dayjs.min.js 在 antd.min.js 之前加载
5. Mock 数据：全部使用静态 mock 数据，无真实 API
6. CDN：全部使用 unpkg
7. useCallback：Menu 的 onOpenChange 使用 useCallback

## 查看方式

直接在浏览器打开任意 HTML 文件（如 `index.html`），或使用本地 HTTP 服务器：
```bash
python -m http.server 8080
# 访问 http://localhost:8080/specs/master/pd-all/pd-dialog-profile/index.html
```

---

**创建时间**: 2026-03-18
**最后更新**: 2026-03-18 (v1.0)
**基于模板**: pd-template.md v4.1
**PD 模块**: dialog-profile
**对应 spec.md**: v1.4 (FR-007~011, FR-015~016, FR-040, FR-047)
