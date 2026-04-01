# 任务文件: `pd-user-mgmt`

**输入**: `specs/master/pd-all/pd-user-mgmt/` + `specs/master/ad/ad-user-mgmt.md` + `specs/master/dd/dd-user-mgmt.md`  
**前置依赖**: `tasks-infra.md`  
**TDD 约束**: 先写失败测试，再写最小实现，再验证通过  
**风险提示**: 不得用本地状态冒充权限收敛、角色调整或账号状态回读成功

## 模块核心业务链路

| 链路 | 起点 | 终点/真实成功信号 | 对应任务 |
|------|------|------------------|---------|
| 创建账号 | 创建弹窗提交 | 列表新增用户、统计卡回读更新、审计日志落库 | `T001,T004,T008,T011,T018` |
| 角色调整 | 编辑角色弹窗保存 | 用户角色更新、旧 token 失效、权限矩阵回读一致 | `T002,T005,T009,T012,T018` |
| 账号禁用 | 状态开关切换 | 目标用户变为 `disabled`，最后一个管理员保护生效 | `T003,T006,T010,T018` |

## 显式未完成声明

- **Deferred**: 用户自主修改密码、SSO
- **Stub**: 无
- **Out of Scope**: 批量导入导出用户、自定义角色管理器
- **Blocked By**: 无

## 测试任务

### 契约 / 集成 / E2E

- [x] T001 [P] [T-CONTRACT] 编写 `backend/tests/contract/test_user_api.py`，覆盖 `POST /api/v1/admin/users`
- [x] T002 [P] [T-CONTRACT] 编写 `backend/tests/contract/test_user_api.py`，覆盖 `PATCH /api/v1/admin/users/{id}/role`
- [x] T003 [P] [T-CONTRACT] 编写 `backend/tests/contract/test_user_api.py`，覆盖 `POST /api/v1/admin/users/{id}/status`
- [x] T004 [P] [T-INTEGRATION] 编写用户管理闭环测试，覆盖创建账号与审计回读
- [x] T005 [P] [T-INTEGRATION] 编写用户管理闭环测试，覆盖角色调整与 token version 递增
- [x] T006 [P] [T-INTEGRATION] 编写用户管理闭环测试，覆盖最后一个管理员保护
- [x] T007 [P] [T-E2E] 编写页面级测试，覆盖创建账号弹窗与结果回读

## 后端任务

- [x] T008 [P] [B-MODEL] 落地用户、角色、能力点与审计相关模型
- [x] T009 [P] [B-SERVICE] 实现创建账号、角色调整、能力点解析
- [x] T010 [P] [B-SERVICE] 实现 capability guard 与 token version 校验
- [x] T011 [B-API] 落地 `GET/POST/PATCH/POST/GET` 用户管理接口
- [x] T012 [P] [B-MODEL] 写入固定角色、能力点与内置 admin

## 前端任务

- [x] T013 [P] [F-API] 打通用户列表、创建、改角色、改状态、权限矩阵 API
- [x] T014 [P] [F-STORE] 统一回读与弹窗状态
- [x] T015 [F-PAGE] 实现 `UserMgmtPage.jsx`，覆盖统计卡、表格、创建弹窗、角色弹窗、权限矩阵
- [x] T016 [P] [F-COMPONENT] 落地权限矩阵能力点展示
- [x] T017 [P] [F-COMPONENT] 落地创建表单与 reset 行为

## 检查点

- [x] T018 [T-CONTRACT] 验证前端真实请求字段、统计卡和列表均来自接口回读
- [x] T019 [T-E2E] 运行模块级 browser stage，覆盖 `permission_visibility`、`form_reset`、`result_readback`

## 完成定义

- [x] 账号可创建、改角色、启停用并真实回读
- [x] 最后一个管理员保护成立，旧 token 会在角色/状态变化后失效
- [x] 权限矩阵、统计卡、列表都来自后端接口
- [x] browser smoke 通过且模块状态推进完成
