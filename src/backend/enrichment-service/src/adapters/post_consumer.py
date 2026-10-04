import json
import logging
import threading
from collections.abc import Callable
from typing import Any

import pika
from pika.adapters.blocking_connection import BlockingConnection
from pika.exceptions import AMQPConnectionError, ConnectionWrongStateError

from src.config.settings import settings

logger = logging.getLogger(__name__)


class PostConsumer:
    def __init__(self, process_event: Callable[[Any, Any], object]) -> None:
        self._process_event = process_event
        self._connection: BlockingConnection | None = None
        self._channel: Any = None
        self._stop_event = threading.Event()

    def run(self) -> None:
        delay = 1
        while not self._stop_event.is_set():
            try:
                self._connect_and_consume()
                delay = 1
            except Exception as exc:
                if self._stop_event.is_set():
                    break
                logger.error(
                    "RabbitMQ post consumer error (%s); retrying in %ds",
                    type(exc).__name__,
                    delay,
                )
                self._stop_event.wait(delay)
                delay = min(delay * 2, 60)

    def stop(self) -> None:
        self._stop_event.set()
        connection = self._connection
        if connection is not None and connection.is_open:
            try:
                connection.add_callback_threadsafe(self._safe_stop_consuming)
            except Exception:
                logger.exception("Failed to stop post consumer cleanly")

    def _safe_stop_consuming(self) -> None:
        channel = self._channel
        connection = self._connection
        if channel is not None and channel.is_open:
            channel.stop_consuming()
        if connection is not None and connection.is_open:
            connection.close()

    def _connect_and_consume(self) -> None:
        parameters = pika.URLParameters(settings.rabbitmq_url)
        parameters.blocked_connection_timeout = settings.blocked_timeout_seconds
        self._connection = pika.BlockingConnection(parameters)
        try:
            self._channel = self._connection.channel()
            self._declare_topology(self._channel)
            self._channel.confirm_delivery()
            self._channel.basic_qos(prefetch_count=1)
            self._channel.basic_consume(
                queue=settings.post_queue,
                on_message_callback=self._on_message,
            )
            logger.info("Consuming parsed posts from '%s'", settings.post_queue)
            self._channel.start_consuming()
        finally:
            if self._connection.is_open:
                self._connection.close()

    @staticmethod
    def _declare_topology(channel: Any) -> None:
        channel.exchange_declare(
            exchange=settings.parsed_exchange,
            exchange_type="topic",
            durable=True,
        )
        channel.exchange_declare(
            exchange=settings.failed_exchange,
            exchange_type="direct",
            durable=True,
        )
        channel.exchange_declare(
            exchange=settings.result_exchange,
            exchange_type="topic",
            durable=True,
        )
        channel.queue_declare(queue=settings.result_queue, durable=True)
        channel.queue_bind(
            queue=settings.result_queue,
            exchange=settings.result_exchange,
            routing_key="post.enriched.v2",
        )
        channel.queue_declare(queue=settings.post_dlq, durable=True)
        channel.queue_bind(
            queue=settings.post_dlq,
            exchange=settings.failed_exchange,
            routing_key=settings.post_failed_routing_key,
        )
        channel.queue_declare(
            queue=settings.post_queue,
            durable=True,
            arguments={
                "x-dead-letter-exchange": settings.failed_exchange,
                "x-dead-letter-routing-key": settings.post_failed_routing_key,
            },
        )
        channel.queue_bind(
            queue=settings.post_queue,
            exchange=settings.parsed_exchange,
            routing_key="post.parsed.v1",
        )

    def _on_message(
        self,
        channel: Any,
        method: Any,
        properties: Any,
        body: bytes,
    ) -> None:
        try:
            event = json.loads(body)
            self._process_event(event, channel)
        except Exception as exc:
            logger.error(
                "Parsed-post delivery rejected (delivery_tag=%s, error_type=%s)",
                method.delivery_tag,
                type(exc).__name__,
            )
            if not channel.is_open or isinstance(exc, AMQPConnectionError):
                raise
            channel.basic_nack(
                delivery_tag=method.delivery_tag,
                requeue=False,
            )
            return

        if not channel.is_open:
            raise ConnectionWrongStateError(
                "Post was persisted but consumer channel closed before ack"
            )
        channel.basic_ack(delivery_tag=method.delivery_tag)
