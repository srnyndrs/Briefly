import json
import logging
import threading
import time
from datetime import UTC, datetime
from typing import Any

import pika
from sqlalchemy.orm import Session, sessionmaker

from src.config.settings import settings
from src.models.read_models import ProcessedEvent
from src.services.projection_use_cases import (
    CreateSubscriptionInput,
    CreateSubscriptionUseCase,
    DeleteSubscriptionInput,
    DeleteSubscriptionUseCase,
    ProjectArticleInput,
    ProjectArticleUseCase,
    ProjectUserPreferencesInput,
    ProjectUserPreferencesUseCase,
)

logger = logging.getLogger("public-api.projector")


class QueryProjector:
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory
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
                    "Projector error: %s — retrying in %ds",
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
                logger.exception("Failed to stop projector cleanly")

    def _safe_stop_consuming(self) -> None:
        if self._channel and self._channel.is_open:
            self._channel.stop_consuming()
        if self._connection and self._connection.is_open:
            self._connection.close()

    def _connect_and_consume(self) -> None:
        params = pika.URLParameters(settings.rabbitmq_url)
        self._connection = pika.BlockingConnection(params)
        self._channel = self._connection.channel()
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

        self._channel.queue_declare(
            queue=settings.query_queue, durable=True
        )

        for key in (
            "preferences.updated.v1",
            "subscription.created.v1",
            "subscription.deleted.v1",
        ):
            self._channel.queue_bind(
                queue=settings.query_queue,
                exchange=settings.account_exchange,
                routing_key=key,
            )

        for key in ("article.parsed.v1",):
            self._channel.queue_bind(
                queue=settings.query_queue,
                exchange=settings.content_exchange,
                routing_key=key,
            )

        self._channel.basic_consume(
            queue=settings.query_queue,
            on_message_callback=self._on_message,
        )
        logger.info(
            "Query projector consuming queue=%s",
            settings.query_queue,
        )
        self._channel.start_consuming()

    def _on_message(
        self,
        ch: Any,
        method: Any,
        properties: Any,
        body: bytes,
    ) -> None:
        _ = properties
        try:
            event = self._decode_message(body)
            if event is None:
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            event_id = event.get("event_id")
            event_type = event.get("event_type")
            payload = event.get("payload") or {}

            if not event_id or not event_type:
                logger.warning(
                    "Dropping event with missing id/type"
                )
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            db = self._session_factory()
            try:
                already = db.get(
                    ProcessedEvent,
                    {
                        "event_id": event_id,
                        "consumer_name": "public-api.query-projector",
                    },
                )
                if already is not None:
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    return

                self._apply_event(db, event_type, payload)
                db.add(
                    ProcessedEvent(
                        event_id=event_id,
                        consumer_name="public-api.query-projector",
                        processed_at=datetime.now(UTC),
                    )
                )
                db.commit()
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception:
                db.rollback()
                logger.exception(
                    "Failed processing event_type=%s event_id=%s",
                    event_type,
                    event_id,
                )
                ch.basic_nack(
                    delivery_tag=method.delivery_tag,
                    requeue=False,
                )
            finally:
                db.close()
        except Exception:
            logger.exception("Unhandled projector message error")
            ch.basic_nack(
                delivery_tag=method.delivery_tag, requeue=False
            )

    def _apply_event(
        self, db: Session, event_type: str, payload: dict[str, Any]
    ) -> None:
        """Route event to appropriate use-case."""
        if event_type == "article.parsed.v1":
            article_id = payload.get("article_id")
            if article_id:
                ProjectArticleUseCase(db).execute(
                    ProjectArticleInput(
                        article_id=article_id, payload=payload
                    )
                )
        elif event_type == "preferences.updated.v1":
            user_id = payload.get("user_id")
            if user_id:
                ProjectUserPreferencesUseCase(db).execute(
                    ProjectUserPreferencesInput(
                        user_id=user_id, payload=payload
                    )
                )
        elif event_type == "subscription.created.v1":
            user_id = payload.get("user_id")
            source_id = payload.get("source_id")
            if user_id and source_id:
                CreateSubscriptionUseCase(db).execute(
                    CreateSubscriptionInput(
                        user_id=user_id,
                        source_id=source_id,
                        payload=payload,
                    )
                )
        elif event_type == "subscription.deleted.v1":
            user_id = payload.get("user_id")
            source_id = payload.get("source_id")
            if user_id and source_id:
                DeleteSubscriptionUseCase(db).execute(
                    DeleteSubscriptionInput(
                        user_id=user_id, source_id=source_id
                    )
                )

    @staticmethod
    def _decode_message(body: bytes) -> dict[str, Any] | None:
        try:
            return json.loads(body)
        except Exception:
            logger.exception("Invalid JSON event payload")
            return None
