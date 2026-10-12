import logging
import threading
from contextlib import asynccontextmanager

import sentry_sdk
import uvicorn
from fastapi import FastAPI
from sentry_sdk.integrations.logging import LoggingIntegration

from src.adapters.post_consumer import PostConsumer
from src.bootstrap import create_post_processor
from src.config.database import init_db
from src.config.settings import settings
from src.schemas.common import HealthResponse

TAG_NAME = "enrichment-service"

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


@asynccontextmanager
async def lifespan(application: FastAPI):
    try:
        if not getattr(application.state, "testing", False):
            init_db()
            consumer = PostConsumer(create_post_processor())
            thread = threading.Thread(
                target=consumer.run,
                daemon=True,
                name="rabbitmq-consumer",
            )
            application.state.consumer = consumer
            application.state.consumer_thread = thread
            thread.start()
            logger.info(
                "Enrichment Service started on port=%d", settings.app_port
            )

        yield
    finally:
        consumer: PostConsumer | None = getattr(
            application.state, "consumer", None
        )
        if consumer:
            consumer.stop()

        thread: threading.Thread | None = getattr(
            application.state, "consumer_thread", None
        )
        if thread and thread.is_alive():
            thread.join(timeout=5)

        logger.info("Enrichment Service stopped.")


app = FastAPI(
    title="Enrichment Service",
    description="Enriches parsed posts with derived metadata.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse, tags=["ops"])
def health() -> HealthResponse:
    return HealthResponse(status="ok", service=TAG_NAME)


if __name__ == "__main__":
    uvicorn.run(
        "src.app:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.env == "development",
    )
