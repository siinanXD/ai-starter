import hashlib

from ai_core import ProviderError
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.dependencies import get_provider
from app.main import app
from app.models.analysis import AnalysisRun
from app.schemas.analyze import AnalysisResult
from tests.conftest import FailingProvider, FakeProvider

UNIQUE = "UNIQUE-CUSTOMER-PHRASE-invoice-overdue-xyz"


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


def test_database_persists_metadata_only(client: TestClient, db_session: Session) -> None:
    response = client.post("/api/v1/analyze", json={"text": UNIQUE})
    assert response.status_code == 200
    rows = db_session.query(AnalysisRun).all()
    assert len(rows) == 1
    row = rows[0]
    assert row.input_hash == hashlib.sha256(UNIQUE.encode("utf-8")).hexdigest()
    assert row.category == "billing"
    assert row.summary
    dumped = " ".join(
        str(value)
        for value in (
            row.id,
            row.input_hash,
            row.category,
            row.summary,
            row.confidence,
            row.suggested_action,
            row.model,
            row.latency_ms,
            row.input_tokens,
            row.output_tokens,
            row.estimated_cost_usd,
            row.created_at,
        )
    )
    assert UNIQUE not in dumped
    assert UNIQUE.lower() not in dumped.lower()


def test_provider_error_type_is_ai_core() -> None:
    assert issubclass(ProviderError, Exception)
