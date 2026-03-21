"""
预下载训练会用到的 Hugging Face 模型（tokenizer + encoder 权重）到项目缓存目录。

用法（在 smartchef-v2/backend 目录）::

    python -m app.scripts.prefetch_hf_cache

可选：把用户主目录下已下载的 hub 快照**复制**到项目缓存（不删除原目录，避免影响其他工具）::

    python -m app.scripts.prefetch_hf_cache --migrate-user-cache

说明：
- `HF_HOME` 由 `configure_huggingface_cache()` 设为 `<backend>/data/hf_cache`（可用环境变量覆盖）。
"""

from __future__ import annotations

import argparse
import logging
import shutil
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")
_logger = logging.getLogger(__name__)

# 与前端 Detail.jsx BASE_MODEL_OPTIONS + trainer 默认对齐（均为 HF 有效 id）
TRAINING_BASE_MODEL_IDS: tuple[str, ...] = (
    "bert-base-chinese",
    "distilbert-base-uncased",
    "prajjwal1/bert-tiny",
)


def _migrate_user_hub_to_project(project_hub: Path) -> None:
    """将 ~/.cache/huggingface/hub 下已有快照复制到项目 hub（仅复制目标不存在的目录）。"""
    user_hub = Path.home() / ".cache" / "huggingface" / "hub"
    if not user_hub.is_dir():
        _logger.info("[migrate] 未找到用户缓存目录: %s", user_hub)
        return
    project_hub.mkdir(parents=True, exist_ok=True)
    n = 0
    for item in sorted(user_hub.iterdir()):
        dest = project_hub / item.name
        if dest.exists():
            continue
        if item.is_dir():
            _logger.info("[migrate] 复制 %s -> %s", item.name, project_hub)
            shutil.copytree(item, dest)
            n += 1
    if n:
        _logger.info("[migrate] 已复制 %d 个快照目录到项目缓存。", n)
    else:
        _logger.info("[migrate] 无需复制（均已存在或无新快照）。")


def _prefetch_one(model_id: str) -> bool:
    """使用 huggingface_hub 拉取仓库快照，不 import torch（避免仅下载时 DLL/环境问题）。"""
    _logger.info("[prefetch] --- %s ---", model_id)
    try:
        from huggingface_hub import snapshot_download

        snapshot_download(repo_id=model_id, repo_type="model")
    except Exception as e:
        _logger.warning("[prefetch] 跳过 %s: %s", model_id, e)
        return False
    _logger.info("[prefetch] OK: %s", model_id)
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="预下载训练用 HF 模型到项目 data/hf_cache")
    parser.add_argument(
        "--migrate-user-cache",
        action="store_true",
        help="将 ~/.cache/huggingface/hub 中项目尚未拥有的快照复制到项目缓存",
    )
    args = parser.parse_args(argv)

    from app.core.hf_cache import configure_huggingface_cache

    configure_huggingface_cache()
    import os

    hf_home = Path(os.environ["HF_HOME"])
    hub = Path(os.environ.get("HF_HUB_CACHE", hf_home / "hub"))
    _logger.info("HF_HOME=%s", hf_home)

    if args.migrate_user_cache:
        _migrate_user_hub_to_project(hub)

    ok = 0
    fail = 0
    for mid in TRAINING_BASE_MODEL_IDS:
        if _prefetch_one(mid):
            ok += 1
        else:
            fail += 1

    _logger.info("[prefetch] 完成：成功 %d，跳过/失败 %d（占位 ID 或网络问题见上方 WARN）", ok, fail)
    return 0


if __name__ == "__main__":
    sys.exit(main())
