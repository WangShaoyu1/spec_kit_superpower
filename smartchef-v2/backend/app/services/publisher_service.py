"""Publish gate check + version snapshot creation (dd-dialog-profile.md §5)."""

import re
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.api_response import BusinessException
from app.models.dialog_profile import (
    DialogProfile, Persona, ProfileLibraryBinding, PublishedVersion,
)
from app.models.model_version import LibraryModelVersion


async def publish(db: AsyncSession, profile_id: UUID, user_id: str) -> dict:
    profile = await db.get(
        DialogProfile, profile_id,
        options=[
            selectinload(DialogProfile.personas),
            selectinload(DialogProfile.library_bindings),
        ],
    )
    if not profile:
        raise BusinessException("E40101", "对话方案不存在")

    bindings = profile.library_bindings or []
    if not bindings:
        raise BusinessException("E40301", "未绑定任何意图库，无法发布")

    missing = []
    for b in bindings:
        published_q = (
            select(func.count())
            .select_from(LibraryModelVersion)
            .where(
                LibraryModelVersion.library_id == b.library_id,
                LibraryModelVersion.is_published == True,  # noqa: E712
            )
        )
        count = (await db.execute(published_q)).scalar() or 0
        if count == 0:
            missing.append(str(b.library_id))

    if missing:
        raise BusinessException(
            "E40301",
            f"以下意图库尚未发布模型: {', '.join(missing)}",
        )

    version_number = await _next_version_number(db, profile_id)

    active_persona = next((p for p in (profile.personas or []) if p.is_active), None)
    snapshot = {
        "profile": {
            "name": profile.name,
            "command_threshold": profile.command_threshold,
            "route_strategy": profile.route_strategy,
            "llm_provider": profile.llm_provider,
            "llm_model": profile.llm_model,
            "session_timeout_min": profile.session_timeout_min,
        },
        "persona": {
            "name": active_persona.name,
            "system_prompt": active_persona.system_prompt,
            "temperature": active_persona.temperature,
            "max_tokens": active_persona.max_tokens,
        } if active_persona else None,
        "bindings": [
            {
                "library_id": str(b.library_id),
                "priority": b.priority,
                "confidence_threshold": b.confidence_threshold,
            }
            for b in bindings
        ],
    }

    existing_active = await db.execute(
        select(PublishedVersion)
        .where(
            PublishedVersion.profile_id == profile_id,
            PublishedVersion.status == "active",
        )
    )
    for v in existing_active.scalars().all():
        v.status = "archived"
        v.archived_at = datetime.now(timezone.utc)

    version = PublishedVersion(
        version_number=version_number,
        profile_id=profile_id,
        config_snapshot=snapshot,
        status="active",
        published_by=user_id,
    )
    db.add(version)

    profile.status = "active"
    await db.flush()

    return _to_dict(version)


async def list_versions(db: AsyncSession, profile_id: UUID) -> list[dict]:
    query = (
        select(PublishedVersion)
        .where(PublishedVersion.profile_id == profile_id)
        .order_by(PublishedVersion.published_at.desc())
    )
    rows = (await db.execute(query)).scalars().all()
    return [_to_dict(v) for v in rows]


async def get_version(db: AsyncSession, version_id: UUID) -> dict:
    version = await db.get(PublishedVersion, version_id)
    if not version:
        raise BusinessException("E40302", "版本不存在")
    return _to_dict(version)


async def archive_version(db: AsyncSession, version_id: UUID) -> dict:
    version = await db.get(PublishedVersion, version_id)
    if not version:
        raise BusinessException("E40302", "版本不存在")

    if version.status == "archived":
        raise BusinessException("E40303", "版本已归档")

    version.status = "archived"
    version.archived_at = datetime.now(timezone.utc)
    await db.flush()
    return _to_dict(version)


async def _next_version_number(db: AsyncSession, profile_id: UUID) -> str:
    latest_q = (
        select(PublishedVersion.version_number)
        .where(PublishedVersion.profile_id == profile_id)
        .order_by(PublishedVersion.published_at.desc())
        .limit(1)
    )
    latest = (await db.execute(latest_q)).scalar()
    if latest:
        match = re.match(r"v(\d+)\.(\d+)", latest)
        if match:
            major = int(match.group(1)) + 1
            return f"v{major}.0"
    return "v1.0"


def _to_dict(v: PublishedVersion) -> dict:
    return {
        "id": str(v.id),
        "version_number": v.version_number,
        "profile_id": str(v.profile_id),
        "config_snapshot": v.config_snapshot,
        "status": v.status,
        "published_by": str(v.published_by),
        "published_at": v.published_at.isoformat() if v.published_at else None,
        "archived_at": v.archived_at.isoformat() if v.archived_at else None,
    }
