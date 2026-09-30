"""Supported enrichment categories and their short definitions."""

CATEGORY_TAXONOMY_VERSION = "categories-v2"

CATEGORY_DEFINITIONS: dict[str, str] = {
    "politics": "Government, ministries, state agencies, public administration, public policy, elections, legislation, diplomacy, official audits, and political/governmental activity.",
    "world": "International affairs, armed conflicts, international diplomacy, major global events, and disasters outside domestic scope.",
    "business": "Private companies, corporate performance, earnings, startups, executive changes, and commercial mergers/acquisitions.",
    "economy": "Macroeconomic trends, inflation, GDP, employment, trade, central bank monetary policy, and interest rates.",
    "finance": "Financial markets, banking, stock exchanges, investing, currencies/exchange rates, personal finance, and crypto.",
    "technology": "Software, artificial intelligence, cybersecurity, consumer electronics, and computing technology.",
    "science": "Scientific research, empirical discoveries, space exploration, physics, biology, and academic studies.",
    "health": "Medicine, healthcare systems, diseases, treatments, clinical trials, pharmaceuticals, and public health.",
    "environment": "Climate change, conservation, environmental protection, pollution, and the natural world.",
    "sports": "Athletic competitions, matches, teams, athletes, and tournaments.",
    "entertainment": "Film, television, music, pop culture, celebrities, gaming, and arts/performances.",
    "lifestyle": "Travel, gastronomy, fashion, personal relationships, wellness, and hobbies.",
    "society": "Social issues, human rights, communities, education, crime, demographics, and public life.",
    "automotive": "Motor vehicles, electric mobility, vehicle technology, and the automotive industry.",
    "other": "A meaningful, distinct topic strictly outside all named categories.",
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
