from collections.abc import Generator

from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.config.settings import settings


class Base(DeclarativeBase):
    metadata = MetaData(schema="query")


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def init_db() -> None:
    from src.models import read_models  # noqa: F401

    if engine.dialect.name == "postgresql":
        with engine.begin() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS query;"))
            conn.execute(
                text(
                    """
                    CREATE OR REPLACE FUNCTION
                    query.keywords_to_search_text(keywords jsonb)
                    RETURNS text
                    LANGUAGE sql
                    IMMUTABLE
                    STRICT
                    PARALLEL SAFE
                    RETURN (
                        SELECT coalesce(string_agg(value, ' ' ORDER BY position), '')
                        FROM jsonb_array_elements_text(keywords)
                            WITH ORDINALITY AS elements(value, position)
                    );
                    """
                )
            )
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as db:
        yield db
