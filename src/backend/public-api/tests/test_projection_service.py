from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.services.projection_use_cases import (
    ProjectArticleInput,
    ProjectArticleUseCase,
)
from src.config.database import Base
from src.models.read_models import ArticleProjection


def test_project_article_use_case_persists_content() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False
    )

    db = SessionLocal()
    try:
        use_case = ProjectArticleUseCase(db)
        use_case.execute(
            ProjectArticleInput(
                article_id="a1",
                payload={
                    "article_id": "a1",
                    "source_id": "s1",
                    "url": "https://example.com/a1",
                    "title": "Title",
                    "description": "Short description",
                    "content": "Full body",
                    "parsed_at": datetime.now(UTC).isoformat(),
                },
            )
        )
        db.commit()

        article = db.get(ArticleProjection, "a1")
        assert article is not None
        assert article.content == "Full body"
        assert article.description == "Short description"
    finally:
        db.close()
