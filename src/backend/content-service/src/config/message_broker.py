import logging

import pika
import pika.adapters.blocking_connection

from src.config.settings import settings

logger = logging.getLogger(__name__)


def create_channel() -> (
    pika.adapters.blocking_connection.BlockingChannel
):
    params = pika.URLParameters(settings.rabbitmq_url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    # Declare both exchanges
    channel.exchange_declare(
        exchange=settings.feed_exchange,
        exchange_type="topic",
        durable=True,
    )
    channel.exchange_declare(
        exchange=settings.parsed_exchange,
        exchange_type="topic",
        durable=True,
    )

    # Durable queue bound to feed.content exchange
    channel.queue_declare(queue=settings.feed_queue, durable=True)
    channel.queue_bind(
        queue=settings.feed_queue,
        exchange=settings.feed_exchange,
        routing_key="feed.raw_fetched.v1",
    )

    logger.info(
        "RabbitMQ ready — consuming '%s'", settings.feed_queue
    )
    return channel
