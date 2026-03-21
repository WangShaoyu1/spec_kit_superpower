"""NLU processing pipeline — preprocess → route → domain handler → response."""

from __future__ import annotations

import random
import time

from app.services.nlu.router import DomainRouter

MOCK_INTENTS = [
    "set_temperature", "set_timer", "start_cooking", "stop_cooking",
    "query_recipe", "adjust_heat", "preheat_oven",
]


class NLUPipeline:
    """Main NLU pipeline coordinating routing and domain handlers."""

    def __init__(self) -> None:
        self.router = DomainRouter()

    async def process(
        self,
        text: str,
        profile_config: dict,
        session_context: dict | None = None,
    ) -> dict:
        """Run full NLU pipeline and return structured result.

        Returns dict with keys: domain, intent, slots, confidence,
        response_text, debug.
        """
        start = time.perf_counter()

        cleaned = self._preprocess(text)

        strategy = profile_config.get("route_strategy", "intent_first")
        threshold = profile_config.get("command_threshold", 0.7)
        domain = self.router.route(cleaned, strategy=strategy, threshold=threshold)

        if domain == "command":
            result = self._handle_command(cleaned, threshold)
        elif domain == "knowledge":
            result = self._handle_knowledge(cleaned)
        else:
            result = self._handle_chitchat(cleaned, profile_config)

        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        result["debug"] = {
            "preprocessed_text": cleaned,
            "route_strategy": strategy,
            "latency_ms": elapsed_ms,
            **result.get("debug", {}),
        }
        return result

    @staticmethod
    def _preprocess(text: str) -> str:
        return text.strip()

    @staticmethod
    def _handle_command(text: str, threshold: float) -> dict:
        intent = random.choice(MOCK_INTENTS)
        confidence = round(random.uniform(threshold, 0.99), 4)
        return {
            "domain": "command",
            "intent": intent,
            "slots": {},
            "confidence": confidence,
            "response_text": f"[mock] 已识别指令: {intent}",
            "debug": {
                "candidates": [{"intent": intent, "confidence": confidence}],
            },
        }

    @staticmethod
    def _handle_knowledge(text: str) -> dict:
        return {
            "domain": "knowledge",
            "intent": None,
            "slots": {},
            "confidence": 0.0,
            "response_text": "[mock] 知识库检索暂未接入，请稍后再试。",
            "debug": {"query": text},
        }

    @staticmethod
    def _handle_chitchat(text: str, profile_config: dict) -> dict:
        persona = profile_config.get("persona") or {}
        persona_name = persona.get("name", "default")
        return {
            "domain": "chitchat",
            "intent": None,
            "slots": {},
            "confidence": 0.0,
            "response_text": f"[mock][persona={persona_name}] 你好！有什么可以帮你的吗？",
            "debug": {"persona": persona_name},
        }
