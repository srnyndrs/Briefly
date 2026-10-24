from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4

EnrichmentStatus = Literal["completed", "abstained", "failed"]


@dataclass(frozen=True, slots=True)
class StoredEnrichment:
    post_id: UUID
    category_ids: tuple[str, ...]
    status: EnrichmentStatus
    reason: str | None
    processed_at: datetime
    post_revision: int = 1
    enrichment_revision: int = 1
    event_id: str = field(default_factory=lambda: str(uuid4()))
    publication_pending: bool = True
