import logging
import threading
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from src.config.database import init_db, SessionLocal
from src.config.settings import settings
from src.routers.auth import router as auth_router
from src.routers.feed import admin_router, router as feed_router
from src.routers.sources import router as sources_router
from src.routers.user import router as user_router
from src.schemas.api import HealthResponse
from src.services.projector import QueryProjector

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("public-api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not getattr(app.state, "testing", False):
        init_db()

        app.state.projector = None
        app.state.projector_thread = None
        if settings.query_consumer_enabled:
            projector = QueryProjector(SessionLocal)
            thread = threading.Thread(
                target=projector.run,
                daemon=True,
                name="rabbitmq-projector",
            )
            thread.start()
            app.state.projector = projector
            app.state.projector_thread = thread

        logger.info(
            "Public API started on port=%d", settings.app_port
        )

    yield

    projector: QueryProjector | None = getattr(
        app.state, "projector", None
    )
    if projector:
        projector.stop()

    thread: threading.Thread | None = getattr(
        app.state, "projector_thread", None
    )
    if thread:
        thread.join(timeout=5)

    logger.info("Public API stopped")


app = FastAPI(
    title="Public API",
    description="Gateway API with JWT validation and read-model queries for Briefly.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse, tags=["ops"])
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="public-api")


# Include routers
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(feed_router)
app.include_router(admin_router)
app.include_router(sources_router)


if __name__ == "__main__":
    uvicorn.run(
        "src.app:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.env == "development",
    )
