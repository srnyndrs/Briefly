import json
from datetime import UTC, datetime
from typing import Any

import pika
from pika.adapters.blocking_connection import BlockingChannel


def publish_event(
    channel: BlockingChannel,
    *,
    exchange: str,
    envelope: dict[str, Any],
) -> None:
    event_type = envelope["event_type"]
    occurred_at = datetime.fromisoformat(
        envelope["occurred_at"].replace("Z", "+00:00")
    )

    if occurred_at.tzinfo is None:
        occurred_at = occurred_at.replace(tzinfo=UTC)

    channel.basic_publish(
        exchange=exchange,
        routing_key=event_type,
        body=json.dumps(envelope, ensure_ascii=False).encode("utf-8"),
        mandatory=True,
        properties=pika.BasicProperties(
            delivery_mode=pika.DeliveryMode.Persistent,
            content_type="application/json",
            message_id=envelope["event_id"],
            type=event_type,
            correlation_id=envelope.get("correlation_id"),
            timestamp=int(occurred_at.timestamp()),
        ),
    )
