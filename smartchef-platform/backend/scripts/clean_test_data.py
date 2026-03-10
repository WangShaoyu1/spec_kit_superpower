#!/usr/bin/env python3
"""
清理测试数据，保留后台登录相关数据（users、roles）。

用法（在 backend 目录下）：
    python -m scripts.clean_test_data
    python -m scripts.clean_test_data --dry-run   # 仅打印将执行的 SQL，不执行

依赖：DATABASE_URL 已配置，alembic 迁移已执行。
"""
from __future__ import annotations

import asyncio
import os
import sys

# 确保 app 可导入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine


# 从父表到子表，TRUNCATE CASCADE 自动清理依赖表；不包含 users、roles
TRUNCATE_ORDER = [
    "request_logs",
    "alert_rules",
    "intents",           # CASCADE -> slots, training_data
    "personas",
    "dialog_profiles",
    "published_versions",
    "test_sessions",
    "test_suites",       # CASCADE -> test_suite_cases, test_reports
    "batch_test_jobs",   # CASCADE -> batch_test_cases
    "knowledge_bases",   # CASCADE -> knowledge_documents, document_chunks
]


async def run_clean(dry_run: bool = False):
    async with engine.begin() as conn:
        for table in TRUNCATE_ORDER:
            stmt = text(f'TRUNCATE TABLE "{table}" CASCADE')
            if dry_run:
                print(f"[DRY-RUN] {stmt}")
            else:
                await conn.execute(stmt)
                print(f"Cleared: {table}")
    print("Done. Kept: users, roles.")


def main():
    dry = "--dry-run" in sys.argv
    if dry:
        print("Dry run (no changes):")
    asyncio.run(run_clean(dry_run=dry))


if __name__ == "__main__":
    main()
