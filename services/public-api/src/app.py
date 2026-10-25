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

from src.adapters.query_projector import QueryProjector
from src.config.database import SessionLocal, init_db
from src.config.settings import settings
from src.routers.auth import router as auth_router
from src.routers.feed import (
    admin_router as feed_admin_router,
)
from src.routers.feed import (
    router as feed_router,
)
from src.routers.posts import (
    admin_router as posts_admin_router,
)
from src.routers.posts import (
    router as posts_router,
)
from src.routers.sources import router as sources_router
from src.routers.user import router as user_router
from src.schemas.common import HealthResponse

TAG_NAME = "public-api"

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


@asynccontextmanager
async def lifespan(application: FastAPI):
    try:
        if not getattr(application.state, "testing", False):
            init_db()
            application.state.projector = None
            application.state.projector_thread = None
            if settings.query_consumer_enabled:
                projector = QueryProjector(SessionLocal)
                thread = threading.Thread(
                    target=projector.run,
                    daemon=True,
                    name="rabbitmq-projector",
                )
                application.state.projector = projector
                application.state.projector_thread = thread
                thread.start()

            logger.info("Public API started on port=%d", settings.app_port)

        yield
    finally:
        projector: QueryProjector | None = getattr(
            application.state, "projector", None
        )
        if projector:
            projector.stop()

        thread: threading.Thread | None = getattr(
            application.state, "projector_thread", None
        )
        if thread and thread.is_alive():
            thread.join(timeout=5)

        logger.info("Public API stopped.")


app = FastAPI(
    title="Public API",
    description="Gateway API with JWT validation and read-model queries.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse, tags=["ops"])
def health() -> HealthResponse:
    return HealthResponse(status="ok", service=TAG_NAME)


# Include routers
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(feed_router)
app.include_router(posts_router)
app.include_router(feed_admin_router)
app.include_router(posts_admin_router)
app.include_router(sources_router)


if __name__ == "__main__":
    uvicorn.run(
        "src.app:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.env == "development",
    )
