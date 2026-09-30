import logging
from collections.abc import Generator

from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.config.settings import settings

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=False,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    metadata = MetaData(schema="crawler")


def init_db() -> None:
    from src.models import source  # noqa: F401

    if engine.dialect.name == "postgresql":
        with engine.begin() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS crawler;"))

    logger.info("Creating missing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema ready.")


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as db:
        yield db
