"""POST /api/suggestions"""
import logging

from fastapi import APIRouter, HTTPException
from app.models import DocumentRequest, SuggestionsResponse
from app.services.document_processor import DocumentProcessingError
from app.services.rag_pipeline import generate_suggestions

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["discovery"])
@router.post("/suggestions", response_model=SuggestionsResponse)
async def suggestions(payload: DocumentRequest) -> SuggestionsResponse:
    try:
        items = generate_suggestions(payload.document_id)
    except DocumentProcessingError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception: # noqa: BLE001
        logger.exception("Suggestion generation failed.")
        items = [] # non-critical feature: degrade, do not 500
    return SuggestionsResponse(document_id=payload.document_id, suggestions=items)