import os
import uuid
from unittest.mock import Mock

os.environ["SENTRY_DSN"] = ""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.app import app
from src.config.database import Base, get_db
from src.models.source import Source
from src.services.crawl_orchestrator import CrawlCycleOrchestrator


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        execution_options={"schema_translate_map": {"crawler": None}},
    )
    Base.metadata.create_all(bind=engine)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def db_session(engine):
    with Session(engine, autoflush=False) as session:
        yield session


@pytest.fixture
def source_factory(db_session):
    def create_source(**values):
        source = Source(
            **{
                "url": f"https://example.com/{uuid.uuid4()}/feed",
                "title": "Example",
                "registrable_domain": "example.com",
            }
            | values
        )
        db_session.add(source)
        db_session.commit()
        db_session.refresh(source)
        return source

    return create_source


@pytest.fixture
def crawl_cycle(engine, monkeypatch):
    response = Mock(
        status_code=200,
        text="<feed/>",
        headers={"ETag": "fresh", "Last-Modified": "new-date"},
    )
    http_get = Mock(return_value=response)
    publisher = Mock()
    monkeypatch.setattr(
        "src.adapters.http_client.requests.get", http_get
    )
    monkeypatch.setattr(
        "src.services.crawl_orchestrator.FeedPublisher",
        Mock(return_value=publisher),
    )
    orchestrator = CrawlCycleOrchestrator(
        sessionmaker(bind=engine, autoflush=False)
    )
    return orchestrator, http_get, publisher


@pytest.fixture
def client(db_session):
    app.state.testing = True

    def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        app.state.testing = False
