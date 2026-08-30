from ai_core import ProviderError, RetryExhaustedError, StructuredOutputError
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.analyze import router as analyze_router
from app.api.health import router as health_router
from app.core.dependencies import OpenAINotConfiguredError
from app.core.settings import get_settings

app = FastAPI(title="ai-starter", version="0.1.0")
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.include_router(health_router)
app.include_router(analyze_router)


async def _provider_failed(_request: Request, _exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=502, content={"detail": "provider_failed"})


for _exc in (ProviderError, RetryExhaustedError, StructuredOutputError):
    app.add_exception_handler(_exc, _provider_failed)


@app.exception_handler(OpenAINotConfiguredError)
async def openai_not_configured(_request: Request, _exc: OpenAINotConfiguredError) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": "openai_not_configured"})
