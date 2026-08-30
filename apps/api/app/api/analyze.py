from ai_core import LLMProvider
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import get_provider
from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse
from app.services.analyze import analyze_text

router = APIRouter()


@router.post("/api/v1/analyze", response_model=AnalyzeResponse)
async def analyze(
    payload: AnalyzeRequest,
    db: Session = Depends(get_db),
    provider: LLMProvider = Depends(get_provider),
) -> AnalyzeResponse:
    return await analyze_text(db, provider, payload.text.strip())
