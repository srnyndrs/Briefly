import json

import pytest
import requests
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.transport import Transport

from src.app import scrub_sentry_event
from src.config.settings import settings


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


@pytest.mark.parametrize(
    "outcome", ["feed-failure", "cycle-fault", "suspension"]
)
def test_reporting_captures_only_actionable_failures(
    crawl_cycle, source_factory, db_session, outcome
):
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
        source = source_factory(
            url="https://example.com/feed?token=secret",
            consecutive_failures=(
                settings.max_retries - 1
                if outcome == "suspension"
                else 0
            ),
        )
        orchestrator, http_get, publisher = crawl_cycle
        if outcome == "cycle-fault":
            publisher.publish_source_fetched.side_effect = ValueError(
                "secret <feed>private content</feed>"
            )
            with pytest.raises(ValueError):
                orchestrator.run_crawl_cycle()
        else:
            http_get.side_effect = requests.Timeout("secret")
            orchestrator.run_crawl_cycle()

        db_session.refresh(source)
        events = transport.events
        if outcome == "feed-failure":
            assert events == []
            assert source.consecutive_failures == 1
        else:
            assert len(events) == 1
            event = events[0]
            assert event["tags"]["cycle_id"]
            if outcome == "cycle-fault":
                assert (
                    event["exception"]["values"][0]["type"]
                    == "ValueError"
                )
                assert source.consecutive_failures == 0
            else:
                assert (
                    event["message"]
                    == "Source suspended after retry limit"
                )
                assert event["tags"]["source_id"] == str(
                    source.source_id
                )
                assert (
                    source.consecutive_failures == settings.max_retries
                )
                orchestrator.run_crawl_cycle()
                assert len(events) == 1
        assert "secret" not in json.dumps(events)
        assert "private content" not in json.dumps(events)
    finally:
        sentry_sdk.get_client().close()
        sentry_sdk.get_global_scope().set_client(previous_client)
