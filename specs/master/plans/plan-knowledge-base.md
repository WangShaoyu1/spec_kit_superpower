# 实施计划: master / pd-knowledge-base

**分支**: `master` | **日期**: 2026-03-31 | **规范**: `specs/master/spec.md`
**输入**: `specs/master/` 下的 `spec.md + pd-all + ad/ + dd/`

## 摘要

在正式 `backend/ + frontend/` 单体工程中完成 `pd-knowledge-base` 模块，交付知识分类管理、文档上传、字段过滤、索引状态回读、文档详情与检索验证。实现策略采用 FastAPI + PostgreSQL 保存分类/文档/检索验证记录，以模块化后端路由延续当前骨架；前端采用 React + Ant Design 实现双栏分类/文档管理与详情页回读。

## Pre-flight 一致性扫描

| 检查项 | 结果 (OK/WARNING/BLOCKER) | 结论 / 处理动作 |
|--------|---------------------------|----------------|
| FR 在 spec / AD / DD 中是否存在冲突 | OK | `FR-004~006` 已收口到知识库模块职责 |
| PD 页面是否真实存在且被 AD 正确引用 | OK | `pd-knowledge-base` 的 `index/detail` 页面完整存在 |
| plan 使用的源码路径是否与当前工程一致 | OK | 唯一真相源仍为 `backend/ + frontend/` |
| PD 是否存在部分覆盖/待补充项 | OK | 本模块无条件准入项 |
| 关键外部依赖/异步链路是否定义真实成功信号 | OK | 上传、索引、详情回读、检索测试均定义了真实成功信号 |

## 技术背景

**语言/版本**: Python 3.10 + React 18  
**主要依赖**: FastAPI、SQLAlchemy、Pydantic Settings、React Router、Ant Design  
**存储**: PostgreSQL (`postgres:postgres@127.0.0.1:5432/smartchef`)  
**测试**: pytest、Vitest、browser smoke  
**目标平台**: Windows 本地研发环境，后续切换线上 PG  
**项目类型**: Web 应用（`backend/` + `frontend/`）  
**性能目标**: 文档详情与检索验证 p95 < 1500ms  
**约束条件**: 上传后必须先展示真实处理状态；过滤结果、索引版本、检索命中都必须来自后端回读  
**规模/范围**: 首版支持 `json` / `markdown` 文档，围绕菜谱知识、公司信息、产品指南三个分类

## 章程检查

- 文档链顺序固定：`spec -> PD -> AD -> DD -> plan -> tasks -> implement -> browser`
- `pd-intent-library` 已达到 `browser_verified`，满足本模块实现依赖
- 不允许用静态文案冒充上传成功、索引成功、过滤结果或检索命中
- 继续沿用“每个业务模块单独 router、`main.py` 只装配”的拆分规则

## 项目结构

### 设计文档（上游输入）

```
specs/master/
├── spec.md
├── pd-all/
│   └── pd-knowledge-base/
├── ad/
│   ├── README.md
│   ├── ad-global.md
│   └── ad-knowledge-base.md
├── dd/
│   ├── README.md
│   ├── dd-global.md
│   └── dd-knowledge-base.md
├── plans/
│   ├── README.md
│   └── plan-knowledge-base.md
└── tasks/
```

### 源代码

```
backend/
├── app/
│   ├── api/
│   ├── dependencies.py
│   ├── models.py
│   └── main.py
└── tests/

frontend/
├── src/
│   ├── app/
│   ├── modules/
│   │   └── knowledge-base/
│   └── services/
└── tests/
```

**结构决策**: 沿用已经完成的模块化后端结构，在 `backend/app/api/knowledge_base.py` 中实现知识库接口；前端新增 `modules/knowledge-base` 页面，并复用统一菜单壳与 API 客户端。

## 阶段规划

### 阶段 1: 文档链补齐与 gate 对齐
**目标**: 补齐 `ad-knowledge-base.md`、`dd-knowledge-base.md`、`plans/plan-knowledge-base.md`、`tasks-knowledge-base.md`  
**检查点**: `ad/dd/tasks` gate 无 blocker

### 阶段 2: 后端核心闭环
**目标**: 实现分类、文档上传、字段过滤、状态机、详情与检索验证接口  
**检查点**: 契约测试覆盖分类 CRUD、上传、详情、重新索引、检索测试

### 阶段 3: 前端模块接入
**目标**: 实现知识库列表页、详情页、上传弹窗、检索测试入口  
**检查点**: 登录后可进入 `/knowledge-base` 并完成主链路操作

### 阶段 4: 模块验证与收口
**目标**: 完成 browser stage、修复缺陷并推进到 `browser_verified`  
**检查点**: `upload_feedback`、`indexing_result_readback`、`empty_state` 均通过 smoke

## 模块核心业务链路

| 模块 | 链路名称 | 起点 | 终点/真实成功信号 | 覆盖方式 |
|------|---------|------|------------------|---------|
| `pd-knowledge-base` | 创建分类 | PM 提交新建分类弹窗 | 左侧分类列表新增记录，统计卡回读更新 | contract + UI test + smoke |
| `pd-knowledge-base` | 上传并索引文档 | PM 选择分类并上传文档 | 文档经历 `uploading -> parsing -> indexing -> ready` 真正变化 | contract + integration + smoke |
| `pd-knowledge-base` | 字段过滤回读 | PM 打开文档详情 | 有效字段、过滤字段、索引版本与详情回读一致 | contract + UI test + smoke |
| `pd-knowledge-base` | 检索验证 | 详情页输入查询 | 返回命中/未命中结果、分数、片段和响应预览 | contract + smoke |

## 显式未完成声明

- **Deferred**: 批量文件压缩包导入、真正的向量数据库接入、复杂 Markdown chunk 策略
- **Stub / 需要 501 的能力**: 无
- **Out of Scope**: 对话方案中的知识库绑定、运行时知识路由、开放闲聊兜底
- **Blocked By**: 无
- **路径单一真相源**: `backend/ + frontend/`

## 测试策略

| 测试类型 | 时机 | 覆盖目标 | 工具 |
|---------|------|---------|------|
| 契约测试 | API 完成后 | 分类 CRUD、上传、详情、重新索引、检索测试 | pytest + TestClient |
| 集成测试 | 后端闭环完成时 | 状态机、分类统计联动、索引版本递增 | pytest |
| 消费契约测试 | 前端联调前 | 列表、详情、过滤结果、检索结果形态 | Vitest |
| Browser smoke | 页面接近完成时 | `upload_feedback`、`indexing_result_readback`、`empty_state` | browser automation |

## 风险与缓解

| 风险类型 | 描述 | 缓解策略 |
|---------|------|---------|
| 技术风险 | 上传后容易被做成前端假成功 | 所有状态以后端回读为准，browser 检查完整状态链路 |
| 过滤风险 | FR-005 规则误伤有效字段 | 详情页同时展示有效字段与过滤字段，支持重新索引复核 |
| 进度风险 | 列表/详情/上传/检索点位较多 | 先打通分类→上传→详情→检索主闭环，再补 UI 细节 |
| 假成功风险 | 检索测试返回硬编码命中结果 | 所有命中片段、分数与预览都来自后端接口 |
