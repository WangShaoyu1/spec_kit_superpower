---
version: 1.0
module: intent-library
based_on:
  - ad/ad-intent-library.md
  - spec.md
---

# 详细设计 (DD): 指令库管理最小闭环示例

## 1. 实体

### 1.1 IntentLibrary

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 指令库 ID |
| library_key | VARCHAR(64) | NOT NULL, UNIQUE | 全局唯一且不可修改 |
| name | VARCHAR(100) | NOT NULL | 指令库名称 |
| language | VARCHAR(8) | NOT NULL, enum: zh/en | 语种 |

### 1.2 TrainingDataset

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 数据集 ID |
| library_id | UUID | FK(intent_libraries.id) | 所属指令库 |
| name | VARCHAR(100) | NOT NULL | 数据集名称 |
| sample_count | INTEGER | >= 0 | 样本数 |
| intent_count | INTEGER | >= 0 | 意图数 |

### 1.3 Intent

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 意图 ID |
| dataset_id | UUID | FK(training_datasets.id) | 所属数据集 |
| intent_key | VARCHAR(128) | NOT NULL | 英文标识 |
| utterance | TEXT | NOT NULL | 最小训练话术 |
| language | VARCHAR(8) | NOT NULL, enum: zh/en | 语种 |
| slots | JSONB | NOT NULL, default '[]' | 词槽引用 |
| source | VARCHAR(16) | NOT NULL, enum: manual/llm | 来源 |

### 1.4 LibraryModelVersion

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 模型版本 ID |
| library_id | UUID | FK(intent_libraries.id) | 所属指令库 |
| train_dataset_id | UUID | FK(training_datasets.id) | 绑定训练集 |
| status | VARCHAR(24) | NOT NULL, enum: draft/training/trained | 本示例只允许创建 draft |

## 2. 状态与约束

- 本示例的模型状态机只落到 `draft`
- 若训练数据集 `intent_count = 0`，禁止创建模型草稿
- 若训练数据集已被另一个非 archived 模型绑定，禁止重复绑定

## 3. 核心算法

### 3.1 创建模型草稿

```text
输入: library_id, train_dataset_id
1. 校验 library_id 存在
2. 校验 train_dataset_id 属于该 library_id
3. 校验 intent_count > 0
4. 校验该 train_dataset_id 未被其他活动模型占用
5. 创建 model_version(status=draft)
6. 返回 draft 模型记录
```

**真实成功信号**:
- 返回的 `status` 必须是 `draft`
- 详情页模型表格可展示 `train_dataset_id` 对应的数据集名称

## 4. 错误码

| 错误码 | 场景 |
|--------|------|
| E50001 | library_key 重复 |
| E50002 | 训练数据集为空，禁止创建模型草稿 |
| E50003 | 训练数据集已被其他活动模型绑定 |

## 5. 显式未完成项

- **Deferred**: 训练、评估、testable、发布、下载
- **Stub**: 无；本示例不允许用 501 假装已覆盖训练链路
- **Out of Scope**: 批量测试、智能分析、权限细则
- **Blocked By**: 无
