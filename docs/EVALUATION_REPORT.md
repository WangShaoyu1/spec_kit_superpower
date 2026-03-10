# SmartChef 项目全方位评价 — 可执行报告

**文档版本**: 1.0  
**评价基准**: Spec-Kit 规范（`specs/master/spec.md`、`plan.md`、`tasks.md`）、`temp_data/config.json`  
**目标**: 从需求匹配、代码质量、测试覆盖、用户路径覆盖、性能指标等维度给出可执行步骤与验收标准，并产出**实际数据**证明完成度与性能。

---

## 一、评价维度总览

| 维度 | 说明 | 产出物 |
|------|------|--------|
| **1. 需求匹配** | FR/SC/用户故事与实现逐条核对 | 需求追溯矩阵 + 缺口清单 |
| **2. 代码质量** | 静态检查、结构规范、安全项 | 检查报告 + 问题清单 |
| **3. 测试用例覆盖** | 单元/集成/合约/E2E 覆盖度与通过率 | 覆盖率报告 + 用例清单 |
| **4. 用户操作路径覆盖** | 10 个用户故事端到端路径验证 | 路径检查表 + 截图/日志 |
| **5. 性能指标** | 延迟、准确率、QPS 等可测量数据 | 性能数据表 + 脚本复现方式 |

---

## 二、前置条件与注意事项

### 2.1 环境要求

- **后端**: Python 3.11+，PostgreSQL 16+，Redis 7+，已执行 `alembic upgrade head` 与 `python -m app.scripts.init_db`
- **前端**: Node 18+，依赖已安装
- **可选**: ZenMux API Key、Brave Search API Key（用于闲聊/联网与部分集成测试）
- **参考**: `specs/master/quickstart.md`、`smartchef-platform/README.md`

### 2.2 注意事项（必读）

1. **性能数据必须真实采集**：延迟、准确率、QPS 等需在真实或准生产环境运行脚本/测试得到，禁止手填估计值。
2. **需求匹配以 spec.md 为准**：FR-001～FR-038、SC-001～SC-013、用户故事 US1～US10 的验收场景为唯一验收依据。
3. **意图基准以 config.json 为准**：`temp_data/config.json` 中的 `intents` 约 39 个功能为指令覆盖范围，评价时需核对实现是否支持全部意图配置与识别。
4. **任务完成度以 tasks.md 为准**：145 条任务（T001～T145）的勾选状态与代码/测试一一对应，未实现项需在缺口清单中列出。
5. **测试需在清洁环境执行**：集成/E2E 前确保数据库迁移最新、Redis 无脏数据；合约测试可 mock 外部依赖。
6. **前端路径需人工或 E2E 验证**：部分用户路径（如「创建方案→手动测试→发布」）需浏览器或 Playwright 等 E2E 执行并记录结果。
7. **设备端 C++ 推理为可选**：V1 可不实现 `device-inference/`，但需在报告中说明；SC-010（Jetson Nano 运行）可标为「未验证」或「N/A」。

---

## 三、维度 1：需求匹配评价

### 3.1 执行步骤

#### 步骤 1.1：功能需求（FR）追溯

- **输入**: `specs/master/spec.md` 第 186～257 行（功能需求 FR-001～FR-038）。
- **操作**: 对每条 FR，在代码库中定位对应实现（API 路由、服务、前端页面），并填写下表（示例）。

| FR 编号 | 描述摘要 | 实现位置（后端/前端） | 状态：实现/部分/未实现 |
|---------|----------|------------------------|-------------------------|
| FR-001  | 角色权限管理、管理员账号 | `app/api/v1/auth.py`、`app/services/auth_service.py`、前端 UserManager | 待填写 |
| FR-002  | 指令增删改查、槽位定义 | `app/api/v1/intents.py`、`app/models/intent.py`、IntentManager 页面 | 待填写 |
| …       | …        | … | … |

- **产出**: 需求追溯矩阵（建议 `docs/requirement_traceability.md`），并汇总「未实现」「部分实现」清单。

#### 步骤 1.2：成功标准（SC）核对

- **输入**: `specs/master/spec.md` 第 259～273 行（SC-001～SC-013）。
- **操作**: 对每条 SC，判断是否有**可执行的验证方式**（测试、脚本、监控数据），并记录实际数据或「待测」。

| SC 编号 | 成功标准摘要 | 验证方式 | 实际数据/结果 |
|---------|--------------|----------|----------------|
| SC-001  | 指令意图识别准确率 ≥ 95%，覆盖 39 个意图 | 批量测试或评估脚本 + 报告 | 待运行后填写 |
| SC-002  | 指令类响应延迟 &lt; 200ms（P95） | 压测或集成测试打点 | 待运行后填写 |
| SC-003  | 知识/闲聊响应 2～4s | 集成测试或手工抽样 | 待运行后填写 |
| SC-007  | PM 全流程 1 小时内完成 | E2E 测试 `tests/e2e/test_pm_workflow.py` 或 quickstart_verify | 待运行后填写 |
| SC-010  | 小模型 Jetson Nano 运行 | 设备端 C++ 模块（可选） | N/A 或待验证 |
| …       | … | … | … |

- **产出**: SC 验证表，含实际数据列（见维度 5 性能部分）。

#### 步骤 1.3：用户故事验收场景

- **输入**: `specs/master/spec.md` 用户故事 1～10，每个故事下的「验收场景」（Given-When-Then）。
- **操作**: 为每个验收场景指定对应测试用例或手动步骤（如 E2E、合约测试名、或操作清单）。

| 用户故事 | 验收场景摘要 | 对应测试/验证方式 |
|----------|--------------|--------------------|
| US1      | 创建指令「设置烹饪时间」、槽位 duration | 合约 test_intents_api / 手动 |
| US1      | 编辑「启动烹饪」提示词/训练数据 | 合约 test_training_data_api |
| …        | … | … |

- **产出**: 用户故事验收映射表；未覆盖的验收场景列入缺口。

#### 步骤 1.4：意图覆盖（39 个功能）

- **输入**: `temp_data/config.json` 中 `intents` 键下的所有意图（与 spec 中「约 39 个已定义功能」对应）。
- **操作**:
  1. 解析 `config.json` 列出所有 intent 名称（可执行下方命令得到清单）。
  2. 检查后台「意图管理」是否支持导入/配置这些意图；检查 NLU 是否在发布版本中加载并识别这些意图。
  3. 若有「意图列表 API」或种子数据，核对是否包含全部 39 个。

- **提取意图清单命令**（在项目根目录执行）:
  ```bash
  python -c "
  import json
  with open('temp_data/config.json', 'r', encoding='utf-8') as f:
      data = json.load(f)
  intents = data.get('intents', {})
  for i, name in enumerate(sorted(intents.keys()), 1):
      print(f\"{i}. {name}\")
  print(f\"\\n合计: {len(intents)} 个意图\")
  "
  ```

- **产出**: 意图清单与「已支持/未支持」状态表。

### 3.2 产出汇总

- **需求追溯矩阵**（FR/SC/用户故事）
- **缺口清单**：未实现或部分实现的 FR、未达标的 SC、未覆盖的验收场景、缺失的意图

---

## 四、维度 2：代码质量评价

### 4.1 执行步骤

#### 步骤 2.1：后端静态检查

```bash
cd smartchef-platform/backend
pip install -e ".[dev]"
ruff check app/
ruff format --check app/
mypy app/ --no-error-summary 2>&1 | tee docs/ruff_mypy_report.txt
```

- **预期**: ruff 无错误；format 通过；mypy 可存在部分 ignore，但需记录。
- **产出**: `docs/ruff_mypy_report.txt`，以及问题清单（若存在）。

#### 步骤 2.2：前端静态检查（若已配置）

```bash
cd smartchef-platform/frontend
npm run lint
npm run build
```

- **产出**: lint 与 build 结果；构建失败项列入问题清单。

#### 步骤 2.3：依赖与安全

- 后端: `pip audit` 或 `safety check`（若已安装）
- 前端: `npm audit`
- 检查 `.env` 是否未提交、密钥是否通过环境变量注入

- **产出**: 依赖漏洞清单（若有）；安全配置检查项（README 或 docs 中说明）。

#### 步骤 2.4：项目结构与规范

- 对照 `specs/master/plan.md` 的「项目结构」一节，核对 `smartchef-platform/backend/app/` 与 `frontend/src/` 的目录、关键文件是否存在（如 `pipeline.py`、`router.py`、各 API 路由、各前端页面）。
- **产出**: 结构符合性列表；缺失或错位目录/文件清单。

### 4.2 Code Review 与文档

- **独立文档**: [docs/CODE_REVIEW.md](./CODE_REVIEW.md) 定义代码质量与 Code Review 的范围、方法、后端/前端要点及产出。
- **执行内容**: 静态检查（ruff、mypy、前端 lint/build）、结构规范核对、安全项检查（鉴权、输入校验、敏感数据）、可维护性（命名、注释）。
- **产出**: 静态检查报告、问题清单（文件:行号–描述–建议）、符合性结论；与评价总结中的「代码质量」一节对应。

---

## 五、维度 3：测试用例覆盖

### 5.1 执行步骤

#### 步骤 3.1：后端单元测试

```bash
cd smartchef-platform/backend
pytest tests/unit/ -v --tb=short 2>&1 | tee docs/test_unit_report.txt
```

- **产出**: 通过/失败数量、失败用例列表；若有 `pytest-cov`：  
  `pytest tests/unit/ --cov=app --cov-report=term-missing --cov-fail-under=0`  
  生成覆盖率（不强制下限，仅记录）。

#### 步骤 3.2：后端集成测试

```bash
# 确保 PostgreSQL、Redis 已启动，.env 已配置
pytest tests/integration/ -v --tb=short 2>&1 | tee docs/test_integration_report.txt
```

- **产出**: 通过/失败数量；需标注哪些用例依赖外部服务（ZenMux、Brave），便于区分「可重复」与「需环境」。

#### 步骤 3.3：后端合约测试

```bash
pytest tests/contract/ -v --tb=short 2>&1 | tee docs/test_contract_report.txt
```

- **产出**: 各 API 合约通过情况；与 `specs/master/contracts/` 中 admin-api、dialog-api 的对应关系说明。

#### 步骤 3.4：E2E 测试

```bash
# 确保后端已启动（或使用 fixture 启动）
pytest tests/e2e/ -v --tb=short 2>&1 | tee docs/test_e2e_report.txt
```

- 若有独立脚本：  
  `python smartchef-platform/backend/e2e_test.py` 或  
  `python smartchef-platform/scripts/quickstart_verify.py --base-url http://localhost:8000`  
  记录通过步骤数/总步骤数。

- **产出**: E2E 通过率、失败步骤；与用户故事（如 US1～US5、版本发布）的对应关系。

#### 步骤 3.5：覆盖率汇总（可选但推荐）

```bash
cd smartchef-platform/backend
pytest tests/ --cov=app --cov-report=html --cov-report=term-missing -q
```

- **产出**: `htmlcov/index.html` 与终端覆盖率汇总；记录 `app/api`、`app/services`、`app/models` 各层覆盖率百分比。

#### 步骤 3.6：测试与任务对应

- **输入**: `specs/master/tasks.md` 中带「测试」的任务（如 T026～T027、T038～T039、T062、T081～T082 等）。
- **操作**: 每个测试任务对应一个或多个测试文件/用例，列出映射表。

- **产出**: 任务→测试用例映射表；未覆盖任务的测试列入缺口。

### 5.2 产出汇总

- 单元/集成/合约/E2E 报告文件及通过率
- 覆盖率报告（若执行）
- 任务→测试映射与缺口

---

## 六、维度 4：用户操作路径覆盖

### 6.1 路径清单（与用户故事对应）

| 路径 ID | 用户故事 | 路径描述 | 验证方式 |
|---------|----------|----------|----------|
| P1      | US1      | 登录 → 意图列表 → 创建指令（含槽位）→ 保存 → 列表可见 | 手动 / E2E |
| P2      | US1      | 编辑已有指令（提示词/训练数据）→ 保存 → 版本「未发布」 | 手动 / E2E |
| P3      | US1      | 删除指令 → 列表移除、训练数据清理 | 手动 / E2E |
| P4      | US2      | 上传菜谱 Markdown/JSON → 解析索引 → 知识库列表可见、可搜索 | 集成 test_knowledge_indexing + 手动 |
| P5      | US3      | 创建方案 A/B，不同 LLM/人设 → 手动测试同问句 → 回复差异可见 | 手动 / E2E |
| P6      | US3      | 选定方案 → 发布 → 确认 → 设备切换、会话重置 | E2E test_pm_workflow 或 quickstart_verify |
| P7      | US4      | 方案 A 测试界面 → 发送「设置温度180度」→ 调试面板展示路由/意图/槽位/耗时 | 合约 test_manual_test_api + 手动 |
| P8      | US4      | 设置设备上下文「正在烹饪」→ 问「还有多久」→ 理解剩余时间 | 集成 / 手动 |
| P9      | US5      | 设备 API 发送「开始烹饪」→ 意图 + 回复 &lt; 200ms | 集成 test_nlu_pipeline + 性能脚本 |
| P10     | US6      | 问菜谱食材 → 知识命中；问天气 → 联网回复 | 集成 test_knowledge_qa、test_chitchat |
| P11     | US7      | 「搜红烧肉」→「收藏它」→ 指代消解正确 | 集成 test_reference_resolution |
| P12     | US8      | 批量测试：生成用例 → 执行 → 查看报告/智能分析 | 合约 test_batch_test_api + 手动 |
| P13     | US9      | 监控仪表盘 → 实时指标；按设备 ID 查会话 → 单轮链路 | 合约 test_monitoring_api + 手动 |
| P14     | US10     | 管理员创建「指令编辑员」→ 该账号登录仅见指令与测试菜单 | 集成 test_rbac + 手动 |

### 6.2 执行方式

- **自动化**: 能由 E2E、集成、合约覆盖的路径，执行命令见维度 3，并在本表标注「自动化通过」。
- **手动**: 在浏览器中按路径操作，每步截图或记录结果（通过/失败），并记录环境（如后端 URL、是否已发布版本）。
- **产出**: 路径检查表（每行：路径 ID、通过/失败、证据文件或说明）。

---

## 七、维度 5：性能指标（实际数据）

### 7.1 指标与采集方法

| 指标 | 规范要求 | 采集方法 | 记录字段 |
|------|----------|----------|----------|
| 指令意图准确率 | SC-001 ≥ 95% | 批量测试报告或 `evaluate_model.py` 输出 | 准确率数值、样本数、意图数 |
| 指令类 P95 延迟 | SC-002 &lt; 200ms | 脚本多次调用 `/dialog/parse` 或 `/dialog/chat`，统计 P95 | P50/P95/P99、样本数 |
| 知识/闲聊延迟 | SC-003 2～4s | 集成测试或脚本调用知识/闲聊样本，记录响应时间 | 平均/中位数、样本数 |
| API 并发 | SC-006 10 QPS | 使用 locust/httpx 并发 10 QPS 持续 1 分钟，看错误率与延迟 | QPS、错误率、P95 |
| PM 全流程耗时 | SC-007 ≤ 1h | E2E 或 quickstart_verify 计时 | 总耗时（分钟） |
| 批量分析根因识别率 | SC-008 ≥ 80% | 若有智能分析报告，抽样对比人工判断 | 根因识别率或「待实现」 |

### 7.2 可执行脚本

**指令延迟采样**（脚本已落地：`backend/scripts/performance_test.py`）:

```bash
cd smartchef-platform/backend
# 需后端已启动且已发布版本
python -m scripts.performance_test
python -m scripts.performance_test --base-url http://localhost:8000 --samples 50 --p95-threshold 200
```

- 输出：P50/P95/P99、样本数、SC-002 通过/失败。
- 将终端输出填入 SC-002 的「实际数据」列。

**准确率**：若有批量测试或 `evaluate_model.py`，运行后从报告或 stdout 中提取「准确率」「F1」等，填入 SC-001。

### 7.3 产出汇总

- **性能数据表**：指标名、规范值、实测值、采样条件（环境、请求数、是否含模型加载等）。
- **脚本与命令**：便于他人复现（可放在 `docs/` 或 `scripts/`）。

---

## 八、评价执行顺序建议

1. **环境准备**：数据库迁移、init_db、后端/前端可启动。
2. **维度 2（代码质量）**：先做静态检查与结构核对，避免带着明显问题做测试。
3. **维度 3（测试覆盖）**：按单元 → 集成 → 合约 → E2E 执行，并生成覆盖率（若需要）。
4. **维度 5（性能）**：在稳定环境下跑延迟/准确率/QPS 脚本，填入 SC 表。
5. **维度 1（需求匹配）**：结合代码与测试结果，填写 FR/SC/用户故事/意图追溯与缺口。
6. **维度 4（用户路径）**：用自动化 + 手动补全路径检查表。

最后汇总：**需求缺口清单**、**测试与路径通过率**、**性能数据表**、**代码质量结论**，形成一页「评价总结」与改进建议。

---

## 九、报告模板（总结页）

评价完成后，可填写以下总结（建议放在 `docs/EVALUATION_SUMMARY.md` 或本文件末尾）：

```markdown
## 评价总结

- **需求匹配**: FR 实现率 __/38，SC 达标 __/13，用户故事验收通过 __/10，意图支持 __/39。
- **代码质量**: Ruff/Format 通过 [ ] 是 [ ] 否，Mypy 问题数 __，结构符合 plan [ ] 是 [ ] 否。
- **测试**: 单元 __ 通过，集成 __ 通过，合约 __ 通过，E2E __ 通过；后端覆盖率约 __%。
- **用户路径**: 自动化 __/14，手动通过 __/14。
- **性能**: SC-001 准确率 __%，SC-002 P95 延迟 __ ms，SC-006 10 QPS 错误率 __%，SC-007 全流程 __ 分钟。
- **主要缺口**: （列举）
- **改进建议**: （列举）
```

---

## 十、参考文件清单

| 文件 | 用途 |
|------|------|
| `specs/master/spec.md` | FR、SC、用户故事、验收场景、边界情况 |
| `specs/master/plan.md` | 技术方案、项目结构、章程检查 |
| `specs/master/tasks.md` | 145 条任务、测试任务、检查点 |
| `specs/master/research.md` | 技术决策与成功标准背景 |
| `specs/master/quickstart.md` | 环境与验证步骤 |
| `specs/master/contracts/*.yaml` | API 合约定义 |
| `temp_data/config.json` | 39 个意图定义（指令配置基准） |
| `smartchef-platform/README.md` | 项目概述、快速启动、技术栈 |
| `smartchef-platform/backend/e2e_test.py` | MVP E2E 步骤 |
| `smartchef-platform/scripts/quickstart_verify.py` | 快速启动端到端验证 |

---

*本报告为可执行评价指南，所有「待填写」「待运行后填写」项均需在正式评价中替换为实际数据或结论。*
