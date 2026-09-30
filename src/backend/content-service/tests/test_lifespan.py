import asyncio
from unittest.mock import MagicMock

import pytest

import src.app as application


def test_lifespan_stops_consumer_when_application_raises(monkeypatch) -> None:
    consumer = MagicMock()
    consumer_factory = MagicMock(return_value=consumer)
    thread = MagicMock()
    thread.is_alive.return_value = False
    monkeypatch.setattr(application, "init_db", MagicMock())
    monkeypatch.setattr(application, "FeedConsumer", consumer_factory)
    monkeypatch.setattr(
        application.threading, "Thread", MagicMock(return_value=thread)
    )
    monkeypatch.setattr(application.app.state, "testing", False, raising=False)

    async def fail() -> None:
        async with application.lifespan(application.app):
            raise RuntimeError("application failed")

    with pytest.raises(RuntimeError, match="application failed"):
        asyncio.run(fail())

    consumer_factory.assert_called_once_with(application._create_feed_processor)
    consumer.stop.assert_called_once_with()


def test_feed_processor_factory_injects_repository(monkeypatch) -> None:
    db = MagicMock()
    repository = MagicMock()
    processor = MagicMock()
    repository_factory = MagicMock(return_value=repository)
    processor_factory = MagicMock(return_value=processor)
    monkeypatch.setattr(application, "PostRepository", repository_factory)
    monkeypatch.setattr(application, "FeedProcessor", processor_factory)

    assert application._create_feed_processor(db) is processor

    repository_factory.assert_called_once_with(db)
    processor_factory.assert_called_once_with(repository)
