"""
预训练模型路径解析：优先使用本机目录，避免在无缓存时静默联网拉取。

- Hub id（如 bert-base-chinese）：默认仍可用，但会先查 HF_HOME 缓存；命中则**不访问外网**。
- 设置 HF_LOCAL_FILES_ONLY=1（或 HF_HUB_OFFLINE=1）时：仅使用缓存/本地路径，缺文件则立即报错，而不是长时间重试下载。
- 本机目录：含 config.json 的文件夹，可通过绝对路径或相对 backend 根目录 / data/models/pretrained/<相对路径> 指定。
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _is_local_pretrain_source(path: Path) -> bool:
    """整模目录（config.json）或仅 tokenizer 目录（训练一般为整模；推理可能只用 tokenizer 子目录）。"""
    if not path.is_dir():
        return False
    if (path / "config.json").is_file():
        return True
    if (path / "tokenizer_config.json").is_file() or (path / "tokenizer.json").is_file():
        return True
    return False


def resolve_pretrained_for_model(model_id_or_path: str) -> tuple[str, dict]:
    """
    供 AutoModel / AutoTokenizer.from_pretrained(..., **kwargs) 使用。

    Returns:
        (resolved_id_or_path, extra_kwargs)
        extra_kwargs 至少可能含 local_files_only=True。
    """
    raw = (model_id_or_path or "").strip().strip('"').strip("'")
    if not raw:
        return raw, {}

    settings = get_settings()
    backend_root = _backend_root()

    local_only = bool(settings.HF_LOCAL_FILES_ONLY) or _env_flag("HF_HUB_OFFLINE") or _env_flag(
        "TRANSFORMERS_OFFLINE"
    )

    # --- 1) 显式本机目录（绝对路径、或相对当前工作目录已存在）---
    p0 = Path(raw)
    if not p0.is_absolute():
        p_try = (Path.cwd() / raw).resolve()
        if _is_local_pretrain_source(p_try):
            logger.info("预训练模型使用本机目录（cwd 相对）: %s", p_try)
            return str(p_try), {"local_files_only": True}
    p_abs = p0.expanduser().resolve()
    if p0.is_absolute() and _is_local_pretrain_source(p_abs):
        logger.info("预训练模型使用本机目录（绝对路径）: %s", p_abs)
        return str(p_abs), {"local_files_only": True}

    # --- 2) 相对 backend / MODEL_DATA_DIR / data/models/pretrained ---
    bases: list[Path] = []
    if settings.MODEL_DATA_DIR:
        bases.append(Path(settings.MODEL_DATA_DIR).expanduser().resolve())
    bases.append(backend_root)
    bases.append(backend_root / "data" / "models" / "pretrained")

    for base in bases:
        cand = (base / raw).resolve()
        if _is_local_pretrain_source(cand):
            logger.info("预训练模型使用本机目录（相对项目）: %s", cand)
            return str(cand), {"local_files_only": True}

    # --- 3) Hub id：可选强制仅本地（仅用 HF_HOME/hub 缓存，不发起下载）---
    extra: dict = {}
    if local_only:
        extra["local_files_only"] = True
        logger.debug("预训练加载 local_files_only=True（HF_LOCAL_FILES_ONLY / HF_HUB_OFFLINE）: %s", raw)
    return raw, extra


def _env_flag(name: str) -> bool:
    v = os.environ.get(name, "").lower()
    return v in ("1", "true", "yes", "on")
