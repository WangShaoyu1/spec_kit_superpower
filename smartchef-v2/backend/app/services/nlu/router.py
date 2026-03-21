"""Domain router — classify user text into command / knowledge / chitchat."""

from __future__ import annotations


COMMAND_KEYWORDS = {
    "设置", "调", "打开", "关闭", "开始", "停止", "预热", "定时",
    "set", "start", "stop", "turn", "open", "close", "preheat",
}
KNOWLEDGE_KEYWORDS = {
    "怎么", "如何", "什么", "为什么", "recipe", "how", "what", "why",
}
CHITCHAT_KEYWORDS = {
    "你好", "hello", "hi", "嗨", "哈喽", "谢谢", "thanks", "再见", "bye",
}


class DomainRouter:
    """Route user text to the appropriate processing domain."""

    def route(
        self,
        text: str,
        strategy: str = "intent_first",
        threshold: float = 0.7,
    ) -> str:
        """Return one of: ``command``, ``knowledge``, ``chitchat``."""
        lower = text.lower()

        if strategy == "knowledge_first":
            if self._matches(lower, KNOWLEDGE_KEYWORDS):
                return "knowledge"
            if self._matches(lower, COMMAND_KEYWORDS):
                return "command"
            return "chitchat"

        # Default: intent_first / auto
        if self._matches(lower, COMMAND_KEYWORDS):
            return "command"
        if self._matches(lower, KNOWLEDGE_KEYWORDS):
            return "knowledge"
        if self._matches(lower, CHITCHAT_KEYWORDS):
            return "chitchat"
        return "chitchat"

    @staticmethod
    def _matches(text: str, keywords: set[str]) -> bool:
        return any(kw in text for kw in keywords)
