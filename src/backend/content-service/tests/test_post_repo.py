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


def test_save_repeated_guid_with_changed_url_updates_persisted_post(
    db_session: Session,
) -> None:
    repo = PostRepository(db_session)
    first_data = _make_post_data(
        source_id=UUID("00000000-0000-0000-0000-000000000001"),
        item_guid="guid-1",
        url="https://example.com/original-url",
        title="Original Title",
    )
    first = repo.create_post(first_data)
    assert first is not None
    first_id = first["post_id"]
    assert first["post_revision"] == 1

    second_data = _make_post_data(
        source_id=UUID("00000000-0000-0000-0000-000000000001"),
        item_guid="guid-1",
        url="https://example.com/updated-url",
        title="Updated Title",
    )
    second = repo.create_post(second_data)

    assert second is not None
    assert second["post_id"] == first_id
    assert second["post_revision"] == 2
    assert second["url"] == "https://example.com/updated-url"
    assert second["title"] == "Updated Title"
    saved = repo.get_post_by_id(first_id)
    assert saved is not None
    assert saved.url == "https://example.com/updated-url"
    assert saved.title == "Updated Title"


def test_list_filters_by_category_not_by_keyword(
    db_session: Session,
) -> None:
    repo = PostRepository(db_session)
    repo.create_post(
        _make_post_data(
            item_guid="guid-category-match",
            url="https://example.com/item1",
            category="technology",
            keywords=["science", "computing"],
        )
    )
    repo.create_post(
        _make_post_data(
            item_guid="guid-keyword-only-match",
            url="https://example.com/item2",
            category="sports",
            keywords=["technology", "football"],
        )
    )

    results = repo.get_posts(limit=10, skip=0, category="technology")
    result_guids = [post.item_guid for post in results]

    assert "guid-category-match" in result_guids
    assert "guid-keyword-only-match" not in result_guids


def test_get_by_guids_filters_by_source_and_requested_items(
    db_session: Session,
) -> None:
    repo = PostRepository(db_session)
    repo.create_post(_make_post_data(item_guid="requested"))
    repo.create_post(_make_post_data(item_guid="other-item"))
    repo.create_post(
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
    first = repo.create_post(
        _make_post_data(
            crawled_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            parsed_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
        )
    )
    assert first["post_revision"] == 1

    repeated = repo.create_post(
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
        ("url", "https://example.com/changed"),
        ("source_title", "Changed Source"),
        ("title", "Changed title"),
        ("description", "Changed description"),
        ("category", "Technology"),
        ("content", "Changed content"),
        ("author", "Changed author"),
        ("published_at", datetime(2026, 3, 1, tzinfo=timezone.utc)),
        ("image_url", "https://example.com/image.png"),
        ("language", "en"),
        ("keywords", ["one", "two"]),
    ],
)
def test_each_canonical_field_change_increments_revision(
    db_session: Session, field: str, changed_value: object
) -> None:
    repo = PostRepository(db_session)
    first = repo.create_post(_make_post_data())

    changed = repo.create_post(_make_post_data(**{field: changed_value}))

    assert changed["post_id"] == first["post_id"]
    assert changed["post_revision"] == 2
    expected_value = (
        changed_value.replace(tzinfo=None)
        if isinstance(changed_value, datetime)
        else changed_value
    )
    assert changed[field] == expected_value


@pytest.mark.parametrize(
    ("field", "initial_value"),
    [
        ("description", "present"),
        ("category", "news"),
        ("content", "present"),
        ("author", "present"),
        ("published_at", datetime(2026, 1, 1, tzinfo=timezone.utc)),
        ("image_url", "https://example.com/image.png"),
        ("language", "en"),
    ],
)
def test_null_transition_in_canonical_field_increments_revision(
    db_session: Session, field: str, initial_value: object
) -> None:
    repo = PostRepository(db_session)
    first = repo.create_post(_make_post_data(**{field: initial_value}))

    changed = repo.create_post(_make_post_data(**{field: None}))

    assert changed["post_id"] == first["post_id"]
    assert changed["post_revision"] == 2
    assert changed[field] is None
