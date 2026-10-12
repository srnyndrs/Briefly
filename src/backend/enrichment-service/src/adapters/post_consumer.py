import json
import logging
import threading
from functools import partial
from typing import Any

import pika
from pika.adapters.blocking_connection import (
    BlockingConnection,
    BlockingChannel,
)
from pika.exceptions import AMQPConnectionError, ConnectionWrongStateError

from src.config.settings import settings
from src.repositories.enrichment_repository import StoredEnrichment
from src.services.post_processor import PostEventProcessor

logger = logging.getLogger(__name__)


class PostConsumer:
    def __init__(self, process_event: PostEventProcessor) -> None:
        self._process_event = process_event
        self._connection: BlockingConnection | None = None
        self._channel: BlockingChannel | None = None
        self._stop_event = threading.Event()
        self._worker: threading.Thread | None = None # Why?

    def run(self) -> None:
        delay = 1
        while not self._stop_event.is_set():
            try:
                ### ---
                while self._worker is not None and self._worker.is_alive():
                    self._worker.join(timeout=0.1)
                    if self._stop_event.is_set():
                        return
                ### ---
                self._connect_and_consume()
                delay = 1
            except Exception as exc:
                if self._stop_event.is_set():
                    break
                logger.error(
                    "RabbitMQ consumer error: %s - retrying in %ds",
                    exc,
                    delay,
                )
                # time.sleep(delay)
                self._stop_event.wait(delay)
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
                exchange=settings.parsed_exchange,
                exchange_type="topic",
                durable=True,
            )
            self._channel.exchange_declare(
                exchange=settings.failed_exchange,
                exchange_type="direct",
                durable=True,
            )
            self._channel.exchange_declare(
                exchange=settings.result_exchange,
                exchange_type="topic",
                durable=True,
            )
            self._channel.queue_declare(
                queue=settings.post_dlq,
                durable=True,
            )
            self._channel.queue_bind(
                queue=settings.post_dlq,
                exchange=settings.failed_exchange,
                routing_key=settings.post_failed_routing_key,
            )
            self._channel.queue_declare(
                queue=settings.post_queue,
                durable=True,
                arguments={
                    "x-dead-letter-exchange": settings.failed_exchange,
                    "x-dead-letter-routing-key": settings.post_failed_routing_key,
                },
            )
            self._channel.queue_bind(
                queue=settings.post_queue,
                exchange=settings.parsed_exchange,
                routing_key="post.parsed.v1",
            )
            self._channel.confirm_delivery()

            logger.info("Waiting for messages on '%s'...", settings.post_queue)
            self._channel.basic_consume(
                queue=settings.post_queue,
                on_message_callback=self._on_message,
            )
            self._channel.start_consuming()
        finally:
            if self._connection.is_open:
                self._connection.close()
            self._channel = None # Why
            self._connection = None # Why

    def _service_connection(self) -> None:
        if self._connection is None or not self._connection.is_open:
            raise ConnectionWrongStateError("Consumer connection is closed")
        self._connection.process_data_events(time_limit=0)

    def _on_message(
        self, ch: Any, method: Any, properties: Any, body: bytes
    ) -> None:
        if self._stop_event.is_set():
            return
        connection = self._connection
        if connection is None:
            raise ConnectionWrongStateError(
                "Delivery has no consumer connection"
            )
        self._worker = threading.Thread(
            target=self._process_delivery,
            args=(connection, method.delivery_tag, body),
            daemon=True,
            name="enrichment-worker",
        )
        self._worker.start()

    def _process_delivery(
        self, connection: BlockingConnection, delivery_tag: int, body: bytes
    ) -> None:
        saved = None
        error = None
        try:
            saved = self._process_event(json.loads(body))
        except Exception as exc:
            error = exc
        self._schedule(connection, self._complete, delivery_tag, saved, error)

    @staticmethod
    def _schedule(
        connection: BlockingConnection, callback: Any, *args: Any
    ) -> None:
        try:
            connection.add_callback_threadsafe(
                partial(callback, connection, *args)
            )
        except ConnectionWrongStateError:
            logger.info(
                "Connection closed before delivery completion; awaiting redelivery"
            )

    def _is_current(self, connection: BlockingConnection) -> bool:
        return (
            not self._stop_event.is_set()
            and connection is self._connection
            and connection.is_open
            and self._channel is not None
            and self._channel.is_open
        )

    def _complete(
        self,
        connection: BlockingConnection,
        delivery_tag: int,
        saved: StoredEnrichment | None,
        error: Exception | None,
    ) -> None:
        if not self._is_current(connection):
            return
        if error is not None or saved is None:
            self._settle(connection, delivery_tag, saved, error)
            return
        if not saved.publication_pending:
            self._settle(connection, delivery_tag, saved, None)
            return
        try:
            self._process_event.publish(saved, self._channel)
        except Exception as exc:
            self._settle(connection, delivery_tag, saved, exc)
            return
        self._worker = threading.Thread(
            target=self._mark_delivery,
            args=(connection, delivery_tag, saved),
            daemon=True,
            name="enrichment-worker",
        )
        self._worker.start()

    def _mark_delivery(
        self,
        connection: BlockingConnection,
        delivery_tag: int,
        saved: StoredEnrichment,
    ) -> None:
        error = None
        try:
            saved = self._process_event.mark_published(saved)
        except Exception as exc:
            error = exc
        self._schedule(connection, self._settle, delivery_tag, saved, error)

    def _settle(
        self,
        connection: BlockingConnection,
        delivery_tag: int,
        saved: StoredEnrichment | None,
        error: Exception | None,
    ) -> None:
        if not self._is_current(connection):
            return
        channel = self._channel
        if error is not None or saved is None or saved.status == "failed":
            logger.error(
                "Parsed-post delivery rejected (delivery_tag=%s, error_type=%s)",
                delivery_tag,
                type(error).__name__
                if error is not None
                else "classifier_error",
            )
            if isinstance(error, AMQPConnectionError):
                raise error
            channel.basic_nack(
                delivery_tag=delivery_tag,
                requeue=False,
            )
            return

        channel.basic_ack(delivery_tag=delivery_tag)
