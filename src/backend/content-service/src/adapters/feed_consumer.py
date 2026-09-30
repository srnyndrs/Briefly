import json
import logging
import threading
import time
from typing import Any

import pika
from pika.adapters.blocking_connection import BlockingConnection, BlockingChannel
from pika.exceptions import AMQPConnectionError, ConnectionWrongStateError

from src.config.database import SessionLocal
from src.config.settings import settings
from src.services.source_processor import SourceProcessorService

logger = logging.getLogger(__name__)


class FeedConsumer:
    def __init__(self) -> None:
        self._connection: BlockingConnection | None = None
        self._channel: BlockingChannel | None = None
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
                    "RabbitMQ consumer error: %s — retrying in %ds",
                    exc,
                    delay,
                )
                time.sleep(delay)
                delay = min(delay * 2, 60)

    def stop(self) -> None:
        self._stop_event.set()
        if self._connection and self._connection.is_open:
            try:
                self._connection.add_callback_threadsafe(
                    self._safe_stop_consuming
                )
            except Exception:
                logger.exception("Failed to stop consumer cleanly")

    def _safe_stop_consuming(self) -> None:
        if self._channel and self._channel.is_open:
            self._channel.stop_consuming()
        if self._connection and self._connection.is_open:
            self._connection.close()

    def _connect_and_consume(self) -> None:
        params = pika.URLParameters(settings.rabbitmq_url)
        params.blocked_connection_timeout = settings.blocked_timeout_seconds
        self._connection = BlockingConnection(params)
        try:
            self._channel = self._connection.channel()
            self._channel.basic_qos(prefetch_count=1)

            self._channel.exchange_declare(
                exchange=settings.feed_exchange,
                exchange_type="topic",
                durable=True,
            )
            self._channel.exchange_declare(
                exchange=settings.parsed_exchange,
                exchange_type="topic",
                durable=True,
            )
            self._channel.exchange_declare(
                exchange=settings.failed_exchange,
                exchange_type="direct",
                durable=True,
            )
            self._channel.queue_declare(
                queue=settings.feed_dlq,
                durable=True
            )
            self._channel.queue_bind(
                queue=settings.feed_dlq,
                exchange=settings.failed_exchange,
                routing_key="feed.failed",
            )
            self._channel.queue_declare(
                queue=settings.feed_queue,
                durable=True
            )
            self._channel.queue_bind(
                queue=settings.feed_queue,
                exchange=settings.feed_exchange,
                routing_key="feed.raw_fetched.v1",
            )
            self._channel.confirm_delivery()

            logger.info(
                "Waiting for messages on '%s'...", settings.feed_queue
            )
            self._channel.basic_consume(
                queue=settings.feed_queue,
                on_message_callback=self._on_message,
            )
            self._channel.start_consuming()
        finally:
            if self._connection.is_open:
                self._connection.close()

    def _service_connection(self) -> None:
        if self._connection is None or not self._connection.is_open:
            raise ConnectionWrongStateError("Consumer connection is closed")
        self._connection.process_data_events(time_limit=0)

    def _on_message(
        self, ch: Any, method: Any, properties: Any, body: bytes
    ) -> None:
        try:
            event = json.loads(body)
            db = SessionLocal()
            try:
                SourceProcessorService(db).process(
                    ch, event, on_progress=self._service_connection
                )
            finally:
                db.close()
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as exc:
            logger.error(
                "Feed processing failed (delivery_tag=%s, error_type=%s)",
                method.delivery_tag,
                type(exc).__name__,
            )
            if not ch.is_open or isinstance(exc, AMQPConnectionError):
                raise
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
