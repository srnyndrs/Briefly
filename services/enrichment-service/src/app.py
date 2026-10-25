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

from src.adapters.ollama_provider import OllamaProvider
from src.adapters.post_consumer import PostConsumer
from src.config.database import SessionLocal, init_db
from src.config.settings import settings
from src.repositories.enrichment_repository import EnrichmentRepository
from src.schemas.common import HealthResponse
from src.services.classification import ArticleInput
from src.services.enrichment_service import EnrichmentService
from src.services.post_processor import PostProcessor
from src.services.provider import instructions

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
    for name in (
        "pika.adapters.utils.connection_workflow",
        "pika.adapters.blocking_connection",
        "pika.adapters.utils.io_services_utils",
        "pika.adapters.utils.selector_ioloop_adapter",
    ):
        ignore_logger(name)
        ignore_logger_for_sentry_logs(name)


def create_enrichment_service() -> EnrichmentService:
    if not settings.ollama_model or not settings.ollama_model.strip():
        raise ValueError("OLLAMA_MODEL is required for runtime enrichment")

    prompt = instructions([])
    provider = OllamaProvider(
        model=settings.ollama_model,
        instructions=prompt,
        base_url=settings.ollama_base_url,
        timeout=settings.ollama_timeout_seconds,
    )
    digest = provider.model_digest()
    logger.info(
        "Ollama runtime model=%s digest=%s",
        settings.ollama_model,
        digest,
    )

    def classify(article: ArticleInput) -> tuple[str, ...]:
        return provider(article).category_ids

    return EnrichmentService(
        EnrichmentRepository(SessionLocal),
        classify,
    )


@asynccontextmanager
async def lifespan(application: FastAPI):
    try:
        if not getattr(application.state, "testing", False):
            init_db()
            consumer = PostConsumer(PostProcessor(create_enrichment_service()))
            thread = threading.Thread(
                target=consumer.run,
                daemon=True,
                name="rabbitmq-consumer",
            )
            application.state.consumer = consumer
            application.state.consumer_thread = thread
            thread.start()
            logger.info("Enrichment Service started on port=%d", settings.app_port)

        yield
    finally:
        consumer: PostConsumer | None = getattr(application.state, "consumer", None)
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
