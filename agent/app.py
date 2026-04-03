import os
from fastapi.responses import HTMLResponse
import requests
from fastapi import FastAPI
from pydantic import BaseModel

from agent.front_page import front_page

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODEL = "llama3.1"

app = FastAPI()

class ChatRequest(BaseModel):
    message: str

def call_model(prompt: str) -> str:
    r = requests.post(
        f"{OLLAMA_HOST}/api/generate",
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False
        },
        timeout=300
    )
    r.raise_for_status()
    return r.json()["response"]

@app.get("/", response_class=HTMLResponse)
def home():
    return front_page

@app.post("/chat")
def chat(req: ChatRequest):
    system_prompt = (
        "You are a local assistant. "
        "Answer clearly. If you need tools, say so."
    )
    full_prompt = f"{system_prompt}\n\nUser: {req.message}\nAssistant:"
    answer = call_model(full_prompt)
    return {"reply": answer}