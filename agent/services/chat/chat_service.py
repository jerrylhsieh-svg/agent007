from typing import Any, Callable, Iterable

from sqlalchemy.orm import Session

from agent.db.data_classes.chat import ChatRequest
from agent.services.analyzer.bank_statement_analyzer import generate_bank_statement_summary, generate_bank_withdraw_summary
from agent.services.analyzer.transaction_analyzer import generate_credit_card_summary
from agent.services.chat.call_model import call_model
from agent.services.constants_and_dependencies import IS_LABEL_TRIGGERS, IS_STATEMENT_PREDICT_TRIGGERS, IS_STATEMENT_TRAIN_TRIGGERS, IS_STATEMENT_TRIGGERS, IS_TRANSACTION_PREDICT_TRIGGERS, IS_TRANSACTION_TRAIN_TRIGGERS, IS_TRANSACTION_TRIGGERS, IS_WITHDRAW_TRIGGERS, SAVE_TRIGGERS
from agent.services.file_flow import handle_file_flow, file_sessions
from agent.services.labeling.labeling import handle_label_flow, label_sessions
from agent.services.repredict_service import repredict_records
from agent.services.train_models_service import train_model
from agent.services.chat.triggers import contains_any_trigger


Route = tuple[Iterable[str], Callable[..., str], dict[str, Any]]
Flow_Route = tuple[Iterable[str], Callable[..., dict[str, Any]], dict[str, dict], dict[str, Any]]

ROUTES: list[Route] = [
    (IS_TRANSACTION_TRIGGERS, generate_credit_card_summary, {}),
    (IS_STATEMENT_TRIGGERS, generate_bank_statement_summary, {}),
    (IS_WITHDRAW_TRIGGERS, generate_bank_withdraw_summary, {}),
    (IS_STATEMENT_TRAIN_TRIGGERS, train_model, {"file_type": "statement"}),
    (IS_TRANSACTION_TRAIN_TRIGGERS, train_model, {"file_type": "transaction"}),
    (IS_STATEMENT_PREDICT_TRIGGERS, repredict_records, {"file_type": "statement"}),
    (IS_TRANSACTION_PREDICT_TRIGGERS, repredict_records, {"file_type": "transaction"}),
]
FLOW_ROUTES: list[Flow_Route] = [
    (SAVE_TRIGGERS, handle_file_flow, file_sessions, {}),
    (IS_LABEL_TRIGGERS, handle_label_flow, label_sessions, {}),
]

def get_reply(req: ChatRequest, db:Session) -> str:
    for flow_triggers, flow_handler, session, flow_extra_kwargs in FLOW_ROUTES:
        if not contains_any_trigger(req.message, flow_triggers, **flow_extra_kwargs,) and req.session_id not in session:
            continue
        result =  flow_handler(req.session_id, req.message)
        if result.get("handled", False):
            return result.get("reply", "Failed to get response")

    for triggers, handler, extra_kwargs in ROUTES:
        if contains_any_trigger(req.message, triggers):
            kwargs = {
            "question": req.message,
            "history": req.history,
            **extra_kwargs,
        }

        if handler in {repredict_records, train_model}:
            kwargs["db"] = db

        return handler(**kwargs)


    return call_model(req.message, req.history)