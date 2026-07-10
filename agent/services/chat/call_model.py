import requests

from agent.services.constants_and_dependencies import MODEL, OLLAMA_HOST

def call_model_history(message: str, history: list[dict] = [], **kwargs) -> str:
    messages = [
        {
            "role": "system",
            "content": "You are a local assistant. Answer clearly and helpfully."
        }
    ]

    for item in history:
        role = item.get("role")
        content = item.get("content", "")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": message})

    return call_model_base(messages)

def call_model_base(message: str|list, **kwargs) -> str:
    r = requests.post(
        f"{OLLAMA_HOST}/api/chat",
        json={
            "model": MODEL,
            "messages": message,
            "stream": False
        },
        timeout=600
    )
    r.raise_for_status()
    data = r.json()
    return data["message"]["content"]