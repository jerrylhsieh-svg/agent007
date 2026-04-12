from __future__ import annotations

from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import HTMLResponse

from agent.services.file_flow import handle_file_flow
from agent.services.call_model import call_model
from agent.models.chat import ChatRequest, ChatResponse, TransactionAnalysisRequest
from agent.services.pdf_extractor import extract_pdf_service
from agent.services.transaction_analysis import analyze_transactions_question



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
    result = handle_file_flow(req.session_id, req.message)
    if result["handled"]:
        return {"reply": result["reply"]}
    answer = call_model(req.message, req.history)
    return {"reply": answer}


@router.post("/pdf/extract")
async def extract_pdf(file: UploadFile = File(...)):
    result =  await extract_pdf_service(file)
    return {
        "ok": True,
        **result,
    }

@router.post("/transactions/analyze")
async def analyze_transactions(req: TransactionAnalysisRequest):
    answer = analyze_transactions_question(req.question, req.history)
    return {"reply": answer}