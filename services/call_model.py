import os
import requests

MODEL = os.getenv("MODEL", "qwen2.5:1.5b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

def call_model(message: str, history: list[dict]) -> str:
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

    r = requests.post(
        f"{OLLAMA_HOST}/api/chat",
        json={
            "model": MODEL,
            "messages": messages,
            "stream": False
        },
        timeout=300
    )
    r.raise_for_status()
    data = r.json()
    return data["message"]["content"]