import logging
import threading
from contextlib import asynccontextmanager
from time import monotonic

import sentry_sdk
import uvicorn
from apscheduler.events import EVENT_SCHEDULER_STARTED
from apscheduler.schedulers.base import STATE_RUNNING
from apscheduler.schedulers.blocking import BlockingScheduler
from fastapi import FastAPI, HTTPException
from sentry_sdk.integrations.logging import (
    LoggingIntegration,
    ignore_logger,
    ignore_logger_for_sentry_logs,
)

from src.config.database import SessionLocal, database_ready, init_db
from src.config.message_broker import broker_ready
from src.config.settings import settings
from src.routers import sources
from src.schemas.common import HealthResponse
from src.services.crawl_orchestrator import CrawlCycleOrchestrator

TAG_NAME = "crawler-service"

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
    application.state.started = False
    scheduler = None
    thread = None
    orchestrator = None
    try:
        if not getattr(application.state, "testing", False):
            init_db()
            orchestrator = CrawlCycleOrchestrator(session_factory=SessionLocal)
            scheduler = BlockingScheduler()
            application.state.scheduler = scheduler
            scheduler_started = threading.Event()
            scheduler.add_listener(
                lambda _: scheduler_started.set(), EVENT_SCHEDULER_STARTED
            )
            scheduler.add_job(
                func=orchestrator.run_crawl_cycle,
                trigger="interval",
                seconds=settings.crawl_interval_seconds,
                id="crawl_cycle",
                replace_existing=True,
            )
            thread = threading.Thread(
                target=scheduler.start,
                daemon=True,
                name="crawl-scheduler",
            )
            application.state.scheduler_thread = thread
            thread.start()
            if not scheduler_started.wait(timeout=5):
                raise RuntimeError("Crawler scheduler failed to start")
            logger.info(
                "Crawler Service started crawl interval=%ds, port=%d",
                settings.crawl_interval_seconds,
                settings.app_port,
            )

        application.state.started = True
        yield
    finally:
        application.state.started = False
        deadline = monotonic() + settings.shutdown_timeout_seconds
        if orchestrator:
            orchestrator.stop()
        if scheduler and scheduler.running:
            scheduler.shutdown(wait=False)

        if thread and thread.is_alive():
            thread.join(timeout=max(0, deadline - monotonic()))

        idle = orchestrator is None or orchestrator.wait_for_idle(
            timeout=max(0, deadline - monotonic())
        )
        if (thread and thread.is_alive()) or not idle:
            logger.warning(
                "Background shutdown deadline reached; process termination must stop remaining work."
            )
        else:
            logger.info("Crawler Service stopped.")


app = FastAPI(
    title="Crawler Service",
    description="Periodically crawls RSS/Atom sources and publishes raw results.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse, tags=["ops"])
def health() -> HealthResponse:
    return HealthResponse(status="ok", service=TAG_NAME)


@app.get("/live", response_model=HealthResponse, tags=["ops"])
def live() -> HealthResponse:
    if not getattr(app.state, "started", False):
        raise HTTPException(status_code=503, detail="Service has not started")

    thread = getattr(app.state, "scheduler_thread", None)
    if thread is None or not thread.is_alive():
        raise HTTPException(status_code=503, detail="Scheduler is not running")

    return HealthResponse(status="ok", service=TAG_NAME)


@app.get("/ready", response_model=HealthResponse, tags=["ops"])
def ready() -> HealthResponse:
    live()
    if (
        not getattr(app.state, "scheduler", None)
        or app.state.scheduler.state != STATE_RUNNING
        or not database_ready()
        or not broker_ready()
    ):
        raise HTTPException(status_code=503, detail="Service is not ready")

    return live()


app.include_router(sources.router)


if __name__ == "__main__":
    uvicorn.run(
        "src.app:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.env == "development",
        timeout_graceful_shutdown=10,
    )
