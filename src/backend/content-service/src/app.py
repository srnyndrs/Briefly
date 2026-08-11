import logging
import threading
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from src.config.database import init_db
from src.config.settings import settings
from src.routers import admin, articles
from src.schemas.common import HealthResponse
from src.services.consumer import FeedConsumer

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("content-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not getattr(app.state, "testing", False):
        init_db()
        logger.info(
            "Content Service started on port=%d", settings.app_port
        )
        consumer = FeedConsumer()
        thread = threading.Thread(
            target=consumer.run,
            daemon=True,
            name="rabbitmq-consumer",
        )
        thread.start()
        app.state.consumer = consumer
        app.state.consumer_thread = thread

    yield

    consumer: FeedConsumer | None = getattr(
        app.state, "consumer", None
    )
    if consumer:
        consumer.stop()
    thread: threading.Thread | None = getattr(
        app.state, "consumer_thread", None
    )
    if thread:
        thread.join(timeout=5)

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
app.include_router(admin.router)


if __name__ == "__main__":
    uvicorn.run(
        "src.app:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.env == "development",
    )
