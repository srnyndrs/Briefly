import json
from io import BytesIO
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from src import app as application
from src.config.settings import Settings, settings
from src.services import runtime


def process(processor, event, channel):
    saved = processor(event)
    processor.publish(saved, channel)
    return (
        processor.mark_published(saved) if saved.publication_pending else saved
    )


@pytest.fixture
def ollama(monkeypatch, session_factory):
    calls = []
    installed = {"digest": "digest-one"}

    def fake_open(request, *, timeout):
        assert timeout == 60
        if request.full_url.endswith("/api/tags"):
            data = {"models": [{"name": "test:latest", **installed}]}
        else:
            calls.append(json.loads(request.data))
            data = {
                "done": True,
                "done_reason": "stop",
                "message": {"content": '{"category_ids":["science"]}'},
            }
        return BytesIO(json.dumps(data).encode())

    monkeypatch.setattr("src.adapters.ollama_provider.urlopen", fake_open)
    monkeypatch.setattr(runtime, "SessionLocal", session_factory)
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


def test_composed_runtime_persists_publishes_and_reuses(ollama) -> None:
    calls, _ = ollama
    event = parsed_event()
    channel = MagicMock()
    saved = process(runtime.create_post_processor(), event, channel)
    reused = process(runtime.create_post_processor(), event, channel)
    assert saved == reused
    assert saved.category_ids == ("science",)
    assert saved.enrichment_version.startswith("ollama-")
    assert len(saved.enrichment_version) <= 100
    assert not saved.publication_pending
    assert len(calls) == 1
    assert (
        json.loads(calls[0]["messages"][1]["content"])["title"]
        == "Research report"
    )
    assert channel.basic_publish.call_count == 1


@pytest.mark.parametrize(
    "change", ["digest", "model", "prompt", "input_policy"]
)
def test_runtime_identity_changes_rerun_same_revision(
    ollama, monkeypatch, change
) -> None:
    calls, installed = ollama
    event = parsed_event()
    channel = MagicMock()
    first = process(runtime.create_post_processor(), event, channel)
    if change == "digest":
        installed["digest"] = "digest-two"
    elif change == "model":
        # Both spellings resolve to the installed latest tag, but record the
        # explicit configured model choice in the identity.
        monkeypatch.setattr(settings, "ollama_model", "test")
    elif change == "prompt":
        monkeypatch.setattr(runtime, "instructions", lambda _: "Changed policy")
    else:
        monkeypatch.setattr(runtime, "INPUT_POLICY_VERSION", "bounded-input-v2")
    second = process(runtime.create_post_processor(), event, channel)
    assert second.enrichment_version != first.enrichment_version
    assert second.enrichment_revision == first.enrichment_revision + 1
    assert len(calls) == 2


@pytest.mark.parametrize("model", [None, "", "   "])
def test_runtime_requires_model(monkeypatch, model) -> None:
    monkeypatch.setattr(settings, "ollama_model", model)
    with pytest.raises(ValueError, match="OLLAMA_MODEL is required"):
        runtime.create_post_processor()


@pytest.mark.parametrize("timeout", [0, -1, 301, float("inf")])
def test_runtime_timeout_is_bounded(timeout) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, ollama_timeout_seconds=timeout)


def test_empty_runtime_model_setting_keeps_evaluation_importable() -> None:
    assert Settings(_env_file=None, ollama_model="").ollama_model == ""


def test_startup_composes_starts_and_stops_consumer(
    ollama, monkeypatch
) -> None:
    init_db = MagicMock()
    consumer = MagicMock()
    thread = MagicMock()
    monkeypatch.setattr(application, "init_db", init_db)
    monkeypatch.setattr(application, "PostConsumer", consumer)
    monkeypatch.setattr(application.threading, "Thread", thread)
    with TestClient(application.app) as client:
        assert client.get("/health").json()["status"] == "ok"
        init_db.assert_called_once_with()
        consumer.assert_called_once()
        assert callable(consumer.call_args.args[0])
        thread.return_value.start.assert_called_once_with()
    consumer.return_value.stop.assert_called_once_with()
    thread.return_value.join.assert_called_once_with(timeout=5)


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
    monkeypatch.setattr(application.threading, "Thread", MagicMock())

    async def fail() -> None:
        async with application.lifespan(application.app):
            raise RuntimeError("application failed")

    with pytest.raises(RuntimeError, match="application failed"):
        asyncio.run(fail())
    consumer.return_value.stop.assert_called_once_with()
