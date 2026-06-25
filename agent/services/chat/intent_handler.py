from typing import Any, Callable

from agent.db.data_classes.intents import Intents
from agent.services.analyzer.bank_statement_analyzer import generate_bank_statement_summary
from agent.services.analyzer.transaction_analyzer import generate_credit_card_summary
from agent.services.chat.call_model import call_model
from agent.services.labeling.labeling import handle_label_flow, label_sessions
from agent.services.queries.query_executor import query_executor
from agent.services.repredict_service import repredict_records
from agent.services.train_models_service import train_model

Handler = Callable[..., str]

INTENT_HANDLERS: dict[Intents, tuple[Handler, dict[str, Any]]] = {
    Intents.ANALYZE_CARD_TRANSACTIONS: (generate_credit_card_summary,{}),
    Intents.ANALYZE_BANK_STATEMENTS: (generate_bank_statement_summary,{}),
    Intents.TRAIN_CARD_MODEL: (train_model,{"file_type": "transaction"}),
    Intents.TRAIN_STATEMENT_MODEL: (train_model,{"file_type": "statement"}),
    Intents.REPREDICT_STATEMENT_RECORDS: (repredict_records, {"file_type": "statement"}),
    Intents.REPREDICT_CARD_RECORDS: (repredict_records, {"file_type": "transaction"}),
    Intents.QUERY_TRANSACTIONS: (query_executor.executing, {}),
    Intents.LABEL_RECORDS: (handle_label_flow, {}),
    Intents.GENERAL_CHAT: (call_model, {"label_sessions": label_sessions}),
    Intents.UNKNOWN: (call_model, {"label_sessions": label_sessions}),
}