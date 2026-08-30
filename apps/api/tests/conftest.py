from collections.abc import Generator

import pytest
from ai_core import CostEstimate, Generation, Usage
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db import Base, get_db
from app.core.dependencies import get_provider
from app.main import app
from app.models import AnalysisRun  # noqa: F401
from app.schemas.analyze import AnalysisResult


@pytest.fixture
def analysis_result() -> AnalysisResult:
    return AnalysisResult(
        summary="The customer is asking about an overdue invoice.",
        category="billing",
        confidence=0.91,
        suggested_action="Check the invoice due date and reply with the status.",
    )


@pytest.fixture
def generation(analysis_result: AnalysisResult) -> Generation:
    return Generation(
        text=analysis_result.model_dump_json(),
        provider="openai",
        model="gpt-4o-mini",
        latency_ms=18,
        usage=Usage(input_tokens=11, output_tokens=22, total_tokens=33),
        cost=CostEstimate("gpt-4o-mini", 11, 22, 0.0002, "known"),
        parsed=analysis_result,
    )


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


class FakeProvider:
    provider = "openai"
    model = "gpt-4o-mini"

    def __init__(self, generation: Generation) -> None:
        self._generation = generation
        self.calls: list[tuple[str, str, type]] = []

    async def complete(self, system: str, user: str) -> Generation:
        raise AssertionError("complete should not be used")

    async def complete_structured(self, system: str, user: str, schema: type) -> Generation:
        self.calls.append((system, user, schema))
        return self._generation


class FailingProvider(FakeProvider):
    async def complete_structured(self, system: str, user: str, schema: type) -> Generation:
        from ai_core import ProviderError

        raise ProviderError("upstream failed")


@pytest.fixture
def fake_provider(generation: Generation) -> FakeProvider:
    return FakeProvider(generation)


@pytest.fixture
def client(db_session: Session, fake_provider: FakeProvider) -> Generator[TestClient, None, None]:
    def _db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = _db
    app.dependency_overrides[get_provider] = lambda: fake_provider
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
