"""Supported enrichment categories and their short definitions."""

CATEGORY_TAXONOMY_VERSION = "categories-v2"

CATEGORY_DEFINITIONS: dict[str, str] = {
    "politics": "Government, elections, legislation, diplomacy, public policy, and political activity.",
    "world": "International affairs, conflicts, disasters, and major global events.",
    "business": "Companies, industries, startups, corporate decisions, mergers, and acquisitions.",
    "economy": "Inflation, employment, interest rates, GDP, trade, and macroeconomic developments.",
    "finance": "Banking, investing, stock markets, personal finance, and cryptocurrencies.",
    "technology": "Software, hardware, artificial intelligence, cybersecurity, and consumer technology.",
    "science": "Scientific research, discoveries, space, physics, biology, and related fields.",
    "health": "Medicine, healthcare, diseases, treatments, nutrition, and public health.",
    "environment": "Climate, conservation, pollution, energy transition, and the natural environment.",
    "sports": "Sports, competitions, teams, athletes, and sporting events.",
    "entertainment": "Movies, television, music, celebrities, gaming, and popular entertainment.",
    "lifestyle": "Travel, food, fashion, relationships, home, and hobbies.",
    "society": "Social issues, communities, education, crime, demographics, and public life.",
    "automotive": "Cars, electric vehicles, automakers, transportation technology, and the automotive industry.",
    "other": "A suitable subject outside the named categories.",
}


def validate_category_ids(value: object) -> tuple[str, ...]:
    """Validate a bounded category collection and return taxonomy order."""
    if not isinstance(value, (list, tuple)) or len(value) > 2:
        raise ValueError("Expected zero to two category IDs")
    if any(
        not isinstance(item, str) or item not in CATEGORY_DEFINITIONS
        for item in value
    ):
        raise ValueError("Unsupported category ID")
    if len(set(value)) != len(value) or ("other" in value and len(value) != 1):
        raise ValueError(
            "Category IDs must be distinct and 'other' must stand alone"
        )
    return tuple(
        category for category in CATEGORY_DEFINITIONS if category in value
    )
