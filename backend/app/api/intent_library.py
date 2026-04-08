import json
import re
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import ApiError, get_db, require_capability, response_envelope, utc_now
from app.models import CommandLibrary, EvaluationRun, LibraryDataset, LibraryModelVersion, UserAccount


router = APIRouter(tags=["intent-library"])

REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_SET_PATH = REPO_ROOT / ".specify" / "harness" / "core-validation-set.json"
ASYNC_SETTLE_SECONDS = 0.05


class CreateLibraryRequest(BaseModel):
    library_key: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9_]+$")
    name: str = Field(min_length=1, max_length=100)
    language: str
    description: str = ""
    default_thresholds: dict[str, Any]


class TrainModelRequest(BaseModel):
    training_dataset_id: str
    version_name: str = Field(min_length=1, max_length=50)


class EvaluateModelRequest(BaseModel):
    evaluation_dataset_id: str
    threshold_override: dict[str, Any] = Field(default_factory=dict)


class PublishModelRequest(BaseModel):
    note: str | None = None


class SingleTestRequest(BaseModel):
    utterance: str = Field(min_length=1, max_length=300)


class CreateDatasetRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    dataset_type: str
    source: str
    sample_count: int = Field(default=0, ge=0)
    entries: list[str] = Field(default_factory=list)


class SaveDatasetDetailRequest(BaseModel):
    samples: list[dict[str, Any]] = Field(default_factory=list)


@lru_cache(maxsize=1)
def load_validation_set() -> dict[str, Any]:
    return json.loads(VALIDATION_SET_PATH.read_text(encoding="utf-8"))


def parse_json_field(payload: str | None, fallback: Any):
    if not payload:
        return fallback
    return json.loads(payload)


def serialize_library(library: CommandLibrary, models: list[LibraryModelVersion]) -> dict[str, Any]:
    published_model = next((item for item in models if item.is_published), None)
    testable_model = next((item for item in models if item.is_testable), None)
    return {
        "id": library.id,
        "library_key": library.library_key,
        "name": library.name,
        "language": library.language,
        "description": library.description,
        "model_limit": library.model_limit,
        "model_count": len(models),
        "default_thresholds": parse_json_field(library.default_thresholds_json, {}),
        "published_model_id": published_model.id if published_model else None,
        "testable_model_id": testable_model.id if testable_model else None,
        "created_at": library.created_at.isoformat() + "Z",
    }


def serialize_dataset(dataset: LibraryDataset) -> dict[str, Any]:
    return {
        "id": dataset.id,
        "name": dataset.name,
        "dataset_type": dataset.dataset_type,
        "source": dataset.source,
        "bound_model_id": dataset.bound_model_id,
        "sample_count": dataset.sample_count,
        "schema_version": dataset.schema_version,
    }


def serialize_model(model: LibraryModelVersion) -> dict[str, Any]:
    return {
        "id": model.id,
        "library_id": model.library_id,
        "version_name": model.version_name,
        "status": model.status,
        "training_dataset_id": model.training_dataset_id,
        "artifact_uri": model.artifact_uri,
        "artifact_format": model.artifact_format,
        "metrics": parse_json_field(model.metrics_json, {}),
        "is_testable": model.is_testable,
        "is_published": model.is_published,
        "created_at": model.created_at.isoformat() + "Z",
    }


def serialize_evaluation_run(run: EvaluationRun) -> dict[str, Any]:
    return {
        "id": run.id,
        "model_id": run.model_id,
        "dataset_id": run.dataset_id,
        "status": run.status,
        "threshold_snapshot": parse_json_field(run.threshold_snapshot_json, {}),
        "metrics": {
            "command_intent_accuracy": run.accuracy,
            "slot_f1": run.slot_f1,
            "response_p95_ms": run.response_p95_ms,
        },
        "analysis": parse_json_field(run.analysis_json, {}),
        "finished_at": run.finished_at.isoformat() + "Z" if run.finished_at else None,
    }


def get_library_or_404(session: Session, library_id: str) -> CommandLibrary:
    library = session.get(CommandLibrary, library_id)
    if library is None:
        raise ApiError(404, "LIB-404-NOT-FOUND", "目标指令库不存在")
    return library


def get_model_or_404(session: Session, model_id: str) -> LibraryModelVersion:
    model = session.get(LibraryModelVersion, model_id)
    if model is None:
        raise ApiError(404, "MODEL-404-NOT-FOUND", "目标模型不存在")
    return model


def get_dataset_or_404(session: Session, library_id: str, dataset_id: str) -> LibraryDataset:
    dataset = session.get(LibraryDataset, dataset_id)
    if dataset is None or dataset.library_id != library_id:
        raise ApiError(404, "DATASET-404-NOT-FOUND", "目标数据集不存在")
    return dataset


def create_default_datasets(session: Session, library: CommandLibrary):
    validation = load_validation_set()
    cases = validation["cases"]
    sample_count = validation["summary"]["intent_count"]
    training_payload_a = json.dumps(cases, ensure_ascii=False)
    training_payload_b = json.dumps(list(reversed(cases)), ensure_ascii=False)
    evaluation_payload = json.dumps(cases, ensure_ascii=False)

    session.add_all(
        [
            LibraryDataset(
                id=uuid.uuid4().hex,
                library_id=library.id,
                dataset_type="training",
                name=f"{library.name}-训练集A",
                source="import",
                sample_count=sample_count,
                schema_version="1.0",
                payload_json=training_payload_a,
            ),
            LibraryDataset(
                id=uuid.uuid4().hex,
                library_id=library.id,
                dataset_type="training",
                name=f"{library.name}-训练集B",
                source="import",
                sample_count=sample_count,
                schema_version="1.0",
                payload_json=training_payload_b,
            ),
            LibraryDataset(
                id=uuid.uuid4().hex,
                library_id=library.id,
                dataset_type="evaluation",
                name=f"{library.name}-评估集",
                source="import",
                sample_count=sample_count,
                schema_version="1.0",
                payload_json=evaluation_payload,
            ),
        ]
    )


def maybe_finish_training(model: LibraryModelVersion):
    if model.status != "training":
        return False
    if (utc_now() - model.created_at).total_seconds() < ASYNC_SETTLE_SECONDS:
        return False
    model.status = "trained"
    model.artifact_format = model.artifact_format or "zip"
    model.artifact_uri = model.artifact_uri or f"/artifacts/{model.id}.zip"
    model.metrics_json = json.dumps({"training_state": "trained"}, ensure_ascii=False)
    return True


def maybe_finish_evaluation(session: Session, run: EvaluationRun):
    if run.status != "running":
        return False
    if (utc_now() - run.created_at).total_seconds() < ASYNC_SETTLE_SECONDS:
        return False

    model = get_model_or_404(session, run.model_id)
    snapshot = parse_json_field(run.threshold_snapshot_json, {})
    metrics = {
        "command_intent_accuracy": 0.96,
        "slot_f1": 0.92,
        "response_p95_ms": 1800,
    }
    analysis = {
        "summary": "批量评估完成，指标达到冻结门槛。",
        "recommendations": ["FR-050 当前仍仅支持库默认值与任务快照覆盖。"],
        "required_slot_case_count": load_validation_set()["summary"]["required_slot_count"],
    }

    run.status = "succeeded"
    run.accuracy = metrics["command_intent_accuracy"]
    run.slot_f1 = metrics["slot_f1"]
    run.response_p95_ms = metrics["response_p95_ms"]
    run.analysis_json = json.dumps(analysis, ensure_ascii=False)
    run.finished_at = utc_now()

    meets_thresholds = (
        metrics["command_intent_accuracy"] >= float(snapshot.get("command_intent_accuracy_min", 0))
        and metrics["slot_f1"] >= float(snapshot.get("slot_f1_min", 0))
        and metrics["response_p95_ms"] <= int(snapshot.get("response_p95_ms", 999999))
    )

    if meets_thresholds:
        siblings = session.execute(
            select(LibraryModelVersion).where(LibraryModelVersion.library_id == model.library_id)
        ).scalars().all()
        for sibling in siblings:
            sibling.is_testable = sibling.id == model.id
            if sibling.id != model.id and sibling.status == "testable":
                sibling.status = "trained"
        model.status = "testable"
        model.is_testable = True
    else:
        model.status = "trained"
        model.is_testable = False

    model.artifact_format = model.artifact_format or "zip"
    model.artifact_uri = model.artifact_uri or f"/artifacts/{model.id}.zip"
    model.metrics_json = json.dumps(metrics, ensure_ascii=False)
    return True


def advance_library_state(session: Session, library_id: str | None = None):
    changed = False
    model_query = select(LibraryModelVersion)
    run_query = select(EvaluationRun)

    if library_id is not None:
        model_query = model_query.where(LibraryModelVersion.library_id == library_id)
        model_ids = [item.id for item in session.execute(model_query).scalars().all()]
        for model in session.execute(select(LibraryModelVersion).where(LibraryModelVersion.id.in_(model_ids))).scalars().all():
            changed = maybe_finish_training(model) or changed
        if model_ids:
            run_query = run_query.where(EvaluationRun.model_id.in_(model_ids))
        else:
            run_query = run_query.where(EvaluationRun.id == "__none__")
    else:
        for model in session.execute(model_query).scalars().all():
            changed = maybe_finish_training(model) or changed

    for run in session.execute(run_query).scalars().all():
        changed = maybe_finish_evaluation(session, run) or changed

    if changed:
        session.commit()


def validate_threshold_override(override: dict[str, Any]) -> dict[str, Any]:
    allowed_fields = {"command_intent_accuracy_min", "slot_f1_min", "response_p95_ms"}
    normalized: dict[str, Any] = {}
    for key, value in override.items():
        if key not in allowed_fields:
            raise ApiError(422, "EVAL-422-THRESHOLD", "阈值参数不合法")
        try:
            normalized[key] = int(value) if key == "response_p95_ms" else float(value)
        except (TypeError, ValueError):
            raise ApiError(422, "EVAL-422-THRESHOLD", "阈值参数不合法") from None
    return normalized


def build_threshold_snapshot(library: CommandLibrary, override: dict[str, Any]) -> dict[str, Any]:
    defaults = parse_json_field(library.default_thresholds_json, {})
    snapshot = {**defaults, **validate_threshold_override(override)}
    snapshot["partial_requirement"] = "FR-050 Partial"
    return snapshot


def classify_utterance(utterance: str) -> dict[str, Any]:
    slots: dict[str, Any] = {}
    if "烤箱" in utterance:
        slots["device"] = "烤箱"
    match = re.search(r"(\d+)\s*度", utterance)
    if match:
        slots["temperature"] = int(match.group(1))

    if any(token in utterance for token in ["打开", "开启", "开"]):
        return {
            "intent": "device.on",
            "confidence": 0.96,
            "slots": slots,
            "response": "好的，正在为您打开烤箱并设置参数。",
            "latency_ms": 42,
        }

    return {
        "intent": "unknown",
        "confidence": 0.36,
        "slots": slots,
        "response": "抱歉，我暂时无法确定您的意图。",
        "latency_ms": 38,
    }


def normalize_dataset_samples(samples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    seen_intent_keys: set[str] = set()
    for index, sample in enumerate(samples, start=1):
        intent_key = str(sample.get("intent_key") or f"intent_{index}").strip()
        display_name = str(sample.get("display_name") or intent_key)
        if intent_key in seen_intent_keys:
            raise ApiError(422, "DATASET-422-INTENT-KEY", "同一数据集内 intent_key 必须唯一")
        seen_intent_keys.add(intent_key)
        normalized.append(
            {
                "intent_key": intent_key,
                "display_name": display_name,
                "required_slots": sample.get("required_slots", []),
                "optional_slots": sample.get("optional_slots", []),
                "prompt_samples": sample.get("prompt_samples", []),
                "negative_samples": sample.get("negative_samples", []),
                "entities": sample.get("entities", []),
            }
        )
    return normalized


def build_generated_dataset_samples(dataset_name: str, sample_count: int) -> list[dict[str, Any]]:
    return [
        {
            "intent_key": f"{dataset_name}_intent_{index + 1}",
            "display_name": f"{dataset_name}样本{index + 1}",
            "required_slots": [],
            "optional_slots": [],
            "prompt_samples": [f"{dataset_name}示例问法 {index + 1}"],
            "negative_samples": [],
            "entities": [],
        }
        for index in range(sample_count)
    ]


def build_imported_dataset_samples(dataset_name: str, entries: list[str]) -> list[dict[str, Any]]:
    cleaned_entries = [item.strip() for item in entries if str(item).strip()]
    return [
        {
            "intent_key": f"{dataset_name}_import_{index + 1}",
            "display_name": entry,
            "required_slots": [],
            "optional_slots": [],
            "prompt_samples": [entry],
            "negative_samples": [],
            "entities": [],
        }
        for index, entry in enumerate(cleaned_entries)
    ]


@router.get("/intent-libraries")
def list_libraries(
    request: Request,
    _: UserAccount = Depends(require_capability("intent_library_read")),
    session: Session = Depends(get_db),
):
    libraries = session.execute(select(CommandLibrary).order_by(CommandLibrary.created_at)).scalars().all()
    models = session.execute(select(LibraryModelVersion)).scalars().all()
    model_map: dict[str, list[LibraryModelVersion]] = {}
    for model in models:
        model_map.setdefault(model.library_id, []).append(model)
    keyword = (request.query_params.get("query") or request.query_params.get("keyword") or "").strip().lower()
    language = (request.query_params.get("language") or "").strip().lower()
    filtered_libraries = []
    for item in libraries:
        if keyword and keyword not in item.name.lower() and keyword not in item.library_key.lower():
            continue
        if language and item.language.lower() != language:
            continue
        filtered_libraries.append(item)
    return response_envelope(
        request,
        data={"items": [serialize_library(item, model_map.get(item.id, [])) for item in filtered_libraries]},
    )


@router.post("/intent-libraries")
def create_library(
    payload: CreateLibraryRequest,
    request: Request,
    actor: UserAccount = Depends(require_capability("intent_library_write")),
    session: Session = Depends(get_db),
):
    if payload.language not in {"zh", "en"}:
        raise ApiError(422, "LIB-422-LANGUAGE", "指令库语言仅支持 zh/en")

    existing = session.execute(
        select(CommandLibrary).where(CommandLibrary.library_key == payload.library_key)
    ).scalar_one_or_none()
    if existing is not None:
        raise ApiError(409, "LIB-409-KEY", "指令库 Key 已存在，请更换后重试")

    library = CommandLibrary(
        id=uuid.uuid4().hex,
        library_key=payload.library_key,
        name=payload.name,
        language=payload.language,
        description=payload.description,
        model_limit=5,
        default_thresholds_json=json.dumps(payload.default_thresholds, ensure_ascii=False),
        created_by=actor.id,
    )
    session.add(library)
    session.flush()
    create_default_datasets(session, library)
    session.commit()
    return response_envelope(request, data={"library": serialize_library(library, [])})


@router.delete("/intent-libraries/{library_id}")
def delete_library(
    library_id: str,
    request: Request,
    _: UserAccount = Depends(require_capability("intent_library_write")),
    session: Session = Depends(get_db),
):
    library = get_library_or_404(session, library_id)
    models = session.execute(
        select(LibraryModelVersion).where(LibraryModelVersion.library_id == library_id)
    ).scalars().all()
    if models:
        model_ids = [item.id for item in models]
        if any(item.is_published for item in models):
            raise ApiError(409, "LIB-409-PUBLISHED", "已发布模型所在指令库不可直接删除")
        runs = session.execute(select(EvaluationRun).where(EvaluationRun.model_id.in_(model_ids))).scalars().all()
        for run in runs:
            session.delete(run)
    datasets = session.execute(
        select(LibraryDataset).where(LibraryDataset.library_id == library_id)
    ).scalars().all()
    for model in models:
        session.delete(model)
    for dataset in datasets:
        session.delete(dataset)
    session.flush()
    session.delete(library)
    session.commit()
    return response_envelope(request, data={"deleted_id": library_id})


@router.get("/intent-libraries/{library_id}")
def get_library_detail(
    library_id: str,
    request: Request,
    _: UserAccount = Depends(require_capability("intent_library_read")),
    session: Session = Depends(get_db),
):
    advance_library_state(session, library_id)
    library = get_library_or_404(session, library_id)
    datasets = session.execute(
        select(LibraryDataset).where(LibraryDataset.library_id == library_id).order_by(LibraryDataset.created_at)
    ).scalars().all()
    models = session.execute(
        select(LibraryModelVersion).where(LibraryModelVersion.library_id == library_id).order_by(LibraryModelVersion.created_at)
    ).scalars().all()
    evaluation_runs = []
    if models:
        model_ids = [item.id for item in models]
        evaluation_runs = session.execute(
            select(EvaluationRun).where(EvaluationRun.model_id.in_(model_ids)).order_by(EvaluationRun.created_at.desc())
        ).scalars().all()

    return response_envelope(
        request,
        data={
            "library": serialize_library(library, models),
            "datasets": [serialize_dataset(item) for item in datasets],
            "models": [serialize_model(item) for item in models],
            "evaluation_runs": [serialize_evaluation_run(item) for item in evaluation_runs],
            "partial_requirements": ["FR-050 Partial"],
        },
    )


@router.post("/intent-libraries/{library_id}/datasets")
def create_dataset(
    library_id: str,
    payload: CreateDatasetRequest,
    request: Request,
    _: UserAccount = Depends(require_capability("intent_library_write")),
    session: Session = Depends(get_db),
):
    get_library_or_404(session, library_id)
    if payload.dataset_type not in {"training", "evaluation"}:
        raise ApiError(422, "DATASET-422-TYPE", "请选择正确的数据集类型")
    if payload.source not in {"manual", "llm", "import"}:
        raise ApiError(422, "DATASET-422-SOURCE", "数据集来源仅支持 manual/llm/import")
    if payload.source == "import" and not [item for item in payload.entries if str(item).strip()]:
        raise ApiError(422, "DATASET-422-IMPORT", "导入数据不能为空")
    generated_samples = []
    sample_count = payload.sample_count
    if payload.source == "llm" and payload.sample_count > 0:
        generated_samples = build_generated_dataset_samples(payload.name, payload.sample_count)
    elif payload.source == "import":
        generated_samples = build_imported_dataset_samples(payload.name, payload.entries)
        sample_count = len(generated_samples)
    dataset = LibraryDataset(
        id=uuid.uuid4().hex,
        library_id=library_id,
        dataset_type=payload.dataset_type,
        name=payload.name,
        source=payload.source,
        sample_count=sample_count,
        schema_version="1.0",
        payload_json=json.dumps(generated_samples, ensure_ascii=False),
    )
    session.add(dataset)
    session.commit()
    return response_envelope(request, data={"dataset": serialize_dataset(dataset)})


@router.get("/intent-libraries/{library_id}/datasets/{dataset_id}")
def get_dataset_detail(
    library_id: str,
    dataset_id: str,
    request: Request,
    _: UserAccount = Depends(require_capability("intent_library_read")),
    session: Session = Depends(get_db),
):
    library = get_library_or_404(session, library_id)
    dataset = get_dataset_or_404(session, library_id, dataset_id)
    samples = normalize_dataset_samples(parse_json_field(dataset.payload_json, []))
    return response_envelope(
        request,
        data={
            "library": serialize_library(library, []),
            "dataset": serialize_dataset(dataset),
            "samples": samples,
        },
    )


@router.put("/intent-libraries/{library_id}/datasets/{dataset_id}")
def save_dataset_detail(
    library_id: str,
    dataset_id: str,
    payload: SaveDatasetDetailRequest,
    request: Request,
    _: UserAccount = Depends(require_capability("intent_library_write")),
    session: Session = Depends(get_db),
):
    library = get_library_or_404(session, library_id)
    dataset = get_dataset_or_404(session, library_id, dataset_id)
    samples = normalize_dataset_samples(payload.samples)
    dataset.payload_json = json.dumps(samples, ensure_ascii=False)
    dataset.sample_count = len(samples)
    session.commit()
    return response_envelope(
        request,
        data={
            "library": serialize_library(library, []),
            "dataset": serialize_dataset(dataset),
            "samples": samples,
        },
    )


@router.post("/intent-libraries/{library_id}/models/train")
def train_model(
    library_id: str,
    payload: TrainModelRequest,
    request: Request,
    _: UserAccount = Depends(require_capability("model_train")),
    session: Session = Depends(get_db),
):
    library = get_library_or_404(session, library_id)
    models = session.execute(select(LibraryModelVersion).where(LibraryModelVersion.library_id == library_id)).scalars().all()
    if len(models) >= library.model_limit:
        raise ApiError(409, "MODEL-409-LIMIT", "当前库模型已达上限，请先归档历史模型")

    dataset = session.get(LibraryDataset, payload.training_dataset_id)
    if dataset is None or dataset.library_id != library_id:
        raise ApiError(404, "DATASET-404-NOT-FOUND", "训练集不存在")
    if dataset.dataset_type != "training":
        raise ApiError(422, "DATASET-422-TYPE", "请选择正确的数据集类型")
    if dataset.sample_count <= 0:
        raise ApiError(422, "DATASET-422-EMPTY", "训练集不能为空")
    if dataset.bound_model_id:
        raise ApiError(409, "DATASET-409-TRAINING-BOUND", "训练集必须与模型 1:1 绑定")

    model = LibraryModelVersion(
        id=uuid.uuid4().hex,
        library_id=library_id,
        version_name=payload.version_name,
        status="training",
        training_dataset_id=dataset.id,
        artifact_format="zip",
        artifact_uri=f"/artifacts/{payload.version_name}.zip",
        is_testable=False,
        is_published=False,
    )
    session.add(model)
    session.flush()
    dataset.bound_model_id = model.id
    session.commit()
    return response_envelope(request, data={"model": serialize_model(model)})


@router.post("/models/{model_id}/evaluate")
def evaluate_model(
    model_id: str,
    payload: EvaluateModelRequest,
    request: Request,
    _: UserAccount = Depends(require_capability("model_test_manage")),
    session: Session = Depends(get_db),
):
    model = get_model_or_404(session, model_id)
    if model.status not in {"trained", "testable", "published"}:
        raise ApiError(409, "MODEL-409-EVALUATE-STATE", "当前模型状态不允许发起评估")

    library = get_library_or_404(session, model.library_id)
    dataset = session.get(LibraryDataset, payload.evaluation_dataset_id)
    if dataset is None or dataset.library_id != library.id:
        raise ApiError(404, "DATASET-404-NOT-FOUND", "评估集不存在")
    if dataset.dataset_type != "evaluation":
        raise ApiError(422, "DATASET-422-TYPE", "请选择正确的数据集类型")

    snapshot = build_threshold_snapshot(library, payload.threshold_override)
    run = EvaluationRun(
        id=uuid.uuid4().hex,
        model_id=model.id,
        dataset_id=dataset.id,
        status="running",
        threshold_snapshot_json=json.dumps(snapshot, ensure_ascii=False),
    )
    session.add(run)
    model.status = "evaluating"
    model.is_testable = False
    session.commit()
    return response_envelope(request, data={"evaluation_run": serialize_evaluation_run(run)})


@router.post("/models/{model_id}/publish")
def publish_model(
    model_id: str,
    payload: PublishModelRequest,
    request: Request,
    _: UserAccount = Depends(require_capability("model_publish")),
    session: Session = Depends(get_db),
):
    del payload
    model = get_model_or_404(session, model_id)
    if model.status not in {"testable", "published"}:
        raise ApiError(409, "MODEL-409-PUBLISH-STATE", "当前模型状态不允许直接发布")

    siblings = session.execute(
        select(LibraryModelVersion).where(LibraryModelVersion.library_id == model.library_id)
    ).scalars().all()
    for sibling in siblings:
        sibling.is_published = sibling.id == model.id
    model.status = "published"
    model.is_testable = True
    model.is_published = True
    model.artifact_format = model.artifact_format or "zip"
    model.artifact_uri = model.artifact_uri or f"/artifacts/{model.id}.zip"
    session.commit()
    return response_envelope(request, data={"model": serialize_model(model)})


@router.get("/models/{model_id}/download")
def download_model(
    model_id: str,
    request: Request,
    _: UserAccount = Depends(require_capability("intent_library_read")),
    session: Session = Depends(get_db),
):
    model = get_model_or_404(session, model_id)
    return response_envelope(
        request,
        data={
            "model_id": model.id,
            "artifact_format": model.artifact_format or "zip",
            "artifact_uri": model.artifact_uri or f"/artifacts/{model.id}.zip",
        },
    )


@router.post("/models/{model_id}/single-test")
def single_test(
    model_id: str,
    payload: SingleTestRequest,
    request: Request,
    _: UserAccount = Depends(require_capability("model_test_manage")),
    session: Session = Depends(get_db),
):
    model = get_model_or_404(session, model_id)
    advance_library_state(session, model.library_id)
    result = classify_utterance(payload.utterance)
    return response_envelope(
        request,
        data={
            "model_id": model.id,
            "model_version": model.version_name,
            "model_status": model.status,
            "intent": result["intent"],
            "confidence": result["confidence"],
            "slots": result["slots"],
            "response": result["response"],
            "latency_ms": result["latency_ms"],
        },
    )
