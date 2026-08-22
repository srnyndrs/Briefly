import json
import uuid

import pika

from src.config.message_broker import create_channel
from src.config.settings import settings
from src.events.envelope import build_envelope


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

    def publish_source_fetched(
        self,
        *,
        source_id: uuid.UUID,
        source_url: str,
        correlation_id: str,
        source_title: str | None = None,
        raw_xml: str,
    ) -> None:
        payload = {
            "source_id": str(source_id),
            "source_url": source_url,
            "source_title": source_title,
            "raw_xml": raw_xml,
        }
        envelope = build_envelope(
            event_type="feed.raw_fetched.v1",
            partition_key=f"source:{source_id}",
            payload=payload,
            correlation_id=correlation_id,
        )
        self._publish("feed.raw_fetched.v1", envelope)

    def close(self) -> None:
        if (
            self._channel.connection
            and self._channel.connection.is_open
        ):
            self._channel.connection.close()
