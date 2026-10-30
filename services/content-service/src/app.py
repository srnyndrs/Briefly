import logging
import threading
from contextlib import asynccontextmanager

import sentry_sdk
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sentry_sdk.integrations.logging import (
    LoggingIntegration,
    ignore_logger,
    ignore_logger_for_sentry_logs,
)
from sqlalchemy.orm import Session

from src.adapters.feed_consumer import FeedConsumer
from src.config.database import database_ready, init_db
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
        "pika.adapters.utils.io_services_utils",
        "pika.adapters.utils.selector_ioloop_adapter",
    ):
        ignore_logger(name)
        ignore_logger_for_sentry_logs(name)


def _create_feed_processor(db: Session) -> FeedProcessor:
    return FeedProcessor(PostRepository(db))


@asynccontextmanager
async def lifespan(application: FastAPI):
    application.state.started = False
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

        application.state.started = True
        yield
    finally:
        application.state.started = False
        consumer: FeedConsumer | None = getattr(application.state, "consumer", None)
        if consumer:
            consumer.stop()

        thread: threading.Thread | None = getattr(
            application.state, "consumer_thread", None
        )
        if thread and thread.is_alive():
            thread.join(timeout=settings.shutdown_timeout_seconds)

        if thread and thread.is_alive():
            logger.warning(
                "Background shutdown deadline reached; process termination must stop remaining work."
            )
        else:
            logger.info("Content Service stopped.")


app = FastAPI(
    title="Content Service",
    description="Parses RSS feeds and extracts article contents.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse, tags=["ops"])
def health() -> HealthResponse:
    return HealthResponse(status="ok", service=TAG_NAME)


@app.get("/live", response_model=HealthResponse, tags=["ops"])
def live() -> HealthResponse | JSONResponse:
    if not getattr(app.state, "started", False):
        return JSONResponse(
            status_code=503, content={"detail": "Service has not started"}
        )

    thread = getattr(app.state, "consumer_thread", None)
    if thread is None or not thread.is_alive():
        return JSONResponse(
            status_code=503, content={"detail": "Consumer is not running"}
        )

    return HealthResponse(status="ok", service=TAG_NAME)


@app.get("/ready", response_model=HealthResponse, tags=["ops"])
def ready() -> HealthResponse | JSONResponse:
    result = live()
    if isinstance(result, JSONResponse):
        return result
    if (
        not getattr(app.state, "consumer", None)
        or not app.state.consumer.is_consuming
        or not database_ready()
    ):
        return JSONResponse(
            status_code=503, content={"detail": "Service is not ready"}
        )

    return result


app.include_router(posts.router)
app.include_router(admin.router)


if __name__ == "__main__":
    uvicorn.run(
        "src.app:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.env == "development",
        timeout_graceful_shutdown=10,
    )
