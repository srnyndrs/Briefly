import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

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


def test_postgres_conditional_save_and_publication_guards() -> None:
    from dataclasses import replace
    from datetime import UTC, datetime

    from src.repositories.stored_enrichment import StoredEnrichment

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
        assert repository.save(replacement, expected_enrichment_revision=1) is None
        repository.mark_published(first.post_id, first.event_id)
        second = repository.save(replacement)
        assert second.enrichment_revision == 2
        repository.mark_published(second.post_id, second.event_id)
        assert repository.save(replace(replacement, post_revision=1)) is None
        assert repository.save(replacement, expected_enrichment_revision=1) is None
        third = repository.save(
            replace(replacement, event_id=str(uuid4())),
            expected_enrichment_revision=2,
        )
        assert third.enrichment_revision == 3
        with pytest.raises(RuntimeError, match="changed"):
            repository.mark_published(second.post_id, second.event_id)
        assert repository.get_by_post_id(first.post_id) == third
        engine.dispose()
        second_engine = create_engine(database_url, pool_pre_ping=True)
        try:
            second_mapped = second_engine.execution_options(
                schema_translate_map={"enrichment": schema}
            )
            second_repository = EnrichmentRepository(
                sessionmaker(bind=second_mapped)
            )

            def unexpected_classifier(_):
                raise AssertionError(
                    "Saved revision must survive engine recreation"
                )

            loaded = EnrichmentService(
                second_repository, unexpected_classifier
            ).enrich_article(
                first.post_id,
                ArticleInput(title="Persistence check"),
                post_revision=2,
            )
            assert loaded == third
        finally:
            second_engine.dispose()
    finally:
        with engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        engine.dispose()
