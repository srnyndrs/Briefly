import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

import pika

from src.config.settings import settings

logger = logging.getLogger("account-service.events")


class EventPublisher:
    def __init__(self) -> None:
        self._connection: pika.BlockingConnection | None = None
        self._channel: pika.channel.Channel | None = None

    def connect(self) -> None:
        try:
            params = pika.URLParameters(settings.rabbitmq_url)
            self._connection = pika.BlockingConnection(params)
            self._channel = self._connection.channel()
            self._channel.exchange_declare(
                exchange=settings.account_exchange,
                exchange_type="topic",
                durable=True,
            )
            logger.info(
                "Connected to RabbitMQ exchange=%s",
                settings.account_exchange,
            )
        except Exception as exc:  # pragma: no cover
            logger.warning(
                "Event publisher disabled (RabbitMQ unavailable): %s",
                exc,
            )
            self._connection = None
            self._channel = None

    def close(self) -> None:
        if self._connection:
            self._connection.close()

    def publish(
        self,
        *,
        event_type: str,
        payload: dict[str, Any],
        correlation_id: str,
        partition_key: str,
        trace_id: str | None = None,
        span_id: str | None = None,
    ) -> None:
        if self._channel is None:
            return

        envelope = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "schema_version": 1,
            "occurred_at": datetime.now(UTC).isoformat(),
            "producer": "account-service",
            "correlation_id": correlation_id,
            "partition_key": partition_key,
            "trace": {
                "trace_id": trace_id,
                "span_id": span_id,
            },
            "payload": payload,
        }

        message = json.dumps(envelope).encode("utf-8")
        properties = pika.BasicProperties(
            content_type="application/json",
            message_id=envelope["event_id"],
            correlation_id=correlation_id,
            timestamp=int(datetime.now(UTC).timestamp()),
            type=event_type,
            delivery_mode=2,
        )
        self._channel.basic_publish(
            exchange=settings.account_exchange,
            routing_key=event_type,
            body=message,
            properties=properties,
        )
