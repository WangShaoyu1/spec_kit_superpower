"""
JointBERT training pipeline (DD §5.3). Runs under FastAPI BackgroundTasks with
dedicated DB sessions (no request-scoped AsyncSession).
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import UUID

import torch
import torch.nn as nn
from sklearn.metrics import f1_score
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from transformers import AutoTokenizer

from app.core import database as db_module
from app.models.dataset import TrainingDataset
from app.models.intent_library import IntentLibrary
from app.models.model_version import LibraryModelVersion
from app.services.training.data_prep import (
    IGNORE_INDEX,
    build_label_maps,
    create_data_loaders,
    load_training_data,
    stratified_split,
    tokenize_samples,
)
from app.services.training.exporter import export_to_onnx, package_artifacts, sha256_file
from app.services.training.joint_model import IntentSlotModel

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)

DEFAULT_TRAIN_CONFIG: dict[str, Any] = {
    "base_model": "bert-base-chinese",
    "max_seq_length": 128,
    "batch_size": 16,
    "learning_rate": 5e-5,
    "max_epochs": 20,
    "early_stopping_patience": 3,
    "train_val_split": 0.8,
    "intent_loss_weight": 0.7,
}

MIN_TRAINING_SAMPLES = 10


class TrainingPreparationError(Exception):
    """Predictable training failures (dataset, counts, config)."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class TrainingCancelled(Exception):
    """User cancelled training (DB status is no longer ``training``)."""


@dataclass
class TrainingPayload:
    model_id: UUID
    library_key: str
    library_language: str
    dataset_id: UUID
    intent_map: dict[str, int]
    slot_map: dict[str, int]
    train_rows: list[dict[str, Any]]
    val_rows: list[dict[str, Any]]
    config: dict[str, Any]
    model_dir: Path
    label_map_out: dict[str, int]
    slot_map_out: dict[str, int]


def _default_base_model(language: str) -> str:
    lang = (language or "").lower()
    if lang.startswith("zh"):
        return "bert-base-chinese"
    return "distilbert-base-uncased"


def _normalize_train_config(raw: dict | None, language: str) -> dict[str, Any]:
    cfg: dict[str, Any] = {**DEFAULT_TRAIN_CONFIG, **(raw or {})}
    if raw and raw.get("epochs") is not None:
        cfg["max_epochs"] = int(raw["epochs"])
    if not cfg.get("base_model"):
        cfg["base_model"] = _default_base_model(language)
    cfg["max_epochs"] = int(cfg.get("max_epochs", 20))
    cfg["batch_size"] = int(cfg.get("batch_size", 16))
    cfg["early_stopping_patience"] = int(cfg.get("early_stopping_patience", 3))
    cfg["train_val_split"] = float(cfg.get("train_val_split", 0.8))
    cfg["intent_loss_weight"] = float(cfg.get("intent_loss_weight", 0.7))
    cfg["max_seq_length"] = int(cfg.get("max_seq_length", 128))
    cfg["learning_rate"] = float(cfg.get("learning_rate", 5e-5))
    return cfg


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _intent_inv_map(intent_map: dict[str, int]) -> dict[int, str]:
    return {v: k for k, v in intent_map.items()}


def _train_one_epoch(
    model: IntentSlotModel,
    loader: torch.utils.data.DataLoader,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    intent_weight: float,
) -> float:
    model.train()
    total_loss = 0.0
    n_batches = 0
    loss_int_fn = nn.CrossEntropyLoss()
    loss_slot_fn = nn.CrossEntropyLoss(ignore_index=IGNORE_INDEX)

    for batch in loader:
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        intent_labels = batch["intent_label"].to(device)
        slot_labels = batch["slot_labels"].to(device)

        optimizer.zero_grad(set_to_none=True)
        intent_logits, slot_logits = model(input_ids, attention_mask)

        li = loss_int_fn(intent_logits, intent_labels)
        ls = loss_slot_fn(slot_logits.view(-1, slot_logits.size(-1)), slot_labels.view(-1))
        loss = intent_weight * li + (1.0 - intent_weight) * ls
        loss.backward()
        optimizer.step()

        total_loss += float(loss.item())
        n_batches += 1

    return total_loss / max(n_batches, 1)


def _evaluate(
    model: IntentSlotModel,
    loader: torch.utils.data.DataLoader | None,
    device: torch.device,
    intent_inv: dict[int, str],
    slot_map: dict[str, int],
) -> tuple[float, float, dict[str, Any]]:
    empty_detail = {
        "val_intent_f1": 0.0,
        "val_slot_f1": 0.0,
        "intent_labels": [intent_inv[i] for i in sorted(intent_inv.keys())],
        "slot_tags": [tag for tag, _ in sorted(slot_map.items(), key=lambda x: x[1])],
    }
    if loader is None:
        return 0.0, 0.0, empty_detail

    model.eval()
    all_intent_true: list[int] = []
    all_intent_pred: list[int] = []
    all_slot_true: list[int] = []
    all_slot_pred: list[int] = []

    with torch.no_grad():
        for batch in loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            intent_labels = batch["intent_label"].to(device)
            slot_labels = batch["slot_labels"].to(device)

            intent_logits, slot_logits = model(input_ids, attention_mask)
            intent_pred = intent_logits.argmax(dim=-1)
            slot_pred = slot_logits.argmax(dim=-1)

            all_intent_true.extend(intent_labels.cpu().tolist())
            all_intent_pred.extend(intent_pred.cpu().tolist())

            for i in range(slot_labels.size(0)):
                for t in range(slot_labels.size(1)):
                    tid = int(slot_labels[i, t].item())
                    if tid == IGNORE_INDEX:
                        continue
                    all_slot_true.append(tid)
                    all_slot_pred.append(int(slot_pred[i, t].item()))

    intent_f1 = f1_score(all_intent_true, all_intent_pred, average="macro", zero_division=0)
    slot_f1 = (
        f1_score(all_slot_true, all_slot_pred, average="macro", zero_division=0)
        if all_slot_true
        else 0.0
    )

    detail = {
        "val_intent_f1": round(float(intent_f1), 6),
        "val_slot_f1": round(float(slot_f1), 6),
        "intent_labels": [intent_inv[i] for i in sorted(intent_inv.keys())],
        "slot_tags": [tag for tag, _ in sorted(slot_map.items(), key=lambda x: x[1])],
    }
    return float(intent_f1), float(slot_f1), detail


def _sync_check_training_cancelled(model_id: UUID, loop: asyncio.AbstractEventLoop) -> None:
    """训练线程内调用：若用户已取消/删除版本，则中止训练。"""

    async def _read_status() -> str | None:
        factory = db_module.async_session_factory
        if factory is None:
            return None
        async with factory() as session:
            m = await session.get(LibraryModelVersion, model_id)
            return m.status if m else None

    fut = asyncio.run_coroutine_threadsafe(_read_status(), loop)
    try:
        status = fut.result(timeout=120)
    except Exception as e:
        logger.warning("训练取消检查失败（忽略）: %s", e)
        return
    if status != "training":
        raise TrainingCancelled()


def _run_torch_train_and_export(
    payload: TrainingPayload,
    progress_cb: Callable[[int], None],
    loop: asyncio.AbstractEventLoop,
) -> dict[str, Any]:
    cfg = payload.config
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    alpha = cfg["intent_loss_weight"]
    max_epochs = cfg["max_epochs"]
    patience = cfg["early_stopping_patience"]
    max_seq = cfg["max_seq_length"]

    logger.info(
        "训练线程开始: base_model=%s device=%s max_epochs=%s batch_size=%s "
        "(10%%=已进入训练线程；12–19%%=DataLoader/加载预训练编码器；≥20%%=各 epoch 结束)",
        cfg["base_model"],
        device,
        max_epochs,
        cfg["batch_size"],
    )

    train_loader, val_loader = create_data_loaders(
        payload.train_rows,
        payload.val_rows,
        cfg["batch_size"],
    )
    progress_cb(12)

    num_intents = len(payload.intent_map)
    num_slot_tags = len(payload.slot_map)
    logger.info(
        "正在加载预训练编码器（首次可能下载数百 MB，仅 tokenizer 已在准备阶段加载）…",
    )
    model = IntentSlotModel(
        cfg["base_model"],
        num_intents=num_intents,
        num_slot_tags=num_slot_tags,
    ).to(device)
    progress_cb(15)
    logger.info("预训练编码器已就绪，开始 epoch 循环（首个 epoch 结束前进度仍为 15%% 左右属正常）")
    _sync_check_training_cancelled(payload.model_id, loop)

    optimizer = torch.optim.AdamW(model.parameters(), lr=cfg["learning_rate"])

    best_intent_f1 = -1.0
    best_state: dict[str, Any] | None = None
    epochs_no_improve = 0

    intent_inv = _intent_inv_map(payload.intent_map)

    val_detail: dict[str, Any] = {
        "val_intent_f1": 0.0,
        "val_slot_f1": 0.0,
        "intent_labels": [intent_inv[i] for i in sorted(intent_inv.keys())],
        "slot_tags": [tag for tag, _ in sorted(payload.slot_map.items(), key=lambda x: x[1])],
    }
    last_epoch = -1

    for epoch in range(max_epochs):
        _sync_check_training_cancelled(payload.model_id, loop)
        _train_one_epoch(model, train_loader, optimizer, device, alpha)
        intent_f1, slot_f1, val_detail = _evaluate(
            model, val_loader, device, intent_inv, payload.slot_map,
        )
        last_epoch = epoch

        # Progress: 20% + (epoch+1)/max_epochs * 60%
        pct = 20 + int((epoch + 1) / max_epochs * 60)
        progress_cb(min(pct, 79))

        logger.info(
            "epoch %s/%s train_loss_n=%s val_intent_f1=%.4f val_slot_f1=%.4f",
            epoch + 1,
            max_epochs,
            epoch,
            intent_f1,
            slot_f1,
        )

        if intent_f1 > best_intent_f1:
            best_intent_f1 = intent_f1
            best_state = {k: v.cpu() for k, v in model.state_dict().items()}
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= patience:
                logger.info("Early stopping at epoch %s (patience=%s)", epoch + 1, patience)
                break

    if best_state is not None:
        model.load_state_dict(best_state)

    _sync_check_training_cancelled(payload.model_id, loop)

    payload.model_dir.mkdir(parents=True, exist_ok=True)
    onnx_path = payload.model_dir / "model.onnx"
    export_to_onnx(model, str(onnx_path), max_seq_length=max_seq)
    progress_cb(90)

    package_artifacts(
        str(payload.model_dir),
        str(payload.model_id),
        payload.library_key,
        payload.library_language,
        payload.label_map_out,
        payload.slot_map_out,
        metrics={
            "best_val_intent_f1": round(float(best_intent_f1), 6),
            "final_val_intent_f1": val_detail["val_intent_f1"],
            "final_val_slot_f1": val_detail["val_slot_f1"],
        },
        config=cfg,
        dataset_id=str(payload.dataset_id),
    )

    onnx_sha = sha256_file(onnx_path)
    return {
        "metrics": {
            "best_val_intent_f1": round(float(best_intent_f1), 6),
            "val_intent_f1": val_detail["val_intent_f1"],
            "val_slot_f1": val_detail["val_slot_f1"],
            "epochs_run": last_epoch + 1,
        },
        "artifact_uri": f"data/models/{payload.library_key}/{payload.model_id}/model.onnx",
        "package_uri": f"data/models/{payload.library_key}/{payload.model_id}/package.zip",
        "artifact_sha256": onnx_sha,
        "extra_val": val_detail,
    }


async def _prepare_payload(model_version_id: UUID) -> TrainingPayload:
    factory = db_module.async_session_factory
    if factory is None:
        raise RuntimeError("Database not initialized")

    # 准备阶段可能较长（首次下载 tokenizer/预训练权重、读库建图），避免前端长期显示 progress=0
    await _set_model_fields(model_version_id, progress=5)

    async with factory() as session:
        stmt = (
            select(LibraryModelVersion)
            .where(LibraryModelVersion.id == model_version_id)
            .options(selectinload(LibraryModelVersion.library))
        )
        model = (await session.execute(stmt)).scalar_one_or_none()
        if not model:
            raise TrainingPreparationError("模型版本不存在")

        if not model.train_dataset_id:
            raise TrainingPreparationError("未绑定训练数据集 (train_dataset_id)")

        library = model.library
        if library is None:
            library = (
                await session.execute(select(IntentLibrary).where(IntentLibrary.id == model.library_id))
            ).scalar_one()

        ds = await session.get(TrainingDataset, model.train_dataset_id)
        if not ds or ds.library_id != model.library_id:
            raise TrainingPreparationError("训练数据集不存在或不属于该模型所在库")

        samples = await load_training_data(session, model.train_dataset_id)
        if len(samples) < MIN_TRAINING_SAMPLES:
            raise TrainingPreparationError(
                f"训练样本数量不足（至少需要 {MIN_TRAINING_SAMPLES} 条相似问）当前: {len(samples)}"
            )

        intent_map, slot_map = build_label_maps(samples)
        cfg = _normalize_train_config(model.train_config, library.language)
        from app.core.hf_pretrained import resolve_pretrained_for_model

        _bm_resolved, _bm_kw = resolve_pretrained_for_model(cfg["base_model"])
        try:
            tokenizer = AutoTokenizer.from_pretrained(_bm_resolved, **_bm_kw)
        except (ValueError, OSError):
            from transformers import BertTokenizer

            tokenizer = BertTokenizer.from_pretrained(_bm_resolved, **_bm_kw)
        tokenized = tokenize_samples(
            samples,
            tokenizer,
            max_length=cfg["max_seq_length"],
            intent_map=intent_map,
            slot_map=slot_map,
        )
        train_rows, val_rows = stratified_split(tokenized, ratio=cfg["train_val_split"])

        model_dir = _backend_root() / "data" / "models" / library.library_key / str(model_version_id)

        return TrainingPayload(
            model_id=model_version_id,
            library_key=library.library_key,
            library_language=library.language,
            dataset_id=model.train_dataset_id,
            intent_map=intent_map,
            slot_map=slot_map,
            train_rows=train_rows,
            val_rows=val_rows,
            config=cfg,
            model_dir=model_dir,
            label_map_out=dict(intent_map),
            slot_map_out=dict(slot_map),
        )


async def _set_model_fields(model_id: UUID, **fields: Any) -> None:
    factory = db_module.async_session_factory
    if factory is None:
        return
    async with factory() as session:
        m = await session.get(LibraryModelVersion, model_id)
        if not m:
            logger.error("Training update: model %s not found", model_id)
            return
        for k, v in fields.items():
            if v is not None or k in ("notes", "artifact_uri", "package_uri"):
                setattr(m, k, v)
        await session.commit()


async def execute_training(model_version_id: UUID, db_url: str) -> None:
    """
    Full training pipeline as specified in DD §5.3.
    Runs under FastAPI BackgroundTasks with isolated DB sessions.
    """
    _ = db_url  # Future: worker processes may set DATABASE_URL before init_db()
    if db_module.async_session_factory is None:
        await db_module.init_db()

    loop = asyncio.get_running_loop()

    # 后台任务已接管（与 HTTP 返回的 training 区分）：用户可见非 0 进度
    await _set_model_fields(model_version_id, progress=1)

    try:
        payload = await _prepare_payload(model_version_id)
    except TrainingPreparationError as e:
        logger.warning("Training skipped: %s", e.message)
        await _set_model_fields(
            model_version_id,
            status="failed",
            notes=e.message,
            progress=0,
        )
        return
    except Exception as e:
        logger.exception("Training preparation failed")
        # 与训练执行阶段一致：把根因写入 notes，便于前端/DB 直接排查（无需只看日志）
        detail = (str(e) or repr(e))[:8000]
        notes = f"训练准备阶段失败: {detail}"
        await _set_model_fields(
            model_version_id,
            status="failed",
            notes=notes,
            progress=0,
        )
        return

    await _set_model_fields(model_version_id, progress=10)

    def progress_sync(p: int) -> None:
        fut = asyncio.run_coroutine_threadsafe(
            _set_model_fields(model_version_id, progress=p),
            loop,
        )
        fut.result(timeout=600)

    try:
        result = await asyncio.to_thread(_run_torch_train_and_export, payload, progress_sync, loop)
    except TrainingCancelled:
        logger.info("Training cancelled: %s", model_version_id)
        await _set_model_fields(
            model_version_id,
            status="failed",
            notes="用户已取消训练",
            progress=0,
        )
        return
    except Exception as e:
        logger.exception("Training execution failed")
        msg = str(e)[:8000]
        await _set_model_fields(
            model_version_id,
            status="failed",
            notes=msg,
            progress=0,
        )
        return

    ev = dict(result["extra_val"])
    ev.pop("intent_labels", None)
    ev.pop("slot_tags", None)
    metrics = {**result["metrics"], **ev}

    await _set_model_fields(
        model_version_id,
        status="trained",
        metrics=metrics,
        artifact_type="onnx",
        artifact_uri=result["artifact_uri"],
        package_uri=result["package_uri"],
        artifact_sha256=result["artifact_sha256"],
        progress=100,
        trained_at=datetime.now(timezone.utc),
        notes=None,
    )

