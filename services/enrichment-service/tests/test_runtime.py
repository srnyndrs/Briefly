import json
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src import app as application
from src.adapters.event_publisher import publish_event
from src.config.settings import settings
from src.events.post_enriched import build_enrichment_event
from src.services.post_processor import PostProcessor
from src.services.provider import ProviderError


def process(processor, event, channel):
    saved = processor.process(event)
    if saved.publication_pending:
        publish_event(
            channel,
            exchange=settings.result_exchange,
            envelope=build_enrichment_event(saved),
        )
    return processor.mark_published(saved) if saved.publication_pending else saved


@pytest.fixture
def ollama(monkeypatch, session_factory):
    calls = []
    installed = {"digest": "digest-one"}

    def fake_open(request, *, timeout):
        assert timeout in (2, 60)
        if request.full_url.endswith("/api/tags"):
            data = {"models": [{"name": settings.ollama_model, **installed}]}
        else:
            calls.append(json.loads(request.data))
            data = {
                "done": True,
                "done_reason": "stop",
                "message": {"content": '{"category_ids":["science"]}'},
            }
        return BytesIO(json.dumps(data).encode())

    monkeypatch.setattr("src.adapters.ollama_provider.urlopen", fake_open)
    monkeypatch.setattr(application, "SessionLocal", session_factory)
    monkeypatch.setattr(settings, "ollama_model", "test:latest")
    monkeypatch.setattr(settings, "ollama_timeout_seconds", 60)
    monkeypatch.setattr(settings, "gemini_api_key", None)
    return calls, installed


def parsed_event() -> dict:
    return {
        "event_id": "parsed-event",
        "event_type": "post.parsed.v1",
        "correlation_id": "correlation",
        "payload": {
            "post_id": str(uuid4()),
            "post_revision": 1,
            "source_id": str(uuid4()),
            "item_guid": "one",
            "url": "https://example.com/one",
            "title": "  Research   report  ",
            "content": "New finding",
        },
    }


def test_composed_runtime_persists_publishes_and_reuses(
    ollama, monkeypatch
) -> None:
    calls, installed = ollama
    event = parsed_event()
    channel = MagicMock()
    saved = process(
        PostProcessor(application.create_enrichment_service()), event, channel
    )
    installed["digest"] = "digest-two"
    monkeypatch.setattr(settings, "ollama_model", "changed:latest")
    reused = process(
        PostProcessor(application.create_enrichment_service()), event, channel
    )
    assert saved == reused
    assert saved.category_ids == ("science",)
    assert not saved.publication_pending
    assert len(calls) == 1
    assert (
        json.loads(calls[0]["messages"][1]["content"])["title"] == "Research report"
    )
    assert channel.basic_publish.call_count == 1


def test_startup_composes_starts_and_stops_consumer(ollama, monkeypatch) -> None:
    init_db = MagicMock()
    consumer = MagicMock()
    thread = MagicMock()
    monkeypatch.setattr(application, "database_ready", lambda: True)
    monkeypatch.setattr(application, "init_db", init_db)
    monkeypatch.setattr(application, "PostConsumer", consumer)
    monkeypatch.setattr(application, "threading", SimpleNamespace(Thread=thread))
    with TestClient(application.app) as client:
        assert client.get("/health").json()["status"] == "ok"
        assert client.get("/live").status_code == 200
        assert client.get("/ready").status_code == 200
        consumer.return_value.is_consuming = False
        assert client.get("/ready").status_code == 503
        assert client.get("/live").status_code == 200
        consumer.return_value.is_consuming = True
        monkeypatch.setattr(application, "database_ready", lambda: False)
        assert client.get("/ready").status_code == 503
        assert client.get("/live").status_code == 200
        monkeypatch.setattr(application, "database_ready", lambda: True)
        assert client.get("/ready").status_code == 200
        with monkeypatch.context() as model_check:
            model_check.setattr(
                application.OllamaProvider,
                "model_digest",
                MagicMock(side_effect=ProviderError("Ollama unavailable")),
            )
            assert client.get("/ready").status_code == 503
            assert client.get("/live").status_code == 200
        assert client.get("/ready").status_code == 200
        thread.return_value.is_alive.return_value = False
        assert client.get("/live").status_code == 503
        assert client.get("/ready").status_code == 503
        assert client.get("/health").status_code == 200
        thread.return_value.is_alive.return_value = True
        init_db.assert_called_once_with()
        consumer.assert_called_once()
        thread.return_value.start.assert_called_once_with()
    consumer.return_value.stop.assert_called_once_with()
    thread.return_value.join.assert_called_once()
    assert not application.app.state.started


def test_missing_model_prevents_consumer_startup(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ollama_model", None)
    monkeypatch.setattr(application, "init_db", MagicMock())
    consumer = MagicMock()
    monkeypatch.setattr(application, "PostConsumer", consumer)
    with pytest.raises(ValueError, match="OLLAMA_MODEL is required"):
        with TestClient(application.app):
            pass
    consumer.assert_not_called()


def test_lifespan_stops_consumer_when_application_raises(
    ollama, monkeypatch
) -> None:
    import asyncio

    consumer = MagicMock()
    monkeypatch.setattr(application, "init_db", MagicMock())
    monkeypatch.setattr(application, "PostConsumer", consumer)
    monkeypatch.setattr(
        application, "threading", SimpleNamespace(Thread=MagicMock())
    )

    async def fail() -> None:
        async with application.lifespan(application.app):
            raise RuntimeError("application failed")

    with pytest.raises(RuntimeError, match="application failed"):
        asyncio.run(fail())
    consumer.return_value.stop.assert_called_once_with()
