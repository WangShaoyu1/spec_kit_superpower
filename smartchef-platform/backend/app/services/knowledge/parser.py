"""Document parser: JSON/Markdown parsing, invalid field filtering, text chunking."""
import json
import re

INVALID_FIELDS = {
    "image_url", "img_url", "pic_url", "oss_url", "video_url",
    "like_count", "likes", "favorite_count", "view_count", "share_count",
    "audit_status", "review_status", "is_deleted", "is_hidden",
    "created_by_app", "app_version", "device_info", "client_ip",
}

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def filter_invalid_fields(data: dict) -> dict:
    if not isinstance(data, dict):
        return data
    filtered = {}
    for key, value in data.items():
        if key.lower() in INVALID_FIELDS:
            continue
        if isinstance(value, str) and (
            value.startswith("http://") or value.startswith("https://")
        ):
            if any(ext in value.lower() for ext in [".jpg", ".png", ".gif", ".mp4", ".oss"]):
                continue
        if isinstance(value, dict):
            value = filter_invalid_fields(value)
        elif isinstance(value, list):
            value = [filter_invalid_fields(item) if isinstance(item, dict) else item for item in value]
        filtered[key] = value
    return filtered


def parse_json_document(raw_content: str) -> tuple[str, str, dict]:
    data = json.loads(raw_content)
    if isinstance(data, list):
        data = data[0] if data else {}

    filtered = filter_invalid_fields(data)
    title = filtered.get("name", filtered.get("title", filtered.get("菜名", "未知文档")))
    content_parts = []
    metadata = {}

    for key, value in filtered.items():
        if key in ("name", "title", "菜名"):
            continue
        if isinstance(value, (dict, list)):
            content_parts.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
            metadata[key] = value
        else:
            content_parts.append(f"{key}: {value}")

    content = f"# {title}\n\n" + "\n".join(content_parts)
    return title, content, metadata


def parse_markdown_document(raw_content: str) -> tuple[str, str, dict]:
    lines = raw_content.strip().split("\n")
    title = "未知文档"
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            title = stripped.lstrip("#").strip()
            break

    json_blocks = re.findall(r'```json\s*(.*?)\s*```', raw_content, re.DOTALL)
    metadata = {}
    for block in json_blocks:
        try:
            parsed = json.loads(block)
            if isinstance(parsed, dict):
                parsed = filter_invalid_fields(parsed)
                metadata.update(parsed)
        except json.JSONDecodeError:
            pass

    return title, raw_content, metadata


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start = end - overlap

    return chunks


def parse_document(raw_content: str, source_format: str) -> tuple[str, str, dict, list[str]]:
    if source_format == "json":
        title, content, metadata = parse_json_document(raw_content)
    else:
        title, content, metadata = parse_markdown_document(raw_content)

    chunks = chunk_text(content)
    return title, content, metadata, chunks
