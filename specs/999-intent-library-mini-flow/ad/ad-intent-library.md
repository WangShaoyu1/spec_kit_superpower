---
version: 1.0
module: intent-library
based_on:
  - spec.md
  - pd-all/pd-intent-library/
---

# 架构设计 (AD): 指令库管理最小闭环示例

## 1. 模块概述

本示例只覆盖“指令库最小闭环”：

- 指令库 CRUD（只要求创建和查看）
- 训练数据集创建
- 数据集内意图维护
- 模型草稿创建并绑定训练集

**PD 页面**: `index.html`、`detail.html`、`datasets.html`、`dataset-detail.html`

## 2. 核心数据流

### 2.1 最小闭环

```mermaid
sequenceDiagram
    participant PM as PM
    participant API as API
    participant Service as IntentLibraryService
    participant DB as PostgreSQL

    PM->>API: POST /api/v1/intent-libraries
    API->>Service: create_library(payload)
    Service->>DB: INSERT intent_library
    Service-->>PM: 201 Created

    PM->>API: POST /api/v1/intent-libraries/{id}/datasets
    API->>Service: create_training_dataset(library_id, payload)
    Service->>DB: INSERT training_dataset
    Service-->>PM: 201 Created

    PM->>API: POST /api/v1/datasets/{id}/intents
    API->>Service: create_intent(dataset_id, payload)
    Service->>DB: INSERT intent
    Service-->>PM: 201 Created

    PM->>API: POST /api/v1/intent-libraries/{id}/models
    API->>Service: create_model_draft(library_id, train_dataset_id)
    Service->>DB: 校验数据集非空且未绑定其他草稿
    Service->>DB: INSERT model_version(status=draft)
    Service-->>PM: 201 Created
```

**真实成功信号**:
- 库详情页能看到 draft 模型
- draft 模型上显示绑定的训练集名称
- 数据集详情页能看到至少一个意图

## 3. 接口契约

### 3.1 指令库

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/intent-libraries | 指令库列表 |
| POST | /api/v1/intent-libraries | 创建指令库 |
| GET | /api/v1/intent-libraries/{id} | 指令库详情 |

### 3.2 数据集与意图

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/intent-libraries/{id}/datasets | 创建训练数据集 |
| GET | /api/v1/intent-libraries/{id}/datasets | 训练数据集列表 |
| POST | /api/v1/datasets/{id}/intents | 创建意图 |
| GET | /api/v1/datasets/{id}/intents | 意图列表 |

### 3.3 模型草稿

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/intent-libraries/{id}/models | 创建模型草稿并绑定训练集 |
| GET | /api/v1/intent-libraries/{id}/models | 模型列表 |

## 4. 风险与约束

- `library_key` 必须唯一，且创建后不可修改
- 训练数据集为空时禁止创建模型草稿
- 训练、评估、发布不在本示例范围，必须在下游显式登记为 `Deferred`
