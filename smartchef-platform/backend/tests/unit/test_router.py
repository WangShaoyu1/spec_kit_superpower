import pytest
from app.services.nlu.router import route_input


@pytest.mark.asyncio
async def test_route_command_keyword():
    result = await route_input("开始烹饪", "zh", strategy="command_first")
    assert result.domain == "command"
    assert result.confidence > 0.5


@pytest.mark.asyncio
async def test_route_knowledge_keyword():
    result = await route_input("红烧肉怎么做", "zh", has_knowledge_base=True, strategy="balanced")
    assert result.domain == "knowledge"


@pytest.mark.asyncio
async def test_route_chitchat_keyword():
    result = await route_input("今天天气怎么样", "zh", strategy="balanced")
    assert result.domain == "chitchat"


@pytest.mark.asyncio
async def test_route_fallback_command_first():
    result = await route_input("abcdef", "zh", strategy="command_first")
    assert result.domain == "command"
