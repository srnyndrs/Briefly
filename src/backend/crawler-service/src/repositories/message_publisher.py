import json
import uuid
from datetime import datetime, timezone

import pika

from src.config.message_broker import create_channel
from src.config.settings import settings
from src.schemas.schemas import (
    EventTrace,
    FeedFetchFailedEvent,
    FeedFetchFailedPayload,
    FeedRawFetchedEvent,
    FeedRawFetchedPayload,
)


class RabbitMQEventPublisher:
    def __init__(self) -> None:
        self._channel = create_channel()

    def _publish(self, routing_key: str, payload: dict) -> None:
        body = json.dumps(payload, default=str).encode("utf-8")
        self._channel.basic_publish(
            exchange=settings.feed_exchange,
            routing_key=routing_key,
            body=body,
            properties=pika.BasicProperties(
                delivery_mode=pika.DeliveryMode.Persistent,
                content_type="application/json",
            ),
        )

    def publish_feed_fetched(
        self,
        *,
        feed_id: uuid.UUID,
        feed_url: str,
        source_title: str | None = None,
        raw_xml: str,
    ) -> None:
        payload = FeedRawFetchedPayload(
            feed_id=feed_id,
            feed_url=feed_url,
            source_title=source_title,
            raw_xml=raw_xml,
        )
        event = FeedRawFetchedEvent(
            event_id=uuid.uuid4(),
            event_type="feed.raw_fetched.v1",
            occurred_at=datetime.now(timezone.utc),
            producer="crawler-service",
            correlation_id=uuid.uuid4(),
            partition_key=f"source:{feed_id}",
            trace=EventTrace(
                trace_id=uuid.uuid4().hex,
                span_id=uuid.uuid4().hex[:16],
            ),
            payload=payload,
        )
        self._publish("feed.raw_fetched.v1", event.model_dump())

    def publish_feed_failed(
        self,
        *,
        feed_id: uuid.UUID,
        feed_url: str,
        error_code: str,
        error_message: str,
        retry_count: int,
    ) -> None:
        payload = FeedFetchFailedPayload(
            feed_id=feed_id,
            feed_url=feed_url,
            error_code=error_code,  # type: ignore[arg-type]
            error_message=error_message,
            retry_count=retry_count,
        )
        event = FeedFetchFailedEvent(
            event_id=uuid.uuid4(),
            event_type="feed.fetch_failed.v1",
            occurred_at=datetime.now(timezone.utc),
            producer="crawler-service",
            correlation_id=uuid.uuid4(),
            partition_key=f"source:{feed_id}",
            trace=EventTrace(
                trace_id=uuid.uuid4().hex,
                span_id=uuid.uuid4().hex[:16],
            ),
            payload=payload,
        )
        self._publish("feed.fetch_failed.v1", event.model_dump())

    def close(self) -> None:
        if (
            self._channel.connection
            and self._channel.connection.is_open
        ):
            self._channel.connection.close()
