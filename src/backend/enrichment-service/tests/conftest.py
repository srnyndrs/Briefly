from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.config.database import Base
from src.models import post_enrichment  # noqa: F401


@pytest.fixture
def session_factory(tmp_path: Path) -> Iterator[sessionmaker[Session]]:
    engine = create_engine(
        URL.create(
            drivername="sqlite+pysqlite",
            database=str(tmp_path / "enrichment.sqlite"),
        ),
        execution_options={"schema_translate_map": {"enrichment": None}},
    )
    Base.metadata.create_all(bind=engine)
    yield sessionmaker(bind=engine, autocommit=False, autoflush=False)
    engine.dispose()
