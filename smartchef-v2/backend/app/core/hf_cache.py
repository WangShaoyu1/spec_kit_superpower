"""
Hugging Face Hub / Transformers 缓存目录配置。

同一 base_model（如 bert-base-chinese）的 tokenizer 与权重在**本机缓存目录内只下载一次**，
之后各次训练只读缓存；变化的是训练数据与产出的 ONNX。

默认将 HF_HOME 指到 backend/data/hf_cache（而非 ~/.cache），便于：
- 与项目/数据目录一起备份或挂载 Docker volume
- 团队在同一部署环境内共享同一份缓存

不把预训练权重打进 git（体积可达数 GB）；部署镜像可在构建阶段执行 prefetch 脚本预下载。
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

_logger = logging.getLogger(__name__)


def configure_huggingface_cache() -> None:
    """在进程内**首次** import transformers/huggingface_hub 之前调用（见 create_app 入口）。"""
    from app.core.config import get_settings

    settings = get_settings()
    backend_root = Path(__file__).resolve().parents[2]

    # 优先级：Settings（.env）> 进程已有 HF_HOME > 项目内默认目录
    if settings.HF_HOME:
        hf_home = Path(settings.HF_HOME).expanduser().resolve()
    elif os.environ.get("HF_HOME"):
        hf_home = Path(os.environ["HF_HOME"]).expanduser().resolve()
    else:
        base = Path(settings.MODEL_DATA_DIR) if settings.MODEL_DATA_DIR else backend_root
        hf_home = (base / "data" / "hf_cache").resolve()

    hf_home.mkdir(parents=True, exist_ok=True)
    hub = hf_home / "hub"
    hub.mkdir(parents=True, exist_ok=True)

    # 写回环境变量，确保 transformers / huggingface_hub 与配置一致
    os.environ["HF_HOME"] = str(hf_home)
    os.environ["HF_HUB_CACHE"] = str(hub)

    _logger.info("HuggingFace 缓存目录 HF_HOME=%s", os.environ["HF_HOME"])
