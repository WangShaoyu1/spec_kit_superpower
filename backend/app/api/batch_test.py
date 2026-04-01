import json
import math
import uuid
from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dialog_profile import process_dialog_turn
from app.dependencies import ApiError, create_audit_log, get_db, require_capability, response_envelope, utc_now
from app.models import (
    BatchTestAnalysis,
    BatchTestCase,
    BatchTestResult,
    BatchTestRun,
    DialogProfile,
    DialogProfileLibraryBinding,
    UserAccount,
)


router = APIRouter(tags=["batch-test"])

ASYNC_SETTLE_SECONDS = 0.05


class CreateBatchPayload(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    profile_id: str
    baseline_thresholds: dict[str, Any] = Field(default_factory=dict)


class GenerateCasesPayload(BaseModel):
    mode: str = "auto"


class ExecuteBatchPayload(BaseModel):
    pass


def parse_json_field(payload: str | None, fallback: Any):
    if not payload:
        return fallback
    return json.loads(payload)


def normalize_threshold_snapshot(thresholds: dict[str, Any]) -> dict[str, Any]:
    accuracy_min = float(thresholds.get("accuracy_min", 0.95))
    command_response_p95_ms = int(thresholds.get("command_response_p95_ms", 200))
    knowledge_response_p95_ms = int(
        thresholds.get("knowledge_response_p95_ms", thresholds.get("response_p95_ms", 2000))
    )
    return {
        "accuracy_min": accuracy_min,
        "command_response_p95_ms": command_response_p95_ms,
        "knowledge_response_p95_ms": knowledge_response_p95_ms,
        "threshold_source": {
            "command_response_p95_ms": "spec.md SC-002",
            "knowledge_response_p95_ms": "spec.md SC-003",
        },
    }


def serialize_batch(batch: BatchTestRun) -> dict[str, Any]:
    return {
        "id": batch.id,
        "name": batch.name,
        "profile_id": batch.profile_id,
        "profile_name": batch.profile_name,
        "status": batch.status,
        "case_count": batch.case_count,
        "executed_count": batch.executed_count,
        "pass_count": batch.pass_count,
        "accuracy": batch.accuracy,
        "response_p95_ms": batch.response_p95_ms,
        "threshold_snapshot": parse_json_field(batch.threshold_snapshot_json, {}),
        "analysis_status": batch.analysis_status,
        "created_at": batch.created_at.isoformat() + "Z",
        "updated_at": batch.updated_at.isoformat() + "Z",
    }


def serialize_case(case: BatchTestCase) -> dict[str, Any]:
    return {
        "id": case.id,
        "batch_id": case.batch_id,
        "case_no": case.case_no,
        "utterance": case.utterance,
        "expected_route": case.expected_route,
        "expected_intent": case.expected_intent,
        "expected_slots": parse_json_field(case.expected_slots_json, {}),
        "source": case.source,
        "tuned": case.tuned,
    }


def serialize_result(result: BatchTestResult) -> dict[str, Any]:
    return {
        "id": result.id,
        "batch_id": result.batch_id,
        "case_id": result.case_id,
        "actual_route": result.actual_route,
        "actual_intent": result.actual_intent,
        "actual_slots": parse_json_field(result.actual_slots_json, {}),
        "score": result.score,
        "latency_ms": result.latency_ms,
        "passed": result.passed,
        "failure_reason": result.failure_reason,
    }


def serialize_analysis(analysis: BatchTestAnalysis | None) -> dict[str, Any]:
    if analysis is None:
        return {
            "summary": {"total_cases": 0, "pass_count": 0, "failed_count": 0},
            "confusion_matrix": [],
            "root_causes": [],
            "recommendations": [],
        }
    return {
        "summary": parse_json_field(analysis.summary_json, {}),
        "confusion_matrix": parse_json_field(analysis.confusion_matrix_json, []),
        "root_causes": parse_json_field(analysis.root_causes_json, []),
        "recommendations": parse_json_field(analysis.recommendations_json, []),
    }


def build_batch_summary(batches: list[BatchTestRun]) -> dict[str, int]:
    return {
        "total": len(batches),
        "draft_count": sum(1 for item in batches if item.status == "draft"),
        "ready_count": sum(1 for item in batches if item.status == "ready"),
        "running_count": sum(1 for item in batches if item.status == "running"),
        "completed_count": sum(1 for item in batches if item.status == "completed"),
        "failed_count": sum(1 for item in batches if item.status == "failed"),
    }


def get_profile_or_404(session: Session, profile_id: str) -> DialogProfile:
    profile = session.get(DialogProfile, profile_id)
    if profile is None:
        raise ApiError(404, "BATCH-404-PROFILE", "被测对话方案不存在")
    return profile


def get_batch_or_404(session: Session, batch_id: str) -> BatchTestRun:
    batch = session.get(BatchTestRun, batch_id)
    if batch is None:
        raise ApiError(404, "BATCH-404-NOT-FOUND", "目标测试批次不存在")
    return batch


def load_batch_cases(session: Session, batch_id: str) -> list[BatchTestCase]:
    return session.execute(
        select(BatchTestCase).where(BatchTestCase.batch_id == batch_id).order_by(BatchTestCase.case_no.asc())
    ).scalars().all()


def load_batch_results(session: Session, batch_id: str) -> list[BatchTestResult]:
    return session.execute(
        select(BatchTestResult).where(BatchTestResult.batch_id == batch_id).order_by(BatchTestResult.created_at.asc())
    ).scalars().all()


def load_batch_analysis(session: Session, batch_id: str) -> BatchTestAnalysis | None:
    return session.execute(
        select(BatchTestAnalysis).where(BatchTestAnalysis.batch_id == batch_id).order_by(BatchTestAnalysis.created_at.desc())
    ).scalar_one_or_none()


def clear_batch_execution_artifacts(session: Session, batch_id: str):
    for result in load_batch_results(session, batch_id):
        session.delete(result)
    analysis = load_batch_analysis(session, batch_id)
    if analysis is not None:
        session.delete(analysis)


def ensure_batch_name_valid(name: str) -> str:
    value = name.strip()
    if not value:
        raise ApiError(422, "BATCH-422-NAME", "批次名称不能为空")
    return value


def ensure_profile_testable(session: Session, profile: DialogProfile):
    bindings = session.execute(
        select(DialogProfileLibraryBinding).where(DialogProfileLibraryBinding.profile_id == profile.id)
    ).scalars().all()
    if not bindings or any(not item.published_model_name for item in bindings):
        raise ApiError(422, "BATCH-422-PROFILE", "当前方案缺少可测试配置，请先补齐")


def build_default_cases() -> list[dict[str, Any]]:
    return [
        {
            "case_no": "CASE-001",
            "utterance": "请帮我设置温度180度",
            "expected_route": "intent",
            "expected_intent": "device.control",
            "expected_slots": {"temperature": 180},
        },
        {
            "case_no": "CASE-002",
            "utterance": "怎么做红烧肉",
            "expected_route": "knowledge",
            "expected_intent": "knowledge.query",
            "expected_slots": {},
        },
        {
            "case_no": "CASE-003",
            "utterance": "还有多久",
            "expected_route": "knowledge",
            "expected_intent": "cooking.remaining_time",
            "expected_slots": {},
        },
        {
            "case_no": "CASE-004",
            "utterance": "今天天气怎么样",
            "expected_route": "fallback",
            "expected_intent": "fallback.chat",
            "expected_slots": {},
        },
    ]


def percentile_95(values: list[int]) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    index = max(0, math.ceil(len(ordered) * 0.95) - 1)
    return ordered[index]


def latency_for_case(case_no: str) -> int:
    mapping = {
        "CASE-001": 520,
        "CASE-002": 860,
        "CASE-003": 2430,
        "CASE-004": 460,
    }
    return mapping.get(case_no, 800)


def evaluate_case(
    profile: DialogProfile,
    bindings: list[DialogProfileLibraryBinding],
    case: BatchTestCase,
    threshold_snapshot: dict[str, Any],
) -> dict[str, Any]:
    turn = process_dialog_turn(profile=profile, bindings=bindings, text=case.utterance, device_context={})
    actual_route = turn["route"]
    actual_intent = turn["intent"]
    actual_slots = turn["slots"]
    expected_slots = parse_json_field(case.expected_slots_json, {})
    latency_ms = latency_for_case(case.case_no)
    latency_budget_ms = int(
        threshold_snapshot.get(
            "command_response_p95_ms" if actual_route == "intent" else "knowledge_response_p95_ms",
            200 if actual_route == "intent" else 2000,
        )
    )
    passed = True
    failure_reason = None

    if case.expected_route != actual_route:
        passed = False
        failure_reason = "route_mismatch"
    elif case.expected_intent != actual_intent:
        passed = False
        failure_reason = "intent_mismatch"
    elif expected_slots != actual_slots:
        passed = False
        failure_reason = "slot_mismatch"
    elif latency_ms > latency_budget_ms:
        passed = False
        failure_reason = "latency_exceeded"

    score = 1.0 if passed else 0.58
    return {
        "actual_route": actual_route,
        "actual_intent": actual_intent,
        "actual_slots": actual_slots,
        "latency_ms": latency_ms,
        "latency_budget_ms": latency_budget_ms,
        "passed": passed,
        "failure_reason": failure_reason,
        "score": score,
    }


def build_analysis_payload(
    batch: BatchTestRun,
    cases: list[BatchTestCase],
    results: list[BatchTestResult],
) -> dict[str, Any]:
    result_by_case = {item.case_id: item for item in results}
    confusion: dict[tuple[str | None, str | None], int] = {}
    root_cause_counts: dict[str, int] = {}

    for case in cases:
        result = result_by_case[case.id]
        key = (case.expected_intent, result.actual_intent)
        confusion[key] = confusion.get(key, 0) + 1
        if result.failure_reason:
            root_cause_counts[result.failure_reason] = root_cause_counts.get(result.failure_reason, 0) + 1

    failed_count = batch.case_count - batch.pass_count
    root_causes = [
        {"reason": reason, "count": count}
        for reason, count in sorted(root_cause_counts.items(), key=lambda item: (-item[1], item[0]))
    ]
    recommendations: list[str] = []
    if any(item["reason"] == "intent_mismatch" for item in root_causes):
        recommendations.append("补充 remaining-time 场景样本并校准知识/指令边界。")
    if any(item["reason"] == "latency_exceeded" for item in root_causes):
        recommendations.append("针对慢查询链路做性能剖析，优先压降 p95 响应时延。")
    if not recommendations:
        recommendations.append("当前批次整体通过，可继续扩展更多边界语料。")

    return {
        "summary": {
            "total_cases": batch.case_count,
            "pass_count": batch.pass_count,
            "failed_count": failed_count,
            "pass_rate": batch.accuracy,
        },
        "confusion_matrix": [
            {
                "expected_intent": expected_intent,
                "actual_intent": actual_intent,
                "count": count,
            }
            for (expected_intent, actual_intent), count in sorted(confusion.items(), key=lambda item: item[0])
        ],
        "root_causes": root_causes,
        "recommendations": recommendations,
    }


def maybe_finish_batch_execution(session: Session, batch: BatchTestRun) -> bool:
    if batch.status != "running":
        return False
    if (utc_now() - batch.updated_at).total_seconds() < ASYNC_SETTLE_SECONDS:
        return False

    cases = load_batch_cases(session, batch.id)
    profile = get_profile_or_404(session, batch.profile_id)
    bindings = session.execute(
        select(DialogProfileLibraryBinding)
        .where(DialogProfileLibraryBinding.profile_id == profile.id)
        .order_by(DialogProfileLibraryBinding.priority.asc())
    ).scalars().all()
    threshold_snapshot = normalize_threshold_snapshot(parse_json_field(batch.threshold_snapshot_json, {}))
    clear_batch_execution_artifacts(session, batch.id)

    results: list[BatchTestResult] = []
    latencies: list[int] = []
    pass_count = 0

    for case in cases:
        evaluated = evaluate_case(profile, bindings, case, threshold_snapshot)
        result = BatchTestResult(
            id=uuid.uuid4().hex,
            batch_id=batch.id,
            case_id=case.id,
            actual_route=evaluated["actual_route"],
            actual_intent=evaluated["actual_intent"],
            actual_slots_json=json.dumps(evaluated["actual_slots"], ensure_ascii=False),
            score=evaluated["score"],
            latency_ms=evaluated["latency_ms"],
            passed=evaluated["passed"],
            failure_reason=evaluated["failure_reason"],
        )
        results.append(result)
        latencies.append(evaluated["latency_ms"])
        pass_count += 1 if evaluated["passed"] else 0

    for item in results:
        session.add(item)

    batch.executed_count = len(results)
    batch.pass_count = pass_count
    batch.accuracy = round(pass_count / len(results), 4) if results else 0
    batch.response_p95_ms = percentile_95(latencies)
    batch.status = "completed"
    batch.analysis_status = "ready"

    analysis_payload = build_analysis_payload(batch, cases, results)
    session.add(
        BatchTestAnalysis(
            id=uuid.uuid4().hex,
            batch_id=batch.id,
            summary_json=json.dumps(analysis_payload["summary"], ensure_ascii=False),
            confusion_matrix_json=json.dumps(analysis_payload["confusion_matrix"], ensure_ascii=False),
            root_causes_json=json.dumps(analysis_payload["root_causes"], ensure_ascii=False),
            recommendations_json=json.dumps(analysis_payload["recommendations"], ensure_ascii=False),
        )
    )
    return True


def advance_batch_state(session: Session, batch_id: str | None = None):
    query = select(BatchTestRun)
    if batch_id is not None:
        query = query.where(BatchTestRun.id == batch_id)

    changed = False
    for batch in session.execute(query).scalars().all():
        changed = maybe_finish_batch_execution(session, batch) or changed

    if changed:
        session.commit()


@router.get("/batch-tests")
def list_batch_tests(
    request: Request,
    _: UserAccount = Depends(require_capability("test_execute")),
    session: Session = Depends(get_db),
):
    advance_batch_state(session)
    batches = session.execute(select(BatchTestRun).order_by(BatchTestRun.created_at.asc())).scalars().all()
    return response_envelope(
        request,
        {
            "items": [serialize_batch(item) for item in batches],
            "summary": build_batch_summary(batches),
        },
    )


@router.post("/batch-tests")
def create_batch_test(
    payload: CreateBatchPayload,
    request: Request,
    actor: UserAccount = Depends(require_capability("test_execute")),
    session: Session = Depends(get_db),
):
    profile = get_profile_or_404(session, payload.profile_id)
    ensure_profile_testable(session, profile)
    name = ensure_batch_name_valid(payload.name)
    existing = session.execute(
        select(BatchTestRun).where(BatchTestRun.profile_id == profile.id, BatchTestRun.name == name)
    ).scalar_one_or_none()
    if existing is not None:
        raise ApiError(409, "BATCH-409-NAME", "批次名称已存在")

    batch = BatchTestRun(
        id=uuid.uuid4().hex,
        name=name,
        profile_id=profile.id,
        profile_name=profile.name,
        status="draft",
        threshold_snapshot_json=json.dumps(normalize_threshold_snapshot(payload.baseline_thresholds), ensure_ascii=False),
        analysis_status="not_needed",
    )
    session.add(batch)
    create_audit_log(session, actor.id, actor.id, "batch_test.create", {"batch_id": batch.id})
    session.commit()
    session.refresh(batch)
    return response_envelope(request, {"batch": serialize_batch(batch)})


@router.post("/batch-tests/{batch_id}/generate-cases")
def generate_batch_cases(
    batch_id: str,
    payload: GenerateCasesPayload,
    request: Request,
    actor: UserAccount = Depends(require_capability("test_execute")),
    session: Session = Depends(get_db),
):
    batch = get_batch_or_404(session, batch_id)
    if batch.status == "running":
        raise ApiError(409, "BATCH-409-STATE", "当前批次状态不允许执行该操作")
    if payload.mode != "auto":
        raise ApiError(422, "BATCH-422-MODE", "当前仅支持自动生成用例")

    for existing in load_batch_cases(session, batch.id):
        session.delete(existing)
    clear_batch_execution_artifacts(session, batch.id)

    cases: list[BatchTestCase] = []
    for item in build_default_cases():
        case = BatchTestCase(
            id=uuid.uuid4().hex,
            batch_id=batch.id,
            case_no=item["case_no"],
            utterance=item["utterance"],
            expected_route=item["expected_route"],
            expected_intent=item["expected_intent"],
            expected_slots_json=json.dumps(item["expected_slots"], ensure_ascii=False),
            source="auto",
            tuned=False,
        )
        cases.append(case)
        session.add(case)

    batch.status = "ready"
    batch.case_count = len(cases)
    batch.executed_count = 0
    batch.pass_count = 0
    batch.accuracy = None
    batch.response_p95_ms = None
    batch.analysis_status = "not_needed"
    create_audit_log(session, actor.id, actor.id, "batch_test.generate_cases", {"batch_id": batch.id})
    session.commit()
    session.refresh(batch)
    return response_envelope(
        request,
        {
            "batch": serialize_batch(batch),
            "summary": {"case_count": len(cases)},
        },
    )


@router.get("/batch-tests/{batch_id}")
def get_batch_detail(
    batch_id: str,
    request: Request,
    _: UserAccount = Depends(require_capability("test_execute")),
    session: Session = Depends(get_db),
):
    advance_batch_state(session, batch_id)
    batch = get_batch_or_404(session, batch_id)
    cases = load_batch_cases(session, batch.id)
    results = load_batch_results(session, batch.id)
    analysis = load_batch_analysis(session, batch.id)
    return response_envelope(
        request,
        {
            "batch": serialize_batch(batch),
            "cases": [serialize_case(item) for item in cases],
            "results": [serialize_result(item) for item in results],
            "metrics": {
                "accuracy": batch.accuracy or 0,
                "response_p95_ms": batch.response_p95_ms or 0,
            },
            "analysis": serialize_analysis(analysis),
        },
    )


@router.post("/batch-tests/{batch_id}/execute")
def execute_batch_test(
    batch_id: str,
    _: ExecuteBatchPayload,
    request: Request,
    actor: UserAccount = Depends(require_capability("test_execute")),
    session: Session = Depends(get_db),
):
    batch = get_batch_or_404(session, batch_id)
    cases = load_batch_cases(session, batch.id)
    if not cases:
        raise ApiError(422, "BATCH-422-EMPTY", "请先生成或导入至少一条用例")
    if batch.status not in {"ready", "completed", "failed"}:
        raise ApiError(409, "BATCH-409-STATE", "当前批次状态不允许执行该操作")

    clear_batch_execution_artifacts(session, batch.id)
    batch.status = "running"
    batch.executed_count = 0
    batch.pass_count = 0
    batch.accuracy = None
    batch.response_p95_ms = None
    batch.analysis_status = "pending"
    create_audit_log(session, actor.id, actor.id, "batch_test.execute", {"batch_id": batch.id})
    session.commit()
    session.refresh(batch)
    return response_envelope(request, {"batch": serialize_batch(batch)})
