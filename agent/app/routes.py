from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.services.file_flow import handle_file_flow
from app.services.save_file import try_handle_file_create
from app.services.call_model import call_model
from app.models import ChatRequest, ChatResponse


router = APIRouter()


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