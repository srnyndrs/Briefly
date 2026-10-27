import argparse
import logging
from uuid import UUID

from src.config.database import SessionLocal
from src.config.message_broker import publisher_channel
from src.config.settings import settings
from src.repositories.post_repository import PostRepository
from src.services.feed_processor import FeedProcessor


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("post_id", type=UUID, help="Required stored post ID")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)

    with publisher_channel(exchange=settings.parsed_exchange) as channel:
        with SessionLocal() as db:
            if not FeedProcessor(PostRepository(db)).reextract_post(
                channel, args.post_id
            ):
                print("No usable content; stored post unchanged.")
                return 1
        print("Post snapshot published after re-extraction.")

        return 0


if __name__ == "__main__":
    raise SystemExit(main())
