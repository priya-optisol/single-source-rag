"""POST /api/query"""

import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.models import QueryRequest, QueryResponse
from app.services.document_processor import DocumentProcessingError
from app.services.evaluator import evaluate_and_log
from app.services.rag_pipeline import answer_question

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["query"])
@router.post("/query", response_model=QueryResponse)
async def query_document(
payload: QueryRequest,
background: BackgroundTasks,
) -> QueryResponse:
    try:
        result = answer_question(payload.document_id, payload.question)
    except DocumentProcessingError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc: # noqa: BLE001
        logger.exception("Query failed.")
        raise HTTPException(status_code=500, detail="Query failed.") from exc
    # Fire-and-forget: the response is already on its way to the user.
    if payload.evaluate and result["grounded"]:
        background.add_task(
        evaluate_and_log,
        document_id=payload.document_id,
        question=payload.question,
        answer=result["answer"],
        contexts=result["contexts"],
        )
    return QueryResponse(
    answer=result["answer"],
    sources=result["sources"],
    document_id=payload.document_id,
    question=payload.question,
    latency_ms=result["latency_ms"],
    grounded=result["grounded"],
    )