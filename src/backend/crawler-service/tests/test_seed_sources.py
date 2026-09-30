import json
from pathlib import Path
from tempfile import TemporaryDirectory

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


@pytest.mark.parametrize(
    "data",
    [
        {"url": "https://example.com/feed", "title": "Example"},
        [
            {"url": "https://example.com/feed", "title": "Example"},
            {"url": "https://example.com/feed", "title": "Duplicate"},
        ],
    ],
    ids=["wrong-shape", "duplicate-url"],
)
def test_seed_file_rejects_invalid_input(seed_file, data):
    seed_file.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError):
        seed_sources.load_sources(seed_file)
