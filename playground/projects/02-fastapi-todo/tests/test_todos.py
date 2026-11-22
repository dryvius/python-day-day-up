import json
import logging

import pytest
from conftest import TEST_API_KEY
from fastapi.testclient import TestClient

AUTH_HEADERS = {"X-API-Key": TEST_API_KEY}


def test_health_does_not_require_authentication(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_request_id_is_returned_and_logged(
    client: TestClient,
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.INFO, logger="todo_api.main"):
        response = client.get("/health", headers={"X-Request-ID": "request-test-123"})

    assert response.headers["X-Request-ID"] == "request-test-123"
    records = [
        json.loads(record.message)
        for record in caplog.records
        if record.name == "todo_api.main"
    ]
    assert records == [
        {
            "event": "http_request_completed",
            "latency_ms": records[0]["latency_ms"],
            "method": "GET",
            "path": "/health",
            "request_id": "request-test-123",
            "status_code": 200,
        }
    ]


def test_todo_end_to_end_crud(client: TestClient) -> None:
    create_response = client.post(
        "/v1/todos",
        headers=AUTH_HEADERS,
        json={"title": "Ship reference implementation"},
    )
    assert create_response.status_code == 201
    todo = create_response.json()
    assert todo["done"] is False

    todo_id = todo["id"]
    assert client.get(f"/v1/todos/{todo_id}", headers=AUTH_HEADERS).json()["title"] == todo["title"]

    update_response = client.patch(
        f"/v1/todos/{todo_id}",
        headers=AUTH_HEADERS,
        json={"done": True},
    )
    assert update_response.status_code == 200
    assert update_response.json()["done"] is True

    list_response = client.get("/v1/todos?done=true", headers=AUTH_HEADERS)
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [todo_id]

    delete_response = client.delete(f"/v1/todos/{todo_id}", headers=AUTH_HEADERS)
    assert delete_response.status_code == 204
    assert client.get(f"/v1/todos/{todo_id}", headers=AUTH_HEADERS).status_code == 404


def test_missing_or_wrong_api_key_returns_401(client: TestClient) -> None:
    assert client.get("/v1/todos").status_code == 401
    assert client.get("/v1/todos", headers={"X-API-Key": "wrong-key"}).status_code == 401


def test_missing_todo_returns_404(client: TestClient) -> None:
    response = client.get("/v1/todos/999", headers=AUTH_HEADERS)

    assert response.status_code == 404


def test_invalid_payload_returns_422(client: TestClient) -> None:
    missing_title = client.post("/v1/todos", headers=AUTH_HEADERS, json={})
    empty_title = client.post("/v1/todos", headers=AUTH_HEADERS, json={"title": ""})

    assert missing_title.status_code == 422
    assert empty_title.status_code == 422
