from sqlalchemy.orm import Session

from agent.db.data_classes.chat import ChatRequest, Intent
from agent.services.chat.classify_intents import classify_intent
from agent.services.chat.intent_handler import INTENT_HANDLERS

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
    decision = classify_intent(
        message=req.message,
        history=req.history,
    )
    
    handler, extra_kwargs = INTENT_HANDLERS[decision.intent]

    kwargs = {
        "message": req.message,
        "history": req.history,
        **extra_kwargs,
    }

    if decision.intent in DB_REQUIRED_INTENTS:
        kwargs["db"] = db
    if decision.intent == Intent.UNKNOWN or decision.confidence < 0.55:
        return INTENT_HANDLERS[ Intent.UNKNOWN][0](**kwargs)
    else:
        return handler(**kwargs)
