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
