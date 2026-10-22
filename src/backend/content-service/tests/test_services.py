import logging
from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest
from feedparser import FeedParserDict
from sqlalchemy.orm import Session

from src.models.post import Post
from src.repositories.post_repository import PostRepository
from src.services.feed_processor import (
    FeedProcessor,
    _entry_guid,
    _normalize_language,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("hu-HU", "hu"),
        ("iw-IL", "he"),
        ("", None),
        ("this-is-not-a-language", None),
    ],
)
def test_normalize_language(raw: str, expected: str | None) -> None:
    assert _normalize_language(raw) == expected


def _make_event(
    source_id: str = "00000000-0000-0000-0000-000000000001",
    source_title: str = "Crawler Source",
    raw_xml: str = '<rss version="2.0"><channel/></rss>',
    correlation_id: str = "test-corr-id",
) -> dict:
    return {
        "event_type": "feed.raw_fetched.v1",
        "correlation_id": correlation_id,
        "payload": {
            "source_id": source_id,
            "source_title": source_title,
            "raw_xml": raw_xml,
        },
        "occurred_at": datetime.now(timezone.utc).isoformat(),
    }


def _capture_saved_payload(
    entry: Any,
    extracted: dict[str, Any],
    feed_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    db = MagicMock()
    channel = MagicMock()
    feed_mock = MagicMock()
    feed_mock.entries = [entry]
    feed_mock.feed = feed_data or {}
    saved_payloads: list[dict[str, Any]] = []

    with (
        patch(
            "src.services.feed_processor.feedparser.parse",
            return_value=feed_mock,
        ),
        patch(
            "src.adapters.content_extractor.extract_article",
            return_value=extracted,
        ),
        patch(
            "src.repositories.post_repository.PostRepository.upsert_post",
            side_effect=lambda data: (
                saved_payloads.append(dict(data))
                or {**data, "post_id": "p1", "post_revision": 1}
            ),
        ),
        patch(
            "src.services.feed_processor.post_publisher.publish_post_parsed_success"
        ),
    ):
        FeedProcessor(PostRepository(db)).process(channel, _make_event())

    return saved_payloads[0]


def test_process_source_uses_feed_metadata_as_baseline() -> None:
    entry = FeedParserDict(
        {
            "id": "g-merge-policy",
            "link": "https://example.com/merge-policy",
            "title": " Feed title ",
            "description": " Feed description ",
            "author": " Feed author ",
            "tags": [{"term": "Feed category"}],
            "published_parsed": (
                2026,
                9,
                12,
                17,
                30,
                35,
                0,
                0,
            ),
            "links": [
                {
                    "rel": "enclosure",
                    "href": "https://example.com/feed-image.jpg",
                }
            ],
        }
    )
    saved = _capture_saved_payload(
        entry,
        {
            "title": "null: undefined",
            "description": "Extracted description",
            "content": "Extracted body",
            "image": "https://example.com/extracted-image.jpg",
            "authors": ["Extracted author"],
            "language": "en",
            "keywords": ["extracted"],
            "publish_date": datetime(2026, 9, 12, 0, 0, tzinfo=timezone.utc),
        },
        {"title": "Publisher", "language": "hu"},
    )
    assert saved["title"] == "Feed title"
    assert saved["description"] == "Feed description"
    assert saved["author"] == "Feed author"
    assert saved["category"] == "Feed category"
    assert saved["published_at"] == datetime(
        2026, 9, 12, 17, 30, 35, tzinfo=timezone.utc
    )
    assert saved["image_url"] == "https://example.com/feed-image.jpg"
    assert saved["language"] == "hu"
    assert saved["content"] == "Extracted body"
    assert saved["keywords"] == ["extracted"]


def test_process_source_normalizes_html_feed_description() -> None:
    entry = FeedParserDict(
        {
            "id": "g-html-description",
            "link": "https://example.com/html-description",
            "title": "Title",
            "description": (
                "<p>Short summary.</p><p>The post "
                '<a href="https://example.com/article">Title</a> '
                "first appeared on "
                '<a href="https://example.com">Example</a>.</p>'
            ),
        }
    )

    saved = _capture_saved_payload(entry, {"content": "Body"})

    assert saved["description"] == (
        "Short summary.\nThe post Title first appeared on Example."
    )
    assert "<" not in saved["description"]
    assert ">" not in saved["description"]


def test_process_source_uses_valid_extracted_fallbacks() -> None:
    entry = FeedParserDict(
        {
            "id": "g-extracted-fallback",
            "link": "https://example.com/extracted-fallback",
            "title": " ",
        }
    )
    saved = _capture_saved_payload(
        entry,
        {
            "title": " Extracted title ",
            "description": " Extracted description ",
            "content": "Body",
            "image": " https://example.com/image.jpg ",
            "authors": [" Extracted author "],
            "language": " en ",
            "keywords": ["keyword"],
        },
    )
    assert saved["title"] == "Extracted title"
    assert saved["description"] == "Extracted description"
    assert saved["author"] == "Extracted author"
    assert saved["image_url"] == "https://example.com/image.jpg"
    assert saved["language"] == "en"


def test_process_source_persists_source_title(
    db_session: Session,
) -> None:
    channel = MagicMock()
    entry = {
        "id": "guid-persisted-title",
        "link": "https://example.com/persisted-title",
        "title": "Title",
    }
    feed_mock = MagicMock()
    feed_mock.entries = [entry]
    feed_mock.feed = {"title": "Persisted Publisher Title"}

    with (
        patch(
            "src.services.feed_processor.feedparser.parse",
            return_value=feed_mock,
        ),
        patch(
            "src.adapters.content_extractor.extract_article",
            return_value={"title": "Title", "content": "Body"},
        ),
        patch(
            "src.services.feed_processor.post_publisher.publish_post_parsed_success"
        ) as mock_publish,
    ):
        FeedProcessor(PostRepository(db_session)).process(
            channel,
            _make_event(
                source_id="00000000-0000-0000-0000-000000000001",
                source_title="  Registered Source  ",
            ),
        )

    db_session.expire_all()
    post = (
        db_session.query(Post)
        .filter(Post.item_guid == "guid-persisted-title")
        .one()
    )
    assert post.source_title == "Registered Source"
    assert mock_publish.call_args.kwargs["source_title"] == "Registered Source"


def test_process_source_propagates_unexpected_extraction_error() -> None:
    db = MagicMock()
    channel = MagicMock()

    entry = {
        "id": "g1",
        "link": "https://bad.url",
        "title": "Bad",
    }
    feed_mock = MagicMock()
    feed_mock.entries = [entry]

    with (
        patch(
            "src.services.feed_processor.feedparser.parse",
            return_value=feed_mock,
        ),
        patch(
            "src.adapters.content_extractor.extract_article",
            side_effect=RuntimeError("network error"),
        ),
        patch(
            "src.repositories.post_repository.PostRepository.upsert_post"
        ) as mock_save,
    ):
        with pytest.raises(RuntimeError, match="network error"):
            FeedProcessor(PostRepository(db)).process(channel, _make_event())
        assert not mock_save.called


@pytest.mark.parametrize("field", ["source_id", "source_title"])
def test_process_source_rejects_missing_source_identity(
    field: str,
) -> None:
    event = _make_event()
    event["payload"].pop(field)

    with pytest.raises(ValueError, match=field):
        FeedProcessor(PostRepository(MagicMock())).process(MagicMock(), event)


@pytest.mark.parametrize(
    ("entry", "expected"),
    [
        ({"guid": "guid", "id": "id", "link": "url"}, "guid"),
        ({"guid": " ", "id": " id ", "link": "url"}, "id"),
        (
            {"id": None, "link": " https://example.com/item "},
            "https://example.com/item",
        ),
    ],
)
def test_entry_guid_uses_first_nonblank_identity(
    entry: dict[str, Any], expected: str
) -> None:
    assert _entry_guid(entry) == expected


@pytest.mark.parametrize(
    ("identity", "link"),
    [
        (
            "https://example.com/posts/42#section",
            "https://example.com/posts/42",
        ),
        ("https://example.com/posts/42#١", "https://example.com/posts/42"),
        ("https://example.com/posts/42#0", "https://example.com/posts/other"),
        ("https://example.com/posts/42#0", "https://other.test/posts/42"),
        ("https://[invalid#0", "https://example.com/posts/42"),
        ("https://example.com/posts/42#0", None),
    ],
)
def test_entry_guid_preserves_unrecognized_identity(
    identity: str, link: str | None
) -> None:
    assert _entry_guid({"guid": identity, "link": link}) == identity


def test_process_source_rejects_missing_entry_identity() -> None:
    with pytest.raises(ValueError, match="item_guid"):
        FeedProcessor(PostRepository(MagicMock())).process(
            MagicMock(),
            _make_event(raw_xml="<rss><channel><item/></channel></rss>"),
        )


def test_numeric_fragment_variants_reuse_saved_post(
    db_session: Session,
) -> None:
    def event(*fragments: str, title: str = "RSS title") -> dict[str, Any]:
        items = "".join(
            f"<item><guid>https://example.com/posts/42#{fragment}</guid>"
            "<link>https://example.com/posts/42?rss=1</link>"
            f"<title>{title}</title></item>"
            for fragment in fragments
        )
        return _make_event(raw_xml=f"<rss><channel>{items}</channel></rss>")

    service = FeedProcessor(PostRepository(db_session))
    with (
        patch(
            "src.adapters.content_extractor.extract_article",
            return_value={"content": "Body"},
        ) as extract,
        patch(
            "src.services.feed_processor.post_publisher.publish_post_parsed_success"
        ) as publish,
    ):
        service.process(MagicMock(), event("0", "1"))
        service.process(MagicMock(), event("12"))
        service.process(MagicMock(), event("0", title="Updated RSS title"))

    extract.assert_called_once_with("https://example.com/posts/42?rss=1")
    snapshots = [call.kwargs for call in publish.call_args_list]
    assert [snapshot["post_revision"] for snapshot in snapshots] == [1, 1, 1, 2]
    assert snapshots[0] == snapshots[1] == snapshots[2]
    assert len({snapshot["post_id"] for snapshot in snapshots}) == 1
    assert {snapshot["item_guid"] for snapshot in snapshots} == {
        "https://example.com/posts/42"
    }
    db_session.expire_all()
    post = db_session.query(Post).one()
    assert str(post.post_id) == snapshots[0]["post_id"]
    assert post.post_revision == 2
    assert post.title == "Updated RSS title"


def test_repeated_feed_reuses_extraction_and_publishes_rss_updates(
    db_session: Session,
) -> None:
    content = "Extracted body"
    event = _make_event(
        raw_xml=(
            "<rss><channel><item><guid>repeated-item</guid>"
            "<link>https://example.com/repeated-item</link>"
            "<title>Original RSS title</title>"
            "<description>Original RSS description</description>"
            "</item></channel></rss>"
        ),
    )
    event["occurred_at"] = "2026-09-20T10:00:00Z"
    service = FeedProcessor(PostRepository(db_session))
    with (
        patch(
            "src.adapters.content_extractor.extract_article",
            return_value={
                "content": content,
                "authors": ["Article author"],
                "keywords": ["extracted keyword"],
                "image": "https://example.com/image.jpg",
                "language": "hu-HU",
                "publish_date": datetime(2026, 9, 20),
            },
        ) as extract,
        patch(
            "src.services.feed_processor.post_publisher.publish_post_parsed_success"
        ) as publish,
    ):
        service.process(MagicMock(), event)
        first_snapshot = publish.call_args.kwargs
        assert first_snapshot["post_revision"] == 1
        db_session.expire_all()
        stored = db_session.query(Post).one()
        first_times = (stored.crawled_at, stored.parsed_at)

        extract.reset_mock()
        event["occurred_at"] = "2026-09-27T10:00:00Z"
        service.process(MagicMock(), event)

        extract.assert_not_called()
        assert publish.call_count == 2
        repeated_snapshot = publish.call_args_list[1].kwargs
        assert repeated_snapshot == first_snapshot
        db_session.expire_all()
        stored = db_session.query(Post).one()
        assert (stored.crawled_at, stored.parsed_at) == first_times
        assert stored.post_revision == 1

        event["payload"]["raw_xml"] = event["payload"]["raw_xml"].replace(
            "Original RSS", "Updated RSS"
        )
        event["payload"]["source_title"] = "Updated Source"
        event["occurred_at"] = "2026-09-28T10:00:00Z"
        service.process(MagicMock(), event)

        extract.assert_not_called()
        assert publish.call_count == 3
        snapshot = publish.call_args.kwargs
        assert snapshot["post_id"] == first_snapshot["post_id"]
        assert snapshot["post_revision"] == 2
        assert snapshot["title"] == "Updated RSS title"
        assert snapshot["description"] == "Updated RSS description"
        assert snapshot["source_title"] == "Updated Source"
        assert snapshot["content"] == content
        assert snapshot["author"] == "Article author"
        assert snapshot["keywords"] == ["extracted keyword"]
        assert snapshot["image_url"] == "https://example.com/image.jpg"
        assert snapshot["language"] == "hu"
        assert snapshot["correlation_id"] == "test-corr-id"

    db_session.expire_all()
    post = db_session.get(Post, UUID(first_snapshot["post_id"]))
    assert post is not None
    assert post.title == "Updated RSS title"
    assert post.content == content
    assert post.crawled_at == datetime(2026, 9, 28, 10)
    assert post.parsed_at != post.crawled_at
    assert post.post_revision == 2
    assert db_session.query(Post).count() == 1


def test_duplicate_entries_in_one_feed_republish_one_revision(
    db_session: Session,
) -> None:
    event = _make_event(
        raw_xml=(
            "<rss><channel>"
            "<item><guid>duplicate</guid><link>https://example.com/duplicate</link>"
            "<title>Same</title></item>"
            "<item><guid>duplicate</guid><link>https://example.com/duplicate</link>"
            "<title>Same</title></item>"
            "</channel></rss>"
        ),
    )
    with (
        patch(
            "src.adapters.content_extractor.extract_article",
            return_value={"content": "Body"},
        ) as extract,
        patch(
            "src.services.feed_processor.post_publisher.publish_post_parsed_success"
        ) as publish,
    ):
        FeedProcessor(PostRepository(db_session)).process(MagicMock(), event)

    extract.assert_called_once_with("https://example.com/duplicate")
    assert [
        call.kwargs["post_revision"] for call in publish.call_args_list
    ] == [1, 1]
    assert (
        publish.call_args_list[0].kwargs["post_id"]
        == publish.call_args_list[1].kwargs["post_id"]
    )
    db_session.expire_all()
    post = db_session.query(Post).one()
    assert post.post_revision == 1


def test_changed_url_extracts_once_and_preserves_stored_fallbacks(
    db_session: Session,
) -> None:
    event = _make_event(
        raw_xml=(
            "<rss><channel><item><guid>changed-url</guid>"
            "<link>https://example.com/original</link>"
            "<title>Original RSS title</title>"
            "<description>Original RSS description</description>"
            "<category>Original category</category>"
            "</item></channel></rss>"
        )
    )
    service = FeedProcessor(PostRepository(db_session))
    with (
        patch(
            "src.adapters.content_extractor.extract_article",
            return_value={
                "content": "Original body",
                "authors": ["Original author"],
                "keywords": ["original"],
                "image": "https://example.com/image.jpg",
                "language": "hu",
                "publish_date": datetime(2026, 9, 20),
            },
        ) as extract,
        patch(
            "src.services.feed_processor.post_publisher.publish_post_parsed_success"
        ) as publish,
    ):
        service.process(MagicMock(), event)
        first_id = publish.call_args.kwargs["post_id"]
        extract.reset_mock()
        extract.return_value = {"error": "HTTP 502"}
        event["payload"]["raw_xml"] = (
            "<rss><channel><item><guid>changed-url</guid>"
            "<link>https://example.com/updated</link>"
            "</item></channel></rss>"
        )

        service.process(MagicMock(), event)
        service.process(MagicMock(), event)

        extract.assert_called_once_with("https://example.com/updated")
        snapshot = publish.call_args.kwargs
        assert publish.call_count == 3
        assert snapshot["post_id"] == first_id
        assert snapshot["url"] == "https://example.com/updated"
        assert snapshot["title"] == "Original RSS title"
        assert snapshot["description"] == "Original RSS description"
        assert snapshot["category"] == "Original category"
        assert snapshot["content"] == "Original body"
        assert snapshot["author"] == "Original author"
        assert snapshot["keywords"] == ["original"]
        assert snapshot["language"] == "hu"
        assert snapshot["image_url"] == "https://example.com/image.jpg"
        assert snapshot["published_at"].startswith("2026-09-20")

    db_session.expire_all()
    post = db_session.get(Post, UUID(first_id))
    assert post is not None
    assert post.url == "https://example.com/updated"
    assert post.content == "Original body"
    assert db_session.query(Post).count() == 1


def test_duplicate_feed_entries_extract_once_and_new_items_extract(
    db_session: Session,
) -> None:
    item = (
        "<item><guid>duplicate</guid>"
        "<link>https://example.com/duplicate</link>"
        "<title>RSS title</title></item>"
    )
    event = _make_event(raw_xml=f"<rss><channel>{item}{item}</channel></rss>")
    service = FeedProcessor(PostRepository(db_session))
    with (
        patch(
            "src.adapters.content_extractor.extract_article",
            return_value={"content": "Body"},
        ) as extract,
        patch(
            "src.services.feed_processor.post_publisher.publish_post_parsed_success"
        ) as publish,
    ):
        service.process(MagicMock(), event)
        extract.assert_called_once_with("https://example.com/duplicate")
        assert publish.call_count == 2
        assert (
            publish.call_args_list[0].kwargs["post_id"]
            == publish.call_args_list[1].kwargs["post_id"]
        )

        extract.reset_mock()
        new_item = item.replace("duplicate", "new-item")
        event["payload"]["raw_xml"] = (
            f"<rss><channel>{item}{new_item}</channel></rss>"
        )
        service.process(MagicMock(), event)
        extract.assert_called_once_with("https://example.com/new-item")
        assert publish.call_count == 4

    assert db_session.query(Post).count() == 2


def test_invalid_article_link_preserves_rss_metadata_without_request(
    db_session: Session,
) -> None:
    entry = {
        "id": "invalid-link",
        "link": "file:///article",
        "title": "RSS title",
    }
    feed = MagicMock(entries=[entry], feed={})
    with (
        patch(
            "src.services.feed_processor.feedparser.parse",
            return_value=feed,
        ),
        patch("src.adapters.content_extractor.extract_article") as extract,
        patch(
            "src.services.feed_processor.post_publisher.publish_post_parsed_success"
        ) as publish,
    ):
        FeedProcessor(PostRepository(db_session)).process(
            MagicMock(), _make_event()
        )

    extract.assert_not_called()
    assert publish.call_args.kwargs["title"] == "RSS title"
    assert publish.call_args.kwargs["url"] == ""


@pytest.mark.parametrize(
    "event",
    [
        {"event_type": "post.parsed.v1"},
        {"event_type": "feed.raw_fetched.v1", "payload": []},
        {
            "event_type": "feed.raw_fetched.v1",
            "payload": {"raw_xml": " "},
        },
    ],
)
def test_invalid_event_shape_is_rejected_before_database_work(
    event: Any,
) -> None:
    db = MagicMock()
    with pytest.raises(ValueError):
        FeedProcessor(PostRepository(db)).process(MagicMock(), event)
    db.query.assert_not_called()


def test_unusable_feed_is_rejected() -> None:
    with pytest.raises(ValueError, match="usable RSS/Atom"):
        FeedProcessor(PostRepository(MagicMock())).process(
            MagicMock(), _make_event(raw_xml="<html>Page</html>")
        )


def test_empty_valid_feed_completes_and_services_io(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO)
    progress = MagicMock()
    FeedProcessor(PostRepository(MagicMock())).process(
        MagicMock(), _make_event(), on_progress=progress
    )
    progress.assert_called_once()
    assert "completed=True" in caplog.text
    assert "entries=0, attempted=0, reused=0, partial=0" in caplog.text


def test_save_without_snapshot_does_not_publish() -> None:
    service = FeedProcessor(PostRepository(MagicMock()))
    service._repo = MagicMock()
    service._repo.get_by_guids.return_value = []
    service._repo.upsert_post.return_value = None
    with (
        patch(
            "src.services.feed_processor.post_publisher.publish_post_parsed_success"
        ) as publish,
        pytest.raises(RuntimeError, match="Post save returned no snapshot"),
    ):
        service.process(
            MagicMock(),
            _make_event(
                raw_xml="<rss><channel><item><guid>item</guid></item></channel></rss>"
            ),
        )
    publish.assert_not_called()


def test_partial_feed_replay_reuses_committed_entries_after_publish_failure(
    db_session: Session,
) -> None:
    event = _make_event(
        raw_xml=(
            '<rss version="2.0"><channel>'
            "<item><guid>first</guid><link>https://example.com/first</link></item>"
            "<item><guid>second</guid><link>https://example.com/second</link></item>"
            "</channel></rss>"
        )
    )
    progress = MagicMock()
    with (
        patch(
            "src.adapters.content_extractor.extract_article",
            return_value={"content": "Body"},
        ) as extract,
        patch(
            "src.services.feed_processor.post_publisher.publish_post_parsed_success"
        ) as publish,
    ):
        publish.side_effect = [None, RuntimeError("Publish confirmation lost")]
        with pytest.raises(RuntimeError, match="Publish confirmation lost"):
            FeedProcessor(PostRepository(db_session)).process(
                MagicMock(), event, on_progress=progress
            )
        original_snapshots = [
            (
                call.kwargs["post_id"],
                call.kwargs["post_revision"],
                call.kwargs["title"],
                call.kwargs["content"],
            )
            for call in publish.call_args_list
        ]
        assert extract.call_count == 2
        extract.reset_mock()
        publish.reset_mock()
        publish.side_effect = None
        progress.reset_mock()

        FeedProcessor(PostRepository(db_session)).process(
            MagicMock(), event, on_progress=progress
        )

    extract.assert_not_called()
    replayed_snapshots = [
        (
            call.kwargs["post_id"],
            call.kwargs["post_revision"],
            call.kwargs["title"],
            call.kwargs["content"],
        )
        for call in publish.call_args_list
    ]
    assert replayed_snapshots == original_snapshots
    assert [revision for _, revision, _, _ in replayed_snapshots] == [1, 1]
    assert progress.call_count == 3
    db_session.expire_all()
    posts = db_session.query(Post).order_by(Post.item_guid).all()
    assert [post.post_revision for post in posts] == [1, 1]
