import json
from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pika

from src.adapters.event_publisher import publish_event
from src.config.message_broker import (
    create_connection_parameters,
    publisher_channel,
)
from src.config.settings import settings
from src.events.preferences_updated import build_preferences_updated_event
from src.models.account import UserPreferences


def test_publish_declares_exchange_confirms_and_sends_envelope() -> None:
    preferences = UserPreferences(
        user_id=uuid4(),
        muted_keywords=["word"],
        muted_categories=[],
        blocked_source_ids=[],
        languages=["en"],
        updated_at=datetime.fromisoformat("2026-10-25T10:00:00+00:00"),
    )
    envelope = build_preferences_updated_event(
        preferences=preferences,
        correlation_id="request-1",
    )
    with patch("src.config.message_broker.pika.BlockingConnection") as factory:
        connection = factory.return_value
        channel = connection.channel.return_value
        with publisher_channel(exchange=settings.account_exchange) as yielded:
            assert yielded is channel
            publish_event(
                channel,
                exchange=settings.account_exchange,
                envelope=envelope,
            )

    channel.exchange_declare.assert_called_once_with(
        exchange=settings.account_exchange,
        exchange_type="topic",
        durable=True,
    )
    channel.confirm_delivery.assert_called_once_with()
    channel.basic_publish.assert_called_once()
    publish_kwargs = channel.basic_publish.call_args.kwargs
    assert publish_kwargs["exchange"] == settings.account_exchange
    assert publish_kwargs["routing_key"] == "preferences.updated.v1"
    assert publish_kwargs["mandatory"] is True
    published_envelope = json.loads(publish_kwargs["body"])
    assert published_envelope == envelope
    assert UUID(published_envelope["event_id"])
    properties = publish_kwargs["properties"]
    assert properties.content_type == "application/json"
    assert properties.message_id == envelope["event_id"]
    assert properties.correlation_id == "request-1"
    assert properties.type == "preferences.updated.v1"
    assert properties.delivery_mode == pika.DeliveryMode.Persistent.value
    assert properties.timestamp == int(
        datetime.fromisoformat(envelope["occurred_at"]).timestamp()
    )
    connection.close.assert_called_once_with()


def test_account_connection_policy_is_preserved() -> None:
    with patch("src.config.message_broker.pika.URLParameters") as factory:
        params = create_connection_parameters()
    factory.assert_called_once_with(settings.rabbitmq_url)
    assert params.blocked_connection_timeout == settings.blocked_timeout_seconds
    assert params.connection_attempts == 2
    assert params.retry_delay == 1.0


def test_publish_propagates_broker_error() -> None:
    channel = MagicMock()
    error = pika.exceptions.UnroutableError([])
    channel.basic_publish.side_effect = error
    envelope = {
        "event_id": "id",
        "event_type": "preferences.updated.v1",
        "occurred_at": "2026-10-25T10:00:00+00:00",
        "payload": {},
    }
    try:
        publish_event(channel, exchange=settings.account_exchange, envelope=envelope)
    except pika.exceptions.UnroutableError as caught:
        assert caught is error
    else:
        raise AssertionError("broker error did not propagate")
