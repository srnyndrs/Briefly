import logging
from contextlib import asynccontextmanager

import uvicorn
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI

from src.config.database import SessionLocal, init_db
from src.config.settings import settings
from src.routers import sources
from src.schemas.schemas import HealthResponse
from src.services.crawl_orchestrator import CrawlCycleOrchestrator

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("crawler-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = None
    if not getattr(app.state, "testing", False):
        # 1. Initialise database schema
        init_db()

        # 2. Schedule periodic crawl cycle
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
        app.state.scheduler = scheduler

        logger.info(
            "Crawler Service started crawl interval=%ds, port=%d",
            settings.crawl_interval_seconds,
            settings.app_port,
        )

    yield

    scheduler: BackgroundScheduler | None = getattr(
        app.state, "scheduler", None
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

app.include_router(sources.router)


@app.get("/health", response_model=HealthResponse, tags=["ops"])
def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="crawler-service",
    )


if __name__ == "__main__":
    uvicorn.run(
        "src.app:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.env == "development",
    )
