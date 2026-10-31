import json
import logging
from collections.abc import Generator
from time import monotonic, sleep

from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import NullPool

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
    connect_args=(
        {"connect_timeout": 5}
        if settings.database_url.startswith("postgresql")
        else {}
    ),
    json_serializer=lambda obj: json.dumps(obj, ensure_ascii=False),
)

readiness_engine = create_engine(
    settings.database_url,
    poolclass=NullPool,
    connect_args=(
        {"connect_timeout": 2, "options": "-c statement_timeout=2000"}
        if engine.dialect.name == "postgresql"
        else {}
    ),
)


def database_ready() -> bool:
    try:
        with readiness_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    class_=Session,
)


def _connect_for_startup() -> Connection:
    deadline = monotonic() + 60
    while True:
        try:
            return engine.connect()
        except OperationalError:
            remaining = deadline - monotonic()
            if remaining <= 0:
                raise
            logger.info("Database unavailable; retrying startup connection...")
            sleep(min(2, remaining))


def init_db() -> None:
    from src.models import account  # noqa: F401

    logger.info("Creating missing database tables...")
    with _connect_for_startup() as conn, conn.begin():
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
