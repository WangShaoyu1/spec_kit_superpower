"""Dialog Profile CRUD service."""

from uuid import UUID

from sqlalchemy import func, inspect as sa_inspect, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.api_response import BusinessException
from app.models.dialog_profile import (
    DialogProfile, ProfileLibraryBinding, PublishedVersion,
)
from app.schemas.profile import CreateProfileRequest, UpdateProfileRequest


async def list_profiles(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    status: str | None = None,
) -> tuple[list[dict], int]:
    query = select(DialogProfile)
    count_query = select(func.count()).select_from(DialogProfile)

    if search:
        pattern = f"%{search}%"
        query = query.where(DialogProfile.name.ilike(pattern))
        count_query = count_query.where(DialogProfile.name.ilike(pattern))

    if status:
        query = query.where(DialogProfile.status == status)
        count_query = count_query.where(DialogProfile.status == status)

    total = (await db.execute(count_query)).scalar() or 0
    query = (
        query.options(selectinload(DialogProfile.library_bindings))
        .order_by(DialogProfile.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await db.execute(query)).scalars().all()

    items = []
    for p in rows:
        latest_ver_q = (
            select(PublishedVersion.version_number)
            .where(PublishedVersion.profile_id == p.id)
            .order_by(PublishedVersion.published_at.desc())
            .limit(1)
        )
        latest_version = (await db.execute(latest_ver_q)).scalar()

        ver_count_q = (
            select(func.count())
            .select_from(PublishedVersion)
            .where(PublishedVersion.profile_id == p.id)
        )
        version_count = (await db.execute(ver_count_q)).scalar() or 0

        items.append(
            _to_dict(p, latest_version=latest_version, version_count=version_count)
        )

    return items, total


async def create_profile(db: AsyncSession, data: CreateProfileRequest, user_id: str) -> dict:
    profile = DialogProfile(
        name=data.name,
        description=data.description,
        command_threshold=data.command_threshold,
        route_strategy=data.route_strategy,
        llm_provider=data.llm_provider,
        llm_model=data.llm_model,
        session_timeout_min=data.session_timeout_min,
        created_by=user_id,
    )
    db.add(profile)
    await db.flush()
    return _to_dict(profile)


async def get_profile(db: AsyncSession, profile_id: UUID) -> dict:
    profile = await db.get(
        DialogProfile, profile_id,
        options=[selectinload(DialogProfile.library_bindings)],
    )
    if not profile:
        raise BusinessException("E40101", "对话方案不存在")

    latest_ver_q = (
        select(PublishedVersion.version_number)
        .where(PublishedVersion.profile_id == profile.id)
        .order_by(PublishedVersion.published_at.desc())
        .limit(1)
    )
    latest_version = (await db.execute(latest_ver_q)).scalar()

    return _to_dict(profile, latest_version=latest_version)


async def update_profile(db: AsyncSession, profile_id: UUID, data: UpdateProfileRequest) -> dict:
    profile = await db.get(DialogProfile, profile_id)
    if not profile:
        raise BusinessException("E40101", "对话方案不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        setattr(profile, key, val)

    await db.flush()
    await db.refresh(profile)
    return _to_dict(profile)


async def delete_profile(db: AsyncSession, profile_id: UUID) -> None:
    profile = await db.get(DialogProfile, profile_id)
    if not profile:
        raise BusinessException("E40101", "对话方案不存在")

    active_ver = (
        await db.execute(
            select(func.count())
            .select_from(PublishedVersion)
            .where(PublishedVersion.profile_id == profile_id)
            .where(PublishedVersion.status == "active")
        )
    ).scalar() or 0

    if active_ver > 0:
        raise BusinessException("E40102", "存在活跃发布版本，无法删除")

    await db.delete(profile)
    await db.flush()


async def get_stats(db: AsyncSession) -> dict:
    total = (await db.execute(select(func.count()).select_from(DialogProfile))).scalar() or 0
    draft = (
        await db.execute(
            select(func.count()).select_from(DialogProfile).where(DialogProfile.status == "draft")
        )
    ).scalar() or 0
    active = (
        await db.execute(
            select(func.count()).select_from(DialogProfile).where(DialogProfile.status == "active")
        )
    ).scalar() or 0
    versions = (
        await db.execute(select(func.count()).select_from(PublishedVersion))
    ).scalar() or 0

    return {"total": total, "draft": draft, "active": active, "published_versions": versions}


def _to_dict(
    p: DialogProfile,
    *,
    latest_version: str | None = None,
    version_count: int | None = None,
) -> dict:
    state = sa_inspect(p)
    if "library_bindings" in state.unloaded:
        bindings_count = 0
    else:
        bindings_count = len(p.library_bindings) if p.library_bindings else 0
    return {
        "id": str(p.id),
        "name": p.name,
        "description": p.description,
        "status": p.status,
        "command_threshold": p.command_threshold,
        "route_strategy": p.route_strategy,
        "llm_provider": p.llm_provider,
        "llm_model": p.llm_model,
        "session_timeout_min": p.session_timeout_min,
        "created_by": str(p.created_by) if p.created_by else None,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        "bindings_count": bindings_count,
        "latest_version": latest_version,
        "version_count": version_count,
    }
