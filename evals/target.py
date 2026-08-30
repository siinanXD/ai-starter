"""Deterministic harness target. Calls analyze_text. No paid API calls."""

from __future__ import annotations

import asyncio

from ai_core import CostEstimate, Generation, Usage

from app.schemas.analyze import AnalysisResult, Category
from app.services.analyze import analyze_text
from evals.db import memory_session

_RULES: tuple[tuple[tuple[str, ...], Category, str, str], ...] = (
    (
        ("invoice", "overdue", "payment", "refund", "billing"),
        "billing",
        "The message is about billing or payment.",
        "Review the invoice or payment record and reply with the status.",
    ),
    (
        ("login", "password", "access", "error", "support"),
        "support",
        "The message is a product support request.",
        "Open a support ticket and ask for the account identifier.",
    ),
    (
        ("pricing", "demo", "plan", "upgrade", "sales"),
        "sales",
        "The message is a sales or pricing inquiry.",
        "Share the relevant plan details and offer a follow-up call.",
    ),
    (
        ("nda", "contract", "legal", "compliance"),
        "legal",
        "The message needs a legal review.",
        "Route the request to legal before making a commitment.",
    ),
)


def classify(text: str) -> AnalysisResult:
    lowered = text.lower()
    for keywords, category, summary, action in _RULES:
        if any(word in lowered for word in keywords):
            return AnalysisResult(
                summary=summary,
                category=category,
                confidence=0.86,
                suggested_action=action,
            )
    return AnalysisResult(
        summary="The message does not match a more specific category.",
        category="other",
        confidence=0.55,
        suggested_action="Ask the customer for one clarifying sentence.",
    )


class _DeterministicProvider:
    provider = "openai"
    model = "eval-fake"

    async def complete(self, system: str, user: str) -> Generation:
        raise AssertionError("complete should not be used")

    async def complete_structured(self, system: str, user: str, schema: type) -> Generation:
        parsed = classify(user)
        return Generation(
            text=parsed.model_dump_json(),
            provider=self.provider,
            model=self.model,
            latency_ms=1,
            usage=Usage(input_tokens=1, output_tokens=1, total_tokens=2),
            cost=CostEstimate(self.model, 1, 1, None, "unknown"),
            parsed=parsed,
        )


def build_target():
    provider = _DeterministicProvider()

    def target(case, _provider):
        session = memory_session()
        try:
            result = asyncio.run(analyze_text(session, provider, case.input))
            return result.model_dump_json()
        finally:
            session.close()

    return target
