import logging
import threading
from contextlib import asynccontextmanager

import sentry_sdk
import uvicorn
from fastapi import FastAPI
from sentry_sdk.integrations.logging import (
    LoggingIntegration,
    ignore_logger,
    ignore_logger_for_sentry_logs,
)
from sqlalchemy.orm import Session

from src.adapters.feed_consumer import FeedConsumer
from src.config.database import init_db
from src.config.settings import settings
from src.repositories.post_repository import PostRepository
from src.routers import admin, posts
from src.schemas.common import HealthResponse
from src.services.feed_processor import FeedProcessor

TAG_NAME = "content-service"

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.env,
        integrations=[LoggingIntegration(sentry_logs_level=logging.WARNING)],
        enable_logs=True,
    )
    for name in (
        "pika.adapters.utils.connection_workflow",
        "pika.adapters.blocking_connection",
    ):
        ignore_logger(name)
        ignore_logger_for_sentry_logs(name)


def _create_feed_processor(db: Session) -> FeedProcessor:
    return FeedProcessor(PostRepository(db))


@asynccontextmanager
async def lifespan(application: FastAPI):
    try:
        if not getattr(application.state, "testing", False):
            init_db()
            consumer = FeedConsumer(_create_feed_processor)
            thread = threading.Thread(
                target=consumer.run,
                daemon=True,
                name="rabbitmq-consumer",
            )
            application.state.consumer = consumer
            application.state.consumer_thread = thread
            thread.start()
            logger.info("Content Service started on port=%d", settings.app_port)

        yield
    finally:
        consumer: FeedConsumer | None = getattr(
            application.state, "consumer", None
        )
        if consumer:
            consumer.stop()

        thread: threading.Thread | None = getattr(
            application.state, "consumer_thread", None
        )
        if thread and thread.is_alive():
            thread.join(timeout=5)

        logger.info("Content Service stopped.")


app = FastAPI(
    title="Content Service",
    description="Parses RSS feeds and extracts article content.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse, tags=["ops"])
def health() -> HealthResponse:
    return HealthResponse(status="ok", service=TAG_NAME)


app.include_router(posts.router)
app.include_router(admin.router)


if __name__ == "__main__":
    uvicorn.run(
        "src.app:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.env == "development",
    )
