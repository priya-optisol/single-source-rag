"""POST /api/topics"""

import logging

from fastapi import APIRouter, HTTPException
from app.models import DocumentRequest, Topic, TopicsResponse
from app.services.document_processor import DocumentProcessingError
from app.services.rag_pipeline import extract_topics

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["discovery"])
@router.post("/topics", response_model=TopicsResponse)
async def topics(payload: DocumentRequest) -> TopicsResponse:
    try:
        items = extract_topics(payload.document_id)
    except DocumentProcessingError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception: # noqa: BLE001
        logger.exception("Topic extraction failed.")
        items = []
    return TopicsResponse(
    document_id=payload.document_id,
    topics=[Topic(**t) for t in items],
    )