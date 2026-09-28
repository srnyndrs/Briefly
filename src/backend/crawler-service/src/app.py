import logging
from contextlib import asynccontextmanager

import sentry_sdk
import uvicorn
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from sentry_sdk.integrations.logging import LoggingIntegration

from src.config.database import SessionLocal, init_db
from src.config.settings import settings
from src.routers import sources
from src.schemas.common import HealthResponse
from src.services.crawl_orchestrator import CrawlCycleOrchestrator

TAG_NAME = "crawler-service"

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
    if (
        "message" in event
        and event["message"] != "Source suspended after retry limit"
    ):
        event["message"] = "Crawler error"
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
        orchestrator = CrawlCycleOrchestrator(
            session_factory=SessionLocal
        )
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            func=orchestrator.run_crawl_cycle,
            trigger="interval",
            seconds=settings.crawl_interval_seconds,
            id="crawl_cycle",
            replace_existing=True,
        )
        scheduler.start()
        application.state.scheduler = scheduler
        logger.info(
            "Crawler Service started crawl interval=%ds, port=%d",
            settings.crawl_interval_seconds,
            settings.app_port,
        )

    yield

    scheduler: BackgroundScheduler | None = getattr(
        application.state, "scheduler", None
    )
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("Scheduler stopped.")

    logger.info("Crawler Service stopped.")


app = FastAPI(
    title="Crawler Service",
    description=(
        "Periodically crawls RSS/Atom sources and publishes events to RabbitMQ. "
        "Part of the Briefly news aggregator platform."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse, tags=["ops"])
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service="crawler-service")


app.include_router(sources.router)


if __name__ == "__main__":
    uvicorn.run(
        "src.app:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.env == "development",
    )
