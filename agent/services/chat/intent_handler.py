from typing import Any, Callable

from agent.db.data_classes.chat import Intent
from agent.services.analyzer.bank_statement_analyzer import generate_bank_statement_summary
from agent.services.analyzer.transaction_analyzer import generate_credit_card_summary
from agent.services.chat.call_model import call_model
from agent.services.chat.query_generators import generate_sql_from_question
from agent.services.labeling.labeling import handle_label_flow, label_sessions
from agent.services.repredict_service import repredict_records
from agent.services.train_models_service import train_model

Handler = Callable[..., str]

INTENT_HANDLERS: dict[Intent, tuple[Handler, dict[str, Any]]] = {
    Intent.ANALYZE_CARD_TRANSACTIONS: (generate_credit_card_summary,{}),
    Intent.ANALYZE_BANK_STATEMENTS: (generate_bank_statement_summary,{}),
    Intent.TRAIN_CARD_MODEL: (train_model,{"file_type": "transaction"}),
    Intent.TRAIN_STATEMENT_MODEL: (train_model,{"file_type": "statement"}),
    Intent.REPREDICT_STATEMENT_RECORDS: (repredict_records, {"file_type": "statement"}),
    Intent.REPREDICT_CARD_RECORDS: (repredict_records, {"file_type": "transaction"}),
    Intent.QUERY_TRANSACTIONS: (generate_sql_from_question, {"schema": ""}),
    Intent.LABEL_RECORDS: (handle_label_flow, {}),
    Intent.GENERAL_CHAT: (call_model, {"label_sessions": label_sessions}),
    Intent.UNKNOWN: (call_model, {"label_sessions": label_sessions}),
}