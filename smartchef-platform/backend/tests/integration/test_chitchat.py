"""闲聊（含联网）集成测试：LLM 回复、人设、联网搜索、多轮上下文。

覆盖场景：
1. 普通闲聊 → LLM 回复（mock LLM API）
2. 人设注入 → system_prompt 正确构建
3. 联网查询（天气/新闻）→ Brave Search 调用 → LLM 整合回复
4. 多轮闲聊上下文保持
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.chitchat.persona import build_system_prompt
from app.services.chitchat.web_search import (
    needs_web_search,
    format_search_context,
)
from app.services.nlu.pipeline import run_pipeline, PipelineConfig


# 内存 session 存储，用于 mock Redis
_session_store = {}


async def _mock_get_session(redis, device_id: str):
    return _session_store.get(device_id)


async def _mock_create_session(redis, device_id: str, version_id=None, timeout_minutes=10):
    import uuid
    from datetime import datetime, timezone

    session = {
        "session_id": str(uuid.uuid4()),
        "device_id": device_id,
        "version_id": version_id,
        "state": "IDLE",
        "current_domain": None,
        "dialog_history": [],
        "entity_stack": [],
        "pending_slots": None,
        "active_intent": None,
        "filled_slots": {},
        "unrecognized_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_active_at": datetime.now(timezone.utc).isoformat(),
    }
    _session_store[device_id] = session
    return session


async def _mock_update_session(redis, device_id: str, session: dict, timeout_minutes=10):
    from datetime import datetime, timezone

    session["last_active_at"] = datetime.now(timezone.utc).isoformat()
    _session_store[device_id] = session


def _mock_add_dialog_turn(session, user_text, route, intent, slots, response):
    from datetime import datetime, timezone

    turn = {
        "turn": len(session["dialog_history"]) + 1,
        "user_text": user_text,
        "route": route,
        "intent": intent,
        "slots": slots,
        "response": response,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    session["dialog_history"].append(turn)
    return session


@pytest.fixture(autouse=True)
def clear_session_store():
    """每个测试前清空 session 存储。"""
    _session_store.clear()
    yield
    _session_store.clear()


@pytest.mark.asyncio
async def test_plain_chitchat_llm_reply(db_session: AsyncSession):
    """普通闲聊 → LLM 回复（mock LLM API）。"""
    with (
        patch(
            "app.services.nlu.pipeline.get_session",
            side_effect=_mock_get_session,
        ),
        patch(
            "app.services.nlu.pipeline.create_session",
            side_effect=_mock_create_session,
        ),
        patch(
            "app.services.nlu.pipeline.update_session",
            side_effect=_mock_update_session,
        ),
        patch(
            "app.services.nlu.pipeline.add_dialog_turn",
            side_effect=_mock_add_dialog_turn,
        ),
        patch(
            "app.services.nlu.pipeline.chat_completion",
            new_callable=AsyncMock,
            return_value="你好！我是 SmartChef，有什么可以帮你的？",
        ),
    ):
        config = PipelineConfig(has_knowledge_base=False)
        result = await run_pipeline(
            db_session,
            MagicMock(),
            "你好",
            "test-device-001",
            config=config,
        )

    assert result.domain == "chitchat"
    assert result.response_text == "你好！我是 SmartChef，有什么可以帮你的？"


def test_persona_injection_system_prompt():
    """人设注入 → system_prompt 正确构建。"""
    # 默认人设
    default = build_system_prompt(None)
    assert "SmartChef" in default
    assert "智能厨房助手" in default

    # 自定义人设
    persona = {
        "name": "小厨",
        "personality": "活泼热情",
        "tone_style": "幽默风趣",
    }
    custom = build_system_prompt(persona)
    assert "小厨" in custom
    assert "活泼热情" in custom
    assert "幽默风趣" in custom

    # 完全自定义 system_prompt
    persona_custom = {"system_prompt": "你是专属厨师助理，只回答做菜问题。"}
    full_custom = build_system_prompt(persona_custom)
    assert full_custom == "你是专属厨师助理，只回答做菜问题。"


@pytest.mark.asyncio
async def test_web_search_integration(db_session: AsyncSession):
    """联网查询（天气/新闻）→ Brave Search 调用 → LLM 整合回复。"""
    mock_search_results = [
        {"title": "北京天气", "description": "今日晴，15-25℃", "url": "https://example.com"},
        {"title": "天气预报", "description": "明天多云", "url": "https://example.com/2"},
    ]

    with (
        patch(
            "app.services.nlu.pipeline.get_session",
            side_effect=_mock_get_session,
        ),
        patch(
            "app.services.nlu.pipeline.create_session",
            side_effect=_mock_create_session,
        ),
        patch(
            "app.services.nlu.pipeline.update_session",
            side_effect=_mock_update_session,
        ),
        patch(
            "app.services.nlu.pipeline.add_dialog_turn",
            side_effect=_mock_add_dialog_turn,
        ),
        patch(
            "app.services.nlu.pipeline.brave_search",
            new_callable=AsyncMock,
            return_value=mock_search_results,
        ),
        patch(
            "app.services.nlu.pipeline.chat_completion",
            new_callable=AsyncMock,
            return_value="根据搜索结果，北京今日晴，15-25℃，适合出行。",
        ),
    ):
        config = PipelineConfig(has_knowledge_base=False)
        result = await run_pipeline(
            db_session,
            MagicMock(),
            "今天北京天气怎么样",
            "test-device-web",
            config=config,
        )

    assert result.domain == "chitchat"
    assert "北京" in result.response_text or "晴" in result.response_text or "天气" in result.response_text
    assert "web_search" in result.debug_info
    assert len(result.debug_info["web_search"]) == 2


def test_needs_web_search_detection():
    """验证联网关键词检测。"""
    assert needs_web_search("今天天气怎么样") is True
    assert needs_web_search("北京 news") is True
    assert needs_web_search("股票行情") is True
    assert needs_web_search("现在几点了") is True
    assert needs_web_search("红烧肉怎么做") is False
    assert needs_web_search("你好") is False


def test_format_search_context():
    """验证搜索结果格式化。"""
    results = [
        {"title": "标题1", "description": "描述1", "url": "http://a.com"},
        {"title": "标题2", "description": "描述2", "url": "http://b.com"},
    ]
    ctx = format_search_context(results)
    assert "以下是搜索结果" in ctx
    assert "标题1" in ctx
    assert "描述1" in ctx
    assert "标题2" in ctx
    assert format_search_context([]) == ""


@pytest.mark.asyncio
async def test_multi_turn_context_preserved(db_session: AsyncSession):
    """多轮闲聊上下文保持。"""
    with (
        patch(
            "app.services.nlu.pipeline.get_session",
            side_effect=_mock_get_session,
        ),
        patch(
            "app.services.nlu.pipeline.create_session",
            side_effect=_mock_create_session,
        ),
        patch(
            "app.services.nlu.pipeline.update_session",
            side_effect=_mock_update_session,
        ),
        patch(
            "app.services.nlu.pipeline.add_dialog_turn",
            side_effect=_mock_add_dialog_turn,
        ),
        patch(
            "app.services.nlu.pipeline.chat_completion",
            new_callable=AsyncMock,
        ) as mock_llm,
    ):
        config = PipelineConfig(has_knowledge_base=False)
        mock_llm.return_value = "第一轮回复"
        r1 = await run_pipeline(
            db_session, MagicMock(), "你好", "device-multi", config=config
        )
        assert r1.domain == "chitchat"

        # 第二轮：应带上首轮历史
        mock_llm.return_value = "第二轮回复"
        r2 = await run_pipeline(
            db_session, MagicMock(), "你叫什么", "device-multi", config=config
        )

    # 验证 chat_completion 被调用时 messages 包含历史
    assert mock_llm.call_count >= 2
    second_call_messages = mock_llm.call_args_list[1].kwargs.get("messages") or mock_llm.call_args_list[1].args[0]
    # 应包含 system + 第一轮 user/assistant + 第二轮 user
    assert len(second_call_messages) >= 3
    user_contents = [m["content"] for m in second_call_messages if m["role"] == "user"]
    assert "你好" in user_contents
    assert "你叫什么" in user_contents
