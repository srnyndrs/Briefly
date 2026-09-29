import logging

import pika
import pika.adapters.blocking_connection

from src.config.settings import settings

logger = logging.getLogger(__name__)


def create_replay_publisher_channel() -> (
    pika.adapters.blocking_connection.BlockingChannel
):
    params = pika.URLParameters(settings.rabbitmq_url)
    params.blocked_connection_timeout = (
        settings.rabbitmq_blocked_timeout_seconds
    )
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    channel.exchange_declare(
        exchange=settings.parsed_exchange,
        exchange_type="topic",
        durable=True,
    )
    channel.confirm_delivery()

    logger.info(
        "RabbitMQ channel ready - exchange='%s'",
        settings.parsed_exchange,
    )
    return channel
