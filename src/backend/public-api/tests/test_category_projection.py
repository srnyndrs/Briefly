from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.config.database import Base
from src.models.read_models import (
    PostEnrichmentProjection,
    PostProjection,
)
from src.repositories.feed_repository import PostRepository
from src.services.feed_models import EffectiveFeedQuery
from src.services.projection_handlers import (
    project_enrichment,
    project_post,
)


def _db() -> Session:
    engine = create_engine(
        "sqlite:///:memory:",
        execution_options={"schema_translate_map": {"query": None}},
    )
    Base.metadata.create_all(bind=engine)
    return Session(engine)


def _post(post_id: str, revision: int, *, title: str = "Article") -> dict:
    return {
        "post_id": post_id,
        "post_revision": revision,
        "source_id": "verified-source",
        "source_title": "Publisher",
        "url": f"https://example.com/{post_id}",
        "title": title,
        "description": None,
        "category": "Publisher label",
        "content": "Body",
        "author": None,
        "language": "en",
        "keywords": [],
        "image_url": None,
        "published_at": datetime(2026, 1, 1, tzinfo=UTC).isoformat(),
    }


def _result(
    post_id: str,
    revision: int,
    category: str | None,
    *,
    status: str = "completed",
    taxonomy: str = "categories-v2",
) -> dict:
    return {
        "post_id": post_id,
        "post_revision": revision,
        "taxonomy_version": taxonomy,
        "status": status,
        "category_id": category,
    }


def test_result_before_post_waits_for_matching_snapshot() -> None:
    db = _db()
    project_enrichment(db, _result("p1", 2, "technology"))
    db.commit()
    assert db.get(PostProjection, "p1") is None

    project_post(db, _post("p1", 1))
    db.commit()
    post = db.get(PostProjection, "p1")
    assert post is not None and post.category is None
    assert post.source_category == "Publisher label"

    project_post(db, _post("p1", 2))
    db.commit()
    assert post.category == "technology"
    assert post.post_revision == 2


def test_post_before_result_and_stale_events_keep_current_category() -> None:
    db = _db()
    project_post(db, _post("p1", 2, title="Current"))
    db.commit()
    post = db.get(PostProjection, "p1")
    assert post is not None
    article_updated_at = post.updated_at
    project_enrichment(db, _result("p1", 2, "science"))
    db.commit()

    project_post(db, _post("p1", 1, title="Stale"))
    project_enrichment(db, _result("p1", 1, "business"))
    db.commit()
    assert post.title == "Current"
    assert post.category == "science"
    assert post.updated_at == article_updated_at
    assert db.get(PostEnrichmentProjection, "p1").post_revision == 2

    project_post(db, _post("p1", 3, title="New snapshot"))
    db.commit()
    assert post.category is None
    project_enrichment(db, _result("p1", 3, "science"))
    db.commit()
    assert post.category == "science"


@pytest.mark.parametrize(
    "category",
    [
        "other",
        "world",
        "economy",
        "finance",
        "entertainment",
        "lifestyle",
        "automotive",
    ],
)
def test_public_category_controls_list_detail_facets_and_muting(
    category: str,
) -> None:
    db = _db()
    other_id = str(uuid4())
    for post_id in (
        other_id,
        "abstained",
        "unsupported",
        "unknown-category",
        "unenriched",
    ):
        project_post(db, _post(post_id, 1))
    db.commit()
    project_enrichment(db, _result(other_id, 1, category))
    project_enrichment(db, _result("abstained", 1, None, status="abstained"))
    project_enrichment(
        db,
        _result("unsupported", 1, "sports", taxonomy="future-taxonomy"),
    )
    project_enrichment(db, _result("unknown-category", 1, "imaginary"))
    db.commit()

    repository = PostRepository(db)
    items, total = repository.list_candidates(
        EffectiveFeedQuery(categories=[category], limit=20)
    )
    assert total == 1
    assert [item.post_id for item in items] == [other_id]
    detail = repository.get_post(UUID(other_id))
    assert detail is not None
    assert detail.category == category
    assert repository.list_filter_options(
        EffectiveFeedQuery(limit=20)
    ).categories == [category]

    visible, total = repository.list_candidates(
        EffectiveFeedQuery(muted_categories=[category], limit=20)
    )
    assert total == 4
    assert {item.post_id for item in visible} == {
        "abstained",
        "unsupported",
        "unknown-category",
        "unenriched",
    }
    assert all(item.category is None for item in visible)
    assert db.get(PostProjection, "unenriched").source_category == (
        "Publisher label"
    )
