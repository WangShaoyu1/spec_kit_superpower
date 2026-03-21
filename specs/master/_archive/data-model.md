# 数据模型: SmartChef 智能对话管理平台

**日期**: 2026-03-03 | **阶段**: 1（设计）| **输入**: spec.md 关键实体 + research.md 技术决策

---

## 实体关系总览

```
User (1) ──────┐
               │ created_by
               ▼
DialogProfile (N) ──┬── references ──→ Intent (N)
                    ├── references ──→ KnowledgeBase (N)
                    ├── contains  ──→ Persona (1)
                    └── snapshots ──→ PublishedVersion (N)
                                          │
                                          │ active_version (0..1)
                                          ▼
                                     DeviceSession (N) ── logs ──→ RequestLog (N)

Intent (1) ── contains ──→ Slot (N)
Intent (1) ── has ──→ TrainingData (N)

KnowledgeBase (1) ── contains ──→ KnowledgeDocument (N)
KnowledgeDocument (1) ── indexed_as ──→ DocumentChunk (N) [with pgvector embedding]

TestSuite (1) ── contains ──→ TestCase (N)
TestSuite (1) ── produces ──→ TestReport (1)

AlertRule (N) ── monitors ──→ RequestLog (N) [via metric aggregation]
```

---

## 持久化实体（PostgreSQL）

### User（系统用户）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 用户唯一标识 |
| username | VARCHAR(64) | UNIQUE, NOT NULL | 登录用户名 |
| password_hash | VARCHAR(256) | NOT NULL | bcrypt 加密密码 |
| display_name | VARCHAR(64) | NOT NULL | 显示名称 |
| role_id | UUID | FK → Role.id | 角色外键 |
| is_active | BOOLEAN | DEFAULT true | 是否启用 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

### Role（角色）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 角色唯一标识 |
| name | VARCHAR(64) | UNIQUE, NOT NULL | 角色名称（如"管理员"、"指令编辑员"） |
| permissions | JSONB | NOT NULL | 权限清单（菜单 + 操作粒度） |
| is_system | BOOLEAN | DEFAULT false | 是否为系统内置角色（不可删除） |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

**权限 JSONB 结构示例**:
```json
{
  "intent_management": { "read": true, "write": true, "delete": true },
  "knowledge_management": { "read": true, "write": false, "delete": false },
  "dialog_profile": { "read": true, "write": true, "delete": false },
  "testing": { "manual": true, "batch": true },
  "version_publish": false,
  "monitoring": { "dashboard": true, "device_logs": true },
  "user_management": false
}
```

### Intent（意图定义）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 意图唯一标识 |
| intent_key | VARCHAR(128) | UNIQUE, NOT NULL | 意图标识符（如 `voice_cmd_start_cooking`） |
| display_name | VARCHAR(128) | NOT NULL | 中文描述（如"启动烹饪"） |
| category | VARCHAR(64) | NOT NULL | 分类（如"烹饪控制"、"菜谱操作"、"系统设置"） |
| description | TEXT | | 详细说明 |
| is_active | BOOLEAN | DEFAULT true | 是否启用 |
| created_by | UUID | FK → User.id | 创建人 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

### Slot（槽位定义）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 槽位唯一标识 |
| intent_id | UUID | FK → Intent.id, NOT NULL | 所属意图 |
| slot_key | VARCHAR(64) | NOT NULL | 槽位标识（如 `duration`、`number`） |
| display_name | VARCHAR(64) | NOT NULL | 中文名称（如"时长"、"温度数值"） |
| entity_type | VARCHAR(64) | NOT NULL | 实体类型（`number`、`time`、`food_name`、`enum`、`free_text`） |
| is_required | BOOLEAN | DEFAULT false | 是否必填 |
| prompt_text | TEXT | | 追问提示（PM 配置，如"请问您要加热多长时间？"） |
| constraints | JSONB | | 值约束（如 `{"min": 30, "max": 300, "unit": "℃"}`） |
| sort_order | INTEGER | DEFAULT 0 | 追问优先级排序 |

**UNIQUE**: (intent_id, slot_key)

### TrainingData（训练数据）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 训练数据唯一标识 |
| intent_id | UUID | FK → Intent.id, NOT NULL | 所属意图 |
| text | TEXT | NOT NULL | 训练语句（如"帮我设置温度到180度"） |
| language | VARCHAR(8) | DEFAULT 'zh' | 语言（zh/en） |
| slot_annotations | JSONB | | 槽位标注（BIO 格式）（如 `[{"slot": "number", "start": 8, "end": 11, "value": "180"}]`） |
| is_auto_translated | BOOLEAN | DEFAULT false | 是否为自动翻译生成 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

### KnowledgeBase（知识库）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 知识库唯一标识 |
| name | VARCHAR(128) | NOT NULL | 知识库名称（如"菜谱知识"、"公司信息"） |
| description | TEXT | | 描述 |
| created_by | UUID | FK → User.id | 创建人 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

### KnowledgeDocument（知识文档）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 文档唯一标识 |
| knowledge_base_id | UUID | FK → KnowledgeBase.id, NOT NULL | 所属知识库 |
| title | VARCHAR(256) | NOT NULL | 文档标题（如菜名） |
| content | TEXT | NOT NULL | 解析后的文档内容（已过滤无效字段） |
| source_format | VARCHAR(16) | NOT NULL | 原始格式（`json` / `markdown`） |
| source_filename | VARCHAR(256) | | 原始文件名 |
| metadata | JSONB | | 文档元信息（如分类标签、食材列表、营养成分） |
| index_status | VARCHAR(16) | DEFAULT 'pending' | 索引状态（pending/indexing/indexed/failed） |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

### DocumentChunk（文档分块 + 向量索引）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 分块唯一标识 |
| document_id | UUID | FK → KnowledgeDocument.id, NOT NULL | 所属文档 |
| chunk_text | TEXT | NOT NULL | 分块文本 |
| chunk_index | INTEGER | NOT NULL | 块在文档中的序号 |
| embedding | vector(768) | NOT NULL | pgvector 向量（768 维，对应 roberta-wwm-ext） |

**INDEX**: HNSW on embedding (cosine distance)

### Persona（闲聊人设）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 人设唯一标识 |
| name | VARCHAR(64) | NOT NULL | 助手名称（如"小厨"） |
| personality | TEXT | NOT NULL | 性格特征描述 |
| tone_style | TEXT | NOT NULL | 语气风格描述 |
| system_prompt | TEXT | NOT NULL | 生成的系统提示词（传递给 LLM） |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

### DialogProfile（对话方案）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 方案唯一标识 |
| name | VARCHAR(128) | NOT NULL | 方案名称（如"方案A - GPT-4o 活泼版"） |
| description | TEXT | | 方案描述 |
| llm_provider | VARCHAR(64) | NOT NULL | 大模型提供商标识（LiteLLM model name） |
| llm_config | JSONB | DEFAULT '{}' | 大模型参数（temperature、max_tokens 等） |
| persona_id | UUID | FK → Persona.id | 关联人设 |
| routing_strategy | VARCHAR(32) | DEFAULT 'command_first' | 路由策略（command_first / knowledge_first / balanced） |
| session_timeout_minutes | INTEGER | DEFAULT 10 | 会话超时时间（分钟） |
| intent_ids | UUID[] | | 关联的意图 ID 列表 |
| knowledge_base_ids | UUID[] | | 关联的知识库 ID 列表 |
| status | VARCHAR(16) | DEFAULT 'draft' | 方案状态（draft / testing / published / archived） |
| created_by | UUID | FK → User.id | 创建人 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

### PublishedVersion（发布版本）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 版本唯一标识 |
| version_number | VARCHAR(32) | UNIQUE, NOT NULL | 版本号（如 `v1.0.0`） |
| profile_id | UUID | FK → DialogProfile.id, NOT NULL | 关联对话方案 |
| profile_snapshot | JSONB | NOT NULL | 发布时对话方案的完整快照 |
| intent_snapshot | JSONB | NOT NULL | 发布时所有意图+槽位的完整快照 |
| model_artifact_path | VARCHAR(512) | | 小模型产物路径（ONNX 文件） |
| is_active | BOOLEAN | DEFAULT false | 是否为当前生效版本 |
| published_by | UUID | FK → User.id | 发布人 |
| published_at | TIMESTAMP | NOT NULL | 发布时间 |
| deactivated_at | TIMESTAMP | | 失效时间 |

**约束**: 同一时间仅一条 `is_active = true`（通过应用层保证，发布新版时先将旧版 is_active 设为 false）

### TestSuite（测试集）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 测试集唯一标识 |
| name | VARCHAR(128) | NOT NULL | 测试集名称 |
| profile_id | UUID | FK → DialogProfile.id, NOT NULL | 关联对话方案 |
| generation_config | JSONB | | 自动生成配置 |
| created_by | UUID | FK → User.id | 创建人 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

### TestCase（测试用例）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 用例唯一标识 |
| suite_id | UUID | FK → TestSuite.id, NOT NULL | 所属测试集 |
| case_number | INTEGER | NOT NULL | 用例编号 |
| input_text | TEXT | NOT NULL | 用例语句 |
| expected_route | VARCHAR(32) | | 预期路由（command/knowledge/chitchat） |
| expected_intent | VARCHAR(128) | | 预期意图标识 |
| expected_slots | JSONB | | 预期槽位 |
| is_manually_tuned | BOOLEAN | DEFAULT false | 是否已手动微调 |
| device_context | JSONB | | 模拟设备上下文 |

### TestReport（测试报告）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 报告唯一标识 |
| suite_id | UUID | FK → TestSuite.id, NOT NULL | 关联测试集 |
| total_cases | INTEGER | NOT NULL | 总用例数 |
| passed_cases | INTEGER | NOT NULL | 通过用例数 |
| accuracy | DECIMAL(5,4) | NOT NULL | 准确率 |
| avg_latency_ms | INTEGER | NOT NULL | 平均延迟 |
| p95_latency_ms | INTEGER | NOT NULL | P95 延迟 |
| is_passed | BOOLEAN | NOT NULL | 是否达标 |
| results_detail | JSONB | NOT NULL | 每条用例的详细结果 |
| analysis_report | JSONB | | 智能分析报告（混淆矩阵、归因分析、优化建议） |
| executed_at | TIMESTAMP | NOT NULL | 执行时间 |

### RequestLog（请求日志）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 日志唯一标识 |
| request_id | VARCHAR(64) | UNIQUE, NOT NULL | 请求追踪 ID |
| device_id | VARCHAR(128) | NOT NULL, INDEX | 设备标识 |
| session_id | VARCHAR(128) | NOT NULL, INDEX | 会话标识 |
| version_id | UUID | FK → PublishedVersion.id | 使用的版本 |
| input_text | TEXT | NOT NULL | 输入文本 |
| detected_language | VARCHAR(8) | | 检测到的语言 |
| route_result | VARCHAR(32) | NOT NULL | 路由结果（command/knowledge/chitchat） |
| route_confidence | DECIMAL(5,4) | | 路由置信度 |
| intent_result | VARCHAR(128) | | 意图标识（指令域） |
| intent_confidence | DECIMAL(5,4) | | 意图置信度 |
| slots_extracted | JSONB | | 提取的槽位 |
| response_text | TEXT | NOT NULL | 响应文本 |
| knowledge_hit | JSONB | | 命中的知识库条目（知识域） |
| device_context | JSONB | | 请求时的设备上下文 |
| latency_ms | INTEGER | NOT NULL | 处理耗时（毫秒） |
| is_error | BOOLEAN | DEFAULT false | 是否异常 |
| error_detail | TEXT | | 异常详情 |
| created_at | TIMESTAMP | NOT NULL, INDEX | 请求时间 |

**索引**: (device_id, created_at), (session_id), (route_result, created_at), (intent_result, created_at)
**分区**: 按 created_at 月度分区（请求量增长后启用）

### AlertRule（告警规则）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 规则唯一标识 |
| name | VARCHAR(128) | NOT NULL | 规则名称 |
| metric_name | VARCHAR(64) | NOT NULL | 监控指标（accuracy / p95_latency / error_rate） |
| operator | VARCHAR(8) | NOT NULL | 比较运算符（lt / gt / lte / gte） |
| threshold | DECIMAL(10,4) | NOT NULL | 阈值 |
| duration_minutes | INTEGER | NOT NULL | 持续时间（分钟） |
| notification_config | JSONB | NOT NULL | 通知配置（邮件/webhook） |
| is_enabled | BOOLEAN | DEFAULT true | 是否启用 |
| created_by | UUID | FK → User.id | 创建人 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

---

## 运行时实体（Redis）

### DeviceSession（设备会话）

**Key 格式**: `session:{device_id}`
**TTL**: 由 DialogProfile.session_timeout_minutes 配置（默认 600 秒）

```json
{
  "session_id": "uuid",
  "device_id": "device_001",
  "version_id": "uuid",
  "state": "IDLE",
  "current_domain": null,
  "dialog_history": [
    {
      "turn": 1,
      "user_text": "搜个红烧肉",
      "route": "command",
      "intent": "search_recipe_by_cuisine_type",
      "slots": { "food_name": "红烧肉" },
      "response": "为您搜索红烧肉相关菜谱...",
      "timestamp": "2026-03-03T10:00:00Z"
    }
  ],
  "entity_stack": [
    { "type": "food_name", "value": "红烧肉", "turn": 1 }
  ],
  "pending_slots": null,
  "active_intent": null,
  "created_at": "2026-03-03T10:00:00Z",
  "last_active_at": "2026-03-03T10:00:05Z"
}
```

---

## 状态转换

### 对话会话状态机

```
                    ┌─────────────────────────────────────┐
                    │                                     │
                    ▼                                     │
  [NEW] ──→ [IDLE] ──→ [ROUTING] ──┬──→ [COMMAND_PROCESSING] ──┬──→ [IDLE]
              ▲                    │                           │
              │                    │    ┌── [SLOT_PROMPTING] ◄─┘
              │                    │    │         │
              │                    │    └─────────┘ (用户回复填充槽位)
              │                    │
              │                    ├──→ [KNOWLEDGE_QA] ──→ [IDLE]
              │                    │
              │                    └──→ [CHITCHAT] ──→ [IDLE]
              │
              │
  [TIMEOUT] ──┘  (超时自动清除，TTL 过期)
  [VERSION_RESET] ─┘  (新版本发布，批量清除)
```

### 对话方案状态

```
  [draft] ──→ [testing] ──→ [published] ──→ [archived]
     ▲            │                            │
     └────────────┘ (回退修改)                  │
     └─────────────────────────────────────────┘ (基于旧版创建新方案)
```

### 知识文档索引状态

```
  [pending] ──→ [indexing] ──→ [indexed]
                    │
                    └──→ [failed] ──→ [pending] (重试)
```
