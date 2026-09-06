import json
import logging
from datetime import UTC, datetime
from typing import Any

import pika

from src.config.settings import settings
from src.events.envelope import build_envelope

logger = logging.getLogger("account-service.events")


class AccountEventPublisher:
    def publish(
        self,
        *,
        event_type: str,
        payload: dict[str, Any],
        correlation_id: str,
        partition_key: str,
    ) -> None:
        envelope = build_envelope(
            event_type=event_type,
            partition_key=partition_key,
            payload=payload,
            correlation_id=correlation_id,
        )

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
