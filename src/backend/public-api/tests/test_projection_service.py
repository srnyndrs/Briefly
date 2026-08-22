from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.config.database import Base
from src.models.read_models import PostProjection
from src.services.projection_use_cases import (
    ProjectPostInput,
    ProjectPostUseCase,
)


def test_project_post_use_case_persists_content() -> None:
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
        use_case = ProjectPostUseCase(db)
        use_case.execute(
            ProjectPostInput(
                post_id="a1",
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
        )
        db.commit()

        post = db.get(PostProjection, "a1")
        assert post is not None
        assert post.content == "Full body"
        assert post.description == "Short description"
        assert post.image_ref == "https://example.com/images/a1.png"
    finally:
        db.close()


def test_project_user_preferences_use_case() -> None:
    from src.models.read_models import UserPreferencesProjection
    from src.services.projection_use_cases import (
        ProjectUserPreferencesInput,
        ProjectUserPreferencesUseCase,
    )

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
        use_case = ProjectUserPreferencesUseCase(db)
        use_case.execute(
            ProjectUserPreferencesInput(
                user_id="u1",
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
