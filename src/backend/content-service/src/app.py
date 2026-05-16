import json
import logging
import threading
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI

from src.config.database import SessionLocal, init_db
from src.config.message_broker import create_channel
from src.config.settings import settings
from src.routers import articles
from src.schemas.common import HealthResponse
from src.services.feed_processor import FeedProcessorService

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("content-service")


def _on_message(
    ch: Any, method: Any, properties: Any, body: bytes
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


def _start_consumer() -> None:
    import time

    delay = 1
    while True:
        try:
            channel = create_channel()
            channel.basic_qos(prefetch_count=5)
            channel.basic_consume(
                queue=settings.feed_queue,
                on_message_callback=_on_message,
            )
            logger.info(
                "Waiting for messages on '%s'...",
                settings.feed_queue,
            )
            delay = 1  # reset after a successful connect
            channel.start_consuming()
        except Exception as exc:
            logger.error(
                "RabbitMQ consumer error: %s — retrying in %ds",
                exc,
                delay,
            )
            time.sleep(delay)
            delay = min(delay * 2, 60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not getattr(app.state, "testing", False):
        init_db()
        logger.info(
            "Content Service started on port=%d", settings.app_port
        )
        t = threading.Thread(
            target=_start_consumer,
            daemon=True,
            name="rabbitmq-consumer",
        )
        t.start()

    yield
    logger.info("Content Service stopped")


app = FastAPI(
    title="Content Service",
    description=(
        "Consumes feed.raw_fetched.v1 events, "
        "extracts articles, stores in PostgreSQL."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse, tags=["ops"])
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="content-service")


app.include_router(articles.router)


if __name__ == "__main__":
    uvicorn.run(
        "src.app:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.env == "development",
    )
