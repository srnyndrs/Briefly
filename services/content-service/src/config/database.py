import json
import logging
from collections.abc import Generator

from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.config.settings import settings

logger = logging.getLogger(__name__)
SCHEMA_NAME = "content"


class Base(DeclarativeBase):
    metadata = MetaData(schema=SCHEMA_NAME)


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    json_serializer=lambda obj: json.dumps(obj, ensure_ascii=False),
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, class_=Session)


def init_db() -> None:
    from src.models import post  # noqa: F401

    if engine.dialect.name == "postgresql":
        with engine.begin() as conn:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA_NAME};"))

    logger.info("Creating missing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema ready.")


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as db:
        yield db
