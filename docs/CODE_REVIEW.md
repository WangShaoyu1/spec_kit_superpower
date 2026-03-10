# SmartChef 代码质量与 Code Review 说明

**文档版本**: 1.0  
**评价基准**: 静态检查、结构规范、安全项、可维护性

---

## 一、Code Review 范围与方法

### 1.1 范围

- **后端**: `smartchef-platform/backend/app/`（API、services、models、core、schemas）
- **前端**: `smartchef-platform/frontend/src/`（pages、components、services、stores）
- **脚本**: `backend/scripts/`、`scripts/`（迁移、初始化、清理、训练等）

### 1.2 方法

| 类型 | 工具/方式 | 说明 |
|------|-----------|------|
| 静态检查 | ruff（lint + format）、mypy | 后端 Python 风格与类型 |
| 前端静态 | ESLint、npm run build | 前端语法与构建 |
| 结构核对 | 与 plan.md / data-model 对照 | 模块、路由、表结构是否一致 |
| 安全项 | 认证/权限、注入、敏感数据 | 接口鉴权、SQL/输入校验、加密与 GDPR |
| 可维护性 | 命名、注释、重复度 | 可读性与变更成本 |

---

## 二、后端 Code Review 要点

### 2.1 静态检查（需在环境中执行）

```bash
cd smartchef-platform/backend
pip install -e ".[dev]"
ruff check app/
ruff format --check app/
mypy app/ --no-error-summary 2>&1 | tee docs/ruff_mypy_report.txt
```

- **Ruff**: 建议零 E/F 错误；format 与 plan 一致（line-length 120）。
- **Mypy**: 可为非严格模式；忽略第三方与迁移；记录未标注类型或 any 的模块。

### 2.2 结构规范

- **API 层**: 仅做参数校验、依赖注入、调用 service、返回 schema；不写业务逻辑。
- **Service 层**: 业务逻辑、事务边界、调用多个 model 或外部服务。
- **Model 层**: 表定义、关系、索引；无业务逻辑。
- **安全**: 敏感接口必须 `require_permission` 或 `get_current_user`；密码仅存 hash；敏感数据走 encryption 模块。

### 2.3 常见问题清单

- [ ] 是否存在未鉴权或鉴权遗漏的写接口？
- [ ] 用户输入是否经 Pydantic 校验并限制长度/类型？
- [ ] 是否存在 raw SQL 拼接（需改为参数化或 ORM）？
- [ ] 异步接口是否一致使用 async/await，避免阻塞？
- [ ] 敏感配置是否从环境变量读取、未写死或提交到仓库？

---

## 三、前端 Code Review 要点

### 3.1 静态与构建

```bash
cd smartchef-platform/frontend
npm run lint
npm run build
```

- 构建通过、无未处理 eslint error。
- 生产构建无控制台报错或未定义变量。

### 3.2 API 调用与错误处理

- 所有请求使用统一 `api` 实例（baseURL、拦截器）；401 统一跳转登录。
- 关键操作（创建/删除/发布）需有 loading 与错误提示（如 message.error(detail)）。
- 列表/下拉数据加载失败时应有占位或重试，避免白屏。

### 3.3 与后端接口对齐

- 路径、方法、请求体/查询参数与后端 OpenAPI 一致（如 PATCH /auth/roles/:id 已补齐）。
- 响应字段使用与后端 schema 一致（如 id、created_at 等）。

### 3.4 React 实践（结合 Vercel 技能）

- 避免在渲染路径中直接请求未缓存数据导致瀑布请求；可并行请求或按需加载。
- 列表较长时考虑虚拟列表或分页，避免一次渲染过多 DOM。
- 状态提升与派生状态：能由 props/state 推导的不单独用 state + effect 同步。

---

## 四、Code Review 产出与记录

### 4.1 建议产出

- **ruff_mypy_report.txt**: 静态检查原始输出（可放入 docs/ 或 CI 产物）。
- **问题清单**: 按「文件: 行号 – 问题描述 – 建议」记录，并标优先级（高/中/低）。
- **符合性结论**: 结构是否符合 plan.md；安全项是否满足 FR-036/FR-037 及章程。

### 4.2 与评价报告的关系

- **EVALUATION_REPORT.md** 中「维度 2：代码质量」引用本 CODE_REVIEW 方法，并汇总结论与问题数。
- **EVALUATION_SUMMARY.md** 的「代码质量」一节填写：Ruff/Mypy/ESLint 是否执行、通过与否、主要问题与改进建议。

---

## 五、本次评价已执行项

- **角色更新接口**: 已补齐后端 `PATCH /auth/roles/{role_id}` 与 `auth_service.update_role`，前端 RoleEditor 已改为 `api.patch`，修复「编辑角色」接口报错。
- **数据库清理脚本**: 已新增 `backend/scripts/clean_test_data.py`，清理测试数据并保留 users、roles；支持 `--dry-run`。
- **静态检查**: 需在本地/CI 安装 dev 依赖后执行上述 ruff/mypy 与前端 lint/build，并将结果填入评价总结。
