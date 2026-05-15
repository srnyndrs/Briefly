"""
RabbitMQ connection and channel factory.

The crawler service uses synchronous *pika* (BlockingConnection) because the
crawl cycle is itself synchronous.  The channel is long-lived per worker; if
the connection drops it is re-created by the caller.

Usage
-----
    from config.message_broker import create_channel

    channel = create_channel()          # declare exchange, return channel
    channel.basic_publish(...)
    channel.connection.close()          # clean-up when done
"""

import logging

import pika
import pika.adapters.blocking_connection

from src.config.settings import settings

logger = logging.getLogger(__name__)


def create_channel() -> (
    pika.adapters.blocking_connection.BlockingChannel
):
    """
    Open a new BlockingConnection and declare the ``feed.content`` topic
    exchange.  Returns the ready-to-use channel.
    """
    params = pika.URLParameters(settings.rabbitmq_url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    channel.exchange_declare(
        exchange=settings.feed_exchange,
        exchange_type="topic",
        durable=True,
    )

    logger.info(
        "RabbitMQ channel ready — exchange='%s'",
        settings.feed_exchange,
    )
    return channel
