"""统一响应构建器：构造 DialogResponse，兼容指令/知识/闲聊三域。

依据 FR-026：API 统一响应格式必须兼容三种域类型，包含：
- 域类型、意图标识（指令域）、槽位列表（指令域）、回复文本、
- 置信度、会话ID、是否需要追问、处理耗时

依据 FR-024：多语言支持，英文输入时用英文回复（提示语、错误提示、确认信息）。
"""
from typing import Any

from pydantic import BaseModel, Field


# ========== 多语言提示文本（FR-024） ==========


def get_empty_input_prompt(language: str) -> str:
    """输入为空时的提示语。"""
    return "Say something~" if language == "en" else "请说点什么吧~"


def get_slot_prompt(slot_def: dict, language: str) -> str:
    """槽位追问提示：优先使用配置的 prompt_text / prompt_text_en。"""
    if language == "en" and slot_def.get("prompt_text_en"):
        return slot_def["prompt_text_en"]
    if slot_def.get("prompt_text"):
        return slot_def["prompt_text"]
    name = slot_def.get("display_name", slot_def["slot_key"])
    return f"What is the {name}?" if language == "en" else f"请问{name}是什么？"


def get_progressive_error_response(unrecognized_count: int, language: str) -> tuple[str, bool]:
    """渐进式错误回复（FR-020）：3 级处理。
    第 1 次未识别：温和重试；第 2 次：选项列表；第 3 次：兜底话术。
    Returns (response_text, should_reset)。
    """
    if language == "en":
        if unrecognized_count <= 1:
            return "Sorry, I didn't catch that. Please try again.", False
        elif unrecognized_count == 2:
            return (
                "I still didn't understand. You could try:\n"
                "1. Start cooking\n2. Set temperature\n3. Search recipe\n4. View recipe",
                False,
            )
        else:
            return (
                "I'm sorry I couldn't understand. Please use the touch screen. "
                "Say 'hello' to restart voice interaction.",
                True,
            )
    # 中文：第 1 次 → 温和重试；第 2 次 → 选项列表；第 3 次 → 兜底话术
    if unrecognized_count <= 1:
        return "没听清，请再说一次。", False
    elif unrecognized_count == 2:
        return (
            "您是想说以下哪个？\n"
            "1. 开始烹饪\n2. 设置温度\n3. 搜索菜谱\n4. 查看菜谱",
            False,
        )
    else:
        return (
            "很抱歉一直无法理解您的指令，建议您使用屏幕触控操作。"
            "如需继续语音交互，请说'你好'重新开始。",
            True,
        )


def get_command_confirmation(display: str, slot_parts: str, language: str) -> str:
    """指令确认回复文本。"""
    if language == "en":
        suffix = f" ({slot_parts})" if slot_parts else ""
        return f"OK, {display}{suffix}"
    suffix = f"（{slot_parts}）" if slot_parts else ""
    return f"好的，{display}{suffix}"


def get_high_risk_confirmation_message(
    intent_key: str, param: str, val: float, unit: str, threshold: float, language: str
) -> str:
    """高风险操作二次确认提示。"""
    if language == "en":
        return (
            f"High risk detected: {intent_key}, {param}={val}{unit} "
            f"exceeds safe threshold {threshold}{unit}. Confirm to continue? (Say 'confirm' or 'cancel')"
        )
    return (
        f"检测到高风险操作：{intent_key}，{param}={val}{unit} "
        f"超过安全阈值 {threshold}{unit}。请确认是否继续？（说'确认'或'取消'）"
    )


class DialogResponse(BaseModel):
    """统一对话响应格式，兼容指令域、知识域、闲聊域。"""

    domain: str = Field(..., description="域类型：command / knowledge / chitchat")
    intent: str | None = Field(None, description="意图标识（指令域专用）")
    slots: dict[str, Any] = Field(default_factory=dict, description="槽位列表（指令域专用）")
    knowledge_hit: list[dict[str, Any]] | dict[str, Any] | None = Field(
        None, description="命中的知识库条目（知识域专用）"
    )
    response_text: str = Field(..., description="回复文本")
    confidence: float = Field(..., ge=0, le=1, description="路由或意图置信度")
    session_id: str | None = Field(None, description="会话 ID")
    needs_followup: bool = Field(False, description="是否需要追问（槽位补全或二次确认）")
    requires_confirmation: bool = Field(False, description="是否需二次确认（FR-019 高风险操作）")
    latency_ms: int = Field(0, ge=0, description="处理耗时（毫秒）")

    model_config = {"extra": "forbid"}


def build_command_response(
    *,
    intent: str,
    slots: dict[str, Any],
    response_text: str,
    confidence: float,
    session_id: str | None = None,
    needs_followup: bool = False,
    requires_confirmation: bool = False,
    latency_ms: int = 0,
) -> DialogResponse:
    """构造指令域响应。

    Args:
        intent: 意图标识
        slots: 槽位键值对
        response_text: 确认或追问的回复文本
        confidence: 意图分类置信度
        session_id: 会话 ID
        needs_followup: 是否需追问（槽位缺失或高风险二次确认）
        requires_confirmation: 是否需二次确认（FR-019 高风险操作）
        latency_ms: 处理耗时

    Returns:
        统一的 DialogResponse
    """
    return DialogResponse(
        domain="command",
        intent=intent,
        slots=slots or {},
        response_text=response_text,
        confidence=confidence,
        session_id=session_id,
        needs_followup=needs_followup,
        requires_confirmation=requires_confirmation,
        latency_ms=latency_ms,
    )


def build_knowledge_response(
    *,
    response_text: str,
    confidence: float,
    session_id: str | None = None,
    knowledge_hit: list[dict[str, Any]] | dict[str, Any] | None = None,
    latency_ms: int = 0,
) -> DialogResponse:
    """构造知识域响应。

    Args:
        response_text: 知识问答回复文本
        confidence: 路由/检索置信度
        session_id: 会话 ID
        knowledge_hit: 命中的知识库条目（单条为 dict，多条为 list）
        latency_ms: 处理耗时

    Returns:
        统一的 DialogResponse
    """
    return DialogResponse(
        domain="knowledge",
        intent=None,
        slots={},
        knowledge_hit=knowledge_hit,
        response_text=response_text,
        confidence=confidence,
        session_id=session_id,
        needs_followup=False,
        latency_ms=latency_ms,
    )


def build_chitchat_response(
    *,
    response_text: str,
    confidence: float,
    session_id: str | None = None,
    latency_ms: int = 0,
) -> DialogResponse:
    """构造闲聊域响应。

    Args:
        response_text: 大模型生成的回复文本
        confidence: 路由置信度
        session_id: 会话 ID
        latency_ms: 处理耗时

    Returns:
        统一的 DialogResponse
    """
    return DialogResponse(
        domain="chitchat",
        intent=None,
        slots={},
        response_text=response_text,
        confidence=confidence,
        session_id=session_id,
        needs_followup=False,
        latency_ms=latency_ms,
    )
