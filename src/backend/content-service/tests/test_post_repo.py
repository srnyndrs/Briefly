from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.repositories.post_repository import PostRepository


def _make_post_data(**overrides) -> dict:
    return {
        "source_id": "source-1",
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
        source_id="source-1",
        item_guid="guid-1",
        url="https://example.com/original-url",
        title="Original Title",
    )
    first_id = repo.save(first_data)
    assert first_id is not None

    second_data = _make_post_data(
        source_id="source-1",
        item_guid="guid-1",
        url="https://example.com/updated-url",
        title="Updated Title",
    )
    second_id = repo.save(second_data)

    assert second_id == first_id
    saved = repo.get_by_id(first_id)
    assert saved is not None
    assert saved.url == "https://example.com/updated-url"
    assert saved.title == "Updated Title"


def test_list_filters_by_category_not_by_keyword(
    db_session: Session,
) -> None:
    repo = PostRepository(db_session)
    repo.save(
        _make_post_data(
            item_guid="guid-category-match",
            url="https://example.com/item1",
            category="technology",
            keywords=["science", "computing"],
        )
    )
    repo.save(
        _make_post_data(
            item_guid="guid-keyword-only-match",
            url="https://example.com/item2",
            category="sports",
            keywords=["technology", "football"],
        )
    )

    results = repo.list(limit=10, skip=0, category="technology")
    result_guids = [post.item_guid for post in results]

    assert "guid-category-match" in result_guids
    assert "guid-keyword-only-match" not in result_guids


def test_get_by_guids_filters_by_source_and_requested_items(
    db_session: Session,
) -> None:
    repo = PostRepository(db_session)
    repo.save(_make_post_data(item_guid="requested"))
    repo.save(_make_post_data(item_guid="other-item"))
    repo.save(
        _make_post_data(source_id="source-2", item_guid="requested")
    )

    posts = repo.get_by_guids(
        "source-1", ["requested", "requested", "missing"]
    )

    assert len(posts) == 1
    assert posts[0].source_id == "source-1"
    assert posts[0].item_guid == "requested"
