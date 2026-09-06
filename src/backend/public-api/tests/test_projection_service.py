from datetime import UTC, datetime

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
    SessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False
    )

    db = SessionLocal()
    try:
        project_post(
            db,
            payload={
                "post_id": "a1",
                "source_id": "s1",
                "url": "https://example.com/a1",
                "title": "Title",
                "description": "Short description",
                "content": "Full body",
                "image_url": "https://example.com/images/a1.png",
                "parsed_at": datetime.now(UTC).isoformat(),
            },
        )
        db.commit()

        post = db.get(PostProjection, "a1")
        assert post is not None
        assert post.content == "Full body"
        assert post.description == "Short description"
        assert post.image_ref == "https://example.com/images/a1.png"
    finally:
        db.close()


def test_project_post_preserves_immutable_fields_on_update() -> (
    None
):
    engine = create_engine(
        "sqlite:///:memory:",
        execution_options={"schema_translate_map": {"query": None}},
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False
    )

    db = SessionLocal()
    try:
        initial_published_at = datetime(
            2026, 1, 1, 12, 0, tzinfo=UTC
        )
        project_post(
            db,
            payload={
                "post_id": "a1",
                "source_id": "s1",
                "title": "Original Title",
                "language": "en",
                "keywords": ["tech"],
                "published_at": initial_published_at.isoformat(),
            },
        )
        db.commit()

        # Update with new title, but new language/keywords/published_at should be preserved
        project_post(
            db,
            payload={
                "post_id": "a1",
                "title": "Updated Title",
                "language": "fr",
                "keywords": ["finance"],
                "published_at": datetime(
                    2026, 2, 1, 12, 0, tzinfo=UTC
                ).isoformat(),
            },
        )
        db.commit()

        post = db.get(PostProjection, "a1")
        assert post is not None
        assert post.title == "Updated Title"
        assert post.language == "en"
        assert post.keywords == ["tech"]
        assert (
            post.published_at.replace(tzinfo=UTC)
            == initial_published_at
        )
    finally:
        db.close()


def test_project_user_preferences() -> None:
    engine = create_engine(
        "sqlite:///:memory:",
        execution_options={"schema_translate_map": {"query": None}},
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False
    )

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
                "category_interests": ["tech", "science"],
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
        assert prefs.category_interests == ["tech", "science"]
    finally:
        db.close()


def test_project_user_preferences_updates_existing() -> None:
    engine = create_engine(
        "sqlite:///:memory:",
        execution_options={"schema_translate_map": {"query": None}},
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False
    )

    db = SessionLocal()
    try:
        project_user_preferences(
            db,
            payload={
                "user_id": "u1",
                "muted_keywords": ["crypto"],
                "category_interests": ["tech"],
            },
        )
        db.commit()

        project_user_preferences(
            db,
            payload={
                "user_id": "u1",
                "muted_keywords": ["ai"],
                "category_interests": ["science"],
            },
        )
        db.commit()

        prefs = db.get(UserPreferencesProjection, "u1")
        assert prefs is not None
        assert prefs.muted_keywords == ["ai"]
        assert prefs.category_interests == ["science"]
    finally:
        db.close()
