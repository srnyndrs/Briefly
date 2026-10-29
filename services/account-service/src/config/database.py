import json
import logging
from collections.abc import Generator

from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.config.settings import settings

logger = logging.getLogger(__name__)
SCHEMA_NAME = "account"


class Base(DeclarativeBase):
    metadata = MetaData(schema=SCHEMA_NAME)


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    json_serializer=lambda obj: json.dumps(obj, ensure_ascii=False),
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    class_=Session,
)


def init_db() -> None:
    from src.models import account  # noqa: F401

    logger.info("Creating missing database tables...")
    with engine.begin() as conn:
        if conn.dialect.name == "postgresql":
            conn.execute(text("SET LOCAL lock_timeout = '30s'"))
            conn.execute(
                text("SELECT pg_advisory_xact_lock(hashtext(:lock_name))"),
                {"lock_name": f"briefly:init_db:{SCHEMA_NAME}"},
            )
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA_NAME};"))
        Base.metadata.create_all(bind=conn)
    logger.info("Database schema ready.")


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as db:
        yield db
