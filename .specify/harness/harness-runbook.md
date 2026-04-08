# Harness Runbook

## 目标

把 `spec -> HumanPD -> AI-PD -> ad -> dd -> plan -> tasks -> implement -> browser` 从“人工记忆流程”变成“受控执行流程”。

## 运行原则

- 每一阶段只读取本阶段必需输入
- 每一阶段完成后立即验证
- `BLOCKER` 不得带入下一阶段
- `WARNING` 必须显式下传，不得隐藏在备注里
- 模块推进必须服从 `module-rollout.json` 与 `module-state.json`
- 同一时间只允许一个模块进入 `implementing`
- `HumanPD` 的页面能力清单必须先满足页面级语义要求：每个 HTML 页面都必须在 README 中显式提供 `page_goal` 与 `primary_user_flows`

## 关键新门禁: GATE-PD-003

`GATE-PD-003` 的含义是：

- 只要 `pd-all/pd-<module>/README.md` 中任一页面缺少 `page_goal`
- 或任一页面缺少 `primary_user_flows`
- 则该模块不得继续进入 `transform-pd / ad / dd / plan / tasks / implement / browser`

为什么要加这条门禁：

- 没有页面级 `goal`，AI-PD 会退化成把模块目标复制到每个页面
- 没有页面级 `primary_user_flows`，AI-PD 很容易把模块级使用场景错误复用到所有页面
- 这会导致下游 `AD / DD / plan / tasks / smoke` 读到的是“模块语义”，而不是“页面语义”

团队应如何理解这条规则：

- `page_goal / primary_user_flows` 不是可选增强项，而是 HumanPD 进入 AI-PD 转换链的前置条件
- 若缺失，应先补 `pd-all`，而不是让下游阶段继续“猜”
- `transform-pd` 可以消费这两个字段，但不应再替代 PD 补写这两个字段

## 主控层

在模块级研发模式下，先由 `MasterAgent` 完成以下动作：

1. 读取 `.specify/harness/module-rollout.json`
2. 读取 `.specify/harness/module-state.json`
3. 选择唯一允许推进的目标模块
4. 对目标模块执行 `transform-pd -> ad -> dd -> tasks -> implement -> browser`
5. 只有通过 browser gate 后，模块才能标记为 `browser_verified`

## 阶段运行口径

### 1. AD

**读取**

- `spec.md`
- `pd-all/pd-index.md`
- `pd-all/pd-<module>/README.md`
- 对应 HTML 原型
- `ai-pd/ai-<module>.md`
- `.cursor/rules/specify-rules.mdc`

**写入**

- `ad/` 或 `ad.md`

**验证**

- 输入制品齐全
- 规则引用有效
- 若 PD 存在条件准入模块，AD 文档必须显式继承
- 不允许存在 `GATE-PD-003`，即所有页面都必须已有 `page_goal / primary_user_flows`

### 2. DD

**读取**

- `spec.md`
- `ai-pd/**`
- `pd-all/**`
- `ad/` 或 `ad.md`
- `.cursor/rules/specify-rules.mdc`

**写入**

- `dd/` 或 `dd.md`

**验证**

- AD 已存在
- AD 引用的 PD 页面真实存在
- 条件准入模块继续显式下传
- 不允许存在 `GATE-PD-003`

### 3. Tasks

**读取**

- `ai-pd/**`
- `pd-all/**`
- `ad/**`
- `dd/**`
- `plans/plan-<module>.md`

**写入**

- `tasks/README.md`
- `tasks/tasks-*.md`

**验证**

- 当前模块 plan 已定义核心业务链路与真实成功信号
- 当前模块 plan 已继承 PD 的条件准入与部分覆盖
- 当前模块 plan 已提供 AI-PD 承接矩阵，并显式区分 `ui-capability / domain-rule / instructional / non-actionable-note`
- pre-flight 扫描输出 `BLOCKER / WARNING / INFO`
- 若 `pd-all` 缺少页面级 `page_goal / primary_user_flows`，必须先回到 PD 补齐，禁止继续拆任务

### 4. Implement

**读取**

- `tasks/**`
- 相关 `ai-pd / pd / ad / dd / plan`
- `docs/DEFECT_WORKFLOW_DESIGN.md`

**写入**

- 代码
- 测试
- 必要的缺陷/验证证据

**验证**

- `BLOCKER` 为 0
- 测试、lint、smoke、review 证据齐全
- 不允许“假成功”
- 不允许忽略 AI-PD `hidden_interactions` 中的 `ui-capability / domain-rule`
- 若当前模块曾命中 `GATE-PD-003`，不得以“代码先做”方式绕过 PD 补齐

### 5. Browser

**读取**

- `module-rollout.json`
- `module-state.json`
- 目标模块 `tasks/**`
- 目标模块对应的 `PD / AD / DD / plan`

**写入**

- 浏览器验证证据
- 缺陷记录或通过结论
- 模块状态（`implementing -> browser_verified`）

**验证**

- `UI smoke` 通过
- `business e2e` 通过
- `quality probes` 通过
- 重点模块额外验证性能与准确率信号
- 重点模块额外验证 `capability_parity`
- 若页面级 `goal / primary_user_flows` 缺失导致 AI-PD 页面语义失真，整体按 `BLOCKER` 处理

## Agent 约束

- 不允许自行扩大输入范围
- 不允许跳过 gate 直接生成下游文档
- 不允许把 `部分覆盖` 当成 `已完成`
- 不允许在存在 `BLOCKER` 时宣称阶段完成
- 不允许越过 `module-rollout.json` 的顺序直接进入其他模块实现
- 不允许在已有模块占用浏览器或实现资源锁时并发启动同类任务
