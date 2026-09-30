import json
from unittest.mock import MagicMock

from src.adapters import post_publisher


def _extract_publish_args(channel: MagicMock) -> tuple[str, bytes]:
    kwargs = channel.basic_publish.call_args.kwargs
    return kwargs["routing_key"], kwargs["body"]


def test_publish_post_parsed_success_emits_content_body() -> None:
    channel = MagicMock()

    post_publisher.publish_post_parsed_success(
        channel,
        post_id="a1",
        source_id="s1",
        item_guid="g1",
        url="https://example.com/a1",
        title="Title",
        source_title="Test Source",
        correlation_id="corr-123",
        content="Full body",
        description="A short description",
        published_at="2026-05-05T00:00:00+00:00",
        author="Example Author",
        image_url="https://example.com/images/a1.png",
    )

    routing_key, body = _extract_publish_args(channel)
    assert channel.basic_publish.call_args.kwargs["mandatory"] is True
    envelope = json.loads(body.decode())

    assert routing_key == "post.parsed.v1"
    assert envelope["correlation_id"] == "corr-123"
    assert envelope["payload"]["content"] == "Full body"
    assert envelope["payload"]["content_length"] == 9
    assert envelope["payload"]["description"] == "A short description"
    assert envelope["payload"]["author"] == "Example Author"
    assert (
        envelope["payload"]["image_url"]
        == "https://example.com/images/a1.png"
    )


def test_publish_post_parsed_success_includes_complete_snapshot() -> (
    None
):
    channel = MagicMock()

    post_publisher.publish_post_parsed_success(
        channel,
        post_id="a1",
        source_id="s1",
        item_guid="g1",
        url="https://example.com/a1",
        title="Title",
        source_title="Test Source",
        correlation_id="corr-123",
        content=None,
    )

    _, body = _extract_publish_args(channel)
    payload = json.loads(body.decode())["payload"]
    assert payload["content_length"] == 0
    assert payload["author"] is None
    assert payload["category"] is None
    assert payload["description"] is None
    assert payload["image_url"] is None
    assert payload["language"] is None
    assert payload["published_at"] is None
    assert payload["keywords"] == []
