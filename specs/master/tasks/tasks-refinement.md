# 横切关注点与完善 (Refinement) 任务

**目的**: 权限完善、性能优化、安全加固、文档收尾、端到端集成验证
**设计依据**: plan.md §阶段3~§阶段4 + dd/dd-global.md §3~§6 + ad/ad-global.md §6
**依赖**: 所有 PD 模块任务基本完成后执行

## 权限完善

- [ ] T001 [B-SERVICE] 完善全部 21 个能力点在各 API 端点的绑定与校验
  - 文件: 所有 `backend/app/api/v1/*.py` (逐个添加 `require_capability` 装饰器)
  - 依据: dd/dd-global.md §3 RBAC 能力点清单
- [ ] T002 [P] [T-INTEGRATION] 完整 RBAC 集成测试: 每个角色(管理员/PM/测试人员)对每个端点的权限验证
  - 文件: `backend/tests/integration/test_rbac_full.py`
  - 依据: dd/dd-global.md §3 能力点矩阵
- [ ] T003 [F-COMPONENT] 前端权限守卫: 无权限按钮禁用+Tooltip+403 页面
  - 文件: `frontend/src/components/PermissionGuard.jsx`, `frontend/src/pages/403.jsx`
  - 依据: pd-template.md §8.3 权限交互规范

## 安全加固

- [ ] T004 [P] [B-CONFIG] 输入校验 XSS/SQL 注入防护加固
  - 文件: `backend/app/core/input_validator.py` (增强)
  - 依据: ad/ad-global.md §6.1 输入校验
- [ ] T005 [P] [B-CONFIG] CORS 配置 + CSRF 防护
  - 文件: `backend/app/main.py`
  - 依据: ad/ad-global.md §6 安全
- [ ] T006 [P] [B-CONFIG] 敏感数据加密存储审查 (密码/Token/API Key)
  - 文件: 审查全部 ORM 模型中的敏感字段
  - 依据: dd/dd-global.md §6

## 性能优化

- [ ] T007 [P] [B-SERVICE] Redis 缓存策略: 监控仪表盘 30s 缓存 + 热数据预加载
  - 文件: `backend/app/services/monitoring/metrics.py` (优化)
  - 依据: dd/dd-monitoring.md §4.2
- [ ] T008 [P] [B-CONFIG] pgvector HNSW 索引参数调优 + 查询性能基准
  - 文件: `backend/app/services/knowledge/retriever.py`
  - 依据: dd/dd-knowledge-base.md §4.5
- [ ] T009 [P] [B-CONFIG] 数据库查询优化: 关键查询添加索引 + 慢查询日志
  - 文件: Alembic 迁移 (添加必要索引)
- [ ] T010 [T-INTEGRATION] 性能基线测试: 指令识别 P95 < 200ms, 知识问答 < 4s, API 并发 10 QPS
  - 文件: `backend/scripts/performance_test.py`
  - 依据: plan.md 性能目标

## 端到端集成

- [ ] T011 [B-SERVICE] 版本加载器: 发布版本→运行时加载各绑定库 published 模型
  - 文件: `backend/app/services/version/loader.py`
  - 依据: dd/dd-dialog-profile.md §4.8 + plan.md S10
- [ ] T012 [B-SERVICE] 对话管理 API 完整集成: POST /dialog 端到端 (文本→预处理→路由→分域处理→响应)
  - 文件: `backend/app/api/v1/dialog.py` (完善)
  - 依据: ad/ad-global.md §5.1 对话推理数据流
- [ ] T013 [P] [T-INTEGRATION] 对话推理端到端集成测试: 指令域/知识域/闲聊域/未知输入 4 条链路
  - 文件: `backend/tests/integration/test_dialog_e2e.py`
  - 依据: ad/ad-global.md §5.1

## 前端完善

- [ ] T014 [P] [F-PAGE] 侧边栏菜单完善: 全部 6 个模块菜单项+图标+权限控制+选中态
  - 文件: `frontend/src/components/Layout/MainLayout.jsx`
  - 依据: pd-all/ 各模块 PD 的导航结构
- [ ] T015 [P] [F-COMPONENT] 全局错误边界 + 404 页面 + 网络异常提示
  - 文件: `frontend/src/components/ErrorBoundary.jsx`, `frontend/src/pages/404.jsx`
- [ ] T016 [P] [F-COMPONENT] 全局弹窗规范: maskClosable=false + Input allowClear
  - 文件: 全局 Ant Design ConfigProvider 配置
  - 依据: plan.md 反馈迭代计划 P0

## 文档与收尾

- [ ] T017 [P] [B-CONFIG] Docker 容器化配置: Dockerfile + docker-compose.yml (后端+前端+PostgreSQL+Redis)
  - 文件: `smartchef-platform/docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`
- [ ] T018 [P] [B-CONFIG] README.md: 项目说明 + 本地启动指南 + API 文档入口
  - 文件: `smartchef-platform/README.md`
- [ ] T019 [P] [T-E2E] 全链路回归 E2E: 登录→创建指令库→训练模型→创建方案→绑定→发布→测试→监控
  - 文件: `frontend/tests/e2e/full-regression.spec.js`

## 检查点

**最终验收标准**:
- [ ] 21 能力点全部绑定且集成测试通过
- [ ] 安全扫描无高危漏洞
- [ ] 性能基线达标 (指令 P95 < 200ms, 知识问答 < 4s)
- [ ] 对话推理 API 端到端 4 条链路全部可用
- [ ] 全链路回归 E2E 通过
- [ ] Docker 部署成功
- [ ] 全部模块无回归
