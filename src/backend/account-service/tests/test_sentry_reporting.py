import json
from unittest.mock import Mock
from uuid import uuid4

import pika
import pytest
import sentry_sdk
from sentry_sdk.transport import Transport

from src.adapters.account_event_publisher import AccountEventPublisher
from src.adapters.password_reset_mailer import (
    PasswordResetDeliveryError,
)
from src.app import app, init_sentry, scrub_sentry_event
from src.config.settings import settings
from src.repositories.account_repository import AccountRepository
from src.routers.deps import get_event_publisher


class CaptureTransport(Transport):
    def __init__(self):
        super().__init__()
        self.events = []

    def capture_envelope(self, envelope):
        for item in envelope.items:
            event = item.get_event()
            if event is not None:
                self.events.append(event)


@pytest.fixture()
def sentry_events(monkeypatch):
    transport = CaptureTransport()
    previous_client = sentry_sdk.get_client()
    sdk_init = sentry_sdk.init
    monkeypatch.setattr(
        settings, "sentry_dsn", "http://public@example.com/1"
    )
    monkeypatch.setattr(
        sentry_sdk,
        "init",
        lambda **options: sdk_init(transport=transport, **options),
    )
    init_sentry()
    try:
        yield transport.events
    finally:
        sentry_sdk.get_client().close()
        sentry_sdk.get_global_scope().set_client(previous_client)
        sentry_sdk.get_global_scope().remove_tag("service")


def test_sentry_is_optional(monkeypatch) -> None:
    monkeypatch.setattr(settings, "sentry_dsn", "")
    initialize = Mock()
    monkeypatch.setattr(sentry_sdk, "init", initialize)
    init_sentry()
    initialize.assert_not_called()


def test_scrubber_keeps_exception_locations_without_account_data() -> (
    None
):
    event = {
        key: {"value": "sensitive-account-data"}
        for key in (
            "request",
            "breadcrumbs",
            "extra",
            "contexts",
            "user",
            "logentry",
        )
    }
    event["exception"] = {
        "values": [
            {
                "type": "RuntimeError",
                "value": "sensitive-account-data",
                "stacktrace": {
                    "frames": [
                        {
                            "filename": "account_service.py",
                            "lineno": 42,
                            "vars": {
                                "password": "sensitive-account-data"
                            },
                            "context_line": "sensitive-account-data",
                            "pre_context": ["sensitive-account-data"],
                            "post_context": ["sensitive-account-data"],
                        }
                    ]
                },
            }
        ]
    }
    scrubbed = scrub_sentry_event(event, {})
    assert "sensitive-account-data" not in json.dumps(scrubbed)
    exception = scrubbed["exception"]["values"][0]
    assert exception["type"] == "RuntimeError"
    assert exception["stacktrace"]["frames"] == [
        {"filename": "account_service.py", "lineno": 42}
    ]


def test_expected_http_errors_are_not_reported(
    sentry_events, client, account, credentials
) -> None:
    assert (
        client.post("/auth/register", json=credentials).status_code
        == 409
    )
    assert (
        client.post(
            "/auth/login",
            json={**credentials, "password": "wrong-password"},
        ).status_code
        == 401
    )
    assert client.get(f"/users/{uuid4()}").status_code == 404
    assert client.post("/auth/register", json={}).status_code == 422
    assert sentry_events == []


def test_unhandled_request_failure_is_reported_once(
    sentry_events, client, credentials, monkeypatch
) -> None:
    monkeypatch.setattr(
        AccountRepository,
        "get_user_by_email",
        Mock(side_effect=RuntimeError("sensitive-account-data")),
    )
    with pytest.raises(RuntimeError):
        client.post(
            "/auth/login",
            json=credentials,
            headers={"Authorization": "Bearer sensitive-account-data"},
        )
    assert len(sentry_events) == 1
    event = sentry_events[0]
    assert event["tags"]["service"] == "account-service"
    assert event["exception"]["values"][-1]["type"] == "RuntimeError"
    serialized = json.dumps(event)
    for sensitive in (
        "sensitive-account-data",
        credentials["email"],
        credentials["password"],
    ):
        assert sensitive not in serialized


@pytest.mark.parametrize("operation", ["mailer", "publisher"])
def test_caught_delivery_failure_is_reported_once(
    sentry_events, client, account, mailer, monkeypatch, operation
) -> None:
    if operation == "mailer":
        monkeypatch.setattr(
            mailer,
            "send",
            Mock(
                side_effect=PasswordResetDeliveryError(
                    "sensitive-account-data"
                )
            ),
        )
        response = client.post(
            "/auth/password-reset/request",
            json={"email": account["email"]},
        )
        assert response.status_code == 202
        assert response.json() == {"status": "accepted"}
        expected_operation = "password_reset_delivery"
    else:
        app.dependency_overrides[get_event_publisher] = (
            AccountEventPublisher
        )
        monkeypatch.setattr(
            pika,
            "BlockingConnection",
            Mock(
                side_effect=pika.exceptions.AMQPConnectionError(
                    "sensitive-account-data"
                )
            ),
        )
        response = client.put(
            f"/users/{account['user_id']}/preferences",
            json={"languages": ["en"]},
        )
        assert response.status_code == 200
        assert client.get(
            f"/users/{account['user_id']}/preferences"
        ).json()["languages"] == ["en"]
        expected_operation = "publish_account_event"
    assert len(sentry_events) == 1
    event = sentry_events[0]
    assert event["tags"]["service"] == "account-service"
    assert event["tags"]["operation"] == expected_operation
    assert "sensitive-account-data" not in json.dumps(event)
