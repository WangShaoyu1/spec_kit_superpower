"""LLM adapter: unified interface via ZenMux OpenAI SDK."""
import logging
from openai import AsyncOpenAI
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def get_llm_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=settings.ZENMUX_API_KEY,
        base_url=settings.ZENMUX_BASE_URL,
    )


async def chat_completion(
    messages: list[dict],
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    max_tokens: int = 512,
) -> str:
    """Call LLM via ZenMux gateway and return response text."""
    try:
        client = get_llm_client()
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return "抱歉，暂时无法生成回复，请稍后再试。"
