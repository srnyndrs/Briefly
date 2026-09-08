from types import SimpleNamespace

from src.adapters.query_projector import QueryProjector
from src.models.read_models import ProcessedEvent


class FakeSession:
    def __init__(self) -> None:
        self.receipts: dict[str, ProcessedEvent] = {}
        self.added: list[ProcessedEvent] = []
        self.commits = 0

    def get(self, model, event_id: str):
        assert model is ProcessedEvent
        return self.receipts.get(event_id)

    def add(self, receipt: ProcessedEvent) -> None:
        self.added.append(receipt)
        self.receipts[receipt.event_id] = receipt

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        raise AssertionError("duplicate delivery should not roll back")

    def close(self) -> None:
        pass


class FakeChannel:
    def __init__(self) -> None:
        self.acknowledged: list[int] = []

    def basic_ack(self, *, delivery_tag: int) -> None:
        self.acknowledged.append(delivery_tag)


def test_duplicate_delivery_projects_once_and_acknowledges_both() -> (
    None
):
    session = FakeSession()
    projector = QueryProjector(lambda: session)
    applied: list[tuple[str, dict]] = []
    projector._apply_event = lambda db, event_type, payload: (
        applied.append((event_type, payload))
    )
    channel = FakeChannel()
    method = SimpleNamespace(delivery_tag=1)
    body = b'{"event_id":"event-1","event_type":"post.parsed.v1","payload":{"post_id":"post-1"}}'

    projector._on_message(channel, method, None, body)
    method.delivery_tag = 2
    projector._on_message(channel, method, None, body)

    assert applied == [("post.parsed.v1", {"post_id": "post-1"})]
    assert len(session.added) == 1
    assert session.commits == 1
    assert channel.acknowledged == [1, 2]
