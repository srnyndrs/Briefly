import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

os.environ["SENTRY_DSN"] = ""

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def postgres_engine():
    from unittest.mock import patch

    from src.config import database

    url = os.environ.get("PUBLIC_API_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set PUBLIC_API_TEST_DATABASE_URL for PostgreSQL checks")
    engine = create_engine(url)
    try:
        with patch.object(database, "engine", engine):
            database.init_db()
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def postgres_db(postgres_engine):
    with postgres_engine.connect() as connection:
        transaction = connection.begin()
        try:
            with Session(
                connection, join_transaction_mode="create_savepoint"
            ) as db:
                yield db
        finally:
            transaction.rollback()


@pytest.fixture
def session_factory():
    from src.models.read_models import Base

    # Avoid pytest's shared temp root, which can have stale Windows permissions.
    with TemporaryDirectory(prefix="public-api-tests-") as directory:
        engine = create_engine(
            f"sqlite:///{(Path(directory) / 'query.db').as_posix()}",
            connect_args={"check_same_thread": False},
            execution_options={"schema_translate_map": {"query": None}},
        )
        try:
            Base.metadata.create_all(engine)
            yield sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
        finally:
            engine.dispose()


@pytest.fixture
def db(session_factory):
    with session_factory() as session:
        yield session


@pytest.fixture(autouse=True)
def reject_upstream_http(monkeypatch):
    original = httpx.Client.send

    def send(client, request, *args, **kwargs):
        from fastapi.testclient import TestClient

        if isinstance(client, TestClient):
            return original(client, request, *args, **kwargs)
        raise AssertionError(
            f"Unexpected upstream HTTP: {request.method} {request.url}"
        )

    monkeypatch.setattr(httpx.Client, "send", send)
