from collections.abc import Generator

import pytest
from authlib.jose import jwt
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from src.app import app
from src.config.database import Base, get_db
from src.config.settings import settings
from src.routers.deps import (
    get_event_publisher,
    get_password_reset_mailer,
)


class RecordingPublisher:
    def __init__(self) -> None:
        self.events: list[dict] = []

    def publish(self, **kwargs) -> None:
        self.events.append(kwargs)


class RecordingPasswordResetMailer:
    def __init__(self) -> None:
        self.messages: list[dict[str, str]] = []

    def send(self, *, email: str, reset_token: str) -> None:
        self.messages.append(
            {"email": email, "reset_token": reset_token}
        )


@pytest.fixture(scope="session")
def engine():
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        execution_options={"schema_translate_map": {"account": None}},
    )
    yield engine
    engine.dispose()


@pytest.fixture(autouse=True)
def auth_settings(monkeypatch) -> None:
    monkeypatch.setattr(
        settings, "jwt_secret", "account-service-test-key"
    )
    monkeypatch.setattr(settings, "admin_emails_csv", "")


@pytest.fixture()
def db_session(engine) -> Generator[Session, None, None]:
    Base.metadata.create_all(bind=engine)
    try:
        with Session(engine) as session:
            yield session
    finally:
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def publisher() -> RecordingPublisher:
    return RecordingPublisher()


@pytest.fixture()
def mailer() -> RecordingPasswordResetMailer:
    return RecordingPasswordResetMailer()


@pytest.fixture()
def client(
    db_session, publisher, mailer
) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_event_publisher] = lambda: publisher
    app.dependency_overrides[get_password_reset_mailer] = lambda: mailer
    app.state.testing = True
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        del app.state.testing


@pytest.fixture()
def credentials() -> dict[str, str]:
    return {"email": "reader@example.com", "password": "test-password"}


@pytest.fixture()
def account(client, credentials) -> dict[str, str]:
    response = client.post("/auth/register", json=credentials)
    assert response.status_code == 201
    tokens = response.json()
    claims = jwt.decode(tokens["access_token"], settings.jwt_secret)
    claims.validate()
    return {**credentials, **tokens, "user_id": claims["sub"]}
