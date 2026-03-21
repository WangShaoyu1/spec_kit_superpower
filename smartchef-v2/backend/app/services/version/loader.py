"""T011: Version loader — resolve published version and profile runtime config."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.dialog_profile import (
    DialogProfile,
    Persona,
    ProfileLibraryBinding,
    PublishedVersion,
)
from app.models.intent_library import IntentLibrary
from app.models.model_version import LibraryModelVersion


class VersionLoader:
    """Load published version config and resolve all bound library models."""

    async def load_active_version(self, db: AsyncSession, profile_id: str | uuid.UUID) -> dict | None:
        """Find the active PublishedVersion for a profile.

        Returns config_snapshot dict, or None if no active version exists.
        """
        pid = uuid.UUID(profile_id) if isinstance(profile_id, str) else profile_id
        stmt = (
            select(PublishedVersion)
            .where(
                PublishedVersion.profile_id == pid,
                PublishedVersion.status == "active",
            )
            .limit(1)
        )
        result = await db.execute(stmt)
        version = result.scalar_one_or_none()
        if version is None:
            return None
        return {
            "version_id": str(version.id),
            "version_number": version.version_number,
            "config_snapshot": version.config_snapshot,
            "published_at": version.published_at.isoformat() if version.published_at else None,
        }

    async def load_profile_runtime(self, db: AsyncSession, profile_id: str | uuid.UUID) -> dict | None:
        """Load full runtime config for a profile.

        Includes profile settings, active persona, bound libraries with
        published model versions, and knowledge-base config stub.
        Returns None when the profile does not exist.
        """
        pid = uuid.UUID(profile_id) if isinstance(profile_id, str) else profile_id

        stmt = (
            select(DialogProfile)
            .options(
                selectinload(DialogProfile.personas),
                selectinload(DialogProfile.library_bindings)
                .selectinload(ProfileLibraryBinding.library),
            )
            .where(DialogProfile.id == pid)
        )
        result = await db.execute(stmt)
        profile = result.scalar_one_or_none()
        if profile is None:
            return None

        active_persona = next((p for p in profile.personas if p.is_active), None)
        persona_config = None
        if active_persona:
            persona_config = {
                "name": active_persona.name,
                "system_prompt": active_persona.system_prompt,
                "temperature": active_persona.temperature,
                "max_tokens": active_persona.max_tokens,
            }

        libraries: list[dict] = []
        for binding in sorted(profile.library_bindings, key=lambda b: b.priority):
            lib = binding.library
            published_model = await self._get_published_model(db, lib.id)
            libraries.append({
                "library_id": str(lib.id),
                "library_key": lib.library_key,
                "name": lib.name,
                "language": lib.language,
                "priority": binding.priority,
                "confidence_threshold": binding.confidence_threshold,
                "published_model": published_model,
            })

        return {
            "profile_id": str(profile.id),
            "name": profile.name,
            "command_threshold": profile.command_threshold,
            "route_strategy": profile.route_strategy,
            "llm_provider": profile.llm_provider,
            "llm_model": profile.llm_model,
            "session_timeout_min": profile.session_timeout_min,
            "persona": persona_config,
            "libraries": libraries,
            "knowledge_base": None,  # placeholder for future KB config
        }

    async def _get_published_model(
        self, db: AsyncSession, library_id: uuid.UUID
    ) -> dict | None:
        """Return the published model version for a given library, if any."""
        stmt = (
            select(LibraryModelVersion)
            .where(
                LibraryModelVersion.library_id == library_id,
                LibraryModelVersion.is_published.is_(True),
            )
            .limit(1)
        )
        result = await db.execute(stmt)
        mv = result.scalar_one_or_none()
        if mv is None:
            return None
        return {
            "model_version_id": str(mv.id),
            "version_name": mv.version_name,
            "artifact_type": mv.artifact_type,
            "artifact_uri": mv.artifact_uri,
            "metrics": mv.metrics,
        }
