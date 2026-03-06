"""Domain router: classify input into command/knowledge/chitchat domains."""
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RouteResult:
    domain: str  # "command" | "knowledge" | "chitchat"
    confidence: float


async def route_input(
    text: str,
    language: str,
    intent_keys: list[str] | None = None,
    has_knowledge_base: bool = False,
    strategy: str = "command_first",
) -> RouteResult:
    """Route user input to the appropriate domain.
    
    In production, this would use a trained classifier.
    Current implementation uses heuristic rules as a foundation.
    """
    text_lower = text.lower()

    command_signals = [
        "开始", "停止", "暂停", "继续", "设置", "调", "关", "开", "启动",
        "加热", "解冻", "定时", "取消", "搜索", "收藏", "推荐", "查找",
        "start", "stop", "pause", "set", "cancel", "search", "cook",
        "音量", "亮度", "温度", "时间", "模式",
    ]

    knowledge_signals = [
        "怎么做", "怎么烧", "需要什么", "食材", "步骤", "做法",
        "营养", "热量", "卡路里", "配料", "多少度", "多长时间",
        "how to", "ingredients", "recipe", "nutrition",
    ]

    chitchat_signals = [
        "天气", "新闻", "股票", "笑话", "故事", "聊聊",
        "你好", "谢谢", "再见", "帮帮", "什么是",
        "weather", "news", "hello", "thanks", "joke",
    ]

    cmd_score = sum(1 for s in command_signals if s in text_lower) * 0.3
    kb_score = sum(1 for s in knowledge_signals if s in text_lower) * 0.3
    chat_score = sum(1 for s in chitchat_signals if s in text_lower) * 0.3

    if strategy == "command_first":
        cmd_score += 0.1
    elif strategy == "knowledge_first":
        kb_score += 0.1

    if not has_knowledge_base:
        kb_score *= 0.5

    scores = {"command": cmd_score, "knowledge": kb_score, "chitchat": chat_score}
    best_domain = max(scores, key=scores.get)
    best_score = scores[best_domain]

    if best_score < 0.15:
        if strategy == "command_first":
            best_domain = "command"
            best_score = 0.4
        else:
            best_domain = "chitchat"
            best_score = 0.3

    confidence = min(best_score + 0.5, 1.0)

    logger.info(f"Route: text='{text[:30]}...' -> domain={best_domain} confidence={confidence:.2f}")
    return RouteResult(domain=best_domain, confidence=round(confidence, 4))
