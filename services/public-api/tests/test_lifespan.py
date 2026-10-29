import asyncio
from unittest.mock import MagicMock

import pytest

import src.app as application


def test_lifespan_stops_projector_when_application_raises(monkeypatch) -> None:
    monkeypatch.setattr(application.app.state, "testing", False, raising=False)
    monkeypatch.setattr(application.app.state, "projector", None, raising=False)
    monkeypatch.setattr(
        application.app.state, "projector_thread", None, raising=False
    )
    projector = MagicMock()
    thread = MagicMock()
    thread.is_alive.side_effect = [True, False]
    monkeypatch.setattr(application.settings, "shutdown_timeout_seconds", 2)
    monkeypatch.setattr(application, "init_db", MagicMock())
    monkeypatch.setattr(
        application, "QueryProjector", MagicMock(return_value=projector)
    )
    monkeypatch.setattr(
        application.threading, "Thread", MagicMock(return_value=thread)
    )
    monkeypatch.setattr(application.settings, "query_consumer_enabled", True)

    async def fail() -> None:
        async with application.lifespan(application.app):
            assert application.app.state.started
            raise RuntimeError("application failed")

    with pytest.raises(RuntimeError, match="application failed"):
        asyncio.run(fail())

    projector.stop.assert_called_once_with()
    thread.join.assert_called_once_with(timeout=2)
    assert not application.app.state.started
