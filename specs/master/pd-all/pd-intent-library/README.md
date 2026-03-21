# pd-intent-library: 指令库管理交互原型

## 项目概述

本交互原型基于 `pd-template.md` v4.0 规范，完整实现指令库管理模块的全链路交互设计（指令库 CRUD → 模型训练 → 评估 → 测试 → 发布）。

**技术栈**: React 18 + Ant Design 6.x (CDN UMD, 无脚手架) + Babel Standalone + Dayjs

**对应规范**: `specs/master/spec.md` v1.4，覆盖 FR: FR-002, FR-003, FR-039~FR-054

**PD 模块 Key**: `intent-library`（参见 `specs/master/pd-index.md`）

## 文件结构与页面层级

```
pd-intent-library/
├── index.html              # 指令库列表页（主导航页面）
├── detail.html             # 指令库详情页（下级页面，从 index 进入）
├── datasets.html           # 数据集管理页（主导航页面）
├── dataset-detail.html     # 数据集数据管理页（下级页面，从 datasets 进入）
├── test.html               # 模型测试页（下级页面，含单条测试对话+批量测试两个Tab）
└── README.md
```

| 页面 | 类型 | 侧边栏菜单 | 返回按钮 | 说明抽屉 |
|------|------|-----------|---------|---------|
| index.html | 主导航页面 | ✅ 指令库管理高亮 | 无 | ✅ 6 Tab |
| detail.html | 下级页面 | ✅ 指令库管理高亮 | ✅ 返回列表 | ✅ 6 Tab |
| datasets.html | 主导航页面 | ✅ 数据集管理高亮 | 无 | ✅ 含 LLM 合成说明 |
| dataset-detail.html | 下级页面 | ✅ 数据集管理高亮 | ✅ 返回数据集列表 | ✅ 3 Tab（数据模型/批量导入/易错点） |
| test.html | 下级页面 | ✅ 指令库管理高亮 | ✅ 返回详情 | ✅ 含单条/批量操作说明 |

**导航逻辑**：
```
index.html (列表) → 点击行 → detail.html (详情)
detail.html (详情) → 点击测试 → test.html (模型测试: 单条对话 + 批量评估)
detail.html (详情) → 点击数据集 → datasets.html (数据集)
datasets.html (数据集列表) → 点击管理数据 → dataset-detail.html (意图数据管理)
```

## 需求追溯矩阵 (FR → PD)

基于 `spec.md` v1.3 中 D016 相关的功能需求：

| FR 编号 | 需求摘要 | PD 页面 | 交互组件 | 覆盖状态 |
|---------|---------|---------|---------|---------|
| FR-039 | 指令库管理，library_key 全局唯一不可改 | index.html | Table + 新建弹窗(Key 字段) | ✅ 完整 |
| FR-043 | 单库模型上限 5 | index.html | Progress 进度条 + Alert | ✅ 完整 |
| FR-043 | 超限禁止新建训练 | detail.html | 训练弹窗 Alert 提示 | ✅ 完整 |
| FR-044 | 模型状态机 draft→...→published | detail.html | G6 状态机 + Tag 状态条 + 规则列表 | ✅ 完整 |
| FR-045 | testable/published 各库唯一 | detail.html | 抽屉规则 Alert + 自动取消逻辑 | ✅ 完整 |
| FR-046 | 允许同时持有 testable+published | detail.html | 抽屉规则说明 | ✅ 完整 |
| FR-047 | 方案发布需库存在 published 模型 | detail.html | 发布门禁逻辑说明 | ✅ 完整 |
| FR-048 | 训练集 1:1、评估集非 1:1 | datasets.html | Tag 展示绑定状态 + Alert 说明 | ✅ 完整 |
| FR-049 | 训练集最小字段 / 评估集全字段 | datasets.html + dataset-detail.html | 导入弹窗 Tab 切换 + 意图数据 CRUD（实体/话术/追问） | ✅ 完整 |
| FR-050 | 阈值"库级默认 + 任务级覆盖" | test.html | 新建任务弹窗 InputNumber | ⚠️ 部分（未展示继承逻辑） |
| FR-051 | 测试入口：单条+批量 | test.html | Tab切换: 单条对话式测试 + 批量评估任务列表 | ✅ 完整 |
| FR-052 | 智能分析（结论/混淆/槽位/低分/建议） | test.html | Collapse 面板 + 分析报告弹窗 | ✅ 完整 |
| FR-053 | model_publish / model_test_manage 权限 | index.html + detail.html | 权限函数 + Tooltip 禁用 | ✅ 完整 |
| FR-054 | 模型产物平台无关下载 | detail.html | 下载模型按钮 + 操作说明流程 | ✅ 完整 |

**范围外 FR（本次 PD 不覆盖）**：

| FR 编号 | 需求摘要 | 状态 |
|---------|---------|------|
| FR-040 | 对话方案并行配置多个指令库 + 指令阈值 | 🔲 属于对话方案 PD |
| FR-041 | 运行时语言检测 + 英文不回退中文 | 🔲 属于 API 设计 |
| FR-042 | 存量迁移策略 | 🔲 属于运维设计 |

## 产出物合规检查表 (vs pd-template.md v3.0)

| 模板条款 | 状态 | 说明 |
|---------|------|------|
| §2.3 下级页面不在侧边栏 | ✅ | detail/test/dataset-detail 无独立菜单项 |
| §2.3 返回按钮与标题同行 | ✅ | detail/test/dataset-detail 返回按钮在标题左侧 |
| §2.4 每页有说明抽屉 | ✅ | 5 页均有"说明"按钮 + Drawer |
| §2.4 抽屉含标签页 | ✅ | index: 6 Tab, detail: 6 Tab, datasets: 4 Tab, dataset-detail: 5 Tab, test: 5 Tab |
| §2.4 信息密度控制 | ✅ | G6 状态机、字段说明等复杂内容在抽屉中 |
| §2.4 抽屉宽度切换 | ✅ | 5 页均有 800/1200 切换 |
| §3.1 CDN 使用 unpkg | ✅ | 全部使用 unpkg |
| §3.3 useCallback for Menu | ✅ | 5 页 handleOpenChange 均用 useCallback |
| §5.5 操作 CRUD 流程图 | ✅ | index 抽屉含编辑/删除流程图，detail 含发布/下载流程图，test 含单条/批量操作流程图 |
| §5.3 数据绑定 1:1/1:N 标注 | ✅ | 训练集 1:1、评估集 1:N 在抽屉 + Alert 中标注 |
| §5.4 危险操作确认 | ✅ | 发布弹窗：版本对比 + 勾选 + 5s 倒计时 |
| §6.3 数据集导入区分类型 | ✅ | 独立按钮 + Radio 切换 + 格式 Tab |
| §8 权限模型 | ✅ | 权限函数 + Tooltip 禁用 + 删除约束 |
| §9 异常处理 | ✅ | 网络检测 + 重试弹窗 + 随机失败模拟 |

## 业务价值

- **解决什么问题**：指令库缺少从 0→1 的完整链路（D016 缺陷），导致配置了指令库也不会生效
- **用户是谁**：产品经理（配置训练）、算法工程师（评估模型）、测试人员（验证质量）
- **使用场景**：
  1. 导入训练数据 → 创建训练任务 → 评估模型 → 发布上线
  2. 使用 LLM 合成数据扩充训练集
  3. 批量评估后查看智能分析报告，定向优化
- **成功标准**：形成"数据→训练→评估→发布→生效"的完整闭环

## 改进历程

**v3.3 (2026-03-16) — 术语修正 + 批量导入**：
1. ✅ 术语修正："命中/未命中话术"明确为系统回复（在意图配置抽屉中），"相似问/排除问"为训练数据（独立抽屉管理）
2. ✅ 意图配置抽屉增加"命中话术"和"未命中话术"字段（系统返回给用户的回复，支持 {slot} 变量替换）
3. ✅ 话术管理抽屉改名为"相似问管理"，Tab 改为"相似问（正样本）"和"排除问（负样本/反例）"
4. ✅ 自定义词槽编辑增加"批量导入"功能：支持 Excel (.xlsx) 和文本文件 (.txt/.csv) 两种导入方式
5. ✅ 新增 Excel 模板下载功能：两列 entity_value + synonyms，标准化导入格式
6. ✅ 文本导入支持直接粘贴：一行一个实体，逗号分隔同义词
7. ✅ 说明抽屉增加"批量导入"Tab，含导入方式对比表和模板说明

**v3.2 (2026-03-16) — 数据集数据管理页面**：
1. ✅ 新增 dataset-detail.html：数据集内意图数据的完整管理页面
2. ✅ 意图定义 CRUD：英文标识(intent_key)、中文名、描述、词槽引用(Slots)、追问配置
3. ✅ 词槽与实体管理：系统词槽只读、自定义词槽 CRUD，含实体值和同义词管理
4. ✅ 意图配置改为抽屉交互；相似问独立抽屉管理
5. ✅ datasets.html "管理数据"按钮改为跳转 dataset-detail.html
6. ✅ datasets.html LLM 弹窗增加提示词模板编辑 + 说明改 Tooltip

**v3.1 (2026-03-16) — 测试页面交互重构**：
1. ✅ 测试入口重构：detail.html "测试"按钮从弹窗改为跳转 test.html
2. ✅ 测试页面重构：test.html 由纯批量测试改为"单条测试 + 批量测试"双 Tab 页面
3. ✅ 单条测试对话式交互：标准聊天窗口，支持多会话管理、历史消息滚动、删除消息/会话、清空全部
4. ✅ Debug 面板：每条机器人回复下方展示意图/置信度/槽位/耗时，置信度颜色编码
5. ✅ 会话列表：左侧面板展示所有会话，支持新建/切换/删除，hover 显示删除按钮

**v3.0 (2026-03-16) — 模板 v3.0 对齐**：
1. ✅ 侧边栏精简：移除"意图管理"、"模型版本"、"训练任务"、"单条测试"、"批量评估"等非独立模块菜单
2. ✅ 返回按钮修正：test.html 返回按钮从独立行移到标题同行
3. ✅ 操作流程图：index 抽屉增加编辑/删除 ASCII 流程图，detail 增加发布/测试/下载流程图
4. ✅ 模型下载：detail.html 增加"下载模型"按钮（FR-054 覆盖）
5. ✅ 操作说明 Tab：detail 和 test 抽屉补充操作说明标签页
6. ✅ 权限实调：index.html 编辑/删除按钮实际调用权限函数 + Tooltip 提示
7. ✅ 评估集字段：datasets.html 导入弹窗补全 actual_score + language + source
8. ✅ README：新增 FR 映射矩阵 + 合规检查表

**v2.0 (2026-03-13) — 初始版本**：
1. ✅ 菜单展开问题修复（useCallback）
2. ✅ 数据流向移至抽屉
3. ✅ 抽屉宽度切换
4. ✅ 测试按钮响应
5. ✅ 中文引号语法修复
6. ✅ CDN 全部改用 unpkg

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
# 访问 http://localhost:8080/specs/master/pd-D016-react/index.html
```

---

**创建时间**: 2026-03-13
**最后更新**: 2026-03-16 (v3.3 术语修正 + 批量导入)
**基于模板**: pd-template.md v4.0
**PD 模块**: intent-library
**对应 spec.md**: v1.4 (FR-002, FR-003, FR-039~FR-054)
