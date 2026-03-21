"""IntentLibrary CRUD service (dd-intent-library.md §4.1)."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_response import BusinessException
from app.models.dataset import TrainingDataset
from app.models.intent_library import IntentLibrary
from app.models.model_version import LibraryModelVersion
from app.schemas.intent_library import CreateLibraryRequest, UpdateLibraryRequest

# DD §4.1：语言仅支持 zh (中文) 或 en (英文)，全项目统一
SUPPORTED_LANGUAGES = {"zh", "en"}
# 入参为 locale 时在存储前归一化为 zh/en
LOCALE_TO_LANG = {"zh-CN": "zh", "zh-TW": "zh", "zh-HK": "zh", "en-US": "en", "en-GB": "en"}


async def _library_intent_count(db: AsyncSession, library_id: UUID) -> int:
    q = select(func.coalesce(func.sum(TrainingDataset.intent_count), 0)).where(
        TrainingDataset.library_id == library_id,
    )
    return int((await db.execute(q)).scalar() or 0)


def _normalize_language(lang: str) -> str:
    """将 locale 归一化为 zh/en，不接受其他值。"""
    n = LOCALE_TO_LANG.get(lang, lang)
    if n not in SUPPORTED_LANGUAGES:
        raise BusinessException("E50103", f"不支持的语言: {lang}")
    return n


async def list_libraries(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    language: str | None = None,
) -> tuple[list[dict], int, int, int]:
    """返回 (items, total, total_zh, total_en)。D021: total_zh/total_en 与 total 同条件统计。"""
    query = select(IntentLibrary)
    count_query = select(func.count()).select_from(IntentLibrary)

    if search:
        pattern = f"%{search}%"
        query = query.where(
            IntentLibrary.name.ilike(pattern) | IntentLibrary.library_key.ilike(pattern)
        )
        count_query = count_query.where(
            IntentLibrary.name.ilike(pattern) | IntentLibrary.library_key.ilike(pattern)
        )

    if language:
        norm = _normalize_language(language)
        query = query.where(IntentLibrary.language == norm)
        count_query = count_query.where(IntentLibrary.language == norm)

    total = (await db.execute(count_query)).scalar() or 0

    # D021: 同条件下的 zh/en 全局统计，供概览卡片使用
    if language:
        norm_lang = _normalize_language(language)
        total_zh = total if norm_lang == "zh" else 0
        total_en = total if norm_lang == "en" else 0
    else:
        zh_count_q = select(func.count()).select_from(IntentLibrary).where(IntentLibrary.language == "zh")
        en_count_q = select(func.count()).select_from(IntentLibrary).where(IntentLibrary.language == "en")
        if search:
            pattern = f"%{search}%"
            zh_count_q = zh_count_q.where(
                IntentLibrary.name.ilike(pattern) | IntentLibrary.library_key.ilike(pattern)
            )
            en_count_q = en_count_q.where(
                IntentLibrary.name.ilike(pattern) | IntentLibrary.library_key.ilike(pattern)
            )
        total_zh = (await db.execute(zh_count_q)).scalar() or 0
        total_en = (await db.execute(en_count_q)).scalar() or 0

    query = query.order_by(IntentLibrary.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(query)).scalars().all()

    items = []
    for lib in rows:
        model_count_q = (
            select(func.count())
            .select_from(LibraryModelVersion)
            .where(LibraryModelVersion.library_id == lib.id)
            .where(LibraryModelVersion.status != "archived")
        )
        model_count = (await db.execute(model_count_q)).scalar() or 0

        latest_q = (
            select(LibraryModelVersion.status)
            .where(LibraryModelVersion.library_id == lib.id)
            .order_by(LibraryModelVersion.created_at.desc())
            .limit(1)
        )
        latest_status = (await db.execute(latest_q)).scalar()
        intent_count = await _library_intent_count(db, lib.id)

        items.append(
            _to_dict(
                lib,
                model_count=model_count,
                latest_model_status=latest_status,
                intent_count=intent_count,
            ),
        )

    return items, total, total_zh, total_en


async def create_library(db: AsyncSession, data: CreateLibraryRequest, user_id: str) -> dict:
    existing = await db.execute(
        select(IntentLibrary).where(IntentLibrary.library_key == data.library_key)
    )
    if existing.scalar():
        raise BusinessException("E50101", f"意图库 key '{data.library_key}' 已存在")

    lang = _normalize_language(data.language)

    lib = IntentLibrary(
        library_key=data.library_key,
        name=data.name,
        language=lang,
        description=data.description,
        default_confidence_threshold=data.default_confidence_threshold,
        default_intent_f1_threshold=data.default_intent_f1_threshold,
        default_slot_f1_threshold=data.default_slot_f1_threshold,
        created_by=user_id,
    )
    db.add(lib)
    await db.flush()
    return _to_dict(lib)


async def get_library(db: AsyncSession, library_id: UUID) -> dict:
    lib = await db.get(IntentLibrary, library_id)
    if not lib:
        raise BusinessException("E50102", "意图库不存在")

    model_count_q = (
        select(func.count())
        .select_from(LibraryModelVersion)
        .where(LibraryModelVersion.library_id == lib.id)
        .where(LibraryModelVersion.status != "archived")
    )
    model_count = (await db.execute(model_count_q)).scalar() or 0

    latest_q = (
        select(LibraryModelVersion.status)
        .where(LibraryModelVersion.library_id == lib.id)
        .order_by(LibraryModelVersion.created_at.desc())
        .limit(1)
    )
    latest_status = (await db.execute(latest_q)).scalar()
    intent_count = await _library_intent_count(db, lib.id)

    return _to_dict(
        lib,
        model_count=model_count,
        latest_model_status=latest_status,
        intent_count=intent_count,
    )


async def update_library(db: AsyncSession, library_id: UUID, data: UpdateLibraryRequest) -> dict:
    lib = await db.get(IntentLibrary, library_id)
    if not lib:
        raise BusinessException("E50102", "意图库不存在")

    update_data = data.model_dump(exclude_unset=True)
    # D022: language 需归一化（与 create 一致，支持 zh-CN -> zh 等）
    if "language" in update_data:
        update_data["language"] = _normalize_language(update_data["language"])
    for key, val in update_data.items():
        setattr(lib, key, val)

    await db.flush()
    await db.refresh(lib)
    return _to_dict(lib)


async def delete_library(db: AsyncSession, library_id: UUID) -> None:
    lib = await db.get(IntentLibrary, library_id)
    if not lib:
        raise BusinessException("E50102", "意图库不存在")

    non_archived = (
        await db.execute(
            select(func.count())
            .select_from(LibraryModelVersion)
            .where(LibraryModelVersion.library_id == library_id)
            .where(LibraryModelVersion.status != "archived")
        )
    ).scalar() or 0

    if non_archived > 0:
        raise BusinessException("E50120", "存在未归档的模型版本，无法删除意图库")

    await db.delete(lib)
    await db.flush()


def _to_dict(
    lib: IntentLibrary,
    *,
    model_count: int | None = None,
    latest_model_status: str | None = None,
    intent_count: int | None = None,
) -> dict:
    return {
        "id": str(lib.id),
        "library_key": lib.library_key,
        "name": lib.name,
        "language": lib.language,
        "description": lib.description,
        "default_confidence_threshold": lib.default_confidence_threshold,
        "default_intent_f1_threshold": lib.default_intent_f1_threshold,
        "default_slot_f1_threshold": lib.default_slot_f1_threshold,
        "created_by": str(lib.created_by) if lib.created_by else None,
        "created_at": lib.created_at.isoformat() if lib.created_at else None,
        "updated_at": lib.updated_at.isoformat() if lib.updated_at else None,
        "model_count": model_count,
        "latest_model_status": latest_model_status,
        "intent_count": intent_count,
    }
