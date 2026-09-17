"""GET /api/evaluations"""

from fastapi import APIRouter, Query
from app.models import EvalListResponse, EvalRecord
from app.services.evaluator import read_evaluations

router = APIRouter(prefix="/api", tags=["evaluation"])
@router.get("/evaluations", response_model=EvalListResponse)
async def list_evaluations(limit: int = Query(50, ge=1, le=500)) -> EvalListResponse:
    raw = read_evaluations(limit=limit)
    records = []
    for item in raw:
        try:
            records.append(EvalRecord(**item))
        except Exception: # noqa: BLE001
            continue # skip malformed lines rather than failing the request
    return EvalListResponse(count=len(records), records=records)
