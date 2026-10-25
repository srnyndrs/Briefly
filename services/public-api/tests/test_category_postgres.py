"""Opt-in PostgreSQL verification of current collection queries."""

from datetime import UTC, datetime
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import text

from src.models.read_models import PostProjection
from src.repositories.feed_repository import PostRepository
from src.services.feed_models import EffectiveFeedQuery


def test_postgres_search_index_and_ranking(postgres_db):
    db = postgres_db
    assert (
        db.scalar(
            text("""SELECT indexdef FROM pg_indexes
        WHERE schemaname = 'query' AND indexname = 'ix_post_projections_search_vector'
    """)
        )
        is not None
    )
    now = datetime.now(UTC)
    for post_id, title, description, keywords, content in [
        ("title", "space telescope", "", [], ""),
        ("description", "Article", "telescope observations", [], ""),
        ("keywords", "Article", "", ["telescope"], ""),
        ("body", "Article", "", [], "telescope"),
    ]:
        db.add(
            PostProjection(
                post_id=uuid5(NAMESPACE_URL, post_id),
                title=title,
                description=description,
                keywords=keywords,
                content=content,
                categories=["science"],
                source_id=uuid5(NAMESPACE_URL, "source"),
                source_title="Source",
                published_at=now,
                updated_at=now,
            )
        )
    db.commit()
    repo = PostRepository(db)
    items, total = repo.list_candidates(
        EffectiveFeedQuery(query="telescope", categories=["science", "health"])
    )
    assert total == 3
    assert [item.post_id for item in items] == [
        uuid5(NAMESPACE_URL, value)
        for value in ("title", "description", "keywords")
    ]
    items, total = repo.list_candidates(
        EffectiveFeedQuery(query="telescope", categories=["health"])
    )
    assert total == 0 and items == []
    phrase, phrase_total = repo.list_candidates(
        EffectiveFeedQuery(query='"space telescope"')
    )
    assert phrase_total == 1 and phrase[0].post_id == uuid5(NAMESPACE_URL, "title")
    negative, negative_total = repo.list_candidates(
        EffectiveFeedQuery(query="telescope -observations")
    )
    assert negative_total == 2
    assert {post.post_id for post in negative} == {
        uuid5(NAMESPACE_URL, "title"),
        uuid5(NAMESPACE_URL, "keywords"),
    }
    keyword_post = db.get(PostProjection, uuid5(NAMESPACE_URL, "keywords"))
    keyword_post.keywords = ["space telescope"]
    db.commit()
    _, phrase_total = repo.list_candidates(
        EffectiveFeedQuery(query='"space telescope"')
    )
    assert phrase_total == 2
    keyword_post.keywords = ["space", "telescope"]
    db.commit()
    phrase, phrase_total = repo.list_candidates(
        EffectiveFeedQuery(query='"space telescope"')
    )
    assert phrase_total == 1 and phrase[0].post_id == uuid5(NAMESPACE_URL, "title")


def test_postgres_category_filters_facets_and_pagination(postgres_db):
    db = postgres_db
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
                post_id=uuid5(NAMESPACE_URL, post_id),
                source_id=uuid5(NAMESPACE_URL, source),
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
    base = dict(
        allowed_source_ids=[uuid5(NAMESPACE_URL, "allowed")],
        languages=["en"],
    )
    first, total = repo.list_candidates(
        EffectiveFeedQuery(**base, categories=["science", "health"], limit=1)
    )
    second, total2 = repo.list_candidates(
        EffectiveFeedQuery(
            **base, categories=["science", "health"], limit=1, offset=1
        )
    )
    assert total == total2 == 2 and first[0].post_id != second[0].post_id
    visible, total = repo.list_candidates(
        EffectiveFeedQuery(**base, muted_categories=["health"])
    )
    assert total == 2 and {p.post_id for p in visible} == {
        uuid5(NAMESPACE_URL, "two"),
        uuid5(NAMESPACE_URL, "empty"),
    }
    assert repo.list_filter_options(
        EffectiveFeedQuery(**base, categories=["health"])
    ).categories == ["health", "science"]
    assert repo.list_personal_filter_options(
        EffectiveFeedQuery(**base)
    ).categories == ["science", "health"]
    searched, total = repo.list_candidates(
        EffectiveFeedQuery(**base, query="Research", categories=["health"])
    )
    assert total == 1 and searched[0].categories == [
        "science",
        "health",
    ]
