import argparse
import json
from urllib.request import urlopen
from uuid import UUID

from src.app import create_enrichment_service
from src.config.database import SessionLocal
from src.events.post_parsed import ParsedPostPayload
from src.repositories.enrichment_repository import EnrichmentRepository
from src.repositories.stored_enrichment import StoredEnrichment
from src.scripts.republish_result import publish_saved_result
from src.services.post_processor import article_from_payload


def reclassify_post(post_id: UUID, content_service_url: str) -> StoredEnrichment:
    url = f"{content_service_url.rstrip('/')}/posts/{post_id}"
    with urlopen(url, timeout=30) as response:
        payload = ParsedPostPayload.model_validate(json.load(response))

    if payload.post_id != post_id:
        raise ValueError("Content-service returned a different post")

    saved = create_enrichment_service().enrich_article(
        post_id,
        article_from_payload(payload),
        post_revision=payload.post_revision,
        force_reclassify=True,
    )

    return publish_saved_result(saved, EnrichmentRepository(SessionLocal))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("post_id", type=UUID)
    parser.add_argument("--content-service-url", required=True)
    args = parser.parse_args()
    saved = reclassify_post(args.post_id, args.content_service_url)
    if saved.status == "failed":
        parser.exit(1, "Classification failed; saved failure published.\n")

    print(f"Result {saved.enrichment_revision} saved and published.")


if __name__ == "__main__":
    main()
