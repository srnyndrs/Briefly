import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from src.config.database import Base
from src.models.post_enrichment import PostEnrichment
from src.repositories.enrichment_repository import EnrichmentRepository
from src.services.classification import ArticleInput
from src.services.enrichment_service import EnrichmentService


def test_fresh_postgres_table_enforces_category_status() -> None:
    database_url = os.environ.get("ENRICHMENT_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set ENRICHMENT_TEST_DATABASE_URL to run PostgreSQL check")

    engine = create_engine(database_url, pool_pre_ping=True)
    schema = f"enrichment_test_{uuid4().hex}"
    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                connection.execute(text(f'CREATE SCHEMA "{schema}"'))
                mapped = connection.execution_options(
                    schema_translate_map={"enrichment": schema}
                )
                Base.metadata.create_all(bind=mapped)
                with pytest.raises(IntegrityError):
                    with connection.begin_nested():
                        connection.execute(
                            PostEnrichment.__table__.insert().values(
                                post_id=uuid4(),
                                event_id=str(uuid4()),
                                category_ids=[],
                                status="completed",
                                processed_at=text("now()"),
                            )
                        )
            finally:
                transaction.rollback()
    finally:
        engine.dispose()


def test_postgres_result_survives_engine_recreation() -> None:
    database_url = os.environ.get("ENRICHMENT_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set ENRICHMENT_TEST_DATABASE_URL to run PostgreSQL check")

    post_id = uuid4()
    article = ArticleInput(title="Persistence check")
    first_engine = create_engine(database_url, pool_pre_ping=True)
    try:
        with first_engine.begin() as connection:
            connection.execute(text("CREATE SCHEMA IF NOT EXISTS enrichment"))
        Base.metadata.create_all(bind=first_engine)
        first_factory = sessionmaker(
            bind=first_engine, class_=Session, autocommit=False, autoflush=False
        )
        first_service = EnrichmentService(
            EnrichmentRepository(first_factory), lambda _: ("science",)
        )
        saved = first_service.enrich_article(post_id, article)
        assert saved.post_revision == 1
    finally:
        first_engine.dispose()

    second_engine = create_engine(database_url, pool_pre_ping=True)
    try:
        second_factory = sessionmaker(
            bind=second_engine,
            class_=Session,
            autocommit=False,
            autoflush=False,
        )
        classifier_calls = 0

        def unexpected_classifier(_: ArticleInput) -> tuple[str, ...]:
            nonlocal classifier_calls
            classifier_calls += 1
            return ("other",)

        loaded = EnrichmentService(
            EnrichmentRepository(second_factory), unexpected_classifier
        ).enrich_article(post_id, article)

        assert loaded == saved
        assert classifier_calls == 0
        newer = EnrichmentService(
            EnrichmentRepository(second_factory), unexpected_classifier
        ).enrich_article(post_id, article, post_revision=2)
        stale = EnrichmentService(
            EnrichmentRepository(second_factory), unexpected_classifier
        ).enrich_article(
            post_id,
            ArticleInput(title="Stale changed input"),
            post_revision=1,
        )

        assert newer.post_revision == 2
        assert stale == newer
        assert classifier_calls == 1
        with second_factory.begin() as session:
            record = session.get(PostEnrichment, post_id)
            if record is not None:
                assert record.post_revision == 2
                session.delete(record)
    finally:
        second_engine.dispose()


def test_postgres_conditional_save_and_publication_guards() -> None:
    from dataclasses import replace
    from datetime import UTC, datetime

    from src.repositories.enrichment_repository import StoredEnrichment

    database_url = os.environ.get("ENRICHMENT_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set ENRICHMENT_TEST_DATABASE_URL to run PostgreSQL check")
    engine = create_engine(database_url, pool_pre_ping=True)
    schema = f"enrichment_test_{uuid4().hex}"
    try:
        with engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        mapped = engine.execution_options(
            schema_translate_map={"enrichment": schema}
        )
        Base.metadata.create_all(bind=mapped)
        repository = EnrichmentRepository(sessionmaker(bind=mapped))
        first = StoredEnrichment(
            post_id=uuid4(),
            post_revision=2,
            category_ids=(),
            status="failed",
            reason="classifier_error",
            processed_at=datetime.now(UTC),
        )
        assert repository.save(first) == first
        replacement = replace(
            first,
            status="completed",
            category_ids=("science",),
            event_id=str(uuid4()),
            reason=None,
        )
        assert repository.save(replacement) is None
        assert (
            repository.save(replacement, expected_enrichment_revision=1) is None
        )
        repository.mark_published(first.post_id, first.event_id)
        second = repository.save(replacement)
        assert second.enrichment_revision == 2
        repository.mark_published(second.post_id, second.event_id)
        assert repository.save(replace(replacement, post_revision=1)) is None
        assert (
            repository.save(replacement, expected_enrichment_revision=1) is None
        )
        third = repository.save(
            replace(replacement, event_id=str(uuid4())),
            expected_enrichment_revision=2,
        )
        assert third.enrichment_revision == 3
        with pytest.raises(RuntimeError, match="changed"):
            repository.mark_published(second.post_id, second.event_id)
        assert repository.get_by_post_id(first.post_id) == third
        with mapped.connect() as connection:
            columns = (
                connection.execute(
                    text(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_schema = :schema AND table_name = 'post_enrichments'"
                    ),
                    {"schema": schema},
                )
                .scalars()
                .all()
            )
        assert set(columns) == {
            "post_id",
            "post_revision",
            "enrichment_revision",
            "category_ids",
            "status",
            "reason",
            "processed_at",
            "event_id",
            "publication_pending",
        }
    finally:
        with engine.begin() as connection:
            connection.execute(
                text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
            )
        engine.dispose()
