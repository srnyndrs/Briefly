from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import Column, Integer, MetaData, Table, event, inspect, text

from src.config import database


def test_init_db_can_repeat_with_existing_tables(monkeypatch, session_factory):
    engine = session_factory.kw["bind"]
    monkeypatch.setattr(database, "engine", engine)

    database.init_db()
    database.init_db()

    assert "post_projections" in inspect(engine).get_table_names()


def test_postgres_init_db_rolls_back_and_serializes_starts(
    monkeypatch, postgres_engine
):
    # Use a disposable schema, never drop the service's own tables.
    schema = f"startup_test_{uuid4().hex}"
    metadata = MetaData(schema=schema)
    Table("probe", metadata, Column("id", Integer, primary_key=True))
    monkeypatch.setattr(database, "engine", postgres_engine)
    monkeypatch.setattr(database, "SCHEMA_NAME", schema)
    monkeypatch.setattr(database, "Base", SimpleNamespace(metadata=metadata))

    def fail_ddl(*args, **kwargs):
        raise RuntimeError("DDL failed")

    try:
        event.listen(metadata, "before_create", fail_ddl)
        try:
            with pytest.raises(RuntimeError, match="DDL failed"):
                database.init_db()
        finally:
            event.remove(metadata, "before_create", fail_ddl)

        assert not inspect(postgres_engine).has_schema(schema)
        barrier = Barrier(2)

        def start():
            barrier.wait(timeout=5)
            database.init_db()

        with ThreadPoolExecutor(max_workers=2) as workers:
            futures = [workers.submit(start) for _ in range(2)]
            for future in futures:
                future.result(timeout=40)

        assert inspect(postgres_engine).get_table_names(schema=schema) == ["probe"]
    finally:
        with postgres_engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
