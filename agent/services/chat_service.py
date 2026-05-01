from typing import Any, Callable, Iterable

from agent.models.chat import ChatRequest
from agent.services.analyzer.bank_statement_analyzer import generate_bank_statement_summary, generate_bank_withdraw_summary
from agent.services.analyzer.transaction_analyzer import generate_credit_card_summary
from agent.services.call_model import call_model
from agent.services.constants_and_dependencies import IS_STATEMENT_TRAIN_TRIGGERS, IS_STATEMENT_TRIGGERS, IS_TRANSACTION_TRAIN_TRIGGERS, IS_TRANSACTION_TRIGGERS, IS_WITHDRAW_TRIGGERS
from agent.services.file_flow import handle_file_flow
from agent.services.train_models_service import train_model
from agent.services.triggers import contains_any_trigger


Route = tuple[Iterable[str], Callable[..., str], dict[str, Any]]

ROUTES: list[Route] = [
    (IS_TRANSACTION_TRIGGERS, generate_credit_card_summary, {}),
    (IS_STATEMENT_TRIGGERS, generate_bank_statement_summary, {}),
    (IS_WITHDRAW_TRIGGERS, generate_bank_withdraw_summary, {}),
    (IS_STATEMENT_TRAIN_TRIGGERS, train_model, {"file_type": "statement"}),
    (IS_TRANSACTION_TRAIN_TRIGGERS, train_model, {"file_type": "transaction"}),
]

def get_reply(req: ChatRequest) -> str:
    result = handle_file_flow(req.session_id, req.message)
    if result["handled"]:
        return result["reply"]

    for triggers, handler, extra_kwargs in ROUTES:
        if contains_any_trigger(req.message, triggers):
            return handler(
                question=req.message,
                history=req.history,
                **extra_kwargs,
            )

    return call_model(req.message, req.history)