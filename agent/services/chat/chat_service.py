from sqlalchemy.orm import Session

from agent.db.data_classes.chat import ChatRequest, Intent
from agent.services.chat.classify_intents import classify_intent
from agent.services.chat.intent_handler import INTENT_HANDLERS
from agent.services.constants_and_dependencies import LOW_CONFIDENCE_THRESHOLD
from agent.services.labeling.labeling import label_sessions

DB_REQUIRED_INTENTS = {
    Intent.ANALYZE_CARD_TRANSACTIONS,
    Intent.ANALYZE_BANK_STATEMENTS,
    Intent.TRAIN_CARD_MODEL,
    Intent.TRAIN_STATEMENT_MODEL,
    Intent.REPREDICT_STATEMENT_RECORDS,
    Intent.REPREDICT_CARD_RECORDS,
    Intent.LABEL_RECORDS,
}

def get_reply(req: ChatRequest, db:Session) -> str:
    if req.session_id in label_sessions:
        intent = Intent.LABEL_RECORDS
        confidence = 1.0
    else:
        decision = classify_intent(
            message=req.message,
            history=req.history,
        )
        intent = decision.intent
        confidence = decision.confidence
    
    if intent == Intent.UNKNOWN or confidence < LOW_CONFIDENCE_THRESHOLD:
        intent = Intent.UNKNOWN
        
    handler, extra_kwargs = INTENT_HANDLERS[intent]

    kwargs = {
        "message": req.message,
        "history": req.history,
        "session_id": req.session_id,
        **extra_kwargs,
    }

    if intent in DB_REQUIRED_INTENTS:
        kwargs["db"] = db

    return handler(**kwargs)
