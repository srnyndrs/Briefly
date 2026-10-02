import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from src.config.database import Base
from src.models.post_enrichment import PostEnrichment
from src.repositories.enrichment_repository import EnrichmentRepository
from src.services.classification import ArticleInput
from src.services.enrichment import EnrichmentService


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
        with first_engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE enrichment.post_enrichments "
                    "ADD COLUMN IF NOT EXISTS post_revision "
                    "INTEGER NOT NULL DEFAULT 1"
                )
            )
        first_factory = sessionmaker(
            bind=first_engine, class_=Session, autocommit=False, autoflush=False
        )
        first_service = EnrichmentService(
            EnrichmentRepository(first_factory), lambda _: "science"
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

        def unexpected_classifier(_: ArticleInput) -> str | None:
            nonlocal classifier_calls
            classifier_calls += 1
            return "other"

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
        assert classifier_calls == 0
        with second_factory.begin() as session:
            record = session.get(PostEnrichment, post_id)
            if record is not None:
                assert record.post_revision == 2
                session.delete(record)
    finally:
        second_engine.dispose()
