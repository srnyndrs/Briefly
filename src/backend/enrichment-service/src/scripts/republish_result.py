"""Republish one stored enrichment event without classifying again."""

import argparse
from uuid import UUID

import pika

from src.adapters.post_consumer import PostConsumer
from src.adapters.result_publisher import publish_result
from src.config.database import SessionLocal
from src.config.settings import settings
from src.repositories.enrichment_repository import EnrichmentRepository


def republish_result(post_id: UUID) -> None:
    repository = EnrichmentRepository(SessionLocal)
    saved = repository.get_by_post_id(post_id)
    if saved is None or saved.result_event is None or saved.event_id is None:
        raise ValueError("No saved result event for this post")

    parameters = pika.URLParameters(settings.rabbitmq_url)
    parameters.blocked_connection_timeout = settings.blocked_timeout_seconds
    connection = pika.BlockingConnection(parameters)
    try:
        channel = connection.channel()
        PostConsumer._declare_topology(channel)
        channel.confirm_delivery()
        publish_result(channel, saved.result_event)
        repository.mark_published(post_id, saved.event_id)
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
