from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

Category = Literal["billing", "support", "sales", "legal", "other"]


class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)

    @field_validator("text")
    @classmethod
    def text_not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("text must not be blank")
        return stripped


class AnalysisResult(BaseModel):
    """Structured model output. Used by ai-core complete_structured."""

    summary: str = Field(min_length=1, max_length=1000)
    category: Category
    confidence: float = Field(ge=0, le=1)
    suggested_action: str = Field(min_length=1, max_length=1000)


class AnalyzeResponse(BaseModel):
    id: UUID
    summary: str
    category: Category
    confidence: float
    suggested_action: str
    model: str
    latency_ms: int
    input_tokens: int | None
    output_tokens: int | None
    estimated_cost_usd: float | None
    created_at: datetime
