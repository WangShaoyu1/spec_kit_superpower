"""Placeholder NLU pipeline — mock classification for development."""

import random


MOCK_INTENTS = [
    "set_temperature", "set_timer", "start_cooking", "stop_cooking",
    "query_recipe", "adjust_heat", "preheat_oven",
]


def classify_message(text: str) -> dict:
    """Return mock NLU classification result.

    Will be replaced by a real pipeline once intent models are integrated.
    """
    domain = route_domain(text)
    if domain == "command":
        intent = random.choice(MOCK_INTENTS)
        confidence = round(random.uniform(0.70, 0.99), 4)
        return {
            "domain": "command",
            "intent": intent,
            "confidence": confidence,
            "slots": {},
            "candidates": [
                {"intent": intent, "confidence": confidence},
            ],
        }
    elif domain == "knowledge":
        return {
            "domain": "knowledge",
            "intent": None,
            "confidence": 0.0,
            "query": text,
        }
    else:
        return {
            "domain": "chitchat",
            "intent": None,
            "confidence": 0.0,
        }


def route_domain(text: str) -> str:
    """Placeholder domain router — keyword-based classification."""
    command_keywords = {"设置", "调", "打开", "关闭", "开始", "停止", "预热", "定时", "set", "start", "stop", "turn"}
    knowledge_keywords = {"怎么", "如何", "什么", "为什么", "recipe", "how", "what", "why"}

    lower = text.lower()

    for kw in command_keywords:
        if kw in lower:
            return "command"

    for kw in knowledge_keywords:
        if kw in lower:
            return "knowledge"

    return "chitchat"
