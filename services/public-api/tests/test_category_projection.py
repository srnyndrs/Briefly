from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.config.database import Base
from src.models.read_models import PostEnrichmentProjection, PostProjection
from src.repositories.feed_repository import PostRepository
from src.services.feed_models import EffectiveFeedQuery
from src.services.projection_handlers import project_enrichment, project_post


def _db():
    engine = create_engine(
        "sqlite:///:memory:",
        execution_options={"schema_translate_map": {"query": None}},
    )
    Base.metadata.create_all(bind=engine)
    return Session(engine)


def _post(post_id, revision, title="Article"):
    return {
        "post_id": post_id,
        "post_revision": revision,
        "source_id": "source",
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
    post_id, revision, categories, enrichment_revision=1, status="completed"
):
    return {
        "post_id": post_id,
        "post_revision": revision,
        "enrichment_revision": enrichment_revision,
        "taxonomy_version": "categories-v2",
        "status": status,
        "category_ids": categories,
        "input_hash": "a" * 64,
        "enrichment_version": "test-policy",
        "processed_at": datetime.now(UTC).isoformat(),
    }


def test_result_before_post_waits_for_matching_snapshot():
    db = _db()
    project_enrichment(db, _result("p1", 2, ["technology", "business"]))
    db.commit()
    assert db.get(PostProjection, "p1") is None
    project_post(db, _post("p1", 1))
    db.commit()
    post = db.get(PostProjection, "p1")
    assert post.categories == [] and post.source_category == "Publisher label"
    project_post(db, _post("p1", 2))
    db.commit()
    assert post.categories == ["technology", "business"]


def test_revisions_duplicates_failure_and_article_update():
    db = _db()
    project_post(db, _post("p1", 2, "Current"))
    db.commit()
    post = db.get(PostProjection, "p1")
    original_time = post.updated_at
    project_enrichment(db, _result("p1", 2, ["science", "health"], 3))
    db.commit()
    project_enrichment(db, _result("p1", 2, ["business"], 2))
    project_enrichment(db, _result("p1", 2, ["sports"], 3))
    project_enrichment(db, _result("p1", 1, ["business"], 99))
    project_post(db, _post("p1", 1, "Old"))
    db.commit()
    assert post.categories == ["science", "health"] and post.title == "Current"
    project_enrichment(db, _result("p1", 2, [], 4, status="failed"))
    db.commit()
    assert post.categories == [] and post.updated_at == original_time
    project_enrichment(db, _result("p1", 2, ["science"], 5))
    db.commit()
    assert post.categories == ["science"]
    project_post(db, _post("p1", 3, "New"))
    db.commit()
    assert post.categories == []
    project_enrichment(db, _result("p1", 2, ["health"], 6))
    db.commit()
    assert post.categories == []
    assert db.get(PostEnrichmentProjection, "p1").enrichment_revision == 5


@pytest.mark.parametrize(
    "changes",
    [
        {"category_ids": ["imaginary"]},
        {"category_ids": ["science", "science"]},
        {"category_ids": ["other", "health"]},
        {"category_ids": []},
        {"category_ids": ["science", "health", "business"]},
        {"post_revision": True},
        {"enrichment_revision": 0},
        {"status": "failed"},
        {"taxonomy_version": "unknown"},
        {"category_id": "science"},
        {"category_ids": None},
        {"input_hash": "bad"},
    ],
)
def test_invalid_current_payload_is_rejected(changes):
    db = _db()
    with pytest.raises(ValueError):
        project_enrichment(db, {**_result("p1", 1, ["science"]), **changes})
    assert db.get(PostEnrichmentProjection, "p1") is None


def test_collection_filters_muting_facets_detail_and_pagination():
    db = _db()
    ids = [str(uuid4()) for _ in range(4)]
    for post_id in ids:
        project_post(db, _post(post_id, 1))
    db.commit()
    project_enrichment(db, _result(ids[0], 1, ["science", "health"]))
    project_enrichment(db, _result(ids[1], 1, ["science"]))
    project_enrichment(db, _result(ids[2], 1, [], status="abstained"))
    db.commit()
    repo = PostRepository(db)
    query = EffectiveFeedQuery(categories=["science", "health"], limit=1)
    first, total = repo.list_candidates(query)
    second, second_total = repo.list_candidates(
        EffectiveFeedQuery(categories=query.categories, limit=1, offset=1)
    )
    assert total == second_total == 2
    assert first[0].post_id != second[0].post_id
    assert repo.get_post(UUID(ids[0])).categories == ["science", "health"]
    assert repo.get_post(UUID(ids[3])).categories == []
    assert repo._category_counts(EffectiveFeedQuery()) == [
        ("science", 2),
        ("health", 1),
    ]
    assert repo.list_filter_options(EffectiveFeedQuery()).categories == [
        "health",
        "science",
    ]
    assert repo.list_personal_filter_options(
        EffectiveFeedQuery()
    ).categories == ["science", "health"]
    visible, total = repo.list_candidates(
        EffectiveFeedQuery(muted_categories=["health"], limit=20)
    )
    assert total == 3 and ids[0] not in {p.post_id for p in visible}
    assert repo.list_filter_options(
        EffectiveFeedQuery(muted_categories=["health"])
    ).categories == ["science"]
