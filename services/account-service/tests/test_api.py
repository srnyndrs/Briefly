from unittest.mock import Mock
from uuid import uuid4

import pika
from authlib.jose import jwt

from src.app import app
from src.config.settings import settings
from src.routers.deps import get_event_publisher


def test_health(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "account-service",
    }


def test_account_display_name(client, account) -> None:
    path = f"/users/{account['user_id']}"
    response = client.get(path)
    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == account["user_id"]
    assert body["email"] == account["email"]
    assert "password_hash" not in body
    assert body["display_name"] is None
    assert body["created_at"].endswith("+00:00")

    updated = client.patch(path, json={"display_name": "  Reader  "})
    assert updated.status_code == 200
    assert updated.json()["display_name"] == "Reader"
    assert client.get(path).json()["display_name"] == "Reader"
    assert client.patch(path, json={}).json()["display_name"] == "Reader"

    assert client.patch(path, json={"display_name": "   "}).status_code == 422
    assert client.get(path).json()["display_name"] == "Reader"

    cleared = client.patch(path, json={"display_name": None})
    assert cleared.status_code == 200
    assert cleared.json()["display_name"] is None
    assert client.get(path).json()["display_name"] is None


def test_preferences_replacement_patch_and_events(
    client, account, publisher
) -> None:
    path = f"/users/{account['user_id']}/preferences"
    empty = {
        "muted_keywords": [],
        "muted_categories": [],
        "blocked_source_ids": [],
        "languages": [],
    }
    defaults = client.get(path)
    assert defaults.status_code == 200
    assert {key: defaults.json()[key] for key in empty} == empty
    assert publisher.events == []

    values = {
        "muted_keywords": ["example"],
        "muted_categories": ["technology"],
        "blocked_source_ids": [str(uuid4())],
        "languages": ["en"],
    }
    replaced = client.put(path, json=values)
    assert replaced.status_code == 200
    assert {key: replaced.json()[key] for key in values} == values
    assert client.get(path).json() == replaced.json()

    patched = client.patch(
        path,
        json={"muted_keywords": None, "languages": ["hu"]},
        headers={"X-Correlation-ID": "request-1"},
    )
    assert patched.status_code == 200
    body = patched.json()
    assert {key: body[key] for key in values} == {
        **values,
        "muted_keywords": [],
        "languages": ["hu"],
    }
    assert body["updated_at"].endswith("+00:00")
    assert client.get(path).json() == body
    assert len(publisher.events) == 2
    event = publisher.events[-1]
    assert event["event_type"] == "preferences.updated.v1"
    assert event["partition_key"] == f"user:{account['user_id']}"
    assert event["correlation_id"] == "request-1"
    assert event["payload"] == {
        **body,
        "updated_at": body["updated_at"],
    }

    reset = client.put(path, json={"languages": ["en"]})
    assert reset.status_code == 200
    assert {key: reset.json()[key] for key in empty} == {
        **empty,
        "languages": ["en"],
    }
    assert client.get(path).json() == reset.json()
    assert len(publisher.events) == 3
    assert publisher.events[-1]["payload"] == {
        **reset.json(),
        "updated_at": reset.json()["updated_at"],
    }


def test_subscription_lifecycle(client, account, publisher) -> None:
    path = f"/users/{account['user_id']}/subscriptions"
    source = {"source_id": str(uuid4())}
    assert client.get(path).json() == []

    created = client.post(path, json=source)
    assert created.status_code == 201
    body = created.json()
    assert body["user_id"] == account["user_id"]
    assert body["source_id"] == source["source_id"]
    assert body["created_at"].endswith("+00:00")
    assert client.post(path, json=source).status_code == 409
    assert client.get(path).json() == [body]

    second = client.post(
        "/auth/register",
        json={
            "email": "second@example.com",
            "password": "test-password",
        },
    )
    assert second.status_code == 201
    claims = jwt.decode(second.json()["access_token"], settings.jwt_secret)
    claims.validate()
    second_path = f"/users/{claims['sub']}/subscriptions"
    second_subscription = client.post(second_path, json=source)
    assert second_subscription.status_code == 201

    subscription_path = f"{path}/{source['source_id']}"
    assert client.delete(subscription_path).status_code == 204
    assert client.get(path).json() == []
    assert client.get(second_path).json() == [second_subscription.json()]
    assert publisher.events == []


def test_unknown_account(client) -> None:
    response = client.get(f"/users/{uuid4()}")
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}


def test_preferences_remain_saved_when_publication_fails(
    client, account, monkeypatch
) -> None:
    app.dependency_overrides.pop(get_event_publisher, None)
    monkeypatch.setattr(
        "src.routers.deps.publisher_channel",
        Mock(side_effect=pika.exceptions.AMQPConnectionError("Broker unavailable")),
    )
    path = f"/users/{account['user_id']}/preferences"
    response = client.put(path, json={"languages": ["en"]})
    assert response.status_code == 200
    assert response.json()["languages"] == ["en"]
    assert client.get(path).json()["languages"] == ["en"]
