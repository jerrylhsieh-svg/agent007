from pydantic import BaseModel, Field
from enum import Enum


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User input message")
    history: list[dict] = []
    session_id: str


class ChatResponse(BaseModel):
    reply: str

class TransactionAnalysisRequest(BaseModel):
    question: str
    history: list[dict] = []

class Intent(str, Enum):
    ANALYZE_CARD_TRANSACTIONS = "analyze_card_transactions"
    ANALYZE_BANK_STATEMENTS = "analyze_bank_statements"
    TRAIN_CARD_MODEL = "train_card_model"
    TRAIN_STATEMENT_MODEL = "train_statement_model"
    REPREDICT_CARD_RECORDS = "repredict_card_records"
    REPREDICT_STATEMENT_RECORDS = "repredict_statement_records"
    SHOW_UNLABELED = "show_unlabeled"
    LABEL_RECORDS = "label_records"
    GENERAL_CHAT = "general_chat"
    UNKNOWN = "unknown"

class RouteDecision(BaseModel):
    intent: Intent
    confidence: float = Field(ge=0, le=1)
    reason: str
    needs_db: bool = False
    extracted_args: dict = Field(default_factory=dict)