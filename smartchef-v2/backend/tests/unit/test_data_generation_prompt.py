"""Regression: custom prompt templates must support {intent_list} (LLM 合成)."""

from unittest.mock import MagicMock

import pytest

from app.core.api_response import BusinessException
from app.services.data_generation_service import (
    _append_per_intent_hint_if_needed,
    _format_generation_prompt,
    _parse_samples_per_intent,
)


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


def test_format_invalid_braces_raises_business():
    intents = [_mock_intent("A", "a", None)]
    with pytest.raises(BusinessException) as ei:
        _format_generation_prompt(
            "bad {intent_list",
            intents=intents,
            current=intents[0],
            intent_examples="x",
            samples_per_intent=1,
        )
    assert ei.value.error_code == "E50603"


def test_parse_samples_per_intent():
    assert _parse_samples_per_intent(150, 20) == 150
    assert _parse_samples_per_intent(None, 20) == 20
    with pytest.raises(BusinessException):
        _parse_samples_per_intent("x", 20)
    with pytest.raises(BusinessException):
        _parse_samples_per_intent(0, 20)


def test_append_hint_when_only_intent_list_template():
    intents = [_mock_intent("煮饭", "cook", "烹饪")]
    tpl = "列表:\n{intent_list}"
    base = _format_generation_prompt(
        tpl,
        intents=intents,
        current=intents[0],
        intent_examples="(无)",
        samples_per_intent=3,
    )
    out = _append_per_intent_hint_if_needed(
        tpl, base, current=intents[0], samples_per_intent=3
    )
    assert "煮饭" in out
    assert "intent_key=cook" in out
    assert "恰好 3 条" in out


def test_no_append_when_intent_name_in_template():
    intents = [_mock_intent("煮饭", "cook", "烹饪")]
    tpl = "为 {intent_name} 生成 {count} 条\n{intent_list}"
    base = _format_generation_prompt(
        tpl,
        intents=intents,
        current=intents[0],
        intent_examples="(无)",
        samples_per_intent=3,
    )
    out = _append_per_intent_hint_if_needed(
        tpl, base, current=intents[0], samples_per_intent=3
    )
    assert out == base
