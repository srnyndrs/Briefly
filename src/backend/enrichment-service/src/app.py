import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

import uvicorn
from fastapi import FastAPI

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
async def lifespan(application: FastAPI):
    if not getattr(application.state, "testing", False):
        init_db()
        logger.info("Enrichment Service started on port=%d", settings.app_port)

    yield

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
