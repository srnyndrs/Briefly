import os
import uuid
from contextlib import contextmanager
from unittest.mock import Mock

os.environ["SENTRY_DSN"] = ""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.app import app
from src.config.database import Base, get_db
from src.config.settings import settings
from src.models.source import Source
from src.services.crawl_orchestrator import CrawlCycleOrchestrator


@pytest.fixture(autouse=True)
def isolated_boundaries_and_settings(monkeypatch):
    def unexpected_call(*args, **kwargs):
        raise AssertionError("Unexpected external HTTP, discovery, or broker call")

    monkeypatch.setattr("src.adapters.http_client.requests.get", unexpected_call)
    monkeypatch.setattr(
        "src.adapters.source_discovery.search_with_info", unexpected_call
    )
    monkeypatch.setattr(
        "src.config.message_broker.pika.BlockingConnection", unexpected_call
    )
    monkeypatch.setattr(settings, "verified_crawl_interval_seconds", 300)
    monkeypatch.setattr(settings, "unverified_crawl_interval_seconds", 1800)
    monkeypatch.setattr(settings, "max_retries", 5)
    monkeypatch.setattr(settings, "fetch_timeout_seconds", 30)
    monkeypatch.setattr(settings, "source_validation_timeout_seconds", 10)
    monkeypatch.setattr(settings, "source_validation_max_bytes", 1_048_576)


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        execution_options={"schema_translate_map": {"crawler": None}},
    )
    try:
        Base.metadata.create_all(bind=engine)
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
    monkeypatch.setattr("src.adapters.http_client.requests.get", http_get)
    publisher_factory = Mock()

    @contextmanager
    def publisher_context(**kwargs):
        publisher_factory(**kwargs)
        yield publisher

    monkeypatch.setattr(
        "src.services.crawl_orchestrator.publisher_channel",
        publisher_context,
    )
    monkeypatch.setattr(
        "src.services.crawl_orchestrator.publish_event", publisher
    )
    orchestrator = CrawlCycleOrchestrator(
        sessionmaker(bind=engine, autoflush=False)
    )
    return orchestrator, http_get, publisher, publisher_factory


@pytest.fixture
def client(db_session):
    overrides = app.dependency_overrides.copy()
    state = app.state._state.copy()
    app.state.testing = True

    def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(overrides)
        app.state._state.clear()
        app.state._state.update(state)
