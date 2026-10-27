import argparse
import json

from pydantic_core import to_jsonable_python

from src.adapters.content_extractor import extract_article


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="Article URL")

    args = parser.parse_args()
    if not args.url.strip():
        parser.error("URL must not be empty.")

    result = extract_article(args.url)

    print(
        json.dumps(
            to_jsonable_python(result),
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
