# 实施计划: master / pd-batch-test

**分支**: `master` | **日期**: 2026-03-31 | **规范**: `specs/master/spec.md`
**输入**: `specs/master/` 下的 `spec.md + pd-all + ad/ + dd/`

## 摘要

在正式 `backend/ + frontend/` 单体工程中完成 `pd-batch-test` 模块，交付平台级对话方案批量测试入口、用例生成/导入、执行结果、达标判断与智能分析报告。实现策略采用 FastAPI + PostgreSQL 保存批次、用例、结果与分析记录；前端采用 React + Ant Design 实现批次目录和结果详情页，并确保所有数量、准确率、耗时与分析建议都来自后端回读。

## Pre-flight 一致性扫描

| 检查项 | 结果 (OK/WARNING/BLOCKER) | 结论 / 处理动作 |
|--------|---------------------------|----------------|
| FR 在 spec / AD / DD 中是否存在冲突 | OK | `FR-012~014` 已收口到方案级批量测试模块 |
| PD 页面是否真实存在且被 AD 正确引用 | OK | `pd-batch-test` 的 `index/detail` 页面完整存在 |
| plan 使用的源码路径是否与当前工程一致 | OK | 唯一真相源仍为 `backend/ + frontend/` |
| PD 是否存在部分覆盖/待补充项 | OK | 本模块定位清晰，不与指令库内评估混用 |
| 关键外部依赖/异步链路是否定义真实成功信号 | OK | 用例数量、执行状态、准确率、耗时与分析都定义了真实成功信号 |

## 技术背景

**语言/版本**: Python 3.10 + React 18  
**主要依赖**: FastAPI、SQLAlchemy、Pydantic Settings、React Router、Ant Design  
**存储**: PostgreSQL (`postgres:postgres@127.0.0.1:5432/smartchef`)  
**测试**: pytest、Vitest、browser smoke  
**目标平台**: Windows 本地研发环境，后续切换线上 PG  
**项目类型**: Web 应用（`backend/` + `frontend/`）  
**性能目标**: 单批次 200 条用例结果页可在 2 秒内完成回读，指标摘要展示完整  
**约束条件**: 评测对象固定为 dialog profile；不允许前端硬编码准确率、耗时、混淆矩阵或建议  
**规模/范围**: 首版支持单方案批次创建、自动生成用例、执行批次、查看报告与基础智能分析

## 章程检查

- 文档链顺序固定：`spec -> PD -> AD -> DD -> plan -> tasks -> implement -> browser`
- `pd-dialog-profile` 已达到 `browser_verified`，满足本模块实现依赖
- 不允许用静态文案冒充执行成功、准确率达标、分析完成
- 继续沿用“每个业务模块单独 router、`main.py` 只装配”的拆分规则

## 项目结构

### 设计文档（上游输入）

```
specs/master/
├── spec.md
├── pd-all/
│   └── pd-batch-test/
├── ad/
│   ├── README.md
│   ├── ad-global.md
│   └── ad-batch-test.md
├── dd/
│   ├── README.md
│   ├── dd-global.md
│   └── dd-batch-test.md
├── plans/
│   ├── README.md
│   └── plan-batch-test.md
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
│   │   └── batch-test/
│   └── services/
└── tests/
```

**结构决策**: 在 `backend/app/api/batch_test.py` 中实现批量测试接口；前端新增 `modules/batch-test` 页面，并复用 dialog profile 的测试/trace 能力做批次执行模拟。

## 阶段规划

### 阶段 1: 文档链补齐与 gate 对齐
**目标**: 补齐 `ad-batch-test.md`、`dd-batch-test.md`、`plans/plan-batch-test.md`、`tasks-batch-test.md`  
**检查点**: `ad/dd/tasks` gate 无 blocker

### 阶段 2: 后端核心闭环
**目标**: 实现批次目录、用例生成、执行引擎、结果聚合与分析接口  
**检查点**: 契约测试覆盖批次创建、生成用例、执行、详情回读

### 阶段 3: 前端模块接入
**目标**: 实现批次列表页、详情结果页、执行与分析展示  
**检查点**: 登录后可进入 `/batch-test` 并完成建批、执行、看报告主链路

### 阶段 4: 模块验证与收口
**目标**: 完成 browser stage、修复缺陷并推进到 `browser_verified`  
**检查点**: `case_count_consistency`、`latency_feedback`、`accuracy_feedback` 均通过 smoke

## 模块核心业务链路

| 模块 | 链路名称 | 起点 | 终点/真实成功信号 | 覆盖方式 |
|------|---------|------|------------------|---------|
| `pd-batch-test` | 创建批次并生成用例 | PM 新建批次后点击生成 | 批次状态变为 `ready`，case_count 回读一致 | contract + UI test + smoke |
| `pd-batch-test` | 执行批次 | 详情页点击执行 | 批次经历 `ready -> running -> completed/failed` 真正变化 | contract + integration + smoke |
| `pd-batch-test` | 查看报告与分析 | 执行完成后打开详情 | 准确率、p95、结果表、混淆矩阵、建议都来自后端回读 | contract + UI test + smoke |

## 显式未完成声明

- **Deferred**: 批量上传压缩包、跨批次趋势对比、真实 LLM 归因分析
- **Stub / 需要 501 的能力**: 无
- **Out of Scope**: 生产压测、线上流量回放、监控告警联动
- **Blocked By**: 无
- **路径单一真相源**: `backend/ + frontend/`

## 测试策略

| 测试类型 | 时机 | 覆盖目标 | 工具 |
|---------|------|---------|------|
| 契约测试 | API 完成后 | 批次创建、生成用例、执行、详情结果与分析 | pytest + TestClient |
| 集成测试 | 后端闭环完成时 | 批次状态机、结果数量、指标聚合、分析回写 | pytest |
| 消费契约测试 | 前端联调前 | 列表、详情、结果表、分析报告字段形态 | Vitest |
| Browser smoke | 页面接近完成时 | `case_count_consistency`、`latency_feedback`、`accuracy_feedback` | browser automation |

## 风险与缓解

| 风险类型 | 描述 | 缓解策略 |
|---------|------|---------|
| 技术风险 | 批次执行容易被简化成只改状态不产出真实结果 | 逐条结果必须落库并在详情页回读 |
| 指标风险 | 准确率/耗时被前端聚合或硬编码 | 统一由后端聚合并返回 |
| 进度风险 | 列表、结果、分析三个区域点位多 | 先打通建批→执行→报告主闭环，再补报告细节 |
| 假成功风险 | 未达标仍显示通过 | 后端统一基于阈值快照计算 pass/fail 与 analysis_status |
