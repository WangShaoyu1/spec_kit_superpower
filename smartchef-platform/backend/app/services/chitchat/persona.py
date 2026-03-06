"""Persona management: convert Persona model to system prompt for LLM."""


def build_system_prompt(persona_data: dict | None) -> str:
    if not persona_data:
        return (
            "你是 SmartChef 智能厨房助手，友好、专业、简洁。"
            "你帮助用户解答烹饪问题、提供菜谱建议和日常闲聊。"
            "回复应简洁明了，控制在 100 字以内。"
        )

    name = persona_data.get("name", "SmartChef")
    personality = persona_data.get("personality", "友好专业")
    tone = persona_data.get("tone_style", "简洁明了")
    custom_prompt = persona_data.get("system_prompt", "")

    if custom_prompt:
        return custom_prompt

    return (
        f"你是一个名叫{name}的智能厨房助手。"
        f"你的性格是{personality}，语气风格是{tone}。"
        "你帮助用户解答烹饪问题、提供菜谱建议和日常闲聊。"
        "回复应简洁明了，控制在 100 字以内。"
    )
