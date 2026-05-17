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
        """Startup check to declare exchange and verify connectivity.
        
        Connection is closed immediately to avoid holding open stale sockets.
        """
        try:
            params = pika.URLParameters(settings.rabbitmq_url)
            # Use short timeouts for the startup check to avoid blocking app start
            params.connection_attempts = 2
            params.retry_delay = 1.0
            
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
            channel.exchange_declare(
                exchange=settings.account_exchange,
                exchange_type="topic",
                durable=True,
            )
            connection.close()
            logger.info(
                "Successfully declared RabbitMQ exchange '%s' on startup.",
                settings.account_exchange,
            )
        except Exception as exc:  # pragma: no cover
            logger.warning(
                "RabbitMQ unavailable at startup: %s. Event publisher will auto-recover on demand.",
                exc,
            )

    def close(self) -> None:
        """No-op cleanup since connections are opened and closed on demand."""
        pass

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
        """Publish an event by opening a connection on demand.
        
        This prevents thread-safety issues from FastAPI's sync threadpool
        and completely avoids stale connection errors (StreamLostError).
        """
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

        try:
            params = pika.URLParameters(settings.rabbitmq_url)
            params.connection_attempts = 2
            params.retry_delay = 1.0
            
            connection = pika.BlockingConnection(params)
            try:
                channel = connection.channel()
                channel.exchange_declare(
                    exchange=settings.account_exchange,
                    exchange_type="topic",
                    durable=True,
                )
                channel.basic_publish(
                    exchange=settings.account_exchange,
                    routing_key=event_type,
                    body=message,
                    properties=properties,
                )
                logger.info(
                    "Published event %s to exchange %s",
                    event_type,
                    settings.account_exchange,
                )
            finally:
                if connection.is_open:
                    connection.close()
        except Exception as exc:
            logger.error(
                "Failed to publish event %s: %s",
                event_type,
                exc,
                exc_info=True,
            )

