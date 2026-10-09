from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.config.database import Base
from src.models.read_models import (
    PostProjection,
    UserPreferencesProjection,
)
from src.services.projection_handlers import (
    project_post,
    project_user_preferences,
)


def test_project_post_persists_content() -> None:
    engine = create_engine(
        "sqlite:///:memory:",
        execution_options={"schema_translate_map": {"query": None}},
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    db = SessionLocal()
    try:
        project_post(
            db,
            payload={
                "post_id": "a1",
                "post_revision": 1,
                "source_id": "s1",
                "source_title": "Source One",
                "url": "https://example.com/a1",
                "title": "Title",
                "description": "Short description",
                "category": None,
                "content": "Full body",
                "author": "Example Author",
                "language": None,
                "keywords": ["tech"],
                "image_url": "https://example.com/images/a1.png",
                "published_at": None,
                "parsed_at": datetime.now(UTC).isoformat(),
            },
        )
        db.commit()

        post = db.get(PostProjection, "a1")
        assert post is not None
        assert post.content == "Full body"
        assert post.description == "Short description"
        assert post.image_ref == "https://example.com/images/a1.png"
        assert post.author == "Example Author"
        assert post.keywords == ["tech"]
        assert post.published_at is None
    finally:
        db.close()


@pytest.mark.parametrize("field", ["source_id", "source_title"])
def test_project_post_rejects_missing_source_identity(
    field: str,
) -> None:
    payload = {
        "post_id": "a1",
        "source_id": "s1",
        "source_title": "Source One",
    }
    payload.pop(field)

    with pytest.raises(ValueError, match=field):
        project_post(MagicMock(), payload)


def test_project_post_replaces_snapshot_fields_on_update() -> None:
    engine = create_engine(
        "sqlite:///:memory:",
        execution_options={"schema_translate_map": {"query": None}},
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    db = SessionLocal()
    try:
        initial_published_at = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
        project_post(
            db,
            payload={
                "post_id": "a1",
                "post_revision": 1,
                "source_id": "s1",
                "source_title": "Source One",
                "url": "https://example.com/a1",
                "title": "Original Title",
                "description": "Original description",
                "category": "technology",
                "content": "Original content",
                "author": "Original Author",
                "language": "en",
                "keywords": ["tech"],
                "image_url": "https://example.com/original.png",
                "published_at": initial_published_at.isoformat(),
            },
        )
        db.commit()

        # A later complete snapshot replaces prior metadata, including nulls.
        project_post(
            db,
            payload={
                "post_id": "a1",
                "post_revision": 2,
                "source_id": "s1",
                "source_title": "Source One",
                "url": "https://example.com/a1-updated",
                "title": "Updated Title",
                "description": None,
                "category": "news",
                "content": None,
                "author": "Updated Author",
                "language": "fr",
                "keywords": ["finance"],
                "image_url": None,
                "published_at": None,
            },
        )
        db.commit()

        post = db.get(PostProjection, "a1")
        assert post is not None
        assert post.canonical_url == "https://example.com/a1-updated"
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
    finally:
        db.close()


def test_project_user_preferences() -> None:
    engine = create_engine(
        "sqlite:///:memory:",
        execution_options={"schema_translate_map": {"query": None}},
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    db = SessionLocal()
    try:
        project_user_preferences(
            db,
            payload={
                "user_id": "u1",
                "muted_keywords": ["crypto", "drama"],
                "muted_categories": ["sports"],
                "blocked_source_ids": ["s-blocked"],
                "languages": ["en", "hu"],
                "updated_at": datetime.now(UTC).isoformat(),
            },
        )
        db.commit()

        prefs = db.get(UserPreferencesProjection, "u1")
        assert prefs is not None
        assert prefs.muted_keywords == ["crypto", "drama"]
        assert prefs.muted_categories == ["sports"]
        assert prefs.blocked_source_ids == ["s-blocked"]
        assert prefs.languages == ["en", "hu"]
    finally:
        db.close()


def test_project_user_preferences_updates_existing() -> None:
    engine = create_engine(
        "sqlite:///:memory:",
        execution_options={"schema_translate_map": {"query": None}},
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    db = SessionLocal()
    try:
        project_user_preferences(
            db,
            payload={
                "user_id": "u1",
                "muted_keywords": ["crypto"],
            },
        )
        db.commit()

        project_user_preferences(
            db,
            payload={
                "user_id": "u1",
                "muted_keywords": ["ai"],
            },
        )
        db.commit()

        prefs = db.get(UserPreferencesProjection, "u1")
        assert prefs is not None
        assert prefs.muted_keywords == ["ai"]
    finally:
        db.close()
