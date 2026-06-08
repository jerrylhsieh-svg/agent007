from sqlalchemy.orm import Session

from agent.db.data_classes.chat import ChatRequest
from agent.db.data_classes.intents import Intents
from agent.services.chat.classify_intents import classify_intent
from agent.services.chat.intent_handler import INTENT_HANDLERS
from agent.services.constants_and_dependencies import LOW_CONFIDENCE_THRESHOLD
from agent.services.labeling.labeling import label_sessions


def get_reply(req: ChatRequest, db:Session) -> str:
    if req.session_id in label_sessions:
        intent = Intents.LABEL_RECORDS
        confidence = 1.0
    else:
        decision = classify_intent(
            message=req.message,
            history=req.history,
        )
        intent = decision.intent
        confidence = decision.confidence
    
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
