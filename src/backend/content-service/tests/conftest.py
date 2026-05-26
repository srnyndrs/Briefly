from typing import Any, Generator

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from src.app import app
from src.config.database import Base, get_db


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=eng)
    return eng


@pytest.fixture(scope="session")
def _session_factory(engine):
    return sessionmaker(
        bind=engine, autocommit=False, autoflush=False
    )


@pytest.fixture()
def db_session(
    engine, _session_factory
) -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    session = _session_factory(bind=connection)

    # Intercept commit() calls and replace with savepoint flush
    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, trans):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, Any, None]:
    app.state.testing = True

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
