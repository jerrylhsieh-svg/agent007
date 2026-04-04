from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User input message")
    history: list[dict] = []
    session_id: str


class ChatResponse(BaseModel):
    reply: str
