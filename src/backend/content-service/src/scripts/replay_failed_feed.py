import argparse
import json
from typing import Any

import pika

from src.config.settings import settings


def replay_failed_feed(channel: Any, event_id: str) -> bool:
    method, properties, body = channel.basic_get(
        queue=settings.feed_dlq
    )
    if method is None:
        return False
    try:
        event = json.loads(body)
        if (
            not isinstance(event, dict)
            or event.get("event_id") != event_id
        ):
            raise ValueError(
                "Next failed feed does not match the requested event ID"
            )
        if event.get("event_type") != "feed.raw_fetched.v1":
            raise ValueError(
                "Failed message is not a feed.raw_fetched.v1 event"
            )
        channel.basic_publish(
            exchange=settings.feed_exchange,
            routing_key="feed.raw_fetched.v1",
            body=body,
            properties=properties,
            mandatory=True,
        )
    except Exception:
        if channel.is_open:
            channel.basic_nack(
                delivery_tag=method.delivery_tag, requeue=True
            )
        raise
    channel.basic_ack(delivery_tag=method.delivery_tag)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "event_id", help="Expected event ID at the head of the DLQ"
    )
    args = parser.parse_args()
    params = pika.URLParameters(settings.rabbitmq_url)
    params.blocked_connection_timeout = (
        settings.rabbitmq_blocked_timeout_seconds
    )
    with pika.BlockingConnection(params) as connection:
        channel = connection.channel()
        channel.confirm_delivery()
        if not replay_failed_feed(channel, args.event_id):
            print("DLQ is empty.")
            return 1
    print("Original feed republished and removed from the DLQ.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
