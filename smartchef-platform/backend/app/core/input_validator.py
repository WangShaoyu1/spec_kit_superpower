"""输入校验中间件 — 长度限制、XSS 防护、SQL 注入字段白名单。

安全加固措施：
- 请求体长度限制（默认 2048 字符）
- HTML 标签过滤（XSS 防护）
- 动态排序/筛选字段名白名单校验
"""
import re
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# HTML 标签匹配正则
_HTML_TAG_RE = re.compile(r"<[^>]+>")

# SQL 注入常见模式（用于额外检测层，SQLAlchemy ORM 已自带参数化防护）
_SQL_INJECTION_PATTERNS = re.compile(
    r"(\b(union|select|insert|update|delete|drop|alter|exec|execute|xp_|sp_)\b.*"
    r"(\b(from|into|table|where|set|values)\b))|"
    r"(--\s)|"
    r"(/\*.*?\*/)|"
    r"(;\s*(drop|delete|update|insert)\b)",
    re.IGNORECASE,
)

# 允许用于排序/筛选的字段白名单
ALLOWED_SORT_FIELDS: set[str] = {
    "id", "created_at", "updated_at", "name", "display_name",
    "intent_key", "category", "status", "priority", "score",
    "confidence", "username", "email", "role",
}

ALLOWED_FILTER_FIELDS: set[str] = ALLOWED_SORT_FIELDS | {
    "device_id", "profile_id", "session_id", "language",
    "domain", "is_active", "is_required", "entity_type",
}


class InputValidationMiddleware(BaseHTTPMiddleware):
    """请求输入校验中间件。"""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        settings = get_settings()
        self.max_length = settings.INPUT_MAX_LENGTH
        self.xss_filter = settings.INPUT_XSS_FILTER_ENABLED

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        # 只校验有请求体的方法
        if request.method in ("POST", "PUT", "PATCH"):
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > self.max_length * 4:
                logger.warning("请求体过大: %s bytes, path=%s", content_length, request.url.path)
                return JSONResponse(
                    status_code=413,
                    content={"detail": f"请求体过大，最大允许 {self.max_length * 4} 字节"},
                )

        # 校验查询参数中的排序/筛选字段
        sort_by = request.query_params.get("sort_by") or request.query_params.get("order_by")
        if sort_by and sort_by not in ALLOWED_SORT_FIELDS:
            logger.warning("非法排序字段: %s, path=%s", sort_by, request.url.path)
            return JSONResponse(
                status_code=400,
                content={"detail": f"不允许的排序字段: {sort_by}"},
            )

        filter_by = request.query_params.get("filter_by") or request.query_params.get("field")
        if filter_by and filter_by not in ALLOWED_FILTER_FIELDS:
            logger.warning("非法筛选字段: %s, path=%s", filter_by, request.url.path)
            return JSONResponse(
                status_code=400,
                content={"detail": f"不允许的筛选字段: {filter_by}"},
            )

        return await call_next(request)


# ---------------------------------------------------------------------------
# 工具函数：可在各 API 层直接调用
# ---------------------------------------------------------------------------

def sanitize_input(text: str, max_length: int | None = None) -> str:
    """清洗用户输入文本：截断 + 去除 HTML 标签。

    Args:
        text: 原始用户输入
        max_length: 最大长度（None 则使用配置默认值）

    Returns:
        清洗后的安全文本
    """
    if max_length is None:
        max_length = get_settings().INPUT_MAX_LENGTH
    text = text[:max_length]
    text = strip_html_tags(text)
    return text.strip()


def strip_html_tags(text: str) -> str:
    """去除文本中的 HTML 标签（XSS 防护）。"""
    return _HTML_TAG_RE.sub("", text)


def validate_sort_field(field_name: str) -> bool:
    """校验排序字段是否在白名单中。"""
    return field_name in ALLOWED_SORT_FIELDS


def validate_filter_field(field_name: str) -> bool:
    """校验筛选字段是否在白名单中。"""
    return field_name in ALLOWED_FILTER_FIELDS


def check_sql_injection(text: str) -> bool:
    """检测文本是否包含可疑的 SQL 注入模式。

    注意：这是额外的防御层，SQLAlchemy ORM 的参数化查询已提供基础防护。

    Returns:
        True 表示检测到可疑内容
    """
    return bool(_SQL_INJECTION_PATTERNS.search(text))
