from ai_core import ProviderError
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.analyze import router as analyze_router
from app.api.health import router as health_router
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


@app.exception_handler(ProviderError)
async def provider_failed(_request: Request, _exc: ProviderError) -> JSONResponse:
    return JSONResponse(status_code=502, content={"detail": "provider_failed"})
