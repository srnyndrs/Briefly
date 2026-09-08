import json
from unittest.mock import Mock

import pika

from src.adapters import account_event_publisher
from src.config.settings import settings
from src.events.envelope import build_envelope


def test_build_envelope_generates_trace_fields() -> None:
    envelope = build_envelope(
        event_type="preferences.updated.v1",
        partition_key="user:user-1",
        payload={"user_id": "user-1"},
        correlation_id="request-1",
    )

    assert envelope["event_type"] == "preferences.updated.v1"
    assert envelope["producer"] == "account-service"
    assert envelope["correlation_id"] == "request-1"
    assert len(envelope["trace"]["trace_id"]) == 32
    assert len(envelope["trace"]["span_id"]) == 16


def test_publish_declares_account_exchange_and_sends_envelope(
    monkeypatch,
):
    params = Mock()
    channel = Mock()
    connection = Mock()
    connection.channel.return_value = channel
    connection.is_open = True

    monkeypatch.setattr(
        account_event_publisher.pika,
        "URLParameters",
        lambda url: params,
    )
    monkeypatch.setattr(
        account_event_publisher.pika,
        "BlockingConnection",
        lambda connection_params: connection,
    )

    publisher = account_event_publisher.AccountEventPublisher()
    publisher.publish(
        event_type="preferences.updated.v1",
        payload={"user_id": "user-1"},
        correlation_id="request-1",
        partition_key="user:user-1",
    )

    assert params.connection_attempts == 2
    assert params.retry_delay == 1.0
    channel.exchange_declare.assert_called_once_with(
        exchange=settings.account_exchange,
        exchange_type="topic",
        durable=True,
    )
    channel.basic_publish.assert_called_once()
    publish_kwargs = channel.basic_publish.call_args.kwargs
    assert publish_kwargs["exchange"] == settings.account_exchange
    assert publish_kwargs["routing_key"] == "preferences.updated.v1"

    envelope = json.loads(publish_kwargs["body"])
    assert envelope["event_type"] == "preferences.updated.v1"
    assert envelope["schema_version"] == 1
    assert envelope["producer"] == "account-service"
    assert envelope["correlation_id"] == "request-1"
    assert envelope["partition_key"] == "user:user-1"
    assert len(envelope["trace"]["trace_id"]) == 32
    assert len(envelope["trace"]["span_id"]) == 16
    assert envelope["payload"] == {"user_id": "user-1"}

    properties = publish_kwargs["properties"]
    assert isinstance(properties, pika.BasicProperties)
    assert properties.content_type == "application/json"
    assert properties.message_id == envelope["event_id"]
    assert properties.correlation_id == "request-1"
    assert properties.type == "preferences.updated.v1"
    assert properties.delivery_mode == 2
    connection.close.assert_called_once_with()
