import json
import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
import requests
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.transport import Transport

from src.app import scrub_sentry_event
from src.config.settings import settings
from src.services.crawl_orchestrator import CrawlCycleOrchestrator


class CaptureTransport(Transport):
    def __init__(self):
        super().__init__()
        self.events = []

    def capture_envelope(self, envelope):
        for item in envelope.items:
            event = item.get_event()
            if event is not None:
                self.events.append(event)


def test_sentry_scrubber_removes_sensitive_event_fields():
    event = {
        "request": {
            "url": "https://example.com/feed?token=secret",
            "headers": {"Authorization": "Bearer secret"},
            "data": "<feed>private content</feed>",
        },
        "breadcrumbs": [{"message": "secret"}],
        "extra": {"body": "<feed>private content</feed>"},
        "contexts": {"secret": "secret"},
        "user": {"email": "private@example.com"},
        "logentry": {
            "message": "error %s",
            "params": ["secret"],
            "formatted": "error secret",
        },
        "exception": {
            "values": [
                {
                    "type": "RuntimeError",
                    "value": "secret <feed>private content</feed>",
                    "stacktrace": {
                        "frames": [
                            {
                                "filename": "crawler.py",
                                "lineno": 12,
                                "vars": {"body": "secret"},
                                "context_line": "secret",
                            }
                        ]
                    },
                }
            ]
        },
    }

    scrubbed = scrub_sentry_event(event, {})

    assert scrubbed["exception"]["values"][0]["type"] == "RuntimeError"
    assert "crawler.py" in json.dumps(scrubbed)
    serialized = json.dumps(scrubbed)
    assert "secret" not in serialized
    assert "private content" not in serialized
    assert "Authorization" not in serialized


def test_suspension_event_keeps_safe_identifiers():
    message = "Source suspended after retry limit"
    event = {
        "message": message,
        "tags": {"source_id": "123", "source_host": "example.com"},
        "logentry": {"formatted": "secret"},
    }

    scrubbed = scrub_sentry_event(event, {})

    assert scrubbed["message"] == message
    assert scrubbed["tags"]["source_host"] == "example.com"
    assert "secret" not in json.dumps(scrubbed)


def test_cycle_fault_captures_one_event_but_feed_failure_captures_none():
    transport = CaptureTransport()
    previous_client = sentry_sdk.get_client()
    sentry_sdk.init(
        dsn="http://public@example.com/1",
        transport=transport,
        before_send=scrub_sentry_event,
        integrations=[LoggingIntegration(level=None, event_level=None)],
        include_local_variables=False,
        send_default_pii=False,
        traces_sample_rate=0.0,
        enable_logs=False,
    )
    try:
        source = SimpleNamespace(
            source_id=uuid.uuid4(),
            url="https://example.com/feed?token=secret",
            title="Example",
            etag=None,
            last_modified=None,
        )
        session_factory = MagicMock()
        repo = MagicMock()
        repo.get_active_sources.return_value = [source]
        repo.save_crawl_failure.return_value = 1
        http = MagicMock()
        publisher = MagicMock()
        with (
            patch(
                "src.services.crawl_orchestrator.SourceRepository",
                return_value=repo,
            ),
            patch(
                "src.services.crawl_orchestrator.RequestsHttpClient",
                return_value=http,
            ),
            patch(
                "src.services.crawl_orchestrator.FeedPublisher",
                return_value=publisher,
            ),
        ):
            orchestrator = CrawlCycleOrchestrator(session_factory)
            http.fetch.side_effect = requests.Timeout("secret")
            orchestrator.run_crawl_cycle()
            assert transport.events == []

            http.fetch.side_effect = None
            http.fetch.return_value = SimpleNamespace(
                status_code=200,
                body="<feed>private content</feed>",
                etag=None,
                last_modified=None,
            )
            publisher.publish_source_fetched.side_effect = ValueError(
                "secret <feed>private content</feed>"
            )
            with pytest.raises(ValueError):
                orchestrator.run_crawl_cycle()

            repo.save_crawl_failure.return_value = settings.max_retries
            orchestrator._handle_failure(
                repo,
                source.source_id,
                source.url,
                "cycle-3",
                requests.Timeout("secret"),
            )
    finally:
        sentry_sdk.get_client().close()
        sentry_sdk.get_global_scope().set_client(previous_client)

    assert len(transport.events) == 2
    fault, suspension = transport.events
    assert fault["exception"]["values"][0]["type"] == "ValueError"
    assert fault["tags"]["cycle_id"]
    assert suspension["message"] == "Source suspended after retry limit"
    assert suspension["tags"]["source_id"] == str(source.source_id)
    assert "secret" not in json.dumps(transport.events)
    assert "private content" not in json.dumps(transport.events)
