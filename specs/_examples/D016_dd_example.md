---
version: 1.0
based_on: D016_defect (已确认)
---

# DD 示例: D016 小模型闭环详细设计

> 这是一个示例，展示如果 D016 按新流程执行，dd.md 应该包含的内容
> 对比实际产生的缺陷，说明新流程如何避免遗漏

## 1. 数据模型详设（缺失导致的问题：训练/评估数据口径不清）

### 1.1 训练数据集 (TrainingDataset)

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|-----|------|-----|--------|------|
| id | UUID | PK | gen_random_uuid() | 唯一标识 |
| library_id | UUID | FK NOT NULL | - | 关联指令库 |
| name | VARCHAR(100) | NOT NULL | - | 数据集名称 |
| description | TEXT | NULL | - | 描述 |
| data_format | VARCHAR(20) | NOT NULL | 'minimal' | 格式类型 |
| row_count | INT | NOT NULL DEFAULT 0 | 0 | 数据行数 |
| created_at | TIMESTAMP | NOT NULL | now() | 创建时间 |

**数据行字段口径（训练集 - 最小字段）**:
```json
{
  "intent_key": "string, 必填, 意图标识",
  "utterance": "string, 必填, 用户表达",
  "language": "enum(zh/en), 必填, 语种",
  "slots": "json, 必填, 槽位标注 {slot_name: value}",
  "source": "enum(manual/llm), 必填, 数据来源"
}
```

**LLM 合成治理规则**:
- 必须覆盖全部 `intent_key`（库内所有意图）
- 每个意图至少 20 条（`MIN_SAMPLES_PER_INTENT = 20`）
- 必须包含口语化、多表达变体（同义改写 ≥ 3 种）
- 提示词有默认模板，可在页面配置

### 1.2 评估数据集 (EvaluationDataset)

**数据行字段口径（评估集 - 全字段）**:
```json
{
  "intent_key": "string, 必填",
  "utterance": "string, 必填",
  "language": "enum(zh/en), 必填",
  "source": "enum(manual/llm), 必填",
  "expected_result": "string, 必填, 期望意图结果",
  "actual_result": "string, 可选, 实际结果（评估后回填）",
  "threshold": "float, 可选, 阈值（评估时快照）",
  "actual_score": "float, 可选, 实际得分（评估后回填）",
  "is_hit": "bool, 可选, 是否命中（评估后回填）"
}
```

**回填规则**:
- 评估前：`actual_result`, `actual_score`, `is_hit` 允许为 NULL
- 评估后：系统自动回填评估结果
- 回填触发：评估任务完成后批量更新

---

## 2. 状态机定义（缺失导致的问题：模型状态流转不清晰）

### 2.1 模型版本状态机 (LibraryModelVersion)

```
                    ┌───────────┐
         ┌─────────►│  archived │◄────────┐
         │          └───────────┘         │
         │                ▲                │
         │                │ 恢复            │
         ▼                │                │
┌───────────┐    ┌───────────┐    ┌───────────┐
│   draft   │───►│  training │───►│  trained  │
└───────────┘    └───────────┘    └─────┬─────┘
   ▲    ▲                               │
   │    └───────────────────────────────┘
   │                        │
   │                        ▼
   │                   ┌───────────┐
   │                   │evaluating │
   │                   └─────┬─────┘
   │                        │
   │                        ▼
   │                   ┌───────────┐
   │                   │ testable  │
   │                   └─────┬─────┘
   │                        │
   │                        ▼
   │                   ┌───────────┐
   └───────────────────┤ published │
                       └───────────┘
```

#### 状态定义

| 状态 | 含义 | 允许的操作 | 限制 |
|-----|------|-----------|------|
| draft | 草稿 | 编辑、删除、创建训练任务 | - |
| training | 训练中 | 查看进度、取消 | 不可编辑 |
| trained | 训练完成 | 创建评估任务 | 不可编辑 |
| evaluating | 评估中 | 查看进度、取消 | 不可编辑 |
| testable | 可测试 | 单条测试、批量测试、设为testable | 库内唯一 |
| published | 已发布 | 查看、下载 | 库内唯一 |
| archived | 已归档 | 恢复为draft | 不可测试/发布 |

#### 状态转移规则

| 从 | 到 | 触发条件 | 前置校验 | 副作用 |
|---|----|---------|---------|--------|
| draft | training | 创建训练任务 | 库内模型数 < 5 | 记录训练参数 |
| training | trained | 训练完成回调 | 训练成功 | 保存模型产物路径 |
| trained | evaluating | 创建评估任务 | 选择评估集 | 记录评估配置 |
| evaluating | testable | 评估完成 | - | 自动生成分析报告 |
| any | testable | 手动切换 | 库内无其他testable | 自动取消旧testable |
| testable | published | 手动发布 | 二次确认 | 通知方案发布校验 |
| any | archived | 手动归档 | - | 清理运行时资源 |
| archived | draft | 手动恢复 | - | 重置训练参数 |

#### 唯一性约束（代码常量）

```python
MAX_MODELS_PER_LIBRARY = 5  # 单库模型数量上限
MAX_TESTABLE_PER_LIBRARY = 1  # 单库 testable 唯一
MAX_PUBLISHED_PER_LIBRARY = 1  # 单库 published 唯一
```

---

## 3. 核心算法详设

### 3.1 算法: 切换 Testable 模型

**输入**:
- `library_id`: UUID, 指令库ID
- `target_model_id`: UUID, 目标模型ID

**输出**:
- `success`: bool
- `previous_model_id`: UUID | null, 被取消testable的模型

**伪代码**:

```python
async def switch_testable_model(library_id: UUID, target_model_id: UUID):
    """
    切换指令库的 testable 模型
    规则: 库内最多1个testable，切换时自动取消旧的
    """
    # 步骤1: 校验目标模型存在且属于该库
    target = await get_model(target_model_id)
    if not target or target.library_id != library_id:
        raise BusinessError("E101", "模型不存在或不属于该指令库")
    
    # 步骤2: 校验目标模型状态允许设为testable
    if target.status not in ["trained", "evaluating", "testable", "published"]:
        raise BusinessError("E102", f"当前状态 {target.status} 不允许设为testable")
    
    # 步骤3: 查找当前testable模型（如果有）
    current_testable = await find_testable_by_library(library_id)
    
    # 步骤4: 在同一事务中执行切换
    async with transaction():
        if current_testable and current_testable.id != target_model_id:
            # 取消旧模型的testable状态
            await update_model_status(
                current_testable.id, 
                is_testable=False
            )
        
        # 设置新模型为testable
        await update_model_status(
            target_model_id, 
            is_testable=True
        )
    
    return {
        "success": True,
        "previous_model_id": current_testable.id if current_testable else None
    }
```

**边界条件**:

| 边界场景 | 处理方式 |
|---------|---------|
| 目标模型已是testable | 返回成功，previous_model_id=null |
| 当前无testable模型 | 直接设置，previous_model_id=null |
| 目标模型正在training | 返回错误 E102，提示等待训练完成 |
| 库内模型数已达上限 | 在创建训练任务时拦截，不在此处处理 |

---

## 4. 错误码体系（缺失导致的问题：错误处理不一致）

### 4.1 模型相关错误码

| 错误码 | 类别 | 含义 | 触发场景 | 用户提示 |
|--------|------|-----|---------|---------|
| E201 | 模型 | 模型不存在 | ID找不到 | "模型不存在或已被删除" |
| E202 | 模型 | 状态不允许 | 当前状态不可执行操作 | "当前状态 {status} 不允许此操作" |
| E203 | 模型 | 库内模型数超限 | 创建训练任务时 ≥5 | "指令库模型数量已达上限(5)，请先归档或删除历史模型" |
| E204 | 模型 | testable切换冲突 | 并发切换 | "模型状态已变更，请刷新后重试" |
| E205 | 模型 | 评估集格式错误 | 导入字段缺失 | "评估集格式错误，缺少必填字段: {fields}" |

### 4.2 方案发布相关错误码

| 错误码 | 类别 | 含义 | 触发场景 | 用户提示 |
|--------|------|-----|---------|---------|
| E301 | 发布 | 指令库无published模型 | 方案发布前校验 | "指令库 {library_name} 没有已发布模型，请先发布模型后再发布方案" |
| E302 | 发布 | 指令库未绑定 | 运行时加载 | "方案未绑定指令库，无法处理指令类请求" |

---

## 5. 权限模型（缺失导致的问题：权限控制不清晰）

### 5.1 权限点定义

| 权限点ID | 权限名称 | 操作范围 | 默认角色 |
|---------|---------|---------|---------|
| intent_library_read | 查看指令库 | GET /api/v1/intent-libraries/* | admin, editor, viewer |
| intent_library_create | 创建指令库 | POST /api/v1/intent-libraries | admin |
| intent_library_update | 编辑指令库 | PUT /api/v1/intent-libraries/{id} | admin, editor |
| intent_library_delete | 删除指令库 | DELETE /api/v1/intent-libraries/{id} | admin |
| model_read | 查看模型 | GET /api/v1/intent-libraries/{id}/models/* | admin, editor, viewer |
| model_train | 创建训练任务 | POST /api/v1/models/{id}/train | admin, editor |
| model_test_manage | 管理testable | POST /api/v1/models/{id}/set-testable | admin, editor |
| model_publish | 发布模型 | POST /api/v1/models/{id}/publish | admin |
| dataset_read | 查看数据集 | GET /api/v1/models/{id}/datasets/* | admin, editor, viewer |
| dataset_create | 创建数据集 | POST /api/v1/models/{id}/datasets | admin, editor |
| dataset_import | 导入数据 | POST /api/v1/datasets/{id}/import | admin, editor |
| evaluation_run | 执行评估 | POST /api/v1/models/{id}/evaluate | admin, editor |

### 5.2 前端权限渲染规则

```javascript
// 按钮/菜单权限控制示例
{
  "指令库管理": {
    "visible": "hasPermission('intent_library_read')",
    "新增按钮": "hasPermission('intent_library_create')",
    "编辑按钮": "hasPermission('intent_library_update')",
    "删除按钮": "hasPermission('intent_library_delete')"
  },
  "模型测试页": {
    "visible": "hasPermission('model_read')",
    "设为testable": "hasPermission('model_test_manage')",
    "发布按钮": "hasPermission('model_publish')"
  }
}
```

---

## 6. 配置项定义（缺失导致的问题：阈值配置层级不清）

### 6.1 库级默认阈值

| 配置项 | 类型 | 默认值 | 范围 | 说明 |
|--------|------|--------|------|------|
| library.default_intent_threshold | float | 0.85 | 0.0-1.0 | 意图匹配默认阈值 |
| library.default_slot_threshold | float | 0.80 | 0.0-1.0 | 槽位匹配默认阈值 |
| library.min_samples_per_intent | int | 20 | 10-100 | 每意图最小训练样本数 |

### 6.2 评估任务级阈值（快照）

评估任务创建时可覆盖库级默认值，写入该次任务的 `threshold_snapshot` 字段。

```json
{
  "task_id": "uuid",
  "threshold_snapshot": {
    "intent_f1": 0.90,  // 本次覆盖值
    "slot_f1": 0.85     // 本次覆盖值
  }
}
```

---

## 7. 追溯矩阵

| DD 章节 | D016 需求点 | 说明 |
|--------|------------|------|
| 1.1 训练集字段 | 六、Excel导入字段口径 | 训练集最小5字段 |
| 1.2 评估集字段 | 六、Excel导入字段口径 | 评估集全9字段 |
| 2.1 模型状态机 | 三、模型状态机 | 7状态+转移规则 |
| 3.1 切换testable | 二、模型关系 | testable自动互斥 |
| 4 错误码 | - | 新增业务错误码 |
| 5 权限点 | 九、权限边界 | model_publish等 |
| 6 配置项 | 七、质量门槛 | 阈值配置层级 |

---

## 对比：按新流程 vs 实际发生

| 缺失点 | 实际缺陷表现 | DD 如何避免 |
|--------|-------------|------------|
| 状态机 | 状态流转混乱 | 明确定义7状态和转移条件 |
| 数据口径 | 训练/评估字段不清 | 明确最小5字段vs全9字段 |
| 唯一性约束 | 库内多testable冲突 | 定义MAX_TESTABLE_PER_LIBRARY=1 |
| 权限点 | 发布控制不严 | 定义model_publish权限点 |
| 阈值配置 | 阈值层级混乱 | 定义库级默认+任务级快照 |
| 错误码 | 错误处理不一致 | 定义E201-E302错误码 |

**结论**: 如果 D016 按新流程补充 DD.md，这些细节在设计阶段就会被明确，大幅降低实现阶段的偏差。
