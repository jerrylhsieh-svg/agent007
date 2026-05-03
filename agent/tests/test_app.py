from io import BytesIO

from fastapi.testclient import TestClient
from unittest.mock import patch
from agent.main import app

client = TestClient(app)


def test_home_returns_200():
    response = client.get("/")
    assert response.status_code == 200


@patch("agent.services.chat.chat_service.call_model")
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


@patch("agent.services.chat.chat_service.call_model")
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

@patch("agent.routes.routes.extract_pdf_service")
def test_pdf_extract_route_returns_ok(mock_extract_pdf_service):
    mock_extract_pdf_service.return_value = {
        "filename": "statement.pdf",
        "page_count": 1,
        "table_count": 0,
        "transaction_count": 2,
        "message": "PDF parsed with layout-based bank statement heuristics.",
        "data": {"pages": [], "tables": [], "transactions": []},
        "saved_to": "/tmp/agent_uploads/statement.pdf.json",
    }

    response = client.post(
        "/pdf/extract",
        files={"file": ("statement.pdf", BytesIO(b"%PDF-1.4 fake"), "application/pdf")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["filename"] == "statement.pdf"
    assert body["transaction_count"] == 2