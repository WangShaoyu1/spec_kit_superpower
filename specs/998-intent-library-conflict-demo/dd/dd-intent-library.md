---
version: 1.0
module: intent-library
based_on:
  - ad/ad-intent-library.md
  - spec.md
---

# 详细设计 (DD): 指令库管理冲突扫描示例

## 1. 核心约束

- 创建模型草稿前必须保证 `intent_count > 0`
- 空训练数据集禁止创建模型草稿

## 2. 核心算法

### 2.1 创建模型草稿

```text
输入: library_id, train_dataset_id
1. 校验 train_dataset_id 属于当前库
2. 校验 intent_count > 0
3. 若为空，返回 E50002
4. 创建 model_version(status=draft)
```

## 3. 错误码

| 错误码 | 场景 |
|--------|------|
| E50002 | 训练数据集为空，禁止创建模型草稿 |
