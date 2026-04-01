import json
import re
import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crypto import decrypt_json, decrypt_text, encrypt_json, encrypt_text
from app.dependencies import ApiError, create_audit_log, get_db, require_capability, response_envelope, utc_now
from app.models import KnowledgeCategory, KnowledgeDocument, KnowledgeRetrievalProbe, UserAccount


router = APIRouter(tags=["knowledge-base"])

ASYNC_SETTLE_SECONDS = 0.05
JSON_VALID_KEYS = {
    "recipe_name",
    "description",
    "main_ingredients",
    "sub_ingredients",
    "ingredients",
    "steps",
    "nutrition",
    "cooking_tools",
    "tags",
    "cooking_time",
}
INVALID_FIELD_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"image|photo|thumbnail|avatar",
        r"oss|s3|cos",
        r"like_count|share_count|comment_count|view_count|favorite_count",
        r"review_status|audit_status|approval",
    ]
]


class CategoryPayload(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    icon: str = Field(min_length=1, max_length=8)
    description: str = Field(default="", max_length=200)


class UploadDocumentPayload(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    format: str
    content: str = Field(min_length=1)


class ReindexPayload(BaseModel):
    reason: str | None = None


class RetrieveTestPayload(BaseModel):
    query: str = Field(min_length=1, max_length=300)


def parse_json_field(payload: str | None, fallback: Any):
    if not payload:
        return fallback
    return decrypt_json(payload, fallback)


def serialize_category(category: KnowledgeCategory) -> dict[str, Any]:
    return {
        "id": category.id,
        "name": category.name,
        "icon": category.icon,
        "description": category.description,
        "document_count": category.document_count,
        "ready_document_count": category.ready_document_count,
        "status": category.status,
    }


def serialize_document(document: KnowledgeDocument) -> dict[str, Any]:
    return {
        "id": document.id,
        "category_id": document.category_id,
        "name": document.name,
        "format": document.format,
        "size_bytes": document.size_bytes,
        "status": document.status,
        "index_version": document.index_version,
        "created_at": document.created_at.isoformat() + "Z",
    }


def get_category_or_404(session: Session, category_id: str) -> KnowledgeCategory:
    category = session.get(KnowledgeCategory, category_id)
    if category is None:
        raise ApiError(404, "KB-CAT-404-NOT-FOUND", "目标分类不存在")
    return category


def get_document_or_404(session: Session, document_id: str) -> KnowledgeDocument:
    document = session.get(KnowledgeDocument, document_id)
    if document is None:
        raise ApiError(404, "KB-DOC-404-NOT-FOUND", "目标文档不存在")
    return document


def update_category_summary(session: Session, category_id: str):
    category = get_category_or_404(session, category_id)
    docs = session.execute(
        select(KnowledgeDocument).where(KnowledgeDocument.category_id == category_id)
    ).scalars().all()
    category.document_count = len(docs)
    ready_count = sum(1 for doc in docs if doc.status == "ready")
    category.ready_document_count = ready_count
    if not docs:
        category.status = "empty"
    elif any(doc.status in {"uploading", "parsing", "indexing"} for doc in docs):
        category.status = "indexing"
    elif all(doc.status == "ready" for doc in docs):
        category.status = "ready"
    else:
        category.status = "indexing"


def filter_json_fields(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    valid_content: list[dict[str, Any]] = []
    filtered_fields: list[dict[str, Any]] = []
    for field, value in payload.items():
        if field in JSON_VALID_KEYS:
            valid_content.append({"field": field, "value": value})
            continue
        if any(pattern.search(field) for pattern in INVALID_FIELD_PATTERNS):
            filtered_fields.append({"field": field, "value": value, "reason": "filtered"})
            continue
        filtered_fields.append({"field": field, "value": value, "reason": "non_qa_field"})
    return valid_content, filtered_fields


def parse_markdown_sections(content: str) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    current_heading = "正文"
    buffer: list[str] = []
    for line in content.splitlines():
        if line.startswith("#"):
            if buffer:
                sections.append({"field": current_heading, "value": "\n".join(buffer).strip()})
                buffer = []
            current_heading = line.lstrip("#").strip() or "正文"
        elif line.strip():
            buffer.append(line.strip())
    if buffer:
        sections.append({"field": current_heading, "value": "\n".join(buffer).strip()})
    if not sections:
        sections.append({"field": "正文", "value": content.strip()})
    return sections


def process_document(document: KnowledgeDocument):
    if document.status not in {"uploading", "indexing"}:
        return False
    if (utc_now() - document.updated_at).total_seconds() < ASYNC_SETTLE_SECONDS:
        return False

    document.status = "parsing"
    content = (decrypt_text(document.source_text) or "").strip()
    if not content:
        document.status = "failed"
        document.error_summary = "文档内容为空"
        return True

    try:
        if document.format == "json":
            payload = json.loads(content)
            if not isinstance(payload, dict):
                raise ValueError("json payload must be object")
            valid_content, filtered_fields = filter_json_fields(payload)
        else:
            valid_content = parse_markdown_sections(content)
            filtered_fields = []
    except Exception:
        document.status = "failed"
        document.error_summary = "文档解析失败"
        return True

    document.valid_content_json = encrypt_json(valid_content)
    document.filtered_fields_json = encrypt_json(filtered_fields)
    document.error_summary = None
    document.status = "ready"
    document.index_version += 1
    return True


def advance_knowledge_state(session: Session, category_id: str | None = None):
    query = select(KnowledgeDocument)
    if category_id:
        query = query.where(KnowledgeDocument.category_id == category_id)
    documents = session.execute(query).scalars().all()
    changed = False
    touched_categories = {doc.category_id for doc in documents}
    for document in documents:
        changed = process_document(document) or changed
    for touched_category in touched_categories:
        update_category_summary(session, touched_category)
    if changed:
        session.commit()


def render_snippet(value: str, query: str) -> str:
    index = value.lower().find(query.lower())
    if index == -1:
        return value[:120]
    start = max(0, index - 20)
    end = min(len(value), index + len(query) + 40)
    return value[start:end]


@router.get("/knowledge-bases")
def list_knowledge_bases(
    request: Request,
    category_id: str | None = Query(default=None),
    _: UserAccount = Depends(require_capability("knowledge_write")),
    session: Session = Depends(get_db),
):
    advance_knowledge_state(session, category_id)
    categories = session.execute(select(KnowledgeCategory).order_by(KnowledgeCategory.created_at)).scalars().all()
    if category_id:
        documents = session.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.category_id == category_id).order_by(KnowledgeDocument.created_at)
        ).scalars().all()
    else:
        documents = []
    return response_envelope(
        request,
        data={
            "categories": [serialize_category(item) for item in categories],
            "documents": [serialize_document(item) for item in documents],
        },
    )


@router.post("/knowledge-bases/categories")
def create_category(
    payload: CategoryPayload,
    request: Request,
    actor: UserAccount = Depends(require_capability("knowledge_write")),
    session: Session = Depends(get_db),
):
    existing = session.execute(select(KnowledgeCategory).where(KnowledgeCategory.name == payload.name)).scalar_one_or_none()
    if existing is not None:
        raise ApiError(409, "KB-CAT-409-NAME", "分类名称已存在，请更换后重试")
    category = KnowledgeCategory(
        id=uuid.uuid4().hex,
        name=payload.name,
        icon=payload.icon,
        description=payload.description,
        status="empty",
    )
    session.add(category)
    create_audit_log(session, actor.id, category.id, "knowledge_category_created", {"name": payload.name})
    session.commit()
    return response_envelope(request, data={"category": serialize_category(category)})


@router.patch("/knowledge-bases/categories/{category_id}")
def update_category(
    category_id: str,
    payload: CategoryPayload,
    request: Request,
    actor: UserAccount = Depends(require_capability("knowledge_write")),
    session: Session = Depends(get_db),
):
    category = get_category_or_404(session, category_id)
    existing = session.execute(
        select(KnowledgeCategory).where(KnowledgeCategory.name == payload.name, KnowledgeCategory.id != category_id)
    ).scalar_one_or_none()
    if existing is not None:
        raise ApiError(409, "KB-CAT-409-NAME", "分类名称已存在，请更换后重试")
    before = category.name
    category.name = payload.name
    category.icon = payload.icon
    category.description = payload.description
    create_audit_log(session, actor.id, category.id, "knowledge_category_updated", {"before": before, "after": payload.name})
    session.commit()
    return response_envelope(request, data={"category": serialize_category(category)})


@router.post("/knowledge-bases/{category_id}/documents/upload")
def upload_document(
    category_id: str,
    payload: UploadDocumentPayload,
    request: Request,
    actor: UserAccount = Depends(require_capability("knowledge_write")),
    session: Session = Depends(get_db),
):
    category = get_category_or_404(session, category_id)
    if payload.format not in {"json", "markdown"}:
        raise ApiError(422, "KB-DOC-422-FORMAT", "仅支持 JSON / Markdown 文档")
    if not payload.content.strip():
        raise ApiError(422, "KB-DOC-422-EMPTY", "文档内容为空，无法建立索引")

    document = KnowledgeDocument(
        id=uuid.uuid4().hex,
        category_id=category.id,
        name=payload.name,
        format=payload.format,
        size_bytes=len(payload.content.encode("utf-8")),
        status="uploading",
        source_text=encrypt_text(payload.content),
    )
    session.add(document)
    update_category_summary(session, category.id)
    create_audit_log(session, actor.id, document.id, "knowledge_document_uploaded", {"name": payload.name})
    session.commit()
    return response_envelope(request, data={"document": serialize_document(document)})


@router.get("/knowledge-documents/{document_id}")
def get_document_detail(
    document_id: str,
    request: Request,
    _: UserAccount = Depends(require_capability("knowledge_write")),
    session: Session = Depends(get_db),
):
    document = get_document_or_404(session, document_id)
    advance_knowledge_state(session, document.category_id)
    document = get_document_or_404(session, document_id)
    probes = session.execute(
        select(KnowledgeRetrievalProbe).where(KnowledgeRetrievalProbe.document_id == document_id).order_by(KnowledgeRetrievalProbe.created_at.desc())
    ).scalars().all()
    return response_envelope(
        request,
        data={
            "document": serialize_document(document),
            "valid_content": parse_json_field(document.valid_content_json, []),
            "filtered_fields": parse_json_field(document.filtered_fields_json, []),
            "probes": [
                {
                    "query": item.query,
                    "hit": item.hit,
                    "score": item.score,
                    "snippet": item.snippet,
                    "response_preview": item.response_preview,
                }
                for item in probes
            ],
        },
    )


@router.post("/knowledge-documents/{document_id}/reindex")
def reindex_document(
    document_id: str,
    payload: ReindexPayload,
    request: Request,
    actor: UserAccount = Depends(require_capability("knowledge_write")),
    session: Session = Depends(get_db),
):
    del payload
    document = get_document_or_404(session, document_id)
    if document.status in {"uploading", "parsing", "indexing"}:
        raise ApiError(409, "KB-DOC-409-REINDEX", "当前文档正在处理，请稍后再试")
    document.status = "indexing"
    document.updated_at = utc_now()
    create_audit_log(session, actor.id, document.id, "knowledge_document_reindexed", {"index_version": document.index_version + 1})
    update_category_summary(session, document.category_id)
    session.commit()
    return response_envelope(request, data={"document": serialize_document(document)})


@router.post("/knowledge-documents/{document_id}/retrieve-test")
def retrieve_test(
    document_id: str,
    payload: RetrieveTestPayload,
    request: Request,
    _: UserAccount = Depends(require_capability("knowledge_write")),
    session: Session = Depends(get_db),
):
    document = get_document_or_404(session, document_id)
    advance_knowledge_state(session, document.category_id)
    document = get_document_or_404(session, document_id)
    if document.status != "ready":
        raise ApiError(409, "KB-DOC-409-REINDEX", "当前文档尚未完成索引")
    query = payload.query.strip()
    if not query:
        raise ApiError(422, "KB-RETRIEVE-422-QUERY", "请输入检索内容")

    valid_content = parse_json_field(document.valid_content_json, [])
    best_match = None
    best_score = 0.0
    for item in valid_content:
        value = item.get("value")
        if isinstance(value, list):
            text = " ".join(str(part) for part in value)
        else:
            text = str(value)
        score = 1.0 if query.lower() in text.lower() else 0.0
        if query in text:
            score += len(query) / max(len(text), 1)
        if score > best_score:
            best_score = score
            best_match = text

    hit = best_match is not None and best_score > 0
    snippet = render_snippet(best_match or "", query) if hit else ""
    response_preview = f"命中文档片段：{snippet}" if hit else "未命中当前文档内容"
    probe = KnowledgeRetrievalProbe(
        id=uuid.uuid4().hex,
        document_id=document.id,
        query=query,
        hit=hit,
        score=round(best_score, 4) if hit else 0.0,
        snippet=snippet or None,
        response_preview=response_preview,
    )
    session.add(probe)
    session.commit()
    return response_envelope(
        request,
        data={
            "hit": hit,
            "score": probe.score,
            "snippet": probe.snippet or "",
            "response_preview": probe.response_preview,
        },
    )


@router.delete("/knowledge-documents/{document_id}")
def delete_document(
    document_id: str,
    request: Request,
    actor: UserAccount = Depends(require_capability("knowledge_write")),
    session: Session = Depends(get_db),
):
    document = get_document_or_404(session, document_id)
    category_id = document.category_id
    probes = session.execute(
        select(KnowledgeRetrievalProbe).where(KnowledgeRetrievalProbe.document_id == document_id)
    ).scalars().all()
    for probe in probes:
        session.delete(probe)
    session.flush()  # PG 外键：先落地删除 probe，再删 document
    session.delete(document)
    create_audit_log(session, actor.id, document_id, "knowledge_document_deleted", {"category_id": category_id})
    session.flush()
    update_category_summary(session, category_id)
    session.commit()
    return response_envelope(request, data={"deleted": True, "document_id": document_id})
