import asyncio
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import src.app as application


def test_lifespan_stops_scheduler_when_application_raises(monkeypatch) -> None:
    monkeypatch.setattr(application.app.state, "testing", False, raising=False)
    monkeypatch.setattr(application.app.state, "scheduler", None, raising=False)
    scheduler = MagicMock(running=True)
    scheduler.add_listener.side_effect = lambda callback, mask: callback(None)
    thread = MagicMock()
    monkeypatch.setattr(application, "init_db", MagicMock())
    monkeypatch.setattr(
        application, "BlockingScheduler", MagicMock(return_value=scheduler)
    )
    monkeypatch.setattr(
        application.threading, "Thread", MagicMock(return_value=thread)
    )

    async def fail() -> None:
        async with application.lifespan(application.app):
            assert application.app.state.started
            raise RuntimeError("application failed")

    with pytest.raises(RuntimeError, match="application failed"):
        asyncio.run(fail())

    scheduler.shutdown.assert_called_once_with(wait=True)
    thread.start.assert_called_once_with()
    thread.join.assert_called_once_with(timeout=5)
    assert not application.app.state.started


def test_probes_detect_database_outage_and_stopped_scheduler(monkeypatch) -> None:
    monkeypatch.setattr(application.app.state, "testing", False, raising=False)
    monkeypatch.setattr(application, "init_db", MagicMock())
    monkeypatch.setattr(application, "database_ready", lambda: True)
    monkeypatch.setattr(application, "broker_ready", lambda: True)
    monkeypatch.setattr(application.settings, "crawl_interval_seconds", 3600)
    with TestClient(application.app) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/live").status_code == 200
        assert client.get("/ready").status_code == 200
        monkeypatch.setattr(application, "broker_ready", lambda: False)
        assert client.get("/ready").status_code == 503
        assert client.get("/live").status_code == 200
        monkeypatch.setattr(application, "broker_ready", lambda: True)
        monkeypatch.setattr(application, "database_ready", lambda: False)
        assert client.get("/ready").status_code == 503
        assert client.get("/live").status_code == 200
        monkeypatch.setattr(application, "database_ready", lambda: True)
        assert client.get("/ready").status_code == 200
        application.app.state.scheduler.pause()
        assert client.get("/ready").status_code == 503
        assert client.get("/live").status_code == 200
        application.app.state.scheduler.shutdown(wait=True)
        application.app.state.scheduler_thread.join(timeout=2)
        assert client.get("/live").status_code == 503
        assert client.get("/ready").status_code == 503
    assert not application.app.state.started
