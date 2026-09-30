import logging
from contextlib import asynccontextmanager

import sentry_sdk
import uvicorn
from fastapi import FastAPI
from sentry_sdk.integrations.logging import LoggingIntegration

from src.config.database import init_db
from src.config.settings import settings
from src.routers import auth, users
from src.schemas.common import HealthResponse

TAG_NAME = "account-service"

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(TAG_NAME)


def scrub_sentry_event(event: dict, _hint: dict) -> dict:
    for key in (
        "request",
        "breadcrumbs",
        "extra",
        "contexts",
        "user",
        "logentry",
    ):
        event.pop(key, None)
    if "message" in event:
        event["message"] = "Account error"
    for item in event.get("exception", {}).get("values", []):
        item["value"] = "[redacted]"
        for frame in item.get("stacktrace", {}).get("frames", []):
            for key in (
                "vars",
                "context_line",
                "pre_context",
                "post_context",
            ):
                frame.pop(key, None)
    return event


if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.env,
        send_default_pii=False,
        include_local_variables=False,
        before_send=scrub_sentry_event,
        integrations=[LoggingIntegration(level=None, event_level=None)],
        traces_sample_rate=0.0,
        enable_logs=False,
    )
    sentry_sdk.set_tag("service", TAG_NAME)


@asynccontextmanager
async def lifespan(application: FastAPI):
    if not getattr(application.state, "testing", False):
        init_db()
        logger.info(
            "Account Service started on port=%d", settings.app_port
        )

    yield

    logger.info("Account Service stopped.")


app = FastAPI(
    title="Account Service",
    description="Identity, account settings, preferences, and subscriptions service for Briefly.",
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
