# Speckit Design-AD - 架构设计

## 目的
将 spec.md 的功能需求和 AI-PD 的语义规格，转化为**技术架构方案**，定义模块结构、数据流向和接口契约。

**核心规范**: `specs/_template/ad-template.md` — 所有 AD 设计 MUST 遵循此模板。

## 输入
- `specs/{branch}/spec.md` - 业务需求 (含模块映射表 + FR 标签)
- `specs/{branch}/pd-all/` - HumanPD（视觉参考层）
- `specs/{branch}/ai-pd/` - AI-PD（AI 主输入）
- `specs/_template/ad-template.md` - AD 设计规范 (框架级模板)

## 前置 Gate（MUST）

1. 从仓库根目录运行 `.specify/scripts/powershell/check-prerequisites.ps1 -Json`，解析 `FEATURE_DIR`
2. 若当前采用模块级 rollout，先运行 `.specify/scripts/powershell/get-module-rollout.ps1 -Json`，确认 `MasterAgent` 选中的目标模块
3. 紧接着运行 `.specify/scripts/powershell/validate-stage-gates.ps1 -Stage ad -Module <target-module> -Json`（非模块模式可省略 `-Module`）
4. 若返回 `status=blocked` 或存在任一 `BLOCKER` 失败码，必须先修上游制品，不得继续生成 AD
5. 若返回 `WARNING`，必须在 AD 文档中显式继承风险，不得把条件准入能力默认视为已闭环
6. 进入 AD 前，必须优先读取 `ai-pd/ai-<module>.md`；`pd-all/` 只用于补充视觉和导航参考

## 执行流程

### Phase 1: 领域与子域划分
基于 spec.md 的关键实体，识别领域边界：
- 核心域（业务核心）
- 支撑域（工具类）
- 通用域（基础能力）

### Phase 2: 组件/模块设计
定义系统的顶层模块结构：

```markdown
## 模块关系图

[前端] ←──REST──→ [API网关] ←──→ [业务模块A] ←──→ [数据存储A]
                           ←──→ [业务模块B] ←──→ [数据存储B]
                           ←──→ [通用模块]
```

### Phase 3: 数据流向设计
为每个核心业务流程定义数据流：

```markdown
## 流程: {流程名称}

1. 触发点: {用户操作/定时任务/API调用}
2. 处理链路:
   - 模块A: {职责}
   - 模块B: {职责}
3. 数据存储: {创建/更新/查询哪些数据}
4. 异常处理: {失败时的降级策略}
```

### Phase 4: 接口契约设计
定义模块间/前后端间的关键接口：

```markdown
## 接口: {接口名称}

- 路径: {HTTP方法} {URL路径}
- 输入: {参数结构}
- 输出: {响应结构}
- 错误码: {业务错误码定义}
```

### Phase 5: 技术选型与约束
- 核心技术栈（语言、框架、数据库）
- 性能目标（延迟、并发、容量）
- 安全约束（认证、授权、加密）
- 部署架构（容器化、服务网格）

### Phase 6: 风险识别
- 技术风险（新技术、性能瓶颈）
- 业务风险（合规、依赖外部服务）
- 缓解策略

## 输出产物

产出物结构取决于模块数量（遵循 `ad-template.md` 规则）：

### 模块数 ≤ 3：单文件

```yaml
# specs/{branch}/ad.md
```

### 模块数 > 3：文件夹

```
specs/{branch}/ad/
├── README.md          # 索引（模块列表、覆盖范围、状态）
├── ad-global.md       # 全局架构（领域划分、技术栈、通用约定、权限模型）
└── ad-<module>.md     # 各模块架构设计（数据流、API 契约、状态图）
```

```yaml
# 每个 ad-<module>.md 包含：
---
version: 1.0
based_on: 
  - spec.md (含模块映射表 + FR 标签)
  - ai-pd/ai-<module>.md (AI 主输入)
  - pd-all/pd-index.md (HumanPD 索引)
  - pd-all/pd-<module>/ (视觉参考)
---

# 1. 模块职责与边界
# 2. 核心数据流（Mermaid 时序图）
# 3. 接口契约（完整 API 表 + 请求/响应示例）
# 4. 与 spec.md 的 FR 追溯矩阵
```

## AD 完整性检查清单

- [ ] 每个 FR 都映射到技术实现方案
- [ ] 模块职责清晰，无循环依赖
- [ ] 核心流程有完整的数据流图
- [ ] 接口契约包含：路径、输入、输出、错误码
- [ ] AI-PD 中的所有能力项与动作契约都有对应 API
- [ ] 性能目标可量化验证
- [ ] 已识别关键技术风险

## 下一步
AD 完成后，进入 DD（详细设计）阶段：`/speckit.design-dd`
