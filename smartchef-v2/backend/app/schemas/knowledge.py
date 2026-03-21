"""Pydantic schemas for Knowledge Base module."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# KnowledgeCategory
# ---------------------------------------------------------------------------

class CreateCategoryRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    parent_id: UUID | None = None
    sort_order: int = Field(0, ge=0)


class UpdateCategoryRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    parent_id: UUID | None = None
    sort_order: int | None = Field(None, ge=0)


class CategoryResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    parent_id: UUID | None
    sort_order: int
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime
    children: list["CategoryResponse"] = []
    document_count: int = 0


# ---------------------------------------------------------------------------
# KnowledgeDocument
# ---------------------------------------------------------------------------

class UpdateDocumentRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    category_id: UUID | None = None


class DocumentResponse(BaseModel):
    id: UUID
    title: str
    category_id: UUID | None
    category_name: str | None = None
    file_path: str
    file_type: str
    file_size: int
    status: str
    chunk_count: int
    error_message: str | None
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime


class DocumentDetailResponse(DocumentResponse):
    chunks: list["ChunkResponse"] = []


# ---------------------------------------------------------------------------
# DocumentChunk
# ---------------------------------------------------------------------------

class ChunkResponse(BaseModel):
    id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    token_count: int
    created_at: datetime


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    category_id: UUID | None = None
    top_k: int = Field(10, ge=1, le=50)


class SearchHit(BaseModel):
    chunk_id: UUID
    document_id: UUID
    document_title: str
    chunk_index: int
    content: str
    score: float
