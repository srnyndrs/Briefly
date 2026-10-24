from datetime import UTC, datetime
from uuid import UUID

import pytest

from src.models.read_models import PostProjection, UserPreferencesProjection
from src.services.projection_handlers import (
    project_post,
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
    post = db.get(
        PostProjection, UUID("00000000-0000-0000-0000-000000000001")
    )
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
        db.get(
            PostProjection, UUID("00000000-0000-0000-0000-000000000001")
        )
        is None
    )


def test_preference_snapshots_replace_collections(db):
    project_user_preferences(
        db,
        {
            "user_id": "00000000-0000-0000-0000-000000000003",
            "muted_keywords": ["crypto", "drama"],
            "muted_categories": ["sports"],
            "blocked_source_ids": [
                "00000000-0000-0000-0000-000000000004"
            ],
            "languages": ["en", "hu"],
        },
    )
    db.commit()
    db.expire_all()
    user_id = UUID("00000000-0000-0000-0000-000000000003")
    prefs = db.get(UserPreferencesProjection, user_id)
    assert prefs.muted_keywords == ["crypto", "drama"]
    assert prefs.muted_categories == ["sports"]
    assert prefs.blocked_source_ids == [
        "00000000-0000-0000-0000-000000000004"
    ]
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
