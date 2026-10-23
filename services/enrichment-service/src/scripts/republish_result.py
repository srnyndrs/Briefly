"""Republish one stored enrichment event without classifying again."""

import argparse
from dataclasses import replace
from uuid import UUID

import pika

from src.adapters.result_publisher import publish_result
from src.config.database import SessionLocal
from src.config.settings import settings
from src.events.post_enriched import build_result_event
from src.repositories.enrichment_repository import (
    EnrichmentRepository,
    StoredEnrichment,
)


def republish_result(post_id: UUID) -> None:
    repository = EnrichmentRepository(SessionLocal)
    saved = repository.get_by_post_id(post_id)
    if saved is None:
        raise ValueError("No saved result event for this post")

    publish_saved_result(saved, repository)


def publish_saved_result(
    saved: StoredEnrichment, repository: EnrichmentRepository
) -> StoredEnrichment:
    """Publish and confirm this exact saved event, then mark its identity."""
    event = build_result_event(saved)
    parameters = pika.URLParameters(settings.rabbitmq_url)
    parameters.blocked_connection_timeout = settings.blocked_timeout_seconds
    connection = pika.BlockingConnection(parameters)
    try:
        channel = connection.channel()
        channel.exchange_declare(
            exchange=settings.result_exchange,
            exchange_type="topic",
            durable=True,
        )
        channel.confirm_delivery()
        publish_result(channel, event)
        repository.mark_published(saved.post_id, saved.event_id)
        return replace(saved, publication_pending=False)
    finally:
        if connection.is_open:
            connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("post_id", type=UUID)
    args = parser.parse_args()
    republish_result(args.post_id)
    print("Saved result event published.")


if __name__ == "__main__":
    main()
