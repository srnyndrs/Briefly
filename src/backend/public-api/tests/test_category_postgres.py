"""Opt-in PostgreSQL verification of current collection queries."""

import os
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from src.config.database import Base
from src.models.read_models import PostProjection
from src.repositories.feed_repository import PostRepository
from src.services.feed_models import EffectiveFeedQuery


def test_postgres_category_arrays_filters_facets_and_pagination():
    url = os.environ.get("PUBLIC_API_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set PUBLIC_API_TEST_DATABASE_URL for PostgreSQL checks")
    schema = f"query_test_{uuid4().hex}"
    engine = create_engine(url)
    try:
        with engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
            Base.metadata.create_all(
                connection.execution_options(
                    schema_translate_map={"query": schema}
                )
            )
        with Session(
            engine.execution_options(schema_translate_map={"query": schema})
        ) as db:
            now = datetime.now(UTC)
            for post_id, categories, source, language in [
                ("one", ["science", "health"], "allowed", "en"),
                ("two", ["science"], "allowed", "en"),
                ("empty", [], "allowed", "en"),
                ("blocked", ["health"], "blocked", "en"),
                ("foreign", ["health"], "allowed", "hu"),
            ]:
                db.add(
                    PostProjection(
                        post_id=post_id,
                        source_id=source,
                        source_title=source,
                        title="Research",
                        categories=categories,
                        language=language,
                        published_at=now,
                        updated_at=now,
                        keywords=[],
                    )
                )
            db.commit()
            repo = PostRepository(db)
            base = dict(allowed_source_ids=["allowed"], languages=["en"])
            first, total = repo.list_candidates(
                EffectiveFeedQuery(
                    **base, categories=["science", "health"], limit=1
                )
            )
            second, total2 = repo.list_candidates(
                EffectiveFeedQuery(
                    **base, categories=["science", "health"], limit=1, offset=1
                )
            )
            assert (
                total == total2 == 2 and first[0].post_id != second[0].post_id
            )
            assert repo._category_counts(EffectiveFeedQuery(**base)) == [
                ("science", 2),
                ("health", 1),
            ]
            visible, total = repo.list_candidates(
                EffectiveFeedQuery(**base, muted_categories=["health"])
            )
            assert total == 2 and {p.post_id for p in visible} == {
                "two",
                "empty",
            }
            assert repo.list_filter_options(
                EffectiveFeedQuery(**base, categories=["health"])
            ).categories == ["health", "science"]
            assert repo.list_personal_filter_options(
                EffectiveFeedQuery(**base)
            ).categories == ["science", "health"]
            searched, total = repo.list_candidates(
                EffectiveFeedQuery(
                    **base, query="Research", categories=["health"]
                )
            )
            assert total == 1 and searched[0].categories == [
                "science",
                "health",
            ]
    finally:
        with engine.begin() as connection:
            connection.execute(
                text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
            )
        engine.dispose()
