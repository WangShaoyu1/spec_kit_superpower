"""Unit tests for app.services.persona_service."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_response import BusinessException
from app.schemas.profile import CreatePersonaRequest
from app.services.persona_service import (
    activate_persona,
    create_persona,
    delete_persona,
    get_persona,
)


def _mock_db() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


def _make_persona(*, profile_id=None, is_active=False):
    p = MagicMock()
    p.id = uuid4()
    p.profile_id = profile_id or uuid4()
    p.name = "test-persona"
    p.system_prompt = "You are helpful."
    p.personality = "friendly"
    p.temperature = 0.7
    p.max_tokens = 1024
    p.is_active = is_active
    p.created_at = None
    p.updated_at = None
    return p


@pytest.mark.asyncio
async def test_create_persona_success():
    db = _mock_db()
    profile_id = uuid4()

    profile_mock = MagicMock()
    profile_mock.id = profile_id

    persona_sentinel = _make_persona(profile_id=profile_id)

    async def fake_get(model, pk, **kw):
        from app.models.dialog_profile import DialogProfile
        if model is DialogProfile:
            return profile_mock
        return persona_sentinel

    db.get = AsyncMock(side_effect=fake_get)

    data = CreatePersonaRequest(
        name="Chef Persona",
        system_prompt="You are a chef assistant.",
        personality="warm",
        temperature=0.8,
        max_tokens=2048,
    )
    result = await create_persona(db, profile_id, data)

    db.add.assert_called_once()
    db.flush.assert_awaited_once()
    assert result["name"] == "Chef Persona"


@pytest.mark.asyncio
async def test_create_persona_profile_not_found():
    db = _mock_db()
    db.get = AsyncMock(return_value=None)

    data = CreatePersonaRequest(
        name="X",
        system_prompt="prompt",
    )
    with pytest.raises(BusinessException) as exc_info:
        await create_persona(db, uuid4(), data)

    assert exc_info.value.error_code == "E40101"


@pytest.mark.asyncio
async def test_get_persona_not_found():
    db = _mock_db()
    db.get = AsyncMock(return_value=None)

    with pytest.raises(BusinessException) as exc_info:
        await get_persona(db, uuid4())

    assert exc_info.value.error_code == "E40201"


@pytest.mark.asyncio
async def test_activate_persona_wrong_profile():
    db = _mock_db()
    persona = _make_persona(profile_id=uuid4())
    db.get = AsyncMock(return_value=persona)

    different_profile_id = uuid4()

    with pytest.raises(BusinessException) as exc_info:
        await activate_persona(db, different_profile_id, persona.id)

    assert exc_info.value.error_code == "E40201"


@pytest.mark.asyncio
async def test_delete_persona_not_found():
    db = _mock_db()
    db.get = AsyncMock(return_value=None)

    with pytest.raises(BusinessException) as exc_info:
        await delete_persona(db, uuid4())

    assert exc_info.value.error_code == "E40201"
