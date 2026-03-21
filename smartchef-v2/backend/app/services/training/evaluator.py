"""Batch evaluation pipeline (dd-intent-library §5.5)."""

from __future__ import annotations

import logging
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from uuid import UUID  # noqa: TC003

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.dataset import EvaluationDataset
from app.models.evaluation import EvaluationRun
from app.models.intent_library import IntentLibrary
from app.models.model_version import LibraryModelVersion
from app.services.inference.model_cache import ModelCache

logger = logging.getLogger(__name__)


def _slots_match(expected: dict, pred_slots: list[dict]) -> bool:
    if not expected:
        return True
    actual = {s["name"]: s["value"] for s in pred_slots}
    return all(key in actual and actual[key] == val for key, val in expected.items())


def compute_confusion_pairs(results: list[dict], top_n: int = 5) -> list[dict]:
    counts: Counter[tuple[str, str]] = Counter()
    for r in results:
        if not r["intent_correct"]:
            counts[(r["expected_intent"], r["predicted_intent"])] += 1
    ordered = sorted(counts.items(), key=lambda x: -x[1])[:top_n]
    return [{"from": a, "to": b, "count": c} for (a, b), c in ordered]


def compute_slot_errors(results: list[dict]) -> list[dict]:
    err_counts: Counter[tuple[str, str]] = Counter()
    for r in results:
        exp = r.get("expected_slots") or {}
        if not exp or r.get("slot_correct"):
            continue
        pred_list = r.get("predicted_slots") or []
        pred = {s["name"]: s["value"] for s in pred_list}
        for k in exp:
            if k not in pred:
                err_counts[(k, "missing")] += 1
            elif pred[k] != exp[k]:
                err_counts[(k, "value_mismatch")] += 1
        for k in pred:
            if k not in exp:
                err_counts[(k, "extra")] += 1
    ordered = sorted(err_counts.items(), key=lambda x: -x[1])
    return [{"slot": slot, "error_type": etype, "count": n} for (slot, etype), n in ordered]


def compute_evaluation_summary(
    results: list,
    threshold_if1: float,
    threshold_sf1: float,
    has_slots_count: int,
) -> dict:
    total = len(results)
    intent_correct = sum(1 for r in results if r["intent_correct"])
    intent_accuracy = intent_correct / total if total > 0 else 0.0

    per_intent: dict = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    for r in results:
        if r["intent_correct"]:
            per_intent[r["expected_intent"]]["tp"] += 1
        else:
            per_intent[r["expected_intent"]]["fn"] += 1
            per_intent[r["predicted_intent"]]["fp"] += 1

    intent_f1_scores = []
    for metrics in per_intent.values():
        p = metrics["tp"] / (metrics["tp"] + metrics["fp"]) if (metrics["tp"] + metrics["fp"]) > 0 else 0
        r_ = metrics["tp"] / (metrics["tp"] + metrics["fn"]) if (metrics["tp"] + metrics["fn"]) > 0 else 0
        f1 = 2 * p * r_ / (p + r_) if (p + r_) > 0 else 0
        intent_f1_scores.append(f1)
    intent_f1 = sum(intent_f1_scores) / len(intent_f1_scores) if intent_f1_scores else 0.0

    slot_correct = sum(1 for r in results if r.get("slot_correct", True) and r.get("expected_slots"))
    slot_f1 = slot_correct / has_slots_count if has_slots_count > 0 else 1.0

    confusion_pairs = compute_confusion_pairs(results, top_n=5)
    slot_errors = compute_slot_errors(results)
    low_score = [
        {
            "text": r["text"],
            "expected": r["expected_intent"],
            "predicted": r["predicted_intent"],
            "score": r["confidence"],
        }
        for r in results
        if r["confidence"] < 0.7
    ][:20]

    return {
        "intent_accuracy": round(intent_accuracy, 4),
        "intent_f1": round(intent_f1, 4),
        "slot_f1": round(slot_f1, 4),
        "pass_intent_threshold": intent_f1 >= threshold_if1,
        "pass_slot_threshold": slot_f1 >= threshold_sf1,
        "total_samples": total,
        "hit_count": intent_correct,
        "confusion_pairs": confusion_pairs,
        "slot_errors": slot_errors,
        "low_score_samples": low_score,
    }


def _artifact_model_dir(artifact_uri: str | None) -> str | None:
    if not artifact_uri:
        return None

    if artifact_uri.rstrip("/").endswith(".onnx"):
        return os.path.dirname(artifact_uri)
    return artifact_uri.rstrip("/")


def _sample_utterance(sample: dict) -> str:
    return str(sample.get("utterance") or sample.get("text") or "")


def _sample_expected_intent(sample: dict) -> str:
    return str(sample.get("expected_result") or sample.get("expected_intent") or "")


async def _restore_evaluation_model_status(
    db: AsyncSession,
    model: LibraryModelVersion,
    snapshot: dict,
) -> None:
    prev = (snapshot or {}).get("model_status") or "trained"
    if prev == "published":
        model.status = "published"
    elif prev == "testable":
        model.status = "testable"
    else:
        model.status = "trained"


async def execute_batch_evaluation(run_id: UUID, db_url: str) -> None:
    """
    Runs as BackgroundTask. Creates own DB engine and session.
    Steps:
    1. Load EvaluationRun, model, evaluation dataset
    2. Load ONNX model via inference engine
    3. For each evaluation sample: classify_intent, extract_slots; compare labels
    4. Compute metrics per DD §5.5
    5. Build confusion_pairs, slot_errors, low_score_samples
    6. Update run with result_summary
    7. Restore model status; merge latest_eval into model.metrics
    """
    engine = create_async_engine(db_url, pool_pre_ping=True)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        async with factory() as db:
            try:
                await _execute_batch_evaluation_impl(db, run_id)
                await db.commit()
            except Exception as e:
                await db.rollback()
                run_row = await db.get(EvaluationRun, run_id)
                model_row = (
                    await db.get(LibraryModelVersion, run_row.model_version_id)
                    if run_row
                    else None
                )
                if run_row:
                    run_row.status = "failed"
                    run_row.completed_at = datetime.now(timezone.utc)
                    run_row.result_summary = {"error": str(e)[:500]}
                if model_row:
                    await _restore_evaluation_model_status(db, model_row, (run_row.snapshot if run_row else {}) or {})
                await db.commit()
                logger.exception("Evaluation run %s failed", run_id)
    finally:
        await engine.dispose()


async def _execute_batch_evaluation_impl(db: AsyncSession, run_id: UUID) -> None:
    run = await db.get(EvaluationRun, run_id)
    if not run:
        raise RuntimeError(f"Evaluation run 不存在: {run_id}")

    run.status = "running"
    run.started_at = datetime.now(timezone.utc)
    if run.total_samples == 0:
        ds0 = await db.get(EvaluationDataset, run.dataset_id)
        if ds0:
            run.total_samples = ds0.sample_count or len(ds0.samples or [])

    model = await db.get(LibraryModelVersion, run.model_version_id)
    dataset = await db.get(EvaluationDataset, run.dataset_id)
    if not model or not dataset:
        raise RuntimeError("模型或评测数据集不存在")

    library = await db.get(IntentLibrary, model.library_id)
    if not run.snapshot:
        run.snapshot = {
            "model_status": model.status,
            "model_version_name": model.version_name,
            "dataset_name": dataset.name,
            "dataset_sample_count": dataset.sample_count,
            "library_default_threshold": library.default_confidence_threshold if library else 0.7,
        }

    from app.core.config import resolve_artifact_path
    resolved_uri = resolve_artifact_path(model.artifact_uri)
    artifact_dir = _artifact_model_dir(resolved_uri)
    if not artifact_dir:
        raise RuntimeError("模型未导出或无 artifact_uri")

    samples = dataset.samples or []
    if not samples:
        raise RuntimeError("评估集为空")

    results: list[dict] = []
    has_slots_count = 0

    try:
        inference_engine = ModelCache.get_or_load(artifact_dir)
    except Exception as e:
        raise RuntimeError(f"加载 ONNX 推理引擎失败: {e}") from e

    for i, sample in enumerate(samples):
        utterance = _sample_utterance(sample)
        expected_intent = _sample_expected_intent(sample)
        expected_slots = sample.get("expected_slots") or {}

        intent_res = inference_engine.classify_intent(utterance)
        slot_res = inference_engine.extract_slots(utterance)

        is_intent_hit = intent_res.intent == expected_intent
        is_slot_hit = _slots_match(expected_slots, slot_res.slots) if expected_slots else True

        if expected_slots:
            has_slots_count += 1

        pred_slots_dict = [
            {"name": s["name"], "value": s["value"], "start": s.get("start"), "end": s.get("end")}
            for s in slot_res.slots
        ]

        results.append(
            {
                "text": utterance,
                "expected_intent": expected_intent,
                "predicted_intent": intent_res.intent,
                "intent_correct": is_intent_hit,
                "confidence": intent_res.confidence,
                "expected_slots": expected_slots,
                "predicted_slots": pred_slots_dict,
                "slot_correct": is_slot_hit,
            }
        )

        if (i + 1) % 10 == 0:
            run.completed_samples = i + 1
            await db.flush()

    summary = compute_evaluation_summary(results, run.threshold_intent_f1, run.threshold_slot_f1, has_slots_count)
    run.status = "completed"
    run.completed_at = datetime.now(timezone.utc)
    run.completed_samples = len(samples)
    run.result_summary = summary

    merged = dict(model.metrics or {})
    merged["latest_eval"] = summary
    model.metrics = merged

    await _restore_evaluation_model_status(db, model, run.snapshot or {})
