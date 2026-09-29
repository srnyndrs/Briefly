"""Opt-in checks against the disposable content_check database on port 5433."""

import os
import uuid
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from src.config.database import Base
from src.repositories.post_repository import PostRepository
from src.services.source_processor import SourceProcessorService

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_POSTGRES_INTEGRATION") != "1",
    reason="Requires the disposable PostgreSQL Compose project",
)


def test_committed_upsert_and_feed_replay_reuse_original_post_id() -> (
    None
):
    engine = create_engine(
        "postgresql://content_check:content_check@127.0.0.1:5433/content_check"
    )
    try:
        with engine.begin() as connection:
            assert (
                connection.scalar(text("SELECT current_database()"))
                == "content_check"
            )
            connection.execute(
                text("CREATE SCHEMA IF NOT EXISTS content")
            )
        Base.metadata.create_all(engine)
        source_id = f"integration-{uuid.uuid4()}"
        event = {
            "event_type": "feed.raw_fetched.v1",
            "correlation_id": "postgres-check",
            "payload": {
                "source_id": source_id,
                "source_title": "Source",
                "raw_xml": '<rss version="2.0"><channel><item><guid>item</guid><title>RSS title</title><link>https://example.com/original</link></item></channel></rss>',
            },
        }
        with (
            patch(
                "src.adapters.content_extractor.extract_article",
                return_value={"content": "Body"},
            ) as extract,
            patch(
                "src.services.source_processor.post_publisher.publish_post_parsed_success"
            ) as publish,
        ):
            publish.side_effect = RuntimeError(
                "Publication failed after commit"
            )
            with Session(engine) as db, pytest.raises(RuntimeError):
                SourceProcessorService(db).process(MagicMock(), event)
            with Session(engine) as db:
                original = PostRepository(db).get_by_guids(
                    source_id, ["item"]
                )[0]
                original_id = original.post_id
                assert original.content == "Body"
            extract.reset_mock()
            publish.side_effect = None
            with Session(engine) as db:
                SourceProcessorService(db).process(MagicMock(), event)
            extract.assert_not_called()
            assert publish.call_args.kwargs["post_id"] == original_id
            event["payload"]["raw_xml"] = (
                event["payload"]["raw_xml"]
                .replace("RSS title", "Updated RSS title")
                .replace("/original", "/changed")
            )
            extract.return_value = {"error": "Blocked"}
            with Session(engine) as db:
                SourceProcessorService(db).process(MagicMock(), event)
            extract.assert_called_once_with(
                "https://example.com/changed"
            )
            with Session(engine) as db:
                post = PostRepository(db).get_by_id(original_id)
                assert post.title == "Updated RSS title"
                assert post.content == "Body"
                assert post.url == "https://example.com/changed"
                assert (
                    len(
                        PostRepository(db).get_by_guids(
                            source_id, ["item"]
                        )
                    )
                    == 1
                )
    finally:
        engine.dispose()
