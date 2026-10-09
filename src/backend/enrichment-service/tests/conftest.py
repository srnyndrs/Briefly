from collections.abc import Iterator
from pathlib import Path
from collections import deque
from unittest.mock import MagicMock

import pytest
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.config.database import Base
from src.models import post_enrichment  # noqa: F401
from src.adapters.post_consumer import PostConsumer


@pytest.fixture
def deliver():
    """Drive queued broker callbacks on the calling thread, with real workers."""

    def run(processor, channel, body, tag=1):
        consumer = PostConsumer(processor)
        callbacks = deque()
        connection = MagicMock(is_open=True)
        connection.add_callback_threadsafe.side_effect = callbacks.append
        consumer._connection = connection
        consumer._channel = channel
        consumer._on_message(channel, MagicMock(delivery_tag=tag), None, body)
        while True:
            consumer._worker.join(timeout=2)
            assert not consumer._worker.is_alive()
            if not callbacks:
                break
            callbacks.popleft()()
        return consumer

    return run


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
