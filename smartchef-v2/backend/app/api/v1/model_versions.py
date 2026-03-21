"""Model version lifecycle routes (dd-intent-library.md §6.2)."""

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Body, Depends, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_response import BusinessException, success_response
from app.core.config import get_settings, resolve_artifact_path
from app.core.database import get_db
from app.core.security import get_current_user_from_token, require_capability
from app.schemas.intent_library import CreateModelRequest, StartEvaluationRequest, StartTrainingRequest
from app.services import model_version_service

router = APIRouter(tags=["model-versions"])


async def _run_training_background(model_version_id: UUID, db_url: str) -> None:
    """D039: 延迟 import trainer，避免在请求线程内加载 torch（可阻塞 >15s 触发 axios 超时）。"""
    from app.services.training.trainer import execute_training

    await execute_training(model_version_id, db_url)


async def _run_evaluation_background(run_id: UUID) -> None:
    from app.services.training.evaluator import execute_batch_evaluation

    settings = get_settings()
    await execute_batch_evaluation(run_id, settings.DATABASE_URL)


@router.get("/intent-libraries/{library_id}/models")
async def list_model_versions(
    request: Request,
    library_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await get_current_user_from_token(request)
    data = await model_version_service.list_model_versions(db, library_id)
    return success_response(data)


@router.post("/intent-libraries/{library_id}/models")
@require_capability("intent_library_write")
async def create_model_version(
    request: Request,
    library_id: UUID,
    body: CreateModelRequest,
    db: AsyncSession = Depends(get_db),
):
    user = request.state.current_user
    data = await model_version_service.create_model_version(db, library_id, body, user.user_id)
    return success_response(data, status_code=201)


@router.post("/models/{model_id}/train")
@require_capability("intent_library_write")
async def start_training(
    request: Request,
    model_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    body: StartTrainingRequest | None = Body(default=None),
):
    data = await model_version_service.start_training(db, model_id, body)
    # 必须先提交事务，再调度后台任务：否则 BackgroundTasks 可能在 get_db commit 之前读库，
    # 仍看到 draft，且可能与未提交的 ORM 状态竞态（表现为状态一直不更新）。
    await db.commit()
    settings = get_settings()
    background_tasks.add_task(_run_training_background, model_id, settings.DATABASE_URL)
    return success_response(data)


@router.post("/models/{model_id}/evaluate")
@require_capability("intent_library_write")
async def start_evaluation(
    request: Request,
    model_id: UUID,
    body: StartEvaluationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    user = request.state.current_user
    data = await model_version_service.start_evaluation(db, model_id, body, user.user_id)
    await db.commit()
    background_tasks.add_task(_run_evaluation_background, UUID(data["id"]))
    return success_response(data, status_code=201)


@router.post("/models/{model_id}/set-testable")
@require_capability("intent_library_write")
async def set_testable(
    request: Request,
    model_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    data = await model_version_service.set_testable(db, model_id)
    return success_response(data)


@router.post("/models/{model_id}/publish")
@require_capability("model_publish")
async def publish_model(
    request: Request,
    model_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    user = request.state.current_user
    data = await model_version_service.publish_model(db, model_id, user.user_id)
    return success_response(data)


@router.post("/models/{model_id}/archive")
@require_capability("intent_library_write")
async def archive_model(
    request: Request,
    model_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    data = await model_version_service.archive_model(db, model_id)
    return success_response(data)


@router.post("/models/{model_id}/restore")
@require_capability("intent_library_write")
async def restore_model(
    request: Request,
    model_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    data = await model_version_service.restore_model(db, model_id)
    return success_response(data)


@router.get("/models/{model_id}")
async def get_model_version(
    request: Request,
    model_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await get_current_user_from_token(request)
    data = await model_version_service.get_model_version(db, model_id)
    return success_response(data)


@router.get("/models/{model_id}/download")
async def download_model(
    request: Request,
    model_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """返回训练打包后的 zip 文件（D039：非 JSON，便于前端 Blob 下载）。"""
    await get_current_user_from_token(request)
    data = await model_version_service.get_model_version(db, model_id)
    pkg = data.get("package_uri")
    if not pkg:
        raise BusinessException("E50204", "模型包不可用，请先完成训练", http_status=404)
    abs_path = resolve_artifact_path(pkg)
    if not abs_path or not Path(abs_path).is_file():
        raise BusinessException("E50204", "模型文件不存在", http_status=404)
    filename = Path(abs_path).name
    return FileResponse(
        path=abs_path,
        filename=filename,
        media_type="application/zip",
    )


@router.get("/evaluation-runs/{run_id}")
async def get_evaluation_run(
    request: Request,
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await get_current_user_from_token(request)
    from app.models.evaluation import EvaluationRun
    run = await db.get(EvaluationRun, run_id)
    if not run:
        from app.core.api_response import BusinessException
        raise BusinessException("E50601", "评测运行不存在")
    return success_response({
        "id": str(run.id),
        "status": run.status,
        "result_summary": run.result_summary,
        "total_samples": run.total_samples,
        "completed_samples": run.completed_samples,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
    })
