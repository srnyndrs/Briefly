import logging

from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

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
    from src.models import feed  # noqa: F401

    if engine.dialect.name == "postgresql":
        with engine.begin() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS crawler;"))

    logger.info("Running database migrations (create_all)...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema ready.")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
