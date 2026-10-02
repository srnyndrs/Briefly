"""Persist classifier results and reuse successful unchanged enrichments."""

import hashlib
import json
from datetime import UTC, datetime
from uuid import UUID

from src.repositories.enrichment_repository import (
    EnrichmentRepository,
    EnrichmentStatus,
    StoredEnrichment,
)
from src.services.classification import (
    ArticleInput,
    Classifier,
    classify_article,
    normalize_article,
)

DEFAULT_ENRICHMENT_VERSION = "classification-v1"


class EnrichmentService:
    """Classify and persist one post without holding a database transaction."""

    def __init__(
        self,
        repository: EnrichmentRepository,
        classifier: Classifier,
        enrichment_version: str = DEFAULT_ENRICHMENT_VERSION,
    ) -> None:
        if not enrichment_version or len(enrichment_version) > 100:
            raise ValueError(
                "Enrichment version must contain 1 to 100 characters"
            )
        self._repository = repository
        self._classifier = classifier
        self._enrichment_version = enrichment_version

    def enrich_article(
        self,
        post_id: UUID,
        article: ArticleInput,
    ) -> StoredEnrichment:
        normalized = normalize_article(article)
        input_hash = _hash_classifier_input(normalized)
        existing = self._repository.get_by_post_id(post_id)
        if (
            existing is not None
            and existing.input_hash == input_hash
            and existing.enrichment_version == self._enrichment_version
            and existing.status in ("completed", "abstained")
        ):
            return existing

        try:
            result = classify_article(normalized, self._classifier)
        except Exception:
            self._repository.save(
                self._result(
                    post_id=post_id,
                    input_hash=input_hash,
                    category_id=None,
                    status="failed",
                    reason="classifier_error",
                )
            )
            raise

        if result.category_id is None:
            reason = (
                "no_usable_text"
                if not any(
                    (normalized.title, normalized.description, normalized.body)
                )
                else "classifier_abstained"
            )
            status: EnrichmentStatus = "abstained"
        else:
            reason = None
            status = "completed"

        enrichment = self._result(
            post_id=post_id,
            input_hash=input_hash,
            category_id=result.category_id,
            status=status,
            reason=reason,
        )
        self._repository.save(enrichment)
        return enrichment

    def _result(
        self,
        *,
        post_id: UUID,
        input_hash: str,
        category_id: str | None,
        status: EnrichmentStatus,
        reason: str | None,
    ) -> StoredEnrichment:
        return StoredEnrichment(
            post_id=post_id,
            input_hash=input_hash,
            enrichment_version=self._enrichment_version,
            category_id=category_id,
            status=status,
            reason=reason,
            processed_at=datetime.now(UTC),
        )


def _hash_classifier_input(article: ArticleInput) -> str:
    payload = json.dumps(
        {
            "title": article.title,
            "description": article.description,
            "body": article.body,
            "language": article.language,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
