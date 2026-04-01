"""仅写入 seed（角色、能力、admin），不跑迁移。表已存在但 user_account 为空时可执行。"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from sqlalchemy.engine import make_url

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import build_settings

from scripts.bootstrap_db import seed_baseline_data


def main() -> None:
    settings = build_settings()
    url = make_url(os.environ.get("DATABASE_URL", settings.database_url))
    seed_baseline_data(url)


if __name__ == "__main__":
    main()
