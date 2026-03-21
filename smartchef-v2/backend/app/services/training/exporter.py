"""ONNX export and artifact packaging for trained JointBERT checkpoints."""

from __future__ import annotations

import hashlib
import json
import logging
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING

import torch

if TYPE_CHECKING:
    from app.services.training.joint_model import IntentSlotModel

logger = logging.getLogger(__name__)


def export_to_onnx(model: IntentSlotModel, save_path: str, max_seq_length: int = 128) -> None:
    """Export PyTorch model to ONNX format with dynamic batch axis."""
    path = Path(save_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    model.eval()
    dummy_input_ids = torch.zeros(1, max_seq_length, dtype=torch.long)
    dummy_attention_mask = torch.ones(1, max_seq_length, dtype=torch.long)
    torch.onnx.export(
        model,
        (dummy_input_ids, dummy_attention_mask),
        str(path),
        input_names=["input_ids", "attention_mask"],
        output_names=["intent_logits", "slot_logits"],
        dynamic_axes={
            "input_ids": {0: "batch_size"},
            "attention_mask": {0: "batch_size"},
            "intent_logits": {0: "batch_size"},
            "slot_logits": {0: "batch_size"},
        },
        opset_version=14,
        do_constant_folding=True,
        dynamo=False,
    )
    logger.info("Exported ONNX model to %s", path)


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    path = Path(path)
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def package_artifacts(
    model_dir: str,
    model_id: str,
    library_key: str,
    language: str,
    label_map: dict,
    slot_map: dict,
    metrics: dict,
    config: dict,
    dataset_id: str,
) -> str:
    """Write JSON sidecars and zip model.onnx + metadata. Returns path to the zip file."""
    root = Path(model_dir)
    root.mkdir(parents=True, exist_ok=True)
    onnx_path = root / "model.onnx"

    label_path = root / "label_map.json"
    slot_path = root / "slot_map.json"
    meta_path = root / "metadata.json"

    label_path.write_text(json.dumps(label_map, ensure_ascii=False, indent=2), encoding="utf-8")
    slot_path.write_text(json.dumps(slot_map, ensure_ascii=False, indent=2), encoding="utf-8")

    metadata = {
        "model_id": model_id,
        "library_key": library_key,
        "language": language,
        "dataset_id": dataset_id,
        "metrics": metrics,
        "train_config": config,
        "artifact_files": ["model.onnx", "label_map.json", "slot_map.json", "metadata.json"],
    }
    if onnx_path.exists():
        metadata["artifact_sha256"] = sha256_file(onnx_path)
    meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    zip_path = root / "package.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in ("model.onnx", "label_map.json", "slot_map.json", "metadata.json"):
            p = root / name
            if p.exists():
                zf.write(p, arcname=name)

    logger.info("Packaged artifacts to %s", zip_path)
    return str(zip_path.resolve())
