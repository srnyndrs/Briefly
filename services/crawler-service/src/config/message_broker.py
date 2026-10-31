import logging
import sys
from collections.abc import Iterator
from contextlib import contextmanager

import pika
from pika.adapters.blocking_connection import BlockingChannel
from pika.adapters.utils.connection_workflow import AMQPConnectorStackTimeout

from src.config.settings import settings

logger = logging.getLogger(__name__)


def create_connection_parameters() -> pika.URLParameters:
    params = pika.URLParameters(settings.rabbitmq_url)
    params.blocked_connection_timeout = settings.blocked_timeout_seconds

    return params


def broker_ready() -> bool:
    try:
        params = create_connection_parameters()
        params.connection_attempts = 1
        params.socket_timeout = 2
        params.stack_timeout = 3
        params.blocked_connection_timeout = 2
        connection = pika.BlockingConnection(params)
        connection.close()
        return True
    except (pika.exceptions.AMQPError, AMQPConnectorStackTimeout, ValueError):
        return False


@contextmanager
def publisher_channel(*, exchange: str) -> Iterator[BlockingChannel]:
    connection = pika.BlockingConnection(create_connection_parameters())
    try:
        channel = connection.channel()
        channel.exchange_declare(
            exchange=exchange, exchange_type="topic", durable=True
        )
        channel.confirm_delivery()
        logger.info("RabbitMQ exchange='%s' ready", exchange)
        yield channel
    except BaseException:
        raise
    finally:
        if connection.is_open:
            active_exception = sys.exc_info()[0] is not None
            try:
                connection.close()
            except Exception:
                if not active_exception:
                    raise
                logger.exception("RabbitMQ connection cleanup failed")
