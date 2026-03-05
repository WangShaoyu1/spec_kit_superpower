# 技术研究: SmartChef 智能对话管理平台

**日期**: 2026-03-03 | **阶段**: 0（研究）| **输入**: plan.md 中的 NEEDS CLARIFICATION 项

---

## 研究任务清单

| # | 未知项 | 状态 |
|---|--------|------|
| R1 | 知识检索向量数据库选型 | ✅ 已决策 |
| R2 | 联网搜索服务选型 | ✅ 已决策 |
| R3 | NLU 小模型架构选型 | ✅ 已决策 |
| R4 | 中文预训练基座模型选型 | ✅ 已决策 |
| R5 | 对话状态管理方案 | ✅ 已决策 |
| R6 | 大模型统一调用方案 | ✅ 已决策 |
| R7 | 设备端小模型推理部署方案 | ✅ 已决策 |
| R8 | 指代消解与省略恢复方案 | ✅ 已决策 |

---

## R1: 知识检索向量数据库选型

**Decision**: PostgreSQL + pgvector 扩展

**Rationale**:
- 项目已使用 PostgreSQL 作为主存储，pgvector 可避免引入额外中间件，降低运维复杂度
- 知识库规模约 1000 道菜谱 + 少量公司文档，向量规模预估 < 10 万条，pgvector 性能完全满足
- pgvector 支持 HNSW 索引，余弦相似度检索延迟在万级向量下 < 10ms
- 与 SQLAlchemy ORM 无缝集成，知识库元数据和向量索引在同一事务中管理
- 章程要求"简单方案优先"（YAGNI），不引入不必要的组件

**Alternatives considered**:
- **ChromaDB**: 轻量好用，但引入独立进程，增加部署复杂度；对于 < 10 万条的规模，pgvector 足够
- **Milvus**: 面向亿级向量的分布式方案，对本项目严重过度设计
- **Elasticsearch**: 全文+向量混合检索能力强，但运维成本高，对 2-3 人团队负担过重

---

## R2: 联网搜索服务选型

**Decision**: Tavily Search API

**Rationale**:
- AI-native 设计，返回清洗后的 Markdown 格式结果，可直接作为 LLM 上下文注入，无需额外解析
- 平均响应时间 ~1.9s，符合闲聊域 2-4s 的整体延迟预算
- 原生 LangChain 集成，与 LiteLLM + 大模型调用链路配合良好
- 定价合理（$5-8/千次查询），1000 次/月免费额度可覆盖开发和测试阶段
- 支持 Search、Extract、Crawl 等多种 API，未来可扩展至深度内容抓取

**Alternatives considered**:
- **SerpAPI**: 覆盖 40+ 搜索引擎，但返回原始 SERP 数据需额外预处理，价格更高（$15/千次），对 LLM 集成不友好
- **Bing Search API**: 已于 2025 年 8 月退役，不可用
- **自建爬虫**: 开发维护成本高，反爬对抗风险大，V1 阶段不现实

---

## R3: NLU 小模型架构选型

**Decision**: JointBERT 架构（联合意图分类 + 槽位提取）

**Rationale**:
- JointBERT 是意图分类 + 槽位填充联合任务的行业标准架构，单次前向推理同时输出意图和槽位
- 共享 BERT 编码层 + 意图分类头（[CLS] token → softmax）+ 槽位序列标注头（token-level → CRF/softmax），参数高效
- 联合训练使意图和槽位特征互相增强（如"设置温度180度"中，意图 set_cooking_temp 和槽位 number=180 互为上下文）
- 架构简单，易于导出 ONNX 格式，便于跨平台部署
- 在 ATIS/SNIPS 等标准数据集上意图准确率 > 97%，槽位 F1 > 95%

**Alternatives considered**:
- **独立意图模型 + 独立槽位模型**: 两个模型串行推理，延迟翻倍，且无法利用联合特征
- **大模型直接做 NLU**: 延迟 1-2s 远超 200ms 要求，且无法在 Jetson Nano 上运行
- **正则/规则匹配**: 讯飞旧方案，已被证明无法满足个性化需求

---

## R4: 中文预训练基座模型选型

**Decision**: chinese-roberta-wwm-ext（哈工大讯飞联合实验室）

**Rationale**:
- 专为中文优化，采用全词遮蔽（Whole Word Masking）策略，对中文分词边界敏感
- base 版本参数量 ~110M（与 BERT-base 同级），推理延迟可控
- 在中文 NLU 基准（CLUE）上持续表现优异，社区生态成熟
- 支持 Hugging Face Transformers，训练/微调/导出 ONNX 工具链完整
- 英文能力可通过 distilbert-base-uncased 独立模型补充，或通过翻译管道将英文输入转中文后统一处理

**Alternatives considered**:
- **bert-base-chinese**: Google 原版中文 BERT，但未使用全词遮蔽，中文效果略逊
- **ERNIE 3.0**: 百度出品，效果好但需百度云平台，与自研路线冲突
- **多语言 BERT (mBERT)**: 中英都支持但两边都不够精，中文效果明显弱于专用模型

---

## R5: 对话状态管理方案

**Decision**: Redis Hash + TTL 过期机制，配合有限状态机（FSM）

**Rationale**:
- Redis Hash 存储设备会话状态（对话历史、活跃槽位栈、当前域、上下文实体），key 格式 `session:{device_id}`
- TTL 实现可配置超时（默认 10 分钟），自动清除过期会话，无需额外定时任务
- 对话状态转换采用 FSM 模型：
  - `IDLE` → 收到输入 → `ROUTING` → 路由完成 → `COMMAND_FILLING` / `KNOWLEDGE_QA` / `CHITCHAT`
  - `COMMAND_FILLING` → 槽位完整 → `COMMAND_CONFIRMED` → 返回结构化指令 → `IDLE`
  - `COMMAND_FILLING` → 槽位缺失 → `SLOT_PROMPTING` → 用户回复 → `COMMAND_FILLING`
- 版本发布时通过 Redis SCAN + DEL 批量清除所有设备会话，实现上下文重置
- Redis 集群支持水平扩展，满足 10 QPS 并发无压力

**Alternatives considered**:
- **内存存储**: 简单但不支持多实例部署，服务重启丢失状态
- **PostgreSQL 存储会话**: 持久但每轮对话读写延迟高，不适合实时对话
- **专用对话引擎（Rasa Core）**: 功能强大但引入重量级依赖，与自研方案耦合

---

## R6: 大模型统一调用方案

**Decision**: LiteLLM Python SDK

**Rationale**:
- 提供统一 OpenAI 兼容接口，调用 100+ 模型提供商（GPT-4o、千问、DeepSeek、Claude 等），与"对话方案可配置大模型"需求完美契合
- 内置重试/降级逻辑，当主模型不可用时自动切换备用模型
- Python SDK 模式（非 Proxy 模式），直接集成到 FastAPI 服务中，无额外进程
- 支持流式输出（streaming），预留后续优化空间
- 生产级性能：~8ms P95 路由开销，对 2-4s 的闲聊响应时间影响可忽略

**Alternatives considered**:
- **直接调用各 LLM SDK**: 每个模型一套代码，切换成本高，对话方案配置需大量 if-else
- **LiteLLM Proxy Server**: 功能更丰富（多租户、计费），但对 2-3 人团队过度设计
- **LangChain ChatModel**: 抽象层太厚，调试困难，且绑定 LangChain 生态

---

## R7: 设备端小模型推理部署方案

**Decision**: ONNX Runtime C++ API

**Rationale**:
- ONNX Runtime 官方提供 C++ API，与设备端 Linux/C++/QT 技术栈完全兼容
- 支持 Jetson Nano 的 CUDA/TensorRT Execution Provider，可充分利用 GPU 算力
- JointBERT (chinese-roberta-wwm-ext base) ONNX 模型大小约 400MB，量化后 (INT8) 可压缩至 ~110MB
- INT8 量化后推理内存占用 < 500MB，在 1.1-1.5GB 可用内存约束内有充足余量
- 推理延迟（CPU fallback）: ~50-80ms，满足 200ms P95 要求
- 模型更新流程：云端训练 → 导出 ONNX → 量化 → 通过 OTA 推送到设备

**Alternatives considered**:
- **TensorRT 直接部署**: 性能更优但仅限 NVIDIA GPU，开发工具链复杂度高
- **NCNN/MNN**: 移动端推理框架，对 BERT 类模型支持不如 ONNX Runtime 成熟
- **TFLite**: TensorFlow 生态，与 PyTorch 训练管道不一致，转换损失风险

---

## R8: 指代消解与省略恢复方案

**Decision**: 基于大模型的上下文改写 + 规则辅助

**Rationale**:
- 对于闲聊/知识域：将最近 N 轮对话历史作为 LLM 上下文，让大模型在理解时自然处理指代和省略
- 对于指令域（需 < 200ms）：采用轻量规则引擎：
  - 指代消解：维护"实体栈"（最近提到的菜谱、温度、时间等），当检测到代词（"它"、"这个"、"那个"）时从栈顶取值
  - 省略恢复：当输入缺少关键实体但上下文有活跃实体时，自动继承（如上轮提到烤箱 → "关掉" 自动补全为"关掉烤箱"）
- 实体栈按域隔离存储在 Redis 会话中，随会话超时或版本更新一起清除
- 规则引擎 + 实体栈的延迟 < 5ms，不影响指令域整体 200ms 预算

**Alternatives considered**:
- **纯大模型处理**: 所有指代消解都走 LLM，延迟 1-2s，指令域不可接受
- **独立指代消解模型**: 需额外训练数据和模型维护成本，V1 阶段 ROI 低
- **纯规则引擎**: 覆盖率有限，复杂指代（如"刚才那个汤的做法"）难以处理

---

## 技术决策总览

| 领域 | 决策 | 关键理由 |
|------|------|---------|
| 向量数据库 | pgvector (PostgreSQL) | 复用现有基础设施，万级规模足够 |
| 联网搜索 | Tavily Search API | AI-native，LLM 友好，性价比高 |
| NLU 架构 | JointBERT（联合意图+槽位） | 行业标准，单次推理，ONNX 友好 |
| 中文基座 | chinese-roberta-wwm-ext | 中文 NLU 最优，全词遮蔽 |
| 对话状态 | Redis Hash + TTL + FSM | 低延迟，可配置超时，支持分布式 |
| LLM 适配 | LiteLLM Python SDK | 统一接口，100+ 模型，内置降级 |
| 设备端推理 | ONNX Runtime C++ | 跨平台，Jetson Nano 支持好 |
| 指代消解 | 规则引擎(指令域) + LLM(闲聊域) | 指令域保 200ms，闲聊域靠 LLM |
