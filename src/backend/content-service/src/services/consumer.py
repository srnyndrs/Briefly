import json
import logging
import threading
import time
from typing import Any

import pika

from src.config.database import SessionLocal
from src.config.settings import settings
from src.services.feed_processor import FeedProcessorService

logger = logging.getLogger("content-service.consumer")


class FeedConsumer:
    def __init__(self) -> None:
        self._connection: pika.BlockingConnection | None = None
        self._channel: (
            pika.adapters.blocking_connection.BlockingChannel | None
        ) = None
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
        self._connection = pika.BlockingConnection(params)
        self._channel = self._connection.channel()
        self._channel.basic_qos(prefetch_count=5)

        self._channel.exchange_declare(
            exchange=settings.feed_exchange,
            exchange_type="topic",
            durable=True,
        )
        self._channel.queue_declare(
            queue=settings.feed_queue, durable=True
        )
        self._channel.queue_bind(
            queue=settings.feed_queue,
            exchange=settings.feed_exchange,
            routing_key="feed.raw_fetched.v1",
        )

        logger.info(
            "Waiting for messages on '%s'...", settings.feed_queue
        )
        self._channel.basic_consume(
            queue=settings.feed_queue,
            on_message_callback=self._on_message,
        )
        self._channel.start_consuming()

    def _on_message(
        self, ch: Any, method: Any, properties: Any, body: bytes
    ) -> None:
        try:
            event = json.loads(body)
            db = SessionLocal()
            try:
                FeedProcessorService(db).process(ch, event)
            finally:
                db.close()
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as exc:
            logger.exception(
                "Unhandled error processing message: %s", exc
            )
            ch.basic_nack(
                delivery_tag=method.delivery_tag, requeue=False
            )
