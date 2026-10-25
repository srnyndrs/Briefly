from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

SUPPORTED_CATEGORIES = frozenset(
    {
        "politics",
        "world",
        "business",
        "economy",
        "finance",
        "technology",
        "science",
        "health",
        "environment",
        "entertainment",
        "lifestyle",
        "automotive",
        "sports",
        "society",
        "other",
    }
)


class EnrichmentPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    post_id: UUID
    post_revision: int = Field(strict=True, ge=1)
    enrichment_revision: int = Field(strict=True, ge=1)
    status: Literal["completed", "abstained", "failed"]
    category_ids: list[str] = Field(strict=True, max_length=2)

    @model_validator(mode="after")
    def validate_categories(self) -> "EnrichmentPayload":
        categories = self.category_ids
        if (
            any(category not in SUPPORTED_CATEGORIES for category in categories)
            or len(set(categories)) != len(categories)
            or ("other" in categories and len(categories) != 1)
            or (self.status == "completed") != bool(categories)
        ):
            raise ValueError("Invalid enrichment category collection or status")
        return self
