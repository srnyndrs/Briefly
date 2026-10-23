import asyncio
from unittest.mock import MagicMock

import pytest

import src.app as application


def test_lifespan_stops_scheduler_when_application_raises(monkeypatch) -> None:
    monkeypatch.setattr(application.app.state, "testing", False, raising=False)
    monkeypatch.setattr(application.app.state, "scheduler", None, raising=False)
    scheduler = MagicMock(running=True)
    monkeypatch.setattr(application, "init_db", MagicMock())
    monkeypatch.setattr(
        application, "BackgroundScheduler", MagicMock(return_value=scheduler)
    )

    async def fail() -> None:
        async with application.lifespan(application.app):
            raise RuntimeError("application failed")

    with pytest.raises(RuntimeError, match="application failed"):
        asyncio.run(fail())

    scheduler.shutdown.assert_called_once_with(wait=True)
