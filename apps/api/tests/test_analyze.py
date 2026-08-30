import hashlib

from ai_core import ProviderError, RetryExhaustedError, StructuredOutputError
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import get_provider
from app.core.settings import Settings
from app.main import app
from app.models.analysis import AnalysisRun
from app.schemas.analyze import AnalysisResult
from tests.conftest import FailingProvider, FakeProvider

UNIQUE = "UNIQUE-CUSTOMER-PHRASE-invoice-overdue-xyz"


def _row_dump(row: AnalysisRun) -> str:
    return " ".join(
        str(value)
        for value in (
            row.id,
            row.input_hash,
            row.category,
            row.confidence,
            row.model,
            row.latency_ms,
            row.input_tokens,
            row.output_tokens,
            row.estimated_cost_usd,
            row.created_at,
        )
    )


def test_analyze_valid(client: TestClient, fake_provider: FakeProvider) -> None:
    response = client.post("/api/v1/analyze", json={"text": UNIQUE})
    assert response.status_code == 200
    body = response.json()
    assert body["summary"]
    assert body["category"] == "billing"
    assert 0 <= body["confidence"] <= 1
    assert body["suggested_action"]
    assert body["model"] == "gpt-4o-mini"
    assert body["latency_ms"] == 18
    assert body["input_tokens"] == 11
    assert body["output_tokens"] == 22
    assert body["estimated_cost_usd"] == 0.0002
    assert len(fake_provider.calls) == 1
    system, user, schema = fake_provider.calls[0]
    assert "untrusted data" in system.lower() or "untrusted" in system.lower()
    assert "UNTRUSTED-" in user
    assert 'trust="untrusted-external"' in user
    assert schema is AnalysisResult


def test_analyze_invalid_empty_text(client: TestClient) -> None:
    response = client.post("/api/v1/analyze", json={"text": "   "})
    assert response.status_code == 422


def test_analyze_invalid_missing_text(client: TestClient) -> None:
    response = client.post("/api/v1/analyze", json={})
    assert response.status_code == 422


def test_analyze_invalid_too_long(client: TestClient) -> None:
    response = client.post("/api/v1/analyze", json={"text": "x" * 4001})
    assert response.status_code == 422


def test_provider_failure(client: TestClient, generation) -> None:
    app.dependency_overrides[get_provider] = lambda: FailingProvider(generation)
    response = client.post("/api/v1/analyze", json={"text": UNIQUE})
    assert response.status_code == 502
    assert response.json() == {"detail": "provider_failed"}
    assert UNIQUE not in response.text


def test_retry_exhausted_is_provider_failure(client: TestClient, generation) -> None:
    class ExhaustingProvider(FakeProvider):
        async def complete_structured(self, system: str, user: str, schema: type):
            raise RetryExhaustedError(
                "gave up after 3 attempts: APITimeoutError",
                attempts=3,
                last_error=TimeoutError("APITimeoutError"),
            )

    app.dependency_overrides[get_provider] = lambda: ExhaustingProvider(generation)
    response = client.post("/api/v1/analyze", json={"text": UNIQUE})
    assert response.status_code == 502
    assert response.json() == {"detail": "provider_failed"}


def test_structured_output_error_is_provider_failure(client: TestClient, generation) -> None:
    class BadStructuredProvider(FakeProvider):
        async def complete_structured(self, system: str, user: str, schema: type):
            raise StructuredOutputError("could not parse")

    app.dependency_overrides[get_provider] = lambda: BadStructuredProvider(generation)
    response = client.post("/api/v1/analyze", json={"text": UNIQUE})
    assert response.status_code == 502
    assert response.json() == {"detail": "provider_failed"}


def test_structured_output_missing_is_provider_failure(
    client: TestClient,
    generation,
) -> None:
    broken = FakeProvider(
        generation.__class__(
            text="not-json",
            provider=generation.provider,
            model=generation.model,
            latency_ms=generation.latency_ms,
            usage=generation.usage,
            cost=generation.cost,
            parsed=None,
        )
    )
    app.dependency_overrides[get_provider] = lambda: broken
    response = client.post("/api/v1/analyze", json={"text": UNIQUE})
    assert response.status_code == 502
    assert response.json() == {"detail": "provider_failed"}


def test_missing_openai_key_returns_503(db_session: Session, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.core.dependencies.get_settings",
        lambda: Settings(openai_api_key="", database_url="sqlite://"),
    )
    get_provider.cache_clear()

    def _db():
        yield db_session

    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = _db
    with TestClient(app) as test_client:
        response = test_client.post("/api/v1/analyze", json={"text": UNIQUE})
    app.dependency_overrides.clear()
    get_provider.cache_clear()
    assert response.status_code == 503
    assert response.json() == {"detail": "openai_not_configured"}


def test_database_persists_metadata_only(client: TestClient, db_session: Session) -> None:
    response = client.post("/api/v1/analyze", json={"text": UNIQUE})
    assert response.status_code == 200
    rows = db_session.query(AnalysisRun).all()
    assert len(rows) == 1
    row = rows[0]
    assert row.input_hash == hashlib.sha256(UNIQUE.encode("utf-8")).hexdigest()
    assert row.category == "billing"
    assert not hasattr(row, "summary")
    assert UNIQUE not in _row_dump(row)


def test_echoed_customer_text_is_not_persisted(
    client: TestClient,
    db_session: Session,
    generation,
) -> None:
    echoed = AnalysisResult(
        summary=UNIQUE,
        category="billing",
        confidence=0.4,
        suggested_action=f"sk-test-secret-{UNIQUE}",
    )
    app.dependency_overrides[get_provider] = lambda: FakeProvider(
        generation.__class__(
            text=echoed.model_dump_json(),
            provider=generation.provider,
            model=generation.model,
            latency_ms=generation.latency_ms,
            usage=generation.usage,
            cost=generation.cost,
            parsed=echoed,
        )
    )
    response = client.post("/api/v1/analyze", json={"text": UNIQUE})
    assert response.status_code == 200
    assert response.json()["summary"] == UNIQUE
    row = db_session.query(AnalysisRun).one()
    dumped = _row_dump(row)
    assert UNIQUE not in dumped
    assert "sk-test-secret" not in dumped


def test_provider_error_type_is_ai_core() -> None:
    assert issubclass(ProviderError, Exception)
