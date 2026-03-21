# 知识库管理 (Knowledge Base) 任务

**PD 交互原型**: pd-all/pd-knowledge-base/ (2 pages: index, detail)
**架构设计**: ad/ad-knowledge-base.md
**详细设计**: dd/dd-knowledge-base.md
**优先级**: P1
**依赖**: tasks-infra.md 必须先完成

## 测试任务（TDD: 先写测试, 确保红灯）

### 契约测试（覆盖 AD API — 12 端点）

- [ ] T001 [P] [T-CONTRACT] 分类 CRUD 契约测试: GET/POST /knowledge/categories, GET/PUT/DELETE /knowledge/categories/{id}
  - 文件: `backend/tests/contract/test_knowledge_categories_api.py`
  - 依据: ad/ad-knowledge-base.md §3.1
- [ ] T002 [P] [T-CONTRACT] 文档 CRUD + 上传 + 重新索引 契约测试: GET/POST /knowledge/documents, GET/PUT/DELETE /knowledge/documents/{id}, POST /knowledge/documents/{id}/reindex
  - 文件: `backend/tests/contract/test_knowledge_documents_api.py`
  - 依据: ad/ad-knowledge-base.md §3.2
- [ ] T003 [P] [T-CONTRACT] 知识检索测试 契约测试: POST /knowledge/search
  - 文件: `backend/tests/contract/test_knowledge_search_api.py`
  - 依据: ad/ad-knowledge-base.md §3.3

### 集成测试（覆盖 AD 数据流）

- [ ] T004 [P] [T-INTEGRATION] 文档上传→解析→分块→向量索引 端到端集成测试
  - 文件: `backend/tests/integration/test_document_indexing.py`
  - 依据: ad/ad-knowledge-base.md §2.1 文档上传索引数据流
- [ ] T005 [P] [T-INTEGRATION] 语义检索集成测试: 查询→向量化→相似度匹配→结果排序
  - 文件: `backend/tests/integration/test_knowledge_retrieval.py`
  - 依据: ad/ad-knowledge-base.md §2.2 检索数据流

### E2E 测试（覆盖 PD 交互路径）

- [ ] T006 [P] [T-E2E] 知识库列表页 E2E: 分类管理+文档上传+搜索筛选
  - 文件: `frontend/tests/e2e/knowledge-base-list.spec.js`
  - 依据: pd-all/pd-knowledge-base/index.html
- [ ] T007 [P] [T-E2E] 文档详情页 E2E: 分块预览+检索测试
  - 文件: `frontend/tests/e2e/knowledge-base-detail.spec.js`
  - 依据: pd-all/pd-knowledge-base/detail.html

## 后端任务

### 数据模型（来自 DD 实体定义）

- [ ] T008 [P] [B-MODEL] 创建 KnowledgeCategory ORM 模型 (id, name, description, parent_id, sort_order)
  - 文件: `backend/app/models/knowledge.py`
  - 依据: dd/dd-knowledge-base.md §1.1
- [ ] T009 [P] [B-MODEL] 创建 KnowledgeDocument ORM 模型 (id, title, category_id, file_path, file_type, file_size, status, chunk_count, error_message)
  - 文件: `backend/app/models/knowledge.py` (扩展)
  - 依据: dd/dd-knowledge-base.md §1.2
- [ ] T010 [P] [B-MODEL] 创建 DocumentChunk ORM 模型 (id, document_id, chunk_index, content, embedding, token_count) + pgvector 列
  - 文件: `backend/app/models/knowledge.py` (扩展)
  - 依据: dd/dd-knowledge-base.md §1.3
- [ ] T011 [P] [B-MODEL] 创建 Pydantic Schema (Category/Document/Chunk Request/Response)
  - 文件: `backend/app/schemas/knowledge.py`
- [ ] T012 [B-MODEL] 生成 Alembic 迁移并运行 (knowledge_categories, knowledge_documents, document_chunks 表 + pgvector 扩展)
  - 文件: `backend/migrations/versions/003_knowledge_base.py`

### 服务层（来自 DD 算法）

- [ ] T013 [B-SERVICE] 分类管理服务 (CRUD + 树形结构 + 级联删除校验)
  - 文件: `backend/app/services/knowledge/category_service.py`
  - 依据: dd/dd-knowledge-base.md §4.1
- [ ] T014 [B-SERVICE] 文档解析服务 (PDF/TXT/DOCX/Excel 解析 + 字段过滤黑名单)
  - 文件: `backend/app/services/knowledge/indexer.py`
  - 依据: dd/dd-knowledge-base.md §4.2 文档解析算法
- [ ] T015 [B-SERVICE] 分块策略服务 (按段落/固定长度分块 + overlap)
  - 文件: `backend/app/services/knowledge/indexer.py` (扩展)
  - 依据: dd/dd-knowledge-base.md §4.3 分块策略
- [ ] T016 [B-SERVICE] 向量索引服务 (embedding 生成 + pgvector HNSW 索引构建)
  - 文件: `backend/app/services/knowledge/indexer.py` (扩展)
  - 依据: dd/dd-knowledge-base.md §4.4 向量索引构建
- [ ] T017 [B-SERVICE] 语义检索服务 (查询向量化 + 相似度匹配 + 结果排序 + 上下文拼接)
  - 文件: `backend/app/services/knowledge/retriever.py`
  - 依据: dd/dd-knowledge-base.md §4.5 语义检索算法
- [ ] T018 [B-SERVICE] 知识问答生成服务 (检索结果 + LLM prompt → 回答)
  - 文件: `backend/app/services/knowledge/qa_generator.py`
  - 依据: dd/dd-knowledge-base.md §4.6

### API 端点（来自 AD 接口契约）

- [ ] T019 [B-API] 分类 CRUD API: GET/POST /knowledge/categories, GET/PUT/DELETE /knowledge/categories/{id}
  - 文件: `backend/app/api/v1/knowledge.py`
  - 依据: ad/ad-knowledge-base.md §3.1
- [ ] T020 [B-API] 文档 CRUD + 上传 + 重新索引 API: GET/POST /documents, GET/PUT/DELETE /documents/{id}, POST /documents/{id}/reindex
  - 文件: `backend/app/api/v1/knowledge.py` (扩展)
  - 依据: ad/ad-knowledge-base.md §3.2
- [ ] T021 [B-API] 知识检索测试 API: POST /knowledge/search
  - 文件: `backend/app/api/v1/knowledge.py` (扩展)
  - 依据: ad/ad-knowledge-base.md §3.3

## 前端任务

### 页面（来自 PD 交互原型）

- [ ] T022 [F-PAGE] 知识库列表页: 分类树+文档列表Table+上传弹窗+搜索筛选+统计卡片
  - 文件: `frontend/src/pages/KnowledgeBase/index.jsx`
  - 依据: pd-all/pd-knowledge-base/index.html
  - PD UI Checklist:
    - [ ] 统计卡片 (4 张 Statistic): 分类总数 (FolderOutlined)、文档总数 (千分位)、已索引 (绿色 #52c41a)、索引中 (蓝色 #1890ff)
    - [ ] 分类选择面板 (左侧 320px): 分类卡片列表 (emoji 图标 + 名称 + Badge docCount + 描述); active 蓝色高亮; 行内编辑 (EditOutlined) / 删除 (DeleteOutlined danger) 按钮; 底部虚线"新建分类"按钮
    - [ ] 分类详情头: 选中分类 (图标 + 名称 + 状态 Tag ready→green / indexing→blue+spin + 描述 + 文档数/已索引数); "上传文档" (primary) + "检索测试" 按钮
    - [ ] 筛选栏 (Row/Col): 搜索文档名称 (Input + SearchOutlined + allowClear)、格式下拉 (Select: JSON/Markdown/TXT)、状态下拉 (Select: 已索引/索引中/失败)、重置按钮
    - [ ] 文档列表 Table (7 列): 文档名称 (a 链接→详情)、格式 (Tag: json→blue / markdown→green / txt→orange)、大小、有效字段/总字段 (monospace + 颜色比率 + Tooltip 过滤字段 + 灰色 -N)、状态 (Tag+图标)、上传时间、操作列
    - [ ] 操作列按钮: 查看 (EyeOutlined link→详情页)、重新索引 (ReloadOutlined link + Tooltip)、删除 (DeleteOutlined link danger→确认 Modal)
    - [ ] 分页: showSizeChanger + showQuickJumper + showTotal
    - [ ] 上传文档 Modal (640px): Dragger 拖拽区 (accept .json/.md/.markdown/.txt, multiple)、Progress 上传进度、字段过滤预览 (有效 green Tag + 无效 red 删除线 Tag)、Alert 解析说明
    - [ ] 分类创建/编辑 Modal (480px): Form 名称 (Input maxLength=30 required)、图标 (Select emoji 预设 5 项 required)、描述 (TextArea maxLength=200 showCount); 编辑时回填数据
    - [ ] 检索测试 Modal (700px): Space.Compact (Input + 搜索按钮); 结果 List (文档名 + 匹配度 Tag ≥80 green / ≥50 orange / default + Progress + snippet HTML 高亮 em); 无结果 Empty
    - [ ] 删除确认 Modal: 区分分类/文档; okType danger; Alert 不可恢复警告; 分类删除提示级联删除文档+索引
    - [ ] 未选分类时: 右侧 Empty "请从左侧选择知识库分类"
    - [ ] 页面头部: 新建分类按钮 (PlusOutlined primary)
- [ ] T023 [F-PAGE] 文档详情页: 元信息+分块预览列表+检索测试面板+重新索引操作
  - 文件: `frontend/src/pages/KnowledgeBase/Detail.jsx`
  - 依据: pd-all/pd-knowledge-base/detail.html
  - PD UI Checklist:
    - [ ] 页面头部: 返回按钮 (ArrowLeftOutlined→列表页) + 文档名称 + 状态 Tag (green "已索引"); 右侧: 重新索引 (ReloadOutlined) + 删除文档 (DeleteOutlined danger)
    - [ ] 文档基本信息: Descriptions (bordered, column=3) — 文档名称 (FileJsonOutlined)、所属分类 (emoji)、格式 (Tag blue)、大小、状态 (Tag green)、上传时间、索引时间、索引版本 (Tag)
    - [ ] 字段解析结果 (FR-005 标识): 左右分栏 Row(Col 13 + Col 11); 左: 绿色边框卡片 "有效字段(已保留)" CheckCircleOutlined + Table (字段 code 绿 / 值 ellipsis / 类型 Tag green); 右: 灰色边框卡片 "无效字段(已过滤)" CloseCircleOutlined + Table (字段 code 删除线 / 原值删除线 / 过滤原因 Tag); 底部 Alert 保留率统计
    - [ ] 索引内容预览: recipe-preview 卡片 — emoji 菜名 h2 + 描述 + Divider + 主料 ul + 辅料 ul + 步骤 ol (有序列表) + 营养 Tag 组 (volcano/orange/gold/lime) + 标签 Tag 组 (magenta/green/blue)
    - [ ] 检索测试面板: Alert 提示 + Input.Search (large, maxWidth=600) + 快速测试按钮组 (多个 link Button 预填检索词自动执行); 命中结果卡片 (绿色边框 #b7eb8f): CheckCircleOutlined + "匹配成功" Tag + 得分 Progress (#52c41a) + 匹配内容 (highlight 黄底 #ffe58f) + 响应预览 (蓝底 #e6f7ff)
    - [ ] 重新索引确认: Modal.confirm 二次确认 (ExclamationCircleOutlined + 提示索引期间检索不稳定)
    - [ ] 删除文档确认 Modal: Alert (error) 不可撤销 + 文档信息摘要 (名称/分类/状态) + 影响范围列表 (向量索引删除 / 知识问答失效 / 不可恢复); okButton danger

### 组件（可复用）

- [ ] T024 [P] [F-COMPONENT] 文档上传组件 (拖拽上传 + 进度条 + 格式校验)
  - 文件: `frontend/src/pages/KnowledgeBase/DocumentUpload.jsx`
- [ ] T025 [P] [F-COMPONENT] 文档状态Tag组件 (uploading/parsing/indexing/ready/error 颜色映射)
  - 文件: `frontend/src/components/DocumentStatusTag.jsx`

### 状态管理与 API 对接

- [ ] T026 [F-STORE] 知识库状态管理 (zustand): 分类树/文档列表/当前文档
  - 文件: `frontend/src/stores/knowledgeStore.js`
- [ ] T027 [F-API] 知识库 API 对接层: 全部 12 端点的前端调用封装
  - 文件: `frontend/src/services/knowledgeApi.js`

## 检查点

**模块验收标准**（对照 PD 交互稿）:
- [ ] 所有测试通过（T001~T007 红灯→绿灯）
- [ ] 分类管理: 树形CRUD全链路可用
- [ ] 文档上传: PDF/TXT/DOCX 上传→解析→分块→索引 完整流程
- [ ] 文档状态流转: uploading→parsing→indexing→ready 正确
- [ ] 语义检索: 输入查询→返回相关文档片段 可用
- [ ] 重新索引: 对已有文档执行重新索引成功
- [ ] 无回归（infra + 先前模块测试仍通过）
