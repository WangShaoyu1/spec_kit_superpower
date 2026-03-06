"""Web search module: Brave Search API integration for real-time content."""
import logging
import httpx
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

REALTIME_KEYWORDS = ["天气", "weather", "股票", "stock", "新闻", "news", "今天", "today", "现在", "now"]


def needs_web_search(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in REALTIME_KEYWORDS)


async def brave_search(query: str, count: int = 3) -> list[dict]:
    """Search using Brave Search API."""
    if not settings.BRAVE_SEARCH_API_KEY:
        logger.warning("Brave Search API key not configured")
        return []

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={"q": query, "count": count, "search_lang": "zh-hans"},
                headers={
                    "X-Subscription-Token": settings.BRAVE_SEARCH_API_KEY,
                    "Accept": "application/json",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        results = []
        for item in data.get("web", {}).get("results", [])[:count]:
            results.append({
                "title": item.get("title", ""),
                "description": item.get("description", ""),
                "url": item.get("url", ""),
            })
        return results

    except Exception as e:
        logger.error(f"Brave Search failed: {e}")
        return []


def format_search_context(results: list[dict]) -> str:
    if not results:
        return ""
    parts = []
    for r in results:
        parts.append(f"- {r['title']}: {r['description']}")
    return "以下是搜索结果：\n" + "\n".join(parts)
