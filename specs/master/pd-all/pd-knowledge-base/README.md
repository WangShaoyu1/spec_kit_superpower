# pd-knowledge-base: 知识库管理交互原型

## 项目概述

本交互原型基于 `pd-template.md` v4.1 规范，完整实现知识库管理模块的全链路交互设计（知识库分类管理 → 文档上传/解析 → 索引建立 → 检索验证）。

**技术栈**: React 18 + Ant Design 6.x (CDN UMD, 无脚手架) + Babel Standalone + Dayjs

**对应规范**: `specs/master/spec.md` v1.4，覆盖 FR: FR-004, FR-005, FR-006

**PD 模块 Key**: `knowledge-base`（参见 `specs/master/pd-all/pd-index.md`）

## 模块定位

- 本模块用于知识文档、分类和检索验证的统一管理
- 本模块关注被管理对象是“知识文档及其索引结果”，不是对话方案或指令配置
- 本模块是知识问答链路进入研发实现前的产品入口

## 文件结构与页面层级

```
pd-knowledge-base/
├── index.html              # 知识库管理页（主导航页面，左栏分类+右栏文档）
├── detail.html             # 文档详情页（下级页面，文档内容预览+检索测试）
└── README.md
```

| 页面 | 类型 | 侧边栏菜单 | 返回按钮 | 说明抽屉 |
|------|------|-----------|---------|---------|
| index.html | 主导航页面 | ✅ 知识库管理高亮 | 无 | ✅ 6 Tab |
| detail.html | 下级页面 | ✅ 知识库管理高亮 | ✅ 返回列表 | ✅ 6 Tab |

**导航逻辑**：
```
index.html (知识库列表) → 点击文档行 → detail.html (文档详情/检索测试)
```

## 需求追溯矩阵 (FR → PD)

| FR 编号 | 需求摘要 | PD 页面 | 交互组件 | 覆盖状态 |
|---------|---------|---------|---------|---------|
| FR-004 | 知识库文档上传（JSON/Markdown），自动解析建立索引 | index.html | 上传弹窗 Dragger + 解析进度 | ✅ 完整 |
| FR-005 | 自动过滤无效字段（图片URL、OSS链接、点赞数等） | index.html + detail.html | 解析结果 Alert + 过滤字段对比 | ✅ 完整 |
| FR-006 | 知识库分类管理（菜谱、公司信息、产品指南） | index.html | 左栏分类列表 + 新建分类弹窗 | ✅ 完整 |

**范围外 FR**：

| FR 编号 | 需求摘要 | 状态 |
|---------|---------|------|
| FR-021 | 知识域检索匹配（API 层） | 🔲 属于 AD/DD |
| FR-007 | 对话方案引用知识库 | 🔗 跨模块: pd-dialog-profile |

**跨模块引用**：

| 引用方向 | 说明 |
|---------|------|
| pd-dialog-profile/detail.html → index.html | 对话方案配置时需要引用知识库能力与分类信息 |
| index.html → detail.html | 从文档列表进入文档详情与检索验证 |

## 产出物合规检查表 (vs pd-template.md v4.1)

| 模板条款 | 状态 | 说明 |
|---------|------|------|
| §2.3 下级页面不在侧边栏 | ✅ | detail 无独立菜单项 |
| §2.3 返回按钮与标题同行 | ✅ | detail 返回按钮在标题左侧 |
| §2.4 每页有说明抽屉 | ✅ | 2 页均有"说明"按钮 + Drawer |
| §2.4 抽屉含 6 标签页 | ✅ | 数据流向/状态流转/字段说明/操作说明/业务逻辑/易错点 |
| §2.4 抽屉宽度切换 | ✅ | 2 页均有 800/1200 切换 |
| §3.1 CDN 使用 unpkg | ✅ | 全部使用 unpkg |
| §3.3 useCallback for Menu | ✅ | handleOpenChange 均用 useCallback |
| §5.5 操作 CRUD 流程图 | ✅ | 新建分类/上传文档/删除文档 均有 Mermaid 流程图 |
| §5.4 危险操作确认 | ✅ | 删除分类、删除文档有确认弹窗 |
| §7.1 模块命名规范 | ✅ | pd-knowledge-base/ |

## 业务价值

- **解决什么问题**：知识库是知识问答能力的数据基础，菜谱数据已就绪需要管理入口
- **用户是谁**：产品经理（上传管理知识库文档、验证检索效果）
- **使用场景**：
  1. 创建分类 → 上传菜谱 JSON → 系统自动解析过滤 → 验证检索结果
  2. 上传公司信息文档 → 归类管理 → 确认索引质量
- **成功标准**：文档上传后可被知识问答检索命中

## 技术约束

1. 无脚手架：纯 CDN 引入，无 build 步骤
2. 显式 window 访问：`const antd = window.antd; const icons = window.icons;`
3. 完整解构：所有使用的组件/图标都在顶部显式解构
4. Mock 数据：全部使用静态 mock 数据，无真实 API
5. 文档上传、解析和检索验证在原型层只表达交互链路，不宣称真实索引后端已闭环

## 查看方式

直接在浏览器打开任意 HTML 文件（如 `index.html`），或使用本地 HTTP 服务器：
```bash
python -m http.server 8080
# 访问 http://localhost:8080/specs/master/pd-all/pd-knowledge-base/index.html
```

---

**创建时间**: 2026-03-18
**最后更新**: 2026-03-18 (v1.0)
**基于模板**: pd-template.md v4.1
**PD 模块**: knowledge-base
**对应 spec.md**: v1.4 (FR-004, FR-005, FR-006)
