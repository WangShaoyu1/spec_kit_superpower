from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.core.database import get_db
from app.core.redis import get_redis
from app.api.deps import require_permission
from app.models.published_version import PublishedVersion
from app.models.dialog_profile import DialogProfile
from app.services.session.device_session import clear_all_sessions

router = APIRouter(prefix="/versions", tags=["版本管理"])


@router.get("")
async def list_versions(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("version_publish.read")),
):
    result = await db.execute(select(PublishedVersion).order_by(PublishedVersion.created_at.desc()))
    versions = result.scalars().all()
    return [
        {
            "id": str(v.id), "version_tag": v.version_tag,
            "profile_id": str(v.profile_id), "description": v.description,
            "is_active": v.is_active, "created_at": v.created_at.isoformat(),
        }
        for v in versions
    ]


@router.post("", status_code=201)
async def publish_version(
    profile_id: UUID, version_tag: str, description: str | None = None,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    current_user=Depends(require_permission("version_publish.write")),
):
    result = await db.execute(select(DialogProfile).where(DialogProfile.id == profile_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="对话方案不存在")

    await db.execute(
        update(PublishedVersion).where(PublishedVersion.is_active == True).values(is_active=False)
    )

    version = PublishedVersion(
        profile_id=profile_id, version_tag=version_tag,
        description=description, is_active=True,
        published_by=current_user.id,
    )
    db.add(version)
    await db.flush()

    cleared = await clear_all_sessions(redis)

    return {
        "id": str(version.id), "version_tag": version_tag,
        "is_active": True, "sessions_cleared": cleared,
    }


@router.post("/{version_id}/activate")
async def activate_version(
    version_id: UUID,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    _=Depends(require_permission("version_publish.write")),
):
    result = await db.execute(select(PublishedVersion).where(PublishedVersion.id == version_id))
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")

    await db.execute(
        update(PublishedVersion).where(PublishedVersion.is_active == True).values(is_active=False)
    )
    version.is_active = True
    await db.flush()

    cleared = await clear_all_sessions(redis)

    return {"status": "ok", "version_tag": version.version_tag, "sessions_cleared": cleared}
