# 横切关注点任务

**目的**: 收口试点中的横切能力，避免“文档可生成但实现不可控”  
**依赖**: `tasks-infra.md`、`tasks-user-mgmt.md`

## 任务

- [x] T001 [P] [T-CONTRACT] 校验响应信封、分页结构、错误码与 `ad.md/dd.md` 一致
- [x] T002 [P] [T-INTEGRATION] 校验前端不以 toast/本地状态冒充成功，必须回读真实结果
- [x] T003 [P] [B-CONFIG] 接入审计日志记录 `user.created` 与 `user.role_changed`
- [x] T004 [T-E2E] 执行 user-mgmt 冒烟回归：创建账号、调整角色、查看权限矩阵

## 收口结果

- 后端补齐 `RequestValidationError` 的统一错误信封，`422` 也统一回传 `code/message/data/request_id/timestamp`
- `user-mgmt` 审计事件改为 `user.created` 与 `user.role_changed`，并新增契约测试锁定口径
- 前端修复权限矩阵 `pm` 列展示，补齐 `UserMgmtPage` 与 `AppShell` 的真实页面回读测试
- 浏览器回归已验证账号创建、角色变化后的页面回读，以及权限矩阵页可见

## 检查点

- [x] 不存在本次 refinement 范围内的未登记风险项
- [x] 可以无阻塞进入 `pd-monitoring`
