# 基础设施任务

**目的**: 固化正式 `backend/` 与 `frontend/` 骨架，为 `pd-user-mgmt` 提供统一工程入口  
**完成标志**: 正式目录、`backend/venv`、前端菜单壳、基础测试均可运行

## Definition of Done

- [x] 正式工程根路径固定为 `backend/ + frontend/`
- [x] `backend/venv` 已创建并安装依赖
- [x] 前端菜单壳与 `user-mgmt` 模块入口已落地
- [x] 后端健康检查测试通过
- [x] 前端壳层测试通过，生产构建可生成

## 已完成任务

- [x] T001 [B-CONFIG] 创建正式 `backend/` 目录与 `pyproject.toml`
- [x] T002 [B-CONFIG] 创建 `backend/venv` 并安装 FastAPI / pytest 等依赖
- [x] T003 [P] [B-CONFIG] 创建应用入口 `backend/app/main.py` 与配置模块 `backend/app/config.py`
- [x] T004 [P] [F-PAGE] 创建 `frontend/`、Vite、菜单壳与 `user-mgmt` 入口页
- [x] T005 [P] [T-CONTRACT] 编写并通过 `backend/tests/test_health.py`

**检查点**: 正式骨架已建立，可继续进入 `pd-user-mgmt` 业务实现
