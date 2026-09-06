import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from src.config.database import init_db
from src.config.settings import settings
from src.routers import auth, users
from src.schemas.common import HealthResponse

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("account-service")


@asynccontextmanager
async def lifespan(application: FastAPI):
    if not getattr(application.state, "testing", False):
        init_db()
        logger.info(
            "Account Service started on port=%d", settings.app_port
        )

    yield

    if not getattr(application.state, "testing", False):
        logger.info("Account Service stopped")


app = FastAPI(
    title="Account Service",
    description="Identity, profile, preferences, and subscriptions service for Briefly.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse, tags=["ops"])
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="account-service")


app.include_router(auth.router)
app.include_router(users.router)


if __name__ == "__main__":
    uvicorn.run(
        "src.app:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.env == "development",
    )
