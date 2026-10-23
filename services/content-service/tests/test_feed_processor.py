from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest
from sqlalchemy.orm import Session

from src.models.post import Post
from src.repositories.post_repository import PostRepository
from src.services.feed_processor import (
    FeedProcessor,
    _entry_guid,
)


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


def test_process_source_rejects_missing_source_identity() -> None:
    event = _make_event()
    event["payload"].pop("source_id")

    repo = MagicMock(spec=PostRepository)
    with pytest.raises(ValueError, match="source_id"):
        FeedProcessor(repo).process(MagicMock(), event)
    repo.get_by_guids.assert_not_called()
    repo.upsert_post.assert_not_called()


@pytest.mark.parametrize(
    ("identity", "link"),
    [
        (
            "https://example.com/posts/42#section",
            "https://example.com/posts/42",
        ),
        ("https://example.com/posts/42#0", "https://example.com/posts/other"),
    ],
)
def test_entry_guid_preserves_unrecognized_identity(
    identity: str, link: str | None
) -> None:
    assert _entry_guid({"guid": identity, "link": link}) == identity


def test_process_source_rejects_missing_entry_identity() -> None:
    repo = MagicMock(spec=PostRepository)
    with pytest.raises(ValueError, match="item_guid"):
        FeedProcessor(repo).process(
            MagicMock(),
            _make_event(raw_xml="<rss><channel><item/></channel></rss>"),
        )
    repo.get_by_guids.assert_not_called()
    repo.upsert_post.assert_not_called()


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
        assert [c.kwargs["post_revision"] for c in publish.call_args_list] == [
            1,
            1,
        ]
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
    post = db_session.query(Post).one()
    assert post.title == "RSS title"
    assert post.content is None


def test_unusable_feed_is_rejected() -> None:
    repo = MagicMock(spec=PostRepository)
    with pytest.raises(ValueError, match="usable RSS/Atom"):
        FeedProcessor(repo).process(
            MagicMock(), _make_event(raw_xml="<html>Page</html>")
        )
    repo.get_by_guids.assert_not_called()
    repo.upsert_post.assert_not_called()


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
    progress.assert_called()
    db_session.expire_all()
    posts = db_session.query(Post).order_by(Post.item_guid).all()
    assert [post.post_revision for post in posts] == [1, 1]


def test_rss_metadata_wins_and_description_becomes_plain_text(
    db_session: Session,
) -> None:
    event = _make_event(
        source_title=" Registered Source ",
        raw_xml="""<rss version="2.0"><channel>
      <title>Feed publisher</title><language>hu-HU</language><item>
      <guid>rss-item</guid><link>https://example.com/rss-item</link>
      <title>Feed title</title><description>&lt;p&gt;Short summary.&lt;/p&gt;&lt;p&gt;More text.&lt;/p&gt;</description>
      <author>Feed author</author><category>News</category>
      <pubDate>Sat, 12 Sep 2026 17:30:35 GMT</pubDate>
      <enclosure url="https://example.com/feed.jpg" type="image/jpeg"/>
      </item></channel></rss>""",
    )
    with (
        patch(
            "src.adapters.content_extractor.extract_article",
            return_value={
                "title": "Extracted title",
                "description": "Extracted description",
                "authors": ["Extracted author"],
                "language": "en",
                "content": "Extracted body",
                "keywords": ["keyword"],
                "image": "https://example.com/extracted.jpg",
                "publish_date": datetime(2026, 9, 1, tzinfo=timezone.utc),
            },
        ),
        patch(
            "src.services.feed_processor.post_publisher.publish_post_parsed_success"
        ) as publish,
    ):
        FeedProcessor(PostRepository(db_session)).process(MagicMock(), event)
    post = db_session.query(Post).one()
    assert post.title == "Feed title"
    assert post.description == "Short summary.\nMore text."
    assert post.author == "Feed author"
    assert post.category == "News"
    assert post.language == "hu"
    assert post.image_url == "https://example.com/feed.jpg"
    assert post.published_at == datetime(2026, 9, 12, 17, 30, 35)
    assert post.source_title == "Registered Source"
    snapshot = publish.call_args.kwargs
    assert snapshot["post_id"] == str(post.post_id)
    assert snapshot["title"] == post.title
    assert snapshot["description"] == post.description
    assert snapshot["source_title"] == post.source_title
    assert snapshot["content"] == post.content == "Extracted body"
    assert snapshot["keywords"] == post.keywords == ["keyword"]


def test_atom_uses_extracted_fallbacks(db_session: Session) -> None:
    event = _make_event(
        raw_xml="""<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="invalid-language">
      <title>Publisher</title><entry><id>atom-item</id>
      <link href="https://example.com/atom-item"/><title> </title>
      </entry></feed>"""
    )
    with (
        patch(
            "src.adapters.content_extractor.extract_article",
            return_value={
                "title": " Extracted title ",
                "description": " Extracted description ",
                "authors": [" Extracted author "],
                "language": " en ",
                "content": "Body",
                "image": " https://example.com/image.jpg ",
            },
        ),
        patch(
            "src.services.feed_processor.post_publisher.publish_post_parsed_success"
        ) as publish,
    ):
        FeedProcessor(PostRepository(db_session)).process(MagicMock(), event)
    post = db_session.query(Post).one()
    assert post.item_guid == "atom-item"
    assert post.title == "Extracted title"
    assert post.description == "Extracted description"
    assert post.author == "Extracted author"
    assert post.language == "en"
    assert post.image_url == "https://example.com/image.jpg"
    assert publish.call_args.kwargs["post_id"] == str(post.post_id)
    assert publish.call_args.kwargs["content"] == post.content == "Body"


def test_empty_valid_feed_completes_without_writes_or_publication() -> None:
    repo = MagicMock(spec=PostRepository)
    with patch(
        "src.services.feed_processor.post_publisher.publish_post_parsed_success"
    ) as publish:
        FeedProcessor(repo).process(MagicMock(), _make_event())
    repo.upsert_post.assert_not_called()
    publish.assert_not_called()
