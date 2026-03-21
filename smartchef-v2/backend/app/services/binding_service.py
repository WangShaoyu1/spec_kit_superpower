"""Profile ↔ IntentLibrary binding management service."""

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.api_response import BusinessException
from app.models.dialog_profile import DialogProfile, ProfileLibraryBinding
from app.models.intent_library import IntentLibrary
from app.schemas.profile import BindLibraryRequest


async def list_bindings(db: AsyncSession, profile_id: UUID) -> list[dict]:
    await _ensure_profile(db, profile_id)
    query = (
        select(ProfileLibraryBinding)
        .options(joinedload(ProfileLibraryBinding.library))
        .where(ProfileLibraryBinding.profile_id == profile_id)
        .order_by(ProfileLibraryBinding.priority.asc())
    )
    rows = (await db.execute(query)).scalars().all()
    return [_to_dict(b) for b in rows]


async def sync_bindings(
    db: AsyncSession,
    profile_id: UUID,
    bindings: list[BindLibraryRequest],
) -> list[dict]:
    await _ensure_profile(db, profile_id)

    for b in bindings:
        lib = await db.get(IntentLibrary, b.library_id)
        if not lib:
            raise BusinessException("E40103", f"意图库 {b.library_id} 不存在")

    await db.execute(
        delete(ProfileLibraryBinding)
        .where(ProfileLibraryBinding.profile_id == profile_id)
    )
    await db.flush()

    new_bindings = []
    for b in bindings:
        binding = ProfileLibraryBinding(
            profile_id=profile_id,
            library_id=b.library_id,
            priority=b.priority,
            confidence_threshold=b.confidence_threshold,
        )
        db.add(binding)
        new_bindings.append(binding)

    await db.flush()

    result_query = (
        select(ProfileLibraryBinding)
        .options(joinedload(ProfileLibraryBinding.library))
        .where(ProfileLibraryBinding.profile_id == profile_id)
        .order_by(ProfileLibraryBinding.priority.asc())
    )
    rows = (await db.execute(result_query)).scalars().all()
    return [_to_dict(b) for b in rows]


async def _ensure_profile(db: AsyncSession, profile_id: UUID) -> DialogProfile:
    profile = await db.get(DialogProfile, profile_id)
    if not profile:
        raise BusinessException("E40101", "对话方案不存在")
    return profile


def _to_dict(b: ProfileLibraryBinding) -> dict:
    lib = b.library
    return {
        "id": str(b.id),
        "profile_id": str(b.profile_id),
        "library_id": str(b.library_id),
        "library_name": lib.name if lib else None,
        "library_key": lib.library_key if lib else None,
        "priority": b.priority,
        "confidence_threshold": b.confidence_threshold,
    }
