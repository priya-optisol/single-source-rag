"""Pydantic request/response schemas."""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field
# --------------------------------------------------------------------------
# Upload
# --------------------------------------------------------------------------

class UploadResponse(BaseModel):
    document_id: str = Field(..., description="Server-generated UUID for this document")
    filename: str
    pages: int
    chunks: int
    message: str = "Document indexed successfully."

# --------------------------------------------------------------------------
# Query
# --------------------------------------------------------------------------
class QueryRequest(BaseModel):
    document_id: str = Field(..., min_length=8, max_length=64)
    question: str = Field(..., min_length=3, max_length=2000)
    evaluate: bool = Field(True, description="Run RAGAS scoring in the background")

class SourceChunk(BaseModel):
    text: str
    page: int | None = None
    chunk_index: int
    rerank_score: float
    vector_rank: int = Field(..., description="Position in the pre-rerank FAISS results")

class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
    document_id: str
    question: str
    latency_ms: int
    grounded: bool = Field(
        True,
        description="False when the pipeline could not find supporting context",
        )
    
# --------------------------------------------------------------------------
# Suggestions / topics
# --------------------------------------------------------------------------
class DocumentRequest(BaseModel):
    document_id: str = Field(..., min_length=8, max_length=64)

class SuggestionsResponse(BaseModel):
    document_id: str
    suggestions: list[str]

class Topic(BaseModel):
    title: str
    summary: str

class TopicsResponse(BaseModel):
    document_id: str
    topics: list[Topic]
# --------------------------------------------------------------------------
# Evaluation
# --------------------------------------------------------------------------
class EvalMetrics(BaseModel):
    faithfulness: float | None = None
    answer_relevancy: float | None = None
    context_precision: float | None = None

class EvalRecord(BaseModel):
    timestamp: datetime
    document_id: str
    question: str
    answer_preview: str
    num_sources: int
    metrics: EvalMetrics
    status: Literal["ok", "error"] = "ok"
    error: str | None = None

class EvalListResponse(BaseModel):
    count: int
    records: list[EvalRecord]
# --------------------------------------------------------------------------
# Misc
# --------------------------------------------------------------------------
class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    embedding_model: str
    llm_model: str