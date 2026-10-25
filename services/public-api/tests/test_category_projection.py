from datetime import UTC, datetime
from uuid import UUID

import pytest

from src.models.read_models import PostEnrichmentProjection, PostProjection
from src.services.projection_handlers import project_enrichment, project_post

POST_ID = "00000000-0000-0000-0000-000000000001"
SOURCE_ID = "00000000-0000-0000-0000-000000000002"


def _post(post_id, revision, title="Article"):
    return {
        "post_id": post_id,
        "post_revision": revision,
        "source_id": SOURCE_ID,
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
        "status": status,
        "category_ids": categories,
    }


def test_result_before_post_waits_for_matching_snapshot(db):
    project_enrichment(db, _result(POST_ID, 2, ["technology", "business"]))
    db.commit()
    assert db.get(PostProjection, UUID(POST_ID)) is None
    project_post(db, _post(POST_ID, 1))
    db.commit()
    post = db.get(PostProjection, UUID(POST_ID))
    assert post.categories == [] and post.source_category == "Publisher label"
    project_post(db, _post(POST_ID, 2))
    db.commit()
    assert post.categories == ["technology", "business"]


def test_revisions_duplicates_failure_and_article_update(db):
    project_post(db, _post(POST_ID, 2, "Current"))
    db.commit()
    post = db.get(PostProjection, UUID(POST_ID))
    original_time = post.updated_at
    project_enrichment(db, _result(POST_ID, 2, ["science", "health"], 3))
    db.commit()
    project_enrichment(db, _result(POST_ID, 2, ["business"], 2))
    project_enrichment(db, _result(POST_ID, 2, ["sports"], 3))
    project_enrichment(db, _result(POST_ID, 1, ["business"], 99))
    project_post(db, _post(POST_ID, 1, "Old"))
    db.commit()
    assert post.categories == ["science", "health"] and post.title == "Current"
    project_enrichment(db, _result(POST_ID, 2, [], 4, status="failed"))
    db.commit()
    assert post.categories == [] and post.updated_at == original_time
    project_enrichment(db, _result(POST_ID, 2, ["science"], 5))
    db.commit()
    assert post.categories == ["science"]
    project_enrichment(db, _result(POST_ID, 2, [], 6, status="abstained"))
    db.commit()
    assert post.categories == [] and post.updated_at == original_time
    project_enrichment(db, _result(POST_ID, 2, ["science"], 7))
    db.commit()
    project_post(db, _post(POST_ID, 3, "New"))
    db.commit()
    assert post.categories == []
    project_enrichment(db, _result(POST_ID, 2, ["health"], 6))
    db.commit()
    assert post.categories == []
    assert db.get(PostEnrichmentProjection, UUID(POST_ID)).enrichment_revision == 7


@pytest.mark.parametrize(
    "changes",
    [
        {"category_ids": ["imaginary"]},
        {"category_ids": ["other", "health"]},
        {"category_ids": []},
        {"post_revision": True},
    ],
)
def test_invalid_current_payload_is_rejected(changes, db):
    with pytest.raises(ValueError):
        project_enrichment(db, {**_result(POST_ID, 1, ["science"]), **changes})
    assert db.get(PostEnrichmentProjection, UUID(POST_ID)) is None
