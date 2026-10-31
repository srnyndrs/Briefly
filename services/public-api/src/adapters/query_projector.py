import json
import logging
import threading
from datetime import UTC, datetime
from typing import Any

from pika.adapters.blocking_connection import (
    BlockingChannel,
    BlockingConnection,
)
from pika.exceptions import (
    AMQPConnectionError,
    ChannelClosed,
    ChannelWrongStateError,
)
from sqlalchemy.exc import InterfaceError, OperationalError, TimeoutError
from sqlalchemy.orm import Session, sessionmaker

from src.config.message_broker import create_connection_parameters
from src.config.settings import settings
from src.models.read_models import ProcessedEvent
from src.services.projection_handlers import (
    project_enrichment,
    project_post,
    project_post_deleted,
    project_user_preferences,
)

logger = logging.getLogger(__name__)


class QueryProjector:
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory
        self._connection: BlockingConnection | None = None
        self._channel: BlockingChannel | None = None
        self._stop_event = threading.Event()
        self._consuming = threading.Event()

    @property
    def is_consuming(self) -> bool:
        return self._consuming.is_set() and not self._stop_event.is_set()

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
                    "Projector error: %s — retrying in %ds",
                    type(exc).__name__,
                    delay,
                )

                if self._stop_event.wait(delay):
                    break

                delay = min(delay * 2, 60)

    def stop(self) -> None:
        self._stop_event.set()
        if self._connection and self._connection.is_open:
            try:
                self._connection.add_callback_threadsafe(self._safe_stop_consuming)
            except Exception:
                logger.exception("Failed to stop projector cleanly")

    def _safe_stop_consuming(self) -> None:
        if self._channel and self._channel.is_open:
            self._channel.stop_consuming()

        if self._connection and self._connection.is_open:
            self._connection.close()

    def _connect_and_consume(self) -> None:
        connection = BlockingConnection(create_connection_parameters())
        self._connection = connection

        try:
            if self._stop_event.is_set():
                return
            self._channel = connection.channel()
            self._channel.basic_qos(prefetch_count=20)

            self._channel.exchange_declare(
                exchange=settings.account_exchange,
                exchange_type="topic",
                durable=True,
            )
            self._channel.exchange_declare(
                exchange=settings.content_exchange,
                exchange_type="topic",
                durable=True,
            )
            self._channel.exchange_declare(
                exchange=settings.enrichment_exchange,
                exchange_type="topic",
                durable=True,
            )
            self._channel.queue_declare(queue=settings.query_queue, durable=True)
            self._channel.queue_bind(
                queue=settings.query_queue,
                exchange=settings.account_exchange,
                routing_key="preferences.updated.v1",
            )
            self._channel.queue_bind(
                queue=settings.query_queue,
                exchange=settings.content_exchange,
                routing_key="post.parsed.v1",
            )
            self._channel.queue_bind(
                queue=settings.query_queue,
                exchange=settings.content_exchange,
                routing_key="post.deleted.v1",
            )
            self._channel.queue_bind(
                queue=settings.query_queue,
                exchange=settings.enrichment_exchange,
                routing_key="post.enriched.v1",
            )

            logger.info(
                "Query projector consuming queue=%s",
                settings.query_queue,
            )
            self._channel.basic_consume(
                queue=settings.query_queue,
                on_message_callback=self._on_message,
            )
            if self._stop_event.is_set():
                return
            self._consuming.set()
            self._channel.start_consuming()
        finally:
            self._consuming.clear()
            try:
                if connection.is_open:
                    connection.close()
            finally:
                if self._connection is connection:
                    self._channel = None
                    self._connection = None

    def _on_message(self, ch: Any, method: Any, props: Any, body: bytes) -> None:
        if self._stop_event.is_set():
            return

        try:
            event = self._decode_message(body)
            if event is None:
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            event_id = event.get("event_id")
            event_type = event.get("event_type")
            payload = event.get("payload") or {}

            if event_type == "post.enriched.v1" and (
                type(event.get("schema_version")) is not int
                or event["schema_version"] != 1
            ):
                raise ValueError("Invalid enrichment schema version")

            if not event_id or not event_type:
                logger.warning("Dropping event with missing id/type")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            with self._session_factory() as db:
                already = db.get(ProcessedEvent, event_id)
                if already is not None:
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    return

                self._apply_event(db, event_type, payload)
                db.add(
                    ProcessedEvent(
                        event_id=event_id,
                        processed_at=datetime.now(UTC),
                    )
                )
                db.commit()

            ch.basic_ack(delivery_tag=method.delivery_tag)
        except (
            AMQPConnectionError,
            ChannelClosed,
            ChannelWrongStateError,
            InterfaceError,
            OperationalError,
            TimeoutError,
        ):
            raise
        except Exception:
            logger.exception("Unhandled projector message error")
            if not ch.is_open:
                raise
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    @staticmethod
    def _apply_event(db: Session, event_type: str, payload: dict[str, Any]) -> None:
        if event_type == "post.parsed.v1":
            project_post(db, payload)
        elif event_type == "post.enriched.v1":
            project_enrichment(db, payload)
        elif event_type == "post.deleted.v1":
            project_post_deleted(db, payload)
        elif event_type == "preferences.updated.v1":
            project_user_preferences(db, payload)

    @staticmethod
    def _decode_message(body: bytes) -> dict[str, Any] | None:
        try:
            return json.loads(body)
        except Exception:
            logger.exception("Invalid JSON event payload")

            return None
