from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from agent.db.session import get_db_session
from agent.services.chat import chat_service
from agent.db.data_classes.chat import ChatRequest, ChatResponse
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
async def chat(req: ChatRequest, db: Session = Depends(get_db_session)):
    reply = chat_service.get_reply(req, db)
    return ChatResponse(reply=reply)

@router.post("/pdf/extract")
async def extract_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...), db: Session = Depends(get_db_session)):
    result =  await extract_pdf_service(background_tasks, file, db)
    return {
        "ok": True,
        **result,
    }