"""Deterministic harness target. No paid API calls."""

from __future__ import annotations

from app.schemas.analyze import AnalysisResult, Category

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


def build_target():
    def target(case, _provider):
        return classify(case.input).model_dump_json()

    return target
