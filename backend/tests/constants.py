"""pytest 与本地 PG 测试库约定（禁用 SQLite）。"""

import os

# 与 test_config 中 smartchef_v2_test 一致；勿与开发库 smartchef_v2 混用。
DEFAULT_PYTEST_DATABASE_URL = (
    "postgresql+psycopg://postgres:postgres@127.0.0.1:5432/smartchef_v2_test"
)


def get_pytest_database_url() -> str:
    return os.environ.get("DATABASE_URL_TEST", DEFAULT_PYTEST_DATABASE_URL)
