from pydantic import BaseModel, Field


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    platform: str | None = Field(default=None, pattern="^(amazon|tiktok|general)$")
    category: str | None = None
    top_k: int | None = Field(default=None, ge=1, le=20)


class KnowledgeSearchResultItem(BaseModel):
    doc_id: str
    content: str
    score: float
    category: str
    platform: str
    source_file: str
    chunk_index: int


class KnowledgeSearchResponse(BaseModel):
    query: str
    results: list[KnowledgeSearchResultItem]
    total: int


class KnowledgeStatsResponse(BaseModel):
    total_chunks: int


class KnowledgeReindexResponse(BaseModel):
    documents: int
    chunks: int
    total: int


class KnowledgeDocumentItem(BaseModel):
    source_file: str
    size_bytes: int
    extension: str
    updated_at: str


class KnowledgeDocumentsResponse(BaseModel):
    items: list[KnowledgeDocumentItem]
    total: int


class KnowledgeUploadResponse(BaseModel):
    source_file: str
    size_bytes: int
    category: str
    reindex: KnowledgeReindexResponse
