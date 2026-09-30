import json
from pathlib import Path
from typing import Any

from src.config.database import SessionLocal, init_db
from src.models.source import Source

SOURCES_FILE = Path(__file__).with_name("sources.json")
SOURCE_FIELDS = {
    "url",
    "title",
    "description",
    "favicon",
    "website_url",
}


def load_sources(path: Path = SOURCES_FILE) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as source_file:
        sources = json.load(source_file)

    if not isinstance(sources, list):
        raise ValueError("The source seed file must contain a JSON list.")

    seen_urls: set[str] = set()
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            raise ValueError(f"Source at index {index} must be a JSON object.")
        for field in ("url", "title"):
            if (
                not isinstance(source.get(field), str)
                or not source[field].strip()
            ):
                raise ValueError(
                    f"Source at index {index} must have a non-empty '{field}'."
                )
        if source["url"] in seen_urls:
            raise ValueError(f"Duplicate source URL: {source['url']}")
        seen_urls.add(source["url"])

    return sources


def seed_sources(path: Path = SOURCES_FILE) -> tuple[int, int]:
    sources = load_sources(path)
    init_db()

    with SessionLocal() as session:
        urls = [source["url"] for source in sources]
        existing_urls = (
            {
                url
                for (url,) in session.query(Source.url)
                .filter(Source.url.in_(urls))
                .all()
            }
            if urls
            else set()
        )
        missing_sources = []
        for source in sources:
            if source["url"] in existing_urls:
                continue
            missing_sources.append(_build_source(source))

        session.add_all(missing_sources)
        session.commit()
        return len(missing_sources), len(existing_urls)


def _build_source(source: dict[str, Any]) -> Source:
    seed_data = {
        key: value for key, value in source.items() if key in SOURCE_FIELDS
    }
    seed_data["verified"] = True
    seed_data["submitted_by_user_id"] = None
    return Source(**seed_data)


def main() -> None:
    added, already_present = seed_sources()
    print(
        f"Source seed complete: {added} added, "
        f"{already_present} already present."
    )


if __name__ == "__main__":
    main()
