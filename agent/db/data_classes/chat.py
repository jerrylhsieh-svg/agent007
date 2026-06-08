from pydantic import BaseModel, Field

from agent.db.data_classes.intents import Intents


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User input message")
    history: list[dict] = Field(default_factory=list)
    session_id: str


class ChatResponse(BaseModel):
    reply: str

class TransactionAnalysisRequest(BaseModel):
    question: str
    history: list[dict] = Field(default_factory=list)

class RouteDecision(BaseModel):
    intent: Intents
    confidence: float = Field(ge=0, le=1)
    reason: str
    needs_db: bool = False
    extracted_args: dict = Field(default_factory=dict)