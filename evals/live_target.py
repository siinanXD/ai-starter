"""Optional live OpenAI target. Refuses to run unless explicitly enabled."""

from __future__ import annotations

import asyncio
import os

from ai_core import OpenAIProvider, build_openai_client, wrap_untrusted

from app.schemas.analyze import AnalysisResult
from app.services.analyze import SYSTEM_PROMPT


def build_target():
    if os.getenv("RUN_OPENAI_EVAL") != "1":
        raise RuntimeError("refusing live OpenAI evals without RUN_OPENAI_EVAL=1")
    api_key = os.environ["OPENAI_API_KEY"]
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    provider = OpenAIProvider(
        build_openai_client(api_key, timeout_seconds=30),
        model,
    )

    def target(case, _provider):
        wrapped = wrap_untrusted(case.input, "eval_text")
        generation = asyncio.run(
            provider.complete_structured(SYSTEM_PROMPT, wrapped, AnalysisResult)
        )
        if not isinstance(generation.parsed, AnalysisResult):
            raise RuntimeError("live eval received no structured result")
        return generation.parsed.model_dump_json()

    return target
