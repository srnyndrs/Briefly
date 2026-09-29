from datetime import datetime, timezone
import logging
from typing import Any
from unittest.mock import MagicMock, patch

from feedparser import FeedParserDict
import pytest
from sqlalchemy.orm import Session

from src.models.post import Post
from src.services.source_processor import (
    SourceProcessorService,
    _entry_guid,
    _normalize_language,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("hu-HU", "hu"),
        ("hu_HU", "hu"),
        ("en-US", "en"),
        ("eng-US", "en"),
        ("iw-IL", "he"),
        ("sr-Latn", "sr"),
        ("fil-PH", "fil"),
        ("yue-Hant-HK", "yue"),
        ("ast-ES", "ast"),
        ("qaa", "qaa"),
        ("", None),
        ("und", None),
        ("this-is-not-a-language", None),
        ("x-private", None),
    ],
)
def test_normalize_language(raw: str, expected: str | None) -> None:
    assert _normalize_language(raw) == expected


def test_normalize_language_precedence_skips_invalid_candidates() -> (
    None
):
    entry = FeedParserDict(
        {
            "id": "g-language-precedence",
            "link": "https://example.com/language-precedence",
            "title": "Title",
            "language": "this-is-not-a-language",
        }
    )

    saved = _capture_saved_payload(
        entry,
        {"content": "Body", "language": "fr-FR"},
        {"language": "hu-HU"},
    )

    assert saved["language"] == "hu"


def test_normalize_language_precedence_uses_extracted_fallback() -> (
    None
):
    entry = FeedParserDict(
        {
            "id": "g-language-extracted-fallback",
            "link": "https://example.com/language-extracted-fallback",
            "title": "Title",
        }
    )

    saved = _capture_saved_payload(
        entry,
        {"content": "Body", "language": "fr-FR"},
        {"language": "this-is-not-a-language"},
    )

    assert saved["language"] == "fr"


def _make_event(
    source_id: str = "s1",
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
            "src.services.source_processor.feedparser.parse",
            return_value=feed_mock,
        ),
        patch(
            "src.adapters.content_extractor.extract_article",
            return_value=extracted,
        ),
        patch(
            "src.repositories.post_repository.PostRepository.save",
            side_effect=lambda data: (
                saved_payloads.append(dict(data)) or "p1"
            ),
        ),
        patch(
            "src.services.source_processor.post_publisher.publish_post_parsed_success"
        ),
    ):
        SourceProcessorService(db).process(channel, _make_event())

    return saved_payloads[0]


def test_process_source_persists_and_publishes() -> None:
    db = MagicMock()
    channel = MagicMock()

    entry = {
        "id": "g1",
        "link": "https://example.com/1",
        "title": "Title",
    }
    feed_mock = MagicMock()
    feed_mock.entries = [entry]

    with (
        patch(
            "src.services.source_processor.feedparser.parse",
            return_value=feed_mock,
        ),
        patch(
            "src.adapters.content_extractor.extract_article",
            return_value={
                "title": "Title",
                "content": "Body",
                "image": None,
            },
        ),
        patch(
            "src.repositories.post_repository.PostRepository.save",
            return_value="p1",
        ),
        patch(
            "src.services.source_processor.post_publisher.publish_post_parsed_success"
        ) as mock_publish,
    ):
        SourceProcessorService(db).process(channel, _make_event())
        assert mock_publish.called
        call_kwargs = mock_publish.call_args.kwargs
        assert call_kwargs["post_id"] == "p1"
        assert call_kwargs["source_id"] == "s1"
        assert call_kwargs["correlation_id"] == "test-corr-id"


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
            "publish_date": datetime(
                2026, 9, 12, 0, 0, tzinfo=timezone.utc
            ),
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


def test_process_source_uses_summary_after_blank_html_description() -> (
    None
):
    entry = FeedParserDict(
        {
            "id": "g-blank-html-description",
            "link": "https://example.com/blank-html-description",
            "title": "Title",
            "description": "<p> </p>",
            "summary": "<p>Feed summary</p>",
        }
    )

    saved = _capture_saved_payload(entry, {"content": "Body"})

    assert saved["description"] == "Feed summary"


def test_process_source_uses_extracted_description_after_blank_html() -> (
    None
):
    entry = FeedParserDict(
        {
            "id": "g-blank-html-description",
            "link": "https://example.com/blank-html-description",
            "title": "Title",
            "description": "<br>",
        }
    )

    saved = _capture_saved_payload(
        entry,
        {
            "content": "Body",
            "description": "<p>Extracted description</p>",
        },
    )

    assert saved["description"] == "Extracted description"


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


def test_process_source_rejects_malformed_extracted_title() -> None:
    entry = FeedParserDict(
        {
            "id": "g-malformed-title",
            "link": "https://example.com/malformed-title",
            "title": "",
        }
    )
    saved = _capture_saved_payload(
        entry,
        {"title": "null: undefined", "content": "Body"},
    )

    assert saved["title"] == "Untitled"


def test_process_source_stores_source_title() -> None:
    db = MagicMock()
    channel = MagicMock()

    entry = {
        "id": "g1",
        "link": "https://example.com/1",
        "title": "Title",
    }
    feed_mock = MagicMock()
    feed_mock.entries = [entry]
    feed_mock.feed = {
        "title": "Feed Publisher Title",
        "language": "hu",
    }

    saved_payloads: list[dict] = []

    def mock_save_impl(data: dict) -> str:
        saved_payloads.append(dict(data))
        return "p1"

    with (
        patch(
            "src.services.source_processor.feedparser.parse",
            return_value=feed_mock,
        ),
        patch(
            "src.adapters.content_extractor.extract_article",
            return_value={
                "title": "Title",
                "content": "Body",
                "image": None,
            },
        ),
        patch(
            "src.repositories.post_repository.PostRepository.save",
            side_effect=mock_save_impl,
        ) as mock_save,
        patch(
            "src.services.source_processor.post_publisher.publish_post_parsed_success"
        ) as mock_publish,
    ):
        SourceProcessorService(db).process(
            channel,
            _make_event(source_id="s1", correlation_id="test-corr"),
        )
        assert mock_save.called
        assert len(saved_payloads) == 1
        assert saved_payloads[0].get("source_title") == "Crawler Source"
        assert (
            mock_publish.call_args.kwargs.get("source_title")
            == "Crawler Source"
        )


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
            "src.services.source_processor.feedparser.parse",
            return_value=feed_mock,
        ),
        patch(
            "src.adapters.content_extractor.extract_article",
            return_value={"title": "Title", "content": "Body"},
        ),
        patch(
            "src.services.source_processor.post_publisher.publish_post_parsed_success"
        ) as mock_publish,
    ):
        SourceProcessorService(db_session).process(
            channel,
            _make_event(
                source_id="source-1",
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
    assert (
        mock_publish.call_args.kwargs["source_title"]
        == "Registered Source"
    )


def test_process_source_propagates_unexpected_extraction_error() -> (
    None
):
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
            "src.services.source_processor.feedparser.parse",
            return_value=feed_mock,
        ),
        patch(
            "src.adapters.content_extractor.extract_article",
            side_effect=RuntimeError("network error"),
        ),
        patch(
            "src.repositories.post_repository.PostRepository.save"
        ) as mock_save,
    ):
        with pytest.raises(RuntimeError, match="network error"):
            SourceProcessorService(db).process(channel, _make_event())
        assert not mock_save.called


@pytest.mark.parametrize("field", ["source_id", "source_title"])
def test_process_source_rejects_missing_source_identity(
    field: str,
) -> None:
    event = _make_event()
    event["payload"].pop(field)

    with pytest.raises(ValueError, match=field):
        SourceProcessorService(MagicMock()).process(MagicMock(), event)


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


def test_process_source_rejects_missing_entry_identity() -> None:
    with pytest.raises(ValueError, match="item_guid"):
        SourceProcessorService(MagicMock()).process(
            MagicMock(),
            _make_event(
                raw_xml="<rss><channel><item/></channel></rss>"
            ),
        )


@pytest.mark.parametrize("content", ["Extracted body", None])
def test_repeated_feed_reuses_extraction_and_publishes_rss_updates(
    db_session: Session, content: str | None
) -> None:
    event = _make_event(
        raw_xml=(
            "<rss><channel><item><guid>repeated-item</guid>"
            "<link>https://example.com/repeated-item</link>"
            "<title>Original RSS title</title>"
            "<description>Original RSS description</description>"
            "</item></channel></rss>"
        ),
    )
    service = SourceProcessorService(db_session)
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
            "src.services.source_processor.post_publisher.publish_post_parsed_success"
        ) as publish,
    ):
        service.process(MagicMock(), event)
        first_snapshot = publish.call_args.kwargs
        extract.reset_mock()
        event["payload"]["raw_xml"] = event["payload"][
            "raw_xml"
        ].replace("Original RSS", "Updated RSS")
        event["payload"]["source_title"] = "Updated Source"
        event["occurred_at"] = "2026-09-28T10:00:00Z"

        service.process(MagicMock(), event)

        extract.assert_not_called()
        assert publish.call_count == 2
        snapshot = publish.call_args.kwargs
        assert snapshot["post_id"] == first_snapshot["post_id"]
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
    post = db_session.get(Post, first_snapshot["post_id"])
    assert post is not None
    assert post.title == "Updated RSS title"
    assert post.content == content
    assert post.crawled_at == datetime(2026, 9, 28, 10)
    assert post.parsed_at != post.crawled_at
    assert db_session.query(Post).count() == 1


@pytest.mark.parametrize(
    ("extracted", "expected_content"),
    [
        ({"content": "Updated body"}, "Updated body"),
        (
            {"error": "HTTP 502", "content": "", "title": ""},
            "Original body",
        ),
    ],
)
def test_changed_url_extracts_once_and_preserves_stored_fallbacks(
    db_session: Session,
    extracted: dict[str, Any],
    expected_content: str,
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
    service = SourceProcessorService(db_session)
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
            "src.services.source_processor.post_publisher.publish_post_parsed_success"
        ) as publish,
    ):
        service.process(MagicMock(), event)
        first_id = publish.call_args.kwargs["post_id"]
        extract.reset_mock()
        extract.return_value = extracted
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
        assert snapshot["content"] == expected_content
        assert snapshot["author"] == "Original author"
        assert snapshot["keywords"] == ["original"]
        assert snapshot["language"] == "hu"
        assert snapshot["image_url"] == "https://example.com/image.jpg"
        assert snapshot["published_at"].startswith("2026-09-20")

    db_session.expire_all()
    post = db_session.get(Post, first_id)
    assert post is not None
    assert post.url == "https://example.com/updated"
    assert post.content == expected_content
    assert db_session.query(Post).count() == 1


@pytest.mark.parametrize(
    "extracted",
    [{"content": "Body"}, {"error": "Blocked", "content": ""}],
)
def test_duplicate_feed_entries_extract_once_and_new_items_extract(
    db_session: Session, extracted: dict[str, Any]
) -> None:
    item = (
        "<item><guid>duplicate</guid>"
        "<link>https://example.com/duplicate</link>"
        "<title>RSS title</title></item>"
    )
    event = _make_event(
        raw_xml=f"<rss><channel>{item}{item}</channel></rss>"
    )
    service = SourceProcessorService(db_session)
    with (
        patch(
            "src.adapters.content_extractor.extract_article",
            return_value=extracted,
        ) as extract,
        patch(
            "src.services.source_processor.post_publisher.publish_post_parsed_success"
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


def test_feed_summary_counts_attempts_reuse_and_partial_results(
    db_session: Session, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO)
    complete = (
        "<item><guid>complete</guid>"
        "<link>https://example.com/complete?secret=value</link>"
        "<title>Complete</title></item>"
    )
    partial = (
        "<item><guid>partial</guid>"
        "<link>https://example.com/partial</link>"
        "<title>RSS title</title></item>"
    )
    event = _make_event(
        raw_xml=f"<rss><channel>{complete}{partial}{partial}</channel></rss>"
    )
    event["event_id"] = "event-1"
    event["occurred_at"] = "2026-01-01T00:00:00"
    with (
        patch(
            "src.adapters.content_extractor.extract_article",
            side_effect=[
                {"content": "Body"},
                {"error": "ArticleException"},
            ],
        ),
        patch(
            "src.services.source_processor.post_publisher.publish_post_parsed_success"
        ) as publish,
    ):
        SourceProcessorService(db_session).process(MagicMock(), event)

    assert publish.call_count == 3
    assert publish.call_args.kwargs["title"] == "RSS title"
    assert publish.call_args.kwargs["content"] is None
    summaries = [
        record.getMessage()
        for record in caplog.records
        if record.getMessage().startswith("Feed processing")
    ]
    assert len(summaries) == 1
    assert "event_id=event-1" in summaries[0]
    assert "source_id=s1" in summaries[0]
    assert "correlation_id=test-corr-id" in summaries[0]
    assert "completed=True" in summaries[0]
    assert "age_seconds=None" not in summaries[0]
    assert "entries=3, attempted=2, reused=1, partial=2" in summaries[0]
    assert "duration_seconds=" in summaries[0]
    assert "secret" not in caplog.text


def test_trimmed_link_is_stored_and_reused(
    db_session: Session,
) -> None:
    entry = {
        "id": "trimmed",
        "link": "  https://example.com/article?one=1&two=2  ",
        "title": "RSS title",
    }
    feed = MagicMock(entries=[entry], feed={})
    with (
        patch(
            "src.services.source_processor.feedparser.parse",
            return_value=feed,
        ),
        patch(
            "src.adapters.content_extractor.extract_article",
            return_value={"content": "Body"},
        ) as extract,
        patch(
            "src.services.source_processor.post_publisher.publish_post_parsed_success"
        ) as publish,
    ):
        service = SourceProcessorService(db_session)
        service.process(MagicMock(), _make_event())
        service.process(MagicMock(), _make_event())

    extract.assert_called_once_with(
        "https://example.com/article?one=1&two=2"
    )
    assert (
        publish.call_args.kwargs["url"]
        == "https://example.com/article?one=1&two=2"
    )


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
            "src.services.source_processor.feedparser.parse",
            return_value=feed,
        ),
        patch(
            "src.adapters.content_extractor.extract_article"
        ) as extract,
        patch(
            "src.services.source_processor.post_publisher.publish_post_parsed_success"
        ) as publish,
    ):
        SourceProcessorService(db_session).process(
            MagicMock(), _make_event()
        )

    extract.assert_not_called()
    assert publish.call_args.kwargs["title"] == "RSS title"
    assert publish.call_args.kwargs["url"] == ""


@pytest.mark.parametrize(
    "event",
    [
        [],
        {},
        {"event_type": "post.parsed.v1"},
        {"event_type": "feed.raw_fetched.v1", "payload": []},
        {
            "event_type": "feed.raw_fetched.v1",
            "payload": {"raw_xml": None},
        },
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
        SourceProcessorService(db).process(MagicMock(), event)
    db.query.assert_not_called()


@pytest.mark.parametrize(
    "xml", ["not XML", "<html>Page</html>", "<rss><channel>"]
)
def test_unusable_feed_is_rejected(xml: str) -> None:
    with pytest.raises(ValueError, match="usable RSS/Atom"):
        SourceProcessorService(MagicMock()).process(
            MagicMock(), _make_event(raw_xml=xml)
        )


def test_empty_valid_feed_completes_and_services_io(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO)
    progress = MagicMock()
    SourceProcessorService(MagicMock()).process(
        MagicMock(), _make_event(), on_progress=progress
    )
    progress.assert_called_once()
    assert "completed=True" in caplog.text
    assert "entries=0, attempted=0, reused=0, partial=0" in caplog.text


def test_missing_saved_post_id_is_not_silently_skipped() -> None:
    service = SourceProcessorService(MagicMock())
    service._repo = MagicMock()
    service._repo.get_by_guids.return_value = []
    service._repo.save.return_value = None
    with (
        patch(
            "src.services.source_processor.post_publisher.publish_post_parsed_success"
        ) as publish,
        pytest.raises(RuntimeError, match="Post save returned no ID"),
    ):
        service.process(
            MagicMock(),
            _make_event(
                raw_xml='<rss version="2.0"><channel><item><guid>item</guid></item></channel></rss>'
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
            "src.services.source_processor.post_publisher.publish_post_parsed_success"
        ) as publish,
    ):
        publish.side_effect = [None, RuntimeError("Publish failed")]
        with pytest.raises(RuntimeError, match="Publish failed"):
            SourceProcessorService(db_session).process(
                MagicMock(), event, on_progress=progress
            )
        assert extract.call_count == 2
        original_ids = [
            call.kwargs["post_id"] for call in publish.call_args_list
        ]
        extract.reset_mock()
        publish.reset_mock()
        publish.side_effect = None
        progress.reset_mock()

        SourceProcessorService(db_session).process(
            MagicMock(), event, on_progress=progress
        )

    extract.assert_not_called()
    assert [
        call.kwargs["post_id"] for call in publish.call_args_list
    ] == original_ids
    assert progress.call_count == 3
    assert db_session.query(Post).count() == 2


def test_malformed_feed_with_usable_entries_still_processes(
    db_session: Session,
) -> None:
    with (
        patch(
            "src.adapters.content_extractor.extract_article",
            return_value={"error": "Blocked"},
        ),
        patch(
            "src.services.source_processor.post_publisher.publish_post_parsed_success"
        ) as publish,
    ):
        SourceProcessorService(db_session).process(
            MagicMock(),
            _make_event(
                raw_xml="<rss><channel><item><guid>usable</guid><title>RSS title</title></item>"
            ),
        )
    assert publish.call_args.kwargs["title"] == "RSS title"
