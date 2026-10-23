import os
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

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
