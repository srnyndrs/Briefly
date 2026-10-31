from unittest.mock import patch

from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import OperationalError

from src.config import database


def test_startup_recovers_and_creates_tables(monkeypatch):
    engine = create_engine(
        "sqlite://",
        execution_options={"schema_translate_map": {database.SCHEMA_NAME: None}},
    )
    monkeypatch.setattr(database, "engine", engine)
    try:
        connection = engine.connect()
        with (
            patch.object(
                engine,
                "connect",
                side_effect=[
                    OperationalError("connect", {}, RuntimeError("DNS not ready")),
                    connection,
                ],
            ),
            patch.object(database, "sleep"),
        ):
            database.init_db()

        assert "post_projections" in inspect(engine).get_table_names()
    finally:
        engine.dispose()
