import argparse
import logging
from uuid import UUID

from src.config.database import SessionLocal
from src.config.message_broker import create_replay_publisher_channel
from src.services.source_processor import SourceProcessorService


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("post_id", type=UUID, help="Required stored post ID")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    channel = create_replay_publisher_channel()
    try:
        with SessionLocal() as db:
            if not SourceProcessorService(db).reextract_post(
                channel, args.post_id
            ):
                print("No usable content; stored post unchanged.")
                return 1
        print("Post snapshot published after re-extraction.")
        return 0
    finally:
        if channel.connection.is_open:
            channel.connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
