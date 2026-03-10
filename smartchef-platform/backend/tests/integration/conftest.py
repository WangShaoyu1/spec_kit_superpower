"""集成测试 conftest。

不覆盖 event_loop 或 setup_db，使需要 DB 的集成测试（如 test_rbac）
使用顶层 conftest 的 fixture，避免 event loop 冲突。
"""
