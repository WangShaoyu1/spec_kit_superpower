import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_persona(client: AsyncClient, auth_headers):
    resp = await client.post(
        "/api/v1/profiles/personas",
        json={
            "name": "小厨",
            "personality": "活泼友好、热情开朗",
            "tone_style": "亲切随和、带有趣味",
            "system_prompt": "你是一个名叫小厨的友好厨房助手",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == "小厨"


@pytest.mark.asyncio
async def test_create_dialog_profile(client: AsyncClient, auth_headers):
    resp = await client.post(
        "/api/v1/profiles",
        json={
            "name": "方案A - GPT-4o 活泼版",
            "description": "使用 GPT-4o 配合活泼人设",
            "llm_provider": "gpt-4o",
            "routing_strategy": "command_first",
            "session_timeout_minutes": 10,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "方案A - GPT-4o 活泼版"
    assert data["llm_provider"] == "gpt-4o"
    assert data["routing_strategy"] == "command_first"
    assert data["status"] == "draft"


@pytest.mark.asyncio
async def test_list_profiles(client: AsyncClient, auth_headers):
    await client.post(
        "/api/v1/profiles",
        json={"name": "方案1", "llm_provider": "gpt-4o"},
        headers=auth_headers,
    )
    resp = await client.get("/api/v1/profiles", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_update_profile(client: AsyncClient, auth_headers):
    create_resp = await client.post(
        "/api/v1/profiles",
        json={"name": "更新前", "llm_provider": "gpt-4o"},
        headers=auth_headers,
    )
    profile_id = create_resp.json()["id"]
    resp = await client.patch(
        f"/api/v1/profiles/{profile_id}",
        json={"name": "更新后", "llm_provider": "qwen-max"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "更新后"
    assert resp.json()["llm_provider"] == "qwen-max"


@pytest.mark.asyncio
async def test_delete_profile(client: AsyncClient, auth_headers):
    create_resp = await client.post(
        "/api/v1/profiles",
        json={"name": "待删除", "llm_provider": "gpt-4o"},
        headers=auth_headers,
    )
    profile_id = create_resp.json()["id"]
    resp = await client.delete(f"/api/v1/profiles/{profile_id}", headers=auth_headers)
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_profile_with_persona(client: AsyncClient, auth_headers):
    persona_resp = await client.post(
        "/api/v1/profiles/personas",
        json={
            "name": "测试人设",
            "personality": "专业可靠",
            "tone_style": "简洁专业",
            "system_prompt": "你是一个专业的厨房助手",
        },
        headers=auth_headers,
    )
    persona_id = persona_resp.json()["id"]

    profile_resp = await client.post(
        "/api/v1/profiles",
        json={"name": "带人设方案", "llm_provider": "gpt-4o", "persona_id": persona_id},
        headers=auth_headers,
    )
    assert profile_resp.status_code == 201
    data = profile_resp.json()
    assert data["persona"] is not None
    assert data["persona"]["name"] == "测试人设"
