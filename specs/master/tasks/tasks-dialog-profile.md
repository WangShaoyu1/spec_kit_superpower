# 对话方案 (Dialog Profile) 任务

**PD 交互原型**: pd-all/pd-dialog-profile/ (3 pages: index, detail, test-chat)
**架构设计**: ad/ad-dialog-profile.md
**详细设计**: dd/dd-dialog-profile.md
**优先级**: P1
**依赖**: tasks-infra.md 必须先完成; 与 tasks-intent-library.md 有跨模块引用 (指令库绑定/发布门禁)

## 测试任务（TDD: 先写测试, 确保红灯）

### 契约测试（覆盖 AD API — 22 端点）

- [ ] T001 [P] [T-CONTRACT] 方案 CRUD 契约测试: GET/POST /profiles, GET/PUT/DELETE /profiles/{id}
  - 文件: `backend/tests/contract/test_profiles_api.py`
  - 依据: ad/ad-dialog-profile.md §3.1
- [ ] T002 [P] [T-CONTRACT] 人设 CRUD + 激活 契约测试: GET/POST/PUT/DELETE /profiles/{id}/personas, POST /profiles/{id}/personas/{pid}/activate
  - 文件: `backend/tests/contract/test_personas_api.py`
  - 依据: ad/ad-dialog-profile.md §3.2
- [ ] T003 [P] [T-CONTRACT] 手动测试 契约测试: POST /profiles/{id}/test/chat, POST/GET/PUT/DELETE sessions, GET/DELETE messages
  - 文件: `backend/tests/contract/test_profile_testing_api.py`
  - 依据: ad/ad-dialog-profile.md §3.3
- [ ] T004 [P] [T-CONTRACT] 发布 + 版本 契约测试: POST /profiles/{id}/publish, GET /profiles/{id}/versions, GET /versions/{vid}
  - 文件: `backend/tests/contract/test_profile_versions_api.py`
  - 依据: ad/ad-dialog-profile.md §3.4
- [ ] T005 [P] [T-CONTRACT] 指令库绑定 契约测试: GET/PUT /profiles/{id}/intent-libraries
  - 文件: `backend/tests/contract/test_profile_bindings_api.py`
  - 依据: ad/ad-dialog-profile.md §3.5

### 集成测试（覆盖 AD 数据流）

- [ ] T006 [P] [T-INTEGRATION] 方案发布流程集成测试: 发布门禁校验→版本快照→状态推进
  - 文件: `backend/tests/integration/test_profile_publish.py`
  - 依据: ad/ad-dialog-profile.md §2.3 版本发布数据流
- [ ] T007 [P] [T-INTEGRATION] 手动测试流程集成测试: 创建会话→发送消息→NLU管道→响应
  - 文件: `backend/tests/integration/test_manual_test_flow.py`
  - 依据: ad/ad-dialog-profile.md §2.2 手动测试数据流

### E2E 测试（覆盖 PD 交互路径）

- [ ] T008 [P] [T-E2E] 方案列表页 E2E: 搜索/新建/编辑/删除/发布 交互路径
  - 文件: `frontend/tests/e2e/dialog-profile-list.spec.js`
  - 依据: pd-all/pd-dialog-profile/index.html
- [ ] T009 [P] [T-E2E] 手动测试页 E2E: 会话创建/消息发送/调试面板 交互路径
  - 文件: `frontend/tests/e2e/dialog-profile-test.spec.js`
  - 依据: pd-all/pd-dialog-profile/test-chat.html

## 后端任务

### 数据模型（来自 DD 实体定义）

- [ ] T010 [P] [B-MODEL] 创建 DialogProfile ORM 模型 (id, name, description, status, command_threshold, route_strategy, created_by)
  - 文件: `backend/app/models/dialog_profile.py`
  - 依据: dd/dd-dialog-profile.md §1.1
- [ ] T011 [P] [B-MODEL] 创建 Persona ORM 模型 (id, profile_id, name, system_prompt, temperature, is_active)
  - 文件: `backend/app/models/persona.py`
  - 依据: dd/dd-dialog-profile.md §1.2
- [ ] T012 [P] [B-MODEL] 创建 ProfileLibraryBinding 关联模型 (profile_id, library_id, priority)
  - 文件: `backend/app/models/profile_binding.py`
  - 依据: dd/dd-dialog-profile.md §1.3
- [ ] T013 [P] [B-MODEL] 创建 ProfileTestSession / ProfileTestMessage ORM 模型
  - 文件: `backend/app/models/profile_test.py`
  - 依据: dd/dd-dialog-profile.md §1.4~§1.5
- [ ] T014 [P] [B-MODEL] 创建 Pydantic Schema (Profile/Persona/Binding/TestSession/TestMessage Request/Response)
  - 文件: `backend/app/schemas/profile.py`
- [ ] T015 [B-MODEL] 生成 Alembic 迁移并运行 (dialog_profiles, personas, profile_library_bindings, profile_test_sessions, profile_test_messages 表)
  - 文件: `backend/migrations/versions/004_dialog_profile.py`

### 服务层（来自 DD 算法）

- [ ] T016 [B-SERVICE] 方案 CRUD 服务 (含草稿/发布状态管理)
  - 文件: `backend/app/services/profile_service.py`
  - 依据: dd/dd-dialog-profile.md §4.1
- [ ] T017 [B-SERVICE] 人设管理服务 (CRUD + 激活互斥: 同方案仅一个 active)
  - 文件: `backend/app/services/persona_service.py`
  - 依据: dd/dd-dialog-profile.md §4.2
- [ ] T018 [B-SERVICE] 指令库绑定服务 (多对多关联 + 优先级排序)
  - 文件: `backend/app/services/binding_service.py`
  - 依据: dd/dd-dialog-profile.md §4.3
- [ ] T019 [B-SERVICE] 发布门禁校验服务 (检查绑定库是否均有 published 模型)
  - 文件: `backend/app/services/version/publisher.py`
  - 依据: dd/dd-dialog-profile.md §4.4 发布门禁算法
- [ ] T020 [B-SERVICE] 版本快照创建服务 (config_snapshot + 版本号递增)
  - 文件: `backend/app/services/version/publisher.py` (扩展)
  - 依据: dd/dd-dialog-profile.md §4.5
- [ ] T021 [B-SERVICE] 手动测试消息处理服务 (创建会话→调用 NLU 管道→返回分域结果+调试信息)
  - 文件: `backend/app/services/testing/manual_test.py`
  - 依据: dd/dd-dialog-profile.md §4.6
- [ ] T022 [B-SERVICE] NLU 主管道调度服务 (文本预处理→路由→分域处理→响应构建)
  - 文件: `backend/app/services/nlu/pipeline.py`
  - 依据: ad/ad-global.md §5.1 对话推理数据流
- [ ] T023 [B-SERVICE] 域路由服务 (指令/知识/闲聊 三域路由)
  - 文件: `backend/app/services/nlu/router.py`
  - 依据: ad/ad-global.md §5.1 路由策略
- [ ] T024 [B-SERVICE] 闲聊域服务 (人设 prompt 注入 + LLM 调用 + 联网搜索)
  - 文件: `backend/app/services/chitchat/llm_adapter.py`, `backend/app/services/chitchat/persona.py`
  - 依据: dd/dd-dialog-profile.md §4.7
- [ ] T025 [B-SERVICE] 设备会话管理服务 (Redis 会话创建/更新/过期)
  - 文件: `backend/app/services/session/device_session.py`, `backend/app/services/session/context.py`
  - 依据: dd/dd-global.md §1.5 DeviceSession

### API 端点（来自 AD 接口契约）

- [ ] T026 [B-API] 方案 CRUD API: GET/POST /profiles, GET/PUT/DELETE /profiles/{id}
  - 文件: `backend/app/api/v1/profiles.py`
  - 依据: ad/ad-dialog-profile.md §3.1
- [ ] T027 [B-API] 人设 CRUD + 激活 API
  - 文件: `backend/app/api/v1/profiles.py` (扩展)
  - 依据: ad/ad-dialog-profile.md §3.2
- [ ] T028 [B-API] 手动测试 API: chat + sessions CRUD + messages
  - 文件: `backend/app/api/v1/testing.py`
  - 依据: ad/ad-dialog-profile.md §3.3
- [ ] T029 [B-API] 发布 + 版本历史 API
  - 文件: `backend/app/api/v1/versions.py`
  - 依据: ad/ad-dialog-profile.md §3.4
- [ ] T030 [B-API] 指令库绑定 API: GET/PUT /profiles/{id}/intent-libraries
  - 文件: `backend/app/api/v1/profiles.py` (扩展)
  - 依据: ad/ad-dialog-profile.md §3.5
- [ ] T031 [B-API] 对话推理 API: POST /dialog (设备端调用入口)
  - 文件: `backend/app/api/v1/dialog.py`
  - 依据: ad/ad-global.md §3.1

## 前端任务

### 页面（来自 PD 交互原型）

- [ ] T032 [F-PAGE] 方案列表页: 搜索+Table+新建弹窗+编辑弹窗+发布按钮+状态筛选
  - 文件: `frontend/src/pages/DialogProfile/index.jsx`
  - 依据: pd-all/pd-dialog-profile/index.html
  - PD UI Checklist:
    - [ ] 统计卡片 x4: 方案总数 / 已发布(绿) / 草稿(蓝) / 测试中(黄) — Statistic 组件, Row gutter=24 Col span=6
    - [ ] 筛选栏: 搜索方案名称(Input+SearchOutlined) + 状态筛选(Select: draft/testing/published/archived) + 策略筛选(Select: command_first/knowledge_first/balanced) + 查询按钮(primary) + 重置按钮
    - [ ] 数据表格 10 列: 方案名称(链接+ID副文本) / 状态(Tag色映射) / 大模型 / 路由策略(Tag色映射) / 绑定指令库(Badge count) / 人设 / 指令阈值(monospace .toFixed(2)) / 会话超时(N分钟) / 更新时间 / 操作(查看/编辑/删除); scroll.x=1400, 操作列 fixed right
    - [ ] 分页: showSizeChanger + showQuickJumper + showTotal
    - [ ] 新建方案按钮: primary + PlusOutlined, 权限控制 canCreate (测试人员禁用+Tooltip)
    - [ ] 新建/编辑方案 Modal: Form 含 name / llmModel(Select) / routingStrategy(Select) / personaName(Select) / sessionTimeout(InputNumber 1~60) / commandThreshold(Slider 0~1 step 0.05 + InputNumber 联动) / libraries(Select mode=multiple 含发布状态标记) + 底部 Alert 发布校验提示
    - [ ] 删除确认 Modal: okType=danger, 展示方案名称 + Alert 不可恢复警告
    - [ ] 角色切换 Select (admin/pm/tester), 动态控制编辑/删除按钮权限
- [ ] T033 [F-PAGE] 方案详情页: 基本信息+人设管理+指令库绑定配置+版本历史
  - 文件: `frontend/src/pages/DialogProfile/Detail.jsx`
  - 依据: pd-all/pd-dialog-profile/detail.html
  - PD UI Checklist:
    - [ ] 页头: 返回按钮(ArrowLeftOutlined) + 方案名称+状态Tag + 手动测试按钮(MessageOutlined) + 发布按钮(RocketOutlined, primary/danger, profile_publish 权限守卫+Tooltip)
    - [ ] 基本信息 Card: Descriptions 3列 bordered — 方案名称/状态(Tag)/大模型/路由策略(Tag)/会话超时/指令阈值/当前发布版本(Tag purple)/创建时间/更新时间; extra=编辑基本信息按钮(EditOutlined)
    - [ ] 编辑基本信息 Modal: Form 含 name / llmModel(Select) / routeStrategy(Select) / intentThreshold(Slider 0~1 step 0.05 + InputNumber 联动) / sessionTimeout(InputNumber 1~60)
    - [ ] 已绑定指令库 Card: 标题含 Badge count; extra=绑定指令库按钮(LinkOutlined, primary); 顶部 Alert 说明多语种路由; Table 6列: 指令库名称(链接) / library_key(code) / 语种(Tag色映射) / 意图数 / Published模型(✓绿/✗红+版本号) / 操作(解绑按钮 danger+二次确认)
    - [ ] 绑定指令库 Modal (800px): Alert 说明 + Table 5列含 rowSelection 多选, 已绑定库预选中
    - [ ] 闲聊人设配置 Card: extra=切换人设(SwapOutlined) + 编辑人设(EditOutlined) + 新建人设(PlusOutlined dashed); 内容=persona-card (active态蓝色边框背景+badge"当前使用") + Descriptions: 助手名称(SmileOutlined)/性格特征/语气风格
    - [ ] 切换人设 Modal (700px, footer=null): Row/Col Grid span=8 展示所有人设卡片, 当前人设标记"当前"badge, 非当前人设含"选择此人设"按钮
    - [ ] 人设编辑/新建 Modal: Form 含 name(助手名称) / personality(性格特征 TextArea) / toneStyle(语气风格 TextArea)
    - [ ] 发布确认 Modal (700px): ① Alert 红色警告"影响所有在线设备"; ② 校验清单(逐项✓/✗: 绑定库/每库published模型/人设/大模型); ③ 版本对比卡片(旧版灰 vs 新版绿); ④ 影响统计(设备数+会话数, 橙色impact-stat); ⑤ Checkbox确认勾选; ⑥ 5秒安全倒计时(SafetyCertificateOutlined); 校验全通过+勾选+倒计时完成才可确认
    - [ ] 版本发布历史 Card: Timeline — 每项: 版本号(bold) + 当前生效Tag(green) + 时间(ClockCircleOutlined) + 描述; 当前=green, 历史=gray
- [ ] T034 [F-PAGE] 手动测试页: 聊天界面+调试面板(分域结果/置信度/耗时)+会话管理
  - 文件: `frontend/src/pages/TestChat/index.jsx`
  - 依据: pd-all/pd-dialog-profile/test-chat.html
  - PD UI Checklist:
    - [ ] 页头: 返回按钮(ArrowLeftOutlined→detail) + 页面标题"手动测试: {方案名}" + 设备上下文按钮(DesktopOutlined, toggle primary/default) + 新建会话按钮(PlusOutlined, primary)
    - [ ] 三栏布局: 会话列表(280px) | 聊天面板(flex:1) | 调试面板(360px); 高度 calc(100vh-180px)
    - [ ] 会话列表面板: 顶部标题"测试会话"+Badge count + 新建会话(dashed block) + 会话卡片列表(session-card: 名称省略号/关联方案Tag/创建时间/消息条数, 选中态蓝色左边框, hover显示删除按钮DeleteOutlined)
    - [ ] 设备上下文状态栏: 黄色背景条(DesktopOutlined + 摘要文字: 烹饪状态/炉门/温度°C/当前页面), 位于聊天面板顶部
    - [ ] 设备上下文配置面板 (可折叠Card): 快捷预设按钮x3(空闲-主页/正在烹饪/菜谱浏览) + Divider + 5列表单(cooking_status Select / door_closed Switch / current_temp InputNumber 0~300°C / current_page Select / screen_info Input) + 应用按钮(primary small)
    - [ ] 聊天消息区: 用户消息(蓝色气泡右对齐, 蓝色圆形头像UserOutlined) + 机器人消息(灰色气泡左对齐, 紫色圆形头像RobotOutlined) + 时间戳; bot消息下方debug-info条(可点击选中, 含domain Tag + intent Tag + responseTime色阶 + "展开调试信息"提示)
    - [ ] Typing指示器: 三圆点跳动动画, 发送等待回复时展示
    - [ ] 消息输入区: TextArea(autoSize 1~4行) + 发送按钮(SendOutlined primary); Enter发送, Shift+Enter换行; 发送中disabled+loading; 底部提示"Enter 发送, Shift+Enter 换行"
    - [ ] 空会话占位: RobotOutlined(48px) + "输入测试消息开始对话" + 示例消息提示
    - [ ] 调试面板 9 区段: ① 路由判断(NodeIndexOutlined: domain Tag + confidence Progress色阶); ② 意图识别(AimOutlined: intent name Tag + confidence%, 仅command); ③ 槽位提取(TagOutlined: Table 3列 name/value含"已消解"Tag/type, 仅command); ④ 指代消解(BranchesOutlined: pronoun→resolved Card, 条件显示); ⑤ 知识库命中(FileTextOutlined: docName/category Tag/score%, 仅knowledge); ⑥ 人设应用(RobotOutlined: name + applied Tag绿/红, 仅chitchat); ⑦ 对话状态(ApiOutlined: previousDomain→currentDomain + slotsFilled Tag); ⑧ 响应耗时(ClockCircleOutlined: Statistic ms, 色阶<200绿/<2000蓝/<4000橙/≥4000红); ⑨ 使用模型(DesktopOutlined: Tag geekblue)
    - [ ] 未选中调试时占位: BugOutlined(40px) + "点击任意机器人回复查看调试信息"
    - [ ] 新建会话 Modal: Form 含 name(会话名称 required) / profile(关联方案 Select) / preset(设备上下文预设 Select: idle/cooking/recipe/custom) / remark(备注 TextArea)

### 组件（可复用）

- [ ] T035 [P] [F-COMPONENT] 人设编辑器组件 (system_prompt 编辑+预览+参数配置)
  - 文件: `frontend/src/pages/DialogProfile/PersonaEditor.jsx`
- [ ] T036 [P] [F-COMPONENT] 指令库绑定选择器组件 (多选+优先级排序+阈值配置)
  - 文件: `frontend/src/pages/DialogProfile/LibrarySelector.jsx`

### 状态管理与 API 对接

- [ ] T037 [F-STORE] 方案状态管理 (zustand): 方案列表/当前方案/人设/会话
  - 文件: `frontend/src/stores/profileStore.js`
- [ ] T038 [F-API] 方案 API 对接层: 全部 22 端点的前端调用封装
  - 文件: `frontend/src/services/profileApi.js`

## 检查点

**模块验收标准**（对照 PD 交互稿）:
- [ ] 所有测试通过（T001~T009 红灯→绿灯）
- [ ] 方案列表: CRUD + 状态筛选全链路可用
- [ ] 人设管理: 创建/编辑/激活互斥 可用
- [ ] 指令库绑定: 多选+优先级+阈值配置 可用
- [ ] 发布门禁: 绑定库缺少 published 模型时正确阻断
- [ ] 手动测试: 会话创建→消息发送→NLU 管道→三域分类结果+调试信息展示
- [ ] 版本历史: 发布后可查看历史版本快照
- [ ] 对话推理 API: POST /dialog 端到端可用
- [ ] 无回归（infra + 先前模块测试仍通过）
