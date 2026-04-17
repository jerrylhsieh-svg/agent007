from unittest.mock import Mock, patch
from agent.services.call_model import call_model


@patch("agent.services.call_model.requests.post")
def test_call_model_builds_expected_payload(mock_post):
    mock_response = Mock()
    mock_response.json.return_value = {
        "message": {"content": "Test reply"}
    }
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    history = [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi there"},
    ]

    result = call_model("how are you?", history)

    assert result == "Test reply"

    _, kwargs = mock_post.call_args
    assert kwargs["json"]["stream"] is False
    assert kwargs["json"]["messages"] == [
        {
            "role": "system",
            "content": "You are a local assistant. Answer clearly and helpfully."
        },
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi there"},
        {"role": "user", "content": "how are you?"},
    ]


@patch("agent.services.call_model.requests.post")
def test_call_model_filters_invalid_history_items(mock_post):
    mock_response = Mock()
    mock_response.json.return_value = {
        "message": {"content": "Filtered reply"}
    }
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    history = [
        {"role": "system", "content": "ignore this"},
        {"role": "tool", "content": "ignore this too"},
        {"role": "user", "content": ""},
        {"role": "assistant", "content": "kept"},
        {"role": "user", "content": "also kept"},
    ]

    call_model("latest question", history)

    _, kwargs = mock_post.call_args
    assert kwargs["json"]["messages"] == [
        {
            "role": "system",
            "content": "You are a local assistant. Answer clearly and helpfully."
        },
        {"role": "assistant", "content": "kept"},
        {"role": "user", "content": "also kept"},
        {"role": "user", "content": "latest question"},
    ]


@patch("agent.services.call_model.requests.post")
def test_call_model_raises_on_http_error(mock_post):
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = Exception("boom")
    mock_post.return_value = mock_response

    try:
        call_model("hi", [])
        assert False, "Expected exception was not raised"
    except Exception as e:
        assert str(e) == "boom"