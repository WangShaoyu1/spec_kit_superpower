# Harness Runbook

## 目标

把 `spec -> pd -> ad -> dd -> plan -> tasks -> implement -> browser` 从“人工记忆流程”变成“受控执行流程”。

## 运行原则

- 每一阶段只读取本阶段必需输入
- 每一阶段完成后立即验证
- `BLOCKER` 不得带入下一阶段
- `WARNING` 必须显式下传，不得隐藏在备注里
- 模块推进必须服从 `module-rollout.json` 与 `module-state.json`
- 同一时间只允许一个模块进入 `implementing`

## 主控层

在模块级研发模式下，先由 `MasterAgent` 完成以下动作：

1. 读取 `.specify/harness/module-rollout.json`
2. 读取 `.specify/harness/module-state.json`
3. 选择唯一允许推进的目标模块
4. 对目标模块执行 `ad -> dd -> tasks -> implement -> browser`
5. 只有通过 browser gate 后，模块才能标记为 `browser_verified`

## 阶段运行口径

### 1. AD

**读取**

- `spec.md`
- `pd-all/pd-index.md`
- `pd-all/pd-<module>/README.md`
- 对应 HTML 原型
- `.cursor/rules/specify-rules.mdc`

**写入**

- `ad/` 或 `ad.md`

**验证**

- 输入制品齐全
- 规则引用有效
- 若 PD 存在条件准入模块，AD 文档必须显式继承

### 2. DD

**读取**

- `spec.md`
- `pd-all/**`
- `ad/` 或 `ad.md`
- `.cursor/rules/specify-rules.mdc`

**写入**

- `dd/` 或 `dd.md`

**验证**

- AD 已存在
- AD 引用的 PD 页面真实存在
- 条件准入模块继续显式下传

### 3. Tasks

**读取**

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
- pre-flight 扫描输出 `BLOCKER / WARNING / INFO`

### 4. Implement

**读取**

- `tasks/**`
- 相关 `pd / ad / dd / plan`
- `docs/DEFECT_WORKFLOW_DESIGN.md`

**写入**

- 代码
- 测试
- 必要的缺陷/验证证据

**验证**

- `BLOCKER` 为 0
- 测试、lint、smoke、review 证据齐全
- 不允许“假成功”

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

## Agent 约束

- 不允许自行扩大输入范围
- 不允许跳过 gate 直接生成下游文档
- 不允许把 `部分覆盖` 当成 `已完成`
- 不允许在存在 `BLOCKER` 时宣称阶段完成
- 不允许越过 `module-rollout.json` 的顺序直接进入其他模块实现
- 不允许在已有模块占用浏览器或实现资源锁时并发启动同类任务
