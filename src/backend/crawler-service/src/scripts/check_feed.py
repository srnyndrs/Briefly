import argparse
import json
from datetime import datetime
import warnings
from bs4 import XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

from feedsearch_crawler import search_with_info
from src.adapters.source_discovery import SourceDiscoveryAdapter


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check a URL using the crawler's source discovery logic."
    )
    parser.add_argument("url", help="Website or potential RSS/Atom feed URL")
    args = parser.parse_args()
    if not args.url.strip():
        parser.error("URL must not be empty")

    # results = SourceDiscoveryAdapter().discover(args.url)

    # print(
    #     json.dumps(
    #         [result.model_dump(mode="json") for result in results],
    #         indent=2,
    #         ensure_ascii=False,
    #     )
    # )

    result = search_with_info(args.url, try_urls=False, include_stats=False)

    allowed_fields = {
        "url", "title", "description", "language", "favicon",
        "last_updated", "site_url", "site_name",
    }

    feeds_data = [
        {k: v for k, v in feed.serialize().items() if k in allowed_fields}
        for feed in result.feeds
    ]

    print(json.dumps(feeds_data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
