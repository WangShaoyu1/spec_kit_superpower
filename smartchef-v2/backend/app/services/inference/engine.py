"""ONNX Runtime-based intent classification and slot extraction (dd §5.1, §5.2)."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass

try:
    import numpy as np
except (ImportError, OSError):
    np = None

try:
    import onnxruntime as ort
except (ImportError, OSError):
    ort = None

try:
    from transformers import AutoTokenizer
except (ImportError, OSError):
    AutoTokenizer = None


def load_json(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def softmax(x):
    if np is None:
        raise RuntimeError("numpy is required for inference")
    e = np.exp(x - np.max(x))
    return e / e.sum()


def _require_inference_deps() -> None:
    if np is None or ort is None or AutoTokenizer is None:
        raise RuntimeError(
            "Intent inference requires optional packages: numpy, onnxruntime, transformers. "
            "Install them to enable ONNX inference."
        )


@dataclass
class IntentResult:
    intent: str
    confidence: float
    all_scores: list[dict]
    latency_ms: int


@dataclass
class SlotResult:
    slots: list[dict]
    latency_ms: int


class IntentSlotInferenceEngine:
    """ONNX Runtime-based inference engine for intent classification + slot extraction."""

    def __init__(self, model_dir: str):
        """
        model_dir contains: model.onnx, label_map.json, slot_map.json, tokenizer/ (optional)
        """
        _require_inference_deps()

        onnx_path = os.path.join(model_dir, "model.onnx")
        self.onnx_session = ort.InferenceSession(
            onnx_path,
            providers=["CPUExecutionProvider"],
        )
        self.label_map = load_json(os.path.join(model_dir, "label_map.json"))
        self.slot_map = load_json(os.path.join(model_dir, "slot_map.json"))

        def _as_class_index(v) -> int:
            if isinstance(v, int):
                return v
            if isinstance(v, str) and v.lstrip("-").isdigit():
                return int(v)
            raise TypeError(f"label/slot map value must be int-like, got {type(v).__name__}: {v!r}")

        self.reverse_label_map = {_as_class_index(v): k for k, v in self.label_map.items()}
        self.reverse_slot_map = {_as_class_index(v): k for k, v in self.slot_map.items()}

        metadata_path = os.path.join(model_dir, "metadata.json")
        metadata = load_json(metadata_path) if os.path.isfile(metadata_path) else {}
        cfg = metadata.get("train_config") or metadata.get("config") or {}

        self.max_seq_length = cfg.get("max_seq_length", 128)

        tokenizer_path = os.path.join(model_dir, "tokenizer")
        base = tokenizer_path if os.path.isdir(tokenizer_path) else cfg.get("base_model", "bert-base-chinese")
        from app.core.hf_pretrained import resolve_pretrained_for_model

        resolved, kw = resolve_pretrained_for_model(base)
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(resolved, **kw)
        except (ValueError, OSError):
            from transformers import BertTokenizer

            self.tokenizer = BertTokenizer.from_pretrained(resolved, **kw)

    def classify_intent(self, text: str, max_seq_length: int | None = None) -> IntentResult:
        """DD §5.1: Intent classification via ONNX Runtime."""
        seq_len = max_seq_length or self.max_seq_length
        start = time.perf_counter()

        inputs = self.tokenizer(
            text,
            max_length=seq_len,
            padding="max_length",
            truncation=True,
            return_tensors="np",
        )
        intent_logits, _ = self.onnx_session.run(
            ["intent_logits", "slot_logits"],
            {"input_ids": inputs["input_ids"], "attention_mask": inputs["attention_mask"]},
        )

        probs = softmax(intent_logits[0])
        predicted_idx = int(np.argmax(probs))
        confidence = float(probs[predicted_idx])
        intent_key = self.reverse_label_map.get(predicted_idx, "unknown")

        all_scores = sorted(
            [
                {
                    "intent_key": self.reverse_label_map.get(i, f"label_{i}"),
                    "score": round(float(p), 4),
                }
                for i, p in enumerate(probs)
            ],
            key=lambda x: x["score"],
            reverse=True,
        )

        latency_ms = int((time.perf_counter() - start) * 1000)
        return IntentResult(
            intent=intent_key,
            confidence=confidence,
            all_scores=all_scores,
            latency_ms=latency_ms,
        )

    def extract_slots(self, text: str, max_seq_length: int | None = None) -> SlotResult:
        """DD §5.2: Slot extraction via ONNX Runtime with BIO decoding."""
        seq_len = max_seq_length or self.max_seq_length
        start = time.perf_counter()

        tok_kwargs: dict = {
            "max_length": seq_len,
            "padding": "max_length",
            "truncation": True,
            "return_tensors": "np",
        }
        if getattr(self.tokenizer, "is_fast", False):
            tok_kwargs["return_offsets_mapping"] = True

        inputs = self.tokenizer(text, **tok_kwargs)
        offset_mapping = inputs.pop("offset_mapping", None)
        if offset_mapping is not None:
            offset_mapping = offset_mapping[0]

        _, slot_logits = self.onnx_session.run(
            ["intent_logits", "slot_logits"],
            {"input_ids": inputs["input_ids"], "attention_mask": inputs["attention_mask"]},
        )

        tag_ids = np.argmax(slot_logits[0], axis=-1)
        attention_len = int(inputs["attention_mask"][0].sum())

        bio_tags = [self.reverse_slot_map.get(int(tid), "O") for tid in tag_ids[:attention_len]]
        if offset_mapping is not None and len(offset_mapping) >= attention_len:
            offset_rows = [tuple(int(x) for x in offset_mapping[i]) for i in range(attention_len)]
        else:
            offset_rows = [(0, 0)] * attention_len

        slots: list[dict] = []
        current: dict | None = None
        for tag, offset in zip(bio_tags, offset_rows, strict=True):
            if tag.startswith("B-"):
                if current:
                    current["value"] = text[current["start"] : current["end"]].strip()
                    if current["value"]:
                        slots.append(current)
                current = {"name": tag[2:], "start": int(offset[0]), "end": int(offset[1])}
            elif tag.startswith("I-") and current and tag[2:] == current["name"]:
                current["end"] = int(offset[1])
            else:
                if current:
                    current["value"] = text[current["start"] : current["end"]].strip()
                    if current["value"]:
                        slots.append(current)
                    current = None
        if current:
            current["value"] = text[current["start"] : current["end"]].strip()
            if current["value"]:
                slots.append(current)

        latency_ms = int((time.perf_counter() - start) * 1000)
        return SlotResult(slots=slots, latency_ms=latency_ms)
