from fastapi.testclient import TestClient
from unittest.mock import patch
from main import app

client = TestClient(app)


def test_home_returns_200():
    response = client.get("/")
    assert response.status_code == 200


@patch("routes.call_model")
def test_chat_returns_model_reply(mock_call_model):
    mock_call_model.return_value = "Hello from mocked model"

    payload = {
        "message": "Hi",
        "history": [{"role": "user", "content": "previous"}],
        "session_id": "1234"
    }

    response = client.post("/chat", json=payload)

    assert response.status_code == 200
    assert response.json() == {"reply": "Hello from mocked model"}
    mock_call_model.assert_called_once_with("Hi", [{"role": "user", "content": "previous"}])


def test_chat_requires_message():
    payload = {
        "history": [{"role": "user", "content": "previous"}]
    }

    response = client.post("/chat", json=payload)

    assert response.status_code == 422


@patch("routes.call_model")
def test_chat_uses_default_empty_history(mock_call_model):
    mock_call_model.return_value = "ok"

    payload = {
        "message": "Hi",
        "session_id": "12345"
    }

    response = client.post("/chat", json=payload)

    assert response.status_code == 200
    assert response.json() == {"reply": "ok"}
    mock_call_model.assert_called_once_with("Hi", [])