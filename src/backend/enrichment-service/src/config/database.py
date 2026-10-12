import logging

from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from src.config.settings import settings

logger = logging.getLogger(__name__)

engine = create_engine(settings.database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    metadata = MetaData(schema="enrichment")


def init_db() -> None:
    from src.models import post_enrichment  # noqa: F401

    if engine.dialect.name == "postgresql":
        with engine.begin() as connection:
            connection.execute(text("CREATE SCHEMA IF NOT EXISTS enrichment"))

    logger.info("Creating missing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema ready.")
