import os
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import requests
from fastapi import FastAPI
from pydantic import BaseModel

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODEL = os.getenv("MODEL", "qwen2.5:1.5b")

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class ChatRequest(BaseModel):
    message: str

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

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/chat")
def chat(req: ChatRequest):
    system_prompt = (
        "You are a local assistant. "
        "Answer clearly. If you need tools, say so."
    )
    full_prompt = f"{system_prompt}\n\nUser: {req.message}\nAssistant:"
    answer = call_model(full_prompt)
    return {"reply": answer}