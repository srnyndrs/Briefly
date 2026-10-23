from datetime import datetime, timezone
from uuid import UUID

import pytest
from sqlalchemy.orm import Session

from src.repositories.post_repository import PostRepository


def _make_post_data(**overrides) -> dict:
    return {
        "source_id": UUID("00000000-0000-0000-0000-000000000001"),
        "item_guid": "guid-1",
        "url": "https://example.com/1",
        "source_title": "Test Source",
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


def test_get_by_guids_filters_by_source_and_requested_items(
    db_session: Session,
) -> None:
    repo = PostRepository(db_session)
    repo.upsert_post(_make_post_data(item_guid="requested"))
    repo.upsert_post(_make_post_data(item_guid="other-item"))
    repo.upsert_post(
        _make_post_data(
            source_id=UUID("00000000-0000-0000-0000-000000000002"),
            item_guid="requested",
        )
    )

    posts = repo.get_by_guids(
        UUID("00000000-0000-0000-0000-000000000001"),
        ["requested", "requested", "missing"],
    )

    assert len(posts) == 1
    assert posts[0].source_id == UUID("00000000-0000-0000-0000-000000000001")
    assert posts[0].item_guid == "requested"


def test_identical_post_returns_existing_snapshot_without_timestamp_changes(
    db_session: Session,
) -> None:
    repo = PostRepository(db_session)
    first = repo.upsert_post(
        _make_post_data(
            crawled_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            parsed_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
        )
    )
    assert first["post_revision"] == 1

    repeated = repo.upsert_post(
        _make_post_data(
            crawled_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
            parsed_at=datetime(2026, 2, 2, tzinfo=timezone.utc),
        )
    )

    assert repeated["post_id"] == first["post_id"]
    assert repeated["post_revision"] == 1
    assert repeated["crawled_at"] == first["crawled_at"]
    assert repeated["parsed_at"] == first["parsed_at"]


@pytest.mark.parametrize(
    ("field", "changed_value"),
    [
        ("title", "Changed title"),
        ("published_at", datetime(2026, 3, 1, tzinfo=timezone.utc)),
        ("keywords", ["one", "two"]),
    ],
)
def test_representative_canonical_change_increments_revision(
    db_session: Session, field: str, changed_value: object
) -> None:
    repo = PostRepository(db_session)
    first = repo.upsert_post(_make_post_data())

    changed = repo.upsert_post(_make_post_data(**{field: changed_value}))

    assert changed["post_id"] == first["post_id"]
    assert changed["post_revision"] == 2
    expected_value = (
        changed_value.replace(tzinfo=None)
        if isinstance(changed_value, datetime)
        else changed_value
    )
    assert changed[field] == expected_value


def test_description_null_transitions_increment_revision(
    db_session: Session,
) -> None:
    repo = PostRepository(db_session)
    first = repo.upsert_post(_make_post_data(description="present"))
    for revision, value in [(2, None), (3, "restored")]:
        saved = repo.upsert_post(_make_post_data(description=value))
        assert saved["post_id"] == first["post_id"]
        assert saved["post_revision"] == revision
        assert saved["description"] == value
