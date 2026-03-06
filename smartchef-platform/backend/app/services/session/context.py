"""Context maintenance: dialog history and entity stack management."""


def get_recent_history(session: dict, max_turns: int = 5) -> list[dict]:
    history = session.get("dialog_history", [])
    return history[-max_turns:]


def build_chat_messages(
    system_prompt: str,
    session: dict,
    current_text: str,
    max_turns: int = 5,
) -> list[dict]:
    messages = [{"role": "system", "content": system_prompt}]

    for turn in get_recent_history(session, max_turns):
        messages.append({"role": "user", "content": turn["user_text"]})
        messages.append({"role": "assistant", "content": turn["response"]})

    messages.append({"role": "user", "content": current_text})
    return messages


def get_entity_stack(session: dict) -> list[dict]:
    return session.get("entity_stack", [])
