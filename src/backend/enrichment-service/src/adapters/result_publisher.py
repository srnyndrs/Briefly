import json
from typing import Any

import pika

from src.config.settings import settings


def publish_result(channel: Any, event: dict) -> None:
    confirmed = channel.basic_publish(
        exchange=settings.result_exchange,
        routing_key="post.enriched.v1",
        body=json.dumps(event, ensure_ascii=False).encode("utf-8"),
        mandatory=True,
        properties=pika.BasicProperties(
            delivery_mode=pika.DeliveryMode.Persistent,
            content_type="application/json",
        ),
    )
    if confirmed is False:
        raise RuntimeError("Result publication was not confirmed")
