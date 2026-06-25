from sqlalchemy.orm import Session

from agent.db.data_classes.chat import ChatRequest
from agent.db.data_classes.intents import Intents
from agent.services.chat.classify_intents import classify_intent
from agent.services.chat.intent_handler import INTENT_HANDLERS
from agent.services.constants_and_dependencies import LOW_CONFIDENCE_THRESHOLD


def get_reply(req: ChatRequest, db:Session) -> str:
    intent, confidence = deciding_intent(req)
    
    if intent == Intents.UNKNOWN or confidence < LOW_CONFIDENCE_THRESHOLD:
        intent = Intents.UNKNOWN
        
    handler, extra_kwargs = INTENT_HANDLERS[intent]

    kwargs = {
        "message": req.message,
        "history": req.history,
        "session_id": req.session_id,
        **extra_kwargs,
    }

    if intent.needs_db:
        kwargs["db"] = db

    return handler(**kwargs)

def deciding_intent(req: ChatRequest) -> tuple[Intents, float]:
    for intent in Intents:
        if req.session_id in intent.session_id_storage:
            return (intent, 1.0)
    decision = classify_intent(
        message=req.message,
        history=req.history,
    )
    return (decision.intent, decision.confidence)
