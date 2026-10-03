import argparse
import json

from src.adapters.source_discovery import SourceDiscoveryAdapter


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check a URL using the crawler's source discovery logic."
    )
    parser.add_argument("url", help="Website or potential RSS/Atom feed URL")
    args = parser.parse_args()
    if not args.url.strip():
        parser.error("URL must not be empty")

    results = SourceDiscoveryAdapter().discover(args.url)
    print(
        json.dumps(
            [result.model_dump(mode="json") for result in results], indent=2
        )
    )


if __name__ == "__main__":
    main()
