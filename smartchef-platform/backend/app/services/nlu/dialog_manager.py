"""Dialog state manager: FSM state machine, slot filling, multi-turn prompting."""
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class DialogState:
    state: str = "IDLE"  # IDLE, ROUTING, COMMAND_PROCESSING, SLOT_PROMPTING, KNOWLEDGE_QA, CHITCHAT
    active_intent: str | None = None
    pending_slots: list[dict] = field(default_factory=list)
    filled_slots: dict = field(default_factory=dict)
    unrecognized_count: int = 0


def check_missing_slots(
    slot_definitions: list[dict],
    extracted_slots: dict,
) -> list[dict]:
    missing = []
    for slot_def in slot_definitions:
        if slot_def.get("is_required") and slot_def["slot_key"] not in extracted_slots:
            missing.append(slot_def)
    missing.sort(key=lambda s: s.get("sort_order", 0))
    return missing


def get_slot_prompt(slot_def: dict) -> str:
    if slot_def.get("prompt_text"):
        return slot_def["prompt_text"]
    name = slot_def.get("display_name", slot_def["slot_key"])
    return f"请问{name}是什么？"


def build_progressive_error_response(unrecognized_count: int, context: str = "") -> tuple[str, bool]:
    """Build progressive error response based on retry count.
    Returns (response_text, should_reset).
    """
    if unrecognized_count <= 1:
        return "抱歉，我没有理解您的意思，您能换种方式再说一次吗？", False
    elif unrecognized_count == 2:
        return "我还是没有理解，您可以试试以下操作：\n1. 开始烹饪\n2. 设置温度\n3. 搜索菜谱\n4. 查看菜谱", False
    else:
        return "很抱歉一直无法理解您的指令，建议您使用屏幕触控操作。如需继续语音交互，请说'你好'重新开始。", True


def process_command_state(
    dialog_state: DialogState,
    intent_key: str,
    extracted_slots: list,
    slot_definitions: list[dict],
    confidence: float,
    threshold: float = 0.3,
) -> tuple[DialogState, str | None, bool]:
    """Process command domain state transition.
    
    Returns: (updated_state, prompt_text_or_none, is_complete)
    """
    if confidence < threshold:
        dialog_state.unrecognized_count += 1
        response, should_reset = build_progressive_error_response(dialog_state.unrecognized_count)
        if should_reset:
            dialog_state.state = "IDLE"
            dialog_state.unrecognized_count = 0
        return dialog_state, response, False

    dialog_state.unrecognized_count = 0
    dialog_state.active_intent = intent_key
    dialog_state.state = "COMMAND_PROCESSING"

    filled = {s.slot_key: s.value for s in extracted_slots}
    dialog_state.filled_slots.update(filled)

    missing = check_missing_slots(slot_definitions, dialog_state.filled_slots)

    if missing:
        dialog_state.state = "SLOT_PROMPTING"
        dialog_state.pending_slots = missing
        prompt = get_slot_prompt(missing[0])
        return dialog_state, prompt, False

    dialog_state.state = "IDLE"
    dialog_state.pending_slots = []
    return dialog_state, None, True
