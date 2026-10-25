import argparse
from dataclasses import replace
from uuid import UUID

from src.adapters.event_publisher import publish_event
from src.config.database import SessionLocal
from src.config.message_broker import publisher_channel
from src.config.settings import settings
from src.events.post_enriched import build_enrichment_event
from src.repositories.enrichment_repository import EnrichmentRepository
from src.repositories.stored_enrichment import StoredEnrichment


def republish_result(post_id: UUID) -> None:
    repository = EnrichmentRepository(SessionLocal)
    saved = repository.get_by_post_id(post_id)
    if saved is None:
        raise ValueError("No saved result event for this post")

    publish_saved_result(saved, repository)


def publish_saved_result(
    saved: StoredEnrichment, repository: EnrichmentRepository
) -> StoredEnrichment:
    with publisher_channel(exchange=settings.result_exchange) as channel:
        publish_event(
            channel,
            exchange=settings.result_exchange,
            envelope=build_enrichment_event(saved),
        )
        repository.mark_published(saved.post_id, saved.event_id)

        return replace(saved, publication_pending=False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("post_id", type=UUID)
    args = parser.parse_args()
    republish_result(args.post_id)

    print("Saved result event published.")


if __name__ == "__main__":
    main()
