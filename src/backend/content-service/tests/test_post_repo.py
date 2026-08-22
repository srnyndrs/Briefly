from datetime import datetime, timezone
from unittest.mock import MagicMock

from sqlalchemy.exc import IntegrityError

from src.repositories.post_repository import PostRepository


def _make_post_data(**overrides) -> dict:
    return {
        "source_id": "source-1",
        "item_guid": "guid-1",
        "url": "https://example.com/1",
        "title": "t1",
        "description": "",
        "category": "",
        "content": "",
        "author": "",
        "published_at": None,
        "crawled_at": None,
        "parsed_at": datetime.now(timezone.utc),
        "image_url": None,
        "language": None,
        "keywords": [],
        **overrides,
    }


def test_save_returns_inserted_id() -> None:
    db = MagicMock()
    db.scalar.return_value = "new-post-id"
    repo = PostRepository(db)

    post_id = repo.save(_make_post_data())

    assert post_id == "new-post-id"
    db.commit.assert_called_once()


def test_save_returns_existing_id_on_integrity_error() -> None:
    db = MagicMock()
    db.scalar.side_effect = IntegrityError(
        "stmt", {}, Exception("boom")
    )
    query_mock = MagicMock()
    filter_mock = MagicMock()
    db.query.return_value = query_mock
    query_mock.filter.return_value = filter_mock
    filter_mock.scalar.return_value = "existing-post-id"

    repo = PostRepository(db)
    post_id = repo.save(_make_post_data())

    assert post_id == "existing-post-id"
    db.rollback.assert_called_once()
