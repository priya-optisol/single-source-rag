"""POST /api/upload"""
import logging

from fastapi import APIRouter, File, HTTPException, UploadFile
from app.config import settings
from app.models import UploadResponse
from app.services.document_processor import DocumentProcessingError, ingest_pdf

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["upload"])

@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf files are accepted.")
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(contents) > settings.max_upload_bytes:
        raise HTTPException(
        status_code=413,
        detail=f"File exceeds the {settings.max_upload_mb} MB limit.",
        )
# PDFs start with the magic bytes %PDF
    if not contents.startswith(b"%PDF-"):
        raise HTTPException(
        status_code=400,
        detail="This does not look like a valid PDF.",
        )
    try:
        result = ingest_pdf(contents, file.filename)
    except DocumentProcessingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc: # noqa: BLE001
        logger.exception("Unexpected upload failure.")
        raise HTTPException(status_code=500, detail="Failed to process document.") from exc
    return UploadResponse(**result)