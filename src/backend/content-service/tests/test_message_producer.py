import json
from unittest.mock import MagicMock

from src.services import event_publisher


def _extract_publish_args(channel: MagicMock) -> tuple[str, bytes]:
    kwargs = channel.basic_publish.call_args.kwargs
    return kwargs["routing_key"], kwargs["body"]


def test_publish_article_updated_emits_expected_event() -> None:
    channel = MagicMock()

    event_publisher.publish_article_updated(
        channel,
        article_id="a1",
        source_id="s1",
        changed_fields=["title", "content"],
    )

    routing_key, body = _extract_publish_args(channel)
    envelope = json.loads(body.decode())

    assert routing_key == "article.updated.v1"
    assert envelope["event_type"] == "article.updated.v1"
    assert envelope["payload"]["article_id"] == "a1"
    assert envelope["payload"]["source_id"] == "s1"
    assert envelope["payload"]["changed_fields"] == [
        "title",
        "content",
    ]


def test_publish_parsed_success_emits_content_body() -> None:
    channel = MagicMock()

    event_publisher.publish_parsed_success(
        channel,
        article_id="a1",
        feed_id="s1",
        item_guid="g1",
        url="https://example.com/a1",
        title="Title",
        content="Full body",
        content_length=9,
        description="A short description",
        published_at="2026-05-05T00:00:00+00:00",
    )

    routing_key, body = _extract_publish_args(channel)
    envelope = json.loads(body.decode())

    assert routing_key == "article.parsed.v1"
    assert envelope["payload"]["content"] == "Full body"
    assert envelope["payload"]["content_length"] == 9
    assert envelope["payload"]["description"] == "A short description"


def test_publish_article_content_extracted_emits_expected_event() -> (
    None
):
    channel = MagicMock()

    event_publisher.publish_article_content_extracted(
        channel,
        article_id="a1",
        source_id="s1",
        content_ref="article:a1",
        image_ref="https://img.example/a1.jpg",
    )

    routing_key, body = _extract_publish_args(channel)
    envelope = json.loads(body.decode())

    assert routing_key == "article.content_extracted.v1"
    assert envelope["event_type"] == "article.content_extracted.v1"
    assert envelope["payload"]["content_ref"] == "article:a1"
    assert (
        envelope["payload"]["image_ref"]
        == "https://img.example/a1.jpg"
    )


def test_publish_article_enriched_emits_expected_event() -> None:
    channel = MagicMock()

    event_publisher.publish_article_enriched(
        channel,
        article_id="a1",
        source_id="s1",
        sentiment="unknown",
        topics=[],
        cluster_id=None,
        model_version="content-service-default-v1",
    )

    routing_key, body = _extract_publish_args(channel)
    envelope = json.loads(body.decode())

    assert routing_key == "article.enriched.v1"
    assert envelope["event_type"] == "article.enriched.v1"
    assert envelope["payload"]["article_id"] == "a1"
    assert envelope["payload"]["source_id"] == "s1"
    assert envelope["payload"]["sentiment"] == "unknown"
    assert envelope["payload"]["topics"] == []
    assert envelope["payload"]["cluster_id"] is None
    assert (
        envelope["payload"]["model_version"]
        == "content-service-default-v1"
    )
