from datetime import UTC, datetime
from uuid import UUID

import pytest

from src.models.read_models import (
    PostDeletionProjection,
    PostEnrichmentProjection,
    PostProjection,
    UserPreferencesProjection,
)
from src.repositories.feed_repository import PostRepository
from src.services.feed_models import EffectiveFeedQuery
from src.services.projection_handlers import (
    project_enrichment,
    project_post,
    project_post_deleted,
    project_user_preferences,
)


def test_post_snapshot_replaces_and_clears_metadata(db):
    payload = {
        "post_id": "00000000-0000-0000-0000-000000000001",
        "post_revision": 1,
        "source_id": "00000000-0000-0000-0000-000000000002",
        "source_title": "Source One",
        "url": "https://example.com/a1",
        "title": "Original Title",
        "description": "Short description",
        "category": "technology",
        "content": "Full body",
        "author": "Original Author",
        "language": "en",
        "keywords": ["tech"],
        "image_url": "https://example.com/image.png",
        "published_at": datetime(2026, 1, 1, tzinfo=UTC).isoformat(),
    }
    project_post(db, payload)
    db.commit()
    db.expire_all()
    post = db.get(PostProjection, UUID("00000000-0000-0000-0000-000000000001"))
    assert post.content == "Full body"
    assert post.description == "Short description"
    assert post.image_ref == payload["image_url"]
    assert post.author == "Original Author"
    assert post.keywords == ["tech"]
    assert post.published_at is not None

    project_post(
        db,
        {
            **payload,
            "post_revision": 2,
            "url": "https://example.com/updated",
            "title": "Updated Title",
            "description": None,
            "category": "news",
            "content": None,
            "author": "Updated Author",
            "language": "fr",
            "keywords": ["finance"],
            "image_url": None,
            "published_at": None,
            "parsed_at": datetime(2026, 1, 2, tzinfo=UTC).isoformat(),
        },
    )
    db.commit()
    db.expire_all()
    assert post.canonical_url == "https://example.com/updated"
    assert post.title == "Updated Title"
    assert post.description is None
    assert post.source_category == "news"
    assert post.categories == []
    assert post.post_revision == 2
    assert post.content is None
    assert post.author == "Updated Author"
    assert post.language == "fr"
    assert post.keywords == ["finance"]
    assert post.image_ref is None
    assert post.published_at is None


def test_post_rejects_missing_source_identity(db):
    with pytest.raises(ValueError, match="source_id"):
        project_post(
            db,
            {
                "post_id": "00000000-0000-0000-0000-000000000001",
                "source_title": "Source One",
            },
        )
    assert (
        db.get(PostProjection, UUID("00000000-0000-0000-0000-000000000001")) is None
    )


@pytest.mark.parametrize(
    "parsed_first", [True, False], ids=["parsed-first", "deleted-first"]
)
def test_deleted_post_tombstone_blocks_late_content_and_enrichment(
    db, parsed_first
):
    post_id = "00000000-0000-0000-0000-000000000011"
    source_id = "00000000-0000-0000-0000-000000000012"
    payload = {
        "post_id": post_id,
        "post_revision": 1,
        "source_id": source_id,
        "source_title": "Source",
        "url": "https://example.com/post",
        "title": "Original",
        "description": None,
        "category": None,
        "content": "Body",
        "author": None,
        "language": "en",
        "keywords": [],
        "image_url": None,
        "published_at": None,
    }
    if parsed_first:
        project_post(db, payload)
        db.commit()
    project_post_deleted(
        db,
        {
            "post_id": post_id,
            "post_revision": 2,
            "deleted_at": datetime.now(UTC).isoformat(),
        },
    )
    # The projector commits each delivery before processing the next event.
    db.commit()
    project_post(db, {**payload, "post_revision": 3, "title": "Late recrawl"})
    db.commit()
    project_enrichment(
        db,
        {
            "post_id": post_id,
            "post_revision": 3,
            "enrichment_revision": 1,
            "status": "completed",
            "category_ids": ["science"],
        },
    )
    db.commit()

    projection = db.get(PostProjection, UUID(post_id))
    if parsed_first:
        assert projection.is_deleted is True
        assert projection.title == "Original"
        assert projection.post_revision == 2
    else:
        assert projection is None
    assert db.get(PostDeletionProjection, UUID(post_id)).post_revision == 2
    assert db.get(PostEnrichmentProjection, UUID(post_id)) is None
    rows, total = PostRepository(db).list_candidates(EffectiveFeedQuery())
    assert rows == []
    assert total == 0
    assert PostRepository(db).get_post(UUID(post_id)) is None

    marker = db.get(PostDeletionProjection, UUID(post_id))
    deleted_at = marker.deleted_at
    project_post_deleted(
        db,
        {
            "post_id": post_id,
            "post_revision": 2,
            "deleted_at": deleted_at.isoformat(),
        },
    )
    db.commit()
    db.refresh(marker)
    assert marker.post_revision == 2
    assert marker.deleted_at == deleted_at


@pytest.mark.parametrize("deleted_at", [None, "not-a-timestamp"])
def test_deletion_requires_its_recorded_timestamp(db, deleted_at):
    post_id = UUID("00000000-0000-0000-0000-000000000013")
    payload = {"post_id": str(post_id), "post_revision": 2}
    with pytest.raises(KeyError):
        project_post_deleted(db, payload)
    with pytest.raises(ValueError):
        project_post_deleted(db, {**payload, "deleted_at": deleted_at})
    assert db.get(PostDeletionProjection, post_id) is None


def test_preference_snapshots_replace_collections(db):
    project_user_preferences(
        db,
        {
            "user_id": "00000000-0000-0000-0000-000000000003",
            "muted_keywords": ["crypto", "drama"],
            "muted_categories": ["sports"],
            "blocked_source_ids": ["00000000-0000-0000-0000-000000000004"],
            "languages": ["en", "hu"],
        },
    )
    db.commit()
    db.expire_all()
    user_id = UUID("00000000-0000-0000-0000-000000000003")
    prefs = db.get(UserPreferencesProjection, user_id)
    assert prefs.muted_keywords == ["crypto", "drama"]
    assert prefs.muted_categories == ["sports"]
    assert prefs.blocked_source_ids == ["00000000-0000-0000-0000-000000000004"]
    assert prefs.languages == ["en", "hu"]

    project_user_preferences(
        db,
        {
            "user_id": str(user_id),
            "muted_keywords": ["ai"],
            "muted_categories": [],
        },
    )
    db.commit()
    db.expire_all()
    assert prefs.muted_keywords == ["ai"]
    assert prefs.muted_categories == []
    assert prefs.blocked_source_ids == []
    assert prefs.languages == []
