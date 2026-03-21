"""Load NLU training samples, BIO labeling, tokenization, and PyTorch DataLoaders."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import torch
from sklearn.model_selection import train_test_split
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from torch.utils.data import DataLoader, Dataset

from app.models.intent import Intent

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

IGNORE_INDEX = -100


@dataclass
class TrainingSample:
    text: str
    intent_key: str
    annotations: list[dict[str, Any]]
    slot_keys_declared: list[str]


def _parse_slot_annotations(raw: dict | list | None) -> list[dict[str, Any]]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [x for x in raw if isinstance(x, dict)]
    if isinstance(raw, dict):
        for key in ("annotations", "spans", "entities"):
            v = raw.get(key)
            if isinstance(v, list):
                return [x for x in v if isinstance(x, dict)]
        if "start" in raw and "end" in raw:
            return [raw]
    return []


async def load_training_data(db: AsyncSession, dataset_id: UUID) -> list[TrainingSample]:
    """Load intents with similar questions and slot annotations for a training dataset."""
    stmt = (
        select(Intent)
        .where(Intent.dataset_id == dataset_id)
        .options(selectinload(Intent.similar_questions))
        .order_by(Intent.sort_order, Intent.intent_key)
    )
    intents = (await db.execute(stmt)).scalars().unique().all()

    samples: list[TrainingSample] = []
    for intent in intents:
        declared = intent.slot_keys or []
        if isinstance(declared, dict):
            declared = list(declared.keys())
        elif not isinstance(declared, list):
            declared = []

        for sq in intent.similar_questions:
            ann = _parse_slot_annotations(sq.slot_annotations)
            samples.append(
                TrainingSample(
                    text=sq.text,
                    intent_key=intent.intent_key,
                    annotations=ann,
                    slot_keys_declared=[str(s) for s in declared],
                )
            )
    logger.info("load_training_data: dataset_id=%s samples=%s", dataset_id, len(samples))
    return samples


def build_label_maps(samples: list[TrainingSample]) -> tuple[dict[str, int], dict[str, int]]:
    """intent_key → id, BIO tag string → id (always includes O)."""
    intent_keys = sorted({s.intent_key for s in samples})
    intent_map = {k: i for i, k in enumerate(intent_keys)}

    slot_names: set[str] = set()
    for s in samples:
        slot_names.update(s.slot_keys_declared)
        for ann in s.annotations:
            slot = ann.get("slot")
            if slot is not None and str(slot).strip():
                slot_names.add(str(slot).strip())

    slot_map: dict[str, int] = {"O": 0}
    idx = 1
    for name in sorted(slot_names):
        slot_map[f"B-{name}"] = idx
        idx += 1
        slot_map[f"I-{name}"] = idx
        idx += 1

    if len(slot_map) == 1:
        # No slots in data — keep a single 'O' class for a degenerate slot head.
        logger.warning("build_label_maps: no slot names found; slot head has single 'O' class")

    return intent_map, slot_map


def _char_level_bio(text: str, annotations: list[dict[str, Any]]) -> list[str]:
    n = len(text)
    tags = ["O"] * n
    for ann in annotations:
        try:
            start = int(ann["start"])
            end = int(ann["end"])
        except (KeyError, TypeError, ValueError):
            continue
        slot = str(ann.get("slot", "entity")).strip() or "entity"
        if start < 0 or end > n or start >= end:
            continue
        tags[start] = f"B-{slot}"
        for i in range(start + 1, end):
            tags[i] = f"I-{slot}"
    return tags


def align_bio_to_tokens(
    text: str,
    char_tags: list[str],
    offsets: list[tuple[int, int]],
    attention_mask: list[int],
    slot_map: dict[str, int],
) -> list[int]:
    """Map character BIO tags to tokenizer token labels; padding/special → IGNORE_INDEX."""
    n = len(text)
    labels: list[int] = []
    for i, (cs, ce) in enumerate(offsets):
        if not attention_mask[i]:
            labels.append(IGNORE_INDEX)
            continue
        if cs == ce:
            labels.append(IGNORE_INDEX)
            continue
        anchor = min(cs, n - 1) if n else 0
        tag = char_tags[anchor] if n > 0 else "O"
        labels.append(slot_map.get(tag, slot_map["O"]))
    return labels


def tokenize_samples(
    samples: list[TrainingSample],
    tokenizer,
    max_length: int,
    intent_map: dict[str, int],
    slot_map: dict[str, int],
) -> list[dict[str, Any]]:
    """Tokenize each sample; returns dicts with tensors and intent label index."""
    rows: list[dict[str, Any]] = []
    for s in samples:
        char_tags = _char_level_bio(s.text, s.annotations)
        enc = tokenizer(
            s.text,
            max_length=max_length,
            padding="max_length",
            truncation=True,
            return_offsets_mapping=True,
            return_attention_mask=True,
            return_tensors=None,
        )
        input_ids = enc["input_ids"]
        attn = enc["attention_mask"]
        offsets = enc["offset_mapping"]
        labels = align_bio_to_tokens(s.text, char_tags, offsets, attn, slot_map)
        rows.append(
            {
                "input_ids": torch.tensor(input_ids, dtype=torch.long),
                "attention_mask": torch.tensor(attn, dtype=torch.long),
                "slot_labels": torch.tensor(labels, dtype=torch.long),
                "intent_label": intent_map[s.intent_key],
            }
        )
    return rows


class JointNLUDataset(Dataset):
    def __init__(self, rows: list[dict[str, Any]]):
        self._rows = rows

    def __len__(self) -> int:
        return len(self._rows)

    def __getitem__(self, i: int) -> dict[str, Any]:
        return self._rows[i]


def _collate_batch(batch: list[dict[str, Any]]) -> dict[str, torch.Tensor]:
    return {
        "input_ids": torch.stack([b["input_ids"] for b in batch]),
        "attention_mask": torch.stack([b["attention_mask"] for b in batch]),
        "slot_labels": torch.stack([b["slot_labels"] for b in batch]),
        "intent_label": torch.tensor([b["intent_label"] for b in batch], dtype=torch.long),
    }


def stratified_split(
    tokenized: list[dict[str, Any]],
    ratio: float = 0.8,
    seed: int = 42,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Train/val split stratified by intent when every intent class has ≥2 examples."""
    if not tokenized:
        return [], []

    y = [int(row["intent_label"]) for row in tokenized]
    indices = list(range(len(tokenized)))
    counts: dict[int, int] = {}
    for lab in y:
        counts[lab] = counts.get(lab, 0) + 1
    stratify_arg = y if counts and min(counts.values()) >= 2 else None

    train_idx, val_idx = train_test_split(
        indices,
        train_size=ratio,
        random_state=seed,
        shuffle=True,
        stratify=stratify_arg,
    )
    return [tokenized[i] for i in train_idx], [tokenized[i] for i in val_idx]


def create_data_loaders(
    train_set: list[dict[str, Any]],
    val_set: list[dict[str, Any]],
    batch_size: int,
) -> tuple[DataLoader, DataLoader | None]:
    train_loader = DataLoader(
        JointNLUDataset(train_set),
        batch_size=batch_size,
        shuffle=True,
        collate_fn=_collate_batch,
        num_workers=0,
    )
    if not val_set:
        return train_loader, None
    val_loader = DataLoader(
        JointNLUDataset(val_set),
        batch_size=batch_size,
        shuffle=False,
        collate_fn=_collate_batch,
        num_workers=0,
    )
    return train_loader, val_loader
