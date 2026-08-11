from collections.abc import Generator

from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.config.settings import settings


class Base(DeclarativeBase):
    metadata = MetaData(schema="account")


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)
SessionLocal = sessionmaker(
    bind=engine, autocommit=False, autoflush=False, class_=Session
)


def init_db() -> None:
    from src.models import account  # noqa: F401

    if engine.dialect.name == "postgresql":
        with engine.begin() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS account;"))
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
