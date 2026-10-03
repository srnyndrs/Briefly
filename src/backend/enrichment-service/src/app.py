import logging
import threading
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI

from src.adapters.post_consumer import PostConsumer
from src.config.database import init_db
from src.config.settings import settings
from src.schemas.common import HealthResponse

TAG_NAME = "enrichment-service"

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(TAG_NAME)


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    if not getattr(application.state, "testing", False):
        init_db()
        processor: Callable[[Any, Any], object] | None = getattr(
            application.state, "post_event_processor", None
        )
        if settings.post_consumer_enabled:
            if processor is None:
                raise RuntimeError(
                    "POST_CONSUMER_ENABLED requires a configured post_event_processor"
                )
            consumer = PostConsumer(processor)
            consumer_thread = threading.Thread(
                target=consumer.run,
                daemon=True,
                name="enrichment-post-consumer",
            )
            consumer_thread.start()
            application.state.consumer = consumer
            application.state.consumer_thread = consumer_thread
        else:
            logger.info("Parsed-post consumption disabled")
        logger.info("Enrichment Service started on port=%d", settings.app_port)

    yield

    consumer: PostConsumer | None = getattr(application.state, "consumer", None)
    if consumer is not None:
        consumer.stop()
    consumer_thread: threading.Thread | None = getattr(
        application.state, "consumer_thread", None
    )
    if consumer_thread is not None:
        consumer_thread.join(timeout=5)

    logger.info("Enrichment Service stopped.")


app = FastAPI(
    title="Enrichment Service",
    description="Enriches parsed posts with derived metadata.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse, tags=["ops"])
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service=TAG_NAME)


if __name__ == "__main__":
    uvicorn.run(
        "src.app:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.env == "development",
    )
