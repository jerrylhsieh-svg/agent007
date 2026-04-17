from __future__ import annotations

from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import HTMLResponse

from agent.services import chat_service
from agent.models.chat import ChatRequest, ChatResponse
from agent.services.pdf_extractor import extract_pdf_service



router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    templates = request.app.state.templates
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    reply = chat_service.get_reply(req)
    return ChatResponse(reply=reply)

@router.post("/pdf/extract")
async def extract_pdf(file: UploadFile = File(...)):
    result =  await extract_pdf_service(file)
    return {
        "ok": True,
        **result,
    }