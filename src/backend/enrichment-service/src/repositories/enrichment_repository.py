from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal, cast
from uuid import UUID

from sqlalchemy.orm import Session, sessionmaker

from src.models.post_enrichment import PostEnrichment

EnrichmentStatus = Literal["completed", "abstained", "failed"]


@dataclass(frozen=True, slots=True)
class StoredEnrichment:
    post_id: UUID
    input_hash: str
    enrichment_version: str
    category_id: str | None
    status: EnrichmentStatus
    reason: str | None
    processed_at: datetime


class EnrichmentRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def get_by_post_id(self, post_id: UUID) -> StoredEnrichment | None:
        with self._session_factory() as session:
            record = session.get(PostEnrichment, post_id)
            if record is None:
                return None
            return self._to_stored(record)

    def save(self, enrichment: StoredEnrichment) -> None:
        with self._session_factory.begin() as session:
            record = session.get(PostEnrichment, enrichment.post_id)
            if record is None:
                record = PostEnrichment(post_id=enrichment.post_id)
                session.add(record)

            record.input_hash = enrichment.input_hash
            record.enrichment_version = enrichment.enrichment_version
            record.category_id = enrichment.category_id
            record.status = enrichment.status
            record.reason = enrichment.reason
            record.processed_at = enrichment.processed_at

    @staticmethod
    def _to_stored(record: PostEnrichment) -> StoredEnrichment:
        processed_at = record.processed_at
        if processed_at.tzinfo is None:
            processed_at = processed_at.replace(tzinfo=UTC)
        return StoredEnrichment(
            post_id=record.post_id,
            input_hash=record.input_hash,
            enrichment_version=record.enrichment_version,
            category_id=record.category_id,
            status=cast(EnrichmentStatus, record.status),
            reason=record.reason,
            processed_at=processed_at,
        )
