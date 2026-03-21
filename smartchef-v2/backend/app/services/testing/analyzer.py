"""Post-execution analysis: accuracy, confusion matrix, slot errors, recommendations."""

import math
import uuid
from collections import Counter, defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.batch_test import TestRun, TestRunAnalysis
from app.services.testing import batch_service


def _slots_match(expected: dict, actual: dict) -> bool:
    if not expected:
        return True
    for key, val in expected.items():
        if key not in actual or actual.get(key) != val:
            return False
    return True


def _macro_prf1_from_pairs(pairs: list[tuple[str, str]]) -> tuple[float | None, float | None, float | None]:
    if not pairs:
        return None, None, None
    labels: set[str] = set()
    for e, a in pairs:
        labels.add(e)
        labels.add(a)
    precs, recs, f1s = [], [], []
    for label in labels:
        tp = sum(1 for e, a in pairs if e == label and a == label)
        fp = sum(1 for e, a in pairs if e != label and a == label)
        fn = sum(1 for e, a in pairs if e == label and a != label)
        p = tp / (tp + fp) if (tp + fp) else 0.0
        r = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * p * r / (p + r) if (p + r) else 0.0
        precs.append(p)
        recs.append(r)
        f1s.append(f1)
    return (
        round(sum(precs) / len(precs), 4),
        round(sum(recs) / len(recs), 4),
        round(sum(f1s) / len(f1s), 4),
    )


def _failure_attribution(runs: list[TestRun], max_samples: int = 5) -> dict:
    cats = {
        "timeout": {"count": 0, "samples": []},
        "intent_mismatch": {"count": 0, "samples": []},
        "domain_mismatch": {"count": 0, "samples": []},
        "slot_error": {"count": 0, "samples": []},
        "low_confidence": {"count": 0, "samples": []},
    }

    def push(cat: str, r: TestRun) -> None:
        entry = cats[cat]
        entry["count"] += 1
        if len(entry["samples"]) < max_samples:
            txt = r.case.input_text if r.case else ""
            entry["samples"].append({
                "input": txt,
                "expected_intent": r.case.expected_intent if r.case else None,
                "actual_intent": r.actual_intent,
                "confidence": r.confidence,
            })

    for r in runs:
        if r.error_message:
            push("timeout", r)
            continue
        if r.is_intent_hit is False:
            push("intent_mismatch", r)
            continue
        if r.is_domain_hit is False:
            push("domain_mismatch", r)
            continue
        if r.case and r.case.expected_slots and not _slots_match(
            r.case.expected_slots or {}, r.actual_slots or {},
        ):
            push("slot_error", r)
            continue
        if r.confidence is not None and r.confidence < 0.35:
            push("low_confidence", r)

    return {k: {"count": v["count"], "samples": v["samples"]} for k, v in cats.items()}


async def generate_analysis(db: AsyncSession, batch_id: uuid.UUID) -> TestRunAnalysis:
    batch = await batch_service.get_batch(db, batch_id)

    runs_result = await db.execute(
        select(TestRun)
        .options(joinedload(TestRun.case))
        .where(TestRun.batch_id == batch_id)
    )
    runs = runs_result.unique().scalars().all()

    total = len(runs)
    if total == 0:
        summary = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "accuracy": 0,
            "avg_latency": 0,
            "p99_latency": 0,
            "f1_score": None,
            "intent_accuracy_rank": [],
            "failure_attribution": {},
        }
        analysis = TestRunAnalysis(
            id=uuid.uuid4(), batch_id=batch_id, summary=summary,
        )
        db.add(analysis)
        await db.flush()
        await db.refresh(analysis)
        return analysis

    intent_hits = sum(1 for r in runs if r.is_intent_hit is True)
    domain_hits = sum(1 for r in runs if r.is_domain_hit is True)
    errors = sum(1 for r in runs if r.error_message)
    latencies = [r.latency_ms for r in runs if r.latency_ms is not None]
    avg_latency = round(sum(latencies) / len(latencies)) if latencies else 0
    p99_latency = None
    if latencies:
        sl = sorted(latencies)
        idx = min(len(sl) - 1, max(0, math.ceil(0.99 * len(sl)) - 1))
        p99_latency = sl[idx]

    evaluable_intent = [r for r in runs if r.is_intent_hit is not None]
    accuracy = round(intent_hits / len(evaluable_intent), 4) if evaluable_intent else 0

    intent_pairs: list[tuple[str, str]] = []
    for r in runs:
        if r.case and r.case.expected_intent and r.actual_intent:
            intent_pairs.append((r.case.expected_intent, r.actual_intent))
    macro_p, macro_r, macro_f1 = _macro_prf1_from_pairs(intent_pairs)

    by_intent: dict[str, dict[str, int]] = defaultdict(lambda: {"correct": 0, "total": 0})
    for r in runs:
        if not r.case or not r.case.expected_intent:
            continue
        k = r.case.expected_intent
        by_intent[k]["total"] += 1
        if r.is_intent_hit is True:
            by_intent[k]["correct"] += 1
    intent_accuracy_rank = [
        {
            "intent": name,
            "correct": v["correct"],
            "total": v["total"],
            "accuracy": round(v["correct"] / v["total"], 4) if v["total"] else 0,
        }
        for name, v in by_intent.items()
    ]
    intent_accuracy_rank.sort(key=lambda x: (x["accuracy"], x["intent"]))

    summary = {
        "total": total,
        "passed": intent_hits,
        "failed": total - intent_hits - errors,
        "errors": errors,
        "accuracy": accuracy,
        "domain_accuracy": round(domain_hits / len([r for r in runs if r.is_domain_hit is not None]), 4)
        if any(r.is_domain_hit is not None for r in runs) else None,
        "avg_latency": avg_latency,
        "p99_latency": p99_latency or 0,
        "f1_score": macro_f1,
        "intent_accuracy_rank": intent_accuracy_rank,
        "failure_attribution": _failure_attribution(runs),
    }

    confusion_counter: Counter = Counter()
    for r in runs:
        if r.case and r.case.expected_intent and r.actual_intent:
            if r.case.expected_intent != r.actual_intent:
                confusion_counter[(r.case.expected_intent, r.actual_intent)] += 1

    confusion_top_n = [
        {"expected": k[0], "actual": k[1], "count": v}
        for k, v in confusion_counter.most_common(20)
    ]

    slot_errors: dict[str, dict[str, int]] = {}
    for r in runs:
        if not r.case:
            continue
        expected = r.case.expected_slots or {}
        actual = r.actual_slots or {}
        for key in set(list(expected.keys()) + list(actual.keys())):
            if key not in slot_errors:
                slot_errors[key] = {"missing_count": 0, "wrong_count": 0}
            if key in expected and key not in actual:
                slot_errors[key]["missing_count"] += 1
            elif key in expected and key in actual and expected[key] != actual[key]:
                slot_errors[key]["wrong_count"] += 1

    slot_error_distribution = [
        {"slot_key": k, **v}
        for k, v in sorted(slot_errors.items(), key=lambda x: -(x[1]["missing_count"] + x[1]["wrong_count"]))
        if v["missing_count"] + v["wrong_count"] > 0
    ]

    low_score_samples = []
    scored_runs = sorted(
        [r for r in runs if r.confidence is not None],
        key=lambda r: r.confidence,
    )
    for r in scored_runs[:20]:
        low_score_samples.append({
            "case_id": str(r.case_id),
            "input": r.case.input_text if r.case else "",
            "expected": r.case.expected_intent if r.case else None,
            "actual": r.actual_intent,
            "confidence": r.confidence,
        })

    recommendations = _generate_recommendations(summary, confusion_top_n, slot_error_distribution)

    batch.accuracy = accuracy
    batch.precision_score = macro_p
    batch.recall_score = macro_r
    batch.p99_latency_ms = p99_latency
    await db.flush()

    analysis = TestRunAnalysis(
        id=uuid.uuid4(),
        batch_id=batch_id,
        summary=summary,
        confusion_top_n=confusion_top_n,
        slot_error_distribution=slot_error_distribution,
        low_score_samples=low_score_samples,
        recommendations=recommendations,
    )
    db.add(analysis)
    await db.flush()
    await db.refresh(analysis)
    return analysis


def _generate_recommendations(
    summary: dict,
    confusion: list[dict],
    slot_errors: list[dict],
) -> list[str]:
    recs: list[str] = []
    accuracy = summary.get("accuracy", 0)

    if accuracy < 0.6:
        recs.append("整体准确率偏低，建议检查训练数据质量和覆盖度")
    elif accuracy < 0.8:
        recs.append("准确率有提升空间，建议针对错误集中的意图补充训练样本")

    if confusion:
        top = confusion[0]
        recs.append(
            f"混淆最严重: 「{top['expected']}」被误识别为「{top['actual']}」共 {top['count']} 次，"
            "建议检查两者训练数据的区分度"
        )

    if slot_errors:
        top_slot = slot_errors[0]
        recs.append(
            f"槽位「{top_slot['slot_key']}」错误最多 "
            f"(缺失 {top_slot['missing_count']}、错误 {top_slot['wrong_count']})，"
            "建议补充实体标注"
        )

    avg_lat = summary.get("avg_latency", 0)
    if avg_lat > 500:
        recs.append(f"平均延迟 {avg_lat}ms 偏高，建议检查模型推理性能")

    if not recs:
        recs.append("测试结果良好，建议持续监控并定期回归测试")

    return recs
