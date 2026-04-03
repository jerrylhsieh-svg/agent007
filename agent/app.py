from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, Request
from pydantic import BaseModel

from services.call_model import call_model


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )

@app.post("/chat")
def chat(req: ChatRequest):
    answer = call_model(req.message, req.history)
    return {"reply": answer}