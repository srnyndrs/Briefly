import logging

from sqlalchemy import MetaData, create_engine, make_url, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from src.config.settings import settings

logger = logging.getLogger(__name__)

database_url = make_url(settings.database_url)
if database_url.drivername == "postgresql":
    database_url = database_url.set(drivername="postgresql+psycopg2")

engine = create_engine(database_url, pool_pre_ping=True)

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
