from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: str | None = None


class KnowledgeBaseInfo(BaseModel):
    id: UUID
    name: str
    description: str | None
    document_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeBaseUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class DocumentChunkInfo(BaseModel):
    id: UUID
    chunk_text: str
    chunk_index: int

    model_config = {"from_attributes": True}


class KnowledgeDocumentInfo(BaseModel):
    id: UUID
    title: str
    content: str
    source_format: str
    source_filename: str | None
    metadata_: dict | None = Field(None, alias="metadata_")
    index_status: str
    chunk_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    knowledge_base_id: UUID | None = None
    top_k: int = Field(5, ge=1, le=20)


class KnowledgeSearchResult(BaseModel):
    document_id: UUID
    document_title: str
    chunk_text: str
    score: float
