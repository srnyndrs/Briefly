import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock

import pytest
from sqlalchemy.orm import sessionmaker

from src.models.source import Source
from src.scripts import seed_sources


@pytest.fixture
def seed_file():
    # Avoid pytest's shared temp root, which can have stale Windows ACLs.
    with TemporaryDirectory(prefix="briefly-crawler-seed-") as directory:
        yield Path(directory) / "sources.json"


def test_seed_command_is_idempotent_and_creates_verified_sources(
    seed_file, engine, db_session, monkeypatch
):
    seed_file.write_text(
        json.dumps(
            [
                {
                    "url": "https://example.co.uk/feed",
                    "title": "Example",
                    "site_url": "https://news.example.co.uk/",
                    "site_name": "Example News",
                    "language": "en-GB",
                    "content_type": "application/rss+xml",
                },
                {"url": "https://other.org/feed", "title": "Other"},
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(seed_sources, "SessionLocal", sessionmaker(bind=engine))
    monkeypatch.setattr(seed_sources, "init_db", lambda: None)

    assert seed_sources.seed_sources(seed_file) == (2, 0)
    sources = db_session.query(Source).order_by(Source.title).all()
    assert all(source.verified for source in sources)
    assert all(source.submitted_by_user_id is None for source in sources)
    assert sources[0].site_url == "https://news.example.co.uk/"
    assert sources[0].site_name == "Example News"
    assert sources[0].language == "en"
    sources[0].title = "Updated by user"
    db_session.commit()

    assert seed_sources.seed_sources(seed_file) == (0, 2)
    db_session.refresh(sources[0])
    assert sources[0].title == "Updated by user"
    assert db_session.query(Source).count() == 2


def test_seed_file_rejects_duplicate_urls_before_database_access(
    seed_file, monkeypatch
):
    seed_file.write_text(
        json.dumps(
            [
                {"url": "https://example.com/feed", "title": "Example"},
                {"url": "https://example.com/feed", "title": "Duplicate"},
            ]
        ),
        encoding="utf-8",
    )
    init_db = Mock(
        side_effect=AssertionError(
            "Invalid seeds must not initialize the database"
        )
    )
    session_factory = Mock(
        side_effect=AssertionError("Invalid seeds must not open a session")
    )
    monkeypatch.setattr(seed_sources, "init_db", init_db)
    monkeypatch.setattr(seed_sources, "SessionLocal", session_factory)
    with pytest.raises(ValueError, match="Duplicate source URL"):
        seed_sources.seed_sources(seed_file)
    init_db.assert_not_called()
    session_factory.assert_not_called()
