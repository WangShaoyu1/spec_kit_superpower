"""Regression: custom prompt templates must support {intent_list} (LLM 合成)."""

from unittest.mock import MagicMock

import pytest

from app.core.api_response import BusinessException
from app.services.data_generation_service import _format_generation_prompt


def _mock_intent(name, key, desc):
    m = MagicMock()
    m.name_zh = name
    m.intent_key = key
    m.description = desc
    return m


def test_format_prompt_includes_intent_list():
    intents = [_mock_intent("煮饭", "cook", "烹饪"), _mock_intent("定时", "timer", None)]
    tpl = "请生成:\n{intent_list}"
    out = _format_generation_prompt(
        tpl,
        intents=intents,
        current=intents[0],
        intent_examples="(无)",
        samples_per_intent=10,
    )
    assert "煮饭" in out
    assert "定时" in out
    assert "cook" in out


def test_format_unknown_placeholder_raises_business():
    intents = [_mock_intent("A", "a", None)]
    with pytest.raises(BusinessException) as ei:
        _format_generation_prompt(
            "{not_a_real_key}",
            intents=intents,
            current=intents[0],
            intent_examples="x",
            samples_per_intent=1,
        )
    assert ei.value.error_code == "E50603"
