from app.services.nlu.dialog_manager import (
    DialogState, check_missing_slots, get_slot_prompt,
    build_progressive_error_response, process_command_state,
)
from app.services.nlu.slot_extractor import SlotValue


def test_check_missing_slots_all_filled():
    defs = [{"slot_key": "temp", "is_required": True}]
    assert check_missing_slots(defs, {"temp": "180"}) == []


def test_check_missing_slots_missing():
    defs = [
        {"slot_key": "temp", "is_required": True, "sort_order": 0},
        {"slot_key": "time", "is_required": True, "sort_order": 1},
    ]
    missing = check_missing_slots(defs, {})
    assert len(missing) == 2
    assert missing[0]["slot_key"] == "temp"


def test_progressive_error_level_1():
    text, reset = build_progressive_error_response(1)
    assert "换种方式" in text
    assert reset is False


def test_progressive_error_level_2():
    text, reset = build_progressive_error_response(2)
    assert "操作" in text
    assert reset is False


def test_progressive_error_level_3():
    text, reset = build_progressive_error_response(3)
    assert "屏幕触控" in text
    assert reset is True


def test_slot_prompt_custom():
    assert "温度" in get_slot_prompt({"slot_key": "temp", "prompt_text": "请设置温度"})


def test_slot_prompt_default():
    assert "什么" in get_slot_prompt({"slot_key": "time", "display_name": "时间"})


def test_process_command_complete():
    state = DialogState()
    extracted = [SlotValue(slot_key="temp", value="180", start=0, end=3)]
    slot_defs = [{"slot_key": "temp", "is_required": True}]
    new_state, prompt, complete = process_command_state(state, "set_temp", extracted, slot_defs, 0.8)
    assert complete is True
    assert prompt is None


def test_process_command_missing_slot():
    state = DialogState()
    extracted = []
    slot_defs = [{"slot_key": "temp", "is_required": True, "display_name": "温度", "sort_order": 0}]
    new_state, prompt, complete = process_command_state(state, "set_temp", extracted, slot_defs, 0.8)
    assert complete is False
    assert prompt is not None
    assert new_state.state == "SLOT_PROMPTING"
